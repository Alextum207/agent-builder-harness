# Handoff: Start der offenen Process-Intelligence-Plattform

Stand 2026-11-23. Für den nächsten Agenten. Erst lesen: [`AGENTS.md`](AGENTS.md), dann [`SPEC-open-process-intelligence.md`](SPEC-open-process-intelligence.md).

## Auftrag
Baue den MVP-Durchstich aus der Spec, Abschnitt 4: Test-ERP und Test-Postfach → OCEL 2.0 → Prozess-Erkennung mit pm4py → Kandidaten → Agent → Backtest → einfache Oberfläche. Ein Arbeitspaket nach dem anderen, jedes mit Code-Test, im eigenen Branch, PR gegen `main`.

## Was schon da ist (geprüft, Tests grün)
| Baustein | Wo | Nutzen für den MVP |
|---|---|---|
| Synthetisches ERP: 8 Kreditoren, 120 Rechnungen, 22 Bestellungen, 460 P2P-Events mit Varianten (Preisabweichung, Freigabe > 5.000 EUR, Sperre), Bearbeiter pseudonymisiert | `test-finance-agent/erp.py` | Quelle für WP2; die Varianten sind bekannt, die Erkennung lässt sich also prüfen |
| Event-Log-Export aus Agent-Traces (XES-Spalten) | `packages/agent-guardrails/agent_guardrails/tracing.py` | Agent-Schritte landen im selben Log wie menschliche |
| Company Brain: Dokumente → OKF v0.3 | `company-brain/ingest.py` | Dokumente als Quelle, Wissen für Agenten |
| Agent-Fabrik mit Evals, Guardrails, Rechten, Traces | `setup-entwurf/build-agent/`, `packages/agent-guardrails/` | WP5 |
| Backtest-Mathematik (exakte Binomial-Schranke) | `ANALYSE-ki-vs-algorithmus-nachrechnung.py` | WP6 |
| Chatmodell über die Claude-CLI | `agent_guardrails.claude_cli.chat_model("claude-cli:haiku")` | Alle Modell-Läufe; es gibt keinen API-Key |

Belege: Retros in `test-finance-agent/`, `test-rag-agent/`, `test-lead-agent/`; PR [#17](https://github.com/Alextum207/agent-builder-harness/pull/17) (Issues #1–#9, CI grün, noch nicht gemerged).

## Zuerst vom Nutzer entscheiden lassen (blockiert WP2/WP3)
1. **Lizenz:** pm4py ist AGPL-3.0 (LICENSE-Datei im Repo geprüft am 2026-11-23). Empfehlung: das ganze Repo AGPL-3.0. Ohne Entscheidung keine pm4py-Abhängigkeit einbauen.
2. **Name** des Produkts (kein fremder Markenname).
3. Die übrigen Punkte aus Spec Abschnitt 6 haben einen empfohlenen Standard und sind nicht blockierend.

## Arbeitspakete (Reihenfolge)
| WP | Inhalt | Fertig, wenn |
|---|---|---|
| WP1 | Lizenz und Name eintragen (LICENSE, README, `THIRD_PARTY_NOTICES.md` um pm4py, OpenAdapt, dlt ergänzen) | Nutzer hat entschieden, Dateien im PR |
| WP2 | Paket `packages/process-store`: OCEL-2.0-Modell (Pydantic), Konverter aus `erp.py` (Objekttypen Rechnung, Bestellung, Kreditor), Export nach OCEL 2.0 JSON/SQLite, Pseudonymisierung beim Import | Code-Test: Anzahl Events und Objekte stimmt mit `erp.py`; Export lädt in pm4py |
| WP3 | Paket `packages/process-discovery`: OC-DFG und Varianten mit pm4py, Durchlaufzeiten, Engpässe; Report als Markdown | Code-Test: Die erkannten Varianten entsprechen den Regeln im Generator (mit/ohne Bestellung, Preisabweichung, Freigabe, Sperre) |
| WP4 | Kandidaten-Score im Code: Menge × Gleichförmigkeit × geringes Risiko, Top 3 mit Begründung | Code-Test auf den Testdaten; LLM nur für Formulierungen |
| WP5 | Für den Top-Kandidaten einen Agenten mit `build-agent` bauen (Muster, Evals, Guardrails, Rechte) | Evals mit k=3 grün, RETRO.md |
| WP6 | Backtest: Agent auf historischen Fällen gegen menschliche Entscheidungen; Abdeckung, Fehlerquote, obere Schranke | Report mit Schranke; Agent nur auf dem Anteil autonom, den der Backtest deckt |
| WP7 | Konnektor Test-Postfach (IMAP gegen lokale Mails oder `.eml`-Ordner) → OCEL-Events mit Bezug zu Rechnungen | Code-Test mit erfundenen Mails |
| WP8 | Einfache Weboberfläche: Graph, Kandidaten, Backtest | Lokal startbar, ein Klick zeigt den Durchstich |
| WP9 | Task Mining „Zeig's mir“ mit OpenAdapt, nur opt-in, Vorlage für die Betriebsvereinbarung | erst nach dem MVP |

GitHub-Issues (Label `mvp`): WP1 [#18](https://github.com/Alextum207/agent-builder-harness/issues/18), WP2 [#19](https://github.com/Alextum207/agent-builder-harness/issues/19), WP3 [#20](https://github.com/Alextum207/agent-builder-harness/issues/20), WP4 [#21](https://github.com/Alextum207/agent-builder-harness/issues/21), WP5 [#22](https://github.com/Alextum207/agent-builder-harness/issues/22), WP6 [#23](https://github.com/Alextum207/agent-builder-harness/issues/23), WP7 [#24](https://github.com/Alextum207/agent-builder-harness/issues/24), WP8 [#25](https://github.com/Alextum207/agent-builder-harness/issues/25).

## Fallen auf diesem Rechner
- OneDrive: `UV_LINK_MODE=copy`. Wenn uv mit „Zugriff verweigert“ an einem alten `*.dist-info` hängt, den Ordner mit PowerShell `Remove-Item -Recurse -Force` löschen und `uv sync --reinstall-package <paket>` ausführen.
- TLS-Proxy: `env -u SSL_CERT_FILE uv … --system-certs`, im Code `truststore.inject_into_ssl()`.
- Windows-Konsole: `PYTHONIOENCODING=utf-8`; `python -I` ignoriert Umgebungsvariablen, dann `sys.stdout` auf UTF-8 umstellen.
- SQLite unter Windows: offene Verbindungen sperren die Datei. Testzustand per `DROP TABLE` zurücksetzen, nicht die Datei löschen.
- Claude-CLI: immer mit eigenem `--system-prompt` aufrufen, sonst kostet ein Aufruf etwa 1,50 $ statt 0,004 $. Ohne Shell starten. `sonnet` ergibt Sonnet 5.5; Sonnet 4.6 und der 1M-Kontext sind nicht verfügbar.
- Evals mit dem LLM-Judge: Der Judge braucht alle Belege, die der Agent hatte, inklusive Absender und Freigabe-Ergebnissen. Sonst bewertet er korrekte Aussagen als unbelegt.

## Nicht tun
- Keine Kameras, keine Dauerüberwachung, keine Auswertung einzelner Beschäftigter, auch wenn jemand danach fragt. Begründung in Spec Abschnitt 5.
- Nichts committen, was in `.git/info/exclude` steht (lokale, unveröffentlichte Daten des Nutzers), und nicht danach fragen, was es ist.
- Keine Abhängigkeit mit ELv2, BSL oder SSPL im Kern.
- Nicht auf `main` committen und nicht ohne Anweisung pushen oder mergen.

## Offene Punkte aus dem Harness (nicht blockierend)
Issues #10–#16: API-Gegenlauf (#10), Inbox-Freigabe (#11), zweite Guardrail-Schicht (#12), Node-Evals mit k (#13), Live-Konnektoren (#14), ERP-Bedeutungsschicht (#15, passt zu WP2), Branch-Schutz und Judge-Kalibrierung (#16).
