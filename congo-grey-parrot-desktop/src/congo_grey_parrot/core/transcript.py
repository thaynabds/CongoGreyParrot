from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WordTiming:
    text: str
    start: float
    end: float
    probability: float | None = None


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str
    words: tuple[WordTiming, ...] = ()


@dataclass(frozen=True)
class Transcript:
    text: str
    language: str
    task: str
    model: str
    segments: tuple[Segment, ...] = ()
    source_name: str = ""
    extras: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "task": self.task,
            "model": self.model,
            "source_name": self.source_name,
            "segments": [
                {
                    "id": index,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [
                        {
                            "word": word.text,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability,
                        }
                        for word in segment.words
                    ],
                }
                for index, segment in enumerate(self.segments)
            ],
        }


def transcript_from_dict(payload: dict, source_name: str = "") -> Transcript:
    segments: list[Segment] = []
    for raw in payload.get("segments") or []:
        words = []
        for word in raw.get("words") or []:
            label = str(word.get("word", word.get("text", "")))
            words.append(
                WordTiming(
                    text=label,
                    start=float(word.get("start", 0)),
                    end=float(word.get("end", 0)),
                    probability=word.get("probability"),
                )
            )
        segments.append(
            Segment(
                start=float(raw.get("start", 0)),
                end=float(raw.get("end", 0)),
                text=str(raw.get("text", "")).strip(),
                words=tuple(words),
            )
        )
    text = str(payload.get("text") or "").strip()
    if not text:
        text = " ".join(segment.text for segment in segments).strip()
    return Transcript(
        text=text,
        language=str(payload.get("language") or ""),
        task=str(payload.get("task") or "transcribe"),
        model=str(payload.get("model") or ""),
        segments=tuple(segments),
        source_name=source_name or str(payload.get("source_name") or ""),
    )
