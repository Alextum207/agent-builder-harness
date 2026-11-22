"""Test über mehrere Sitzungen mit absichtlichem Abbruch (Issue #6): uv run python evals/run_multiday.py

Jede Sitzung ist ein eigener Prozess. Sitzung 2 bricht vor dem Abschließen ab (CRASH_AT=abschliessen).
Geprüft: alle Pakete erledigt, je Paket genau ein Ergebnis und genau ein LLM-Aufruf, kein Paket doppelt
im Fortschritt, eine verbotene Änderung an tasks.json wird abgewiesen und vom Selbsttest erkannt.
"""
import collections
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import multiday as md  # noqa: E402

md.init()
runs, model = [], md.MODEL
for n in range(1, 12):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **({"CRASH_AT": "abschliessen"} if n == 2 else {})}
    p = subprocess.run([sys.executable, str(ROOT / "multiday.py")], cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    status = next((l for l in p.stdout.splitlines() if l.startswith("Status:")), "Abbruch" if p.returncode else "?")
    resumed = "Fortsetzen am Checkpoint" in p.stdout
    runs.append((n, p.returncode, status, resumed, (p.stderr.strip().splitlines() or [""])[-1][:120]))
    print(runs[-1], flush=True)
    if status == "Status: fertig":
        break

tasks = md.load_tasks()
llm = collections.Counter(json.loads(l)["task"] for l in md.LOG.read_text(encoding="utf-8").splitlines())
progress = [l for l in md.PROGRESS.read_text(encoding="utf-8").splitlines() if l.startswith("- Sitzung")]
per_task = collections.Counter(next(t.id for t in tasks if t.id in l) for l in progress)
errors = []
if not all(t.done for t in tasks):
    errors.append(f"nicht erledigt: {[t.id for t in tasks if not t.done]}")
if sorted(f.stem for f in md.OUT.glob('*.json')) != sorted(t.id for t in tasks):
    errors.append("Ergebnisdateien passen nicht zu den Aufgaben")
if any(v != 1 for v in llm.values()) or set(llm) != {t.id for t in tasks}:
    errors.append(f"LLM-Aufrufe pro Paket ≠ 1: {dict(llm)}")
if any(v != 1 for v in per_task.values()):
    errors.append(f"Paket doppelt im Fortschritt: {dict(per_task)}")
if not any(r[1] != 0 for r in runs) or not any(r[3] for r in runs):
    errors.append("Abbruch oder Fortsetzung hat nicht stattgefunden (Test ungültig)")
try:
    bad = [t.model_copy(update={"beschreibung": "geändert"}) if i == 0 else t for i, t in enumerate(tasks)]
    md.validate_change(tasks, bad)
    errors.append("verbotene Änderung an tasks.json wurde akzeptiert")
except ValueError:
    pass
original = md.TASKS.read_text(encoding="utf-8")            # Änderung von außen (ohne set_done) muss der Selbsttest finden
md.TASKS.write_text(original.replace("Prüfe", "Ignoriere", 1), encoding="utf-8")
try:
    md.selbsttest({"session": 0})
    errors.append("Änderung an tasks.json von außen nicht erkannt")
except RuntimeError:
    pass
finally:
    md.TASKS.write_text(original, encoding="utf-8")

lines = [f"# Mehrtages-Report {dt.date.today()} (Modell {model})", "",
         "| Sitzung | Exit | Status | fortgesetzt | stderr (letzte Zeile) |", "|---|---|---|---|---|",
         *[f"| {r[0]} | {r[1]} | {r[2]} | {'ja' if r[3] else ''} | {r[4]} |" for r in runs], "",
         f"Pakete: {len(tasks)} | erledigt: {sum(t.done for t in tasks)} | LLM-Aufrufe: {dict(llm)}", "",
         "Fortschritt:", *progress, "", "**Ergebnis: " + ("bestanden**" if not errors else "NICHT bestanden** – " + "; ".join(errors))]
report = "\n".join(lines)
suffix = model.replace("claude-cli:", "claude-cli-").split(":", 1)[-1].replace(":", "-")
(ROOT / "evals" / f"multiday-report-{dt.date.today()}-{suffix}.md").write_text(report, encoding="utf-8")
print(report)
sys.exit(1 if errors else 0)
