from __future__ import annotations

from dataclasses import dataclass


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
