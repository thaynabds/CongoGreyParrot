from __future__ import annotations

import asyncio
import json
from pathlib import Path

FEATURE = "navegador"
DESCRIPTION = (
    "Lê rolagens do navegador (Roll20 e outros VTTs) via userscript Tampermonkey "
    "e retransmite no Discord. Usa um servidor HTTP local que só aceita conexões de localhost."
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
// @version      1.1
// @description  Envia rolagens do Roll20 para o bot de Discord rodando no computador.
// @author       Thayná Batista da Silva
// @match        https://app.roll20.net/editor/*
// @match        https://app.roll20.net/campaigns/*
// @match        http://localhost:30000/*
// @match        http://127.0.0.1:30000/*
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

    function isFoundry() {{
        return location.hostname === 'localhost' || location.hostname === '127.0.0.1';
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

    if (isFoundry()) {{
        observeFoundry();
    }} else {{
        observeRoll20();
    }}
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

    async def gate(interaction: discord.Interaction) -> bool:
        if bot.store.enabled("navegador"):
            return True
        await interaction.response.send_message(
            "A função navegador está desativada. Use /funcoes ativar navegador.", ephemeral=True
        )
        return False

    async def handle_roll(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            raw = await asyncio.wait_for(reader.read(8192), timeout=5)
        except asyncio.TimeoutError:
            writer.close()
            return
        text = raw.decode("utf-8", errors="replace")

        # Parse method and path from first line
        first_line = text.split("\r\n", 1)[0] if "\r\n" in text else text.split("\n", 1)[0]
        parts = first_line.split()
        method = parts[0] if parts else ""
        path = parts[1] if len(parts) > 1 else ""

        # Respond to CORS preflight
        if method == "OPTIONS":
            writer.write(
                b"HTTP/1.1 204 No Content\r\n"
                b"Access-Control-Allow-Origin: *\r\n"
                b"Access-Control-Allow-Methods: POST, OPTIONS\r\n"
                b"Access-Control-Allow-Headers: Content-Type\r\n"
                b"\r\n"
            )
            await writer.drain()
            writer.close()
            return

        if method != "POST" or path != "/roll":
            writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot Found")
            await writer.drain()
            writer.close()
            return

        # Extract JSON body (after blank line)
        separator = "\r\n\r\n" if "\r\n\r\n" in text else "\n\n"
        body = text.split(separator, 1)[1] if separator in text else ""
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            writer.write(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 12\r\n\r\nJSON inválido")
            await writer.drain()
            writer.close()
            return

        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nAccess-Control-Allow-Origin: *\r\n\r\nOK")
        await writer.drain()
        writer.close()

        # Forward to Discord
        config = _load_config(bot)
        channel_id = config.get("channel_id")
        if not channel_id:
            return
        channel = bot.get_channel(int(channel_id))
        if channel is None:
            return

        vtt = payload.get("vtt", "VTT")
        player = payload.get("player", "?")
        expression = payload.get("expression", "")
        total = payload.get("total", "")
        detail = payload.get("detail", "")

        parts_msg = [f"[{vtt.upper()}] **{player}**"]
        if expression:
            parts_msg.append(f"`{expression}`")
        if total:
            parts_msg.append(f"= **{total}**")
        if detail:
            parts_msg.append(f"({detail[:200]})")
        await channel.send(" ".join(parts_msg))

    async def start_server(port: int) -> None:
        server = await asyncio.start_server(handle_roll, "127.0.0.1", port)
        _server_handle["server"] = server
        async with server:
            await server.serve_forever()

    @navegador.command(name="ligar", description="Inicia o servidor local que recebe rolagens do navegador.")
    async def ligar(interaction: discord.Interaction, porta: int = _DEFAULT_PORT) -> None:
        if not await gate(interaction):
            return
        if _server_handle["task"] and not _server_handle["task"].done():
            await interaction.response.send_message(
                f"O relay já está rodando na porta {_server_handle['port']}.", ephemeral=True
            )
            return
        _server_handle["port"] = porta
        try:
            task = bot.loop.create_task(start_server(porta))
            _server_handle["task"] = task
            await interaction.response.send_message(
                f"Relay iniciado na porta {porta}. "
                "Instale o userscript no Tampermonkey com `/navegador userscript`. "
                "Defina o canal de destino com `/navegador canal`."
            )
        except OSError as exc:
            await interaction.response.send_message(
                f"Não consegui abrir a porta {porta}: {exc}", ephemeral=True
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

    bot.tree.add_command(navegador)
