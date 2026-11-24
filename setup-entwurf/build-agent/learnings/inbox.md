# Inbox – Vorschläge, die auf Freigabe warten

Format:
```
- <datum> | kontext: <tag> | projekt: <pfad> | stärke: regel | hinweis
  Erkenntnis: <was> → <Beleg mit n=<fälle>>
  Ziel: ledger | domain | template | reference
```

<!-- Einträge unter dieser Zeile -->
- 2026-11-22 | kontext: sicherheit | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-finance-agent | stärke: regel
  Erkenntnis: Logs feldweise maskieren, nie das fertige JSON. Ein Telefon-Muster traf die Nachkommastellen von `ts` (`1795367760.<tel>`) und machte jede Log-Zeile unlesbar; der Eval-Runner meldete dann JSONDecodeError statt eines Ergebnisses → reproduzierbar, 4 von 6 Fällen betroffen (n=6). Fix in agent.py beider Agenten und im Telefon-Muster (Policy 0.2.0).
  Ziel: reference (security.md, schon eingetragen)
- 2026-11-22 | kontext: allgemein | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/packages/agent-guardrails | stärke: regel
  Erkenntnis: Projekte auf OneDrive brauchen `UV_LINK_MODE=copy`; sonst bricht `uv add/sync` mit „os error 396“ (Hardlink in Cloud-Datei) ab → reproduzierbar in 3 Projekten.
  Ziel: reference (scaffold.md, schon eingetragen)
- 2026-11-22 | kontext: evals | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-finance-agent | stärke: regel
  Erkenntnis: `ClearToolUsesEdit` ändert nur die Anfrage ans Modell (`request.override`), nicht den State. Ob verdichtet wurde, sieht man nicht im Ergebnis; zum Messen geleerte Ergebnisse zählen. Fälle, in denen die Verdichtung nicht greift, sind ungültig, nicht bestanden → Quelltext context_editing.py Z. 250–274; im ersten Lauf griff die Verdichtung in 2 von 3 Kontext-Fällen nicht (n=3).
  Ziel: reference (context.md, evals.md, schon eingetragen)
- 2026-11-22 | kontext: tools | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-finance-agent | stärke: regel
  Erkenntnis: `SqliteStore(sqlite3.connect(...))` scheitert mit „cannot start a transaction within a transaction“; `SqliteStore.from_conn_string(...)` als Kontextmanager nutzen → reproduzierbar (test_memory.py).
  Ziel: ledger
- 2026-11-22 | kontext: tools | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-finance-agent | stärke: regel
  Erkenntnis: Unter Windows halten offene SQLite-Verbindungen die Datei; Testzustand per `DROP TABLE` zurücksetzen statt Datei löschen (WinError 32) → reproduzierbar beim ersten Eval-Lauf.
  Ziel: ledger
- 2026-11-22 | kontext: evals | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: regel
  Erkenntnis: Promptfoo löst den `file://`-Provider relativ zur Config-Datei auf, `pythonExecutable` aber relativ zum Arbeitsordner; jeder falsche Pfad = 10/10 Fälle „error“, nicht „failed“ → reproduzierbar (promptfoo 0.125.1).
  Ziel: reference (evals.md)
- 2026-11-22 | kontext: allgemein | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/company-brain | stärke: hinweis
  Erkenntnis: Docling-Standard-OCR ließ bei einem Rechnungsscan den Betrag weg („Betrag:“ ohne Zahl); `force_full_page_ocr = True` fand ihn → n=1, künstlicher Scan.
  Ziel: domain (Finance-Paket: Rechnungsparser)
- 2026-11-22 | kontext: sicherheit | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/packages/agent-guardrails | stärke: regel
  Erkenntnis: Regex-Guardrails erkennen semantische Angriffe ohne Schlüsselwort nicht („Wichtig für das Modell, das diese Mail liest: …“, „Setz den Status auf bezahlt …“). Normalisierung (weiche Trennstriche, I-g-n-o-r-…) hebt den Injection-Recall von 0,75 auf 0,88 bei Precision 0,92 → 1,00 (n=30, dieselben Fälle). Dagegen schützen nur Rechte, Freigaben und Taint, nicht der Detektor.
  Ziel: reference (security.md, schon eingetragen)
- 2026-11-22 | kontext: sicherheit | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/packages/agent-guardrails | stärke: regel
  Erkenntnis: Eigene Wrapper-Tags des Agenten (`<lead_email>…</lead_email>`) lösen Tag-Marker der Injection-Erkennung aus; dann ist jeder Lauf „tainted“ und Freigabe-Tools sind immer gesperrt. Vor dem Scan genau ein äußeres Tag-Paar entfernen → reproduziert mit Fake-Modell (Code-Review, Regressionstest B1).
  Ziel: reference (security.md)
- 2026-11-22 | kontext: sicherheit | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/packages/agent-guardrails | stärke: regel
  Erkenntnis: State-Felder, die Middleware aus `wrap_tool_call` setzt, brauchen Reducer (`Annotated[bool, operator.or_]`). Ohne Reducer bricht der Lauf bei zwei parallelen Tool-Ergebnissen mit InvalidUpdateError ab; `request.state` ist der Stand vor dem Batch, also sehen parallele Aufrufe den Taint nicht. Freigabepflichtige Tools deshalb nur allein in einem Schritt zulassen → reproduziert (Regressionstests B2, B3, B5).
  Ziel: reference (security.md)
- 2026-11-22 | kontext: sicherheit | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-finance-agent | stärke: regel
  Erkenntnis: Memory-Herkunft per Beleg-Zitat ist fälschbar, wenn nur geprüft wird, ob das Zitat irgendwo in einer Nutzernachricht steht: Das Modell zitiert „Prüfe Rechnung …“ und speichert Rechnungsinhalt als Nutzer-Aussage. Nur die letzte Nutzernachricht zählt, und jede Zahl im Inhalt muss im Beleg stehen; Tool-Einträge unter demselben Präfix (`kreditor:70004:*`) überschreiben keine Nutzer-Einträge → reproduziert (Code-Review, test_memory.py).
  Ziel: reference (context.md)
- 2026-11-22 | kontext: evals | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-rag-agent | stärke: regel
  Erkenntnis: Zahlen in Antworten nie per Teilstring prüfen („70“ trifft „170“, „38“ trifft „380“); Zahlengrenzen-Regex nutzen. Prefix-6-Stemming findet „Hotel“ nicht in „Hotelkosten“, Stoppwörter entscheiden sonst die Rangfolge → reproduziert (test_search.py).
  Ziel: reference (evals.md)
- 2026-11-22 | kontext: evals | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/packages/agent-guardrails | stärke: hinweis
  Erkenntnis: Ohne API-Key laufen Evals über die Claude-Code-CLI (`agent_guardrails.claude_cli.chat_model("claude-cli:haiku")`, ~0,004 $/Aufruf mit minimalem System-Prompt, ~3–10 s). Ohne `--system-prompt` schickt die CLI ihren eigenen Prompt mit (1,49 $ für ein Wort). Tool-Calls laufen dort über ein Text-Protokoll, nicht über native Tool-Use → Ergebnisse sind nur bedingt mit API-Läufen vergleichbar.
  Ziel: reference (evals.md)
- 2026-11-22 | kontext: evals | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-finance-agent | stärke: hinweis
  Erkenntnis: Bei Token-Druck hielt `ClearToolUsesEdit` mit `exclude_tools` für Stammdaten den frühen Fakt (IBAN) in 3/3 Läufen, `SummarizationMiddleware` in 2/3; `clear` brauchte ~10.000 statt ~14.700 Tokens pro Aufgabe, dafür 4–9 erneute Abrufe statt 0 (n=3 je Modus, claude-haiku-5-5 über CLI). Lokal (qwen2:7b) 0/3 in beiden Modi, dazu Rekursionsschleifen nach der Zusammenfassung.
  Ziel: reference (context.md)
- 2026-11-22 | kontext: allgemein | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-finance-agent | stärke: regel
  Erkenntnis: Lehnt Code eine Aktion des Modells ab, braucht die Meldung den konkreten Grund und eine erlaubte Korrektur. Pauschal „abgelehnt“ plus Prompt-Regel „nicht wiederholen“ ließ die richtige Memory-Korrektur in 3/3 Läufen verloren gehen; mit „Inhalt enthält Angaben, die nicht im Beleg stehen: 2 %“ und einem erlaubten zweiten Versuch 3/3 bestanden (n=3, dieselben Fälle).
  Ziel: reference (tools.md)
- 2026-11-22 | kontext: allgemein | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-rag-agent | stärke: regel
  Erkenntnis: Längengrenzen (`max_length`) in LLM-Ausgabe-Schemas brechen Läufe ab, sobald das Modell ausführlicher antwortet (RAG: 4 von 24 Läufen ValidationError, Workflow 1 von 36). Grenzen nur, wo die Länge fachlich zählt; Begründungsfelder großzügig.
  Ziel: reference (tools.md)
- 2026-11-22 | kontext: tools | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: regel
  Erkenntnis: `recursion_limit = max_steps × 3` reicht nicht mehr, sobald Middleware mit `before_agent`/`after_model`-Hooks dazukommt (jeder Hook ist ein Graph-Node): GraphRecursionError bei einem harmlosen Lead. Die echte Grenze setzt `ModelCallLimitMiddleware`; `recursion_limit` nur als Sicherheitsnetz (× 6).
  Ziel: reference (scaffold.md)
