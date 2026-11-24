import json
import os
import sys
import time
import uuid
from pathlib import Path

import truststore
import yaml
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware, ModelCallLimitMiddleware, ModelRetryMiddleware,
    ToolCallLimitMiddleware, ToolRetryMiddleware,
)
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

import agent_guardrails as ag
from agent_guardrails.claude_cli import chat_model
from agent_guardrails.tracing import TracingMiddleware, run_span, setup_tracing
from tools import IRREVERSIBLE, TOOLS

truststore.inject_into_ssl()  # System-Zertifikate statt certifi (TLS-Inspektion durch Virenscanner/Proxy)
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
_, front, system_prompt = (ROOT / "config.md").read_text(encoding="utf-8").split("---", 2)
CFG = yaml.safe_load(front)
MODEL = os.environ.get("MODEL", CFG["model"])  # z. B. MODEL=ollama:granite4.1:8b für lokale Läufe
POLICY = ag.load_policy()                      # zentrales Paket packages/agent-guardrails (Issue #7)
PRICE = {"input": 0, "output": 0} if MODEL.startswith(("ollama:", "claude-cli:")) else CFG["price_usd_per_mtok"]
TRACER = setup_tracing(ROOT / "traces", CFG["log_retention_days"])   # Issue #3
APPROVAL = set(IRREVERSIBLE) | {t.name for t in TOOLS if t.name in POLICY.approval_required_tools}

agent = create_agent(
    model=chat_model(MODEL),   # MODEL=claude-cli:haiku läuft über die Claude-CLI (ohne API-Key)
    tools=TOOLS,
    system_prompt=system_prompt.strip(),
    middleware=[
        TracingMiddleware(CFG["kontext"], PRICE, POLICY),
        AnthropicPromptCachingMiddleware(unsupported_model_behavior="ignore"),
        ModelRetryMiddleware(max_retries=3, on_failure="error"),  # Default "continue" tarnt Ausfälle als Antwort
        ToolRetryMiddleware(max_retries=3),
        ModelCallLimitMiddleware(run_limit=CFG["max_steps"], exit_behavior="end"),
        ToolCallLimitMiddleware(run_limit=CFG["max_steps"]),
        HumanInTheLoopMiddleware(interrupt_on={
            name: {"allowed_decisions": ["approve", "reject"]} for name in APPROVAL
        }),
        ag.GuardrailMiddleware(POLICY),
    ],
    checkpointer=InMemorySaver(),
)



def mask(text: str) -> str:  # DSGVO: keine Klartext-Adressen in Logs (Muster aus der zentralen Policy)
    return POLICY.mask(text)


def ask_human(action: dict) -> str:
    answer = input(f"Freigabe nötig: {action['name']} {json.dumps(action['args'], ensure_ascii=False)}\napprove/reject? ")
    return "approve" if answer.strip().lower() == "approve" else "reject"


def run(task: str, decide=ask_human) -> dict:
    run_id = uuid.uuid4().hex[:8]
    config = {"configurable": {"thread_id": run_id}, "recursion_limit": CFG["max_steps"] * 6}   # Middleware-Hooks sind eigene Nodes; die echte Grenze setzt ModelCallLimit
    log = ROOT / "logs" / f"{run_id}.log"
    log.parent.mkdir(exist_ok=True)
    payload = {"messages": [{"role": "user", "content": f"<lead_email>\n{task}\n</lead_email>"}]}
    with run_span(TRACER, CFG["kontext"], run_id):
        return _loop(payload, config, log, run_id, decide)


def _loop(payload, config, log, run_id, decide) -> dict:
    step = 0
    while True:
        for update in agent.stream(payload, config, stream_mode="updates"):
            for node, data in update.items():
                for msg in (data or {}).get("messages", []) if isinstance(data, dict) else []:
                    step += 1
                    calls = getattr(msg, "tool_calls", None) or []
                    with log.open("a", encoding="utf-8") as f:   # nur Textfelder maskieren, nie das fertige JSON
                        f.write(json.dumps({
                            "run": run_id, "step": step, "node": node, "ts": time.time(),
                            "type": msg.type,  # ai = Think/Act, tool = Observe
                            "content": mask(msg.text[:2000]),  # nur Text, keine rohen Blöcke/Signaturen
                            "tool_calls": [{"name": c["name"], "args": json.loads(mask(json.dumps(c["args"], ensure_ascii=False)))}
                                           for c in calls],
                            "usage": getattr(msg, "usage_metadata", None),
                        }, ensure_ascii=False, default=str) + "\n")
        state = agent.get_state(config)
        if not state.interrupts:
            return {**state.values, "run_id": run_id}
        request = state.interrupts[0].value  # HITLRequest: eine Entscheidung pro action_request
        decisions = [{"type": decide(a)} for a in request["action_requests"]]
        payload = Command(resume={"decisions": decisions})


if __name__ == "__main__":
    result = run(sys.stdin.read() if len(sys.argv) < 2 else Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(result["messages"][-1].content)
