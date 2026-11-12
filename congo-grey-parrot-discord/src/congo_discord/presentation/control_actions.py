"""Ações que só o bot ligado consegue fazer (voz, botões, mensagens), pedidas pelo AI Conector.

Cada ação confere ids numéricos, respeita as funções desligadas em /funcoes e nunca
deixa o texto chamar @everyone, cargos ou pessoas.
"""

from __future__ import annotations

import logging

import discord

from congo_discord.service.control import start_server

log = logging.getLogger(__name__)
_NO_MENTIONS = discord.AllowedMentions.none()


def _id(args: dict, key: str) -> int:
    raw = str(args.get(key, "")).strip()
    if not raw.isdigit() or len(raw) > 20:
        raise ValueError(f"Informe {key} com o número do Discord.")
    return int(raw)


def _text(args: dict, key: str, limit: int = 1800) -> str:
    value = str(args.get(key, "")).strip()
    if not value:
        raise ValueError(f"Escreva {key}.")
    return value[:limit]


def _gate(bot, key: str) -> None:
    if not bot.store.enabled(key):
        raise ValueError(f"A função {key} está desativada. Ative com funcoes_ativar.")


async def _text_channel(bot, args: dict, key: str = "canal_id"):
    channel = bot.get_channel(_id(args, key))
    if channel is None:
        channel = await bot.fetch_channel(_id(args, key))
    if not isinstance(channel, discord.abc.Messageable):
        raise ValueError("Esse canal não recebe mensagens.")
    return channel


def _voice_channel(bot, args: dict):
    channel = bot.get_channel(_id(args, "canal_voz_id"))
    if not isinstance(channel, discord.VoiceChannel | discord.StageChannel):
        raise ValueError("Esse id não é de um canal de voz que o bot enxerga. Use servidores.")
    return channel


def _guild(bot, args: dict):
    guild = bot.get_guild(_id(args, "servidor_id"))
    if guild is None:
        raise ValueError("O bot não está nesse servidor. Use servidores.")
    return guild


async def _servidores(bot, args: dict) -> str:
    lines = []
    for guild in bot.guilds:
        lines.append(f"Servidor {guild.name} ({guild.id})")
        for channel in guild.text_channels[:50]:
            lines.append(f"  texto #{channel.name} ({channel.id})")
        for channel in guild.voice_channels[:50]:
            people = len(channel.members)
            lines.append(f"  voz {channel.name} ({channel.id}), {people} pessoa(s)")
        voice = guild.voice_client
        if voice is not None:
            lines.append(f"  o bot está na voz: {voice.channel}")
    return "\n".join(lines) or "O bot ainda não está em nenhum servidor."


async def _enviar(bot, args: dict) -> str:
    channel = await _text_channel(bot, args)
    message = await channel.send(_text(args, "texto"), allowed_mentions=_NO_MENTIONS)
    return f"Mensagem enviada (id {message.id})."


async def _tocar(bot, args: dict) -> str:
    from congo_discord.presentation.bot import _sound_path, start_audio

    _gate(bot, "ambiente")
    channel = _voice_channel(bot, args)
    path = _sound_path(bot.sounds, _text(args, "arquivo", 200))
    if path is None:
        raise ValueError(f"Não achei esse arquivo em {bot.sounds}. Use listar_sons.")
    voice = channel.guild.voice_client
    if voice is None:
        voice = await channel.connect()
    elif voice.channel != channel:
        await voice.move_to(channel)
    loop = bool(args.get("repetir", False))
    start_audio(voice, path, loop)
    return f"Tocando {path.name} em {channel.name}." + (" Em repetição." if loop else "")


async def _parar(bot, args: dict) -> str:
    voice = _guild(bot, args).voice_client
    if voice is not None:
        voice.stop()
    return "Áudio parado."


async def _sair(bot, args: dict) -> str:
    guild = _guild(bot, args)
    bot.meetings.pop(guild.id, None)
    voice = guild.voice_client
    if voice is None:
        return "O bot não estava em canal de voz."
    if getattr(voice, "is_listening", lambda: False)():
        voice.stop_listening()
    await voice.disconnect()
    return "Saí do canal de voz."


async def _marcar(bot, args: dict) -> str:
    from congo_discord.presentation.bot import session_view

    _gate(bot, "agenda")
    channel = await _text_channel(bot, args)
    title = _text(args, "titulo", 200)
    when = _text(args, "quando", 200)
    guild_id = str(getattr(getattr(channel, "guild", None), "id", ""))
    session_id = bot.store.add_session(guild_id, str(channel.id), title, when)
    view = session_view(bot.store, session_id)
    bot.add_view(view)
    await channel.send(f"{title}\nQuando: {when}\nEscolha uma opção.", view=view, allowed_mentions=_NO_MENTIONS)
    return f"Sessão marcada em #{getattr(channel, 'name', channel.id)} com os botões de presença."


async def _reuniao_entrar(bot, args: dict) -> str:
    from congo_discord.presentation.bot import _flush_meeting, _Sink
    from congo_discord.service.meeting_audio import MeetingAudio

    _gate(bot, "reuniao")
    channel = _voice_channel(bot, args)
    text_channel = await _text_channel(bot, args, "canal_texto_id") if args.get("canal_texto_id") else None
    try:
        from discord.ext import voice_recv
    except ImportError:
        raise ValueError("Falta o pacote discord-ext-voice-recv no ambiente do bot.") from None
    client = channel.guild.voice_client
    if client is None:
        client = await channel.connect(cls=voice_recv.VoiceRecvClient)
    elif client.channel != channel:
        await client.move_to(channel)
    if not hasattr(client, "listen"):
        raise ValueError("O bot já está na voz tocando som. Use sair_voz e tente de novo.")
    audio = MeetingAudio()
    bot.meetings[channel.guild.id] = audio
    client.listen(_Sink(audio))
    bot.loop.create_task(_flush_meeting(bot, channel.guild.id, text_channel))
    if text_channel is not None:
        await text_channel.send(
            "O AI Conector ligou a transcrição desta chamada. Cada fala fica com o nome de quem falou.",
            allowed_mentions=_NO_MENTIONS,
        )
    return f"Transcrevendo a chamada em {channel.name}. Use sair_voz para parar."


ACTIONS = {
    "servidores": _servidores,
    "enviar_mensagem": _enviar,
    "tocar_som": _tocar,
    "parar_som": _parar,
    "sair_voz": _sair,
    "marcar_sessao": _marcar,
    "reuniao_entrar": _reuniao_entrar,
}


async def start_control(bot):
    async def handler(action: str, args: dict) -> str:
        function = ACTIONS.get(action)
        if function is None:
            raise ValueError("Ação desconhecida.")
        await bot.wait_until_ready()
        log.info("AI Conector: %s", action)
        try:
            return await function(bot, args)
        except discord.Forbidden:
            raise ValueError("O Discord negou: falta permissão para o bot nesse canal.") from None
        except discord.NotFound:
            raise ValueError("O Discord não achou esse canal.") from None

    try:
        bot._congo_control = await start_server(handler)
    except OSError as exc:  # o bot funciona sem o canal; só o AI Conector fica limitado
        log.warning("AI Conector sem canal local: %s", exc)
