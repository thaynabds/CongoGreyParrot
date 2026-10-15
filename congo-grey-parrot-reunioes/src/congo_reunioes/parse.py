from __future__ import annotations

import re
from dataclasses import dataclass

_TIME_ARROW = re.compile(r"((?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{1,3})\s+-->")
_VOICE = re.compile(r"<v(?:\.\w+)?\s+([^>]+)>(.*?)</v>", re.IGNORECASE | re.DOTALL)
_VOICE_OPEN = re.compile(r"^<v(?:\.\w+)?\s+([^>]+)>\s*(.*)$", re.IGNORECASE)
_LINE = re.compile(
    r"^(?:\[(?P<when>[^\]]+)\]\s*)?(?P<name>[^:\n]{1,80}):\s*(?P<text>\S.*)$"
)
_TAG = re.compile(r"<[^>]+>")


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
    for line in raw.replace("\r\n", "\n").splitlines():
        found.extend(_lines_from_text(line.strip(), ""))
    return found


def _lines_from_text(body: str, when: str) -> list[SpokenLine]:
    found: list[SpokenLine] = []
    for line in body.splitlines():
        match = _LINE.match(line.strip())
        if not match:
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
    ordered = [f"Reunião: {platform}", "Quem falou, o que disse e quando:"]
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
