from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from congo_discord.persistence.store import CORE_FEATURES
from congo_discord.service.envfile import load_env_file

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "mcp") not in sys.path:
    sys.path.insert(0, str(_REPO / "mcp"))

from runtime import make_server, serve  # noqa: E402

_ENV = Path(__file__).resolve().parents[2] / ".env"

SLASH_HELP = """
Comandos digitados no Discord, não no terminal.
/dados rolar, vantagem, desvantagem, percentil, pool, oculto.
/ficha definir, ver, rolar.
/iniciativa adicionar, proximo, lista, limpar.
/regra consultar.
/som fundo, efeito, parar, lista.
/handout envia uma imagem.
/nome gera pessoa, taverna ou boato.
/sessao marcar, lista.
/grupo item, ouro, xp, lista.
/reuniao entrar, sair, resumo, limpar.
/arquivo transcrever, ler.
/funcoes listar, ativar, desativar, remover, adicionar.
/vtt catalogo, conectar, atual, testar, enviar, desconectar.
/atualizar mostra o Git.
/eco, /musica e /navegador existem quando o arquivo da pasta plugins está no lugar.
""".strip()


def build_server():
    server = make_server("Congo Grey Parrot Discord")

    @server.tool()
    def status_bot() -> str:
        """Diz se o processo do bot está ligado e se o arquivo .env existe, sem ler segredos."""
        running = "ligado" if _bot_running() else "desligado"
        env = "existe" if _ENV.is_file() else "não existe"
        return f"Bot {running}. Arquivo .env {env}."

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
        payload = json.dumps({"content": body[:1800]}).encode("utf-8")
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
