"""Evals pro Workflow-Node plus Ende-zu-Ende (Issue #2): uv run python evals/run_node_evals.py [n]

Fall-Format (evals/node_cases.jsonl), erzeugt aus dem Test-ERP:
  {"id": ..., "node": "extrahieren" | "kontieren" | "e2e", "input": {...State...}, "expect": {...}}
Der Runner ruft LLM-Nodes direkt mit ihrer Eingabe auf, nicht nur die ganze Kette.
"""
import datetime as dt
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import erp  # noqa: E402
import workflow  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
CASES = ROOT / "evals" / "node_cases.jsonl"


def generate(n: int) -> list[dict]:
    erp.build()
    con = erp.connect()
    rows = con.execute("SELECT r.nr, r.text, r.betrag, k.nr AS knr, k.name, k.standardkonto FROM rechnungen r "
                       "JOIN kreditoren k ON k.nr = r.kreditor WHERE r.nr != 'RE-2026-0099' ORDER BY r.nr").fetchall()
    out = []
    for r in random.Random(11).sample(rows, n):
        inp = {"text": r["text"]}
        out.append({"id": f"{r['nr']}-extr", "node": "extrahieren", "input": inp,
                    "expect": {"kreditor_name": r["name"], "rechnungsnr": r["nr"], "brutto_eur": r["betrag"]}})
        out.append({"id": f"{r['nr']}-konto", "node": "kontieren", "input": inp, "expect": {"konto": r["standardkonto"]}})
        out.append({"id": f"{r['nr']}-e2e", "node": "e2e", "input": inp,
                    "expect": {"kreditor_nr": r["knr"], "konto": r["standardkonto"],
                               "entscheidung": "Freigabe Leitung" if r["betrag"] > workflow.FREIGABE_AB_EUR else "Buchungsvorschlag"}})
    CASES.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in out) + "\n", encoding="utf-8")
    return out


def check(node: str, exp: dict, got: dict) -> list[str]:
    if node == "extrahieren":
        e, errs = got["extrakt"], []
        if e["kreditor_name"].strip().lower() != exp["kreditor_name"].lower():
            errs.append(f"Kreditor '{e['kreditor_name']}'")
        if e["rechnungsnr"].strip() != exp["rechnungsnr"]:
            errs.append(f"Nr '{e['rechnungsnr']}'")
        if abs(e["brutto_eur"] - exp["brutto_eur"]) > 0.01:
            errs.append(f"Betrag {e['brutto_eur']} statt {exp['brutto_eur']}")
        return errs
    return [f"{k}: {got.get(k)!r} statt {v!r}" for k, v in exp.items() if got.get(k) != v]


cases = generate(N)
res: dict[str, list[bool]] = {"extrahieren": [], "kontieren": [], "e2e": []}
rows = []
for c in cases:
    t0 = time.time()
    try:
        got = workflow.WORKFLOW.invoke(c["input"]) if c["node"] == "e2e" else workflow.LLM_NODES[c["node"]](c["input"])
        errs = check(c["node"], c["expect"], got)
    except Exception as exc:
        errs = [f"{type(exc).__name__}: {exc}"[:160]]
    res[c["node"]].append(not errs)
    rows.append(f"| {c['id']} | {c['node']} | {'✅' if not errs else '❌'} | {'; '.join(errs)} | {time.time() - t0:.1f} |")
    print(rows[-1], flush=True)

rate = {k: sum(v) / len(v) for k, v in res.items()}
product = rate["extrahieren"] * rate["kontieren"]
hint = ("⚠ Kette liegt deutlich unter dem Produkt der Nodes: Vertrag zwischen Nodes prüfen (Code-Checks, Formate)."
        if rate["e2e"] < product - 0.10 else "Kette entspricht etwa dem Produkt der Nodes.")
report = "\n".join([f"# Node-Report {dt.date.today()} (n={N} Rechnungen, Modell {workflow.MODEL})", "",
                    "| Node | Trefferquote |", "|---|---|",
                    f"| extrahieren (LLM) | {rate['extrahieren']:.0%} |", f"| kontieren (LLM) | {rate['kontieren']:.0%} |",
                    f"| Produkt der Nodes | {product:.0%} |", f"| **Ende-zu-Ende** | **{rate['e2e']:.0%}** |", "", hint, "",
                    "| Fall | Node | ok | Abweichung | s |", "|---|---|---|---|---|", *rows])
suffix = workflow.MODEL.split(":", 1)[1].replace(":", "-")
(ROOT / "evals" / f"node-report-{dt.date.today()}-{suffix}.md").write_text(report, encoding="utf-8")
print(report)
