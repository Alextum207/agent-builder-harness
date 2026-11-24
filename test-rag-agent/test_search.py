"""Selbsttest Suche und Router-Absicherung ohne Model-Calls: uv run python test_search.py"""
import rag


def top(*begriffe, frage=""):
    return [(round(s, 2), c["doc"].rsplit("/", 1)[1]) for s, c in rag._bewertet(list(begriffe), frage)[:4]]


for b in (["Hotel"], ["Hotelzimmer", "Hamburg"]):
    print(b, top(*b))
    assert rag.suche(b, 4)[0]["doc"].endswith("reisekosten-2026.md.md"), b
print(["Kilometerpauschale"], top("Kilometerpauschale"))
assert not rag.belegt(["Kilometerpauschale"]), "fehlt-Fall darf keinen starken Beleg haben"
frage = "Wie hoch ist die Kilometerpauschale für Fahrten mit dem Privatauto?"
print("fehlt", top("Kilometerpauschale", "Privatauto", frage=frage))
assert not rag.belegt(["Kilometerpauschale", "Privatauto"], frage)
assert rag._woerter("die für mit wie ist pro Hotel") == {"hotel"}  # Füllwörter zählen nicht

# Router: Rechnen bleibt ohne Suche, Richtlinienfrage wird trotz "ohne_suche" gesucht
assert rag.modus_pruefen("ohne_suche", ["Umsatzsteuer", "netto"], "Wie viel sind 19 % Umsatzsteuer auf 200 EUR netto?") == "ohne_suche"
assert rag.modus_pruefen("ohne_suche", ["Hotelzimmer", "Nacht"], "Wie viel darf ein Hotelzimmer pro Nacht kosten?") == "eine_suche"
assert rag.modus_pruefen("ohne_suche", ["Bewirtung", "Kunden"], "Bis zu welchem Betrag wird eine Bewirtung erstattet?") == "eine_suche"
assert rag.modus_pruefen("mehrstufig", [], "x") == "mehrstufig"

# Unbelegte Zitate → Übergabetext statt der unbelegten Antwort
z = rag.zitate_pruefen({"treffer": [], "zitate": ["erfunden#0"], "antwort": "110 EUR"})
assert z["ergebnis"] == "mensch" and z["antwort"] == rag.UEBERGABE, z
print("ok")
