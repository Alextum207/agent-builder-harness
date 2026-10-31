import json
import re
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

from tools import IRREVERSIBLE, TOOLS

truststore.inject_into_ssl()  # System-Zertifikate statt certifi (TLS-Inspektion durch Virenscanner/Proxy)
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
_, front, system_prompt = (ROOT / "config.md").read_text(encoding="utf-8").split("---", 2)
CFG = yaml.safe_load(front)

agent = create_agent(
    model=CFG["model"],
    tools=TOOLS,
    system_prompt=system_prompt.strip(),
    middleware=[
        AnthropicPromptCachingMiddleware(),
        ModelRetryMiddleware(max_retries=3, on_failure="error"),  # Default "continue" tarnt Ausfälle als Antwort
        ToolRetryMiddleware(max_retries=3),
        ModelCallLimitMiddleware(run_limit=CFG["max_steps"], exit_behavior="end"),
        ToolCallLimitMiddleware(run_limit=CFG["max_steps"]),
        HumanInTheLoopMiddleware(interrupt_on={
            name: {"allowed_decisions": ["approve", "reject"]} for name in IRREVERSIBLE
        }),
    ],
    checkpointer=InMemorySaver(),
)

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def mask(text: str) -> str:  # DSGVO: keine Klartext-Adressen in Logs
    return EMAIL.sub(lambda m: m.group()[0] + "***@" + m.group().split("@")[1], text)


def ask_human(action: dict) -> str:
    answer = input(f"Freigabe nötig: {action['name']} {json.dumps(action['args'], ensure_ascii=False)}\napprove/reject? ")
    return "approve" if answer.strip().lower() == "approve" else "reject"


def run(task: str, decide=ask_human) -> dict:
    run_id = uuid.uuid4().hex[:8]
    config = {"configurable": {"thread_id": run_id}, "recursion_limit": CFG["max_steps"] * 3}
    log, step = ROOT / "logs" / f"{run_id}.log", 0
    log.parent.mkdir(exist_ok=True)
    payload = {"messages": [{"role": "user", "content": f"<lead_email>\n{task}\n</lead_email>"}]}
    while True:
        for update in agent.stream(payload, config, stream_mode="updates"):
            for node, data in update.items():
                for msg in (data or {}).get("messages", []) if isinstance(data, dict) else []:
                    step += 1
                    calls = getattr(msg, "tool_calls", None) or []
                    with log.open("a", encoding="utf-8") as f:
                        f.write(mask(json.dumps({
                            "run": run_id, "step": step, "node": node, "ts": time.time(),
                            "type": msg.type,  # ai = Think/Act, tool = Observe
                            "content": msg.text[:2000],  # nur Text, keine rohen Blöcke/Signaturen
                            "tool_calls": [{"name": c["name"], "args": c["args"]} for c in calls],
                            "usage": getattr(msg, "usage_metadata", None),
                        }, ensure_ascii=False, default=str)) + "\n")
        state = agent.get_state(config)
        if not state.interrupts:
            return {**state.values, "run_id": run_id}
        request = state.interrupts[0].value  # HITLRequest: eine Entscheidung pro action_request
        decisions = [{"type": decide(a)} for a in request["action_requests"]]
        payload = Command(resume={"decisions": decisions})


if __name__ == "__main__":
    result = run(sys.stdin.read() if len(sys.argv) < 2 else Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(result["messages"][-1].content)
