# Agent Builder Harness

Ein Claude-Code-Skill, der LLM-Agenten nach festem Ablauf baut, prüft und aus jedem Projekt lernt. Dazu zwei damit gebaute Agenten und die Spezifikation für den nächsten Schritt.

Ohne Harness legt Claude bei jedem Agenten frei los: ohne feste Struktur, ohne Evals und oft mit veralteten APIs aus dem Gedächtnis. `build-agent` gibt dafür eine Checkliste vor. Erkenntnisse aus einem Projekt gehen nach Freigabe in ein Ledger und stehen dem nächsten Build zur Verfügung.

Die Dokumentation ist auf Deutsch.

## Inhalt

| Pfad | Was | Stand |
|---|---|---|
| [`setup-entwurf/build-agent/`](setup-entwurf/build-agent/SKILL.md) | Der Skill: Referenzen, Ledger, Template | im Einsatz |
| [`setup-entwurf/write-skill/`](setup-entwurf/write-skill/SKILL.md) | Skill zum Schreiben weiterer Skills | im Einsatz |
| [`setup-entwurf/SPEC-build-agent.md`](setup-entwurf/SPEC-build-agent.md) | Spezifikation des Skills | fertig |
| [`test-lead-agent/`](test-lead-agent/) | Erster Testlauf: qualifiziert B2B-Leads mit LangChain | erfundene Daten |
| [`werkstudent-agent/`](werkstudent-agent/README.md) | Sucht Werkstudentenstellen und prüft Anschreiben per Code | ohne persönliche Daten |
| [`SPEC-firmen-agent.md`](SPEC-firmen-agent.md) | Vision: Agent lernt Firmenprozesse und verdient sich Autonomie | Entwurf |
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

| Projekt | Lauf | Ergebnis |
|---|---|---|
| `test-lead-agent` | n=6, k=3, `claude-haiku-5-5` ([Retro](test-lead-agent/RETRO.md)) | pass@3 100 %, 0,00084 $ pro Lauf, 3–4 Model-Calls |
| `test-lead-agent` | n=6, k=1, lokal `granite4.1:8b` ([Report](test-lead-agent/evals/report-2026-10-14-k1-granite4.1-8b.md)) | 4/6, Injection-Fall nicht bestanden |
| `werkstudent-agent` | 22 Code-Evals ohne Model-Calls ([Report](werkstudent-agent/evals/report-2026-10-31-k1.md)) | 22/22 |

Sechs erfundene Fälle sind nur ein Hinweis, kein Qualitätsnachweis. Belastbarer sind die fünf reproduzierbaren Bugs aus der [Retro](test-lead-agent/RETRO.md), darunter der `ModelRetryMiddleware`-Default, der API-Ausfälle als normale Antwort tarnt. Die Fixes stehen im [Ledger](setup-entwurf/build-agent/learnings/ledger.md).

## Loslegen

Skill installieren (Bash, [Claude Code](https://claude.com/claude-code) vorausgesetzt):

```bash
cp -r setup-entwurf/build-agent ~/.claude/skills/
```

Danach reicht in Claude Code ein Satz wie „Bau mir einen Agent, der …“ oder der direkte Aufruf mit `/build-agent`. Bestehende Agenten prüfst du mit `/build-agent audit`.

Lead-Agent starten (Python ≥ 3.13, [uv](https://docs.astral.sh/uv/)):

```bash
cd test-lead-agent
echo "ANTHROPIC_API_KEY=..." > .env
uv sync
uv run python evals/run_evals.py 3
```

Der Eval-Lauf ruft die Anthropic-API auf. Lokal geht es mit Ollama über `MODEL=ollama:granite4.1:8b`.

## Nicht im Repo

- **Persönliche Daten:** `werkstudent-agent/context/` mit Profil, Lebenslauf und Firmenliste. Ohne `context/profil.md` laufen dessen Anschreiben-Prüfung und Evals nicht.
- **Laufzeitdaten und Secrets:** `.env`, `.secrets/`, `logs/`, `workspace/`.
- **Fremde Skills im Original:** Herkunft und Lizenz stehen in [`sources.md`](setup-entwurf/build-agent/references/sources.md) und [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
