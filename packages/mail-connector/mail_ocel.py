"""Konnektor Test-Postfach → OCEL 2.0 JSON (WP7, Issue #24). Nur Standardbibliothek, nur lesen.

    uv run python mail_ocel.py <eml-ordner> <out.jsonocel> --erp ../../test-finance-agent/workspace/erp.db --eigene-domain firma.example

Quellen: ein Ordner mit .eml-Dateien oder ein IMAP-Postfach (read-only, BODY.PEEK setzt kein Gelesen-Flag).
Verknüpfung (SPEC-firmen-agent C 18): Rechnungsnummer in Betreff/Text → Rechnung; Kreditor über die Rechnung
im ERP, sonst über die Absender-Domain; Antworten ohne Nummer erben die Rechnung ihres Mailverlaufs.

Datenschutz (DSGVO, §87 BetrVG): Kein Betreff, kein Text, keine Adresse landet im Log. Personen erscheinen nur
als gesalzenes Pseudonym, Mailverläufe als Hash. Ausgewertet wird der Prozess, nicht die Person.
"""
import argparse
import email
import email.policy
import email.utils
import hashlib
import imaplib
import json
import re
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator

RECHNUNG = re.compile(r"\bRE-\d{4}-\d{4}\b")
# Reihenfolge = Vorrang: eine Mahnung nennt fast immer auch das Wort „Rechnung“.
THEMEN = [("Mahnung", r"mahnung|zahlungserinnerung"), ("Gutschrift", r"gutschrift"),
          ("Rückfrage", r"rückfrage|frage zu|unklar|bitte um klärung"), ("Rechnung", r"rechnung")]


def from_eml_dir(folder: Path) -> Iterator[bytes]:
    for p in sorted(folder.glob("*.eml")):
        yield p.read_bytes()


def from_imap(host: str, user: str, password: str, mailbox: str = "INBOX",
              imap_cls=imaplib.IMAP4_SSL) -> Iterator[bytes]:
    with imap_cls(host) as m:
        m.login(user, password)
        m.select(mailbox, readonly=True)
        _, data = m.search(None, "ALL")
        for num in data[0].split():
            _, msg = m.fetch(num, "(BODY.PEEK[])")
            yield msg[0][1]


def rechnungen_aus_erp(db: Path) -> dict[str, str]:
    """Rechnungsnummer → Kreditor-Nr. aus dem Test-ERP, read-only geöffnet."""
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        return dict(con.execute("SELECT nr, kreditor FROM rechnungen"))
    finally:
        con.close()


def _hash(salt: str, value: str) -> str:
    return hashlib.sha256(f"{salt}:{value.lower()}".encode()).hexdigest()[:10]


def _text(msg) -> str:
    part = msg.get_body(preferencelist=("plain", "html"))
    return part.get_content() if part else ""


def to_ocel(raw_mails: Iterable[bytes], salt: str, eigene_domain: str,
            rechnungen: dict[str, str], domain_kreditor: dict[str, str] | None = None) -> dict:
    """Jede Mail wird ein Event. Objekte: Rechnung, Kreditor (IDs wie im ERP), Mailverlauf, Person (Pseudonym)."""
    if not salt:
        raise ValueError("salt fehlt: ohne Salz sind die Pseudonyme per Wörterbuch umkehrbar")
    domain_kreditor = domain_kreditor or {}
    mails = []
    for raw in raw_mails:
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        mails.append((email.utils.parsedate_to_datetime(msg["Date"]), msg))
    mails.sort(key=lambda m: m[0])

    objects: dict[str, str] = {}             # id → type
    verlauf_rechnungen: dict[str, set[str]] = {}
    events = []
    for i, (ts, msg) in enumerate(mails, 1):
        absender = email.utils.parseaddr(msg["From"] or "")[1].lower()
        domain = absender.rpartition("@")[2]
        intern = domain == eigene_domain.lower()
        refs = (msg["References"] or "").split() or (msg["In-Reply-To"] or "").split()
        root = refs[0] if refs else (msg["Message-ID"] or f"ohne-id-{i}")
        verlauf = f"MV-{_hash(salt, root)}"
        betreff, text = msg["Subject"] or "", _text(msg)

        rnrs = {r for r in RECHNUNG.findall(f"{betreff}\n{text}") if r in rechnungen}
        rnrs |= verlauf_rechnungen.get(verlauf, set())            # Antwort ohne Nummer erbt den Verlauf
        verlauf_rechnungen.setdefault(verlauf, set()).update(rnrs)
        kreditoren = {rechnungen[r] for r in rnrs}
        if not intern and domain in domain_kreditor:
            kreditoren.add(domain_kreditor[domain])

        thema = next((t for t, pat in THEMEN if re.search(pat, f"{betreff}\n{text}", re.I)), "Mail")
        person = f"P-{_hash(salt, absender)}"
        rel = ([{"objectId": r, "qualifier": "betrifft"} for r in sorted(rnrs)]
               + [{"objectId": k, "qualifier": "Kreditor"} for k in sorted(kreditoren)]
               + [{"objectId": verlauf, "qualifier": "Teil von"},
                  {"objectId": person, "qualifier": "Absender"}])
        objects.update({r: "Rechnung" for r in rnrs} | {k: "Kreditor" for k in kreditoren}
                       | {verlauf: "Mailverlauf", person: "Person"})
        events.append({"id": f"mail-{i}", "type": f"{thema} {'gesendet' if intern else 'eingegangen'}",
                       "time": ts.isoformat(), "attributes": [{"name": "kanal", "value": "E-Mail"}],
                       "relationships": rel})

    return {
        "objectTypes": [{"name": t, "attributes": []} for t in sorted(set(objects.values()))],
        "eventTypes": [{"name": t, "attributes": [{"name": "kanal", "type": "string"}]}
                       for t in sorted({e["type"] for e in events})],
        "objects": [{"id": o, "type": t, "attributes": [], "relationships": []} for o, t in sorted(objects.items())],
        "events": events,
    }


if __name__ == "__main__":
    import os
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("eml_ordner", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--erp", type=Path, required=True)
    ap.add_argument("--eigene-domain", required=True)
    a = ap.parse_args()
    ocel = to_ocel(from_eml_dir(a.eml_ordner), os.environ["MAIL_PSEUDO_SALT"], a.eigene_domain, rechnungen_aus_erp(a.erp))
    a.out.write_text(json.dumps(ocel, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ocel['events'])} Events, {len(ocel['objects'])} Objekte → {a.out}")
