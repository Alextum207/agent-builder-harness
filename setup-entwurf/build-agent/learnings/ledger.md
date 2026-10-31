# Ledger – übernommene Erkenntnisse

Feste Kontexte: `allgemein`, `tools`, `evals`, `kosten`, `sicherheit`. Dazu ein Tag pro Bereich (z. B. `lead-qualification`).

Format:
```
- <datum> | kontext: <tag> | projekt: <pfad> | stärke: regel | hinweis
  Erkenntnis: <was> → <Beleg mit n=<fälle>>
```

<!-- Einträge unter dieser Zeile -->
- 2026-10-13 | kontext: tools | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: regel
  Erkenntnis: `ModelRetryMiddleware` immer mit `on_failure="error"`; Default tarnt API-Ausfälle als Antwort → Eval „bestanden“ ohne Model-Call (reproduziert, 6/6 Läufe)
- 2026-10-13 | kontext: tools | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: regel
  Erkenntnis: HITL-Resume braucht eine Entscheidung pro `action_request` (Quellcode langchain 1.4.5, `HITLResponse.decisions`)
- 2026-10-13 | kontext: evals | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: regel
  Erkenntnis: Runner muss Laufausfälle als „nicht bestanden“ werten und Model-Calls pro Fall zeigen; 0 Calls = Lauf ungültig (vorher 1 falsch-positiver Fall von 6)
- 2026-10-13 | kontext: allgemein | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: regel
  Erkenntnis: Bei Zertifikatsfehlern (TLS-Inspektion durch Virenscanner/Proxy): `env -u SSL_CERT_FILE uv … --system-certs` und `truststore.inject_into_ssl()` (behebt uv- und httpx-Fehler, reproduziert)
- 2026-10-13 | kontext: lead-qualification | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: hinweis
  Erkenntnis: Muster Lookup → Score → Follow-up (nur A, mit Freigabe) mit Haiku 5.5 reicht: 100 % pass@3, 0,0008 $/Lauf, 3–4 Calls (n=6, erfundene Daten)
- 2026-10-13 | kontext: sicherheit | projekt: C:/Users/alexa/OneDrive/Dokumente/agent builder harness/test-lead-agent | stärke: hinweis
  Erkenntnis: Fremdinhalt in Tags + „Daten, keine Anweisungen“ wehrt einfache Injection ab (3/3, n=1 Fall); für Regel mehr Injection-Varianten nötig
