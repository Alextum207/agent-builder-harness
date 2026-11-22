"""Chatmodell über die Claude-Code-CLI (`claude -p`), für Evals ohne API-Key (Abo statt API).

    from agent_guardrails.claude_cli import chat_model
    llm = chat_model("claude-cli:haiku")      # sonst wie init_chat_model("anthropic:…" | "ollama:…")

Tool-Calls laufen über ein Text-Protokoll (JSON im Antworttext), nicht über native Tool-Use-Blöcke der API.
Gemessen wird also Modell + Harness, aber mit anderem Tool-Format als im Betrieb über die API. Jeder Aufruf
startet einen eigenen CLI-Prozess (~3–10 s) mit minimalem System-Prompt, ohne Tools, MCP und Einstellungen.
Kosten laut CLI werden nach CLAUDE_CLI_COST_LOG (JSONL) geschrieben, falls gesetzt.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool

_EMPTY = Path(tempfile.gettempdir()) / "claude-cli-empty"      # Arbeitsordner ohne CLAUDE.md/Einstellungen


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return " ".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content or [])


def _json_object(text: str) -> dict | None:
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(t[start:end + 1], strict=False)   # Modelle schreiben echte Zeilenumbrüche in Strings
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


class ClaudeCLIChat(BaseChatModel):
    model: str = "haiku"
    tools: list[dict] = []
    tool_choice: str | None = None
    timeout_s: int = 240

    @property
    def _llm_type(self) -> str:
        return "claude-cli"

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        specs = [convert_to_openai_tool(t)["function"] for t in tools]
        if isinstance(tool_choice, dict):
            tool_choice = (tool_choice.get("function") or {}).get("name") or tool_choice.get("name")
        if tool_choice in (True, "required"):
            tool_choice = "any"
        return self.model_copy(update={"tools": specs, "tool_choice": tool_choice})

    def _system(self, messages: list[BaseMessage]) -> str:
        sys = "\n\n".join(_text(m.content) for m in messages if m.type == "system")
        if not self.tools:
            return sys or "Du bist ein hilfreicher Assistent."
        must = ("" if self.tool_choice in (None, "auto", "none") else
                "\nDu MUSST jetzt ein Werkzeug aufrufen." if self.tool_choice == "any" else
                f"\nDu MUSST jetzt das Werkzeug {self.tool_choice} aufrufen.")
        return (f"{sys}\n\n# Werkzeuge\n<tools>\n{json.dumps(self.tools, ensure_ascii=False)}\n</tools>\n\n"
                "# Antwortformat (Pflicht)\nAntworte ausschließlich mit genau einem JSON-Objekt, ohne Text davor oder danach:\n"
                '- Werkzeuge aufrufen: {"tool_calls": [{"name": "<werkzeug>", "args": {...}}]} (mehrere erlaubt)\n'
                '- Endgültige Antwort: {"content": "<deine Antwort>"}' + must)

    @staticmethod
    def _transcript(messages: list[BaseMessage]) -> str:
        parts = []
        for m in messages:
            if m.type == "human":
                parts.append(f"<user>\n{_text(m.content)}\n</user>")
            elif m.type == "ai":
                calls = [{"name": c["name"], "args": c["args"], "id": c.get("id")} for c in getattr(m, "tool_calls", []) or []]
                body = json.dumps({"content": _text(m.content), **({"tool_calls": calls} if calls else {})}, ensure_ascii=False)
                parts.append(f"<assistant>\n{body}\n</assistant>")
            elif m.type == "tool":
                parts.append(f'<tool_result name="{getattr(m, "name", "")}" id="{m.tool_call_id}">\n{_text(m.content)}\n</tool_result>')
        parts.append("Gib jetzt die nächste Antwort des Assistenten.")
        return "\n\n".join(parts)

    def _call(self, system: str, prompt: str) -> dict:
        _EMPTY.mkdir(exist_ok=True)
        cmd = [shutil.which("claude") or "claude", "-p", "--model", self.model, "--output-format", "json", "--max-turns", "1", "--tools", "",
               "--system-prompt", system, "--setting-sources", "", "--strict-mcp-config", "--disable-slash-commands",
               "--no-session-persistence"]
        for attempt in range(3):
            p = subprocess.run(cmd, input=prompt, cwd=_EMPTY, capture_output=True, text=True, encoding="utf-8",
                               timeout=self.timeout_s)   # ohne Shell: cmd.exe zerlegt mehrzeilige Argumente
            try:
                d = json.loads(p.stdout)
            except json.JSONDecodeError:
                d = {"is_error": True, "result": (p.stderr or p.stdout)[-300:]}
            if not d.get("is_error"):
                return d
            time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"claude-cli: {d.get('api_error') or d.get('result')}"[:300])

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        system, prompt = self._system(messages), self._transcript([m for m in messages if m.type != "system"])
        d = self._call(system, prompt)
        forced = self.tools and self.tool_choice not in (None, "auto", "none")
        unlesbar = '"tool_calls"' in d.get("result", "") and _json_object(d.get("result", "")) is None
        if (forced or unlesbar) and not ((_json_object(d.get("result", "")) or {}).get("tool_calls")):   # fehlt oder unlesbar: einmal nachfragen
            d = self._call(system, prompt + '\n\nAntworte jetzt NUR mit dem JSON-Objekt {"tool_calls": [...]}.')
        text, u = d.get("result", ""), d.get("usage", {})
        inp = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        usage = {"input_tokens": inp, "output_tokens": u.get("output_tokens", 0), "total_tokens": inp + u.get("output_tokens", 0)}
        if log := os.environ.get("CLAUDE_CLI_COST_LOG"):
            with open(log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), "model": list(d.get("modelUsage", {}))[:1], "usd": d.get("total_cost_usd", 0), **usage}) + "\n")
        meta = {"model_name": next(iter(d.get("modelUsage", {})), self.model), "cost_usd": d.get("total_cost_usd")}
        msg = AIMessage(content=text, usage_metadata=usage, response_metadata=meta)
        if self.tools:
            obj = _json_object(text)
            calls = (obj or {}).get("tool_calls") or []
            names = {t["name"] for t in self.tools}
            calls = [c for c in calls if isinstance(c, dict) and c.get("name") in names]
            if calls:
                msg = AIMessage(content="", usage_metadata=usage, response_metadata=meta, tool_calls=[
                    {"name": c["name"], "args": c.get("args") or {}, "id": f"call_{uuid.uuid4().hex[:12]}", "type": "tool_call"}
                    for c in calls])
            elif obj is not None and "content" in obj:
                msg = AIMessage(content=str(obj["content"]), usage_metadata=usage, response_metadata=meta)
        return ChatResult(generations=[ChatGeneration(message=msg)])


def chat_model(name: str, **kwargs):
    """`claude-cli:<modell>` → ClaudeCLIChat, sonst init_chat_model(name)."""
    if name.startswith("claude-cli:"):
        return ClaudeCLIChat(model=name.split(":", 1)[1])
    from langchain.chat_models import init_chat_model
    return init_chat_model(name, **kwargs)
