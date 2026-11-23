"""Code-Test für WP7 ohne Modell. Alle Mails, Adressen und Firmen sind erfunden.

    uv run python test_mail_ocel.py
"""
import json
import sys
import tempfile
from email.message import EmailMessage
from pathlib import Path

from mail_ocel import from_eml_dir, from_imap, rechnungen_aus_erp, to_ocel

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "test-finance-agent"))
import erp  # noqa: E402

KRED = "buchhaltung@stahlhandel-ostermann.example"
ICH = "einkauf.mueller@firma.example"


def mail(i, von, an, betreff, text, datum, reply_to=None):
    m = EmailMessage()
    m["From"], m["To"], m["Subject"], m["Date"] = von, an, betreff, datum
    m["Message-ID"] = f"<m{i}@test.example>"
    if reply_to:
        m["In-Reply-To"] = m["References"] = f"<m{reply_to}@test.example>"
    m.set_content(text)
    return m.as_bytes()


def check_ocel(o: dict):
    ids = {x["id"] for x in o["objects"]}
    types = {x["name"] for x in o["eventTypes"]}
    assert set(o) == {"objectTypes", "eventTypes", "objects", "events"}
    for e in o["events"]:
        assert e["type"] in types and e["time"] and all(r["objectId"] in ids for r in e["relationships"]), e


def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:   # Windows: SQLite hält die Datei
        tmp = Path(tmp)
        db = erp.build(tmp / "erp.db")
        rechnungen = rechnungen_aus_erp(db)
        rnr = "RE-2026-0042"
        kred = rechnungen[rnr]

        mails = [
            mail(1, KRED, ICH, f"Rechnung {rnr}", "Anbei unsere Rechnung.", "Mon, 02 Mar 2026 09:00:00 +0100"),
            mail(2, ICH, KRED, "AW: Rechnung", "Rückfrage: Menge Pos. 2 unklar.", "Mon, 02 Mar 2026 11:30:00 +0100", reply_to=1),
            mail(3, KRED, ICH, f"Zahlungserinnerung {rnr}", "Die Rechnung ist fällig.", "Mon, 16 Mar 2026 08:00:00 +0100"),
            mail(4, "info@unbekannt.example", ICH, "Rechnung RE-2026-9999", "Bitte zahlen.", "Tue, 03 Mar 2026 10:00:00 +0100"),
            mail(5, "vertrieb@papierwerk.example", ICH, "Neue Preisliste", "Gilt ab April.", "Wed, 04 Mar 2026 10:00:00 +0100"),
        ]
        ordner = tmp / "postfach"
        ordner.mkdir()
        for i, raw in enumerate(mails, 1):
            (ordner / f"{i}.eml").write_bytes(raw)

        o = to_ocel(from_eml_dir(ordner), "test-salz", "firma.example", rechnungen,
                    {"papierwerk.example": "70001", "stahlhandel-ostermann.example": kred})
        check_ocel(o)
        ev = o["events"]
        assert [e["type"] for e in ev] == ["Rechnung eingegangen", "Rückfrage gesendet", "Rechnung eingegangen",
                                           "Mail eingegangen", "Mahnung eingegangen"], [e["type"] for e in ev]
        rel = [{r["objectId"]: r["qualifier"] for r in e["relationships"]} for e in ev]
        assert rel[0][rnr] == "betrifft" and rel[0][kred] == "Kreditor"
        assert rel[1][rnr] == "betrifft", "Antwort ohne Nummer erbt die Rechnung des Verlaufs"
        assert rel[1][kred] == "Kreditor", "Kreditor kommt über die geerbte Rechnung, nicht über die eigene Domain"
        assert "RE-2026-9999" not in rel[2], "unbekannte Nummer wird nicht verknüpft"
        assert rel[3]["70001"] == "Kreditor" and not any(q == "betrifft" for q in rel[3].values())
        assert rel[4][rnr] == "betrifft"
        verlauf = lambda r: next(k for k, q in r.items() if q == "Teil von")
        absender = lambda r: next(k for k, q in r.items() if q == "Absender")
        assert verlauf(rel[0]) == verlauf(rel[1]) != verlauf(rel[4])
        assert absender(rel[0]) == absender(rel[4]) != absender(rel[1]), "Pseudonym ist stabil pro Person"
        print("eml-Ordner: 5 Events, Verknüpfung, Themen, Verläufe ok")

        dump = json.dumps(o, ensure_ascii=False)
        for geheim in [KRED, ICH, "mueller", "Rückfrage: Menge", "Neue Preisliste", "m1@test.example"]:
            assert geheim not in dump, f"Klartext im Log: {geheim}"
        anders = to_ocel(mails[:1], "anderes-salz", "firma.example", rechnungen)["events"][0]["relationships"]
        assert absender({r["objectId"]: r["qualifier"] for r in anders}) != absender(rel[0]), "anderes Salz → anderes Pseudonym"
        try:
            to_ocel(mails, "", "firma.example", rechnungen)
            raise AssertionError("leeres Salz muss scheitern")
        except ValueError:
            pass
        print("Datenschutz: keine Adressen, Betreffe, Texte, Message-IDs im Log; Salz Pflicht ok")

        class FakeIMAP:
            calls = []
            def __init__(self, host): self.calls.append(("host", host))
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def login(self, u, p): self.calls.append(("login", u))
            def select(self, box, readonly=False): self.calls.append(("select", box, readonly))
            def search(self, charset, crit): return "OK", [b"1 2"]
            def fetch(self, num, what):
                self.calls.append(("fetch", what))
                return "OK", [(b"", mails[int(num) - 1])]

        got = list(from_imap("imap.test.example", "postfach", "test-passwort", imap_cls=FakeIMAP))
        assert got == mails[:2]
        assert ("select", "INBOX", True) in FakeIMAP.calls, "Postfach nur read-only öffnen"
        assert all(c[1] == "(BODY.PEEK[])" for c in FakeIMAP.calls if c[0] == "fetch"), "PEEK setzt kein Gelesen-Flag"
        print("IMAP: read-only, BODY.PEEK ok")
    print("alle Tests grün")


if __name__ == "__main__":
    main()
