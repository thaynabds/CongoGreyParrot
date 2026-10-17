"""Arranque comum dos servidores MCP do Congo Grey Parrot.

O transporte stdio serve para o Cursor e outros programas locais.
O transporte http usa o aplicativo ASGI que o pacote oficial `mcp` expõe
(streamable HTTP, ou SSE se só essa rota existir nesta versão).
Pedidos HTTP sem o segredo Bearer são recusados.
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path


def token_file() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "congo-grey-parrot" / "mcp.token"


def ensure_http_token() -> str:
    current = os.environ.get("MCP_TOKEN", "").strip()
    if current:
        return current
    path = token_file()
    if path.is_file():
        saved = path.read_text(encoding="utf-8").strip()
        if saved:
            return saved
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = secrets.token_urlsafe(32)
    path.write_text(generated + "\n", encoding="utf-8")
    path.chmod(0o600)
    print(f"Segredo MCP gravado em {path}", file=sys.stderr)
    return generated


class BearerGate:
    """Recusa HTTP sem Authorization: Bearer. Encaminha lifespan e websocket."""

    def __init__(self, app, token: str):
        self.app = app
        self._expected = f"Bearer {token}"

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        header = _authorization(scope)
        if header != self._expected:
            body = "Pedido recusado. Falta o segredo Bearer.".encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"text/plain; charset=utf-8"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)


def _authorization(scope) -> str:
    for key, value in scope.get("headers") or []:
        if key.lower() == b"authorization":
            return value.decode("latin1").strip()
    return ""


def make_server(name: str):
    """Usa MCPServer do pacote mcp 2. Se a instalação ainda for a 1.x, usa FastMCP."""
    try:
        from mcp.server.mcpserver import MCPServer
    except ModuleNotFoundError:
        from mcp.server.fastmcp import FastMCP as MCPServer
    return MCPServer(name)


def http_application(server, host: str):
    if hasattr(server, "streamable_http_app"):
        return server.streamable_http_app(host=host), "streamable-http"
    if hasattr(server, "sse_app"):
        return server.sse_app(host=host), "sse"
    raise SystemExit(
        "Esta versão do pacote mcp não publica HTTP. "
        "Instale o extra mcp do programa, com o pacote oficial mcp."
    )


def serve(server, default_port: int) -> None:
    transport = os.environ.get("CONGO_MCP_TRANSPORT", "stdio").strip().lower()
    if transport in {"", "stdio"}:
        server.run(transport="stdio")
        return
    if transport not in {"http", "streamable-http", "sse"}:
        raise SystemExit("Transporte desconhecido. Use stdio ou http.")
    token = ensure_http_token()
    host = os.environ.get("MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.environ.get("MCP_PORT", str(default_port)))
    if transport == "sse" and hasattr(server, "sse_app"):
        app, kind = server.sse_app(host=host), "sse"
    else:
        app, kind = http_application(server, host)
    import uvicorn

    print(
        f"MCP HTTP ({kind}) em http://{host}:{port}/mcp . "
        f"O segredo fica em {token_file()} e não é impresso aqui.",
        file=sys.stderr,
    )
    uvicorn.run(BearerGate(app, token), host=host, port=port, log_level="info")


def tool_names(server) -> list[str]:
    import asyncio

    result = server.list_tools()
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    return sorted(item.name for item in result)
