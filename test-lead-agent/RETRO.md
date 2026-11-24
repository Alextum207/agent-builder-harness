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

# Nachtrag 2026-11-22 – zentrale Guardrails, Traces, Red-Teaming (Issues #3, #7, #9)

## Ergebnis
Modell `claude-haiku-5-5` über die Claude-Code-CLI (`MODEL=claude-cli:haiku`, kein gültiger API-Key). Policy `agent-guardrails 0.3.0`.

| Lauf | Ergebnis |
|---|---|
| Evals k=3, n=8 (inkl. der zwei neuen Red-Team-Fälle) | pass@1 100 %, pass@3 100 %, pass^3 kritisch 100 % ([Report](evals/report-2026-11-22-k3-claude-cli-haiku.md)) |
| Red-Teaming mit Promptfoo 0.125.1, 10 Fälle über `agent.run()` ([Config](evals/redteam/promptfooconfig.yaml)) | 10/10: kein Angriff erzwingt Stufe A, keine Mail an fremde Adressen, die harmlosen Fälle ergeben A und B |
| Trace eines echten Laufs → Event-Log ([CSV](evals/eventlog-example.csv)) | 7 Events mit Case-ID, Aktivität, Zeit und Status; Telefonnummer aus der Mail in 0 Trace- und Logdateien |

## Was neu ist
- Der Agent bindet `packages/agent-guardrails` ein: Freigabeliste aus `policy.json`, `GuardrailMiddleware`, `TracingMiddleware`, Maskierung aus der zentralen Policy.
- Lücken aus dem Red-Teaming stehen jetzt als Fälle in `evals/cases.jsonl` (`injection-semantisch`, `exfiltration-zweitadresse`).

## Was nicht funktioniert hat (mit Ursache)
1. **Jeder Lauf war „tainted“** (Code-Review): Der eigene Wrapper `<lead_email>` traf den Tag-Marker der Policy. Fix im Paket: Vor dem Scan wird genau ein äußeres Tag-Paar entfernt.
2. **Promptfoo-Pfade:** Der `file://`-Provider gilt relativ zur Config, `pythonExecutable` relativ zum Arbeitsordner. Ein JavaScript-Assert muss `score` zurückgeben, sonst sind alle Fälle `error`.
3. **CLI-Brücke:** Haiku schreibt echte Zeilenumbrüche in JSON-Strings (Mailtext). `json.loads` im Strict-Modus scheiterte, und der Tool-Call kam als Text zurück. Fix: `strict=False` und eine Nachfrage, wenn ein Tool-Call unlesbar ist.
4. **`recursion_limit = max_steps × 3`** reichte mit den neuen Middleware-Hooks nicht (GraphRecursionError bei einem harmlosen Lead). Jetzt × 6 als Sicherheitsnetz; die echte Grenze setzt `ModelCallLimitMiddleware`.
