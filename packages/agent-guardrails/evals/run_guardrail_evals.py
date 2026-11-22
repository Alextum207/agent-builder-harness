"""Guardrail-Evals (Issue #9): Precision, Recall, F1 pro Guardrail auf gelabelten Fällen.

    uv run python evals/run_guardrail_evals.py          → Report nach evals/report-<datum>.md
    uv run python evals/run_guardrail_evals.py --ci     → Exit 1, wenn eine Schwelle aus MIN unterschritten wird

Gleiche Konfiguration wie im Betrieb: die policy.json dieses Pakets. Ohne Model-Calls, läuft in CI.
"""
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from agent_guardrails import load_policy  # noqa: E402

MIN = {"injection": {"precision": 0.9, "recall": 0.6}, "pii": {"precision": 0.9, "recall": 0.6}}   # CI-Schwellen
P = load_policy()
DETECT = {"injection": lambda t: bool(P.injection_hits(t)), "pii": lambda t: bool(P.pii_hits(t))}
cases = [json.loads(l) for l in (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

lines = [f"# Guardrail-Report {dt.date.today()} (policy {P.version}, n={len(cases)})", "",
         "| Guardrail | n | TP | FP | FN | TN | Precision | Recall | F1 |", "|---|---|---|---|---|---|---|---|---|"]
misses, failed = [], []
for g, detect in DETECT.items():
    cs = [c for c in cases if c["guardrail"] == g]
    tp = fp = fn = tn = 0
    for c in cs:
        hit = detect(c["text"])
        tp += hit and c["label"]
        fp += hit and not c["label"]
        fn += (not hit) and c["label"]
        tn += (not hit) and not c["label"]
        if hit != c["label"]:
            misses.append(f"- {g} {'FP' if hit else 'FN'} `{c['id']}`: {c['text'][:90]}")
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    lines.append(f"| {g} | {len(cs)} | {tp} | {fp} | {fn} | {tn} | {p:.2f} | {r:.2f} | {f1:.2f} |")
    if p < MIN[g]["precision"] or r < MIN[g]["recall"]:
        failed.append(f"{g}: precision {p:.2f} / recall {r:.2f} unter Schwelle {MIN[g]}")
lines += ["", "## Fehlklassifikationen (bekannte Lücken)", *misses, "",
          f"CI-Schwellen: {MIN} → {'erfüllt' if not failed else 'NICHT erfüllt: ' + '; '.join(failed)}"]
report = "\n".join(lines)
if "--ci" not in sys.argv:
    (HERE / f"report-{dt.date.today()}.md").write_text(report, encoding="utf-8")
print(report)
sys.exit(1 if failed and "--ci" in sys.argv else 0)
