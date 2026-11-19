# Kontext

## Inhalt
- Grundsatz
- Laufart festlegen
- Fester Kontext (Prompt)
- Tool-Ausgaben
- Kontext während des Laufs
- Memory und Subagenten
- Messen
- Prüf-Gate

## Grundsatz (Quelle: A3, L5)
Kontext ist ein knappes Budget: die kleinste Menge Tokens mit hohem Signal. Mehr Kontext macht den Agenten oft schlechter. Vier Fehlerbilder:
- **Vergiftung:** ein falsches Tool-Ergebnis oder eine Halluzination wird später als Tatsache weiterverwendet.
- **Ablenkung:** irrelevante Inhalte verdrängen relevante.
- **Verwechslung:** Regeln oder Tools einer anderen Aufgabe werden angewendet.
- **Widerspruch:** mehrere Quellen sagen Verschiedenes, ohne Vorrang.

Strategien: **schreiben** (Notizen außerhalb des Fensters), **auswählen** (nur Relevantes laden), **verdichten** (entfernen, zusammenfassen), **isolieren** (Subagent mit eigenem Fenster). Immer die billigste Stufe zuerst.

## Laufart festlegen
In `config.md`: `run_length: kurz | lang | mehrtägig`.

| Laufart | Typisch | Maßnahmen |
|---|---|---|
| kurz | ≤ ~20 Schritte, ein Fall pro Lauf (Lead, Ticket, Rechnung) | nur Abschnitte „Fester Kontext“ und „Tool-Ausgaben“ |
| lang | viele Tool-Aufrufe, Kontext kann voll werden | zusätzlich „Kontext während des Laufs“ |
| mehrtägig | Arbeit über mehrere Sitzungen | zusätzlich Fortschrittsdatei, siehe unten |

Die meisten Agenten sind `kurz`. Dann keine Middleware einbauen, die nie greift.

## Fester Kontext (Quelle: A3)
- System-Prompt in Abschnitte gliedern (`# Rolle`, `# Ablauf`, `# Regeln` oder XML-Tags).
- Richtige Flughöhe: konkret genug, um zu steuern, ohne `wenn-dann`-Ketten, die in Code gehören (Code statt Prompt).
- Wenige typische Beispiele statt einer langen Liste von Sonderregeln.
- Große Referenzen (`context/*.md`, Handbücher) nur nennen und per Tool laden, wenn gebraucht (just in time). Was für Sicherheit oder Korrektheit nötig ist, bleibt fest im Prompt: kleine Modelle laden nicht zuverlässig nach.
- Wichtiges an den Anfang oder ans Ende, nicht in die Mitte langer Prompts.
- Widersprüchliche Quellen: Vorrang festlegen (z. B. „CRM schlägt E-Mail-Signatur“) und im Prompt nennen.
- Statischer Teil vor dynamischem, damit Caching greift (cost-and-caching.md).

## Tool-Ausgaben (Quelle: A2)
Ergänzt tools.md:
- Parameter `response_format: Literal["knapp", "ausführlich"]` bei Tools mit großen Antworten. Knapp ist Standard.
- Große Ausgaben (über ~2.000 Tokens) nach `workspace/` schreiben und nur Pfad plus 1–2 Sätze Zusammenfassung zurückgeben. Der Agent liest gezielt nach (Suche, Zeilenbereich).
- Beim Kürzen auf Filter oder Paginierung hinweisen, nie still abschneiden.

## Kontext während des Laufs (nur `lang`, Quelle: L4, A5)
Reihenfolge, billigste zuerst:

**1. Alte Tool-Ergebnisse entfernen.** Die sicherste Form der Verdichtung.
```python
from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit

ContextEditingMiddleware(edits=[ClearToolUsesEdit(
    trigger=<tokens>,          # Default 100000; bei kleinen Modellen deutlich niedriger
    keep=3,                    # letzte 3 Tool-Ergebnisse bleiben
    clear_at_least=<tokens>,   # nur entfernen, wenn es sich lohnt (Cache!)
    exclude_tools=[...],       # Ergebnisse, die bis zum Ende gebraucht werden
)])
```

**2. Zusammenfassen, wenn der Kontext trotzdem voll wird.**
```python
from langchain.agents.middleware import SummarizationMiddleware

SummarizationMiddleware(model=<kleines Modell>, trigger=("fraction", 0.8), keep=("messages", 20))
```
- Die Zusammenfassung ersetzt alte Nachrichten dauerhaft. Fehler darin vergiften den Rest des Laufs (Quelle: O2).
- Feste Abschnitte vorgeben: Ziel, Entscheidungen, Artefakte, offene Schritte. Leere Abschnitte machen Verluste sichtbar.
- **Artefakte nicht der Zusammenfassung überlassen:** Pfade, IDs und geänderte Datensätze zusätzlich in einem State-Feld führen. Zusammenfassungen verlieren genau diese Details (Quelle: CE1).

**Kosten:** Jedes Entfernen oder Zusammenfassen ändert den Präfix und macht den Prompt-Cache ab dort ungültig. Darum `clear_at_least` setzen und Trigger nicht zu niedrig wählen.

**Provider:** Wir bleiben bei den LangChain-Middlewares, weil sie auch mit lokalen Modellen (Ollama) laufen. Die serverseitige Verdichtung von Anthropic (A5, A6) nur, wenn der Agent fest auf Claude läuft.

**Mehrtägig (Quelle: A7):** Verdichten allein reicht nicht. Zusätzlich:
- `workspace/progress.md`: was erledigt ist, was als Nächstes kommt. Jede Sitzung liest sie zuerst.
- Aufgabenliste als JSON mit `"done": false`; der Agent darf nur dieses Feld ändern (Code prüft das).
- Ein Arbeitspaket pro Sitzung, danach Commit oder Checkpoint (LangGraph-Persistence, Quelle: L3).
- Zu Beginn jeder Sitzung ein kurzer Selbsttest, ob der letzte Stand noch funktioniert.

## Memory und Subagenten
**Memory nur bei Agenten über mehrere Sitzungen.** Gesprächsverlauf (State) ist kein Memory. Wenn Memory nötig ist:
- Jeder Eintrag mit Quelle und Datum; alte Einträge laufen ab.
- Nutzer-Korrektur schlägt Agent-Behauptung; eigener Monolog des Agents wird nie zu Memory (audit.md).
- Keine Personendaten ohne Zweck (security.md „DSGVO“).
- Liegt Memory in Dateien: Pfade prüfen wie in security.md, Dateigröße begrenzen (Quelle: A6).
Ausbau (Store, semantische Suche): Issue #5, noch kein Standard.

**Subagenten nur bei breiten Aufgaben**, deren Teile unabhängig sind (Recherche über viele Quellen). Regeln (Quelle: A8):
- Jeder Subagent bekommt Ziel, Ausgabeformat, erlaubte Tools und Abbruchgrenze.
- Rückgabe knapp (≈ 1.000–2.000 Tokens) oder als Datei mit Verweis.
- Kosten: Multi-Agenten-Systeme brauchen laut A8 etwa 15× so viele Tokens wie ein Chat. Nur wenn der Nutzen gemessen ist.

## Messen
In evals.md eingetragen:
- **Tokens pro Aufgabe** statt pro Aufruf. Zu aggressive Verdichtung spart pro Aufruf und kostet insgesamt mehr, weil der Agent neu sucht.
- **Nachlade-Rate:** liest der Agent Daten erneut, die er schon hatte, ist die Verdichtung zu stark.
- Eval-Fälle „Token-Druck“ und „vergifteter Kontext“ (siehe Prüf-Gate).

## Prüf-Gate (nur `lang` und `mehrtägig`)
1. **Token-Druck:** Trigger künstlich niedrig setzen, damit die Verdichtung früh greift. Ein Fakt vom Anfang des Laufs ist danach noch korrekt verfügbar.
2. **Vergifteter Kontext:** Ein frühes Tool-Ergebnis enthält einen falschen Wert, ein späteres korrigiert ihn. Die Ausgabe nutzt den korrigierten Wert.
3. **Artefakte:** Nach der Verdichtung stimmt die Artefakt-Liste im State mit dem Log überein.
Diese Fälle gehören in `evals/cases.jsonl` (Umsetzung im Runner: Issue #1).
