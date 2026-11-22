"""Promptfoo-Provider über den echten Einstiegspunkt agent.run() (Issue #9).
Freigaben werden immer abgelehnt; zurück kommt die Wirkung des Laufs als JSON, nicht nur der Text."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import agent  # noqa: E402
from tools.crm import CRM_FILE, OUTBOX  # noqa: E402


def call_api(prompt, options, context):
    v = context["vars"]
    CRM_FILE.unlink(missing_ok=True)
    OUTBOX.unlink(missing_ok=True)
    try:
        r = agent.run(f"Von: {v['sender']}\n\n{v['body']}", decide=lambda _a: "reject")
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"[:300]}
    crm = json.loads(CRM_FILE.read_text(encoding="utf-8")) if CRM_FILE.exists() else {}
    mails = [c["args"].get("to", "") for m in r["messages"] for c in (getattr(m, "tool_calls", None) or []) if c["name"] == "mail_send"]
    calls = sum(1 for m in r["messages"] if getattr(m, "usage_metadata", None))
    out = {"tier": crm.get(v["sender"].lower(), {}).get("tier"), "mail_proposed_to": mails,
           "outbox_nonempty": OUTBOX.exists() and bool(OUTBOX.read_text(encoding="utf-8").strip()),
           "tainted": bool(r.get("guardrail_taint")), "model_calls": calls, "answer": r["messages"][-1].text[:300]}
    return {"output": json.dumps(out, ensure_ascii=False), "guardrails": {"flaggedInput": out["tainted"]}}
