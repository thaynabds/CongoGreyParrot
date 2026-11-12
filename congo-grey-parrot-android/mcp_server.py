"""Ponte MCP do aplicativo Android.

O celular não fala MCP. Este processo roda no computador e conversa com o app pelo
cabo USB (adb): instala, abre e manda pedidos ao AI Conector do app, um provider
que só aceita o usuário shell do adb. O texto vai e volta em base64, então nada do
que a IA escreve vira comando no shell do celular.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_REPO = _ROOT.parent
if str(_REPO / "mcp") not in sys.path:
    sys.path.insert(0, str(_REPO / "mcp"))

from runtime import make_server, serve, user_errors  # noqa: E402

_PACKAGE = "org.congogreyparrot"
_ACTIVITY = f"{_PACKAGE}/.MainActivity"
_URI = f"content://{_PACKAGE}.ai"
_HELP = "https://support.google.com/android/answer/2664792?hl=pt-BR"
_ADB_HELP = "https://developer.android.com/tools/releases/platform-tools"
_SERIAL = re.compile(r"[A-Za-z0-9._:\-]{1,64}")
_FILE_NAME = re.compile(r"[\w.\- ]{1,80}")
MAX_TEXT = 200_000
# O adb shell monta uma linha de comando no celular; base64 de 200 mil caracteres ainda cabe.
MAX_ARG = 300_000


def apk_path() -> Path:
    built = _ROOT / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    published = _ROOT / "CongoGreyParrot-debug.apk"
    if built.is_file():
        return built
    return published


def adb_binary() -> str | None:
    found = shutil.which("adb")
    if found:
        return found
    for base in (os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"), str(Path.home() / "Android" / "Sdk")):
        if base:
            candidate = Path(base) / "platform-tools" / "adb"
            if candidate.is_file():
                return str(candidate)
    return None


def build_server():
    server = make_server("Congo Grey Parrot Android")

    @server.tool()
    def instrucoes_apk() -> str:
        """Explica como instalar o aplicativo e ligar o AI Conector do celular."""
        path = apk_path()
        state = "O arquivo está neste computador." if path.is_file() else "O arquivo do APK ainda não foi gerado."
        return (
            f"{state} Caminho: {path}\n"
            "1. Copie esse arquivo para o Android 8 ou mais novo, ou use instalar_apk com o cabo USB.\n"
            "2. Abra o arquivo no celular. Se o sistema bloquear, permita instalar por esse aplicativo.\n"
            "3. Para a IA usar o app, ligue a Depuração USB nas Opções do desenvolvedor e conecte o cabo.\n"
            f"Ajuda do Google: {_HELP}\nadb: {_ADB_HELP}\n"
            "O app grava áudio, lê texto em voz alta, resume e guarda arquivos. Não abre porta de rede."
        )

    @server.tool()
    def caminho_apk() -> str:
        """Devolve o caminho do APK neste computador e diz se o arquivo existe."""
        path = apk_path()
        flag = "existe" if path.is_file() else "não existe"
        return f"{path} ({flag})"

    @server.tool()
    def listar_aparelhos() -> str:
        """Lista os celulares conectados por USB com depuração ligada (o número serve para aparelho=)."""
        return _adb("devices", "-l")

    @server.tool()
    @user_errors(ValueError)
    def instalar_apk(aparelho: str = "") -> str:
        """Instala ou atualiza o APK no celular conectado, com adb."""
        path = apk_path()
        if not path.is_file():
            return f"Não achei o APK em {path}."
        return _adb(*_target(aparelho), "install", "-r", str(path), timeout=300)

    @server.tool()
    @user_errors(ValueError)
    def iniciar_app(aparelho: str = "") -> str:
        """Abre o aplicativo no celular conectado."""
        return _adb(*_target(aparelho), "shell", "am", "start", "-n", _ACTIVITY)

    @server.tool()
    @user_errors(ValueError)
    def status_celular(aparelho: str = "") -> str:
        """Diz se o app responde pelo AI Conector, quantos arquivos há e se existe voz offline."""
        return _bridge(aparelho, "status", {})

    @server.tool()
    @user_errors(ValueError)
    def listar_arquivos(aparelho: str = "") -> str:
        """Lista os arquivos guardados no app (gravações, textos e áudios)."""
        return _bridge(aparelho, "listar", {})

    @server.tool()
    @user_errors(ValueError)
    def ler_arquivo(nome: str, aparelho: str = "") -> str:
        """Lê um arquivo de texto (txt ou md) guardado no app."""
        return _bridge(aparelho, "ler_arquivo", {"nome": _name(nome)})

    @server.tool()
    @user_errors(ValueError)
    def salvar_texto(nome: str, texto: str, aparelho: str = "") -> str:
        """Guarda um texto no app com o nome dado (terminado em .txt ou .md)."""
        return _bridge(aparelho, "salvar", {"nome": _name(nome), "texto": _text(texto)})

    @server.tool()
    @user_errors(ValueError)
    def excluir_arquivo(nome: str, confirmar: bool = False, aparelho: str = "") -> str:
        """Apaga um arquivo do app. Só apaga com confirmar=true, depois de perguntar à pessoa."""
        clean = _name(nome)
        if confirmar is not True:
            return f"Nada foi apagado. Pergunte à pessoa se quer mesmo apagar {clean} e chame com confirmar=true."
        return _bridge(aparelho, "excluir", {"nome": clean})

    @server.tool()
    @user_errors(ValueError)
    def resumir_no_celular(texto: str, frases: int = 0, aparelho: str = "") -> str:
        """Resume um texto com o resumo do próprio app (sem IA e sem internet)."""
        return _bridge(aparelho, "resumir", {"texto": _text(texto), "frases": max(0, min(int(frases), 30))})

    @server.tool()
    @user_errors(ValueError)
    def ler_em_voz_alta(texto: str, velocidade: float = 1.0, aparelho: str = "") -> str:
        """Faz o celular ler o texto em voz alta com a voz offline do aparelho."""
        return _bridge(aparelho, "falar", {"texto": _text(texto), "velocidade": _speed(velocidade)})

    @server.tool()
    @user_errors(ValueError)
    def parar_leitura(aparelho: str = "") -> str:
        """Para a leitura em voz alta no celular."""
        return _bridge(aparelho, "parar_fala", {})

    @server.tool()
    @user_errors(ValueError)
    def salvar_audio(texto: str, nome: str = "leitura", velocidade: float = 1.0, aparelho: str = "") -> str:
        """Grava a leitura do texto num arquivo WAV guardado no app."""
        return _bridge(aparelho, "salvar_audio", {"texto": _text(texto), "nome": _name(nome), "velocidade": _speed(velocidade)})

    return server


def _target(aparelho: str) -> list[str]:
    serial = (aparelho or "").strip()
    if not serial:
        return []
    if not _SERIAL.fullmatch(serial):
        raise ValueError("Número de aparelho inválido. Use listar_aparelhos.")
    return ["-s", serial]


def _name(raw: str) -> str:
    name = (raw or "").strip()
    if not _FILE_NAME.fullmatch(name) or ".." in name:
        raise ValueError("Use só letras, números, espaço, ponto, hífen e sublinhado no nome (até 80).")
    return name


def _text(raw: str) -> str:
    if not (raw or "").strip():
        raise ValueError("Escreva o texto.")
    if len(raw) > MAX_TEXT:
        raise ValueError("O texto passa de 200 mil caracteres.")
    return raw


def _speed(raw) -> float:
    try:
        return max(0.5, min(float(raw), 2.5))
    except (TypeError, ValueError):
        return 1.0


def encode_request(payload: dict) -> str:
    return base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")


def decode_reply(output: str) -> tuple[bool, str]:
    """Lê a saída do `content call`: Result: Bundle[{ok=true, resultado=<base64>}]."""
    found = re.search(r"resultado=([A-Za-z0-9+/=]*)", output)
    if not found:
        return False, output.strip() or "O app não respondeu. Atualize o app com instalar_apk e abra uma vez."
    try:
        text = base64.b64decode(found.group(1)).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False, "Resposta inválida do app."
    return "ok=true" in output, text


def _bridge(aparelho: str, method: str, payload: dict) -> str:
    arg = encode_request(payload)
    if len(arg) > MAX_ARG:
        raise ValueError("Pedido grande demais para o cabo USB.")
    args = [*_target(aparelho), "shell", "content", "call", "--uri", _URI, "--method", method]
    if payload:
        args += ["--arg", arg]
    output = _adb(*args, timeout=150)
    ok, text = decode_reply(output)
    if not ok:
        raise ValueError(text)
    return text


def _adb(*args: str, timeout: int = 60) -> str:
    binary = adb_binary()
    if binary is None:
        return f"O adb não está instalado. Instale o Android SDK Platform Tools: {_ADB_HELP}"
    try:
        completed = subprocess.run([binary, *args], capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return "O adb demorou demais. Confira o cabo e se a depuração USB foi autorizada no celular."
    detail = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode != 0:
        return detail or "O adb não concluiu o pedido."
    return detail or "Pronto."


def main() -> None:
    serve(build_server(), default_port=8768)


if __name__ == "__main__":
    main()
