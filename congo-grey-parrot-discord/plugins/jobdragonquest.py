"""Plugin do JobDragonQuest para o bot de Discord do Congo Grey Parrot.

Entrega os avisos do JobDragonQuest por mensagem direta (mesmo com o painel fechado) e responde a /jobdragonquest resumo,
/jobdragonquest avisos e /jobdragonquest pendencias só na conversa privada com o bot e só para a dona configurada.

Instalação: scripts/conectar-congo.sh no repositório do JobDragonQuest. Depois, no Discord: /funcoes ativar jobdragonquest.
Configuração em ~/.config/jobdragonquest/congo.env (permissão 600), nunca no código:

    JOBDRAGONQUEST_API_URL=http://127.0.0.1:8080
    JOBDRAGONQUEST_TOKEN=jdq_...            (token pessoal criado em Configurações no painel)
    JOBDRAGONQUEST_DISCORD_USER_ID=123...   (seu id de usuário no Discord)
    JOBDRAGONQUEST_POLL_SECONDS=60
"""

from __future__ import annotations

import json
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, NamedTuple

FEATURE = "jobdragonquest"
DESCRIPTION = "Liga o JobDragonQuest: avisos por mensagem direta e /jobdragonquest resumo, avisos e pendencias (só para a dona)."

CONFIG_PATH = Path(os.environ.get("JOBDRAGONQUEST_CONGO_CONFIG", str(Path.home() / ".config" / "jobdragonquest" / "congo.env")))
SENT_PATH = CONFIG_PATH.with_name("congo-enviados.json")
MAX_RESPONSE = 1024 * 1024
MAX_MESSAGE = 1800
MAX_REMEMBERED = 500
TOKEN = re.compile(r"^jdq_[A-Za-z0-9_-]{43}$")
DISCORD_ID = re.compile(r"^\d{17,20}$")
LOOPBACK = {"127.0.0.1", "localhost", "::1"}


class ConfigError(Exception):
    """Configuração ausente ou insegura. A mensagem nunca traz o token."""


class Config(NamedTuple):
    """Imutável. NamedTuple em vez de dataclass: o Congo carrega plugins sem registrar o módulo em sys.modules."""

    api_url: str
    token: str
    owner_id: int
    poll_seconds: int


def load_config(path: Path = CONFIG_PATH) -> Config:
    if not path.is_file():
        raise ConfigError(f"configuração não encontrada em {path}: rode scripts/conectar-congo.sh no JobDragonQuest")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ConfigError(f"{path} pode ser lido por outras contas (permissão {oct(mode)}): use chmod 600")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    api_url = validate_url(values.get("JOBDRAGONQUEST_API_URL", "http://127.0.0.1:8080"))
    token = values.get("JOBDRAGONQUEST_TOKEN", "")
    if not TOKEN.match(token):
        raise ConfigError("JOBDRAGONQUEST_TOKEN ausente ou em formato inválido")
    owner = values.get("JOBDRAGONQUEST_DISCORD_USER_ID", "")
    if not DISCORD_ID.match(owner):
        raise ConfigError("JOBDRAGONQUEST_DISCORD_USER_ID precisa ser o número do seu usuário no Discord")
    try:
        poll = max(30, min(3600, int(values.get("JOBDRAGONQUEST_POLL_SECONDS", "60"))))
    except ValueError:
        poll = 60
    return Config(api_url, token, int(owner), poll)


def validate_url(raw: str) -> str:
    """Só a própria máquina por HTTP, ou HTTPS. Sem usuário, senha, query ou fragmento."""
    parsed = urllib.parse.urlsplit(raw.strip())
    if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.hostname:
        raise ConfigError("JOBDRAGONQUEST_API_URL inválida")
    local = parsed.scheme == "http" and parsed.hostname in LOOPBACK
    if not local and parsed.scheme != "https":
        raise ConfigError("JOBDRAGONQUEST_API_URL precisa ser http://127.0.0.1 ou HTTPS")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class JobDragonQuestApi:
    """Cliente mínimo da API. Caminhos fixos, sem redirecionamento, com tempo e tamanho limitados."""

    def __init__(self, config: Config, opener: urllib.request.OpenerDirector | None = None):
        self._config = config
        self._opener = opener or urllib.request.build_opener(_NoRedirect)

    def request(self, method: str, path: str, body: object | None = None) -> object:
        if not path.startswith("/api/v1/"):
            raise ValueError("caminho de API inválido")
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self._config.api_url + path,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._config.token}",
                "Accept": "application/json",
                **({"Content-Type": "application/json"} if data is not None else {}),
            },
        )
        try:
            with self._opener.open(request, timeout=15) as response:
                raw = response.read(MAX_RESPONSE + 1)
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise ApiError(401, "token do JobDragonQuest inválido, vencido ou revogado") from None
            raise ApiError(exc.code, f"o JobDragonQuest respondeu {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ApiError(0, "não consegui falar com o JobDragonQuest; ele está ligado?") from None
        if len(raw) > MAX_RESPONSE:
            raise ApiError(0, "resposta grande demais")
        return json.loads(raw.decode("utf-8")) if raw else None


def clip(text: str, limit: int = MAX_MESSAGE) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def notification_text(item: dict, hide_details: bool) -> str:
    """Mensagem do aviso. Com "esconder detalhes", não cita empresa, cargo nem texto vindo de fora."""
    if hide_details:
        return "JobDragonQuest: você tem um aviso novo. Abra o painel para ver."
    priority = {"HIGH": "Importante", "MEDIUM": "Aviso", "LOW": "Aviso"}.get(str(item.get("priority")), "Aviso")
    return clip(f"JobDragonQuest · {priority}: {item.get('message', '')}")


def summary_text(summary: dict) -> str:
    fields = [
        ("Vagas encontradas", "jobsFound"),
        ("Candidaturas", "applicationsTotal"),
        ("Em andamento", "inProgress"),
        ("Entrevistas", "interviewsScheduled"),
        ("Testes pendentes", "testsPending"),
        ("Propostas", "offers"),
        ("Sem atualização", "stale"),
        ("Pendências", "pendingItems"),
        ("Fontes a conferir", "sourcesToCheck"),
    ]
    return "JobDragonQuest\n" + "\n".join(f"{label}: {int(summary.get(key, 0) or 0)}" for label, key in fields)


def list_text(title: str, items: list, line: Callable[[dict], str], empty: str) -> str:
    if not items:
        return f"{title}\n{empty}"
    return clip(f"{title}\n" + "\n".join(f"• {line(item)}" for item in items[:15]))


class SentLog:
    """Avisos já enviados por DM e a hora em que o plugin começou (arquivo 600 ao lado da configuração).

    A hora de início evita despejar avisos antigos na primeira vez em que o plugin roda.
    """

    def __init__(self, path: Path = SENT_PATH):
        self._path = path
        self.since: datetime | None = None
        self._ids: list[str] = []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(data, list):  # formato antigo: só a lista de ids
            self._ids = [str(value) for value in data if isinstance(value, str)][-MAX_REMEMBERED:]
        elif isinstance(data, dict):
            self._ids = [str(value) for value in data.get("ids", []) if isinstance(value, str)][-MAX_REMEMBERED:]
            self.since = parse_instant(data.get("since"))

    def __contains__(self, item_id: str) -> bool:
        return item_id in self._ids

    def start(self, now: datetime) -> None:
        self.since = now
        self._save()

    def add(self, item_id: str) -> None:
        self._ids = (self._ids + [item_id])[-MAX_REMEMBERED:]
        self._save()

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump({"since": self.since.isoformat() if self.since else None, "ids": self._ids}, handle)
        except OSError:
            pass


def parse_instant(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def pending_dms(api: JobDragonQuestApi, sent: SentLog, now: datetime | None = None) -> list[tuple[str, str]]:
    """Avisos a mandar por DM: canal "sistema" ligado, ainda não lidos, não adiados e não enviados.

    Lê os avisos recentes da conta (não só a fila de entrega): com o painel aberto, o aviso vira "entregue" em
    segundos, mas a pessoa ainda deve recebê-lo no Discord. Na primeira execução só marca a hora de início.
    """
    now = now or datetime.now(timezone.utc)
    if sent.since is None:
        sent.start(now)
        return []
    data = api.request("GET", "/api/v1/notifications?size=30") or {}
    items = data.get("items", []) if isinstance(data, dict) else []
    view = api.request("GET", "/api/v1/notifications/preferences") or {}
    hide = bool((view.get("settings") or {}).get("hideDetails")) if isinstance(view, dict) else True
    out: list[tuple[str, str]] = []
    for item in reversed(items):  # do mais antigo para o mais novo
        item_id = str(item.get("id", ""))
        created = parse_instant(item.get("createdAt"))
        snoozed = parse_instant(item.get("snoozedUntil"))
        if (not item_id or not item.get("system") or item.get("readAt") or item_id in sent
                or created is None or created < sent.since or (snoozed is not None and snoozed > now)):
            continue
        out.append((item_id, notification_text(item, hide)))
    return out


def setup(bot) -> None:  # pragma: no cover - depende do discord.py e de um bot conectado
    import asyncio
    import logging

    import discord
    from discord import app_commands

    log = logging.getLogger("congo.jobdragonquest")
    try:
        config = load_config()
    except ConfigError as exc:
        log.warning("Plugin JobDragonQuest sem configuração: %s", exc)
        config = None

    # Só na conversa privada com o bot: o comando não aparece nos servidores nem em grupos.
    group = app_commands.Group(
        name="jobdragonquest",
        description="Seu JobDragonQuest: resumo, avisos e pendências (privado)",
        allowed_contexts=app_commands.AppCommandContext(guild=False, dm_channel=True, private_channel=False),
    )
    none = discord.AllowedMentions.none()

    async def answer(interaction: discord.Interaction, build: Callable[[JobDragonQuestApi], str]) -> None:
        if not bot.store.enabled(FEATURE):
            await interaction.response.send_message("A função jobdragonquest está desativada. Use /funcoes ativar jobdragonquest.", ephemeral=True)
            return
        if config is None:
            await interaction.response.send_message("O JobDragonQuest ainda não foi configurado: rode scripts/conectar-congo.sh.", ephemeral=True)
            return
        if interaction.user.id != config.owner_id:
            await interaction.response.send_message("Este comando é só para a dona do JobDragonQuest.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            text = await asyncio.to_thread(build, JobDragonQuestApi(config))
        except ApiError as exc:
            text = f"JobDragonQuest: {exc}"
        await interaction.followup.send(clip(text), ephemeral=True, allowed_mentions=none)

    @group.command(name="resumo", description="Contadores do seu JobDragonQuest")
    async def resumo(interaction: discord.Interaction) -> None:
        await answer(interaction, lambda api: summary_text(api.request("GET", "/api/v1/dashboard/summary") or {}))

    @group.command(name="avisos", description="Avisos não lidos do JobDragonQuest")
    async def avisos(interaction: discord.Interaction) -> None:
        def build(api: JobDragonQuestApi) -> str:
            data = api.request("GET", "/api/v1/notifications?unreadOnly=true&size=15") or {}
            return list_text("Avisos não lidos", data.get("items", []), lambda n: str(n.get("message", "")), "Nenhum aviso não lido.")

        await answer(interaction, build)

    @group.command(name="pendencias", description="Pendências que dependem de você")
    async def pendencias(interaction: discord.Interaction) -> None:
        def build(api: JobDragonQuestApi) -> str:
            items = api.request("GET", "/api/v1/dashboard/pending") or []
            return list_text("Pendências", items, lambda p: str(p.get("message", "")), "Nenhuma pendência. Tudo em dia.")

        await answer(interaction, build)

    bot.tree.add_command(group)

    async def deliver_loop() -> None:
        await bot.wait_until_ready()
        sent = SentLog()
        while not bot.is_closed():
            if config is not None and bot.store.enabled(FEATURE):
                try:
                    batch = await asyncio.to_thread(pending_dms, JobDragonQuestApi(config), sent)
                    if batch:
                        owner = await bot.fetch_user(config.owner_id)
                        for item_id, text in batch:
                            await owner.send(text, allowed_mentions=none)
                            sent.add(item_id)
                except ApiError as exc:
                    log.warning("JobDragonQuest: %s", exc)
                except discord.HTTPException as exc:
                    log.warning("JobDragonQuest: o Discord recusou a mensagem direta (código %s)", exc.status)
            await asyncio.sleep(config.poll_seconds if config else 300)

    asyncio.get_running_loop().create_task(deliver_loop())
