from __future__ import annotations

import re
from dataclasses import dataclass

from congo_discord.resumo import resumir, resumir_falas, resumo_texto

SUMMARY_SUFFIXES = (".txt", ".md", ".vtt", ".srt")
MAX_SUMMARY_FILE_BYTES = 2 * 1024 * 1024
_TIMING = re.compile(r"-->|^\d+$|^WEBVTT|^NOTE\b")
_VOICE_TAG = re.compile(r"<v(?:\.\w+)?\s+([^>]{1,60})>(.*?)(?:</v>|$)", re.IGNORECASE)
_TAG = re.compile(r"<[^>]{0,200}>")


@dataclass(frozen=True)
class Utterance:
    speaker: str
    text: str
    when: str


def render_meeting(lines: list[Utterance]) -> str:
    if not lines:
        return "Ainda não há falas registradas nesta reunião."
    ordered = ["Transcrição, com o nome em cada fala:"]
    grouped: dict[str, list[str]] = {}
    for line in lines:
        speech = " ".join(line.text.split())
        ordered.append(f"[{line.when}] {line.speaker}: {speech}")
        grouped.setdefault(line.speaker, []).append(f"[{line.when}] {speech}")
    ordered.append("")
    ordered.append("O que cada pessoa disse, e quando:")
    for speaker, items in grouped.items():
        ordered.append(f"{speaker}:")
        ordered.extend(f"- {item}" for item in items)
    return "\n".join(ordered)


def summarize_meeting(lines: list[Utterance], sentences: int = 0) -> str:
    """Resumo da reunião: frases do próprio texto, sem IA e sem internet."""
    if not lines:
        return "Ainda não há falas registradas nesta reunião."
    result = resumir_falas(((line.speaker, line.text) for line in lines), sentences)
    return resumo_texto(result, "Resumo da reunião")


def text_from_upload(filename: str, data: bytes) -> str:
    """Texto de um arquivo enviado no Discord. Recusa tipo desconhecido e arquivo grande."""
    name = (filename or "").lower()
    if not name.endswith(SUMMARY_SUFFIXES):
        raise ValueError("Envie um arquivo TXT, MD, VTT ou SRT.")
    if len(data) > MAX_SUMMARY_FILE_BYTES:
        raise ValueError("O arquivo passa de 2 MB.")
    text = data.decode("utf-8-sig", errors="replace")
    if not name.endswith((".vtt", ".srt")):
        return text
    kept = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line or _TIMING.search(line):
            continue
        voice = _VOICE_TAG.match(line)
        if voice:
            line = f"{voice.group(1).strip()}: {voice.group(2)}"
        kept.append(_TAG.sub("", line))
    return "\n".join(kept)


def summarize_text(text: str, sentences: int = 0, title: str = "Resumo") -> str:
    return resumo_texto(resumir(text, sentences), title)
