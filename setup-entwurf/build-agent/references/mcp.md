# MCP-Server mit fastmcp

Nur nötig, wenn Tools von mehreren Clients (Claude Code, Claude Desktop, andere Agents) genutzt werden sollen. Für einen einzelnen Agent reichen normale LangChain-Tools.

## Server
`uv add fastmcp` (Paketname in der Doku bestätigen). Muster (Quelle: M1):
```python
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

mcp = FastMCP(name="crm", mask_error_details=True)   # interne Fehlertexte nicht nach außen

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True), timeout=30.0)
def crm_leads_search(
    query: Annotated[str, Field(description="Firmenname oder E-Mail-Domain")],
    limit: Annotated[int, Field(ge=1, le=50)] = 10,
) -> dict:
    """Sucht Leads im CRM. Für Details danach crm_leads_get nutzen."""
    if not query.strip():
        raise ToolError("query ist leer. Beispiel: crm_leads_search(query='acme.com')")
    ...
    return {"status": "ok", "summary": "...", "data": {...}, "next_actions": [...]}
```
- Gleicher Rückgabevertrag wie in `tools.md`; Dicts werden automatisch zu `structuredContent`.
- `ToolError` für Fehler, die der Agent sehen soll (mit Korrekturbeispiel).
- Annotations ehrlich setzen: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`. Sie sind nur Hinweise, keine Sicherheit (Quelle: M1, A2).
- Logik unabhängig vom Transport halten.

## Transport und Auth (Quelle: M2)
- Lokal: stdio (`mcp.run()`).
- Remote: Streamable HTTP, `mcp.run(transport="http", host="0.0.0.0", port=8000)` bzw. `mcp.http_app()` mit uvicorn.
- **Remote nie ohne Auth:**
  - Entwicklung: `StaticTokenVerifier`, Token aus Umgebungsvariable.
  - Produktion: OAuth-Provider oder JWT-Verifier, mit explizitem Signing-Key.
- Secrets nur über Umgebungsvariablen.

## Resources mit Quellen
Liefert der Server Dokumente für RAG, gehören Quellen-Metadaten in jede Rückgabe: Dateiname/URI, Seite oder Abschnitt, Stand. So kann der Agent zitieren (siehe evals.md, RAG-Metriken).

## In einen LangChain-Agent einbinden
Paket `langchain-mcp-adapters` (`MultiServerMCPClient`) lädt MCP-Tools als LangChain-Tools. API in der Doku prüfen.
