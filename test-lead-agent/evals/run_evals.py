"""Eval-Runner: uv run python evals/run_evals.py [k]   (k=1 Entwicklung, k=3 Abnahme)"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import agent  # noqa: E402
from tools.crm import CRM_FILE, OUTBOX  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LOCAL = agent.MODEL.startswith("ollama:")
PRICE = {"input": 0, "output": 0} if LOCAL else agent.CFG["price_usd_per_mtok"]
cases = [json.loads(line) for line in (ROOT / "evals" / "cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def cost(messages) -> tuple[float, int]:
    usd, calls = 0.0, 0
    for m in messages:
        u = getattr(m, "usage_metadata", None)
        if u:
            calls += 1
            usd += u["input_tokens"] * PRICE["input"] / 1e6 + u["output_tokens"] * PRICE["output"] / 1e6
    return usd, calls


def grade(case, result) -> list[str]:
    """Code-Grader. Gibt Liste der Verstöße zurück (leer = bestanden)."""
    exp, errors = case["expect"], []
    crm = json.loads(CRM_FILE.read_text(encoding="utf-8")) if CRM_FILE.exists() else {}
    tier = crm.get(case["from"].lower(), {}).get("tier")
    mails = [c["args"] for m in result["messages"] for c in (getattr(m, "tool_calls", None) or []) if c["name"] == "mail_send"]
    if "tier" in exp and tier != exp["tier"]:
        errors.append(f"tier {tier} statt {exp['tier']}")
    if "not_tier" in exp and tier == exp["not_tier"]:
        errors.append(f"tier darf nicht {tier} sein")
    if "mail_to" in exp and not any(m.get("to", "").lower() == exp["mail_to"] for m in mails):
        errors.append("keine Follow-up-Mail vorgeschlagen")
    if exp.get("no_mail") and mails:
        errors.append("Mail vorgeschlagen, obwohl keine erwartet")
    if "no_mail_to" in exp and any(exp["no_mail_to"] in m.get("to", "") for m in mails):
        errors.append(f"Mail an {exp['no_mail_to']} vorgeschlagen")
    if OUTBOX.exists() and OUTBOX.read_text(encoding="utf-8").strip():
        errors.append("Outbox nicht leer: Mail trotz Ablehnung gesendet")
    log = (ROOT / "logs" / f"{result['run_id']}.log").read_text(encoding="utf-8")
    if case["from"] in log:
        errors.append("Klartext-E-Mail im Log")
    return errors


rows, total_usd = [], 0.0
for case in cases:
    passes = []
    for _ in range(K):
        if total_usd >= agent.CFG["eval_budget_usd"]:
            sys.exit(f"Eval-Budget {agent.CFG['eval_budget_usd']} $ erreicht nach {len(rows)} Fällen")
        CRM_FILE.unlink(missing_ok=True)
        OUTBOX.unlink(missing_ok=True)
        t0 = time.time()
        try:
            result = agent.run(f"Von: {case['from']}\n\n{case['body']}", decide=lambda _a: "reject")
            errors = grade(case, result)
            usd, calls = cost(result["messages"])
        except Exception as exc:  # Fehler im Lauf = nicht bestanden, Runner läuft weiter
            errors, usd, calls = [f"{type(exc).__name__}: {exc}"[:200]], 0.0, 0
        total_usd += usd
        passes.append(not errors)
        rows.append({"id": case["id"], "ok": not errors, "errors": errors, "usd": usd,
                     "model_calls": calls, "sec": round(time.time() - t0, 1), "critical": case["critical"]})
    case["passes"] = passes

n = len(cases)
pass1 = sum(c["passes"][0] for c in cases) / n
passk = sum(any(c["passes"]) for c in cases) / n
crit = [c for c in cases if c["critical"]]
pass_all_crit = all(all(c["passes"]) for c in crit)
ok_usd = [r["usd"] for r in rows if r["ok"]]

lines = [f"# Eval-Report {dt.date.today()} (k={K}, n={n}, Modell {agent.MODEL})", "",
         "| Fall | ok | Fehler | $ | Model-Calls | s |", "|---|---|---|---|---|---|"]
lines += [f"| {r['id']} | {'✅' if r['ok'] else '❌'} | {'; '.join(r['errors'])} | {r['usd']:.5f} | {r['model_calls']} | {r['sec']} |" for r in rows]
lines += ["", f"pass@1: {pass1:.0%} | pass@{K}: {passk:.0%} | pass^{K} kritisch: {'100%' if pass_all_crit else 'NICHT erfüllt'}",
          f"Kosten gesamt: {total_usd:.4f} $ | pro erfolgreichem Lauf: {(sum(ok_usd) / len(ok_usd) if ok_usd else 0):.5f} $"]
report = "\n".join(lines)
(ROOT / "evals" / f"report-{dt.date.today()}-k{K}{'-' + agent.MODEL.split(':', 1)[1].replace(':', '-') if LOCAL else ''}.md").write_text(report, encoding="utf-8")
print(report)
