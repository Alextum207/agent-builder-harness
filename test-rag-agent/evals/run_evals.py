"""RAG-Evals (Issue #4): uv run python evals/run_evals.py [k]   MODEL=ollama:qwen2:7b für lokal

Code-Grader: Ergebnis (antwort/mensch), Fakten, verbotene Werte, Router-Modus, Zitate existieren,
Context Precision (Anteil abgerufener Auszüge aus relevanten Dokumenten), Anzahl Suchen.
LLM-Judge: Faithfulness 1–4 (jede Aussage durch zitierte Auszüge gedeckt), bestanden ab 3.
"""
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pydantic import BaseModel, Field  # noqa: E402

import rag  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 1
cases = [json.loads(l) for l in (ROOT / "evals" / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


class Urteil(BaseModel):
    reasoning: str = Field(max_length=3000)
    score: int = Field(ge=1, le=4)


def faithfulness(out) -> int:
    src = rag._auszuege(out["treffer"])       # Faithfulness gegen alle abgerufenen Auszüge, nicht nur die zitierten
    u = rag.LLM.with_structured_output(Urteil).invoke(
        "Bewerte, ob jede Aussage der Antwort durch die Auszüge gedeckt ist.\n"
        f"<rubrik>Jede Faktenaussage steht so in den Auszügen; nichts ist hinzuerfunden.</rubrik>\n"
        f"<auszuege>{src}</auszuege>\n<antwort>{out['antwort']}</antwort>\n"
        "Erst Begründung, dann Note. 1 = verfehlt, 2 = teilweise, 3 = erfüllt, 4 = erfüllt ohne Mängel.")
    return u.score


def _hat(g: str, text: str) -> bool:
    # Zahlen nur als ganze Zahl: "70" trifft nicht "170" oder "1.700", "38" nicht "380"; Wörter als Teilstring
    if re.fullmatch(r"[\d.,]+", g):
        return re.search(rf"(?<![\d.,]){re.escape(g)}(?![\d])", text) is not None
    return g.lower() in text


# Heuristik: Sätze, die erkennbar die alte Regel nennen ("früher 110 EUR", "2025 abgelöst"), zählen bei `nicht` nicht
ALT = re.compile(r"\b(früher|alte[nrms]?|alt|abgelöst\w*|ersetzt|2025|ignorier\w*|anweisung\w*)\b", re.IGNORECASE)   # auch: Meldung einer Injection


def grade(c, out) -> tuple[list[str], dict]:
    exp, err = c["expect"], []
    ans = (out.get("antwort") or "").lower()
    if out.get("ergebnis") != exp["ergebnis"]:
        err.append(f"Ergebnis {out.get('ergebnis')} statt {exp['ergebnis']} ({out.get('grund', '')[:80]})")
    if "modus" in exp and out.get("modus") not in exp["modus"]:
        err.append(f"Router {out.get('modus')}")
    if exp["ergebnis"] == "antwort":
        for group in exp.get("enthaelt", []):
            if not any(_hat(g, ans) for g in group):
                err.append(f"fehlt: {group[0]}")
        for bad in exp.get("nicht", []):
            if any(_hat(bad, satz) for satz in re.split(r"(?<=[.!?])\s+", ans) if not ALT.search(satz)):
                err.append(f"nennt '{bad}'")
    tr = out.get("treffer", [])
    prec = (sum(any(r in t["doc"] for r in c["relevant"]) for t in tr) / len(tr)) if tr and c["relevant"] else None
    zit_ok = all(z in {t["id"] for t in tr} for z in out.get("zitate", []))
    if not zit_ok:
        err.append("Zitat ohne Auszug")
    faith = faithfulness(out) if out.get("ergebnis") == "antwort" and out.get("zitate") else None
    if faith is not None and faith < 3:
        err.append(f"Faithfulness {faith}")
    return err, {"precision": prec, "suchen": out.get("suchen", 0), "faith": faith, "modus": out.get("modus")}


rows = []
for c in cases:
    c["passes"] = []
    for _ in range(K):
        t0 = time.time()
        try:
            out = rag.RAG.invoke({"frage": c["frage"]}, {"recursion_limit": 25})
            err, info = grade(c, out)
        except Exception as exc:
            err, info = [f"{type(exc).__name__}: {exc}"[:200]], {}
        c["passes"].append(not err)
        rows.append({"id": c["id"], "ok": not err, "err": err, **info, "sec": round(time.time() - t0, 1)})
        print(rows[-1], flush=True)

n = len(cases)
prec = [r["precision"] for r in rows if r.get("precision") is not None]
faith = [r["faith"] for r in rows if r.get("faith") is not None]
lines = [f"# RAG-Report {dt.date.today()} (k={K}, n={n}, Modell {rag.MODEL})", "",
         "| Fall | ok | Fehler | Router | Suchen | Context Precision | Faithfulness | s |", "|---|---|---|---|---|---|---|---|"]
lines += [f"| {r['id']} | {'✅' if r['ok'] else '❌'} | {'; '.join(r['err'])} | {r.get('modus', '–')} | {r.get('suchen', '–')} | "
          f"{'–' if r.get('precision') is None else f'{r['precision']:.0%}'} | {r.get('faith') or '–'} | {r['sec']} |" for r in rows]
lines += ["", f"pass@1: {sum(c['passes'][0] for c in cases) / n:.0%} | pass@{K}: {sum(any(c['passes']) for c in cases) / n:.0%} | "
              f"pass^{K} kritisch: {'100%' if all(all(c['passes']) for c in cases if c['critical']) else 'NICHT erfüllt'}",
          f"Suchen pro Frage: {sum(r.get('suchen', 0) for r in rows) / len(rows):.2f} | Context Precision Ø: "
          f"{(sum(prec) / len(prec) if prec else 0):.0%} | Faithfulness Ø: {(sum(faith) / len(faith) if faith else 0):.2f}",
          "", "Judge = dasselbe Modell wie der Agent; bei lokalem 7B-Modell ist die Faithfulness-Note nur ein Hinweis."]
report = "\n".join(lines)
suffix = rag.MODEL.split(":", 1)[1].replace(":", "-") if rag.MODEL.startswith("ollama:") else rag.MODEL.split(":")[-1]
(ROOT / "evals" / f"report-{dt.date.today()}-k{K}-{suffix}.md").write_text(report, encoding="utf-8")
print(report)
