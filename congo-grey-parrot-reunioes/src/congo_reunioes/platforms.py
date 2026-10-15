from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeetingPlatform:
    key: str
    name: str
    site: str
    note: str


# Endereços públicos de ajuda. O programa não entra na conta dessas reuniões.
PLATFORMS = (
    MeetingPlatform(
        "teams",
        "Microsoft Teams",
        "https://learn.microsoft.com/microsoftteams/meeting-transcription-captions",
        "Baixe a transcrição em VTT. O nome de quem falou vem nesse arquivo.",
    ),
    MeetingPlatform(
        "meet",
        "Google Meet",
        "https://support.google.com/meet/answer/12849897",
        "No Google Workspace a reunião pode gerar transcrição. Importe o VTT ou o texto exportado.",
    ),
    MeetingPlatform(
        "zoom",
        "Zoom",
        "https://support.zoom.com/",
        "Importe o VTT da transcrição, se a reunião tiver gerado uma.",
    ),
    MeetingPlatform(
        "webex",
        "Webex",
        "https://help.webex.com/",
        "Importe o VTT ou um texto no formato Nome: fala.",
    ),
    MeetingPlatform(
        "jitsi",
        "Jitsi Meet",
        "https://jitsi.org/",
        "Não confirmei transcrição com nomes. Use o áudio local ou um texto Nome: fala.",
    ),
)


def find_platform(name: str) -> MeetingPlatform | None:
    cleaned = name.strip().lower()
    compact = "".join(character for character in cleaned if character.isalnum())
    for item in PLATFORMS:
        if item.key == compact or item.name.lower() == cleaned:
            return item
    return None


def platform_label(name: str) -> str:
    known = find_platform(name)
    return known.name if known else name.strip()[:80]


def catalog_text() -> str:
    lines = [
        "Reuniões conhecidas. Este programa não entra na conta delas.",
        "Para estas e para qualquer outra, importe a transcrição com congo-reunioes importar.",
    ]
    for item in PLATFORMS:
        lines.append(f"{item.name}. {item.site} {item.note}")
    lines.append("Um nome que não esteja aqui também serve. Ele fica só como rótulo da anotação.")
    return "\n".join(lines)
