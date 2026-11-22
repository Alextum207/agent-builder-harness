"""Finance-Recherche-Agent auf dem Test-ERP: uv run python agent.py "Frage"

Zeigt Kontext-Verdichtung mit Artefakt-Liste (#1), Traces (#3), zentrale Guardrails (#7) und eigene Identität (#8).
"""
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import NotRequired

import truststore
import yaml
from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    AgentMiddleware, ClearToolUsesEdit, ContextEditingMiddleware, HumanInTheLoopMiddleware, ModelCallLimitMiddleware,
    ModelRetryMiddleware, SummarizationMiddleware, ToolCallLimitMiddleware,
)
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_config
from langgraph.types import Command

import agent_guardrails as ag
import tools
from agent_guardrails.claude_cli import chat_model
from agent_guardrails.tracing import TracingMiddleware, run_span, setup_tracing

truststore.inject_into_ssl()
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
_, front, SYSTEM_PROMPT = (ROOT / "config.md").read_text(encoding="utf-8").split("---", 2)
CFG = yaml.safe_load(front)
MODEL = os.environ.get("MODEL", CFG["model"])
LOCAL = MODEL.startswith("ollama:")
FREE = MODEL.startswith(("ollama:", "claude-cli:"))   # claude-cli: Kosten kommen aus CLAUDE_CLI_COST_LOG
PRICE = {"input": 0, "output": 0} if FREE else CFG["price_usd_per_mtok"]
POLICY = ag.load_policy()
IDENTITY = ag.Identity.from_config(CFG)
tools.WRITE = IDENTITY.allows("erp", "write")          # zweite Linie: DB nur mit Schreibrecht beschreibbar
TRACER = setup_tracing(ROOT / "traces", CFG["log_retention_days"])
ID = re.compile(r"RE-2026-\d{4}|\b700\d\d\b")


class ArtifactState(AgentState):
    artifacts: NotRequired[list[str]]


class ArtifactMiddleware(AgentMiddleware):
    """Führt jede angefasste Rechnungs- oder Kreditorennummer im State (context.md: Artefakte nicht der
    Zusammenfassung überlassen). Läuft vor SummarizationMiddleware, sieht also alle Tool-Aufrufe."""
    state_schema = ArtifactState

    def _collect(self, state):
        seen = list(state.get("artifacts", []))
        for m in state["messages"]:
            for c in getattr(m, "tool_calls", None) or []:
                for i in ID.findall(json.dumps(c["args"])):
                    if i not in seen:
                        seen.append(i)
        return None if seen == state.get("artifacts", []) else {"artifacts": seen}

    def before_model(self, state, runtime):
        return self._collect(state)

    def after_agent(self, state, runtime):
        return self._collect(state)


CLEARED: dict[str, int] = {}     # Lauf → Anzahl geleerter Tool-Ergebnisse (ContextEditing ändert nur die Anfrage, nicht den State)


class CountingContextEditing(ContextEditingMiddleware):
    def wrap_model_call(self, request, handler):
        def counted(req):
            n = sum(1 for m in req.messages if m.type == "tool" and m.text == ClearToolUsesEdit().placeholder)
            if n:
                tid = get_config()["configurable"]["thread_id"]
                CLEARED[tid] = max(CLEARED.get(tid, 0), n)
            return handler(req)
        return super().wrap_model_call(request, counted)


def build(trigger_tokens: int | None = None, keep_messages: int | None = None, mode: str | None = None):
    """mode `clear`: alte Tool-Ergebnisse entfernen, Stammdaten ausgenommen (billigste Stufe, context.md).
    mode `summarize`: Verlauf zusammenfassen (ersetzt Nachrichten dauerhaft)."""
    comp = CFG["compaction"]
    trigger, keep, mode = trigger_tokens or comp["trigger_tokens"], keep_messages or comp["keep_messages"], mode or comp["mode"]
    approval = {n: {"allowed_decisions": ["approve", "reject"]}
                for n in POLICY.approval_required_tools if n in {t.name for t in tools.TOOLS}}
    compaction = (CountingContextEditing(edits=[ClearToolUsesEdit(trigger=trigger, keep=keep, exclude_tools=comp["exclude_tools"])])
                  if mode == "clear" else
                  SummarizationMiddleware(model=chat_model(MODEL), trigger=("tokens", trigger), keep=("messages", keep)))
    return create_agent(
        model=chat_model(MODEL),
        tools=tools.TOOLS,
        system_prompt=SYSTEM_PROMPT.strip(),
        middleware=[
            TracingMiddleware(IDENTITY.agent_id, PRICE, POLICY),
            ArtifactMiddleware(),
            compaction,
            AnthropicPromptCachingMiddleware(unsupported_model_behavior="ignore"),
            ModelRetryMiddleware(max_retries=3, on_failure="error"),
            ModelCallLimitMiddleware(run_limit=CFG["max_steps"], exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=CFG["max_steps"]),
            HumanInTheLoopMiddleware(interrupt_on=approval),
            ag.GuardrailMiddleware(POLICY),
            ag.PermissionMiddleware(IDENTITY, tools.TOOL_SCOPES),
        ],
        checkpointer=InMemorySaver(),
    )


AGENT = build()


def ask_human(action: dict) -> str:
    answer = input(f"Freigabe nötig: {action['name']} {json.dumps(action['args'], ensure_ascii=False)}\napprove/reject? ")
    return "approve" if answer.strip().lower() == "approve" else "reject"


def run(question: str, decide=ask_human, agent=None) -> dict:
    agent = agent or AGENT
    run_id = uuid.uuid4().hex[:8]
    config = {"configurable": {"thread_id": run_id}, "recursion_limit": CFG["max_steps"] * 6}   # Middleware-Hooks sind eigene Nodes; die echte Grenze setzt ModelCallLimit
    log, step = ROOT / "logs" / f"{run_id}.log", 0
    log.parent.mkdir(exist_ok=True)
    payload = {"messages": [{"role": "user", "content": question}]}
    seen: set[str] = set()      # HITL gibt bei Interrupt die letzte AI-Nachricht erneut aus: nicht doppelt loggen
    with run_span(TRACER, IDENTITY.agent_id, run_id):
        while True:
            for update in agent.stream(payload, config, stream_mode="updates"):
                for node, data in update.items():
                    for msg in (data or {}).get("messages", []) if isinstance(data, dict) else []:
                        if not hasattr(msg, "type") or msg.type == "remove":
                            continue
                        if msg.id:
                            if msg.id in seen:
                                continue
                            seen.add(msg.id)
                        step += 1
                        calls = getattr(msg, "tool_calls", None) or []
                        with log.open("a", encoding="utf-8") as f:   # nur Textfelder maskieren, nie das fertige JSON
                            f.write(json.dumps({
                                "run": run_id, "step": step, "node": node, "ts": time.time(), "type": msg.type,
                                "name": getattr(msg, "name", None), "content": POLICY.mask(msg.text[:2000]),
                                "tool_calls": [{"name": c["name"], "args": json.loads(POLICY.mask(json.dumps(c["args"], ensure_ascii=False)))}
                                               for c in calls],
                                "usage": getattr(msg, "usage_metadata", None),
                            }, ensure_ascii=False, default=str) + "\n")
            state = agent.get_state(config)
            if not state.interrupts:
                return {**state.values, "run_id": run_id}
            request = state.interrupts[0].value
            payload = Command(resume={"decisions": [{"type": decide(a)} for a in request["action_requests"]]})


if __name__ == "__main__":
    print(run(" ".join(sys.argv[1:]) or sys.stdin.read())["messages"][-1].text)
