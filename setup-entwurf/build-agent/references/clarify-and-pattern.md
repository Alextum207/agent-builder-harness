# Klären und Muster wählen

## 1 Klären
Maximal drei Fragen, nur was noch unbekannt ist:
1. **Ziel und Erfolgskriterium:** Was ist ein gutes Ergebnis, messbar? (z. B. „Lead-Score stimmt in 9 von 10 Fällen mit Vertrieb überein“)
2. **Ein-/Ausgaben und Auslöser:** Woher kommen Daten (Webhook, Zeitplan, Chat, Datei), was kommt raus (JSON, E-Mail, CRM-Eintrag)?
3. **Systeme und Aktionen:** Welche APIs/Tools? Welche Aktionen sind **irreversibel**?

Immer mitklären (kann in Frage 2 oder 3 stecken):
- **Personenbezogene Daten?** (Namen, E-Mails, Telefonnummern von Leads/Kunden) → ja: siehe security.md „DSGVO“; bei Kundenprojekten fragen, ob ein AVV mit dem LLM-Anbieter besteht.
- **Betrieb:** nur lokal oder dauerhaft für einen Kunden (Webhook, Zeitplan)? → dauerhaft: Phase Deploy einplanen.
- **Datenlage:** Sind die Eingabedaten zugänglich, vollständig und konsistent (Stichprobe von 5–10 echten oder realistischen Fällen ansehen)? Fehlende oder widersprüchliche Daten zuerst klären; daran scheitern die meisten Piloten, nicht am Modell (Quelle: SAP1).
- **Laufart:** kurz, lang oder mehrtägig? → `run_length` (context.md).
- **Autonomie:** Wie viel darf der Agent allein? → `autonomy_level` (unten).

Danach: Kontext-Tag festlegen und im Projekt in `config.md` notieren.

### Autonomie-Stufe
`autonomy_level` in `config.md`, Standard `vorschlagen` (Quelle: SAP1, OAI2):

| Stufe | Agent | Mensch |
|---|---|---|
| `beobachten` | schlägt nur vor, schreibt nichts | handelt selbst |
| `vorschlagen` | bereitet vor, jede schreibende Aktion wartet auf Freigabe | gibt frei |
| `ausführen` | reversible Aktionen allein, mit Log | prüft im Nachgang Stichproben |
| `autonom` | alles außer `IRREVERSIBLE` allein | nur Grenzfälle und Stichproben |

- Irreversible Aktionen brauchen auf jeder Stufe Freigabe (security.md).
- Hochstufen nur mit Eval- oder Backtest-Zahlen, nie auf Verdacht. Die Stufe gilt pro Prozess, nicht pro Agent-Plattform.
- Die Stufe wird im Code durchgesetzt (welche Tools in die Freigabeliste kommen), nicht im Prompt.

## 2 Muster wählen
Die einfachste Zeile, die passt, gewinnt (Quelle: A1):

| Situation | Muster | Umsetzung |
|---|---|---|
| Ein Aufruf mit Retrieval/Beispielen reicht | **Kein Agent** | einzelner Call, Skill hier beenden |
| Feste Schritte nacheinander | Prompt Chaining | `StateGraph`, lineare Nodes, Code-Checks zwischen Nodes |
| Schritte pro Fall verschieden, aber vor der Ausführung prüfbar; hohe Tragweite | Plan-then-Execute | Planer-Node erzeugt Plan als Pydantic-Liste → Code prüft (nur erlaubte Schritte) → `interrupt()` zur Freigabe → Ausführung Schritt für Schritt ohne LLM-Entscheidung |
| Eingaben fallen in klare Kategorien | Routing | Klassifizier-Node (kleines Modell) + `add_conditional_edges` |
| Unabhängige Teilaufgaben | Parallelisierung | parallele Kanten / `Send`; Voting = gleiche Aufgabe mehrfach |
| Teilaufgaben erst zur Laufzeit bekannt | Orchestrator-Worker | Planer-Node + `Send` an Worker-Nodes |
| Klare Qualitätskriterien, Feedback hilft messbar | Evaluator-Optimizer | Generator-Node ↔ Kritiker-Node, max. 3 Runden |
| Fragen an Firmenwissen; ob und wie oft gesucht wird, hängt von der Frage ab | Agentic / Adaptive RAG | Router-Node (ohne Suche / eine / mehrstufig) → Retrieval-Node (Code) → Prüf-Node (reicht? Widerspruch?) → Nachsuchen bis `max_suchen` → Antwort mit Zitaten → Code prüft Zitate; Ausgang „Mensch“ |
| Offene Aufgabe, Schrittzahl unbekannt | ReAct-Agent | `create_agent` mit Tools und Middleware |

Regeln:
- **Workflow vor Agent:** Wenn sich der Ablauf als Graph aufschreiben lässt, ist es ein Workflow (Quelle: A1, F8 „own your control flow“).
- **Kleine Agents:** Ein Agent pro klar umrissener Aufgabe; große Aufgaben als Workflow aus kleinen Agents (Quelle: F10).
- **Parallel, wo unabhängig:** Unabhängige Tool-Aufrufe oder Nodes parallel ausführen; Claude ruft Tools ohnehin parallel auf.
- **Fehler multiplizieren sich:** Fünf Schritte mit je 95 % ergeben zusammen ≈ 77 %. Jeder zusätzliche LLM-Schritt muss sich messbar lohnen; zwischen Schritten Schema-Checks im Code (Quelle: SAP1).
- **Plan statt Schleife:** Bei hoher Tragweite lieber Plan-then-Execute als ReAct. Der Zufall bleibt im Plan, den ein Mensch sieht; die Ausführung ist deterministisch.
- **Kritiker vorsichtig:** Evaluator-Optimizer kann richtige Antworten „verschlimmbessern“. Nur einsetzen, wenn ein Eval zeigt, dass die zweite Runde besser ist.
- **Unsicherheit statt Erfinden:** Bei Wissens-Agents einen Ausgang „unzureichende/widersprüchliche Quellen → Mensch fragen“ vorsehen.

### Agentic / Adaptive RAG (Quelle: SAP1)
Referenz: `test-rag-agent/rag.py` über ein OKF-Bundle aus `company-brain/ingest.py`.
- **Adaptive:** Ein Router (kleines Modell, strukturierte Ausgabe) wählt `ohne_suche | eine_suche | mehrstufig` und liefert Suchbegriffe. Das Limit pro Modus steht in `config.md` (`max_suchen: {ohne_suche: 0, eine_suche: 2, mehrstufig: 3}`) und wird in der Kante nach dem Prüf-Node erzwungen, nicht im Prompt.
- **Agentic:** Der Prüf-Node bewertet `ausreichend`, `widerspruch` und liefert bessere Suchbegriffe; nachgesucht wird nur bis zum Limit.
- **Ausgang Mensch im Code:** Widerspruch → Mensch; nach dem Limit nicht ausreichend → Mensch; Zitate, die nicht zu abgerufenen Auszügen gehören → Mensch.
- Retrieval ist Code (Keyword-Suche über Abschnitte, Titel und `stand` aus dem OKF-Kopf). Embeddings erst, wenn die Keyword-Suche messbar zu wenig findet (Context Precision im Report).
- Auszüge gehen als `<auszug id=… dokument=… stand=…>` ins Modell; Auszüge mit Injection-Markern bekommen den Taint-Hinweis aus dem Guardrails-Paket.

Ergebnis: gewähltes Muster + ein Satz Begründung in `config.md`.
