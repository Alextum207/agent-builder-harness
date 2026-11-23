# Spec: Offene Process-Intelligence-Plattform

Status: **ruht seit 2026-11-24**, abgelöst durch [`SPEC-handwerk-wissen.md`](SPEC-handwerk-wissen.md) (#28). Bleibt als Referenz für OCEL und die Agenten-Seite. Ursprünglich: Entwurf 2026-11-23 · Arbeitstitel, Name offen · baut auf `SPEC-firmen-agent.md` (Agenten-Seite) und dem fertigen Harness auf

## 1 Idee in einem Satz
Ein Mittelständler verbindet einmal seine Kanäle. Die Plattform macht daraus einen Prozess-Graphen, zeigt, wo Arbeit hängt und was sich automatisieren lässt, und baut für den besten Kandidaten einen Agenten. Der Agent beweist sich erst im Backtest und im Schattenmodus, bevor er allein arbeitet. Alles ist Open Source und selbst betreibbar.

## 2 Positionierung
Vergleichsmaßstab sind kommerzielle Process-Mining-Suiten wie Celonis. Keine Verbindung zu Celonis, der Name dient nur dem Vergleich.

| | Kommerzielle Suite | Diese Plattform |
|---|---|---|
| Zielgruppe | Konzern mit SAP und Datenteam | Mittelstand ohne Datenprojekt |
| Einstieg | Extraktionsprojekt mit Beratern | Kanäle verbinden: Postfach, Dokumente, Tickets, ERP-Datenbank lesend |
| Ergebnis | Prozessanalyse, Automationsbausteine | Prozessanalyse **plus** gebaute und geprüfte Agenten |
| Autonomie | wird konfiguriert | wird verdient: Backtest gegen Menschen, Schattenmodus, Freigabe pro Prozess |
| Betrieb | SaaS | Open Source, selbst betreibbar, EU-only oder lokal möglich |
| Mitbestimmung | Projektsache | Standard-Betriebsvereinbarung und Pseudonymisierung ab Werk |

Ehrliche Schwächen: weniger Tiefe im Process Mining, keine SAP-Standardkonnektoren, kein Vertrieb. Der Hebel ist Geschwindigkeit im Mittelstand und Offenheit.

## 3 Architektur
```text
 Kanäle ──► 1 Verbinden ──► 2 Event-Speicher (OCEL 2.0) ──► 3 Prozess-Erkennung ──► 4 Kandidaten
 (Mail, Docs,  Konnektoren    Objekte + Events,              Graph, Varianten,      Menge × Gleichförmigkeit
  Tickets, ERP) + Secrets      pseudonymisiert                Durchlaufzeiten        × geringes Risiko
                                                                                          │
 5 Task Mining (opt-in) ─────────────────────────────────────────────────────────────────┤
 „Zeig's mir“: Bildschirm + Sprache, nur freiwillig/BV                                    ▼
                                         7 Autonomie ◄── 6 Agent-Fabrik (build-agent-Harness)
                                         Backtest, Schatten, Freigabe, Rückstufung
```

| Schicht | Bausteine | Lizenz | Vorhanden im Repo |
|---|---|---|---|
| 1 Verbinden | [dlt](https://github.com/dlt-hub/dlt) für API-Quellen; eigene schlanke Konnektoren für IMAP/Graph, SQL read-only, Dateien | Apache-2.0 | Datei-Import (`company-brain`), ERP read-only (`test-finance-agent/erp.py`) |
| 2 Event-Speicher | OCEL 2.0 (Objekte, Events, Beziehungen) in SQLite/DuckDB, später Postgres; Pseudonymisierung beim Import | – | XES-artiger Event-Log-Export (`agent_guardrails.tracing`), P2P-Log (`erp.py`) |
| 3 Prozess-Erkennung | [pm4py](https://github.com/process-intelligence-solutions/pm4py) (OC-DFG, Varianten, Konformität); LLM benennt und erklärt nur, sieht Metadaten statt Rohdaten (Ansatz PMAx) | **AGPL-3.0** | – |
| 4 Kandidaten | Code: Menge × Gleichförmigkeit × Risiko (SPEC-firmen-agent E 27–30) | – | – |
| 5 Task Mining | [OpenAdapt](https://github.com/OpenAdaptAI/OpenAdapt) (Aufnahme von Klicks und Fenstern) plus Transkription | MIT | – |
| 6 Agent-Fabrik | `build-agent`, `agent-guardrails`, Evals, Company Brain | eigen | fertig |
| 7 Autonomie | Backtest mit exakter Binomial-Schranke, Schattenmodus, Rückstufung | – | Rechnung in `ANALYSE-ki-vs-algorithmus-nachrechnung.py` |

Nicht verwenden im Kern: Airbyte und Nango (ELv2, source-available).

## 4 MVP (Ziel: Demo in 6–8 Wochen)
Ein Durchstich auf erfundenen Daten, ohne UI-Politur:
1. Das Test-ERP (`erp.py`, 120 Rechnungen, 460 Events) und ein Test-Postfach werden zu einem OCEL-2.0-Log mit den Objekten Rechnung, Bestellung, Kreditor und Mail.
2. pm4py erkennt Prozess-Graph und Varianten. Der Report zeigt Häufigkeit, Durchlaufzeit und Engpässe, Bearbeiter nur als Pseudonym.
3. Die Kandidaten-Liste nennt die drei besten Automatisierungs-Kandidaten mit Begründung, als Rechnung und nicht als LLM-Meinung.
4. Für den besten Kandidaten baut `build-agent` einen Agenten mit Evals.
5. Der Backtest auf historischen Fällen zeigt Abdeckung und Fehlerquote gegen die Menschen, mit oberer Schranke.
6. Eine einfache Weboberfläche zeigt Graph, Kandidaten und Backtest. Ein Knopf „Schattenmodus starten“ folgt nach dem MVP.

Fertig, wenn der Durchstich mit einem Befehl auf den Testdaten läuft und jede Stufe einen Code-Test hat.

## 5 Leitplanken (gelten ab Zeile 1)
- Bewertet wird der Prozess oder der Agent, nie einzelne Beschäftigte. Keine Leistungsberichte über Personen (SPEC-firmen-agent D 22–23).
- Task Mining nur freiwillig (Start und Stopp durch die Person) oder mit Betriebsvereinbarung. Keine Kamera, keine Dauerüberwachung. Eine Vorlage für die Betriebsvereinbarung ist Teil des Produkts.
- KI zur Bauzeit, Code zur Laufzeit. Irreversible Aktionen nur nach Freigabe.
- Nur erfundene Daten im Repo. Konnektoren lesen standardmäßig nur.

## 6 Offene Entscheidungen (Nutzer)
1. **Lizenz des Repos:** Mit pm4py im Kern verlangt die AGPL-3.0, dass auch die Plattform AGPL-3.0 wird (Empfehlung). Alternative: pm4py nur als getrennter Dienst und der Rest Apache-2.0; das ist rechtlich zu prüfen. Bis zur Entscheidung gibt es keine LICENSE-Datei, und es gilt „alle Rechte vorbehalten“.
2. **Name** (kein fremder Markenname).
3. **UI-Stack:** FastAPI + schlankes Frontend (Empfehlung) oder Streamlit für die Demo.
4. **Erster echter Kanal nach dem Test-ERP:** Postfach (Empfehlung) oder Ticketsystem.
