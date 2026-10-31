# Spec: `build-agent` – lernender Master-Skill für Agent- und Workflow-Builds

Status: ready-for-agent (kein Issue-Tracker eingerichtet, daher als Datei)

## Problem Statement

Wenn ich mit Claude Code Agents oder LLM-Workflows baue, arbeitet Claude jedes Mal frei los: ohne feste Ordnerstruktur, ohne Think → Act → Observe-Schleife mit Logs, ohne Evals vorab, oft mit veralteten Library-APIs aus dem Gedächtnis und mit selbstgebautem Code statt bewährter Frameworks. Das Ergebnis sind vermeidbare Bugs und unnötige Kosten.

Die vorhandenen Einzel-Skills (aus ECC und selbst geschrieben) widersprechen sich teilweise (Python vs. TypeScript, unterschiedliche Begriffe und Formate), konkurrieren beim Auslösen und kosten Grundlast. Außerdem geht Wissen aus abgeschlossenen Projekten verloren: Was bei einem Lead-Qualifier funktioniert hat, weiß Claude beim nächsten nicht mehr. Jeder Build startet bei null.

## Solution

Ein einziger Skill `build-agent`, der mich durch jeden Agent- oder Workflow-Build führt: von der Klärung über Muster-Wahl, Grundgerüst, Tools, Sicherheit, Evals und Kosten bis zum Ausführen. Er nutzt einen festen Stack (Python, LangGraph/LangChain, fastmcp, Pydantic) und schlägt aktuelle Doku über context7 nach.

Die bisherigen Einzel-Skills gehen als aufeinander abgestimmte Referenzdateien in diesem Skill auf. Er hat drei Modi: neuen Agent bauen, bestehenden Agent auditieren, nur Evals erstellen.

Am Ende jedes Builds wertet der Skill automatisch das Projekt aus (Logs, Evals, Kosten) und schlägt belegte Erkenntnisse vor. Nach meinem OK fließen sie in ein nach Kontext getaggtes Ledger; nach zwei bestätigten Projekten im selben Bereich entstehen daraus Playbooks und wiederverwendbare Code-Templates. So wird jeder weitere Build zuverlässiger und günstiger, ohne dass der Skill sich unkontrolliert selbst umschreibt.

## User Stories

### Einstieg und Modi
1. Als Builder will ich mit „bau mir einen Agent, der …“ automatisch den `build-agent`-Skill auslösen, damit ich keinen Befehl kennen muss.
2. Als Builder will ich `/build-agent` explizit aufrufen können, damit ich den Skill auch erzwingen kann.
3. Als Builder will ich einen Modus `audit`, damit ich einen bestehenden Agent auf Schwachstellen prüfen lassen kann, ohne neu zu bauen.
4. Als Builder will ich einen Modus `eval`, damit ich für einen bestehenden Agent nur Evals erstellen oder laufen lassen kann.
5. Als Builder will ich, dass der Skill bei einfachen Einzel-LLM-Aufrufen ohne Schleife oder Tools nicht auslöst, damit kein Overhead entsteht.
6. Als Builder will ich, dass nur ein Skill für „Agent bauen“ zuständig ist, damit nicht zwei Skills um denselben Auftrag konkurrieren.

### Klären
7. Als Builder will ich maximal drei gezielte Rückfragen (Ziel, Ein-/Ausgaben, benötigte Tools/APIs, Erfolgskriterium), damit der Build auf klaren Anforderungen startet.
8. Als Builder will ich, dass bereits bekannte Informationen nicht erneut abgefragt werden, damit ich Zeit spare.
9. Als Builder will ich, dass der Skill den Kontext (Bereich wie lead-qualification, marketing) erkennt, damit passende Playbooks und Templates geladen werden.

### Muster wählen
10. Als Builder will ich, dass der Skill begründet zwischen Workflow und autonomem Agent entscheidet, damit ich nicht unnötig Autonomie (und Unzuverlässigkeit) einbaue.
11. Als Builder will ich eine Auswahl aus bewährten Mustern (Chaining, Routing, Parallelisierung, Orchestrator-Worker, Evaluator-Optimizer, ReAct-Agent), damit die Architektur zur Aufgabe passt.
12. Als Builder will ich, dass parallele Tool-Aufrufe erlaubt sind, wo Schritte unabhängig sind, damit Läufe schneller werden.
13. Als Builder will ich, dass ein vorhandenes Template für den erkannten Kontext bevorzugt wird, damit ich getesteten Code wiederverwende statt neu zu generieren.

### Scaffold
14. Als Builder will ich eine feste Projektstruktur (config, context, skills, tools, workspace, logs, evals), damit jeder Agent gleich aufgebaut und auffindbar ist.
15. Als Builder will ich, dass `config.md` Identität, Kernregeln und Modellparameter enthält und bei Claude-Code-Agents die einzige Quelle ist, damit es keine doppelten Regeln gibt.
16. Als Builder will ich, dass `workspace/`, `logs/` und `.env` automatisch von Git ausgeschlossen werden, damit keine Rohdaten oder Secrets eingecheckt werden.
17. Als Builder will ich, dass die Think → Act → Observe-Schleife über LangGraph umgesetzt wird statt selbstgebaut, damit ich bewährte Persistenz und Kontrolle nutze.
18. Als Builder will ich harte Abbruchbedingungen (Ziel erreicht, max. Schritte, wiederholte identische Aktion), damit Agents nicht endlos laufen und Geld verbrennen.
19. Als Builder will ich, dass jeder Schritt (Gedanke, Aktion, Argumente, Beobachtung, Zeitstempel) als JSON-Zeile geloggt wird, damit ich jeden Lauf nachvollziehen kann.
20. Als Builder will ich, dass Secrets nur über Umgebungsvariablen kommen, damit sie nie in config, Logs oder Code landen.

### Tools
21. Als Builder will ich, dass jedes Tool ein Pydantic-Schema für seine Eingaben hat, damit falsche Parameter im Code abgefangen werden statt geraten.
22. Als Builder will ich ein einheitliches Rückgabeformat (status, summary, next_actions bzw. strukturierter Fehler), damit der Agent Ergebnisse und Fehler zuverlässig verarbeiten kann.
23. Als Builder will ich ein hartes Retry-Limit (3), damit fehlerhafte Tools nicht in Endlosschleifen laufen.
24. Als Builder will ich, dass Tools idempotent gebaut werden, wo möglich, damit ein Wiederholungsaufruf keinen Schaden anrichtet.
25. Als Builder will ich, dass große Tool-Ausgaben gekürzt werden, damit der Kontext nicht überläuft.
26. Als Builder will ich MCP-Server mit fastmcp in Python bauen, damit der ganze Stack einheitlich ist.
27. Als Builder will ich, dass Remote-MCP-Server über HTTP eine Authentifizierung haben, damit niemand Unbefugtes meine Tools aufruft.

### Sicherheit und Freigaben
28. Als Builder will ich, dass irreversible Aktionen (E-Mail senden, Zahlung, Löschen, Deploy) vor Ausführung eine menschliche Freigabe über LangGraph-Interrupts brauchen, damit kein Agent unwiderruflichen Schaden anrichtet.
29. Als Builder will ich, dass reversible oder rein lesende Aktionen ohne Freigabe laufen, damit der Agent nicht ständig nachfragt.
30. Als Builder will ich Schutz gegen versteckte Anweisungen in Webseiten, E-Mails oder Dokumenten (Indirect Prompt Injection), damit fremde Inhalte den Agent nicht umsteuern.
31. Als Builder will ich, dass Tool-Ausgaben niemals System-Prompt oder Tool-Berechtigungen verändern können, damit die Kontrolle beim Code bleibt.
32. Als Builder will ich, dass Regeln, die eingehalten werden müssen (Formate, Budgets, verbotene Tools), im Code erzwungen werden statt nur im Prompt, damit sie nicht ignoriert werden können.

### RAG und Quellen
33. Als Builder will ich, dass bei RAG-Agents Metadaten (Datei, Seite, Abschnitt) beim Chunking erhalten bleiben, damit Antworten belegbar sind.
34. Als Builder will ich, dass der Agent Zitat-Anker in seine Antworten einbettet, damit ich und meine Kunden jede Aussage prüfen können.
35. Als Builder will ich, dass der Agent bei fehlenden oder widersprüchlichen Quellen Unsicherheit meldet statt zu halluzinieren, damit keine erfundenen Fakten ausgeliefert werden.

### Evals
36. Als Builder will ich, dass vor dem Implementieren mindestens drei Eval-Fälle (Normalfall, Grenzfall, Fehlerfall) festgelegt werden, damit Erfolg messbar ist.
37. Als Builder will ich deterministische Grader (Schema, Regex, exakte Werte) für Strukturen, damit Prüfungen billig und eindeutig sind.
38. Als Builder will ich LLM-as-a-Judge für inhaltliche Qualität, wobei der Judge erst begründet und dann auf einer kleinen Skala (1–4) bewertet, damit Bewertungen stabiler sind.
39. Als Builder will ich bei RAG-Agents Metriken wie Faithfulness und Context Precision, damit ich weiß, ob Antworten wirklich aus den Quellen stammen.
40. Als Builder will ich Zuverlässigkeit über pass@k sehen, damit ich weiß, wie oft der Agent bei wiederholten Läufen besteht.
41. Als Builder will ich, dass Evals nach jeder Prompt- oder Code-Änderung erneut laufen, damit Regressionen auffallen.

### Kosten und Caching
42. Als Builder will ich Modell-Routing nach Aufgabentyp (z. B. Klassifikation → kleines Modell, komplexe Planung → großes Modell), damit ich nicht für jede Aufgabe das teuerste Modell bezahle.
43. Als Builder will ich, dass statische Teile (System-Prompt, Tool-Definitionen, SOPs) im Prompt vor dynamischen Teilen (RAG-Chunks, Nutzereingabe) stehen, damit Prompt-Caching greift.
44. Als Builder will ich ein Budget-Limit pro Lauf im Code, damit Kosten nicht ausufern.
45. Als Builder will ich, dass Kosten und Latenz pro Lauf geloggt werden, damit ich sie über Projekte vergleichen kann.

### Ausführen und Verifizieren
46. Als Builder will ich, dass der Agent am Ende einmal komplett durchläuft und das Log gezeigt wird, damit ich sehe, dass er wirklich funktioniert.
47. Als Builder will ich, dass Claude nichts als fertig meldet, ohne Evals gelaufen und Ergebnisse gezeigt zu haben, damit ich mich auf „fertig“ verlassen kann.
48. Als Builder will ich, dass vor jedem Code mit einer Library die aktuelle Doku über context7 geholt wird, damit keine veralteten APIs verwendet werden.

### Lernkreislauf
49. Als Builder will ich, dass am Ende jedes Builds automatisch eine Retro läuft, damit Erkenntnisse nicht verloren gehen.
50. Als Builder will ich, dass die Retro Logs, Eval-Ergebnisse und Kosten auswertet statt Bauchgefühl, damit Erkenntnisse belegt sind.
51. Als Builder will ich, dass jedes Projekt eine eigene Retro-Datei mit allen Details bekommt, damit ich später nachlesen kann, was passiert ist.
52. Als Builder will ich, dass die Retro Vorschläge nur in eine Inbox schreibt, damit nichts ohne mein OK in die Regeln gelangt.
53. Als Builder will ich, dass jeder Vorschlag einen Beleg hat (Projekt, Messwert vorher/nachher, Kosten), damit ich fundiert entscheiden kann.
54. Als Builder will ich, dass übernommene Erkenntnisse mit Kontext-Tag (z. B. lead-qualification, tools, kosten) und Projektpfad ins Ledger kommen, damit sie gezielt wiedergefunden werden.
55. Als Builder will ich feste allgemeine Kontexte (allgemein, tools, evals, kosten, sicherheit), damit bereichsübergreifende Erkenntnisse sauber einsortiert werden.
56. Als Builder will ich, dass bei einem neuen Build nur die Ledger-Einträge des passenden Kontexts plus die allgemeinen gelesen werden, damit Builds günstig bleiben.
57. Als Builder will ich, dass nach dem ersten Projekt in einem neuen Bereich ein Playbook- und Template-Entwurf vorgeschlagen wird, damit Wissen früh festgehalten wird.
58. Als Builder will ich, dass ein Playbook erst nach zwei bestätigten Projekten im selben Kontext als bestätigt gilt, damit Einzelfälle keine Regeln werden.
59. Als Builder will ich, dass keine leeren Bereichs-Gerüste vorab angelegt werden, damit der Skill nur echtes Wissen enthält.
60. Als Builder will ich, dass Templates aus echtem, getestetem Projektcode entstehen, damit Wiederverwendung zuverlässig ist.
61. Als Builder will ich, dass Kern-Ablauf und allgemeine Regeln stabil bleiben und sich nur bei bereichsübergreifend bestätigten Erkenntnissen ändern, damit der Skill vorhersagbar bleibt.
62. Als Builder will ich Probleme, die erst später im Betrieb auffallen, einfach mitteilen können, damit sie wie Retro-Erkenntnisse in die Inbox kommen.

### Aufräumen und Versionierung
63. Als Builder will ich, dass der Skill Aufräumen vorschlägt, sobald ein Kontext zu voll wird (ca. 50 Einträge oder eine Datei über ca. 300 Zeilen), damit ich nicht selbst daran denken muss.
64. Als Builder will ich, dass Aufräumen pro Kontext läuft, damit andere Bereiche unberührt bleiben.
65. Als Builder will ich, dass beim Aufräumen Widersprüche aufgelöst (neuere, besser belegte Regel gewinnt), Doppeltes zusammengefasst und Veraltetes gestrichen wird, damit der Skill konsistent bleibt.
66. Als Builder will ich eine Änderungsliste zum Abnicken vor jedem Aufräumen, damit nichts ohne mein OK verschwindet.
67. Als Builder will ich, dass jede übernommene Erkenntnis automatisch als Git-Commit mit Projektverweis gespeichert wird, damit ich nachvollziehen kann, warum eine Regel existiert.
68. Als Builder will ich eine schlechte Änderung (z. B. ein fehlerhaftes Template) per Satz zurücknehmen lassen können, damit Fehler nicht in künftige Projekte wandern.

### Setup
69. Als Builder will ich, dass alle neuen Dateien zuerst im Entwurfsordner des Projekts landen, damit ich sie vor der Installation reviewen kann.
70. Als Builder will ich eine schlanke globale CLAUDE.md (3–4 Zeilen), damit ich nicht bei jeder Anfrage Tokens für Agent-Regeln zahle.
71. Als Builder will ich, dass `write-skill` eigenständig bleibt und Skills nach Trigger, Schrittfolge, Edge Cases, Erfolgsmetrik und Evaluation strukturiert, damit auch Agent-SOPs einheitlich sind.
72. Als Builder will ich, dass jede Regel im Skill ihre Quelle nennt, damit ich weiß, worauf sie beruht.

## Implementation Decisions

- **Ein Skill statt neun:** `build-agent` ersetzt die Einzel-Skills `agent-scaffold`, `agent-harness-construction`, `agent-security-hardening`, `agent-architecture-audit`, `eval-harness`, `mcp-server-patterns`, `prompt-caching-strategy`, `cost-aware-llm-pipeline`. Diese werden nicht separat installiert.
- **Progressive Disclosure:** Die Hauptdatei ist ein kurzer Router (unter ~150 Zeilen) mit Modi und Phasen. Jede Phase verweist auf eine eigene Referenzdatei, die nur geladen wird, wenn die Phase dran ist.
- **Komponenten des Skills:**
  - Router (Modi `build`, `audit`, `eval`; Phasenreihenfolge)
  - Referenzen (stabil): Muster-Wahl, Scaffold, Tools, MCP, Sicherheit, Evals, Kosten & Caching, Audit, Retro
  - Domains (wächst): ein Playbook pro Kontext
  - Templates (wächst): getesteter Code pro Kontext
  - Learnings: Inbox (Vorschläge) und Ledger (übernommene Erkenntnisse)
- **Phasenfolge im Modus `build`:** Klären → Muster wählen → Scaffold → Tools → Sicherheit → Evals → Kosten & Caching → Ausführen → Retro.
- **Modus `audit`:** nutzt die Audit-Referenz plus Sicherheit, Tools, Evals; ändert Code erst nach Freigabe.
- **Modus `eval`:** nutzt nur die Eval-Referenz.
- **Stack:** Python; LangGraph für Schleife, Zustand, Persistenz und Freigaben; LangChain für Modell- und Tool-Anbindung; fastmcp für MCP-Server; Pydantic für Schemas. TypeScript nur, wenn ein Projekt es verlangt.
- **HITL-Mechanik:** Die aktuelle LangGraph-API für Interrupts (dynamisches `interrupt()` vs. statisches `interrupt_before`) wird beim Bauen über context7 verifiziert und dann festgelegt.
- **Tool-Vertrag:** Pydantic-Input-Schema; Rückgabe mit `status`, `summary`, `next_actions`; Fehler strukturiert mit Typ, Meldung und Handlungsvorschlag; max. 3 Retries.
- **Projekt-Scaffold:** config.md, context/, skills/, tools/, workspace/, logs/, evals/, RETRO.md; workspace, logs und .env gitignored.
- **Log-Format:** eine JSON-Zeile pro Schritt mit step, thought, action, args, observation, ts; zusätzlich Kosten und Latenz pro Lauf.
- **Ledger-Eintragsformat:**
  ```
  - <Datum> | kontext: <tag> | projekt: <pfad>
    Erkenntnis: <was> → <Messwert vorher/nachher oder Beleg>
  ```
- **Promotion-Regeln:** Retro → Inbox (automatisch). Inbox → Ledger (nur mit OK). Ledger → Domain-Playbook + Template (nach 2 bestätigten Projekten im selben Kontext, mit OK). Ledger → Referenz (nur bei bereichsübergreifend bestätigter Erkenntnis, mit OK).
- **Aufräum-Trigger:** Vorschlag bei >~50 Einträgen in einem Kontext oder einer Datei >~300 Zeilen; Ausführung pro Kontext, nur mit OK.
- **Versionierung:** lokales Git-Repo im installierten Skill-Ordner; ein Commit pro übernommener Erkenntnis bzw. Aufräumaktion, Commit-Message nennt Projekt und Kontext.
- **Inhaltsfilter aus der Gemini-Liste:** übernommen werden Pydantic-Schemas, Retry-Limit, Tool-Rückgabeformat, HITL bei irreversiblen Aktionen, Indirect-Prompt-Injection-Schutz, Cache-Reihenfolge, Judge „erst Begründung, dann Note“ mit Skala 1–4, RAG-Zitat-Metadaten. Gestrichen: lokales SLM/Ollama, Cohen's Kappa, semantisches Komplexitäts-Routing, Bounding Boxes, ReWOO-Pflicht, Shadow-AI-Audit, HITL-Pflicht in Skill-Beschreibungen, Enterprise-Regelwerk.
- **Quellen:** Anthropic (Building Effective Agents, Writing Tools for Agents, Context Engineering, Skill-Authoring-Doku), LangGraph-Doku (via context7), 12-Factor Agents, OWASP Top 10 für LLM-Anwendungen. Jede Regel trägt einen Quellenvermerk.
- **Globale CLAUDE.md:** nur: Doku via context7 vor Library-Code; Agent-/Workflow-Builds über `build-agent`; nichts als fertig melden ohne Ausführung.
- **write-skill:** bleibt eigenständig, Struktur Trigger / Schritte / Edge Cases / Erfolgsmetrik / Evaluation.
- **Lizenz:** ECC-Inhalte sind MIT; Herkunft wird im Skill vermerkt.

## Testing Decisions

- **Gute Tests prüfen äußeres Verhalten:** Was erzeugt der Skill bei einer realistischen Anfrage (Dateien, Läufe, Vorschläge), nicht wie er intern formuliert ist.
- **Ein Haupt-Seam:** ein kompletter Durchlauf von `build-agent` in einem frischen Testprojekt mit einer realistischen Anfrage (z. B. „bau mir einen Agent, der eingehende Leads per E-Mail bewertet“). Geprüft wird:
  - Projektstruktur vollständig, workspace/logs/.env gitignored
  - LangGraph-Schleife mit Abbruchbedingungen; Log mit allen Feldern pro Schritt
  - Tools mit Pydantic-Schema und einheitlichem Rückgabeformat
  - Freigabe-Unterbrechung vor einer irreversiblen Aktion (E-Mail senden)
  - mindestens 3 Evals vorhanden und ausgeführt, Ergebnis gezeigt
  - RETRO.md im Projekt und ein belegter Vorschlag in der Inbox mit Kontext-Tag
- **Trigger-Tests:** ein Prompt, der auslösen muss („bau mir einen Agent …“), und einer, der nicht auslösen darf (einzelner LLM-Aufruf ohne Tools).
- **Modus-Tests:** `audit` an einem bewusst fehlerhaften Mini-Agent (z. B. Tool ohne Schema, keine Abbruchbedingung) muss diese Mängel finden und vor Codeänderung um Freigabe bitten; `eval` erzeugt nur Evals.
- **Lernkreislauf-Test:** zwei simulierte Projekte im selben Kontext → nach dem zweiten wird ein Playbook- und Template-Vorschlag erzeugt; nach Freigabe entsteht genau ein Git-Commit.
- **Prior Art:** keine bestehenden Tests im Projekt (Ordner ist leer). `write-skill` definiert das Muster „ein positiver und ein negativer Trigger-Test“.

## Out of Scope

- Backend-Skill (FastAPI, Datenbank, Auth): eigener Skill später bei Bedarf.
- Lokale SLMs / Ollama, Cohen's Kappa, Enterprise-Regelwerk, Shadow-AI-Audit.
- TypeScript als Standard-Stack.
- Vorab angelegte Bereichs-Playbooks (Marketing, Lead-Qualification usw.) ohne echtes Projekt.
- Manueller Lern-Modus (`/build-agent learn`); spätere Probleme werden im Gespräch gemeldet.
- Automatisches Ändern der Regeln ohne Freigabe.
- Installation nach `~/.claude/` vor dem Review.

## Further Notes

- Kein Issue-Tracker konfiguriert; für Tickets `/setup-matt-pocock-skills` ausführen oder diese Datei als Spec verwenden.
- Der context7-MCP-Server ist bereits auf User-Ebene installiert (ohne API-Key); Rate-Limits beachten.
- Die 9 Quell-Skills liegen im Entwurfsordner unter `skills/` und dienen als Ausgangsmaterial.
