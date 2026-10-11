from __future__ import annotations

import shutil
from pathlib import Path

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.files.naming import assert_inside
from congo_grey_parrot.models.catalog import VoiceEntry, load_voice_catalog, scan_installed_voices
from congo_grey_parrot.models.downloader import download_file


class ModelService:
    def __init__(self, voice_root: Path, whisper_root: Path):
        self.voice_root = voice_root
        self.whisper_root = whisper_root
        self.voice_root.mkdir(parents=True, exist_ok=True)
        self.whisper_root.mkdir(parents=True, exist_ok=True)
        self.extra_voices: list[Path] = []
        self.extra_whisper: list[Path] = []

    def voice_roots(self) -> list[Path]:
        return _unique_dirs([self.voice_root, *self.extra_voices])

    def whisper_roots(self) -> list[Path]:
        return _unique_dirs([self.whisper_root, *self.extra_whisper])

    def catalog(self) -> tuple[VoiceEntry, ...]:
        return load_voice_catalog()

    def installed(self):
        found = []
        seen = set()
        for root in self.voice_roots():
            for voice in scan_installed_voices(root):
                key = str(voice.model_path.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(voice)
        return tuple(found)

    def download_voice(self, entry: VoiceEntry, progress, cancel, destination: Path | None = None) -> Path:
        if any(part in entry.id for part in ("/", "\\", "..")):
            raise AppError("Identificador de voz inválido.")
        root = (destination or self.voice_root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        folder = (root / entry.id).resolve()
        assert_inside(root, folder)
        folder.mkdir(parents=True, exist_ok=True)
        model_path = folder / f"{entry.id}.onnx"
        config_path = folder / f"{entry.id}.onnx.json"

        def first(done: int, total: int) -> None:
            fraction = (done / total) if total else 0
            progress(int(fraction * 80), "Baixando modelo da voz")

        def second(done: int, total: int) -> None:
            fraction = (done / total) if total else 0
            progress(80 + int(fraction * 20), "Baixando configuração da voz")

        download_file(entry.model_url, model_path, first, cancel)
        try:
            download_file(entry.config_url, config_path, second, cancel)
        except Exception:
            model_path.unlink(missing_ok=True)
            raise
        if not model_path.is_file() or not config_path.is_file():
            raise AppError("A voz ficou incompleta e foi descartada.")
        progress(100, "Voz instalada")
        return folder

    def remove_voice(self, folder: Path) -> None:
        target = folder.expanduser().resolve()
        roots = {root.resolve() for root in self.voice_roots()}
        if target in roots:
            raise AppError("Não vou apagar a pasta inteira de vozes.")
        if not any(root == target or root in target.parents for root in roots):
            raise AppError("Essa voz está fora das pastas conhecidas.")
        shutil.rmtree(target)

    def clear_whisper_cache(self) -> None:
        for root in self.whisper_roots():
            if not root.exists():
                continue
            for child in list(root.iterdir()):
                if child.is_dir() and "faster-whisper" in child.name:
                    shutil.rmtree(child)


def _unique_dirs(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in found:
            found.append(resolved)
    return found
