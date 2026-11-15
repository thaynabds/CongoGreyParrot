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
            "A janela ativa não tem texto exposto pela acessibilidade."
        )
    wav = Path(tempfile.mkdtemp(prefix="ler-janela-")) / "leitura.wav"
    speech.synthesize(text, wav)
    played = play(wav)
    return text, (None if played else wav)


def main(argv: list[str] | None = None) -> int:
    try:
        text, wav = read_active_window(SpeechService())
    except (AccessibilityUnavailable, AppError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if wav is not None:
        print(f"Nenhum tocador de áudio encontrado. O áudio está em {wav}", file=sys.stderr)
    return 0
