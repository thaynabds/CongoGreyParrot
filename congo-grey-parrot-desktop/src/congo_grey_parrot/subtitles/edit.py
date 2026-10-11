from __future__ import annotations

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.core.transcript import Segment


def shift_segments(segments: tuple[Segment, ...], delta_seconds: float) -> tuple[Segment, ...]:
    shifted = []
    for segment in segments:
        start = max(0.0, segment.start + delta_seconds)
        end = max(start + 0.05, segment.end + delta_seconds)
        words = tuple(
            type(word)(
                text=word.text,
                start=max(0.0, word.start + delta_seconds),
                end=max(0.0, word.end + delta_seconds),
                probability=word.probability,
            )
            for word in segment.words
        )
        shifted.append(Segment(start, end, segment.text, words))
    return tuple(shifted)


def split_segment(segments: tuple[Segment, ...], index: int) -> tuple[Segment, ...]:
    if index < 0 or index >= len(segments):
        raise AppError("Escolha um trecho para dividir.")
    current = segments[index]
    words = current.text.split()
    if len(words) < 2:
        midpoint = (current.start + current.end) / 2
        left = Segment(current.start, midpoint, current.text, ())
        right = Segment(midpoint, max(current.end, midpoint + 0.05), current.text, ())
    else:
        cut = len(words) // 2
        midpoint = current.start + (current.end - current.start) / 2
        left = Segment(current.start, midpoint, " ".join(words[:cut]), ())
        right = Segment(midpoint, current.end, " ".join(words[cut:]), ())
    return segments[:index] + (left, right) + segments[index + 1 :]


def merge_with_next(segments: tuple[Segment, ...], index: int) -> tuple[Segment, ...]:
    if index < 0 or index >= len(segments) - 1:
        raise AppError("Escolha um trecho que tenha outro depois dele.")
    current = segments[index]
    nxt = segments[index + 1]
    text = " ".join(part for part in (current.text.strip(), nxt.text.strip()) if part)
    merged = Segment(current.start, max(current.end, nxt.end), text, current.words + nxt.words)
    return segments[:index] + (merged,) + segments[index + 2 :]
