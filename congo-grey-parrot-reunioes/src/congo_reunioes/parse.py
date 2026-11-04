from __future__ import annotations

import html
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

_TIME_ARROW = re.compile(r"((?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{1,3})\s+-->")
_VOICE = re.compile(r"<v(?:\.\w+)?\s+([^>]+)>(.*?)</v>", re.IGNORECASE | re.DOTALL)
_VOICE_OPEN = re.compile(r"^<v(?:\.\w+)?\s+([^>]+)>\s*(.*)$", re.IGNORECASE)
_LINE = re.compile(
    r"^(?:\[(?P<when>[^\]]+)\]\s*)?(?P<name>[^:\n]{1,80}):\s*(?P<text>\S.*)$"
)
_TAG = re.compile(r"<[^>]+>")
# O Google Meet põe o horário numa linha sozinha, a cada poucos minutos.
_STAMP_ALONE = re.compile(r"^(?:\d{1,2}:)?\d{1,2}:\d{2}$")
_DOCX_PARAGRAPH = re.compile(r"</w:p>")
_DOCX_TEXT = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<w:(?:tab|br)\s*/>")
MAX_DOCX_XML_BYTES = 30 * 1024 * 1024
TRANSCRIPT_SUFFIXES = {".vtt", ".txt", ".srt", ".docx"}


@dataclass(frozen=True)
class SpokenLine:
    speaker: str
    text: str
    when: str


def parse_transcript(raw: str) -> list[SpokenLine]:
    text = raw.lstrip("\ufeff")
    if "WEBVTT" in text[:200] or "-->" in text:
        lines = _parse_vtt(text)
        if lines:
            return lines
    return _parse_plain(text)


def _parse_vtt(raw: str) -> list[SpokenLine]:
    found: list[SpokenLine] = []
    for block in re.split(r"\n\s*\n", raw.replace("\r\n", "\n")):
        when = ""
        payload: list[str] = []
        for line in block.splitlines():
            match = _TIME_ARROW.search(line)
            if match:
                when = match.group(1).replace(".", ",")
                continue
            if line.strip() in {"WEBVTT", "NOTE"} or line.strip().isdigit():
                continue
            if line.strip():
                payload.append(line.strip())
        if not payload:
            continue
        body = "\n".join(payload)
        voices = list(_VOICE.finditer(body))
        if voices:
            for voice in voices:
                speech = _clean(voice.group(2))
                if speech:
                    found.append(SpokenLine(voice.group(1).strip(), speech, when))
            continue
        open_voice = _VOICE_OPEN.match(body)
        if open_voice:
            speech = _clean(open_voice.group(2))
            if speech:
                found.append(SpokenLine(open_voice.group(1).strip(), speech, when))
            continue
        found.extend(_lines_from_text(body, when))
    return found


def _parse_plain(raw: str) -> list[SpokenLine]:
    found: list[SpokenLine] = []
    when = ""
    for line in raw.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if _STAMP_ALONE.match(stripped):
            when = stripped
            continue
        found.extend(_lines_from_text(stripped, when))
    return found


def read_transcript_file(path: Path) -> str:
    """Texto de um VTT, SRT, TXT ou DOCX. O DOCX é o que o Google Docs baixa da transcrição do Meet."""
    if path.suffix.lower() == ".docx":
        return _docx_text(path)
    return path.read_text(encoding="utf-8-sig", errors="replace")


def _docx_text(path: Path) -> str:
    # Lê o XML com expressão regular, sem parser de XML: nada de entidade externa,
    # e o tamanho descompactado tem limite, contra arquivo-bomba.
    try:
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > MAX_DOCX_XML_BYTES:
                raise ValueError("O DOCX é grande demais para uma transcrição.")
            xml = archive.read(info).decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError):
        raise ValueError("Esse arquivo não é um DOCX válido.") from None
    paragraphs = []
    for chunk in _DOCX_PARAGRAPH.split(xml):
        pieces = []
        for match in _DOCX_TEXT.finditer(chunk):
            pieces.append(html.unescape(match.group(1)) if match.group(1) is not None else " ")
        paragraphs.append("".join(pieces))
    return "\n".join(paragraphs)


def _lines_from_text(body: str, when: str) -> list[SpokenLine]:
    found: list[SpokenLine] = []
    for line in body.splitlines():
        match = _LINE.match(line.strip())
        if not match:
            continue
        # "10:00 GMT-3" no título ou "terminou após 00:45:12" não são falas.
        if match.group("name")[-1:].isdigit() and match.group("text")[:1].isdigit():
            continue
        found.append(SpokenLine(match.group("name").strip(), _clean(match.group("text")), match.group("when") or when))
    return found


def _clean(text: str) -> str:
    return " ".join(_TAG.sub("", text).split())


def render_notes(lines: list[SpokenLine], platform: str) -> str:
    if not lines:
        return (
            "Não encontrei falas com nome. O Teams e o Meet colocam o nome na transcrição baixada. "
            "Uma gravação única do microfone não traz esses nomes.\n"
            "Formato aceito: Nome: o que a pessoa disse"
        )
    ordered = [f"Reunião: {platform}", summary_text(lines), "", "Quem falou, o que disse e quando:"]
    grouped: dict[str, list[str]] = {}
    for line in lines:
        stamp = f"[{line.when}] " if line.when else ""
        ordered.append(f"{stamp}{line.speaker}: {line.text}")
        grouped.setdefault(line.speaker, []).append(f"{stamp}{line.text}")
    ordered.append("")
    ordered.append("Por pessoa:")
    for speaker, items in grouped.items():
        ordered.append(f"{speaker}:")
        ordered.extend(f"- {item}" for item in items)
    return "\n".join(ordered)


def summary_text(lines: list[SpokenLine]) -> str:
    """Resumo contado das falas. Não usa IA e não inventa conteúdo."""
    counts: dict[str, int] = {}
    for line in lines:
        counts[line.speaker] = counts.get(line.speaker, 0) + 1
    ranking = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    people = ", ".join(f"{name} ({count})" for name, count in ranking)
    stamps = [line.when for line in lines if line.when]
    span = f" De {stamps[0]} a {stamps[-1]}." if stamps else ""
    return f"Resumo: {len(lines)} falas de {len(counts)} pessoas. Falas por pessoa: {people}.{span}"
