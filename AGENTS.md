# AGENTS.md

Anleitung für Coding-Agenten (Claude Code, Codex, Cursor) in diesem Repo. Dokumentation und Kommentare sind auf Deutsch.

## Worum es geht
Zwei Ebenen in einem Repo:
1. **Harness** (fertig, mit Evals belegt): `build-agent`-Skill, zentrales Guardrails-Paket, Company Brain, vier Testagenten.
2. **Produkt** (Start): Wissen von der Baustelle für kleine Handwerksbetriebe. Der Meister filmt seine Arbeit mit dem Handy, die KI stellt danach höchstens 3 Nachfragen, und daraus entstehen Anleitungen und Job-Akten für die Einarbeitung. Gedacht als Hilfe auf der Baustelle, nicht als Bürotool. Plan: [`SPEC-handwerk-wissen.md`](SPEC-handwerk-wissen.md), nächste Schritte: [`HANDOFF.md`](HANDOFF.md), Issues mit Label `handwerk`. Die frühere Process-Intelligence-Spec ruht.

## Struktur
| Pfad | Inhalt |
|---|---|
| `setup-entwurf/build-agent/` | Skill-Entwurf: Ablauf, Referenzen, Ledger, Inbox. Installiert wird erst nach Freigabe. |
| `packages/agent-guardrails/` | Policy, Identität und Rechte, Tracing mit Event-Log-Export, Chatmodell über die Claude-CLI |
| `packages/mail-connector/` | Postfach (.eml oder IMAP, read-only) → OCEL 2.0 JSON, pseudonymisiert, verknüpft mit Rechnung und Kreditor |
| `company-brain/` | Dokumente → OKF-v0.3-Bundle (Docling, markitdown) |
| `test-finance-agent/` | Synthetisches ERP (SQLite, P2P-Event-Log), Recherche-Agent, Workflow, Memory, Mehrtages-Scaffold |
| `test-rag-agent/`, `test-lead-agent/` | RAG über das Brain; Lead-Agent mit Red-Teaming |
| `SPEC-handwerk-wissen.md` | Aktuelle Produkt-Spec: Video → Schritte → Nachfragen → Anleitung, Job-Akte, Assistent |
| `SPEC-open-process-intelligence.md`, `SPEC-firmen-agent.md` | Frühere Produkt-Specs, ruhen; Referenz für Agenten-Seite und OCEL |

## Befehle
Jedes Projekt hat eine eigene `uv`-Umgebung. Auf diesem Rechner immer setzen:
```bash
export UV_LINK_MODE=copy PYTHONIOENCODING=utf-8      # OneDrive verträgt keine Hardlinks; Windows-Konsole cp1252
env -u SSL_CERT_FILE uv sync --system-certs          # TLS-Proxy auf dem Rechner; im Code truststore.inject_into_ssl()
```
Tests ohne Modell (alle müssen grün sein, bevor etwas als fertig gilt):
```bash
cd packages/agent-guardrails && uv run python test_guardrails.py && uv run python evals/run_guardrail_evals.py --ci
cd test-finance-agent && uv run python test_memory.py
cd test-rag-agent && uv run python test_search.py
cd company-brain && uv run python test_ingest.py
cd packages/mail-connector && uv run python test_mail_ocel.py
```
Modell-Evals: Es gibt keinen gültigen API-Key. Läufe gehen über die Claude-Code-CLI mit `MODEL=claude-cli:haiku` (claude-haiku-5-5), lokale Modelle nicht verwenden. Beispiel: `MODEL=claude-cli:haiku uv run python evals/run_evals.py 3`.

## Regeln
- **Doku zuerst:** Vor Code gegen eine Library die aktuelle Doku holen (context7 oder offizielle Doku), Versionen nicht aus dem Gedächtnis.
- **Code statt Prompt:** Formate, Limits, Freigaben, Rechte im Code erzwingen. Irreversible Aktionen nur nach menschlicher Freigabe.
- **Fertig heißt gelaufen:** Tests oder Evals ausführen und das Ergebnis zeigen. Ein Lauf ohne Model-Calls ist ungültig, nicht bestanden.
- **Nur erfundene Daten:** in Tests, Evals und Fixtures; keine echten Personen- oder Kundendaten.
- **Mitarbeiterdaten:** Bewertet wird der Agent, der Prozess oder das Gerät, nie einzelne Beschäftigte (§87 BetrVG, DSGVO). Kein Endpunkt und kein Report liefert Zahlen pro Person.
- **Aufnahmen (Kamera, Ton):** nur zur Wissensweitergabe, nie zur Leistungskontrolle. Start und Stopp nur durch die aufnehmende Person. Alle Anwesenden und der Kunde wissen Bescheid und willigen ein. Gibt es einen Betriebsrat, nur mit Betriebsvereinbarung. Smalltalk- und Kunden-Abschnitte werden nach der Transkription gelöscht (§201 StGB). Das Rohvideo wird nach der Verarbeitung gelöscht, bis auf die Ausschnitte, die eine Anleitung braucht. Gesichter werden unkenntlich gemacht. Keine versteckten, fest montierten oder dauerhaft laufenden Kameras. Videos und Ton kommen nie ins Repo. Details: `SPEC-handwerk-wissen.md`, Abschnitt 10.
- **Lizenzen:** Vor jeder neuen Abhängigkeit die Lizenz im Repo prüfen (LICENSE-Datei, nicht Blogposts). Keine source-available-Lizenzen (ELv2, BSL, SSPL) im Produktkern.
- **Öffentliches Repo:** Nichts aus lokalen Ausschlüssen (`.git/info/exclude`) committen. Keine Secrets, `.env`, Logs, Traces, `workspace/`.
- **Marken:** Fremde Produktnamen nur als Vergleich, nie im eigenen Produktnamen.
- **Erkenntnisse:** Neue Learnings mit Beleg nach `setup-entwurf/build-agent/learnings/inbox.md`; ins Ledger erst nach Freigabe durch den Nutzer.
- **Git:** Nicht auf `main` committen; Branch, dann PR. Push und Merge nur auf Anweisung.
