from __future__ import annotations

import html


def _item(name: str, present: bool, fix: str, url: str) -> str:
    label = html.escape(name)
    if present:
        return f"<b>{label}:</b> disponível"
    return (
        f"<b>{label}:</b> ausente. {html.escape(fix)} "
        f'<a href="{html.escape(url)}">{html.escape(url)}</a>'
    )


def component_html(whisper: bool, piper: bool, espeak: bool, ffmpeg: bool) -> str:
    lines = [
        "<b>Componentes neste computador</b>",
        _item(
            "Transcrição faster-whisper",
            whisper,
            "No ambiente do programa: pip install faster-whisper. "
            "Depois, em Modelos e vozes, baixe um modelo.",
            "https://github.com/SYSTRAN/faster-whisper",
        ),
        _item(
            "Biblioteca Piper",
            piper,
            "No ambiente do programa: pip install piper-tts. "
            "Depois, em Modelos e vozes, baixe uma voz.",
            "https://github.com/OHF-Voice/piper1-gpl",
        ),
        _item(
            "espeak-ng",
            espeak,
            "No Ubuntu, Debian ou Linux Mint: sudo apt install espeak-ng",
            "https://github.com/espeak-ng/espeak-ng",
        ),
        _item(
            "FFmpeg",
            ffmpeg,
            "No Ubuntu, Debian ou Linux Mint: sudo apt install ffmpeg",
            "https://ffmpeg.org/download.html",
        ),
    ]
    return "<br>".join(lines)
