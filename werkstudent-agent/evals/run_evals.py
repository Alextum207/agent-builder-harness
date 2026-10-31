"""Code-Evals für werkstudent-agent. uv run python evals/run_evals.py [k]  → evals/report-<datum>-k<k>.md
Nicht parallel zu scrape.py laufen lassen (Tracker wird kurz durch einen Testzustand ersetzt)."""
import json, shutil, sys, time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_letter, gmail, scrape  # noqa: E402

FIX, POSTINGS, LETTERS = ROOT / "evals" / "fixtures", ROOT / "workspace" / "postings", ROOT / "workspace" / "letters"
CLEAN = (FIX / "clean.md").read_text(encoding="utf-8")


class FakeGmail:  # zählt Aufrufe statt zu senden
    def __init__(self): self.calls = []
    def users(self): return self
    def drafts(self): return self
    def create(self, **kw): self.calls.append("create"); return self
    def send(self, **kw): self.calls.append("send"); return self
    def execute(self): return {"id": "fake-1"}


def letter(c) -> str:
    text = CLEAN
    for old, new in c["replace"]:
        assert old in text, f"Fixture-Ersatz nicht gefunden: {old}"
        text = text.replace(old, new)
    p = LETTERS / "evaltest.md"
    p.write_text(text, encoding="utf-8")
    errs = check_letter.check(p)
    return "ok" if not errs else " | ".join(errs)


def gmail_case(c) -> str:
    fake = FakeGmail()
    (LETTERS / "evaltest.draft").unlink(missing_ok=True)
    (LETTERS / "evaltest.pdf").write_bytes(b"%PDF-1.4 test")
    md = LETTERS / "evaltest.md"
    md.write_text(CLEAN if c["action"] != "draft_bad" else CLEAN.replace("eine Stunde", "7 Stunden"), encoding="utf-8")
    try:
        if c["action"] == "send":
            (LETTERS / "evaltest.draft").write_text("fake-draft")
            gmail.send("evaltest", c["confirm"], svc=fake)
        else:
            gmail.draft("evaltest", svc=fake)
    except SystemExit:
        pass
    return "keine_wirkung" if not fake.calls else ("entwurf" if fake.calls == ["create"] else ",".join(fake.calls))


def run_case(c) -> tuple[bool, str]:
    t = c["type"]
    if t == "filter":
        got = scrape.passt({**c["input"], "text": ""})
        return got == c["expect"], str(got)
    if t == "felder":
        got = scrape.felder(c["input"])
        return all(got[k] == v for k, v in c["expect"].items()), json.dumps(got, ensure_ascii=False)
    if t == "letter":
        got = letter(c)
        return (got == "ok") if c["expect"] == "ok" else (c["expect"] in got), got
    if t == "gmail":
        got = gmail_case(c)
        return got == c["expect"], got
    if t == "mask":
        got = scrape.mask(c["input"])
        return c["expect"] not in got, got
    raise ValueError(t)


def main(k=1):
    LETTERS.mkdir(parents=True, exist_ok=True)
    POSTINGS.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / "posting.txt", POSTINGS / "evaltest.txt")
    tracker_backup = scrape.TRACKER.read_bytes() if scrape.TRACKER.exists() else None
    scrape.TRACKER.write_text("id,status\nevaltest,anschreiben\n", encoding="utf-8")
    cases = [json.loads(l) for l in (ROOT / "evals" / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows, crit_fail = [], 0
    try:
        for c in cases:
            results = []
            for _ in range(k):
                t0 = time.time()
                try:
                    ok, got = run_case(c)
                except Exception as e:  # Ausnahme = nicht bestanden
                    ok, got = False, f"EXCEPTION {e}"
                results.append((ok, got, time.time() - t0))
            passed = sum(r[0] for r in results)
            crit_fail += bool(c.get("critical") and passed < k)
            rows.append((c["id"], c.get("critical", False), passed, k, results[-1][1][:160], results[-1][2]))
    finally:
        for f in ("evaltest.md", "evaltest.pdf", "evaltest.draft"):
            (LETTERS / f).unlink(missing_ok=True)
        (POSTINGS / "evaltest.txt").unlink(missing_ok=True)
        if tracker_backup is None:
            scrape.TRACKER.unlink(missing_ok=True)
        else:
            scrape.TRACKER.write_bytes(tracker_backup)
    n_ok = sum(r[2] == r[3] for r in rows)
    lines = [f"# Eval-Report {date.today()} (k={k}, Code-Grader; deterministische Tools, keine Model-Calls)", "",
             f"Bestanden: {n_ok}/{len(rows)} | kritisch nicht bestanden: {crit_fail}", "",
             "| Fall | kritisch | bestanden | Latenz | Ergebnis |", "|---|---|---|---|---|"]
    lines += [f"| {i} | {'ja' if cr else ''} | {p}/{kk} | {lat * 1000:.0f} ms | {g.replace('|', '/')} |" for i, cr, p, kk, g, lat in rows]
    report = ROOT / "evals" / f"report-{date.today()}-k{k}.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(1 if crit_fail else 0)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
