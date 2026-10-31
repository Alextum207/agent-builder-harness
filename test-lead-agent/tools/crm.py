"""Fake-CRM und Mailversand für den Test. Daten sind erfunden; Zustand liegt in workspace/."""
import json
from pathlib import Path
from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel, Field

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
CRM_FILE = WORKSPACE / "crm.json"
OUTBOX = WORKSPACE / "outbox.jsonl"

COMPANIES = {
    "acme-maschinenbau.de": {"name": "ACME Maschinenbau GmbH", "industry": "Maschinenbau", "employees": 450},
    "nordstahl-werke.de": {"name": "Nordstahl Werke AG", "industry": "Stahlindustrie", "employees": 1200},
    "baeckerei-huber.de": {"name": "Bäckerei Huber", "industry": "Lebensmittelhandwerk", "employees": 8},
    "techhandel24.de": {"name": "Techhandel24", "industry": "Onlinehandel", "employees": 60},
}


def ok(summary, data=None, next_actions=()):
    return {"status": "ok", "summary": summary, "data": data or {}, "next_actions": list(next_actions)}


def fail(error_type, summary, fix_hint):
    return {"status": "error", "error_type": error_type, "summary": summary, "fix_hint": fix_hint}


class LookupInput(BaseModel):
    domain: str = Field(description="Domain aus der Absenderadresse ohne 'www', z. B. 'acme-maschinenbau.de'")


@tool(args_schema=LookupInput)
def crm_company_lookup(domain: str) -> dict:
    """Schlägt Firmendaten (Name, Branche, Mitarbeiterzahl) zu einer E-Mail-Domain nach. Nur lesend."""
    domain = domain.lower().removeprefix("www.").strip()
    if "@" in domain:
        return fail("invalid_input", "Domain enthält '@'", "Nur den Teil nach '@' übergeben, z. B. domain='acme-maschinenbau.de'")
    company = COMPANIES.get(domain)
    if not company:
        return ok(f"Keine Firmendaten zu {domain}", {}, ["Nach E-Mail-Inhalt bewerten, im Zweifel B"])
    return ok(f"{company['name']}: {company['industry']}, {company['employees']} Mitarbeiter", company,
              ["crm_leads_set_score"])


class ScoreInput(BaseModel):
    lead_email: str = Field(description="Absenderadresse des Leads")
    tier: Literal["A", "B", "C"] = Field(description="A = kaufbereit, B = teilweise passend, C = kein Fit")
    reason: str = Field(max_length=300, description="Ein Satz Begründung")


@tool(args_schema=ScoreInput)
def crm_leads_set_score(lead_email: str, tier: str, reason: str) -> dict:
    """Setzt die Qualifizierungsstufe eines Leads im CRM. Überschreibt eine vorhandene Stufe (idempotent)."""
    WORKSPACE.mkdir(exist_ok=True)
    crm = json.loads(CRM_FILE.read_text(encoding="utf-8")) if CRM_FILE.exists() else {}
    crm[lead_email.lower()] = {"tier": tier, "reason": reason}
    CRM_FILE.write_text(json.dumps(crm, ensure_ascii=False, indent=2), encoding="utf-8")
    return ok(f"Lead auf Stufe {tier} gesetzt", {"tier": tier},
              ["mail_send mit Terminangebot"] if tier == "A" else ["Abschließend antworten"])


class MailInput(BaseModel):
    to: str = Field(description="Empfängeradresse (Absender des Leads)")
    subject: str = Field(max_length=120)
    body: str = Field(max_length=2000)


@tool(args_schema=MailInput)
def mail_send(to: str, subject: str, body: str) -> dict:
    """Sendet eine E-Mail. Irreversibel: läuft nur nach menschlicher Freigabe. Nur für Follow-ups an Stufe-A-Leads."""
    WORKSPACE.mkdir(exist_ok=True)
    with OUTBOX.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"to": to, "subject": subject, "body": body}, ensure_ascii=False) + "\n")
    return ok(f"E-Mail an {to} gesendet")
