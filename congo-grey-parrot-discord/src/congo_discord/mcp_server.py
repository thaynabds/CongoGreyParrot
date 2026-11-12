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
from congo_discord.service import control
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
/conector mostra o AI Conector: como ligar uma IA ao bot por MCP (só para a dona do bot).
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
    @user_errors(ValueError, TypeError)
    def enviar_mensagem(canal_id: str, texto: str, confirmar: bool = False) -> str:
        """Publica uma mensagem num canal de texto pelo bot. Só envia com confirmar=true, depois de mostrar o texto à pessoa."""
        channel = _snowflake(canal_id, "canal_id")
        body = texto.strip()
        if not body:
            return "Escreva o texto da mensagem."
        if confirmar is not True:
            return "Nada foi enviado. Mostre o texto à pessoa e chame de novo com confirmar=true."
        ok, reply = control.call("enviar_mensagem", {"canal_id": channel, "texto": body[:1800]})
        if ok:
            return reply
        return _rest_send(channel, body) if "não está ligado" in reply and _bot_running() else reply

    # Ações ao vivo: precisam do bot ligado --------------------------------

    @server.tool()
    @user_errors(ValueError)
    def listar_servidores() -> str:
        """Servidores, canais de texto e de voz que o bot enxerga, com os ids. Precisa do bot ligado."""
        return _live("servidores", {})

    @server.tool()
    @user_errors(ValueError, TypeError)
    def tocar_som(canal_voz_id: str, arquivo: str, repetir: bool = False) -> str:
        """Entra no canal de voz e toca um arquivo da pasta de sons (use listar_sons). repetir=true deixa como fundo."""
        args = {"canal_voz_id": _snowflake(canal_voz_id, "canal_voz_id"), "arquivo": Path(arquivo).name, "repetir": bool(repetir)}
        return _live("tocar_som", args)

    @server.tool()
    @user_errors(ValueError, TypeError)
    def parar_som(servidor_id: str) -> str:
        """Para o áudio do bot no servidor."""
        return _live("parar_som", {"servidor_id": _snowflake(servidor_id, "servidor_id")})

    @server.tool()
    @user_errors(ValueError, TypeError)
    def sair_voz(servidor_id: str) -> str:
        """Tira o bot do canal de voz e para a transcrição ao vivo, se estiver ligada."""
        return _live("sair_voz", {"servidor_id": _snowflake(servidor_id, "servidor_id")})

    @server.tool()
    @user_errors(ValueError, TypeError)
    def marcar_sessao(canal_id: str, titulo: str, quando: str, confirmar: bool = False) -> str:
        """Publica a próxima sessão no canal, com botões de presença. Só publica com confirmar=true."""
        if confirmar is not True:
            return "Nada foi publicado. Confirme com a pessoa e chame de novo com confirmar=true."
        args = {"canal_id": _snowflake(canal_id, "canal_id"), "titulo": titulo.strip()[:200], "quando": quando.strip()[:200]}
        return _live("marcar_sessao", args)

    @server.tool()
    @user_errors(ValueError, TypeError)
    def reuniao_entrar(canal_voz_id: str, canal_texto_id: str = "", confirmar: bool = False) -> str:
        """Liga a transcrição ao vivo de uma chamada (grava o que as pessoas falam). Só liga com confirmar=true, e avisa no canal de texto."""
        if confirmar is not True:
            return "Nada foi ligado. Transcrever uma chamada grava a fala das pessoas: confirme com a pessoa e chame com confirmar=true."
        args = {"canal_voz_id": _snowflake(canal_voz_id, "canal_voz_id")}
        if canal_texto_id.strip():
            args["canal_texto_id"] = _snowflake(canal_texto_id, "canal_texto_id")
        return _live("reuniao_entrar", args)

    # Mesa: funciona com o bot ligado ou desligado ---------------------------

    @server.tool()
    @user_errors(ValueError, TypeError)
    def rolar_dados(expressao: str, modo: str = "normal") -> str:
        """Rola dados, por exemplo 1d20+5 ou 2d6+1d4. modo: normal, vantagem ou desvantagem."""
        from congo_discord.domain.dice import roll_expression, roll_pair

        _need("dados")
        if modo not in {"normal", "vantagem", "desvantagem"}:
            raise ValueError("Use modo normal, vantagem ou desvantagem.")
        if modo == "normal":
            result = roll_expression(expressao[:200])
            return f"{result.expression}: {result.total}\n{result.detail}"
        first, second = roll_pair(expressao[:200])
        high = modo == "vantagem"
        chosen = first if (first.total >= second.total) == high else second
        return f"{modo}: {chosen.total}\n{first.total} e {second.total}"

    @server.tool()
    @user_errors(ValueError, TypeError)
    def rolar_percentil(pericia: int) -> str:
        """Rola 1d100 contra uma perícia de 1 a 100."""
        from congo_discord.domain.dice import roll_percent

        _need("dados")
        result = roll_percent(int(pericia))
        return f"{result.expression}: {result.total}. {result.detail}."

    @server.tool()
    @user_errors(ValueError, TypeError)
    def rolar_pool(quantidade: int, faces: int = 10, limite: int = 6) -> str:
        """Rola um grupo de dados e conta quantos atingiram o limite."""
        from congo_discord.domain.dice import roll_pool

        _need("dados")
        result = roll_pool(int(quantidade), int(faces), int(limite))
        return f"Sucessos: {result.total}. Dados: {result.detail}."

    @server.tool()
    @user_errors(ValueError, TypeError)
    def gerar_nome(tipo: str = "pessoa", quantidade: int = 1) -> str:
        """Gera nomes de pessoa, de taverna ou boatos para a mesa."""
        from congo_discord.domain.names import fantasy_name

        _need("nomes")
        if tipo not in {"pessoa", "taverna", "boato"}:
            raise ValueError("Use tipo pessoa, taverna ou boato.")
        return "\n".join(fantasy_name(tipo) for _ in range(max(1, min(int(quantidade), 10))))

    @server.tool()
    @user_errors(ValueError, TypeError)
    def consultar_regra(tipo: str, nome: str) -> str:
        """Busca uma magia ou um monstro na Open5e (só leitura, com a fonte)."""
        from congo_discord.domain.rules import spell_text

        _need("regras")
        if tipo not in {"magia", "monstro"}:
            raise ValueError("Use tipo magia ou monstro.")
        return _open5e(tipo, nome.strip()[:100], spell_text)

    @server.tool()
    @user_errors(ValueError, TypeError)
    def ficha_ver(servidor_id: str, jogador_id: str) -> str:
        """Mostra os atributos guardados de um jogador naquele servidor."""
        _need("fichas")
        rows = _with_store(lambda store: store.sheet(_snowflake(servidor_id, "servidor_id"), _snowflake(jogador_id, "jogador_id")))
        return "\n".join(f"{row['attribute']}: {int(row['modifier']):+d}" for row in rows) or "Esse jogador ainda não tem atributos."

    @server.tool()
    @user_errors(ValueError, TypeError)
    def ficha_definir(servidor_id: str, jogador_id: str, atributo: str, modificador: int) -> str:
        """Guarda o modificador de um atributo na ficha de um jogador, por exemplo percepcao 3."""
        _need("fichas")
        name = atributo.strip().lower()[:40]
        if not name:
            raise ValueError("Informe o atributo.")
        value = max(-100, min(int(modificador), 100))
        _with_store(lambda store: store.set_attribute(_snowflake(servidor_id, "servidor_id"), _snowflake(jogador_id, "jogador_id"), name, value))
        return f"{name}: {value:+d}"

    @server.tool()
    @user_errors(ValueError, TypeError)
    def iniciativa(servidor_id: str, acao: str = "lista", nome: str = "", resultado: int = 0, confirmar: bool = False) -> str:
        """Ordem de turno. acao: lista, adicionar (nome e resultado), proximo ou limpar (com confirmar=true)."""
        _need("iniciativa")
        guild = _snowflake(servidor_id, "servidor_id")

        def run(store):
            if acao == "adicionar":
                if not nome.strip():
                    raise ValueError("Informe o nome.")
                store.add_initiative(guild, nome.strip()[:80], int(resultado))
            elif acao == "proximo":
                current = store.next_initiative(guild)
                if current is None:
                    return "A iniciativa está vazia."
                return f"Agora: {current['name']} ({current['score']})."
            elif acao == "limpar":
                if confirmar is not True:
                    return "Nada foi apagado. Confirme com a pessoa e chame com confirmar=true."
                store.clear_initiative(guild)
                return "Iniciativa limpa."
            elif acao != "lista":
                raise ValueError("Use acao lista, adicionar, proximo ou limpar.")
            rows = store.initiative(guild)
            return "\n".join(f"{index + 1}. {row['name']} ({row['score']})" for index, row in enumerate(rows)) or "A iniciativa está vazia."

        return _with_store(run)

    @server.tool()
    @user_errors(ValueError, TypeError)
    def grupo(servidor_id: str, item: str = "", quantidade: int = 0) -> str:
        """Inventário do grupo. Sem item, lista tudo. Com item (ou ouro, ou xp), soma ou tira a quantidade."""
        _need("inventario")
        guild = _snowflake(servidor_id, "servidor_id")

        def run(store):
            if item.strip():
                total = store.add_item(guild, item.strip()[:80], max(-10**9, min(int(quantidade), 10**9)))
                return f"{item.strip().lower()}: {total}"
            rows = store.inventory(guild)
            return "\n".join(f"{row['name']}: {row['amount']}" for row in rows) or "O grupo ainda não tem itens."

        return _with_store(run)

    @server.tool()
    @user_errors(ValueError, TypeError)
    def sessoes(servidor_id: str) -> str:
        """Lista as sessões marcadas e as presenças confirmadas."""
        _need("agenda")

        def run(store):
            lines = []
            for row in store.sessions(_snowflake(servidor_id, "servidor_id"))[:20]:
                counts = store.rsvp_counts(int(row["id"]))
                presence = ", ".join(f"{name} {total}" for name, total in counts.items()) or "sem respostas"
                lines.append(f"{row['title']} ({row['when_text']}): {presence}")
            return "\n".join(lines) or "Nenhuma sessão marcada."

        return _with_store(run)

    @server.tool()
    @user_errors(ValueError, TypeError)
    def reuniao(servidor_id: str, acao: str = "transcricao", frases: int = 0, confirmar: bool = False) -> str:
        """Reunião gravada pelo bot. acao: transcricao, resumo ou limpar (com confirmar=true)."""
        from congo_discord.domain.summary import Utterance, render_meeting, summarize_meeting

        _need("reuniao")
        guild = _snowflake(servidor_id, "servidor_id")
        if acao == "limpar":
            if confirmar is not True:
                return "Nada foi apagado. Confirme com a pessoa e chame com confirmar=true."
            _with_store(lambda store: store.clear_utterances(guild))
            return "Transcrição apagada deste servidor."
        rows = _with_store(lambda store: store.utterances(guild))
        lines = [Utterance(row["speaker"], row["body"], row["when_text"]) for row in rows]
        if acao == "resumo":
            return summarize_meeting(lines, max(0, min(int(frases), 30)))
        if acao != "transcricao":
            raise ValueError("Use acao transcricao, resumo ou limpar.")
        return render_meeting(lines)

    @server.tool()
    @user_errors(ValueError, TypeError)
    def ligar_funcao(nome: str, ligada: bool = True) -> str:
        """Liga (ligada=true) ou desliga uma função do bot pelo nome de listar_funcoes."""
        key = nome.strip()
        changed = _with_store(lambda store: store.set_enabled(key, bool(ligada)))
        if not changed:
            raise ValueError("Não achei essa função. Use listar_funcoes.")
        return f"{key} {'ligada' if ligada else 'desligada'}."

    @server.tool()
    def listar_sons() -> str:
        """Arquivos da pasta de sons do bot, para tocar_som."""
        folder = _data_dir() / "sons"
        files = sorted(item.name for item in folder.glob("*") if item.is_file()) if folder.is_dir() else []
        return f"Pasta: {folder}\n" + ("\n".join(files) or "Nenhum arquivo. Coloque MP3, OGG ou WAV nessa pasta.")

    return server


def _data_dir() -> Path:
    return Path(os.environ.get("CONGO_DISCORD_DATA", Path.home() / ".local" / "share" / "congo-grey-parrot-discord"))


def _with_store(function):
    from congo_discord.persistence.store import Store

    store = Store(_data_dir() / "bot.sqlite3")
    try:
        return function(store)
    finally:
        store.close()


def _need(feature: str) -> None:
    if not _with_store(lambda store: store.enabled(feature)):
        raise ValueError(f"A função {feature} está desativada. Use ligar_funcao para ligar.")


def _snowflake(raw, label: str) -> str:
    value = str(raw).strip()
    if not value.isdigit() or not 15 <= len(value) <= 20:
        raise ValueError(f"Informe {label} com o número do Discord (use listar_servidores).")
    return value


def _live(action: str, args: dict) -> str:
    ok, reply = control.call(action, args)
    if not ok:
        raise ValueError(reply)
    return reply


def _open5e(kind: str, name: str, spell_text) -> str:
    from urllib.parse import quote

    slug = "spells" if kind == "magia" else "monsters"
    for url in (
        f"https://api.open5e.com/v2/{slug}/?search={quote(name)}",
        f"https://api.open5e.com/{slug}/?search={quote(name)}&limit=1",
    ):
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                payload = json.loads(response.read(2_000_000).decode("utf-8"))
        except Exception:
            continue
        text = spell_text(payload)
        if not text.startswith("Nenhum resultado"):
            return text + "\nFonte: https://open5e.com"
    return "A consulta não respondeu ou não achou esse nome. Busca manual: https://open5e.com"


def _rest_send(channel: str, body: str) -> str:
    """Plano B para um bot antigo, sem o canal local: envia pela API com o token do .env."""
    token = _bot_token()
    if token is None:
        return "O arquivo .env não tem DISCORD_TOKEN. Rode o instalador de novo."
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
    return f"Mensagem enviada (id {data.get('id', '')})."


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
