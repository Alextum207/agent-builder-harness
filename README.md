# Agent Builder Harness

Ein Claude-Code-Skill, der LLM-Agenten nach festem Ablauf baut, prüft und aus jedem Projekt lernt. Dazu ein zentrales Guardrails-Paket, ein Company Brain für Firmenwissen und vier damit gebaute Agenten.

**Nächster Schritt:** Auf diesem Harness entsteht ein Werkzeug gegen den Wissensverlust im Handwerk. Der Meister filmt seine Arbeit mit dem Handy, ohne dabei etwas zu erklären. Danach stellt die KI ihm höchstens drei kurze Fragen, die er per Sprache beantwortet. Daraus entstehen Anleitungen und Job-Akten mit Material, die neue Leute auf der Baustelle per Sprache oder Foto abfragen. Es hilft auf der Baustelle und ist kein Bürotool; vorhandene Handwerker-Software wird angebunden. Plan: [`SPEC-handwerk-wissen.md`](SPEC-handwerk-wissen.md), Übergabe: [`HANDOFF.md`](HANDOFF.md).

Ohne Harness legt Claude bei jedem Agenten frei los: ohne feste Struktur, ohne Evals und oft mit veralteten APIs aus dem Gedächtnis. `build-agent` gibt dafür eine Checkliste vor. Erkenntnisse aus einem Projekt gehen nach Freigabe in ein Ledger und stehen dem nächsten Build zur Verfügung.

Die Dokumentation ist auf Deutsch. Hinweise für Coding-Agenten: [`AGENTS.md`](AGENTS.md).

## Inhalt

| Pfad | Was | Stand |
|---|---|---|
| [`setup-entwurf/build-agent/`](setup-entwurf/build-agent/SKILL.md) | Der Skill: Referenzen, Ledger, Template | im Einsatz |
| [`setup-entwurf/write-skill/`](setup-entwurf/write-skill/SKILL.md) | Skill zum Schreiben weiterer Skills | im Einsatz |
| [`setup-entwurf/SPEC-build-agent.md`](setup-entwurf/SPEC-build-agent.md) | Spezifikation des Skills | fertig |
| [`test-lead-agent/`](test-lead-agent/RETRO.md) | Qualifiziert B2B-Leads; mit zentralen Guardrails, Traces und Promptfoo-Red-Teaming | erfundene Daten |
| [`werkstudent-agent/`](werkstudent-agent/README.md) | Sucht Werkstudentenstellen und prüft Anschreiben per Code | ohne persönliche Daten |
| [`company-brain/`](company-brain/AGENTS.md) | Liest Firmendokumente (Docling-Parser) als Bundle im Open Knowledge Format ein, Agenten suchen per grep | Selbsttest grün |
| [`packages/agent-guardrails/`](packages/agent-guardrails/agent_guardrails/__init__.py) | Zentrales Paket für alle Agenten: Policy 0.3.0 (Injection, PII, Freigabeliste, Rate-Limit), Identität und Rechte, OpenTelemetry-Traces mit Event-Log-Export, Chatmodell über die Claude-CLI | Selbsttest + Guardrail-Evals grün, CI-Workflow |
| [`test-finance-agent/`](test-finance-agent/RETRO.md) | Synthetisches ERP (SQLite, P2P-Event-Log), Recherche-Agent mit Kontext-Evals, Rechnungs-Workflow mit Node-Report, Memory, Mehrtages-Scaffold | erfundene Daten |
| [`test-rag-agent/`](test-rag-agent/RETRO.md) | Agentic/Adaptive RAG über ein Company-Brain-Bundle mit Ausgang „Mensch“ | erfundene Dokumente |
| [`SPEC-handwerk-wissen.md`](SPEC-handwerk-wissen.md) | Produkt: Handy-Video → Schritte → KI-Nachfragen → Anleitung, Job-Akte, Assistent auf der Baustelle | Entwurf, Phase A geplant |
| [`packages/mail-connector/`](packages/mail-connector/mail_ocel.py) | Postfach (.eml oder IMAP, read-only) → OCEL 2.0, pseudonymisiert | Code-Test grün |
| [`HANDOFF.md`](HANDOFF.md) | Übergabe an den nächsten Agenten: Stand, Entscheidungen, Reihenfolge | aktuell |
| [`SPEC-open-process-intelligence.md`](SPEC-open-process-intelligence.md) | Frühere Richtung: Kanäle → OCEL 2.0 → Prozess-Erkennung → Kandidaten → Agenten | ruht |
| [`SPEC-firmen-agent.md`](SPEC-firmen-agent.md) | Agenten-Seite: lernt Firmenprozesse und verdient sich Autonomie (124 Anforderungen) | Entwurf |
| [`ANALYSE-ki-vs-algorithmus.md`](ANALYSE-ki-vs-algorithmus.md) | Wo braucht das Produkt KI, wo reicht Code? Mit [Nachrechnung](ANALYSE-ki-vs-algorithmus-nachrechnung.py) | Analyse |

## So arbeitet `build-agent`

Der Skill hat drei Modi: `build` (Standard), `audit` und `eval`. Ein Build läuft in zehn Schritten:

```text
Klären → Muster wählen → Scaffold → Tools → Sicherheit → Evals definieren
       → Kosten & Caching → Ausführen → Deploy (bei Dauerbetrieb) → Retro
                                                                      │
       Ledger, Playbooks, Templates  ◄── nach Freigabe ◄── Vorschläge ┘
```

Vor jeder Phase lädt der Skill nur die Erkenntnisse, die zum Kontext passen. Seine wichtigsten Regeln:

- **Code statt Prompt:** Formate, Limits und Freigaben werden im Code erzwungen.
- **Freigabe:** Irreversible Aktionen laufen nur nach menschlichem OK.
- **Fertig heißt gelaufen:** Ein Build gilt erst mit ausgeführten Evals und einer `RETRO.md` als fertig.
- **Doku zuerst:** Vor dem Code wird die aktuelle Library-Doku geholt.
- **Einfach vor autonom:** Ein Workflow geht vor einem Agenten, ein kleiner Agent vor einem großen.

Der Stack ist Python, LangChain `create_agent`, LangGraph, Pydantic, fastmcp und `uv`.

## Ergebnisse

Stand 2026-11-22: Alle Modell-Läufe mit `claude-haiku-5-5` liefen über die Claude-Code-CLI (`MODEL=claude-cli:haiku`), weil kein gültiger API-Key vorlag. Tool-Calls liefen dabei über ein Text-Protokoll statt über native Tool-Use; mit API-Key einmal über `MODEL=anthropic:claude-haiku-5-5` gegenprüfen. Die Kosten laut CLI lagen bei zusammen rund 0,21 $ für 466 Aufrufe.

| Projekt | Lauf | Ergebnis |
|---|---|---|
| `test-lead-agent` | n=8, k=3 ([Retro](test-lead-agent/RETRO.md)) | pass@1 100 %, pass^3 kritisch 100 % |
| `test-lead-agent` | Red-Teaming, 10 Angriffe und Kontrollfälle über `agent.run()` (Promptfoo) | 10/10: keine erzwungene Stufe A, keine Mail an fremde Adressen |
| `test-finance-agent` | Kontext-Evals n=9, k=3 ([Retro](test-finance-agent/RETRO.md)) | pass@1 100 %; Token-Druck mit Zusammenfassung nur 2/3, mit `clear` 3/3 |
| `test-finance-agent` | dasselbe lokal mit `qwen2:7b` | pass@1 56 %; vergifteter Kontext 0/6 |
| `test-finance-agent` | Rechnungs-Workflow, n=12 | Nodes 100 % / 100 %, Kette 92 % |
| `test-finance-agent` | Memory über 4 Sitzungen, k=3 · Mehrtages-Lauf mit Abbruch | 3/3 · bestanden, kein Paket verloren oder doppelt |
| `test-rag-agent` | n=8, k=3 ([Retro](test-rag-agent/RETRO.md)) | pass^3 kritisch 100 %; Widerspruch und fehlende Info → Mensch 6/6; Faithfulness Ø 3,73 von 4 |
| `packages/agent-guardrails` | 55 gelabelte Fälle ([Report](packages/agent-guardrails/evals/report-2026-11-22.md)) | Injection P 1,00 / R 0,88; PII P 1,00 / R 0,86 |
| `test-lead-agent` | 2026-10-13: n=6, k=3, API | pass@3 100 %, 0,00084 $ pro Lauf |
| `werkstudent-agent` | 22 Code-Evals ohne Model-Calls ([Report](werkstudent-agent/evals/report-2026-10-31-k1.md)) | 22/22 |

Die Fallzahlen sind klein und die Daten erfunden. Quoten sind deshalb nur Hinweise. Belastbarer sind die reproduzierbaren Bugs aus den Retros, etwa:
- Ein Telefon-Muster zerstörte JSON-Logs.
- Ein eigener Wrapper-Tag machte jeden Lauf „tainted“.
- Die Herkunft im Memory ließ sich per Zitat fälschen.
- Bei parallelen Tool-Aufrufen ließ sich die Taint-Sperre umgehen.

Die Erkenntnisse daraus warten in der [Inbox](setup-entwurf/build-agent/learnings/inbox.md) auf Freigabe fürs Ledger.

Zwei Regex-Lücken bleiben bewusst offen: semantische Injection ohne Schlüsselwort und verschleierte E-Mail-Adressen. Gegen Injection schützen dort Rechte, Freigaben und Taint, nicht der Detektor.

## Loslegen

Skill installieren (Bash, [Claude Code](https://claude.com/claude-code) vorausgesetzt):

```bash
cp -r setup-entwurf/build-agent ~/.claude/skills/
```

Danach reicht in Claude Code ein Satz wie „Bau mir einen Agent, der …“ oder der direkte Aufruf mit `/build-agent`. Bestehende Agenten prüfst du mit `/build-agent audit`.

Agenten und Evals starten (Python ≥ 3.13, [uv](https://docs.astral.sh/uv/)). Auf OneDrive vorher `UV_LINK_MODE=copy` setzen:

```bash
cd test-finance-agent
echo "ANTHROPIC_API_KEY=..." > .env
uv sync
uv run python erp.py                     # Test-ERP und P2P-Event-Log erzeugen
uv run python evals/run_evals.py 3       # Kontext-Evals; analog run_node_evals.py, run_memory_evals.py, run_multiday.py
```

Ohne API-Key, mit Claude-Abo: `MODEL=claude-cli:haiku`. Lokal mit Ollama: `MODEL=ollama:<modell>`. Code-Evals ohne Modell:
- `packages/agent-guardrails/test_guardrails.py` und `evals/run_guardrail_evals.py`
- `test-finance-agent/test_memory.py`
- `test-rag-agent/test_search.py`
- `company-brain/test_ingest.py`
- `packages/mail-connector/test_mail_ocel.py`

Firmendokumente einlesen: `cd company-brain && uv run python ingest.py <ordner> <quellname>`, siehe [`AGENTS.md`](company-brain/AGENTS.md).

## Roadmap

Produkt nach [`SPEC-handwerk-wissen.md`](SPEC-handwerk-wissen.md), Abschnitt 11. Lizenz und Name sind noch offen ([#18](https://github.com/Alextum207/agent-builder-harness/issues/18)). Bis dahin gibt es keine LICENSE-Datei, und es gilt „alle Rechte vorbehalten“.

| Phase | Inhalt | Issues |
|---|---|---|
| A · [Kurs-Demo](https://github.com/Alextum207/agent-builder-harness/milestone/1) | Video → Schritte → Nachfragen → Job-Akte → Anleitung → Assistent, Demo im Browser | [#29](https://github.com/Alextum207/agent-builder-harness/issues/29), [#38](https://github.com/Alextum207/agent-builder-harness/issues/38), [#36](https://github.com/Alextum207/agent-builder-harness/issues/36), [#30](https://github.com/Alextum207/agent-builder-harness/issues/30), [#31](https://github.com/Alextum207/agent-builder-harness/issues/31), [#39](https://github.com/Alextum207/agent-builder-harness/issues/39) |
| B · [Pilot](https://github.com/Alextum207/agent-builder-harness/milestone/2) | App für Android und iPhone, Datenschutz-Paket, Anbindung der Handwerker-Software, 4 Wochen mit einem SHK-Betrieb | [#34](https://github.com/Alextum207/agent-builder-harness/issues/34), [#40](https://github.com/Alextum207/agent-builder-harness/issues/40), [#37](https://github.com/Alextum207/agent-builder-harness/issues/37), [#41](https://github.com/Alextum207/agent-builder-harness/issues/41) |

Harness-Arbeiten stehen als [GitHub-Issues](https://github.com/Alextum207/agent-builder-harness/issues), sortiert nach Labels `prio:P1` (jetzt), `prio:P2` (beim ersten echten Firmenprozess) und `prio:P3` (ab mehreren Agenten). Die Issues #1–#9 sind in PR #17 umgesetzt, die Folgearbeiten stehen in #10–#16. Grundlage ist der Abgleich mit Anthropic, OpenAI, Google ADK, LangChain, SAP und der Celonis-Fallstudie, siehe [`sources.md`](setup-entwurf/build-agent/references/sources.md).

## Nicht im Repo

- **Persönliche Daten:** `werkstudent-agent/context/` mit Profil, Lebenslauf und Firmenliste. Ohne `context/profil.md` laufen dessen Anschreiben-Prüfung und Evals nicht.
- **Laufzeitdaten und Secrets:** `.env`, `.secrets/`, `logs/`, `workspace/`, `traces/`, `company-brain/brain/`.
- **Fremde Skills im Original:** Herkunft und Lizenz stehen in [`sources.md`](setup-entwurf/build-agent/references/sources.md) und [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
