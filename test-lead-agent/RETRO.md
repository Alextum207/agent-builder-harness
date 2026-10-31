# Retro 2026-10-13 – test-lead-agent (kontext: lead-qualification)

## Ergebnis
Evals (n=6, k=3, claude-haiku-5-5): pass@1 100 % | pass@3 100 % | pass^3 kritisch 100 % | Kosten/Lauf 0,00084 $ | Latenz 4–7 s | 3–4 Model-Calls pro Lauf.
Prompt-Caching greift ab dem 2. Model-Call (1.500–2.100 Tokens Cache-Read).

## Was funktioniert hat
- `create_agent` + `HumanInTheLoopMiddleware`: `mail_send` stoppt vor Ausführung, Ablehnung hinterlässt keine Wirkung (Outbox leer, 18/18).
- Fremdinhalt in `<lead_email>`-Tags + Regel „Daten, keine Anweisungen“: Injection-Fall 3/3 abgewehrt (kein Stufe A, keine Mail an Angreifer).
- Log-Maskierung: keine Klartext-Adresse in 18 Logs.
- Tool-Vertrag `status/summary/data/next_actions`: Agent folgt `next_actions` (Lookup → Score → Mail).
- Middleware-Namen aus dem Skill existieren alle (langchain 1.4.5, langgraph 1.2.15).

## Was nicht funktioniert hat (mit Ursache)
1. **Stille Ausfälle:** `ModelRetryMiddleware` hat Default `on_failure="continue"` und gibt nach dem letzten Versuch eine normale AI-Nachricht mit Fehlertext zurück. Folge: Injection-Eval „bestanden“, obwohl kein Modell lief. Fix: `on_failure="error"`.
2. **Resume-Format:** HITL erwartet eine Entscheidung pro `action_request`; das Skill-Muster lieferte genau eine (Absturz bei 2 gleichzeitigen Aktionen). Fix: Liste über `request["action_requests"]`.
3. **Zertifikate:** Netzwerk-Monitor auf dem Rechner bricht TLS auf; uv (wegen `SSL_CERT_FILE`→certifi) und httpx scheitern. Fix: `env -u SSL_CERT_FILE uv … --system-certs`, im Code `truststore.inject_into_ssl()`.
4. **Log-Ballast:** `str(msg.content)` loggt rohe Content-Blöcke inkl. Thinking-Signaturen. Fix: `msg.text`.
5. **uv init** legte eine Paketstruktur (`src/`, build-system) an, die ein Agent nicht braucht. Fix: `uv init --bare` bzw. `[tool.uv] package = false`.

## Wiederverwendet aus Skill
Scaffold-Muster (mit den Fixes oben), Tool-Vertrag, Eval-Format, Sicherheits-Prüf-Gate. Keine Domain-/Template-Dateien vorhanden (erstes Projekt).

## Grenzen
- n=6 Fälle, erfundene Daten: Qualitätsaussagen sind nur „Hinweis“. Die Bugs 1–5 sind reproduzierbar („Regel“).
- Kein LLM-Judge-Fall, kein Deploy getestet.

## Vorschläge an den Skill
Siehe `learnings/inbox.md` des Skills.
