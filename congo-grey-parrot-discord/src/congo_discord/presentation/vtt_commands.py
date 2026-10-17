from __future__ import annotations

import asyncio

import discord
from discord import app_commands

from congo_discord.domain.vtt_catalog import catalog_text, find_vtt
from congo_discord.service.vtt_bridge import check_table_url, post_event


def register_vtt(bot) -> None:
    vtt = app_commands.Group(name="vtt", description="Liga a mesa virtual, da lista ou de fora dela")

    async def gate(interaction: discord.Interaction) -> bool:
        if bot.store.enabled("vtt"):
            return True
        await interaction.response.send_message(
            "A função vtt está desativada. Quem administra o servidor pode usar /funcoes ativar.",
            ephemeral=True,
        )
        return False

    def manages(interaction: discord.Interaction) -> bool:
        from congo_discord.presentation.bot import _can_manage

        return _can_manage(interaction)

    @vtt.command(name="catalogo", description="Mostra as mesas conhecidas e como conectar uma que não esteja na lista.")
    async def catalogo(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        await interaction.response.send_message(catalog_text()[:1900], ephemeral=True)

    @vtt.command(name="conectar", description="Guarda o link ou o webhook de qualquer mesa.")
    async def conectar(
        interaction: discord.Interaction,
        nome: str,
        url: str,
        token: str = "",
    ) -> None:
        if not await gate(interaction):
            return
        if interaction.guild_id is None or not manages(interaction):
            await interaction.response.send_message("Só quem administra o servidor conecta uma mesa.", ephemeral=True)
            return
        try:
            safe = check_table_url(url)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        known = find_vtt(nome)
        label = known.name if known else nome.strip()[:80]
        bot.store.set_vtt(str(interaction.guild_id), label, safe, token.strip(), known is not None)
        extra = ""
        if known is None:
            extra = " Esse nome não está na lista, e a conexão genérica aceita isso."
        secret = " Token guardado." if token.strip() else ""
        await interaction.response.send_message(
            f"Mesa conectada: {label}. {safe}.{secret}{extra} O bot não entra na conta da plataforma.",
            ephemeral=True,
        )

    @vtt.command(name="atual", description="Mostra a mesa conectada, sem revelar o token.")
    async def atual(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        row = bot.store.vtt(str(interaction.guild_id)) if interaction.guild_id else None
        if row is None:
            await interaction.response.send_message("Nenhuma mesa conectada. Use /vtt conectar.", ephemeral=True)
            return
        token = "sim" if row["token"] else "não"
        await interaction.response.send_message(
            f"{row['name']}\n{row['url']}\nToken: {token}",
            ephemeral=True,
        )

    @vtt.command(name="testar", description="Envia um aviso de teste para o endereço conectado.")
    async def testar(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        if not manages(interaction):
            await interaction.response.send_message("Só quem administra o servidor testa a mesa.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        text = await _send(bot, interaction, "ping", "Teste de conexão do Congo Grey Parrot.")
        await interaction.followup.send(text, ephemeral=True)

    @vtt.command(name="enviar", description="Envia um texto para a mesa conectada.")
    async def enviar(interaction: discord.Interaction, texto: str) -> None:
        if not await gate(interaction):
            return
        await interaction.response.defer()
        text = await _send(bot, interaction, "note", texto[:1500])
        await interaction.followup.send(text)

    @vtt.command(name="desconectar", description="Esquece a mesa conectada neste servidor.")
    async def desconectar(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        if interaction.guild_id is None or not manages(interaction):
            await interaction.response.send_message("Só quem administra o servidor desconecta a mesa.", ephemeral=True)
            return
        if bot.store.clear_vtt(str(interaction.guild_id)):
            await interaction.response.send_message("Mesa desconectada.")
            return
        await interaction.response.send_message("Não havia mesa conectada.", ephemeral=True)

    bot.tree.add_command(vtt)


async def relay_roll(bot, interaction: discord.Interaction, text: str) -> None:
    outbox = getattr(bot, "foundry_outbox", None)
    if outbox is not None and text.strip():
        outbox.push(interaction.user.display_name, text=text)
    if interaction.guild_id is None or not bot.store.enabled("vtt"):
        return
    if bot.store.vtt(str(interaction.guild_id)) is None:
        return
    result = await _send(bot, interaction, "roll", text)
    if result.startswith("Enviado"):
        return
    await interaction.followup.send(result, ephemeral=True)


async def _send(bot, interaction: discord.Interaction, kind: str, text: str) -> str:
    if interaction.guild_id is None:
        return "A mesa só conecta dentro de um servidor."
    row = bot.store.vtt(str(interaction.guild_id))
    if row is None:
        return "Nenhuma mesa conectada. Use /vtt conectar."
    payload = {
        "source": "congo-grey-parrot-discord",
        "kind": kind,
        "user": interaction.user.display_name,
        "text": text,
    }
    try:
        status, _body = await asyncio.to_thread(post_event, row["url"], row["token"], payload)
    except ValueError as exc:
        return str(exc)
    if status >= 400:
        return f"A mesa respondeu {status}. O endereço recebeu o aviso, mas recusou."
    return f"Enviado para {row['name']} ({status})."
