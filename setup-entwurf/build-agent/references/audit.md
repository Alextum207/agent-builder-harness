# Audit eines bestehenden Agents

## Inhalt
- Ablauf
- Die 12 Schichten
- Schnelldiagnose
- Standard-Prüfung
- Fix-Reihenfolge
- Report

## Ablauf (Quelle: E3)
1. **Umfang:** Welches System, Einstiegspunkte, Modelle, Symptome, seit wann?
2. **Belege sammeln:** Agent-Schleife, Tool-Router, Prompt-Aufbau, Memory, Logs, Configs lesen. Suchen nach:
   ```bash
   rg -n "must.*tool|always use|immer.*tool" --type md      # Tool-Pflicht nur im Prompt
   rg -n "invoke\(|messages\.create|chat\.completions" -t py # versteckte LLM-Aufrufe
   rg -n "fallback|retry|repair|re-?prompt" -t py           # stille Reparaturschleifen
   rg -n "interrupt|HumanInTheLoop" -t py                    # Freigaben vorhanden?
   ```
3. **Befunde zuordnen:** Symptom, Mechanismus, Schicht, Ursache, Beleg (`datei:zeile`), Sicherheit 0–1.
4. **Fix-Plan vorlegen und auf Freigabe warten.** Kein `Edit`/`Write` vor dem OK.
5. Nach Freigabe umsetzen, Evals laufen lassen (fehlen sie: zuerst `evals.md`).

## Die 12 Schichten
| # | Schicht | Typischer Fehler |
|---|---|---|
| 1 | System-Prompt | widersprüchliche oder aufgeblähte Anweisungen |
| 2 | Verlauf | veralteter Kontext aus früheren Runden |
| 3 | Langzeit-Memory | alte Themen in neuen Gesprächen |
| 4 | Verdichtung | Zusammenfassungen kommen als Pseudo-Fakten zurück |
| 5 | Abruf | doppelte Zusammenfassungen fressen Kontext |
| 6 | Tool-Auswahl | falsches Tool, Pflicht-Tool übersprungen |
| 7 | Tool-Ausführung | behauptet Aufruf, der nie stattfand |
| 8 | Tool-Auswertung | Ergebnis missverstanden oder ignoriert |
| 9 | Antwortformung | Format kaputt |
| 10 | Ausgabe-Plattform | UI/API verändert eine korrekte Antwort |
| 11 | Versteckte Reparatur | zweiter LLM-Durchlauf ohne Vertrag |
| 12 | Persistenz | abgelaufener Zustand als aktuell genutzt |

## Schnelldiagnose
| Frage | Wenn ja |
|---|---|
| Kann das Modell ein Pflicht-Tool überspringen und trotzdem antworten? | Tool nicht im Code erzwungen |
| Tauchen alte Inhalte in neuen Runden auf? | Memory-Verschmutzung |
| Steht dieselbe Info in Prompt, Memory und Verlauf? | Kontext-Duplikat |
| Läuft vor der Auslieferung ein zweiter LLM-Durchlauf? | versteckte Reparatur |
| Unterscheidet sich interne und ausgelieferte Antwort? | Plattform-Verfälschung |
| Kann der eigene Monolog des Agents zu Memory werden? | Memory-Vergiftung |

## Standard-Prüfung (gegen diesen Skill)
- Tool-Inputs mit Pydantic, Rückgabevertrag `status/summary/data/next_actions` (tools.md)
- Retries ≤ 3 und nur bei vorübergehenden Fehlern
- Freigabe vor irreversiblen Aktionen; Wirkung erst nach `interrupt()`
- Abbruch: `recursion_limit`, Loop-Guard
- Log pro Schritt vorhanden
- Evals vorhanden und aktuell
- Fremdinhalte als Daten markiert; Prüf-Gate aus security.md
- Bei RAG: Zitate mit Quelle
- Cache-Reihenfolge statisch → dynamisch
- `run_length` passt zum echten Lauf (Schritte und Tokens im Log); bei `lang` Verdichtung vorhanden, bei `kurz` keine unnötige Middleware (context.md)
- Keine rohen Großausgaben im Verlauf; Artefakte (Pfade, IDs) im State statt nur in einer Zusammenfassung
- `autonomy_level` gesetzt und im Code durchgesetzt (Freigabeliste passt zur Stufe)

## Fix-Reihenfolge (Code vor Prompt)
1. Tool-Pflichten und Freigaben im Code erzwingen.
2. Versteckte Reparaturschleifen entfernen oder mit klarem Vertrag versehen.
3. Kontext-Duplikate entfernen.
4. Memory-Aufnahme verschärfen (Nutzer-Korrektur schlägt Agent-Behauptung).
5. Ausgabe durchreichen statt umformen.
6. Interne Kommunikation als typisiertes JSON statt Freitext.

## Report
Reihenfolge: Befunde nach Schwere (`kritisch` → falsches Verhalten mit Überzeugung; `hoch` → häufig falsch/instabil; `mittel` → fragil/verschwenderisch; `niedrig` → kosmetisch), dann Diagnose welche Schicht was verursacht, dann geordneter Fix-Plan. Keine Einleitung, kein Lob.
