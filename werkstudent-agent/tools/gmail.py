"""Gmail: Entwurf anlegen oder Entwurf senden. Beide Aufrufe stehen in .claude/settings.json unter `ask`,
d. h. Claude Code fragt Alexander vor JEDEM Aufruf. Zusätzlich prüft der Code selbst:

uv run python tools/gmail.py draft <id>                       Entwurf mit Anschreiben-PDF + Lebenslauf
uv run python tools/gmail.py send <id> --confirm <id>         sendet den Entwurf aus workspace/letters/<id>.draft
"""
import truststore; truststore.inject_into_ssl()
import base64, csv, subprocess, sys
from email.message import EmailMessage
from pathlib import Path
from check_letter import parse

ROOT = Path(__file__).resolve().parent.parent
LETTERS, SECRETS = ROOT / "workspace" / "letters", ROOT / ".secrets"
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]   # Entwürfe + Senden, kein Lesen
CV = {"de": ROOT / "context" / "cv" / "Lebenslauf_Alexander_Saade_v-final.pdf",
      "en": ROOT / "context" / "cv" / "Lebenslauf_Alexander_Saade_EN.pdf"}


def service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    token, creds = SECRETS / "token.json", None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(str(SECRETS / "credentials.json"), SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def set_status(i: str, status: str):
    tracker = ROOT / "workspace" / "tracker.csv"
    with tracker.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r["id"] == i:
            r["status"] = status
    with tracker.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def draft(i: str, svc=None) -> str:
    md = LETTERS / f"{i}.md"
    check = subprocess.run([sys.executable, str(ROOT / "tools" / "check_letter.py"), str(md)], capture_output=True, text=True)
    if check.returncode:                       # fail closed: nur geprüfte Anschreiben
        sys.exit("Abbruch, check_letter nicht grün:\n" + check.stdout)
    d = parse(md.read_text(encoding="utf-8"))
    if not d.get("AN"):
        sys.exit("Abbruch: keine E-Mail-Adresse in der Anzeige → Bewerbung über das Portal.")
    pdf, cv = md.with_suffix(".pdf"), CV[d["SPRACHE"]]
    for f in (pdf, cv):
        if not f.exists():
            sys.exit(f"Abbruch: Anlage fehlt: {f}")
    msg = EmailMessage()
    msg["To"], msg["Subject"] = d["AN"], d["MAIL_BETREFF"]
    msg.set_content(d["MAIL"])
    name = "Anschreiben" if d["SPRACHE"] == "de" else "Cover_Letter"
    msg.add_attachment(pdf.read_bytes(), "application", "pdf", filename=f"{name}_Alexander_Saade.pdf")
    msg.add_attachment(cv.read_bytes(), "application", "pdf", filename=cv.name)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    res = (svc or service()).users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    (LETTERS / f"{i}.draft").write_text(res["id"], encoding="utf-8")
    set_status(i, "entwurf")
    return res["id"]


def send(i: str, confirm: str, svc=None) -> str:
    if confirm != i:                           # zweites, ausdrückliches OK pro Mail
        sys.exit("Abbruch: --confirm muss genau die Job-ID wiederholen.")
    f = LETTERS / f"{i}.draft"
    if not f.exists():
        sys.exit("Abbruch: kein Entwurf zu dieser ID. Zuerst `draft`.")
    res = (svc or service()).users().drafts().send(userId="me", body={"id": f.read_text().strip()}).execute()
    set_status(i, "gesendet")
    return res["id"]


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "draft":
        print("Entwurf angelegt:", draft(a[1]))
    elif len(a) == 4 and a[0] == "send" and a[2] == "--confirm":
        print("Gesendet:", send(a[1], a[3]))
    else:
        sys.exit(__doc__)
