# Deploy (dauerhafter Betrieb)

Nur wenn der Agent nicht nur lokal läuft (Kunde, Webhook, Zeitplan). Muster gegen aktuelle Doku prüfen.

## Inhalt
- Bausteine
- API mit Freigabe per Link
- Traces und Event-Log
- Fallen
- Zeitplan, Alarm, Aufräumen
- Abnahme

## Bausteine
| Baustein | Wahl |
|---|---|
| Auslöser | FastAPI-Endpunkt `POST /run` (Webhook); Zeitpläne rufen denselben Endpunkt auf (cron, n8n, GitHub Actions) (Quelle: F11) |
| Zustand | `SqliteSaver` bei einem Server, `PostgresSaver` bei mehreren Instanzen oder echten Kundendaten (scaffold.md) |
| Freigabe | Benachrichtigung (Slack-Webhook oder E-Mail) mit signiertem Link → Bestätigungsseite → `Command(resume=...)` (Quelle: F6, F7) |
| Alarm | jede unbehandelte Exception → gleiche Benachrichtigung |
| Hosting | Container mit `uv`; Secrets als Umgebungsvariablen der Plattform |

Setup: `uv add fastapi uvicorn httpx` plus Checkpointer-Paket.

## API mit Freigabe per Link
```python
import hashlib, hmac, html, os, uuid
from typing import Literal
import httpx
from fastapi import BackgroundTasks, FastAPI, Form, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langgraph.types import Command
from agent import agent                      # mit persistentem Checkpointer kompiliert

API_KEY = os.environ["AGENT_API_KEY"]
SECRET = os.environ["APPROVAL_SECRET"].encode()
BASE_URL = os.environ["BASE_URL"]
NOTIFY_URL = os.environ["SLACK_WEBHOOK_URL"]
app = FastAPI()

class RunInput(BaseModel):
    task: str

def sign(thread_id: str) -> str:
    return hmac.new(SECRET, thread_id.encode(), hashlib.sha256).hexdigest()

def check_sig(thread_id: str, sig: str) -> None:
    if not hmac.compare_digest(sign(thread_id), sig):
        raise HTTPException(403)

def notify(text: str) -> None:
    httpx.post(NOTIFY_URL, json={"text": text}, timeout=10)

def execute(thread_id: str, payload) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    try:
        agent.invoke(payload, config)
        state = agent.get_state(config)
        if state.interrupts:
            actions = [a["name"] for a in state.interrupts[0].value["action_requests"]]
            notify(f"Freigabe nötig: {', '.join(actions)}\n"     # keine Inhalte/Personendaten im Kanal
                   f"{BASE_URL}/approve/{thread_id}?sig={sign(thread_id)}")
    except Exception as exc:
        notify(f"Agent-Fehler in {thread_id}: {type(exc).__name__}")   # keine Daten im Alarm
        raise

@app.post("/run")
def run(body: RunInput, bg: BackgroundTasks, x_api_key: str = Header()):
    if not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401)
    thread_id = uuid.uuid4().hex
    bg.add_task(execute, thread_id, {"messages": [{"role": "user", "content": body.task}]})
    return {"thread_id": thread_id}

@app.get("/approve/{thread_id}", response_class=HTMLResponse)
def approve_page(thread_id: str, sig: str):
    check_sig(thread_id, sig)
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    if not state.interrupts:
        return "Bereits entschieden."
    details = "<br>".join(html.escape(f"{a['name']}: {a['args']}")   # Agent-Inhalt nie roh ins HTML
                          for a in state.interrupts[0].value["action_requests"])
    return f"""<p>{details}</p>
<form method="post"><input type="hidden" name="sig" value="{html.escape(sig)}">
<button name="decision" value="approve">Freigeben</button>
<button name="decision" value="reject">Ablehnen</button></form>"""

@app.post("/approve/{thread_id}")
def approve(thread_id: str, bg: BackgroundTasks, sig: str = Form(),
            decision: Literal["approve", "reject"] = Form()):
    check_sig(thread_id, sig)
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    if not state.interrupts:
        raise HTTPException(409, "Bereits entschieden")
    n = len(state.interrupts[0].value["action_requests"])      # eine Entscheidung pro Aktion
    bg.add_task(execute, thread_id, Command(resume={"decisions": [{"type": decision}] * n}))
    return {"ok": True}
```

## Traces und Event-Log (Quelle: AWS1)
OpenTelemetry statt LangSmith: anbieterneutral, in der EU selbst betreibbar (OTLP an Collector, Jaeger oder Langfuse), keine Laufdaten an einen US-SaaS.
```python
from agent_guardrails.tracing import TracingMiddleware, run_span, setup_tracing
TRACER = setup_tracing(ROOT / "traces", CFG["log_retention_days"])        # löscht ältere Tagesdateien
middleware=[TracingMiddleware(agent_id, PRICE, POLICY), ...]               # als erstes Element: umschließt alle anderen
with run_span(TRACER, agent_id, run_id): agent.stream(...)
```
- Ein Trace pro Lauf, ein Span pro Model- und Tool-Aufruf: `gen_ai.*`-Attribute (Modell, Tokens), `cost.usd`, `latency.ms`, `tool.status`. Tool-Argumente maskiert und gekürzt.
- `case.id` (= `thread_id`) steht an jedem Span, damit der Export nicht an Parent-Ketten hängt (LangGraph führt Nodes in Threads aus).
- Event-Log: `uv run python -m agent_guardrails.tracing traces/ eventlog.csv` → Spalten `case:concept:name, concept:name, time:timestamp, org:resource, …` (XES-Namen, lädt in pm4py und Celonis). Dasselbe Format hat der P2P-Log des Test-ERP (`test-finance-agent/erp.py`), so landen Agent- und Menschen-Schritte im selben Prozessmodell.
- Betrieb: `JsonlSpanExporter` durch `OTLPSpanExporter` an einen Collector in der EU ersetzen.

## Fallen
- **Link-Scanner:** E-Mail- und Slack-Scanner rufen Links per GET auf. Deshalb löst GET nie eine Aktion aus, nur der POST-Button.
- **Doppelte Freigabe:** Vor dem Resume prüfen, ob noch ein Interrupt offen ist (409 sonst).
- **Neustart:** Mit `InMemorySaver` sind offene Freigaben nach einem Neustart weg. Im Betrieb immer persistenter Checkpointer.
- **Mehrere Instanzen:** `SqliteSaver` nur mit einer Instanz; sonst `PostgresSaver`.
- **Keine Daten in Alarmen:** Fehlermeldungen nennen Thread und Fehlertyp, keine Personendaten.
- **Endpunkt schützen:** `POST /run` nur mit API-Key; HTTPS über die Hosting-Plattform.

## Zeitplan, Alarm, Aufräumen
- Zeitplan: externer Scheduler ruft `POST /run` mit API-Key auf. Kein eigener Scheduler im Agent.
- Mehrtägige Läufe (`run_length: mehrtägig`): der Scheduler startet je Sitzung `multiday.py`; der Agent macht genau ein Paket und endet (context.md).
- Logs: täglicher Job löscht `logs/*.log` älter als `log_retention_days`.
- Checkpoints: alte Threads regelmäßig entfernen (wachsen sonst unbegrenzt) (Quelle: L3).
- Health: `GET /health` gibt 200 zurück, damit die Plattform Ausfälle erkennt.

## Abnahme
1. `POST /run` ohne Key → 401.
2. Lauf mit irreversibler Aktion → Benachrichtigung kommt, GET auf den Link löst nichts aus, POST „Ablehnen“ → keine Wirkung.
3. Server neu starten, dann freigeben → Lauf setzt korrekt fort.
4. Erzwungener Fehler → Alarm ohne Personendaten.
