from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

FEATURE = "musica"
DESCRIPTION = (
    "Toca áudio no canal de voz: link do YouTube, link do Spotify, "
    "lista de reprodução salva ou arquivo de áudio enviado. "
    "Gerencia fila e listas por servidor."
)

_YTDLP_OPTS: dict = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

_FFMPEG_OPTIONS: dict = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


def _playlists_path(bot) -> Path:
    return bot.sounds.parent / "playlists.json"


def _load_playlists(bot) -> dict:
    path = _playlists_path(bot)
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_playlists(bot, data: dict) -> None:
    _playlists_path(bot).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _fetch_audio(url: str) -> tuple[str | None, str | None]:
    """Returns (stream_url, title) or (None, error_message)."""
    try:
        import yt_dlp
    except ImportError:
        return None, "yt-dlp não está instalado. pip install yt-dlp"
    opts = dict(_YTDLP_OPTS)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None, "Nenhum resultado para esse link ou busca."
            if "entries" in info:
                entry = next((e for e in info["entries"] if e), None)
                if entry is None:
                    return None, "A lista não tem faixas acessíveis."
                info = entry
            stream_url = info.get("url") or info.get("webpage_url")
            title = info.get("title") or url
            return stream_url, title
    except Exception as exc:
        return None, f"Não consegui buscar o áudio: {exc}"


def _ensure_queue(bot, guild_id: int) -> list:
    if not hasattr(bot, "_music_queues"):
        bot._music_queues = {}
    if guild_id not in bot._music_queues:
        bot._music_queues[guild_id] = []
    return bot._music_queues[guild_id]


def _clear_queue(bot, guild_id: int) -> None:
    if hasattr(bot, "_music_queues"):
        bot._music_queues[guild_id] = []


def setup(bot) -> None:
    import discord
    from discord import app_commands

    musica = app_commands.Group(name="musica", description="Toca áudio no canal de voz")
    playlist_group = app_commands.Group(
        name="playlist", description="Gerencia listas de reprodução salvas", parent=musica
    )

    async def gate(interaction: discord.Interaction) -> bool:
        if bot.store.enabled("musica"):
            return True
        await interaction.response.send_message(
            "A função musica está desativada. Use /funcoes ativar musica.", ephemeral=True
        )
        return False

    async def join_voice(interaction: discord.Interaction):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        channel = member.voice.channel if member and member.voice else None
        if channel is None:
            await interaction.response.send_message(
                "Entre em um canal de voz antes de usar esse comando.", ephemeral=True
            )
            return None
        voice = interaction.guild.voice_client if interaction.guild else None
        if voice is None:
            voice = await channel.connect()
        elif getattr(voice, "channel", None) != channel:
            await voice.move_to(channel)
        return voice

    async def play_next(guild_id: int, voice, response_channel) -> None:
        queue = _ensure_queue(bot, guild_id)
        if not queue:
            return
        track = queue[0]

        def after_play(error):
            if error and response_channel is not None:
                asyncio.run_coroutine_threadsafe(
                    response_channel.send(f"Erro durante a reprodução: {error}"),
                    bot.loop,
                )
            tmp = track.get("tmp_path")
            if tmp:
                Path(tmp).unlink(missing_ok=True)
            if queue and queue[0] is track:
                queue.pop(0)
            asyncio.run_coroutine_threadsafe(
                play_next(guild_id, voice, response_channel), bot.loop
            )

        try:
            source = discord.FFmpegPCMAudio(track["url"], **_FFMPEG_OPTIONS)
            voice.play(source, after=after_play)
            if response_channel is not None:
                await response_channel.send(f"Tocando: **{track['title']}**")
        except Exception as exc:
            if response_channel is not None:
                await response_channel.send(
                    f"Não consegui tocar '{track['title']}'. "
                    f"FFmpeg precisa estar instalado: https://ffmpeg.org/download.html\n{exc}"
                )
            if queue and queue[0] is track:
                queue.pop(0)

    @musica.command(
        name="tocar",
        description="Toca um link do YouTube, Spotify ou busca por nome. Adiciona à fila se algo já toca.",
    )
    async def tocar(interaction: discord.Interaction, link_ou_busca: str) -> None:
        if not await gate(interaction):
            return
        voice = await join_voice(interaction)
        if voice is None:
            return
        await interaction.response.defer()
        stream_url, title = await asyncio.to_thread(_fetch_audio, link_ou_busca)
        if stream_url is None:
            await interaction.followup.send(title or "Não achei esse link.", ephemeral=True)
            return
        queue = _ensure_queue(bot, interaction.guild_id)
        track = {"url": stream_url, "title": title, "source": link_ou_busca}
        queue.append(track)
        if voice.is_playing() or len(queue) > 1:
            await interaction.followup.send(
                f"Adicionado à fila na posição {len(queue)}: **{title}**"
            )
        else:
            await interaction.followup.send(f"Carregando: **{title}**")
            await play_next(interaction.guild_id, voice, interaction.channel)

    @musica.command(
        name="arquivo",
        description="Toca um arquivo de áudio enviado diretamente no comando.",
    )
    async def arquivo(interaction: discord.Interaction, audio: discord.Attachment) -> None:
        if not await gate(interaction):
            return
        voice = await join_voice(interaction)
        if voice is None:
            return
        await interaction.response.defer()
        data = await audio.read()
        suffix = Path(audio.filename).suffix or ".mp3"
        handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        handle.write(data)
        handle.flush()
        handle.close()
        tmp_path = handle.name
        queue = _ensure_queue(bot, interaction.guild_id)
        track = {
            "url": tmp_path,
            "title": audio.filename,
            "source": "arquivo",
            "tmp_path": tmp_path,
        }
        queue.append(track)
        if voice.is_playing() or len(queue) > 1:
            await interaction.followup.send(
                f"Arquivo adicionado à fila na posição {len(queue)}: **{audio.filename}**"
            )
        else:
            await interaction.followup.send(f"Carregando arquivo: **{audio.filename}**")
            await play_next(interaction.guild_id, voice, interaction.channel)

    @musica.command(name="pular", description="Pula a faixa atual.")
    async def pular(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        voice = interaction.guild.voice_client if interaction.guild else None
        if voice and voice.is_playing():
            voice.stop()
            await interaction.response.send_message("Faixa pulada.")
        else:
            await interaction.response.send_message("Nada está tocando.", ephemeral=True)

    @musica.command(name="parar", description="Para a reprodução, esvazia a fila e sai do canal.")
    async def parar(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        _clear_queue(bot, interaction.guild_id)
        voice = interaction.guild.voice_client if interaction.guild else None
        if voice is not None:
            voice.stop()
            await voice.disconnect()
        await interaction.response.send_message("Reprodução parada e fila limpa.")

    @musica.command(name="fila", description="Mostra as faixas na fila de reprodução.")
    async def fila(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        queue = _ensure_queue(bot, interaction.guild_id)
        if not queue:
            await interaction.response.send_message("A fila está vazia.", ephemeral=True)
            return
        lines = [
            f"{'> ' if i == 0 else f'{i + 1}. '}{t['title']}"
            for i, t in enumerate(queue[:20])
        ]
        if len(queue) > 20:
            lines.append(f"... e mais {len(queue) - 20} faixa(s).")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @playlist_group.command(name="criar", description="Cria uma lista de reprodução nomeada para este servidor.")
    async def playlist_criar(interaction: discord.Interaction, nome: str) -> None:
        if not await gate(interaction):
            return
        data = _load_playlists(bot)
        guild_key = str(interaction.guild_id)
        data.setdefault(guild_key, {})
        if nome in data[guild_key]:
            await interaction.response.send_message(
                f"Já existe uma lista chamada '{nome}'.", ephemeral=True
            )
            return
        data[guild_key][nome] = []
        _save_playlists(bot, data)
        await interaction.response.send_message(
            f"Lista '{nome}' criada. Adicione faixas com /musica playlist adicionar."
        )

    @playlist_group.command(
        name="adicionar",
        description="Adiciona um link do YouTube ou Spotify a uma lista de reprodução.",
    )
    async def playlist_adicionar(
        interaction: discord.Interaction, nome: str, link: str
    ) -> None:
        if not await gate(interaction):
            return
        data = _load_playlists(bot)
        guild_key = str(interaction.guild_id)
        if nome not in data.get(guild_key, {}):
            await interaction.response.send_message(
                f"Lista '{nome}' não existe. Crie com /musica playlist criar.", ephemeral=True
            )
            return
        await interaction.response.defer()
        stream_url, title = await asyncio.to_thread(_fetch_audio, link)
        if stream_url is None:
            await interaction.followup.send(title or "Não achei esse link.", ephemeral=True)
            return
        data[guild_key][nome].append({"url": stream_url, "title": title, "source": link})
        _save_playlists(bot, data)
        pos = len(data[guild_key][nome])
        await interaction.followup.send(
            f"**{title}** adicionado à lista '{nome}' na posição {pos}."
        )

    @playlist_group.command(name="listar", description="Mostra todas as listas de reprodução deste servidor.")
    async def playlist_listar(interaction: discord.Interaction) -> None:
        if not await gate(interaction):
            return
        data = _load_playlists(bot)
        guild_playlists = data.get(str(interaction.guild_id), {})
        if not guild_playlists:
            await interaction.response.send_message(
                "Nenhuma lista criada. Use /musica playlist criar.", ephemeral=True
            )
            return
        lines = [
            f"{nome}: {len(faixas)} faixa(s)" for nome, faixas in guild_playlists.items()
        ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @playlist_group.command(name="ver", description="Mostra as faixas de uma lista de reprodução.")
    async def playlist_ver(interaction: discord.Interaction, nome: str) -> None:
        if not await gate(interaction):
            return
        data = _load_playlists(bot)
        tracks = data.get(str(interaction.guild_id), {}).get(nome)
        if tracks is None:
            await interaction.response.send_message(
                f"Lista '{nome}' não existe.", ephemeral=True
            )
            return
        if not tracks:
            await interaction.response.send_message(
                f"A lista '{nome}' está vazia.", ephemeral=True
            )
            return
        lines = [f"{i + 1}. {t['title']}" for i, t in enumerate(tracks[:20])]
        if len(tracks) > 20:
            lines.append(f"... e mais {len(tracks) - 20} faixa(s).")
        await interaction.response.send_message(
            f"**Lista '{nome}'**:\n" + "\n".join(lines), ephemeral=True
        )

    @playlist_group.command(
        name="tocar",
        description="Adiciona todas as faixas de uma lista à fila e começa a tocar.",
    )
    async def playlist_tocar(interaction: discord.Interaction, nome: str) -> None:
        if not await gate(interaction):
            return
        data = _load_playlists(bot)
        tracks = data.get(str(interaction.guild_id), {}).get(nome)
        if not tracks:
            await interaction.response.send_message(
                f"Lista '{nome}' não existe ou está vazia.", ephemeral=True
            )
            return
        voice = await join_voice(interaction)
        if voice is None:
            return
        await interaction.response.defer()
        queue = _ensure_queue(bot, interaction.guild_id)
        was_empty = not voice.is_playing() and not queue
        queue.extend(tracks)
        await interaction.followup.send(
            f"{len(tracks)} faixa(s) da lista '{nome}' adicionadas à fila."
        )
        if was_empty:
            await play_next(interaction.guild_id, voice, interaction.channel)

    @playlist_group.command(
        name="remover",
        description="Remove uma faixa de uma lista de reprodução pelo número de posição.",
    )
    async def playlist_remover(
        interaction: discord.Interaction, nome: str, posicao: int
    ) -> None:
        if not await gate(interaction):
            return
        data = _load_playlists(bot)
        guild_key = str(interaction.guild_id)
        tracks = data.get(guild_key, {}).get(nome)
        if tracks is None:
            await interaction.response.send_message(
                f"Lista '{nome}' não existe.", ephemeral=True
            )
            return
        if not 1 <= posicao <= len(tracks):
            await interaction.response.send_message(
                f"Posição inválida. A lista '{nome}' tem {len(tracks)} faixa(s).",
                ephemeral=True,
            )
            return
        removed = tracks.pop(posicao - 1)
        _save_playlists(bot, data)
        await interaction.response.send_message(
            f"**{removed['title']}** removido da lista '{nome}'."
        )

    @playlist_group.command(name="apagar", description="Apaga uma lista de reprodução inteira.")
    async def playlist_apagar(interaction: discord.Interaction, nome: str) -> None:
        if not await gate(interaction):
            return
        data = _load_playlists(bot)
        guild_key = str(interaction.guild_id)
        if nome not in data.get(guild_key, {}):
            await interaction.response.send_message(
                f"Lista '{nome}' não existe.", ephemeral=True
            )
            return
        del data[guild_key][nome]
        _save_playlists(bot, data)
        await interaction.response.send_message(f"Lista '{nome}' apagada.")

    bot.tree.add_command(musica)
