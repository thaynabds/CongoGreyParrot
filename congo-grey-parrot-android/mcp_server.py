"""Ponte MCP do aplicativo Android.

O celular não fala MCP. Este processo roda no computador e só sabe
mostrar o APK, explicar a instalação e, se o adb estiver instalado,
instalar e abrir o aplicativo.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_REPO = _ROOT.parent
if str(_REPO / "mcp") not in sys.path:
    sys.path.insert(0, str(_REPO / "mcp"))

from runtime import make_server, serve  # noqa: E402

_ACTIVITY = "org.congogreyparrot/.MainActivity"
_HELP = (
    "https://support.google.com/android/answer/2664792?hl=pt-BR"
)


def apk_path() -> Path:
    built = _ROOT / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    published = _ROOT / "CongoGreyParrot-debug.apk"
    if built.is_file():
        return built
    return published


def build_server():
    server = make_server("Congo Grey Parrot Android")

    @server.tool()
    def instrucoes_apk() -> str:
        """Explica como instalar o aplicativo no celular. O app em si não é um servidor MCP."""
        path = apk_path()
        state = "O arquivo está neste computador." if path.is_file() else "O arquivo do APK ainda não foi gerado."
        return (
            f"{state} Caminho: {path}\n"
            "1. Copie esse arquivo para o Android 8 ou mais novo.\n"
            "2. Abra o arquivo no celular.\n"
            "3. Se o sistema bloquear, permita instalar por esse aplicativo.\n"
            f"Ajuda do Google: {_HELP}\n"
            "O aplicativo grava áudio e lê texto. Não transcreve com Whisper e não abre uma porta de rede."
        )

    @server.tool()
    def caminho_apk() -> str:
        """Devolve o caminho do APK neste computador e diz se o arquivo existe."""
        path = apk_path()
        flag = "existe" if path.is_file() else "não existe"
        return f"{path} ({flag})"

    @server.tool()
    def instalar_apk() -> str:
        """Instala o APK com adb, se o adb e o arquivo existirem."""
        return _adb("install", "-r", str(apk_path()))

    @server.tool()
    def iniciar_app() -> str:
        """Abre o aplicativo no celular conectado, se o adb existir."""
        return _adb("shell", "am", "start", "-n", _ACTIVITY)

    return server


def _adb(*args: str) -> str:
    binary = shutil.which("adb")
    if binary is None:
        return "O adb não está instalado. Use instrucoes_apk e copie o arquivo para o celular."
    if args[0] == "install" and not Path(args[-1]).is_file():
        return f"Não achei o APK em {args[-1]}."
    completed = subprocess.run([binary, *args], capture_output=True, text=True, timeout=180, check=False)
    detail = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode != 0:
        return detail or "O adb não concluiu o pedido."
    return detail or "Pronto."


def main() -> None:
    serve(build_server(), default_port=8768)


if __name__ == "__main__":
    main()
