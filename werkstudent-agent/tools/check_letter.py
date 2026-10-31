"""Prüft ein Anschreiben hart: Belege, Lebenslauf-Wiederholung, Struktur, Sie-Form, Mail-Länge.

uv run python tools/check_letter.py workspace/letters/<id>.md     Exit 0 = ok, 1 = Fehler (Liste auf stdout)

Format der Datei (Schlüssel am Zeilenanfang, Inhalt bis zum nächsten Schlüssel):
ID: <job-id>            SPRACHE: de|en          AN: <E-Mail aus der Anzeige oder leer>
EMPFAENGER: / DATUM: / BETREFF: / ANREDE: / TEXT: / GRUSS: / BELEGE: P3, M2 / MAIL_BETREFF: / MAIL:
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFIL = ROOT / "context" / "profil.md"
KEYS = ["ID", "SPRACHE", "AN", "EMPFAENGER", "DATUM", "BETREFF", "ANREDE", "TEXT", "GRUSS", "BELEGE", "MAIL_BETREFF", "MAIL"]
# Begriffe, die eine Behauptung tragen: dürfen nur vorkommen, wenn Profil oder Anzeige sie nennen
TECH = """python java javascript typescript sql nosql r scala go rust c++ c# excel vba power bi powerbi tableau qlik looker
spark hadoop databricks snowflake dbt airflow kafka docker kubernetes aws azure gcp google cloud sap s/4hana abap
celonis signavio uipath aris pafnow apromore pm4py langchain langgraph llamaindex crewai autogen openai chatgpt gpt claude
gemini mistral llama hugging face pytorch tensorflow keras scikit-learn sklearn pandas numpy fastapi flask django react
node n8n make zapier lovable codex playwright selenium twilio websockets rest graphql git github gitlab jira salesforce
hubspot servicenow camunda bpmn power automate rpa mlops ml devops kaggle""".split()
TECH_MULTI = ["power bi", "hugging face", "google cloud", "power automate", "s/4hana"]
DU = re.compile(r"\b(du|dich|dir|dein|deine|deinen|deinem|deiner|euch|euer|eure)\b", re.I)


def parse(text: str) -> dict:
    parts = re.split(r"^(" + "|".join(KEYS) + r"):", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower())


def shingles(s: str, n=5) -> set:
    w = re.findall(r"\w+", s.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def check(path: Path) -> list[str]:
    d = parse(path.read_text(encoding="utf-8"))
    err = [f"Feld fehlt: {k}" for k in KEYS if k != "AN" and not d.get(k)]
    if err:
        return err
    profil = PROFIL.read_text(encoding="utf-8")
    cv = profil.split("## Lebenslauf (Wortlaut", 1)[1]
    posting_files = [p for p in (ROOT / "workspace" / "postings").glob(f"{d['ID']}*.txt")]
    if not posting_files:
        return [f"Keine Quelle workspace/postings/{d['ID']}*.txt (Anzeige oder Firmenseite) gefunden"]
    quellen = norm(profil + "\n".join(p.read_text(encoding="utf-8") for p in posting_files))
    behauptung = "\n".join(d[k] for k in ("EMPFAENGER", "BETREFF", "TEXT", "MAIL_BETREFF", "MAIL"))
    low = norm(behauptung)

    # 1 Zahlen müssen belegt sein (Datum der Kopfzeile ausgenommen)
    for z in sorted(set(re.findall(r"\d+(?:[.,]\d+)*", behauptung))):
        if not re.search(rf"(?<![\w.,]){re.escape(z)}(?![\d]|[.,]\d)", quellen):
            err.append(f"Zahl ohne Beleg: {z}")
    # 2 Tech-/Tool-Namen müssen belegt sein
    for t in TECH_MULTI + TECH:
        if re.search(r"(?<![\w/])" + re.escape(t) + r"(?![\w/])", low) and not re.search(r"(?<![\w/])" + re.escape(t) + r"(?![\w/])", quellen):
            err.append(f"Begriff ohne Beleg: {t}")
    # 3 Eigennamen: Akronyme, CamelCase, Wörter mit Ziffern, „bei/at X“ müssen belegt sein
    namen = set(re.findall(r"\b[A-ZÄÖÜ]{2,}(?=\b|-)|\b[A-Za-z]+[a-z][A-Z]\w*\b|\b\w*\d\w*[A-Za-z]\w*\b", behauptung))
    namen |= set(re.findall(r"\b(?:bei|at)\s+([A-ZÄÖÜ][\w&-]+)", behauptung)) - {"Ihnen", "Ihrem", "Ihrer", "Ihr", "Ihre", "your", "you"}
    for n in sorted(namen):
        if norm(n).strip(".-") not in quellen:
            err.append(f"Name ohne Beleg: {n}")
    # 4 Belege-IDs müssen im Profil existieren
    for b in re.findall(r"[PML]\d+", d["BELEGE"]):
        if not re.search(rf"\*\*{b}[ :]", profil):
            err.append(f"Beleg-ID existiert nicht: {b}")
    # 5 Lebenslauf nicht nacherzählen
    cv_sh = shingles(cv)
    saetze = [s for s in re.split(r"(?<=[.!?])\s+", d["TEXT"]) if len(s.split()) >= 6]
    nah = [s for s in saetze if len(shingles(s)) and len(shingles(s) & cv_sh) / len(shingles(s)) > 0.3]
    if any(len(shingles(s) & cv_sh) / len(shingles(s)) > 0.5 for s in nah) or len(nah) > 1:
        err.append(f"Zu nah am Lebenslauf-Wortlaut ({len(nah)} Satz/Sätze): " + " | ".join(s[:70] for s in nah))
    stationen = [s.strip() for s in re.search(r"## Stationen.*?\n(.+?)\n", profil, re.S).group(1).split("|")]
    genannt = [s for s in stationen if s.lower() in d["TEXT"].lower()]
    if len(genannt) > 3:
        err.append(f"Zu viele Stationen ({len(genannt)} > 3): {', '.join(genannt)}")
    # 6 Struktur, Ton, Länge
    if re.match(r"\s*betreff", d["BETREFF"], re.I):
        err.append("Betreffzeile beginnt mit „Betreff“")
    if d["SPRACHE"] == "de" and (m := DU.findall(behauptung)):
        err.append(f"Du-Form statt Sie: {sorted(set(m))}")
    w = len(d["TEXT"].split())
    if not 150 <= w <= 380:
        err.append(f"Anschreiben-Text {w} Wörter (erlaubt 150–380, eine Seite)")
    n_mail = len([s for s in re.split(r"(?<=[.!?])\s+", d["MAIL"]) if s.strip()])
    if not 4 <= n_mail <= 6:
        err.append(f"Mail hat {n_mail} Sätze (erlaubt 4–6)")
    # 7 Empfänger-Adresse nur wörtlich aus der Quelle
    if d.get("AN") and d["AN"].lower() not in quellen:
        err.append(f"E-Mail-Adresse steht nicht in der Anzeige/Firmenseite: {d['AN']}")
    return err


if __name__ == "__main__":
    errors = check(Path(sys.argv[1]))
    print("OK" if not errors else "\n".join("FEHLER: " + e for e in errors))
    sys.exit(1 if errors else 0)
