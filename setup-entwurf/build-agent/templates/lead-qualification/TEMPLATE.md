---
status: entwurf
projekte: [C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent]
getestet: langchain 1.4.5, langgraph 1.2.15, langchain-anthropic 1.7.6, claude-haiku-5-5
---
# Template: Lead-Qualifizierung

Bewertet eingehende Lead-E-Mails (A/B/C), schreibt die Stufe ins CRM, schlägt bei A eine Follow-up-Mail vor (nur nach Freigabe).

## Verwenden
1. Ordner ins neue Projekt kopieren, `uv sync` (bei Zertifikatsfehlern: `env -u SSL_CERT_FILE uv sync --system-certs`).
2. Platzhalter ersetzen: `grep -rn "<[A-Z_]*>" .` muss danach leer sein (außer `<lead_email>`).
3. `tools/crm.py`: Fake-CRM und Fake-Mailversand durch echte Anbindung ersetzen; Tool-Vertrag und Pydantic-Schemas beibehalten, `mail_send` bleibt in `IRREVERSIBLE`.
4. `evals/cases.jsonl`: erfundene Beispielfälle durch eigene (weiterhin erfundene, keine echten Personendaten) ersetzen; mindestens Normal-, Grenz-, Fehler- und Injection-Fall.
5. `.env` mit `ANTHROPIC_API_KEY` anlegen, `uv run --system-certs python evals/run_evals.py 1`.

## Ergebnis im Ursprungsprojekt
pass@3 100 %, pass^3 kritisch 100 % (n=6, k=3, erfundene Daten), 0,0008 $/Lauf, 3–4 Model-Calls.

## Nicht enthalten
Deploy (Webhook, persistenter Checkpointer, Freigabe per Link): siehe `references/deploy.md`.
