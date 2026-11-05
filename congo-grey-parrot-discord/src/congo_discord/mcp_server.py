from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from congo_discord.persistence.store import CORE_FEATURES
from congo_discord.service.envfile import load_env_file
from congo_discord.service.invite import PERMISSIONS, invite_url

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "mcp") not in sys.path:
    sys.path.insert(0, str(_REPO / "mcp"))

from runtime import make_server, serve, user_errors  # noqa: E402

_ENV = Path(__file__).resolve().parents[2] / ".env"
_UNIT = "congo-discord.service"
# Token de bot do Discord: três partes em base64 separadas por ponto.
_SECRET = re.compile(r"[\w-]{23,28}\.[\w-]{6,7}\.[\w-]{27,40}|(?i:bot)\s+[\w.-]{40,}")

SLASH_HELP = """
Comandos digitados no Discord, não no terminal.
/dados rolar, vantagem, desvantagem, percentil, pool, oculto.
/ficha definir, ver, rolar.
/iniciativa adicionar, proximo, lista, limpar.
/regra consultar.
/som fundo, efeito, parar, lista.
/handout envia imagem, vídeo ou arquivo de até 8 MB no canal ou no privado. No canal, também entra no Foundry se o módulo estiver ativo.
/nome gera pessoa, taverna ou boato.
/sessao marcar, lista.
/grupo item, ouro, xp, lista.
/reuniao entrar, sair, transcricao, resumo, limpar.
/arquivo transcrever, resumir, ler.
/funcoes listar, ativar, desativar, remover, adicionar.
/vtt catalogo, conectar, atual, testar, enviar, desconectar.
/atualizar mostra o Git.
/navegador ligar, desligar, status, canal, token, falar, arquivo, modulo, userscript.
/eco e /musica existem quando o arquivo da pasta plugins está no lugar.
""".strip()


def build_server():
    server = make_server("Congo Grey Parrot Discord")

    @server.tool()
    def status_bot() -> str:
        """Diz se o bot está ligado, se o .env existe e se o token está preenchido, sem mostrar o token."""
        running = "ligado" if _bot_running() else "desligado"
        if not _ENV.is_file():
            return f"Bot {running}. Arquivo .env não existe. Rode ./instalar.sh na pasta do bot."
        token = "preenchido" if _bot_token() else "vazio: cole o token do Developer Portal no .env"
        service = _service_state()
        return f"Bot {running}. Arquivo .env existe. DISCORD_TOKEN {token}. Serviço systemd: {service}."

    @server.tool()
    @user_errors(ValueError, TypeError)
    def ver_log(linhas: int = 50) -> str:
        """Últimas linhas do log do serviço do bot (systemd do usuário), com tokens apagados. De 1 a 200 linhas."""
        count = max(1, min(int(linhas), 200))
        journal = shutil.which("journalctl")
        if not journal:
            return "Este computador não tem journalctl. O log aparece no terminal onde o bot foi aberto."
        try:
            result = subprocess.run(
                [journal, "--user", "-u", _UNIT, "-n", str(count), "--no-pager", "-o", "cat"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return "Não consegui ler o log agora."
        text = redact(result.stdout.strip())
        if not text:
            return "Sem log do serviço. Ou o bot roda pelo terminal, ou ./servico.sh instalar ainda não foi usado."
        return text

    @server.tool()
    @user_errors(ValueError)
    def link_convite(id_aplicacao: str, id_servidor: str = "") -> str:
        """Monta o convite OAuth2 do bot com as permissões mínimas. Quem administra o servidor abre o link e autoriza."""
        url = invite_url(id_aplicacao, id_servidor)
        names = ", ".join(PERMISSIONS)
        return f"{url}\nPermissões pedidas: {names}. Sem Administrador."

    @server.tool()
    def listar_funcoes() -> str:
        """Lista os nomes das funções que o código do bot conhece e se começam ligadas."""
        lines = []
        for key, description in CORE_FEATURES.items():
            initial = "desligada" if key == "reuniao" else "ligada"
            lines.append(f"{key}: {description} Começa {initial}.")
        return "\n".join(lines)

    @server.tool()
    def ajuda_comandos() -> str:
        """Texto de ajuda dos comandos com barra. Não chama o Discord."""
        return SLASH_HELP

    @server.tool()
    def enviar_comando(canal_id: str, texto: str) -> str:
        """Envia uma mensagem no canal só se o bot já estiver ligado, com o token guardado no .env."""
        if not _bot_running():
            return "O bot não está ligado. Abra o atalho do Discord e deixe a janela aberta."
        token = _bot_token()
        if token is None:
            return "O arquivo .env não tem DISCORD_TOKEN. Rode o instalador de novo."
        channel = canal_id.strip()
        if not channel.isdigit():
            return "Informe o número do canal, não o nome."
        body = texto.strip()
        if not body:
            return "Escreva o texto da mensagem."
        # Um texto vindo de um modelo de IA não pode chamar @everyone nem cargos.
        payload = json.dumps({"content": body[:1800], "allowed_mentions": {"parse": []}}).encode("utf-8")
        request = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel}/messages",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
                "User-Agent": "CongoGreyParrotMCP (https://github.com/thaynabds/CongoGreyParrot)",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return f"O Discord recusou a mensagem. Código {exc.code}."
        except urllib.error.URLError:
            return "Não consegui falar com o Discord agora."
        message_id = data.get("id", "")
        return f"Mensagem enviada como o bot. id {message_id}"

    return server


def _bot_running() -> bool:
    proc = Path("/proc")
    if not proc.is_dir():
        return False
    me = os.getpid()
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == me:
            continue
        try:
            command = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        if "mcp_server" in command or "congo-discord-mcp" in command:
            continue
        if "congo-discord" in command or "congo_discord" in command:
            return True
    return False


def redact(text: str) -> str:
    return _SECRET.sub("[segredo apagado]", text)


def _service_state() -> str:
    systemctl = shutil.which("systemctl")
    if not systemctl:
        return "indisponível"
    try:
        result = subprocess.run(
            [systemctl, "--user", "is-active", _UNIT],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=_user_bus_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return "indisponível"
    state = result.stdout.strip() or "desconhecido"
    return "não instalado" if state in {"inactive", "unknown"} and not _unit_file().is_file() else state


def _user_bus_env() -> dict[str, str]:
    """O cliente MCP abre o servidor com ambiente mínimo, sem XDG_RUNTIME_DIR, e o systemctl --user não acha o barramento."""
    env = dict(os.environ)
    if not env.get("XDG_RUNTIME_DIR") and hasattr(os, "getuid"):
        runtime = Path(f"/run/user/{os.getuid()}")
        if runtime.is_dir():
            env["XDG_RUNTIME_DIR"] = str(runtime)
    return env


def _unit_file() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "systemd" / "user" / _UNIT


def _bot_token() -> str | None:
    load_env_file(_ENV)
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        return None
    return token


def main() -> None:
    serve(build_server(), default_port=8767)


if __name__ == "__main__":
    main()
