# AGENTS.md

Anleitung für Coding-Agenten (Claude Code, Codex, Cursor) in diesem Repo. Dokumentation und Kommentare sind auf Deutsch.

## Worum es geht
Zwei Ebenen in einem Repo:
1. **Harness** (fertig, mit Evals belegt): `build-agent`-Skill, zentrales Guardrails-Paket, Company Brain, vier Testagenten.
2. **Produkt** (Start): offene Process-Intelligence-Plattform für den Mittelstand. Sie verbindet Systeme, erkennt Prozesse, findet Automatisierungs-Kandidaten und baut dafür geprüfte Agenten. Plan: [`SPEC-open-process-intelligence.md`](SPEC-open-process-intelligence.md), nächste Schritte: [`HANDOFF.md`](HANDOFF.md).

## Struktur
| Pfad | Inhalt |
|---|---|
| `setup-entwurf/build-agent/` | Skill-Entwurf: Ablauf, Referenzen, Ledger, Inbox. Installiert wird erst nach Freigabe. |
| `packages/agent-guardrails/` | Policy, Identität und Rechte, Tracing mit Event-Log-Export, Chatmodell über die Claude-CLI |
| `company-brain/` | Dokumente → OKF-v0.3-Bundle (Docling, markitdown) |
| `test-finance-agent/` | Synthetisches ERP (SQLite, P2P-Event-Log), Recherche-Agent, Workflow, Memory, Mehrtages-Scaffold |
| `test-rag-agent/`, `test-lead-agent/` | RAG über das Brain; Lead-Agent mit Red-Teaming |
| `SPEC-firmen-agent.md` | Ursprüngliche Produkt-Spec (124 Anforderungen); gilt weiter für die Agenten-Seite |

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
```
Modell-Evals: Es gibt keinen gültigen API-Key. Läufe gehen über die Claude-Code-CLI mit `MODEL=claude-cli:haiku` (claude-haiku-5-5), lokale Modelle nicht verwenden. Beispiel: `MODEL=claude-cli:haiku uv run python evals/run_evals.py 3`.

## Regeln
- **Doku zuerst:** Vor Code gegen eine Library die aktuelle Doku holen (context7 oder offizielle Doku), Versionen nicht aus dem Gedächtnis.
- **Code statt Prompt:** Formate, Limits, Freigaben, Rechte im Code erzwingen. Irreversible Aktionen nur nach menschlicher Freigabe.
- **Fertig heißt gelaufen:** Tests oder Evals ausführen und das Ergebnis zeigen. Ein Lauf ohne Model-Calls ist ungültig, nicht bestanden.
- **Nur erfundene Daten:** in Tests, Evals und Fixtures; keine echten Personen- oder Kundendaten.
- **Mitarbeiterdaten:** Bewertet wird der Agent oder der Prozess, nie einzelne Beschäftigte (§87 BetrVG, DSGVO). Task Mining und Aufnahmen nur freiwillig oder mit Betriebsvereinbarung, pseudonymisiert. Keine Dauerüberwachung, keine Kameras.
- **Lizenzen:** Vor jeder neuen Abhängigkeit die Lizenz im Repo prüfen (LICENSE-Datei, nicht Blogposts). Keine source-available-Lizenzen (ELv2, BSL, SSPL) im Produktkern.
- **Öffentliches Repo:** Nichts aus lokalen Ausschlüssen (`.git/info/exclude`) committen. Keine Secrets, `.env`, Logs, Traces, `workspace/`.
- **Marken:** Fremde Produktnamen nur als Vergleich, nie im eigenen Produktnamen.
- **Erkenntnisse:** Neue Learnings mit Beleg nach `setup-entwurf/build-agent/learnings/inbox.md`; ins Ledger erst nach Freigabe durch den Nutzer.
- **Git:** Nicht auf `main` committen; Branch, dann PR. Push und Merge nur auf Anweisung.
