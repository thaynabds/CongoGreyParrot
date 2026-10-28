import asyncio
import base64
import json

from congo_discord.service.foundry_relay import (
    http_bytes,
    FoundryOutbox,
    discord_roll_line,
    dispatch,
    normalize_roll,
    parse_http,
    prepare_upload,
)


def test_foundry_outbox_delivers_and_acks_once():
    outbox = FoundryOutbox(limit=2)
    assert outbox.push("", expression="", total="", text="   ") is None
    first = outbox.push("Ana", text="eu abro a porta")
    outbox.push("Bruno", expression="1d20+5", total="18", text="ataque")
    outbox.push("Caio", text="terceira some da fila")
    pending = outbox.pending()
    assert len(pending) == 2
    assert pending[0]["player"] == "Bruno"
    assert pending[1]["text"] == "terceira some da fila"
    assert first is not None
    assert not outbox.ack(first.id)
    assert outbox.ack(pending[0]["id"])
    assert outbox.pending()[0]["player"] == "Caio"


def test_roll_from_foundry_becomes_a_discord_line_and_stays_out_of_the_outbox():
    body = b'{"vtt":"foundry","player":"Mestre","expression":"1d20+5","total":"17","detail":"ataque"}'
    raw = b"POST /roll HTTP/1.1\r\nContent-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body
    parsed = parse_http(raw)
    assert parsed is not None
    method, path, body = parsed
    outbox = FoundryOutbox()
    status, payload, content_type = dispatch(method, path, body, outbox)
    assert status == 200
    assert content_type == "application/json"
    roll = json.loads(payload)
    assert roll == normalize_roll(roll)
    assert discord_roll_line(roll) == "[FOUNDRY] **Mestre** `1d20+5` = **17** (ataque)"
    assert outbox.pending() == []


def test_pending_and_ack_roundtrip():
    outbox = FoundryOutbox()
    note = outbox.push("Discord", expression="2d6", total="9", text="cura")
    assert note is not None
    status, payload, _kind = dispatch("GET", "/foundry/pending", b"", outbox)
    assert status == 200
    assert json.loads(payload)["items"][0]["id"] == note.id
    ack = json.dumps({"id": note.id}).encode("utf-8")
    status, _body, _kind = dispatch("POST", "/foundry/ack", ack, outbox)
    assert status == 200
    assert outbox.pending() == []
    status, _body, _kind = dispatch("POST", "/roll", b"{}", outbox)
    assert status == 400
    assert parse_http(b"POST /roll HTTP/1.1\r\nContent-Length: 20\r\n\r\n{}") is None


def test_image_roundtrip_blocks_executable_and_limits_size():
    outbox = FoundryOutbox()
    note = outbox.push("Ana", text="mapa", upload=("mapa.png", "image/png", b"\x89PNG"))
    assert note is not None and note.file_id
    status, payload, content_type = dispatch("GET", f"/foundry/file/{note.file_id}", b"", outbox)
    assert status == 200
    assert payload == b"\x89PNG"
    assert content_type.startswith("image/png")
    assert outbox.ack(note.id)
    assert dispatch("GET", f"/foundry/file/{note.file_id}", b"", outbox)[0] == 404
    try:
        prepare_upload("virus.exe", "application/octet-stream", b"MZ")
    except ValueError:
        pass
    else:
        raise AssertionError("executável deveria ser recusado")
    encoded = base64.b64encode(b"GIF89a").decode("ascii")
    body = json.dumps({
        "vtt": "foundry",
        "player": "Mestre",
        "file": {"name": "cena.gif", "type": "image/gif", "data": encoded},
    }).encode("utf-8")
    status, payload, _kind = dispatch("POST", "/roll", body, outbox)
    assert status == 200
    assert json.loads(payload)["filename"] == "cena.gif"
    assert outbox.pending() == []


def test_local_socket_accepts_a_foundry_roll():
    async def scenario() -> None:
        outbox = FoundryOutbox()

        async def handle(reader, writer) -> None:
            raw = await reader.read(4096)
            parsed = parse_http(raw)
            assert parsed is not None
            status, payload, kind = dispatch(*parsed, outbox)
            writer.write(http_bytes(status, payload, kind))
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(handle, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        _reader, writer = await asyncio.open_connection("127.0.0.1", port)
        body = b'{"vtt":"foundry","player":"Ana","expression":"1d6","total":"4","detail":"cura"}'
        writer.write(b"POST /roll HTTP/1.1\r\nContent-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body)
        await writer.drain()
        data = await _reader.read(4096)
        writer.close()
        server.close()
        await server.wait_closed()
        assert data.startswith(b"HTTP/1.1 200 ")
        assert b'"player": "Ana"' in data
        assert outbox.pending() == []

    asyncio.run(scenario())


def _request(host: str, token: str | None, method: str = "GET") -> bytes:
    lines = [f"{method} /foundry/pending HTTP/1.1", f"Host: {host}"]
    if token is not None:
        lines.append(f"X-Congo-Token: {token}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii")


def test_relay_token_is_required_for_every_route():
    from congo_discord.service.foundry_relay import parse_headers, request_allowed

    token = "segredo-do-relay"
    good = parse_headers(_request("127.0.0.1:7477", token))
    assert request_allowed("GET", good, token, 7477)
    assert request_allowed("POST", parse_headers(_request("localhost:7477", token)), token, 7477)
    assert not request_allowed("GET", parse_headers(_request("127.0.0.1:7477", None)), token, 7477)
    assert not request_allowed("GET", parse_headers(_request("127.0.0.1:7477", "errado")), token, 7477)
    assert not request_allowed("GET", good, "", 7477)


def test_relay_host_blocks_dns_rebinding():
    from congo_discord.service.foundry_relay import parse_headers, request_allowed

    token = "segredo-do-relay"
    assert not request_allowed("GET", parse_headers(_request("evil.example:7477", token)), token, 7477)
    assert not request_allowed("GET", parse_headers(_request("127.0.0.1:9999", token)), token, 7477)
    assert not request_allowed("OPTIONS", parse_headers(_request("evil.example:7477", None, "OPTIONS")), token, 7477)
    assert request_allowed("OPTIONS", parse_headers(_request("127.0.0.1:7477", None, "OPTIONS")), token, 7477)
    assert b"X-Congo-Token" in http_bytes(204, b"", "text/plain")
