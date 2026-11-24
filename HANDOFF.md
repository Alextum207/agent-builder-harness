# Handoff: Harness

Stand 2026-11-24. Für den nächsten Agenten. Zuerst [`AGENTS.md`](AGENTS.md) lesen.

## Wo das Produkt ist
Das Produkt **eyecraft** (Wissen von der Baustelle für Handwerksbetriebe) liegt seit dem 2026-11-24 im eigenen, privaten Repo [Alextum207/eyecraft](https://github.com/Alextum207/eyecraft), mit Spec, Handoff und Issues. Die Produkt-Issues wurden von hier dorthin verschoben (#18 und #28–#41 sind dort jetzt #1–#15). Die frühere Process-Intelligence-Spec ([`SPEC-open-process-intelligence.md`](SPEC-open-process-intelligence.md)) ruht.

Dieses Repo bleibt der **Harness**: Skill `build-agent`, `agent-guardrails`, Company Brain und die Testagenten. eyecraft bindet die Bausteine als Git-Abhängigkeit ein.

## Was eyecraft vom Harness braucht
1. **PRs mergen, in dieser Reihenfolge:** #17 (Guardrails, Brain, Testagenten), dann #26 (frühere Spec), dann #27 (Mail-Konnektor), dann den Branch `docs/handwerk-plan`. Auf `main` gibt es `packages/` noch nicht.
2. **Company Brain als installierbares Paket** (für eyecraft #4): `company-brain` hat heute `package = false`.
3. **RAG-Teil aus `test-rag-agent` als wiederverwendbares Modul** (für eyecraft #5).

Ob 2 und 3 hier oder in eyecraft gelöst werden, entscheidet das jeweilige eyecraft-Issue.

## Offene Harness-Issues
#10–#14 und #16 (API-Gegenlauf, Inbox-Freigabe, zweite Guardrail-Schicht, Node-Evals, Live-Konnektoren, Branch-Schutz), dazu #24 (wird mit PR #27 geschlossen).

## Fallen auf diesem Rechner
- OneDrive: `UV_LINK_MODE=copy`. Wenn uv mit „Zugriff verweigert“ an einem alten `*.dist-info` hängt, den Ordner mit PowerShell `Remove-Item -Recurse -Force` löschen und `uv sync --reinstall-package <paket>` ausführen.
- TLS-Proxy: `env -u SSL_CERT_FILE uv … --system-certs`, im Code `truststore.inject_into_ssl()`.
- Windows-Konsole: `PYTHONIOENCODING=utf-8`. `python -I` ignoriert Umgebungsvariablen; dann `sys.stdout` auf UTF-8 umstellen.
- SQLite unter Windows: Offene Verbindungen sperren die Datei. Testzustand per `DROP TABLE` zurücksetzen statt die Datei zu löschen; `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)`.
- Claude-CLI: immer mit eigenem `--system-prompt` aufrufen, sonst kostet ein Aufruf etwa 1,50 $ statt 0,004 $. Ohne Shell starten. `sonnet` ergibt Sonnet 5.5.
- Evals mit LLM-Judge: Der Judge braucht alle Belege, die der Agent hatte, sonst bewertet er korrekte Aussagen als unbelegt.
- Bash-Heredocs mit deutschen Anführungszeichen und Backticks sind fehleranfällig. Längere Texte für `gh` als Datei schreiben und `--body-file` nutzen.

## Nicht tun
- Nichts committen, was in `.git/info/exclude` steht, und nicht danach fragen, was es ist.
- Keine Abhängigkeit mit ELv2, BSL oder SSPL im Kern.
- Nicht auf `main` committen, nicht ohne Anweisung pushen oder mergen.
