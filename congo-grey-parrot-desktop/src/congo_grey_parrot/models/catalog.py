from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

@dataclass(frozen=True)
class VoiceEntry:
    id: str
    name: str
    language: str
    language_label: str
    quality: str
    model_url: str
    config_url: str

    @property
    def card_url(self) -> str:
        folder = self.model_url.rsplit("/", 1)[0].replace("/resolve/main/", "/blob/main/")
        return f"{folder}/MODEL_CARD"


@dataclass(frozen=True)
class WhisperModelInfo:
    name: str
    profile: str
    translates_to_english: bool
    note: str


WHISPER_MODELS = (
    WhisperModelInfo("tiny", "Leve", True, "Cerca de 1 GB de VRAM na tabela oficial."),
    WhisperModelInfo("base", "Leve", True, "Cerca de 1 GB de VRAM na tabela oficial."),
    WhisperModelInfo("small", "Equilibrado", True, "Cerca de 2 GB de VRAM na tabela oficial."),
    WhisperModelInfo("medium", "Equilibrado", True, "Cerca de 5 GB de VRAM na tabela oficial. Indicado para tradução."),
    WhisperModelInfo("large", "Alta precisão", True, "Cerca de 10 GB de VRAM na tabela oficial."),
    WhisperModelInfo("turbo", "Rápido", False, "Não traduz. O README indica uso para transcrição."),
    WhisperModelInfo("tiny.en", "Inglês leve", False, "Somente inglês."),
    WhisperModelInfo("base.en", "Inglês leve", False, "Somente inglês."),
    WhisperModelInfo("small.en", "Inglês", False, "Somente inglês."),
    WhisperModelInfo("medium.en", "Inglês", False, "Somente inglês."),
)


def load_voice_catalog() -> tuple[VoiceEntry, ...]:
    raw = files("congo_grey_parrot.models").joinpath("voices.json").read_text(encoding="utf-8")
    payload = json.loads(raw)
    return tuple(VoiceEntry(**item) for item in payload)


@dataclass(frozen=True)
class InstalledVoice:
    voice_id: str
    folder: Path
    model_path: Path
    config_path: Path


def scan_installed_voices(root: Path) -> tuple[InstalledVoice, ...]:
    if not root.exists():
        return ()
    found: list[InstalledVoice] = []
    for model in sorted(root.rglob("*.onnx")):
        config = Path(str(model) + ".json")
        if config.is_file():
            found.append(InstalledVoice(model.stem, model.parent, model, config))
    return tuple(found)


def installed_whisper_names(root: Path) -> tuple[str, ...]:
    if not root.exists():
        return ()
    names = []
    for path in sorted(root.iterdir()):
        if path.is_dir() and "faster-whisper" in path.name:
            label = path.name.split("--")[-1]
            prefix = "faster-whisper-"
            if label.startswith(prefix):
                label = label[len(prefix):]
            names.append(label)
    return tuple(names)
