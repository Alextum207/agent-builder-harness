# Tools

## Inhalt
- Tool-Auswahl
- Tool-Vertrag (Schema, Rückgabe, Fehler)
- Beispiel
- Granularität und Risiko
- Anti-Patterns

## Tool-Auswahl (Quelle: A2, A3)
- Wenige, durchdachte Tools für die wichtigsten Abläufe; erweitern nur bei beobachtetem Bedarf.
- Nicht jede API-Route einzeln wrappen: mehrstufige Abläufe zu einem Tool bündeln (z. B. `crm_find_or_create_lead` statt `search` + `create`).
- Gezielte Suche statt Datendump.
- Jedes Tool hat einen eindeutigen Zweck; wenn ein Mensch nicht sagen könnte, welches Tool passt, kann es der Agent auch nicht.
- Namen mit Präfix nach System und Ressource: `crm_leads_search`, `mail_send`.

## Tool-Vertrag
**Eingabe:** immer ein Pydantic-Modell mit Feldbeschreibungen und Grenzen (`max_length`, `Literal`, `ge/le`). Eindeutige Feldnamen (`user_id` statt `user`). Fehlerträchtiges unmöglich machen, z. B. Enums statt Freitext (Quelle: A1 „poka-yoke“).

**Rückgabe:** immer ein Dict in diesem Format:
```python
{"status": "ok" | "warning" | "error",
 "summary": "ein Satz, was passiert ist",
 "data": {...},                    # nur aussagekräftige Felder, keine UUID-Wüsten
 "next_actions": ["..."]}          # was der Agent sinnvoll als Nächstes tun kann
```
**Fehler:** gleiches Format mit `status: "error"` plus `error_type` und `fix_hint` mit einem korrekten Beispielaufruf. Keine Tracebacks, keine nackten Fehlercodes (Quelle: A2, F9).

**Große Ausgaben:** kürzen, mit Hinweis wie weiter eingrenzen/paginieren (`"summary": "50 von 812 Treffern, nutze filter=..."`). Bei Tools mit großen Antworten ein Feld `response_format: Literal["knapp", "ausführlich"]` (Standard knapp); sehr große Ergebnisse nach `workspace/` schreiben und nur Pfad plus Kurzfassung zurückgeben (context.md).

**Retries:** max. 3, nur bei vorübergehenden Fehlern (Netzwerk, Rate-Limit, 5xx). Bei Auth- oder Validierungsfehlern sofort abbrechen.

**Idempotenz:** Schreibende Tools nehmen einen `idempotency_key` oder arbeiten per Upsert, damit ein Wiederholungsaufruf keinen Schaden anrichtet.

## Beispiel
```python
from typing import Literal
from pydantic import BaseModel, Field
from langchain.tools import tool

def ok(summary, data=None, next_actions=()):
    return {"status": "ok", "summary": summary, "data": data or {}, "next_actions": list(next_actions)}

def fail(error_type, summary, fix_hint):
    return {"status": "error", "error_type": error_type, "summary": summary, "fix_hint": fix_hint}

class ScoreInput(BaseModel):
    lead_id: str = Field(description="CRM-ID des Leads, z. B. 'L-1042'")
    tier: Literal["A", "B", "C"] = Field(description="A = kaufbereit, B = interessiert, C = kalt")
    reason: str = Field(max_length=300)

@tool(args_schema=ScoreInput)
def crm_leads_set_score(lead_id: str, tier: str, reason: str) -> dict:
    """Setzt die Qualifizierungsstufe eines Leads im CRM. Überschreibt eine vorhandene Stufe (idempotent)."""
    ...
    return ok(f"Lead {lead_id} auf {tier} gesetzt", {"lead_id": lead_id, "tier": tier},
              ["mail_draft_followup, falls tier == 'A'"])

TOOLS = [crm_leads_set_score]
IRREVERSIBLE = {"mail_send"}          # → Freigabe, siehe scaffold.md
```

## Beschreibungen
Wie für einen neuen Junior-Entwickler: was das Tool tut, wann man es nimmt und wann nicht, Abgrenzung zu ähnlichen Tools, ein Beispiel. Kleine Verbesserungen an Beschreibungen bringen oft große Effekte (Quelle: A2).

## Granularität und Risiko
| Risiko | Beispiele | Regel |
|---|---|---|
| lesend | suchen, abrufen | frei |
| reversibel schreibend | Entwurf speichern, Feld setzen | frei, idempotent |
| irreversibel | senden, zahlen, löschen, deployen | eigenes kleines Tool, in `IRREVERSIBLE`, Freigabe |
| Code/Shell/Netzwerk frei | Shell, beliebige URL | vermeiden; wenn nötig siehe security.md |

## Anti-Patterns
- Viele Tools mit überlappender Bedeutung.
- Regeln wie „nutze immer Tool X“ nur im Prompt statt im Code.
- Fehler ohne Hinweis auf den nächsten Schritt.
- Rohe API-Antworten ungefiltert in den Kontext.

## Tools prüfen
Tools mit echten, mehrstufigen Aufgaben testen; Transkripte lesen: viele redundante Aufrufe deuten auf fehlende Filter/Pagination, falsche Parameter auf unklare Beschreibungen (Quelle: A2).
