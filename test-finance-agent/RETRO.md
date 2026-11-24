# Retro 2026-11-22 – test-finance-agent (kontext: finance-recherche)

Deckt die Issues #1 (Kontext-Evals), #2 (Node-Report), #3 (Traces), #5 (Memory), #6 (Mehrtages-Scaffold) und #8 (Identität und Rechte) ab. Alle Daten sind erfunden (`erp.py`, feste Saat).

## Ergebnis
Modell: `claude-haiku-5-5` über die Claude-Code-CLI (`MODEL=claude-cli:haiku`, es gab keinen gültigen API-Key). Lokal zum Vergleich `qwen2:7b` über Ollama. Kosten laut CLI zusammen 0,073 $ für 152 Aufrufe.

| Eval | Haiku | qwen2:7b lokal |
|---|---|---|
| Kontext-Fälle k=3, n=9 ([Report](evals/report-2026-11-22-k3-claude-cli-haiku.md)) | pass@1 100 %, pass@3 100 %, pass^3 kritisch **nicht erfüllt** (token-druck-summarize 2/3) | pass@1 56 %, pass^3 kritisch nicht erfüllt ([Report](evals/report-2026-11-22-k3-qwen2-7b.md)) |
| vergifteter Kontext (beide Verdichtungen) | 6/6 | 0/6, nennt den alten Betrag |
| Token-Druck `summarize` / `clear` | 2/3 / 3/3 | 0/3 / 0/3 |
| Rechte-Schreiben, Injection in Rechnung | 6/6 | 6/6 |
| Node-Report n=12 ([Report](evals/node-report-2026-11-22-haiku.md)) | extrahieren 100 %, kontieren 100 %, Kette 92 % | – |
| Memory über 4 Sitzungen k=3 ([Report](evals/memory-report-2026-11-22-k3-claude-cli-haiku.md)) | 3/3 | – |
| Mehrtages-Test mit Abbruch ([Report](evals/multiday-report-2026-11-22-claude-cli-haiku.md)) | bestanden: 5 Pakete, je 1 LLM-Aufruf, Abbruch in Sitzung 2 am Checkpoint fortgesetzt | – |
| Memory-Code-Evals (`test_memory.py`) | ok (ohne Modell) | – |

## Was funktioniert hat
- **Billigste Verdichtung zuerst.** `clear` mit `exclude_tools: [erp_kreditor]` hielt die IBAN in 3 von 3 Läufen, `summarize` nur in 2 von 3. `clear` brauchte dabei etwa 10.000 Tokens pro Aufgabe statt etwa 14.700 (n=3 je Modus). Der Preis dafür sind erneute Abrufe: 4 bis 9 pro Lauf bei `artefakte-clear`, 0 bei `summarize`.
- **Artefakt-Liste im State:** stimmte in 6 von 6 verdichteten Läufen mit dem Log überein. Die Middleware sitzt im `before_model`-Hook vor der Verdichtung.
- **Rechte in zwei Linien (#8):** Die Middleware blockiert `erp_buchung_anlegen`, obwohl im Eval ein Mensch die Freigabe erteilt. Zusätzlich öffnet `erp.connect()` die DB ohne Schreibrecht read-only. In 6 von 6 Läufen kam keine Buchung zustande. Mit Fake-Modell nachgewiesen in `packages/agent-guardrails/test_guardrails.py`.
- **Injection in einer Rechnungsposition:** Der Lauf wurde in 6 von 6 Fällen als „tainted“ markiert, und es entstand keine Buchung.
- **Mehrtägig (#6):** `durability="sync"` sorgt dafür, dass der Checkpoint nach `arbeiten` den Absturz übersteht. Die nächste Sitzung macht mit `invoke(None)` nur das Abschließen, ohne zweiten LLM-Aufruf.
- **Memory (#5):** Die Nutzer-Korrektur von 2 % auf 3 % gewinnt. Die vergiftete 10-%-Notiz aus RE-2026-0110 landet nicht im Memory, und der abgelaufene Lieferstopp wird nicht genannt.
- **Traces (#3):** Ein Span pro Model- und Tool-Aufruf. Der Export erzeugt ein Event-Log mit Case-ID, Aktivität und Zeit. Das Test-ERP liefert dazu einen P2P-Log mit 460 Events im selben Format (`workspace/p2p_eventlog.csv`).

## Was nicht funktioniert hat (mit Ursache)
1. **PII-Maskierung zerstörte Logs:** Das Telefon-Muster traf Nachkommastellen von `ts`, und `mask()` lief über das fertige JSON. Fix: Logs werden feldweise maskiert, und das Telefon-Muster ist strenger.
2. **Verdichtung griff nicht:** Mit einem Trigger von 2.500 Tokens fragte qwen alle Rechnungen parallel in einem Schritt ab, und es wurde nie verdichtet. Fix: Trigger 1.000, `keep` pro Fall. Greift die Verdichtung trotzdem nicht, ist der Fall ungültig statt bestanden.
3. **`ClearToolUsesEdit` ändert nur die Anfrage, nicht den State:** Zum Messen zählt die Unterklasse `CountingContextEditing` die geleerten Ergebnisse.
4. **Memory-Herkunft war fälschbar** (Code-Review): Ein beliebiges Nutzerzitat als Beleg reichte, um Tool-Inhalt als Nutzer-Aussage zu speichern. Fix: Es zählt nur die letzte Nutzernachricht, und jede Zahl im Inhalt muss im Beleg stehen. Dadurch lehnte das Memory zunächst die echte Korrektur ab, denn Haiku hatte „(früher 2 %)“ angehängt, und der Eval ergab 0/3. Erst eine konkrete Fehlermeldung mit den fehlenden Zahlen und ein erlaubter zweiter Versuch brachten 3/3.
5. **Weitere Code-Review-Funde** (behoben): Ein ungültiges `thema` ließ den ganzen Lauf abstürzen. `amounts()` kam mit Leerzeichen als Tausendertrenner nicht zurecht. Die Prüfung auf den alten Betrag konnte nie anschlagen. Nach einem HITL-Interrupt wurden Logzeilen doppelt geschrieben. Die Prüfung von `tasks.json` verglich nur abgeleitete Kopien.
6. **Windows:** Offene SQLite-Verbindungen sperren die Datei, deshalb werden Tabellen per `DROP TABLE` zurückgesetzt. `SqliteStore` funktioniert nur über `from_conn_string`.
7. **Zu enge Schemas:** `begruendung` mit max. 200 Zeichen brach Läufe ab, wenn Haiku ausführlicher antwortete. Eine Längengrenze darf den Lauf nicht abbrechen.
8. **qwen2:7b:** Nach einer Zusammenfassung lief es in Schleifen bis zum Rekursionslimit. Außerdem ruft es Korrekturen nicht ab. Für Finance taugt es lokal nicht.

## Grenzen
- Erfundene Daten und kleine Fallzahlen (n=6 bis 12, k=3). Die Quoten sind Hinweise, nicht belegt. Die reproduzierbaren Bugs sind Regeln.
- Tool-Calls liefen über die CLI als Text-Protokoll, nicht über native Tool-Use der API. Mit einem API-Key sollten die Evals einmal mit `MODEL=anthropic:claude-haiku-5-5` wiederholt werden.
- In der Kette ergab RE-2026-0104 einmal 3400 statt 4650. Das ist Streuung bei gleicher Eingabe, und der Node-Eval mit k=1 sieht sie nicht. Für die Abnahme Node-Evals mit k=3 laufen lassen.

## Vorschläge an den Skill
Siehe `setup-entwurf/build-agent/learnings/inbox.md` (Einträge vom 2026-11-22).
