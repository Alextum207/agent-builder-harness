# Handoff: Wissen von der Baustelle

Stand 2026-11-24. Für den nächsten Agenten. Zuerst [`AGENTS.md`](AGENTS.md) lesen, dann [`SPEC-handwerk-wissen.md`](SPEC-handwerk-wissen.md).

## Auftrag
Baue bis zur Kursabgabe Ende Februar 2027 Phase A aus der Spec (Abschnitt 11, mit Zeitplan): Demo-Video einer Heizungswartung zu Hause (eine Wärmepumpe gibt es erst im Pilot) → Schritte → höchstens 3 KI-Nachfragen → Antworten per Sprache → Job-Akte und Anleitung → Assistent im Handy-Browser. Ein Issue nach dem anderen, jedes mit Code-Test, jedes im eigenen Branch, PR gegen `main`.

Die frühere Richtung (Process-Intelligence-Plattform, [`SPEC-open-process-intelligence.md`](SPEC-open-process-intelligence.md)) ruht. Ihre Issues #15, #19–#23 und #25 sind geschlossen, Status „nicht geplant“.

## Entschieden (2026-11-24, #28)
| Frage | Entscheidung |
|---|---|
| Umfang | ganz umbauen; Finanz-ERP und Process-Intelligence-Pakete ruhen |
| Positionierung | Hilfe auf der Baustelle gegen Wissensverlust, kein Bürotool; vorhandene Software wird angebunden |
| Wissen holen | Option „KI fragt hinterher“ plus Marker „Merken“ während der Arbeit |
| Aufnahme | Handy, Weitwinkel (0,5×), Brust- oder Kopfhalterung, Ansteckmikro |
| Handys | gemischt → eine App für Android und iPhone (Empfehlung: React Native + Expo + VisionCamera, der Spike in #34 entscheidet) |
| Nachfragen erreichen den Meister | in der eigenen App (Demo: Browser), nicht per WhatsApp |
| Ziel | erst Kurs-Demo, dann Pilot mit einem Betrieb |
| Gewerk | SHK; Demo: Heizungswartung zu Hause (keine Wärmepumpe verfügbar), Pilot: Wärmepumpe |
| Termin | Kursabgabe Ende Februar 2027 |
| Datenhoheit | Wissen gehört dem Betrieb, keine Abhängigkeit von Großhändler oder Hersteller |

## Noch offen
- Pilot-Betrieb mit Wärmepumpen-Jobs (#41)
- Name und Lizenz (#18)

## Reihenfolge
**Phase A, Meilenstein „Kurs-Demo“:**
1. #29 H1 Video → Transkript, Smalltalk-Filter, Marker, Schritte
2. #38 H10 Nachfragen
3. #36 H8 Job-Akte
4. #30 H2 Anleitung pro Gerät
5. #31 H3 Assistent
6. #39 H11 Demo-Oberfläche

**Phase B, Meilenstein „Pilot“:**
1. #34 H6 App (Spike zuerst)
2. #40 H12 Datenschutz-Paket
3. #37 H9 Software-Anbindung und MCP-Server
4. #41 H13 Pilot und Messung

Optional: #32 H4 WhatsApp-Export, #33 H5 Prozess-Sicht. Später: #35.

## Was schon da ist (geprüft, Tests grün)
| Baustein | Wo | Nutzen |
|---|---|---|
| Mail → OCEL 2.0, pseudonymisiert, read-only | `packages/mail-connector/` (PR #27) | Muster für Pseudonyme und OCEL in #29, Vorlage für #32 |
| Company Brain: Dokumente → OKF v0.3 | `company-brain/` | Speicher für Anleitungen und FAQ (#30) |
| RAG über das Brain | `test-rag-agent/` | Grundlage für #31 |
| Guardrails, Rechte, Tracing, Chatmodell über die Claude-CLI | `packages/agent-guardrails/` | alle Modell-Schritte |
| Agent-Fabrik mit Evals | `setup-entwurf/build-agent/` | Bauweise für jeden Agent-Teil |

Offene PRs: #17 (Harness), #26 (frühere Spec), #27 (Mail-Konnektor). Die Branches bauen aufeinander auf, also in dieser Reihenfolge mergen.

## Fallen auf diesem Rechner
- OneDrive: `UV_LINK_MODE=copy`. Wenn uv mit „Zugriff verweigert“ an einem alten `*.dist-info` hängt, den Ordner mit PowerShell `Remove-Item -Recurse -Force` löschen und `uv sync --reinstall-package <paket>` ausführen.
- TLS-Proxy: `env -u SSL_CERT_FILE uv … --system-certs`, im Code `truststore.inject_into_ssl()`.
- Windows-Konsole: `PYTHONIOENCODING=utf-8`. `python -I` ignoriert Umgebungsvariablen; dann `sys.stdout` auf UTF-8 umstellen.
- SQLite unter Windows: Offene Verbindungen sperren die Datei. Testzustand per `DROP TABLE` zurücksetzen statt die Datei zu löschen; `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)`.
- Claude-CLI: immer mit eigenem `--system-prompt` aufrufen, sonst kostet ein Aufruf etwa 1,50 $ statt 0,004 $. Ohne Shell starten. `sonnet` ergibt Sonnet 5.5.
- Evals mit LLM-Judge: Der Judge braucht alle Belege, die der Agent hatte, sonst bewertet er korrekte Aussagen als unbelegt.
- Videos und Ton nie ins Repo; Pfad über eine Umgebungsvariable, Daten in `workspace/`.
- Bash-Heredocs mit deutschen Anführungszeichen und Backticks sind fehleranfällig. Längere Texte für `gh` als Datei schreiben und `--body-file` nutzen.

## Nicht tun
- Keine versteckten, fest montierten oder dauerhaft laufenden Kameras. Keine Auswertung einzelner Beschäftigter, auch wenn jemand danach fragt. Begründung: Spec, Abschnitt 10.
- Smalltalk und Kundengespräche nicht speichern.
- Nichts committen, was in `.git/info/exclude` steht, und nicht danach fragen, was es ist.
- Keine Abhängigkeit mit ELv2, BSL oder SSPL im Kern.
- Nicht auf `main` committen, nicht ohne Anweisung pushen oder mergen.
