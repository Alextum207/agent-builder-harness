# Kosten und Caching

## Modell-Routing nach Aufgabentyp
| Aufgabe | Modell (Stand prüfen) |
|---|---|
| Klassifizieren, extrahieren, Routing-Entscheidung, Judge | `claude-haiku-5-5` |
| Standard-Agent-Arbeit | `claude-sonnet-5-5` |
| schwierige Planung, lange Analysen | `claude-opus-5-5` |
- Routing im Code nach Node/Aufgabe, nicht nach Textlänge. Jeder Node bekommt sein Modell aus `config.md`, keine verstreuten Modellnamen im Code.
- Preise nicht hart codieren; bei Bedarf aktuelle Preise nachschlagen.
- Erst günstig starten, teureres Modell nur, wenn Evals es belegen.

## Budget pro Lauf
- `budget_usd` aus `config.md`. Kosten pro Aufruf aus den Usage-Daten der Antwort (`usage_metadata`) summieren und ins Log schreiben.
- Budget erreicht: Lauf anhalten und den Menschen fragen (weiter / abbrechen), nicht stillschweigend weiterlaufen und nicht hart abstürzen.
- Retries nur bei vorübergehenden Fehlern (siehe tools.md), sonst verbrennen sie Budget.

## Prompt-Caching (Quelle: C1, A4)
Reihenfolge beim Cache-Präfix: **Tools → System → Messages**. Ein Treffer braucht ein exakt gleiches Präfix.
- Ganz oben und unverändert: Tool-Definitionen, System-Prompt aus `config.md`, SOPs, feste Beispiele.
- Ganz unten: Nutzereingabe, frisch abgerufene RAG-Chunks, Zeitstempel, Request-Daten.
- Nie Zeitstempel oder IDs in den System-Prompt; Tool-Liste nicht pro Anfrage ändern (invalidiert alles).
- Mindestlänge: 512 Tokens für die 5.5-Modelle, sonst 1.024+; kürzere Präfixe werden nicht gecacht.
- Cache-Lesen kostet einen Bruchteil des normalen Inputs, Cache-Schreiben etwas mehr. Lohnt sich ab der zweiten Wiederverwendung innerhalb der TTL (5 min Standard).
- Umsetzung mit LangChain: `cache_control` auf dem letzten statischen Block bzw. die Prompt-Caching-Middleware von `langchain-anthropic`. API in der Doku prüfen.

## Messen
- Pro Lauf loggen: `cache_read_input_tokens`, `cache_creation_input_tokens`, `input_tokens`, `output_tokens`, Latenz.
- Diese Werte stehen im Eval-Report. Eine Änderung, die Evals besteht, aber Kosten oder Latenz deutlich verschlechtert, ist eine Regression.
