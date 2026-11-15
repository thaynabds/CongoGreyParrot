"""Comando `congo-grey-parrot ler-janela`: lê em voz alta a janela ativa.

Pensado para um atalho do sistema (por exemplo, o atalho personalizado do GNOME
ou do KDE). Assim a leitura funciona em qualquer programa, sem instalar nada em
cada aplicação, porque a janela ativa é lida pela árvore de acessibilidade.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.screen.accessibility import AccessibilityUnavailable, active_window_text
from congo_grey_parrot.speech.service import SpeechService

PLAYERS = (
    ("pw-play", ["pw-play"]),
    ("paplay", ["paplay"]),
    ("aplay", ["aplay", "-q"]),
)


def play_wav(path: Path) -> bool:
    for binary, command in PLAYERS:
        if shutil.which(binary):
            result = subprocess.run([*command, str(path)], check=False)
            return result.returncode == 0
    return False


def read_active_window(speech: SpeechService, play=play_wav) -> tuple[str, Path | None]:
    """Devolve o texto lido e o arquivo WAV (None se nada foi gerado)."""
    text = active_window_text()
    if not text.strip():
        raise AccessibilityUnavailable(
            "A janela ativa não tem texto exposto pela acessibilidade. "
            "Rode `congo-grey-parrot instalar-atalho` uma vez para ativar a acessibilidade "
            "do sistema e abra o navegador de novo."
        )
    folder = Path(tempfile.mkdtemp(prefix="ler-janela-"))
    wav = folder / "leitura.wav"
    try:
        speech.synthesize(text, wav)
        played = play(wav)
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    if played:
        # O áudio contém o texto da tela; não fica guardado depois de tocar.
        shutil.rmtree(folder, ignore_errors=True)
        return text, None
    return text, wav


def install_shortcut_main() -> int:
    from congo_grey_parrot.screen.shortcut import DEFAULT_BINDING, install_shortcut

    try:
        desktop, _ = install_shortcut()
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Não consegui criar o atalho: {error}", file=sys.stderr)
        print(f"Crie um atalho manual com o comando `congo-grey-parrot ler-janela` e a tecla {DEFAULT_BINDING}.", file=sys.stderr)
        return 1
    name = {"cinnamon": "Cinnamon", "gnome": "GNOME"}.get(desktop, desktop)
    print(f"Atalho criado no {name}: {DEFAULT_BINDING} lê a janela ativa.")
    print("A acessibilidade do sistema foi ativada, para os navegadores exporem o texto.")
    print("Feche e abra de novo os navegadores que já estavam abertos.")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        text, wav = read_active_window(SpeechService())
    except (AccessibilityUnavailable, AppError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if wav is not None:
        print(f"Nenhum tocador de áudio encontrado. O áudio está em {wav}", file=sys.stderr)
    return 0
