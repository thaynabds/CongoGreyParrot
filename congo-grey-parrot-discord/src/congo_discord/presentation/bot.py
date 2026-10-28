from __future__ import annotations

import asyncio
import io
import os
import tempfile
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from congo_discord.domain.dice import roll_expression, roll_pair, roll_percent, roll_pool
from congo_discord.domain.names import fantasy_name
from congo_discord.domain.rules import spell_text
from congo_discord.domain.summary import Utterance, render_meeting
from congo_discord.presentation.vtt_commands import register_vtt, relay_roll
from congo_discord.service.envfile import load_env_file
from congo_discord.service.foundry_relay import prepare_upload
from congo_discord.service.meeting_audio import MeetingAudio
from congo_discord.service.plugins import load_plugins
from congo_discord.service.updater import update_report

_WHISPER = "https://github.com/SYSTRAN/faster-whisper"
_VOICE_RECV = "https://github.com/imayhaveborkedit/discord-ext-voice-recv"
_FFMPEG = "https://ffmpeg.org/download.html"
_OPEN5E = "https://open5e.com/"
_DISCORD_APP = "https://discord.com/developers/applications"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _owner_id() -> int | None:
    raw = os.environ.get("CONGO_DISCORD_OWNER_ID", "")
    return int(raw) if raw.isdigit() else None


def _can_manage(interaction: discord.Interaction) -> bool:
    if interaction.user.id == _owner_id():
        return True
    permissions = getattr(interaction, "permissions", None)
    return bool(permissions and permissions.manage_guild)


def _clip(text: str, limit: int = 1800) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n... texto cortado."


class CongoBot(commands.Bot):
    def __init__(self, store, repo: Path, sounds: Path, plugins: Path):
        intents = discord.Intents.default()
        intents.voice_states = True
        # Texto digitado por jogadores volta no canal. Ninguém chama @everyone ou um cargo pelo bot.
        super().__init__(
            command_prefix="!",
            intents=intents,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True),
        )
        self.store = store
        self.repo = repo
        self.sounds = sounds
        self.plugins = plugins
        self.meetings: dict[int, MeetingAudio] = {}
        self._whisper = None

    async def setup_hook(self) -> None:
        register(self)
        load_plugins(self.plugins, self.store, self)
        for row in self.store.all_sessions():
            self.add_view(session_view(self.store, int(row["id"])))
        guild = os.environ.get("CONGO_DISCORD_GUILD_ID", "")
        if guild.isdigit():
            target = discord.Object(id=int(guild))
            self.tree.copy_global_to(guild=target)
            await self.tree.sync(guild=target)
        else:
            await self.tree.sync()


def session_view(store, session_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    for status in ("Confirmado", "Atrasado", "Ausente"):
        button = discord.ui.Button(label=status, custom_id=f"sessao:{session_id}:{status}")

        async def callback(interaction: discord.Interaction, chosen: str = status, current: int = session_id) -> None:
            store.rsvp(current, str(interaction.user.id), chosen)
            counts = store.rsvp_counts(current)
            detail = ", ".join(f"{name} {total}" for name, total in counts.items()) or "sem respostas"
            await interaction.response.send_message(f"{interaction.user.display_name}: {chosen}. {detail}", ephemeral=True)

        button.callback = callback
        view.add_item(button)
    return view


def register(bot: CongoBot) -> None:
    dados = app_commands.Group(name="dados", description="Rolagens da mesa")
    ficha = app_commands.Group(name="ficha", description="Atributos do jogador")
    iniciativa = app_commands.Group(name="iniciativa", description="Ordem de turno")
    regra = app_commands.Group(name="regra", description="Consulta curta de regras")
    som = app_commands.Group(name="som", description="Som de fundo e efeito")
    sessao = app_commands.Group(name="sessao", description="Agenda da mesa")
    grupo = app_commands.Group(name="grupo", description="Inventário, ouro e XP")
    reuniao = app_commands.Group(name="reuniao", description="Chamada e transcrição ao vivo")
    arquivo = app_commands.Group(name="arquivo", description="Transcrição e leitura de um arquivo")
    funcoes = app_commands.Group(name="funcoes", description="Liga, desliga, adiciona ou remove funções")

    async def gate(interaction: discord.Interaction, key: str) -> bool:
        if bot.store.enabled(key):
            return True
        await interaction.response.send_message(
            f"A função {key} está desativada. Quem administra o servidor pode usar /funcoes ativar.",
            ephemeral=True,
        )
        return False

    @dados.command(name="rolar", description="Rola uma expressão, por exemplo 1d20+5 ou 2d6+1d4.")
    async def rolar(interaction: discord.Interaction, expressao: str) -> None:
        if not await gate(interaction, "dados"):
            return
        text = _roll_text(expressao)
        await interaction.response.send_message(text)
        if "\n" in text:
            await relay_roll(bot, interaction, text)

    @dados.command(name="vantagem", description="Rola a expressão duas vezes e fica com o maior total.")
    async def vantagem(interaction: discord.Interaction, expressao: str) -> None:
        if not await gate(interaction, "dados"):
            return
        text = _pair_text(expressao, high=True)
        await interaction.response.send_message(text)
        if "\n" in text:
            await relay_roll(bot, interaction, text)

    @dados.command(name="desvantagem", description="Rola a expressão duas vezes e fica com o menor total.")
    async def desvantagem(interaction: discord.Interaction, expressao: str) -> None:
        if not await gate(interaction, "dados"):
            return
        text = _pair_text(expressao, high=False)
        await interaction.response.send_message(text)
        if "\n" in text:
            await relay_roll(bot, interaction, text)

    @dados.command(name="percentil", description="Rola 1d100 contra uma perícia de 1 a 100.")
    async def percentil(interaction: discord.Interaction, pericia: int) -> None:
        if not await gate(interaction, "dados"):
            return
        try:
            result = roll_percent(pericia)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        text = (
            f"{result.expression}: {result.total}. {result.detail}. "
            "Isto é uma leitura simples de d100. A regra oficial do jogo continua no livro da editora."
        )
        await interaction.response.send_message(text)
        await relay_roll(bot, interaction, text)

    @dados.command(name="pool", description="Conta quantos dados atingiram o limite.")
    async def pool(interaction: discord.Interaction, quantidade: int, faces: int = 10, limite: int = 6) -> None:
        if not await gate(interaction, "dados"):
            return
        try:
            result = roll_pool(quantidade, faces, limite)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        text = f"Sucessos: {result.total}. Dados: {result.detail}."
        await interaction.response.send_message(text)
        await relay_roll(bot, interaction, text)

    @dados.command(name="oculto", description="Rola e mostra o resultado só para quem chamou o comando.")
    async def oculto(interaction: discord.Interaction, expressao: str) -> None:
        if not await gate(interaction, "dados"):
            return
        await interaction.response.send_message(_roll_text(expressao), ephemeral=True)

    @ficha.command(name="definir", description="Guarda um modificador, por exemplo percepcao 3.")
    async def ficha_definir(interaction: discord.Interaction, atributo: str, modificador: int) -> None:
        if not await gate(interaction, "fichas"):
            return
        bot.store.set_attribute(str(interaction.guild_id), str(interaction.user.id), atributo, modificador)
        await interaction.response.send_message(f"{atributo.lower()}: {modificador:+d}", ephemeral=True)

    @ficha.command(name="ver", description="Mostra os atributos guardados de um jogador.")
    async def ficha_ver(interaction: discord.Interaction, jogador: discord.Member | None = None) -> None:
        if not await gate(interaction, "fichas"):
            return
        person = jogador or interaction.user
        rows = bot.store.sheet(str(interaction.guild_id), str(person.id))
        if not rows:
            await interaction.response.send_message(f"{person.display_name} ainda não tem atributos.", ephemeral=True)
            return
        lines = [f"{row['attribute']}: {int(row['modifier']):+d}" for row in rows]
        await interaction.response.send_message(f"{person.display_name}\n" + "\n".join(lines))

    @ficha.command(name="rolar", description="Rola 1d20 mais o modificador guardado.")
    async def ficha_rolar(interaction: discord.Interaction, atributo: str) -> None:
        if not await gate(interaction, "fichas"):
            return
        modifier = bot.store.attribute(str(interaction.guild_id), str(interaction.user.id), atributo)
        if modifier is None:
            await interaction.response.send_message("Esse atributo ainda não está na ficha.", ephemeral=True)
            return
        sign = f"+{modifier}" if modifier >= 0 else str(modifier)
        await interaction.response.send_message(_roll_text(f"1d20{sign}") + f"\nAtributo: {atributo.lower()}")

    @iniciativa.command(name="adicionar", description="Inclui um nome na ordem, do maior resultado para o menor.")
    async def iniciativa_adicionar(interaction: discord.Interaction, nome: str, resultado: int) -> None:
        if not await gate(interaction, "iniciativa"):
            return
        bot.store.add_initiative(str(interaction.guild_id), nome, resultado)
        await interaction.response.send_message(_initiative_text(bot, interaction.guild_id))

    @iniciativa.command(name="proximo", description="Mostra quem age agora e passa a vez.")
    async def iniciativa_proximo(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "iniciativa"):
            return
        current = bot.store.next_initiative(str(interaction.guild_id))
        if current is None:
            await interaction.response.send_message("A iniciativa está vazia.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"Agora: {current['name']} ({current['score']}).\n" + _initiative_text(bot, interaction.guild_id)
        )

    @iniciativa.command(name="lista", description="Mostra a ordem de turno.")
    async def iniciativa_lista(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "iniciativa"):
            return
        await interaction.response.send_message(_initiative_text(bot, interaction.guild_id))

    @iniciativa.command(name="limpar", description="Apaga a ordem de turno deste servidor.")
    async def iniciativa_limpar(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "iniciativa"):
            return
        bot.store.clear_initiative(str(interaction.guild_id))
        await interaction.response.send_message("Iniciativa limpa.")

    @regra.command(name="consultar", description="Busca uma magia ou um monstro na Open5e.")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="magia", value="magia"),
        app_commands.Choice(name="monstro", value="monstro"),
    ])
    async def regra_consultar(interaction: discord.Interaction, tipo: str, nome: str) -> None:
        if not await gate(interaction, "regras"):
            return
        await interaction.response.defer()
        text = await asyncio.to_thread(_open5e, tipo, nome)
        await interaction.followup.send(_clip(text))

    @som.command(name="fundo", description="Toca em repetição um arquivo da pasta de sons.")
    async def som_fundo(interaction: discord.Interaction, arquivo: str) -> None:
        if not await gate(interaction, "ambiente"):
            return
        await _play(interaction, bot, arquivo, loop=True)

    @som.command(name="efeito", description="Toca uma vez um arquivo da pasta de sons, junto do fundo se ele estiver ativo.")
    async def som_efeito(interaction: discord.Interaction, arquivo: str) -> None:
        if not await gate(interaction, "ambiente"):
            return
        await _play(interaction, bot, arquivo, loop=False)

    @som.command(name="parar", description="Para o áudio do bot no canal de voz.")
    async def som_parar(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "ambiente"):
            return
        voice = interaction.guild.voice_client if interaction.guild else None
        if voice is not None:
            voice.stop()
        await interaction.response.send_message("Áudio parado.")

    @som.command(name="lista", description="Lista os arquivos de som disponíveis.")
    async def som_lista(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "ambiente"):
            return
        files = sorted(path.name for path in bot.sounds.glob("*") if path.is_file())
        body = "\n".join(files) if files else "A pasta de sons está vazia."
        await interaction.response.send_message(_clip(f"Pasta: {bot.sounds}\n{body}"), ephemeral=True)

    @bot.tree.command(name="handout", description="Envia imagem, vídeo ou arquivo no canal ou só para um jogador.")
    async def handout(interaction: discord.Interaction, arquivo: discord.Attachment, jogador: discord.Member | None = None) -> None:
        if not await gate(interaction, "handout"):
            return
        if arquivo.size > 8 * 1024 * 1024:
            await interaction.response.send_message("O arquivo passou de 8 MB.", ephemeral=True)
            return
        data = await arquivo.read()
        try:
            filename, media_type, data = prepare_upload(arquivo.filename, arquivo.content_type or "", data)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        outbox = getattr(bot, "foundry_outbox", None)
        if jogador is None and outbox is not None:
            outbox.push(interaction.user.display_name, upload=(filename, media_type, data))
        payload = discord.File(io.BytesIO(data), filename=filename)
        if jogador is None:
            await interaction.response.send_message(file=payload)
            return
        await jogador.send(file=payload)
        await interaction.response.send_message(f"Arquivo enviado no privado de {jogador.display_name}.", ephemeral=True)

    @bot.tree.command(name="nome", description="Gera um nome, uma taverna ou um boato.")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="pessoa", value="pessoa"),
        app_commands.Choice(name="taverna", value="taverna"),
        app_commands.Choice(name="boato", value="boato"),
    ])
    async def nome(interaction: discord.Interaction, tipo: str = "pessoa", quantidade: int = 1) -> None:
        if not await gate(interaction, "nomes"):
            return
        count = min(10, max(1, quantidade))
        lines = [fantasy_name(tipo) for _ in range(count)]
        await interaction.response.send_message("\n".join(lines))

    @sessao.command(name="marcar", description="Marca a próxima sessão e abre os botões de presença.")
    async def sessao_marcar(interaction: discord.Interaction, titulo: str, quando: str) -> None:
        if not await gate(interaction, "agenda"):
            return
        session_id = bot.store.add_session(str(interaction.guild_id), str(interaction.channel_id), titulo, quando)
        view = session_view(bot.store, session_id)
        bot.add_view(view)
        await interaction.response.send_message(
            f"{titulo}\nQuando: {quando}\nEscolha uma opção.",
            view=view,
        )

    @sessao.command(name="lista", description="Lista as sessões marcadas neste servidor.")
    async def sessao_lista(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "agenda"):
            return
        rows = bot.store.sessions(str(interaction.guild_id))
        if not rows:
            await interaction.response.send_message("Nenhuma sessão marcada.", ephemeral=True)
            return
        lines = []
        for row in rows[:10]:
            counts = bot.store.rsvp_counts(int(row["id"]))
            presence = ", ".join(f"{name} {total}" for name, total in counts.items()) or "sem respostas"
            lines.append(f"{row['title']} ({row['when_text']}): {presence}")
        await interaction.response.send_message("\n".join(lines))

    @grupo.command(name="item", description="Soma ou tira uma quantidade de um item do grupo.")
    async def grupo_item(interaction: discord.Interaction, nome: str, quantidade: int) -> None:
        if not await gate(interaction, "inventario"):
            return
        total = bot.store.add_item(str(interaction.guild_id), nome, quantidade)
        await interaction.response.send_message(f"{nome.lower()}: {total}")

    @grupo.command(name="ouro", description="Soma ou tira ouro do grupo.")
    async def grupo_ouro(interaction: discord.Interaction, quantidade: int) -> None:
        if not await gate(interaction, "inventario"):
            return
        total = bot.store.add_item(str(interaction.guild_id), "ouro", quantidade)
        await interaction.response.send_message(f"Ouro: {total}")

    @grupo.command(name="xp", description="Soma ou tira XP do grupo.")
    async def grupo_xp(interaction: discord.Interaction, quantidade: int) -> None:
        if not await gate(interaction, "inventario"):
            return
        total = bot.store.add_item(str(interaction.guild_id), "xp", quantidade)
        await interaction.response.send_message(f"XP: {total}")

    @grupo.command(name="lista", description="Mostra itens, ouro e XP.")
    async def grupo_lista(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "inventario"):
            return
        rows = bot.store.inventory(str(interaction.guild_id))
        body = "\n".join(f"{row['name']}: {row['amount']}" for row in rows) or "O grupo ainda não tem itens."
        await interaction.response.send_message(body)

    @reuniao.command(name="entrar", description="Entra na sua chamada e passa a transcrever quem fala.")
    async def reuniao_entrar(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "reuniao"):
            return
        voice = interaction.user.voice.channel if isinstance(interaction.user, discord.Member) and interaction.user.voice else None
        if voice is None:
            await interaction.response.send_message("Entre em um canal de voz antes de chamar o bot.", ephemeral=True)
            return
        if not _can_manage(interaction):
            await interaction.response.send_message("Só quem administra o servidor liga a escuta da reunião.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            from discord.ext import voice_recv
        except ImportError:
            await interaction.followup.send(
                "Falta o pacote que recebe o áudio da chamada.\n"
                "pip install discord-ext-voice-recv\n"
                f"{_VOICE_RECV}"
            )
            return
        client = interaction.guild.voice_client
        if client is None:
            client = await voice.connect(cls=voice_recv.VoiceRecvClient)
        elif getattr(client, "channel", None) != voice:
            await client.move_to(voice)
        audio = MeetingAudio()
        bot.meetings[interaction.guild_id] = audio
        client.listen(_Sink(audio))
        bot.loop.create_task(_flush_meeting(bot, interaction.guild_id, interaction.channel))
        await interaction.followup.send(
            "A transcrição ao vivo está ligada. O nome de cada pessoa entra em cada fala. "
            "Use /reuniao sair para parar. O áudio é transcrito neste computador com faster-whisper."
        )

    @reuniao.command(name="sair", description="Para a transcrição e sai da chamada.")
    async def reuniao_sair(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "reuniao"):
            return
        bot.meetings.pop(interaction.guild_id, None)
        client = interaction.guild.voice_client if interaction.guild else None
        if client is not None:
            if getattr(client, "is_listening", lambda: False)():
                client.stop_listening()
            await client.disconnect()
        await interaction.response.send_message("Saí da chamada. O texto já gravado continua em /reuniao resumo.")

    @reuniao.command(name="resumo", description="Mostra a transcrição com o nome e o horário de cada fala.")
    async def reuniao_resumo(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "reuniao"):
            return
        rows = bot.store.utterances(str(interaction.guild_id))
        lines = [Utterance(row["speaker"], row["body"], row["when_text"]) for row in rows]
        await interaction.response.send_message(_clip(render_meeting(lines)))

    @reuniao.command(name="limpar", description="Apaga a transcrição guardada deste servidor.")
    async def reuniao_limpar(interaction: discord.Interaction) -> None:
        if not await gate(interaction, "reuniao"):
            return
        if not _can_manage(interaction):
            await interaction.response.send_message("Só quem administra o servidor apaga a transcrição.", ephemeral=True)
            return
        bot.store.clear_utterances(str(interaction.guild_id))
        await interaction.response.send_message("Transcrição apagada deste servidor.")

    @arquivo.command(name="transcrever", description="Transcreve um áudio ou vídeo enviado no comando.")
    async def arquivo_transcrever(interaction: discord.Interaction, audio: discord.Attachment, traduzir: bool = False) -> None:
        if not await gate(interaction, "arquivo"):
            return
        await interaction.response.defer()
        text = await asyncio.to_thread(_transcribe_bytes, bot, audio.filename, await audio.read(), traduzir)
        await interaction.followup.send(_clip(text))

    @arquivo.command(name="ler", description="Gera um áudio do texto com Piper ou espeak-ng, se estiverem instalados.")
    async def arquivo_ler(interaction: discord.Interaction, texto: str) -> None:
        if not await gate(interaction, "arquivo"):
            return
        await interaction.response.defer()
        path, message = await asyncio.to_thread(_speak, texto)
        if path is None:
            await interaction.followup.send(message)
            return
        await interaction.followup.send(message, file=discord.File(path))

    @funcoes.command(name="listar", description="Mostra cada função e se ela está ligada.")
    async def funcoes_listar(interaction: discord.Interaction) -> None:
        lines = [
            f"{'ligada' if row['enabled'] else 'desligada'} | {row['key']} | {row['description']}"
            for row in bot.store.features()
        ]
        await interaction.response.send_message(_clip("\n".join(lines)), ephemeral=True)

    @funcoes.command(name="ativar", description="Liga uma função pelo nome interno.")
    async def funcoes_ativar(interaction: discord.Interaction, nome: str) -> None:
        await _switch(interaction, bot, nome, True)

    @funcoes.command(name="desativar", description="Desliga uma função pelo nome interno.")
    async def funcoes_desativar(interaction: discord.Interaction, nome: str) -> None:
        await _switch(interaction, bot, nome, False)

    @funcoes.command(name="remover", description="Remove uma função adicionada na pasta plugins. As funções originais só desligam.")
    async def funcoes_remover(interaction: discord.Interaction, nome: str) -> None:
        if not _can_manage(interaction):
            await interaction.response.send_message("Só quem administra o servidor remove uma função.", ephemeral=True)
            return
        if bot.store.remove_custom(nome):
            await interaction.response.send_message(
                f"{nome} saiu da lista. Apague o arquivo em {bot.plugins} e reinicie o bot para o comando sumir."
            )
            return
        await interaction.response.send_message(
            "Essa função faz parte do bot. Use /funcoes desativar. Só uma função da pasta plugins pode ser removida.",
            ephemeral=True,
        )

    @funcoes.command(name="adicionar", description="Explica como colocar uma função nova na pasta plugins.")
    async def funcoes_adicionar(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "Crie um arquivo .py em "
            f"{bot.plugins} com FEATURE, DESCRIPTION e def setup(bot). "
            "Reinicie o bot. A função entra desligada até /funcoes ativar. "
            "Documentação dos comandos: https://discordpy.readthedocs.io/en/stable/interactions/api.html",
            ephemeral=True,
        )

    @bot.tree.command(name="atualizar", description="Mostra o estado do Git e, se autorizado, baixa atualizações.")
    async def atualizar(interaction: discord.Interaction) -> None:
        if interaction.user.id != _owner_id():
            await interaction.response.send_message(
                "Só a conta definida em CONGO_DISCORD_OWNER_ID atualiza o programa neste computador.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        allow = os.environ.get("CONGO_DISCORD_ALLOW_UPDATE") == "1"
        text = await asyncio.to_thread(update_report, bot.repo, allow)
        await interaction.followup.send(_clip(text), ephemeral=True)

    for group in (dados, ficha, iniciativa, regra, som, sessao, grupo, reuniao, arquivo, funcoes):
        bot.tree.add_command(group)
    register_vtt(bot)


def _roll_text(expression: str) -> str:
    try:
        result = roll_expression(expression)
    except ValueError as exc:
        return str(exc)
    return f"{result.expression}: {result.total}\n{result.detail}"


def _pair_text(expression: str, high: bool) -> str:
    try:
        first, second = roll_pair(expression)
    except ValueError as exc:
        return str(exc)
    chosen = first if (first.total >= second.total) == high else second
    label = "vantagem" if high else "desvantagem"
    return f"{label}: {chosen.total}\n{first.total} e {second.total}"


def _initiative_text(bot: CongoBot, guild_id: int | None) -> str:
    rows = bot.store.initiative(str(guild_id))
    if not rows:
        return "A iniciativa está vazia."
    return "\n".join(f"{index + 1}. {row['name']} ({row['score']})" for index, row in enumerate(rows))


def _sound_path(folder: Path, name: str) -> Path | None:
    candidate = (folder / Path(name).name).resolve()
    if candidate.parent != folder.resolve() or not candidate.is_file():
        return None
    return candidate


async def _play(interaction: discord.Interaction, bot: CongoBot, name: str, loop: bool) -> None:
    path = _sound_path(bot.sounds, name)
    if path is None:
        await interaction.response.send_message(
            f"Não achei esse arquivo em {bot.sounds}. Use /som lista.",
            ephemeral=True,
        )
        return
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    channel = member.voice.channel if member and member.voice else None
    if channel is None:
        await interaction.response.send_message("Entre em um canal de voz antes.", ephemeral=True)
        return
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice is None:
        voice = await channel.connect()
    try:
        if loop:
            if voice.is_playing():
                voice.stop()
            voice.play(discord.FFmpegPCMAudio(str(path), before_options="-stream_loop -1"))
            voice._congo_sound = path
        else:
            effect = discord.FFmpegPCMAudio(str(path))
            background = getattr(voice, "_congo_sound", None)
            if voice.is_playing():
                voice.stop()
            if isinstance(background, Path) and background.is_file():
                from congo_discord.presentation.mix import LayeredSource

                voice.play(
                    LayeredSource(
                        discord.FFmpegPCMAudio(str(background), before_options="-stream_loop -1"),
                        effect,
                    )
                )
            else:
                voice.play(effect)
    except Exception as exc:
        await interaction.response.send_message(
            f"Não consegui tocar o áudio. O FFmpeg precisa estar instalado: {_FFMPEG}\n{exc}",
            ephemeral=True,
        )
        return
    note = " O fundo fica em repetição." if loop else ""
    await interaction.response.send_message(f"Tocando {path.name}.{note}")


class _Sink:
    def __init__(self, audio: MeetingAudio):
        self.audio = audio

    def wants_opus(self) -> bool:
        return False

    def write(self, user, data) -> None:
        if user is None:
            return
        speaker = getattr(user, "display_name", None) or str(getattr(user, "id", "desconhecido"))
        pcm = getattr(data, "pcm", b"")
        self.audio.add(speaker, pcm)

    def cleanup(self) -> None:
        return None


async def _flush_meeting(bot: CongoBot, guild_id: int, channel) -> None:
    while guild_id in bot.meetings:
        await asyncio.sleep(5)
        audio = bot.meetings.get(guild_id)
        if audio is None:
            return
        for speaker, wav in audio.flush():
            text = await asyncio.to_thread(_transcribe_wav_bytes, bot, wav)
            if not text.strip():
                continue
            bot.store.add_utterance(str(guild_id), speaker, text.strip(), _now())
            if channel is not None:
                await channel.send(_clip(f"[{_now()}] {speaker}: {text.strip()}"))


def _transcribe_wav_bytes(bot: CongoBot, wav: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        handle.write(wav)
        name = handle.name
    try:
        return _transcribe_path(bot, Path(name))
    finally:
        Path(name).unlink(missing_ok=True)


def _transcribe_bytes(bot: CongoBot, filename: str, payload: bytes, translate: bool = False) -> str:
    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(payload)
        name = handle.name
    try:
        return _transcribe_path(bot, Path(name), translate)
    finally:
        Path(name).unlink(missing_ok=True)


def _transcribe_path(bot: CongoBot, path: Path, translate: bool = False) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return f"O faster-whisper não está instalado. pip install faster-whisper\n{_WHISPER}"
    if bot._whisper is None:
        bot._whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _info = bot._whisper.transcribe(str(path), task="translate" if translate else "transcribe")
    return " ".join(segment.text.strip() for segment in segments) or "Não encontrei fala nesse trecho."


def _speak(text: str) -> tuple[str | None, str]:
    import shutil
    import subprocess

    binary = shutil.which("espeak-ng")
    if binary is None:
        return None, (
            "Este bot não usa a janela do computador nem o aplicativo de celular. "
            "Para ler texto aqui, instale o espeak-ng neste computador: sudo apt install espeak-ng. "
            "https://github.com/espeak-ng/espeak-ng"
        )
    folder = Path(tempfile.mkdtemp())
    target = folder / "leitura.wav"
    completed = subprocess.run(
        [binary, "-w", str(target), "--stdin"],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 or not target.is_file():
        detail = completed.stderr.strip() or "o espeak-ng não gerou o arquivo."
        return None, detail
    return str(target), "Áudio gerado com espeak-ng, neste bot."


def _open5e(kind: str, name: str) -> str:
    import json
    from urllib.parse import quote
    from urllib.request import urlopen

    slug = "spells" if kind == "magia" else "monsters"
    query = quote(name)
    for url in (
        f"https://api.open5e.com/v2/{slug}/?search={query}",
        f"https://api.open5e.com/{slug}/?search={query}&limit=1",
    ):
        try:
            with urlopen(url, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            continue
        text = spell_text(payload)
        if not text.startswith("Nenhum resultado"):
            return text + f"\n{_OPEN5E}"
    return f"A consulta não respondeu ou não achou esse nome. Busca manual: {_OPEN5E}"


async def _switch(interaction: discord.Interaction, bot: CongoBot, name: str, enabled: bool) -> None:
    if not _can_manage(interaction):
        await interaction.response.send_message("Só quem administra o servidor liga ou desliga funções.", ephemeral=True)
        return
    if not bot.store.set_enabled(name.strip(), enabled):
        await interaction.response.send_message("Não achei essa função. Use /funcoes listar.", ephemeral=True)
        return
    state = "ligada" if enabled else "desligada"
    await interaction.response.send_message(f"{name.strip()} {state}.")


def main() -> None:
    load_env_file(Path(__file__).resolve().parents[3] / ".env")
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Falta DISCORD_TOKEN. Abra o arquivo .env desta pasta, cole o token e rode de novo. "
            f"Crie o aplicativo em {_DISCORD_APP}. Nunca grave o token no repositório."
        )
    repo = Path(__file__).resolve().parents[4]
    data = Path(os.environ.get("CONGO_DISCORD_DATA", Path.home() / ".local" / "share" / "congo-grey-parrot-discord"))
    sounds = data / "sons"
    sounds.mkdir(parents=True, exist_ok=True)
    from congo_discord.persistence.store import Store

    store = Store(data / "bot.sqlite3")
    plugins = Path(__file__).resolve().parents[3] / "plugins"
    CongoBot(store, repo, sounds, plugins).run(token)
