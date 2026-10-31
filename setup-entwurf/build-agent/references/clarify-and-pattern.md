# Klären und Muster wählen

## 1 Klären
Maximal drei Fragen, nur was noch unbekannt ist:
1. **Ziel und Erfolgskriterium:** Was ist ein gutes Ergebnis, messbar? (z. B. „Lead-Score stimmt in 9 von 10 Fällen mit Vertrieb überein“)
2. **Ein-/Ausgaben und Auslöser:** Woher kommen Daten (Webhook, Zeitplan, Chat, Datei), was kommt raus (JSON, E-Mail, CRM-Eintrag)?
3. **Systeme und Aktionen:** Welche APIs/Tools? Welche Aktionen sind **irreversibel**?

Immer mitklären (kann in Frage 2 oder 3 stecken):
- **Personenbezogene Daten?** (Namen, E-Mails, Telefonnummern von Leads/Kunden) → ja: siehe security.md „DSGVO“; bei Kundenprojekten fragen, ob ein AVV mit dem LLM-Anbieter besteht.
- **Betrieb:** nur lokal oder dauerhaft für einen Kunden (Webhook, Zeitplan)? → dauerhaft: Phase Deploy einplanen.

Danach: Kontext-Tag festlegen und im Projekt in `config.md` notieren.

## 2 Muster wählen
Die einfachste Zeile, die passt, gewinnt (Quelle: A1):

| Situation | Muster | Umsetzung |
|---|---|---|
| Ein Aufruf mit Retrieval/Beispielen reicht | **Kein Agent** | einzelner Call, Skill hier beenden |
| Feste Schritte nacheinander | Prompt Chaining | `StateGraph`, lineare Nodes, Code-Checks zwischen Nodes |
| Eingaben fallen in klare Kategorien | Routing | Klassifizier-Node (kleines Modell) + `add_conditional_edges` |
| Unabhängige Teilaufgaben | Parallelisierung | parallele Kanten / `Send`; Voting = gleiche Aufgabe mehrfach |
| Teilaufgaben erst zur Laufzeit bekannt | Orchestrator-Worker | Planer-Node + `Send` an Worker-Nodes |
| Klare Qualitätskriterien, Feedback hilft messbar | Evaluator-Optimizer | Generator-Node ↔ Kritiker-Node, max. 3 Runden |
| Offene Aufgabe, Schrittzahl unbekannt | ReAct-Agent | `create_agent` mit Tools und Middleware |

Regeln:
- **Workflow vor Agent:** Wenn sich der Ablauf als Graph aufschreiben lässt, ist es ein Workflow (Quelle: A1, F8 „own your control flow“).
- **Kleine Agents:** Ein Agent pro klar umrissener Aufgabe; große Aufgaben als Workflow aus kleinen Agents (Quelle: F10).
- **Parallel, wo unabhängig:** Unabhängige Tool-Aufrufe oder Nodes parallel ausführen; Claude ruft Tools ohnehin parallel auf.
- **Unsicherheit statt Erfinden:** Bei Wissens-Agents einen Ausgang „unzureichende/widersprüchliche Quellen → Mensch fragen“ vorsehen.

Ergebnis: gewähltes Muster + ein Satz Begründung in `config.md`.
