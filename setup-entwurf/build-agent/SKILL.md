---
name: build-agent
description: Builds, audits, and evaluates LLM agents and LLM workflows in Python with LangGraph/LangChain - scaffold, tools, human approval, evals, cost control - and learns from every project to make future builds more reliable and cheaper. Use when the user wants to build, create, or set up an agent, assistant, bot, or automated LLM workflow, or wants to audit or evaluate an existing one.
---

# Build Agent

## Trigger
- Neuer Agent, Bot, Assistent oder LLM-Workflow (Modus `build`, Standard).
- Bestehenden Agent prüfen (Modus `audit`) oder nur Evals erstellen/laufen lassen (Modus `eval`).
- Modus aus der Anfrage oder dem Argument ableiten (`/build-agent audit`).
- **Nicht** auslösen für einen einzelnen LLM-Aufruf ohne Schleife und ohne Tools: den Aufruf einfach schreiben.

## Vor jeder Phase: Gelerntes laden
1. Kontext-Tag der Aufgabe bestimmen (kebab-case, z. B. `lead-qualification`). Vorhandene Tags: `grep -o "kontext: [a-z-]*" learnings/ledger.md | sort -u`.
2. Nur passende Einträge lesen, nie das ganze Ledger: `grep -A1 -E "kontext: (<tag>|allgemein|tools|evals|kosten|sicherheit) " learnings/ledger.md`.
3. Falls vorhanden: `domains/<kontext>.md` lesen und `templates/<kontext>/` als Ausgangscode nutzen statt neu zu generieren.

## Modus `build`
Checkliste kopieren und abhaken:
```
- [ ] 1 Klären            → references/clarify-and-pattern.md
- [ ] 2 Muster wählen     → references/clarify-and-pattern.md
- [ ] 3 Scaffold          → references/scaffold.md
- [ ] 4 Tools & Kontext   → references/tools.md, references/context.md (+ references/mcp.md, falls ein MCP-Server entsteht)
- [ ] 5 Sicherheit        → references/security.md
- [ ] 6 Evals definieren  → references/evals.md   (vor jedem Prompt-Tuning)
- [ ] 7 Kosten & Caching  → references/cost-and-caching.md
- [ ] 8 Ausführen         → Evals laufen lassen, Ergebnis + ein Log zeigen
- [ ] 9 Deploy            → references/deploy.md  (nur bei dauerhaftem Betrieb)
- [ ] 10 Retro            → references/retro.md   (immer; ohne RETRO.md ist der Build nicht fertig)
```

## Modus `audit`
`references/audit.md`, dazu `references/security.md` und `references/tools.md` als Prüfmaßstab. Keine Code-Änderung vor Freigabe des Fix-Plans.

## Modus `eval`
Nur `references/evals.md`.

## Harte Regeln (alle Phasen)
- **Stack:** Python, LangChain `create_agent` für Tool-Agents, LangGraph `StateGraph` für Workflows, Pydantic für Schemas, fastmcp für MCP-Server, `uv` für Abhängigkeiten.
- **Doku zuerst:** Vor Code mit einer Library die aktuelle Doku über context7 (oder offizielle Doku) holen. Code-Beispiele in diesen Referenzen sind Muster, keine API-Garantie.
- **Code statt Prompt:** Was eingehalten werden muss (Formate, Limits, Freigaben, verbotene Aktionen), wird im Code erzwungen. Prompts sind nur Ratschläge.
- **Freigabe:** Irreversible Aktionen (senden, zahlen, löschen, deployen) laufen nur nach menschlicher Freigabe.
- **Fertig heißt gelaufen:** Nie „fertig“ melden ohne ausgeführte Evals und gezeigtes Ergebnis.
- **Einfach vor autonom:** Workflow vor Agent, kleiner Agent vor großem (Quelle: A1, F10).
- **Vorrang:** Während eines Builds führt dieser Skill. Andere Skills (z. B. `tdd`, `prototype`) nur gezielt innerhalb einer Phase. Minimalismus-Regeln (z. B. ponytail) gelten für den Agent-Code selbst, aber Evals, Logs, Limits, Freigaben und Retro sind Pflichtteile und kein Over-Engineering.
- **Personendaten:** keine echten Personen- oder Kundendaten in Evals, Templates, Ledger (security.md „DSGVO“).

## Edge cases
- Projekt hat schon eine Struktur: anpassen, keine Ordner doppeln.
- Nutzer will TypeScript: Muster übertragen, Stack-Regel gilt dann nicht.
- context7 nicht verfügbar: offizielle Doku per WebFetch.
- Kein API-Key für Evals: Evals schreiben, Lauf als „nicht ausgeführt“ melden, nicht als bestanden. Ausweg mit Claude-Abo: `MODEL=claude-cli:haiku` über `agent_guardrails.claude_cli` (Text-Protokoll für Tools, im Report so kennzeichnen).

## Erfolgsmetrik
- Alle Checklistenpunkte abgehakt (Deploy ggf. begründet ausgelassen), Evals ausgeführt und Ergebnis gezeigt.
- Projekt enthält Struktur, Logs eines echten Laufs und `RETRO.md`. Fehlt `RETRO.md`, ist der Build nicht fertig.
- Mindestens ein belegter Vorschlag in `learnings/inbox.md` oder die begründete Aussage „keine neue Erkenntnis“.

## Evaluation
- Checkliste vollständig? Eval-Report vorhanden? Ein Log mit allen Feldern pro Schritt?
- Freigabe-Test: Eine irreversible Aktion ohne Freigabe hinterlässt keine Wirkung.

Quellen: `references/sources.md`.
