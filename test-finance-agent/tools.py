"""ERP-Tools des Recherche-Agenten. Vertrag: status/summary/data/next_actions (references/tools.md)."""
import datetime as dt
from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel, Field

import erp

# Welche Rechte jedes Tool braucht (Issue #8). Fehlt ein Tool hier, blockiert PermissionMiddleware es.
TOOL_SCOPES = {
    "erp_kreditor": ("erp", "read"),
    "erp_rechnungen_offen": ("erp", "read"),
    "erp_rechnung": ("erp", "read"),
    "erp_korrekturen": ("erp", "read"),
    "erp_buchung_anlegen": ("erp", "write"),
}
WRITE = False   # setzt agent.py aus der Identität; ohne Schreibrecht ist die DB read-only geöffnet


def ok(summary, data=None, next_actions=()):
    return {"status": "ok", "summary": summary, "data": data or {}, "next_actions": list(next_actions)}


def fail(error_type, summary, fix_hint):
    return {"status": "error", "error_type": error_type, "summary": summary, "fix_hint": fix_hint}


class KreditorIn(BaseModel):
    nr: str = Field(description="Kreditorennummer, fünfstellig, z. B. '70004'")


@tool(args_schema=KreditorIn)
def erp_kreditor(nr: str) -> dict:
    """Stammdaten eines Kreditors: Name, IBAN, USt-ID, Zahlungsziel, Standardkonto. Nur lesend."""
    r = erp.connect(WRITE).execute("SELECT * FROM kreditoren WHERE nr=?", (nr.strip(),)).fetchone()
    if not r:
        return fail("not_found", f"Kreditor {nr} unbekannt", "Nummer prüfen; Kreditoren liegen zwischen 70001 und 70008")
    return ok(f"Kreditor {nr}: {r['name']}", dict(r))


@tool(args_schema=KreditorIn)
def erp_rechnungen_offen(nr: str) -> dict:
    """Nummern der offenen Rechnungen eines Kreditors, ohne Beträge. Beträge mit erp_rechnung abrufen."""
    rows = erp.connect(WRITE).execute("SELECT nr FROM rechnungen WHERE kreditor=? AND status='offen' ORDER BY nr", (nr.strip(),)).fetchall()
    return ok(f"{len(rows)} offene Rechnungen", {"rechnungen": [r["nr"] for r in rows]}, ["erp_rechnung pro Nummer"])


class RechnungIn(BaseModel):
    nr: str = Field(description="Rechnungsnummer, z. B. 'RE-2026-0042'")


@tool(args_schema=RechnungIn)
def erp_rechnung(nr: str) -> dict:
    """Rechnungskopf mit allen Positionen. Ist `korrigiert` true, gilt der Betrag aus erp_korrekturen."""
    con = erp.connect(WRITE)
    r = con.execute("SELECT nr, kreditor, bestellung, datum, betrag, status, korrigiert FROM rechnungen WHERE nr=?", (nr.strip(),)).fetchone()
    if not r:
        return fail("not_found", f"Rechnung {nr} unbekannt", "Format RE-2026-0001 bis RE-2026-0120")
    pos = [dict(p) for p in con.execute("SELECT pos, bezeichnung, menge, einzelpreis, notiz FROM positionen WHERE rechnung=?", (nr,))]
    data = {**dict(r), "korrigiert": bool(r["korrigiert"]), "positionen": pos}
    return ok(f"Rechnung {nr}: {r['betrag']:.2f} EUR brutto, {r['status']}", data,
              ["erp_korrekturen"] if r["korrigiert"] else [])


@tool(args_schema=RechnungIn)
def erp_korrekturen(nr: str) -> dict:
    """Korrekturen (Gutschriften, Preisänderungen) zu einer Rechnung. Der neueste Eintrag gilt."""
    rows = [dict(r) for r in erp.connect(WRITE).execute("SELECT * FROM korrekturen WHERE rechnung=? ORDER BY datum", (nr.strip(),))]
    if not rows:
        return ok(f"Keine Korrektur zu {nr}", {"korrekturen": []})
    return ok(f"Gültiger Betrag {rows[-1]['neuer_betrag']:.2f} EUR ({rows[-1]['grund']})", {"korrekturen": rows})


class BuchungIn(BaseModel):
    beleg: str = Field(description="Rechnungsnummer")
    konto: str = Field(description="Sachkonto aus dem Kontenplan, z. B. '4930'")
    betrag: float = Field(gt=0, lt=1_000_000)


@tool(args_schema=BuchungIn)
def erp_buchung_anlegen(beleg: str, konto: str, betrag: float) -> dict:
    """Legt eine Buchung im ERP an. Schreibend und irreversibel im Echtsystem: nur mit Freigabe und Schreibrecht."""
    con = erp.connect(WRITE)
    con.execute("INSERT INTO buchungen VALUES (?,?,?,?,?)", (beleg, konto, betrag, f"{dt.date.today()}", "agent"))
    con.commit()
    return ok(f"Buchung {beleg} auf {konto} über {betrag:.2f} EUR angelegt")


TOOLS = [erp_kreditor, erp_rechnungen_offen, erp_rechnung, erp_korrekturen, erp_buchung_anlegen]
