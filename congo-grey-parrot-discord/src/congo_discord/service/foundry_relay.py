from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_HTTP_BYTES = 12 * 1024 * 1024

_BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".dll", ".so", ".sh", ".ps1",
    ".jar", ".scr", ".apk", ".dmg", ".app", ".html", ".htm", ".xhtml",
    ".svg", ".js", ".mjs",
}
_BLOCKED_TYPES = {
    "text/html", "image/svg+xml", "application/javascript", "text/javascript",
}


def _clip(value: str, limit: int) -> str:
    text = " ".join(value.split())
    return text[:limit]


@dataclass(frozen=True)
class FoundryNote:
    id: str
    player: str
    expression: str
    total: str
    text: str
    file_id: str = ""
    filename: str = ""
    media_type: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "player": self.player,
            "expression": self.expression,
            "total": self.total,
            "text": self.text,
            "file_id": self.file_id,
            "filename": self.filename,
            "media_type": self.media_type,
        }


class FoundryOutbox:
    def __init__(self, limit: int = 40) -> None:
        self._limit = limit
        self._seq = 0
        self._items: list[FoundryNote] = []
        self._files: dict[str, tuple[str, str, bytes]] = {}

    def push(
        self,
        player: str,
        expression: str = "",
        total: str = "",
        text: str = "",
        upload: tuple[str, str, bytes] | None = None,
    ) -> FoundryNote | None:
        cleaned_player = _clip(player, 80) or "Discord"
        cleaned_expression = _clip(expression, 200)
        cleaned_total = _clip(total, 40)
        cleaned_text = _clip(text, 500)
        filename = ""
        media_type = ""
        data = b""
        if upload is not None:
            filename, media_type, data = prepare_upload(*upload)
        if not cleaned_expression and not cleaned_total and not cleaned_text and not data:
            return None
        self._seq += 1
        file_id = str(self._seq) if data else ""
        note = FoundryNote(
            str(self._seq),
            cleaned_player,
            cleaned_expression,
            cleaned_total,
            cleaned_text,
            file_id,
            filename,
            media_type,
        )
        if data:
            self._files[file_id] = (filename, media_type, data)
        self._items.append(note)
        if len(self._items) > self._limit:
            self._items = self._items[-self._limit :]
        self._drop_orphan_files()
        return note

    def pending(self) -> list[dict[str, str]]:
        return [item.as_dict() for item in self._items]

    def file_bytes(self, file_id: str) -> tuple[str, str, bytes] | None:
        return self._files.get(file_id)

    def ack(self, item_id: str) -> bool:
        before = len(self._items)
        self._items = [item for item in self._items if item.id != item_id]
        self._drop_orphan_files()
        return len(self._items) != before

    def _drop_orphan_files(self) -> None:
        kept = {item.file_id for item in self._items if item.file_id}
        self._files = {key: value for key, value in self._files.items() if key in kept}


def safe_filename(name: str) -> str:
    base = Path(str(name).replace("\x00", "")).name.strip()
    if not base or base in {".", ".."}:
        raise ValueError("O arquivo precisa de um nome.")
    suffix = Path(base).suffix.lower()
    if suffix in _BLOCKED_EXTENSIONS:
        raise ValueError("Esse tipo de arquivo não entra.")
    cleaned = "".join(character if character.isalnum() or character in "._- " else "_" for character in base)
    cleaned = cleaned.strip("._ ")[:80]
    if not cleaned or Path(cleaned).suffix.lower() in _BLOCKED_EXTENSIONS:
        raise ValueError("Esse tipo de arquivo não entra.")
    return cleaned


def safe_media_type(value: str) -> str:
    raw = str(value or "").split(";", 1)[0].strip().lower()
    if raw in _BLOCKED_TYPES or not re.fullmatch(r"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+", raw):
        return "application/octet-stream"
    return raw


def prepare_upload(name: str, media_type: str, data: bytes) -> tuple[str, str, bytes]:
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise ValueError("O arquivo chegou vazio.")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("O arquivo passou de 8 MB.")
    filename = safe_filename(name)
    return filename, safe_media_type(media_type), bytes(data)


def attached_file(payload: dict) -> tuple[str, str, bytes] | None:
    incoming = payload.get("file")
    if not incoming:
        return None
    if not isinstance(incoming, dict):
        raise ValueError("O arquivo chegou incompleto.")
    encoded = incoming.get("data") or ""
    if not isinstance(encoded, str) or len(encoded) > MAX_HTTP_BYTES:
        raise ValueError("O arquivo passou de 8 MB.")
    try:
        data = base64.b64decode(encoded, validate=False)
    except (ValueError, TypeError) as exc:
        raise ValueError("O arquivo chegou incompleto.") from exc
    return prepare_upload(str(incoming.get("name") or "arquivo"), str(incoming.get("type") or ""), data)


def normalize_roll(payload: object, has_file: bool = False) -> dict[str, str] | None:
    if not isinstance(payload, dict):
        return None
    vtt = _clip(str(payload.get("vtt") or "vtt"), 40).lower() or "vtt"
    player = _clip(str(payload.get("player") or "Mesa"), 80) or "Mesa"
    expression = _clip(str(payload.get("expression") or ""), 200)
    total = _clip(str(payload.get("total") or ""), 40)
    detail = _clip(str(payload.get("detail") or ""), 400)
    if not expression and not total and not detail and not has_file:
        return None
    return {
        "vtt": vtt,
        "player": player,
        "expression": expression,
        "total": total,
        "detail": detail,
    }


def discord_roll_line(roll: dict[str, str]) -> str:
    parts = [f"[{roll['vtt'].upper()}] **{roll['player']}**"]
    if roll["expression"]:
        parts.append(f"`{roll['expression']}`")
    if roll["total"]:
        parts.append(f"= **{roll['total']}**")
    if roll["detail"]:
        parts.append(f"({roll['detail']})")
    return " ".join(parts)


def parse_http(raw: bytes) -> tuple[str, str, bytes] | None:
    separator = b"\r\n\r\n" if b"\r\n\r\n" in raw else b"\n\n" if b"\n\n" in raw else b""
    if not separator:
        return None
    header, body = raw.split(separator, 1)
    lines = header.decode("utf-8", errors="replace").splitlines()
    if not lines:
        return None
    parts = lines[0].split()
    if len(parts) < 2:
        return None
    length = 0
    for line in lines[1:]:
        if line.lower().startswith("content-length:"):
            try:
                length = int(line.split(":", 1)[1].strip() or "0")
            except ValueError:
                return None
    if length < 0 or length > MAX_HTTP_BYTES:
        return None
    if len(body) < length:
        return None
    path = parts[1].split("?", 1)[0]
    return parts[0].upper(), path, body[:length]


def dispatch(method: str, path: str, body: bytes, outbox: FoundryOutbox) -> tuple[int, bytes, str]:
    if method == "OPTIONS":
        return 204, b"", "text/plain"
    if method == "GET" and path == "/foundry/pending":
        payload = json.dumps({"items": outbox.pending()}, ensure_ascii=False).encode("utf-8")
        return 200, payload, "application/json"
    if method == "GET" and path.startswith("/foundry/file/"):
        file_id = path.removeprefix("/foundry/file/")
        stored = None if "/" in file_id or not file_id else outbox.file_bytes(file_id)
        if stored is None:
            return 404, b"Not Found", "text/plain"
        filename, media_type, data = stored
        return 200, data, f"{media_type}; name={filename}"
    if method == "POST" and path == "/foundry/ack":
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return 400, b'{"error":"json"}', "application/json"
        if not isinstance(payload, dict) or not outbox.ack(str(payload.get("id") or "")):
            return 404, b'{"error":"missing"}', "application/json"
        return 200, b'{"ok":true}', "application/json"
    if method == "POST" and path == "/roll":
        try:
            payload = json.loads(body.decode("utf-8") or "")
        except json.JSONDecodeError:
            return 400, "JSON inválido".encode("utf-8"), "text/plain"
        try:
            incoming_file = attached_file(payload) if isinstance(payload, dict) else None
        except ValueError as exc:
            return 400, str(exc).encode("utf-8"), "text/plain"
        roll = normalize_roll(payload, has_file=incoming_file is not None)
        if roll is None:
            return 400, "Rolagem vazia".encode("utf-8"), "text/plain"
        if incoming_file is not None:
            roll["filename"] = incoming_file[0]
        return 200, json.dumps(roll, ensure_ascii=False).encode("utf-8"), "application/json"
    return 404, b"Not Found", "text/plain"


def http_bytes(status: int, body: bytes, content_type: str) -> bytes:
    reason = {200: "OK", 204: "No Content", 400: "Bad Request", 404: "Not Found"}.get(status, "OK")
    media_type, _, name = content_type.partition("; name=")
    disposition = f'Content-Disposition: attachment; filename="{name}"\r\n' if name else ""
    header = (
        f"HTTP/1.1 {status} {reason}\r\n"
        f"Content-Type: {media_type}\r\n"
        f"{disposition}"
        f"Content-Length: {len(body)}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Access-Control-Allow-Private-Network: true\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return header.encode("ascii") + body
