from __future__ import annotations

import asyncio
import io
import json
import zipfile
from pathlib import Path

from congo_discord.service.foundry_relay import (
    MAX_HTTP_BYTES,
    FoundryOutbox,
    attached_file,
    discord_roll_line,
    dispatch,
    http_bytes,
    parse_http,
)

FEATURE = "navegador"
DESCRIPTION = (
    "Liga o Discord ao Roll20 e ao Foundry VTT no mesmo computador. "
    "O Foundry usa o módulo em foundry/congo-grey-parrot. O servidor HTTP só aceita 127.0.0.1."
)

_DEFAULT_PORT = 7477
_USERSCRIPT_NAME = "congo-relay.user.js"


def _relay_config_path(bot) -> Path:
    return bot.sounds.parent / "relay_config.json"


def _load_config(bot) -> dict:
    path = _relay_config_path(bot)
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_config(bot, data: dict) -> None:
    _relay_config_path(bot).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _userscript_path(bot) -> Path:
    return bot.sounds.parent / _USERSCRIPT_NAME


def _write_userscript(bot, port: int) -> Path:
    script = f"""\
// ==UserScript==
// @name         Congo Grey Parrot, Relay de Rolagens
// @namespace    https://github.com/thaynabds/CongoGreyParrot
// @version      1.2
// @description  Envia rolagens do Roll20 ou do Foundry para o bot de Discord no mesmo computador.
// @author       Thayná Batista da Silva
// @match        https://app.roll20.net/editor/*
// @match        https://app.roll20.net/campaigns/*
// @match        http://localhost/*
// @match        http://127.0.0.1/*
// @match        https://localhost/*
// @match        https://127.0.0.1/*
// @match        http://*:30000/*
// @match        https://*:30000/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// @connect      127.0.0.1
// ==/UserScript==

(function () {{
    'use strict';

    const RELAY_URL = 'http://127.0.0.1:{port}/roll';

    function sendRoll(payload) {{
        GM_xmlhttpRequest({{
            method: 'POST',
            url: RELAY_URL,
            headers: {{ 'Content-Type': 'application/json' }},
            data: JSON.stringify(payload),
            onerror: function () {{
                console.warn('[Congo] Relay offline. O bot de Discord está rodando?');
            }}
        }});
    }}

    function extractFromMessage(messageEl) {{
        var playerEl = messageEl.querySelector('.by');
        var player = playerEl
            ? playerEl.textContent.replace(/:$/, '').trim()
            : 'Desconhecido';

        // Rolagens inline do Roll20
        messageEl.querySelectorAll('.inlinerollresult').forEach(function (rollEl) {{
            var expression = rollEl.getAttribute('data-origroll')
                || rollEl.getAttribute('title')
                || '';
            var totalEl = rollEl.querySelector('.resultRoll')
                || rollEl.querySelector('.basicdiceresult');
            var total = totalEl
                ? totalEl.textContent.trim()
                : rollEl.textContent.trim();
            var detail = rollEl.getAttribute('title') || '';
            if (expression || total) {{
                sendRoll({{ vtt: 'roll20', player: player, expression: expression, total: total, detail: detail }});
            }}
        }});

        // Rolltemplate padrão (fichas de personagem)
        var templateEl = messageEl.querySelector('[class*="rolltemplate"]');
        if (templateEl) {{
            var labelEls = templateEl.querySelectorAll('[class*="label"], [class*="attr"]');
            var valueEls = templateEl.querySelectorAll('[class*="val"], [class*="value"]');
            if (valueEls.length > 0) {{
                var label = labelEls.length > 0 ? labelEls[0].textContent.trim() : '';
                var value = valueEls[0].textContent.trim();
                sendRoll({{ vtt: 'roll20', player: player, expression: label, total: value, detail: '' }});
            }}
        }}
    }}

    // Foundry VTT (localhost:30000)
    function extractFromFoundry(messageEl) {{
        var speaker = messageEl.querySelector('.message-sender');
        var player = speaker ? speaker.textContent.trim() : 'Desconhecido';
        var rollEl = messageEl.querySelector('.dice-total');
        var formulaEl = messageEl.querySelector('.dice-formula');
        if (rollEl) {{
            var total = rollEl.textContent.trim();
            var expression = formulaEl ? formulaEl.textContent.trim() : '';
            var tooltipEl = messageEl.querySelector('.dice-tooltip');
            var detail = tooltipEl ? tooltipEl.textContent.replace(/\\s+/g, ' ').trim() : '';
            sendRoll({{ vtt: 'foundry', player: player, expression: expression, total: total, detail: detail }});
        }}
    }}

    function moduleAlreadyRuns() {{
        return typeof unsafeWindow !== 'undefined' && unsafeWindow.__congoFoundryModule;
    }}

    function observeRoll20() {{
        var chat = document.querySelector('#textchat .content');
        if (!chat) {{ setTimeout(observeRoll20, 1000); return; }}
        new MutationObserver(function (mutations) {{
            mutations.forEach(function (m) {{
                m.addedNodes.forEach(function (node) {{
                    if (node.nodeType === 1 && node.classList.contains('message')) {{
                        extractFromMessage(node);
                    }}
                }});
            }});
        }}).observe(chat, {{ childList: true }});
        console.log('[Congo Grey Parrot] Relay de rolagens ativo no Roll20, porta {port}.');
    }}

    function observeFoundry() {{
        var chatLog = document.querySelector('#chat-log');
        if (!chatLog) {{ setTimeout(observeFoundry, 1500); return; }}
        new MutationObserver(function (mutations) {{
            mutations.forEach(function (m) {{
                m.addedNodes.forEach(function (node) {{
                    if (node.nodeType === 1 && node.classList.contains('chat-message')) {{
                        extractFromFoundry(node);
                    }}
                }});
            }});
        }}).observe(chatLog, {{ childList: true }});
        console.log('[Congo Grey Parrot] Relay de rolagens ativo no Foundry VTT, porta {port}.');
    }}

    var tries = 0;
    function boot() {{
        if (moduleAlreadyRuns()) return;
        if (document.querySelector('#chat-log') && document.querySelector('#board')) {{
            observeFoundry();
            return;
        }}
        if (location.hostname.endsWith('roll20.net')) {{
            observeRoll20();
            return;
        }}
        if (tries++ < 20) setTimeout(boot, 1500);
    }}
    boot();
}})();
"""
    path = _userscript_path(bot)
    path.write_text(script, encoding="utf-8")
    return path


def setup(bot) -> None:
    import discord
    from discord import app_commands

    navegador = app_commands.Group(
        name="navegador",
        description="Relay de rolagens do navegador para o Discord",
    )

    _server_handle: dict = {"task": None, "server": None, "port": _DEFAULT_PORT}
    bot.foundry_outbox = FoundryOutbox()

    async def gate(interaction: discord.Interaction) -> bool:
        if bot.store.enabled("navegador"):
            return True
        await interaction.response.send_message(
            "A função navegador está desativada. Use /funcoes ativar navegador.", ephemeral=True
        )
        return False

    async def read_request(reader: asyncio.StreamReader) -> bytes:
        raw = b""
        while len(raw) < MAX_HTTP_BYTES + 8192:
            chunk = await asyncio.wait_for(reader.read(65536), timeout=30)
            if not chunk:
                break
            raw += chunk
            if parse_http(raw) is not None:
                break
        return raw

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            raw = await read_request(reader)
        except asyncio.TimeoutError:
            writer.close()
            return
        parsed = parse_http(raw)
        if parsed is None:
            writer.write(http_bytes(400, "pedido incompleto".encode("utf-8"), "text/plain"))
            await writer.drain()
            writer.close()
            return
        method, path, body = parsed
        status, payload, content_type = dispatch(method, path, body, bot.foundry_outbox)
        writer.write(http_bytes(status, payload, content_type))
        await writer.drain()
        writer.close()
        if method == "POST" and path == "/roll" and status == 200:
            incoming = json.loads(body.decode("utf-8"))
            upload = attached_file(incoming)
            await post_roll(json.loads(payload.decode("utf-8")), upload)

    async def post_roll(roll: dict, upload: tuple[str, str, bytes] | None = None) -> None:
        config = _load_config(bot)
        channel_id = config.get("channel_id")
        if not channel_id:
            return
        channel = bot.get_channel(int(channel_id))
        if channel is None:
            return
        discord_file = None
        if upload is not None:
            discord_file = discord.File(io.BytesIO(upload[2]), filename=upload[0])
        await channel.send(discord_roll_line(roll), file=discord_file)

    async def bind(port: int) -> None:
        server = await asyncio.start_server(handle_client, "127.0.0.1", port)
        _server_handle["server"] = server
        _server_handle["port"] = port
        _server_handle["task"] = asyncio.create_task(server.serve_forever())

    @navegador.command(name="ligar", description="Inicia o servidor local que recebe rolagens do navegador.")
    async def ligar(interaction: discord.Interaction, porta: int = _DEFAULT_PORT) -> None:
        if not await gate(interaction):
            return
        if _server_handle["task"] and not _server_handle["task"].done():
            await interaction.response.send_message(
                f"O relay já está rodando na porta {_server_handle['port']}.", ephemeral=True
            )
            return
        try:
            await bind(porta)
        except OSError as exc:
            await interaction.response.send_message(
                f"Não consegui abrir a porta {porta}: {exc}", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"Relay iniciado em http://127.0.0.1:{porta}. "
            "No Foundry, ative o módulo Congo Grey Parrot. "
            "Defina o canal com `/navegador canal`."
        )

    @navegador.command(name="desligar", description="Para o servidor local de relay.")
    async def desligar(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        server = _server_handle.get("server")
        task = _server_handle.get("task")
        if server:
            server.close()
            _server_handle["server"] = None
        if task and not task.done():
            task.cancel()
            _server_handle["task"] = None
        await interaction.response.send_message("Relay parado.")

    @navegador.command(name="status", description="Mostra se o relay está ativo e em qual porta.")
    async def status(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        task = _server_handle.get("task")
        ativo = task is not None and not task.done()
        porta = _server_handle["port"] if ativo else ",,"
        config = _load_config(bot)
        channel_id = config.get("channel_id")
        channel = bot.get_channel(int(channel_id)) if channel_id else None
        canal = channel.mention if channel else "não configurado"
        estado = f"ativo na porta {porta}" if ativo else "parado"
        await interaction.response.send_message(
            f"Relay: {estado}. Canal de destino: {canal}.", ephemeral=True
        )

    @navegador.command(
        name="canal",
        description="Define o canal do Discord onde as rolagens do navegador serão postadas.",
    )
    async def canal(interaction: discord.Interaction, destino: discord.TextChannel) -> None:
        if not await gate(interaction):
            return
        config = _load_config(bot)
        config["channel_id"] = str(destino.id)
        _save_config(bot, config)
        await interaction.response.send_message(
            f"Rolagens do navegador serão postadas em {destino.mention}."
        )

    @navegador.command(
        name="userscript",
        description="Envia o arquivo .user.js para instalar no Tampermonkey (Roll20 e Foundry VTT).",
    )
    async def userscript(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        porta = _server_handle["port"]
        path = _write_userscript(bot, porta)
        await interaction.response.send_message(
            f"Instale este arquivo no Tampermonkey ou Greasemonkey. "
            f"Ele monitora rolagens no Roll20 e no Foundry VTT e envia para a porta {porta}.\n"
            "Como instalar: abra o Tampermonkey, clique em 'Adicionar script' e arraste o arquivo.",
            file=discord.File(str(path), filename=_USERSCRIPT_NAME),
            ephemeral=True,
        )

    @navegador.command(name="arquivo", description="Envia imagem, vídeo ou arquivo para o Discord e para o Foundry.")
    async def arquivo(interaction: discord.Interaction, arquivo: discord.Attachment, texto: str = "") -> None:
        if not await gate(interaction):
            return
        if arquivo.size > 8 * 1024 * 1024:
            await interaction.response.send_message("O arquivo passou de 8 MB.", ephemeral=True)
            return
        data = await arquivo.read()
        try:
            note = bot.foundry_outbox.push(
                interaction.user.display_name,
                text=texto,
                upload=(arquivo.filename, arquivo.content_type or "", data),
            )
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        if note is None:
            await interaction.response.send_message("Arquivo vazio.", ephemeral=True)
            return
        config = _load_config(bot)
        channel = bot.get_channel(int(config["channel_id"])) if config.get("channel_id") else None
        message = "Arquivo na fila do Foundry."
        if channel is not None and channel.id != interaction.channel_id:
            await channel.send(
                f"[DISCORD] **{interaction.user.display_name}** {texto}".strip(),
                file=discord.File(io.BytesIO(data), filename=note.filename),
            )
            message = f"Arquivo enviado em {channel.mention} e na fila do Foundry."
        await interaction.response.send_message(
            message + " O módulo precisa estar ativo na mesa, neste computador.",
            file=discord.File(io.BytesIO(data), filename=note.filename),
        )

    @navegador.command(name="falar", description="Envia um texto deste Discord para o chat do Foundry.")
    async def falar(interaction: discord.Interaction, texto: str) -> None:
        if not await gate(interaction):
            return
        note = bot.foundry_outbox.push(interaction.user.display_name, text=texto)
        if note is None:
            await interaction.response.send_message("Texto vazio.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Texto na fila do Foundry. O módulo precisa estar ativo na mesa, neste computador."
        )

    @navegador.command(name="modulo", description="Envia o módulo do Foundry VTT para instalar na pasta modules.")
    async def modulo(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        folder = Path(__file__).resolve().parents[1] / "foundry" / "congo-grey-parrot"
        if not folder.is_dir():
            await interaction.response.send_message(
                "A pasta foundry/congo-grey-parrot não está junto do bot.", ephemeral=True
            )
            return
        blob = io.BytesIO()
        with zipfile.ZipFile(blob, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    archive.write(path, Path("congo-grey-parrot") / path.relative_to(folder))
        blob.seek(0)
        await interaction.response.send_message(
            "Copie a pasta congo-grey-parrot para Data/modules do Foundry, ative o módulo no mundo "
            "e volte à mesa. A instalação do Foundry explica a pasta Data em "
            "https://foundryvtt.com/article/module-development/.",
            file=discord.File(blob, filename="congo-grey-parrot-foundry.zip"),
            ephemeral=True,
        )

    async def autostart() -> None:
        await bot.wait_until_ready()
        if not bot.store.enabled("navegador"):
            return
        if _server_handle["task"] and not _server_handle["task"].done():
            return
        try:
            await bind(_DEFAULT_PORT)
        except OSError:
            return

    bot.loop.create_task(autostart())
    bot.tree.add_command(navegador)
