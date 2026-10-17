from __future__ import annotations

import json
from dataclasses import dataclass


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

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "player": self.player,
            "expression": self.expression,
            "total": self.total,
            "text": self.text,
        }


class FoundryOutbox:
    def __init__(self, limit: int = 40) -> None:
        self._limit = limit
        self._seq = 0
        self._items: list[FoundryNote] = []

    def push(self, player: str, expression: str = "", total: str = "", text: str = "") -> FoundryNote | None:
        cleaned_player = _clip(player, 80) or "Discord"
        cleaned_expression = _clip(expression, 200)
        cleaned_total = _clip(total, 40)
        cleaned_text = _clip(text, 500)
        if not cleaned_expression and not cleaned_total and not cleaned_text:
            return None
        self._seq += 1
        note = FoundryNote(
            str(self._seq),
            cleaned_player,
            cleaned_expression,
            cleaned_total,
            cleaned_text,
        )
        self._items.append(note)
        if len(self._items) > self._limit:
            self._items = self._items[-self._limit :]
        return note

    def pending(self) -> list[dict[str, str]]:
        return [item.as_dict() for item in self._items]

    def ack(self, item_id: str) -> bool:
        before = len(self._items)
        self._items = [item for item in self._items if item.id != item_id]
        return len(self._items) != before


def normalize_roll(payload: object) -> dict[str, str] | None:
    if not isinstance(payload, dict):
        return None
    vtt = _clip(str(payload.get("vtt") or "vtt"), 40).lower() or "vtt"
    player = _clip(str(payload.get("player") or "Mesa"), 80) or "Mesa"
    expression = _clip(str(payload.get("expression") or ""), 200)
    total = _clip(str(payload.get("total") or ""), 40)
    detail = _clip(str(payload.get("detail") or ""), 400)
    if not expression and not total and not detail:
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
    if length < 0 or length > 20000:
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
        roll = normalize_roll(payload)
        if roll is None:
            return 400, "Rolagem vazia".encode("utf-8"), "text/plain"
        return 200, json.dumps(roll, ensure_ascii=False).encode("utf-8"), "application/json"
    return 404, b"Not Found", "text/plain"


def http_bytes(status: int, body: bytes, content_type: str) -> bytes:
    reason = {200: "OK", 204: "No Content", 400: "Bad Request", 404: "Not Found"}.get(status, "OK")
    header = (
        f"HTTP/1.1 {status} {reason}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Access-Control-Allow-Private-Network: true\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return header.encode("ascii") + body
