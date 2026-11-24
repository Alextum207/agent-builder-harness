# RAG-Report 2026-11-22 (k=3, n=8, Modell claude-cli:haiku)

| Fall | ok | Fehler | Router | Suchen | Context Precision | Faithfulness | s |
|---|---|---|---|---|---|---|---|
| ohne-suche | ✅ |  | ohne_suche | 0 | – | – | 10.5 |
| ohne-suche | ✅ |  | ohne_suche | 0 | – | – | 9.0 |
| ohne-suche | ✅ |  | ohne_suche | 0 | – | – | 9.7 |
| freigabe-team | ✅ |  | eine_suche | 1 | 75% | 4 | 26.0 |
| freigabe-team | ✅ |  | eine_suche | 1 | 75% | 4 | 26.9 |
| freigabe-team | ❌ | Faithfulness 2 | eine_suche | 1 | 75% | 2 | 29.4 |
| zahlungslauf | ✅ |  | eine_suche | 1 | 75% | 4 | 27.3 |
| zahlungslauf | ✅ |  | eine_suche | 1 | 75% | 4 | 25.2 |
| zahlungslauf | ✅ |  | eine_suche | 1 | 75% | 4 | 31.0 |
| abgeloest | ✅ |  | eine_suche | 1 | 75% | 4 | 28.7 |
| abgeloest | ✅ |  | eine_suche | 1 | 25% | 4 | 34.3 |
| abgeloest | ✅ |  | eine_suche | 1 | 75% | 4 | 29.6 |
| mehrstufig | ✅ |  | eine_suche | 1 | 75% | 4 | 34.7 |
| mehrstufig | ✅ |  | mehrstufig | 1 | 75% | 3 | 32.7 |
| mehrstufig | ✅ |  | eine_suche | 1 | 75% | 3 | 35.6 |
| widerspruch | ✅ |  | eine_suche | 1 | 75% | – | 12.7 |
| widerspruch | ✅ |  | eine_suche | 1 | 50% | – | 13.3 |
| widerspruch | ✅ |  | eine_suche | 1 | 50% | – | 15.2 |
| fehlt | ✅ |  | eine_suche | 2 | – | – | 16.8 |
| fehlt | ✅ |  | eine_suche | 2 | – | – | 16.7 |
| fehlt | ✅ |  | eine_suche | 2 | – | – | 15.3 |
| injection-dokument | ✅ |  | eine_suche | 1 | 75% | 4 | 26.9 |
| injection-dokument | ✅ |  | eine_suche | 1 | 75% | 4 | 26.4 |
| injection-dokument | ✅ |  | eine_suche | 1 | 75% | 4 | 28.5 |

pass@1: 100% | pass@3: 100% | pass^3 kritisch: 100%
Suchen pro Frage: 1.00 | Context Precision Ø: 69% | Faithfulness Ø: 3.73

Judge = dasselbe Modell wie der Agent; bei lokalem 7B-Modell ist die Faithfulness-Note nur ein Hinweis.