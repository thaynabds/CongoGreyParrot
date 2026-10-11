from __future__ import annotations

import json
import re
from dataclasses import dataclass

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.core.transcript import Segment, Transcript, transcript_from_dict

TIME_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})")


@dataclass(frozen=True)
class CaptionOptions:
    highlight_words: bool = False
    max_line_width: int | None = None
    max_line_count: int | None = None
    max_words_per_line: int | None = None


def format_timestamp(seconds: float, separator: str = ",") -> str:
    milliseconds = max(0, int(round(float(seconds) * 1000)))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{milliseconds:03d}"


def parse_timestamp(value: str) -> float:
    text = value.strip()
    if re.fullmatch(r"\d+(?:[.,]\d+)?", text):
        return float(text.replace(",", "."))
    match = TIME_RE.fullmatch(text)
    if not match:
        raise AppError(f"Tempo inválido: {value}")
    hours, minutes, seconds, fraction = match.groups()
    millis = int(fraction.ljust(3, "0")[:3])
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + millis / 1000


def wrap_caption(
    text: str,
    width: int | None = None,
    max_lines: int | None = None,
    max_words: int | None = None,
) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    words = cleaned.split()
    if max_words and not width:
        lines = [" ".join(words[index : index + max_words]) for index in range(0, len(words), max_words)]
    elif width:
        lines = []
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if current and len(trial) > width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
    else:
        lines = [cleaned]
    if max_lines is not None and max_lines > 0:
        lines = lines[:max_lines]
    return "\n".join(lines)


def cues_for(transcript: Transcript, options: CaptionOptions | None = None) -> list[tuple[float, float, str]]:
    options = options or CaptionOptions()
    cues: list[tuple[float, float, str]] = []
    for segment in transcript.segments:
        if options.highlight_words and segment.words:
            for word in segment.words:
                label = word.text.strip()
                if label:
                    cues.append((word.start, word.end, f"<u>{label}</u>"))
            continue
        text = wrap_caption(
            segment.text,
            options.max_line_width,
            options.max_line_count,
            None if options.max_line_width else options.max_words_per_line,
        )
        if text:
            cues.append((segment.start, segment.end, text))
    return cues


def render_srt(transcript: Transcript, options: CaptionOptions | None = None) -> str:
    blocks = []
    for index, (start, end, text) in enumerate(cues_for(transcript, options), start=1):
        blocks.append(
            f"{index}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n"
        )
    return "\n".join(blocks).strip() + ("\n" if blocks else "")


def render_vtt(transcript: Transcript, options: CaptionOptions | None = None) -> str:
    lines = ["WEBVTT", ""]
    for start, end, text in cues_for(transcript, options):
        lines.append(f"{format_timestamp(start, '.')} --> {format_timestamp(end, '.')}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_tsv(transcript: Transcript) -> str:
    rows = ["start\tend\ttext"]
    for segment in transcript.segments:
        if not segment.text.strip():
            continue
        rows.append(
            f"{int(round(segment.start * 1000))}\t{int(round(segment.end * 1000))}\t{segment.text.strip()}"
        )
    return "\n".join(rows) + "\n"


def render_ass(transcript: Transcript, options: CaptionOptions | None = None) -> str:
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BorderStyle, Outline, Shadow, Alignment\n"
        "Style: Default,DejaVu Sans,42,&H00FFFFFF,&H00000000,1,2,0,2\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Text\n"
    )
    lines = [header.rstrip("\n")]
    for start, end, text in cues_for(transcript, options):
        payload = text.replace("\n", r"\N")
        lines.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,{payload}"
        )
    return "\n".join(lines) + "\n"


def _ass_time(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 100)))
    hours, milliseconds = divmod(milliseconds, 360_000)
    minutes, milliseconds = divmod(milliseconds, 6_000)
    secs, centiseconds = divmod(milliseconds, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def render_json(transcript: Transcript) -> str:
    return json.dumps(transcript.to_dict(), ensure_ascii=False, indent=2) + "\n"


def render_jsonl(transcript: Transcript) -> str:
    rows = []
    for index, segment in enumerate(transcript.segments):
        rows.append(
            json.dumps(
                {
                    "id": index,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "language": transcript.language,
                    "task": transcript.task,
                    "model": transcript.model,
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(rows) + ("\n" if rows else "")


def parse_srt(text: str) -> Transcript:
    blocks = re.split(r"\n\s*\n", text.strip())
    segments: list[Segment] = []
    for block in blocks:
        lines = [line.strip("\ufeff") for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        timing_index = 1 if "-->" not in lines[0] else 0
        if timing_index >= len(lines) or "-->" not in lines[timing_index]:
            continue
        start_raw, end_raw = [part.strip() for part in lines[timing_index].split("-->", 1)]
        end_raw = end_raw.split()[0]
        body = "\n".join(lines[timing_index + 1 :]).strip()
        segments.append(Segment(parse_timestamp(start_raw), parse_timestamp(end_raw.split()[0]), body))
    if not segments:
        raise AppError("Não encontrei legendas nesse arquivo.")
    joined = " ".join(segment.text.replace("\n", " ") for segment in segments)
    return Transcript(text=joined, language="", task="transcribe", model="", segments=tuple(segments))


def parse_vtt(text: str) -> Transcript:
    body = re.sub(r"^WEBVTT.*\n", "", text.strip(), count=1)
    return parse_srt(body)


def parse_transcript_json(text: str, source_name: str = "") -> Transcript:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AppError("O JSON não pôde ser lido.") from exc
    if isinstance(payload, dict) and "segments" in payload:
        return transcript_from_dict(payload, source_name)
    raise AppError("O JSON não tem o campo segments.")


def segments_from_table(rows: list[tuple[str, str, str]]) -> tuple[Segment, ...]:
    segments: list[Segment] = []
    for index, (start, end, text) in enumerate(rows, start=1):
        if not str(text).strip():
            continue
        try:
            start_s = parse_timestamp(start)
            end_s = parse_timestamp(end)
        except AppError as exc:
            raise AppError(f"Linha {index}: {exc}") from exc
        if end_s <= start_s:
            raise AppError(f"Linha {index}: o fim precisa ser maior que o início.")
        segments.append(Segment(start_s, end_s, str(text).strip()))
    return tuple(segments)


def transcript_from_segments(segments: tuple[Segment, ...], source_name: str = "") -> Transcript:
    text = " ".join(segment.text.replace("\n", " ") for segment in segments).strip()
    return Transcript(
        text=text,
        language="",
        task="transcribe",
        model="",
        segments=segments,
        source_name=source_name,
    )
