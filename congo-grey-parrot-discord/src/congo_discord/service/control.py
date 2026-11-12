"""Canal local entre o servidor MCP e o bot ligado.

Socket Unix numa pasta 0700, com o próprio socket em 0600, e o bot confere o uid de quem
conecta. Nenhuma porta TCP: um site aberto no navegador não alcança um socket Unix.
Uma linha JSON vai, uma linha JSON volta, com tamanho limitado.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import struct
from pathlib import Path

MAX_REQUEST = 64 * 1024
MAX_REPLY = 256 * 1024


def socket_path() -> Path:
    explicit = os.environ.get("CONGO_DISCORD_CONTROL", "").strip()
    if explicit:
        return Path(explicit)
    runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    if not runtime and hasattr(os, "getuid") and Path(f"/run/user/{os.getuid()}").is_dir():
        runtime = f"/run/user/{os.getuid()}"
    base = Path(runtime) if runtime else Path.home() / ".local" / "share" / "congo-grey-parrot-discord"
    return base / "congo-discord" / "control.sock"


def _peer_uid(sock) -> int | None:
    if not hasattr(socket, "SO_PEERCRED"):
        return None
    raw = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


async def start_server(handler):
    """Abre o socket do bot. handler(action, args) é async e devolve texto."""
    path = socket_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    if path.is_socket() or path.exists():
        path.unlink()

    async def serve_one(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            raw_sock = writer.get_extra_info("socket")
            uid = _peer_uid(raw_sock) if raw_sock is not None else None
            if uid is not None and uid != os.getuid():
                await _reply(writer, False, "Pedido recusado: outro usuário.")
                return
            line = await asyncio.wait_for(reader.readline(), timeout=10)
            if not line or len(line) > MAX_REQUEST:
                await _reply(writer, False, "Pedido grande demais ou vazio.")
                return
            request = json.loads(line.decode("utf-8"))
            action = str(request.get("action", ""))
            args = request.get("args") or {}
            if not isinstance(args, dict):
                raise ValueError("args precisa ser um objeto.")
            text = await asyncio.wait_for(handler(action, args), timeout=120)
            await _reply(writer, True, text)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            await _reply(writer, False, str(exc) or "Pedido inválido.")
        except asyncio.TimeoutError:
            await _reply(writer, False, "O bot demorou demais para responder.")
        except Exception as exc:  # o bot continua ligado mesmo se uma ação falhar
            await _reply(writer, False, f"A ação falhou: {type(exc).__name__}")
        finally:
            writer.close()

    old_umask = os.umask(0o177)
    try:
        server = await asyncio.start_unix_server(serve_one, path=str(path), limit=MAX_REQUEST + 2)
    finally:
        os.umask(old_umask)
    os.chmod(path, 0o600)
    return server


async def _reply(writer: asyncio.StreamWriter, ok: bool, text: str) -> None:
    body = json.dumps({"ok": ok, "text": str(text)[:MAX_REPLY]}, ensure_ascii=False) + "\n"
    writer.write(body.encode("utf-8"))
    await writer.drain()


def call(action: str, args: dict | None = None, timeout: float = 130) -> tuple[bool, str]:
    """Usado pelo servidor MCP. Devolve (ok, texto). Bot desligado vira ok=False com explicação."""
    path = socket_path()
    if not path.is_socket():
        return False, "O bot não está ligado (ou é uma versão sem o canal do AI Conector). Ligue o bot e tente de novo."
    payload = json.dumps({"action": action, "args": args or {}}, ensure_ascii=False).encode("utf-8") + b"\n"
    if len(payload) > MAX_REQUEST:
        return False, "Pedido grande demais."
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        try:
            client.connect(str(path))
            client.sendall(payload)
            chunks = []
            total = 0
            while True:
                chunk = client.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_REPLY * 2 or chunk.endswith(b"\n"):
                    break
        except (OSError, socket.timeout):
            return False, "Não consegui falar com o bot agora."
    try:
        reply = json.loads(b"".join(chunks).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return False, "Resposta inválida do bot."
    return bool(reply.get("ok")), str(reply.get("text", ""))
