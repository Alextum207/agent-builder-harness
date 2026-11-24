"""Traces pro Model- und Tool-Aufruf (OpenTelemetry) und Export als Event-Log (Issue #3).

Warum OpenTelemetry statt LangSmith: anbieterneutral, in der EU selbst betreibbar (Collector, Jaeger, Langfuse
nehmen OTLP an), keine Daten an einen US-SaaS. Attribute folgen den GenAI-Konventionen (gen_ai.*).

    tracer = setup_tracing(ROOT / "traces", retention_days=30)
    middleware=[TracingMiddleware(agent_id, price_usd_per_mtok, policy), ...]
    with run_span(tracer, agent_id, case_id): agent.invoke(...)
    uv run python -m agent_guardrails.tracing <traces-ordner> <ausgabe.csv>   → Event-Log
"""
import csv
import datetime as dt
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage
from langgraph.config import get_config
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import Status, StatusCode

from . import Policy, _text, load_policy


def _iso(ns: int) -> str:
    return dt.datetime.fromtimestamp(ns / 1e9, dt.timezone.utc).isoformat(timespec="milliseconds")


class JsonlSpanExporter(SpanExporter):
    """Eine Datei pro Tag. Für Betrieb stattdessen OTLPSpanExporter an einen Collector in der EU."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def export(self, spans) -> SpanExportResult:
        with (self.folder / f"{dt.date.today()}.jsonl").open("a", encoding="utf-8") as f:
            for s in spans:
                f.write(json.dumps({
                    "trace_id": f"{s.context.trace_id:032x}", "span_id": f"{s.context.span_id:016x}",
                    "parent_id": f"{s.parent.span_id:016x}" if s.parent else None, "name": s.name,
                    "start": _iso(s.start_time), "end": _iso(s.end_time), "status": s.status.status_code.name,
                    "attributes": dict(s.attributes or {}),
                }, ensure_ascii=False) + "\n")
        return SpanExportResult.SUCCESS


def prune(folder: Path, retention_days: int) -> int:
    """Aufbewahrung nach log_retention_days aus config.md."""
    cutoff, n = dt.date.today() - dt.timedelta(days=retention_days), 0
    for f in Path(folder).glob("*.jsonl"):
        try:
            old = dt.date.fromisoformat(f.stem) < cutoff
        except ValueError:
            continue
        if old:
            f.unlink()
            n += 1
    return n


def setup_tracing(folder: Path, retention_days: int = 30) -> trace.Tracer:
    prune(folder, retention_days)
    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):     # nur einmal pro Prozess setzen
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(JsonlSpanExporter(folder)))
        trace.set_tracer_provider(provider)
    return trace.get_tracer("agent-harness")


def _case_id() -> str:
    try:
        return str(get_config()["configurable"]["thread_id"])
    except Exception:
        return "unbekannt"


@contextmanager
def run_span(tracer: trace.Tracer, agent_id: str, case_id: str):
    """Ein Trace pro Lauf. case.id steht zusätzlich an jedem Span, damit der Export nicht von Parent-Ketten abhängt."""
    with tracer.start_as_current_span(f"invoke_agent {agent_id}") as span:
        span.set_attributes({"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": agent_id, "case.id": case_id})
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, type(e).__name__))
            raise
        span.set_status(Status(StatusCode.OK))


class TracingMiddleware(AgentMiddleware):
    def __init__(self, agent_id: str, price_usd_per_mtok: dict, policy: Policy | None = None):
        super().__init__()
        self.agent_id, self.price = agent_id, price_usd_per_mtok
        self.policy = policy or load_policy()
        self.tracer = trace.get_tracer("agent-harness")

    def wrap_model_call(self, request, handler):
        model = getattr(request.model, "model", None) or getattr(request.model, "model_name", "?")
        with self.tracer.start_as_current_span(f"chat {model}") as span:
            span.set_attributes({"gen_ai.operation.name": "chat", "gen_ai.request.model": str(model),
                                 "gen_ai.agent.name": self.agent_id, "case.id": _case_id()})
            t0 = time.perf_counter()
            try:
                response = handler(request)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, type(e).__name__))
                raise
            msgs = getattr(response, "result", None) or [response]
            u = getattr(msgs[-1], "usage_metadata", None) or {}
            cost = (u.get("input_tokens", 0) * self.price["input"] + u.get("output_tokens", 0) * self.price["output"]) / 1e6
            calls = [c["name"] for c in getattr(msgs[-1], "tool_calls", None) or []]
            span.set_attributes({"gen_ai.usage.input_tokens": u.get("input_tokens", 0),
                                 "gen_ai.usage.output_tokens": u.get("output_tokens", 0),
                                 "cost.usd": round(cost, 8), "latency.ms": round((time.perf_counter() - t0) * 1000),
                                 "gen_ai.response.tool_calls": ",".join(calls)})
            span.set_status(Status(StatusCode.OK))
            return response

    def wrap_tool_call(self, request, handler):
        name = request.tool_call["name"]
        with self.tracer.start_as_current_span(f"execute_tool {name}") as span:
            span.set_attributes({"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": name,
                                 "gen_ai.agent.name": self.agent_id, "case.id": _case_id(),
                                 "tool.args": self.policy.mask(json.dumps(request.tool_call["args"], ensure_ascii=False))[:500]})
            t0 = time.perf_counter()
            try:
                result = handler(request)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, type(e).__name__))
                raise
            msg = result if isinstance(result, ToolMessage) else next(
                (m for m in (getattr(result, "update", None) or {}).get("messages", []) if isinstance(m, ToolMessage)), None)
            status = "ok"
            if msg is not None:
                try:
                    status = json.loads(_text(msg.content)).get("status", "ok")
                except (ValueError, AttributeError):
                    status = "error" if msg.status == "error" else "ok"
            span.set_attributes({"tool.status": status, "latency.ms": round((time.perf_counter() - t0) * 1000)})
            span.set_status(Status(StatusCode.OK) if status == "ok" else Status(StatusCode.ERROR, status))
            return result


EVENTLOG_COLUMNS = ["case:concept:name", "concept:name", "time:timestamp", "time:start", "org:resource",
                    "status", "tokens_in", "tokens_out", "cost_usd", "trace_id"]


def export_eventlog(folder: Path, out: Path) -> int:
    """Spans → Event-Log (CSV, XES-Spaltennamen). Lädt in pm4py (read_csv + format_dataframe) und Celonis.
    Case = Lauf, Aktivität = Agent-Lauf / Modell / Tool, Zeitstempel = Ende des Spans."""
    rows = []
    for f in sorted(Path(folder).glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            s = json.loads(line)
            a = s["attributes"]
            op = a.get("gen_ai.operation.name")
            activity = {"invoke_agent": "Agent-Lauf",
                        "chat": "Modell entscheidet",
                        "execute_tool": f"Tool {a.get('gen_ai.tool.name')}"}.get(op, s["name"])
            rows.append({"case:concept:name": a.get("case.id", s["trace_id"]), "concept:name": activity,
                         "time:timestamp": s["end"], "time:start": s["start"], "org:resource": a.get("gen_ai.agent.name"),
                         "status": a.get("tool.status", s["status"].lower()),
                         "tokens_in": a.get("gen_ai.usage.input_tokens", ""), "tokens_out": a.get("gen_ai.usage.output_tokens", ""),
                         "cost_usd": a.get("cost.usd", ""), "trace_id": s["trace_id"]})
    rows.sort(key=lambda r: (r["case:concept:name"], r["time:timestamp"]))
    with Path(out).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EVENTLOG_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("python -m agent_guardrails.tracing <traces-ordner> <ausgabe.csv>")
    print(f"{export_eventlog(Path(sys.argv[1]), Path(sys.argv[2]))} Events geschrieben")
