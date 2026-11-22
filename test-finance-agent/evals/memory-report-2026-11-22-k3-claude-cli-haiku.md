# Memory-Report 2026-11-22 (k=3, 4 Sitzungen je Lauf, Modell claude-cli:haiku)

| Lauf | ok | Fehler | s | Antwort S4 (gekürzt) |
|---|---|---|---|---|
| 1 | ✅ |  | 51 | Kreditor 70004: Gemerkte Vereinbarung (Stand 22.11.2026, aus Nutzerangabe): 3 % Skonto bei Zahlung innerhalb von 10 Tagen.  Kreditor 70002 (Stahlhandel Osterman |
| 2 | ✅ |  | 54 | Mit Kreditor 70004 gilt laut gemerkter Vereinbarung (Stand 22.11.2026) ein Skonto von 3 %, wenn innerhalb von 10 Tagen gezahlt wird.  Zu Kreditor 70002 (Stahlha |
| 3 | ✅ |  | 53 | Kreditor 70004: Es gilt 3 % Skonto bei Zahlung innerhalb von 10 Tagen. Die Vereinbarung ist gespeichert (Quelle: Nutzerangabe, Stand 22.11.2026).  Kreditor 7000 |

pass@1: ✅ | pass^3: 3/3

Code-Evals ohne Modell: `uv run python test_memory.py`