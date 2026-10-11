from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

TEXT_FILTER = (
    "Texto (*.txt);;Markdown (*.md);;Word (*.docx);;PDF (*.pdf);;"
    "SubRip (*.srt);;WebVTT (*.vtt);;ASS (*.ass);;TSV (*.tsv);;JSON (*.json);;JSONL (*.jsonl)"
)
PLAIN_FILTER = "Texto (*.txt);;Markdown (*.md);;Word (*.docx);;PDF (*.pdf)"
AUDIO_FILTER = "WAV (*.wav);;MP3 (*.mp3);;M4A (*.m4a);;OGG (*.ogg);;FLAC (*.flac)"
MEDIA_FILTER = (
    "WAV (*.wav);;MP3 (*.mp3);;M4A (*.m4a);;OGG (*.ogg);;FLAC (*.flac);;"
    "MP4 (*.mp4);;MKV (*.mkv);;WebM (*.webm);;MOV (*.mov)"
)


def warn(parent, text: str) -> None:
    QMessageBox.warning(parent, "Project Congo Grey Parrot", text)


def info(parent, text: str) -> None:
    QMessageBox.information(parent, "Project Congo Grey Parrot", text)


def confirm(parent, text: str) -> bool:
    answer = QMessageBox.question(parent, "Project Congo Grey Parrot", text)
    return answer == QMessageBox.StandardButton.Yes


def ask_save(parent, suggested: str, file_filter: str) -> Path | None:
    name, selected = QFileDialog.getSaveFileName(parent, "Salvar arquivo", suggested, file_filter)
    if not name:
        return None
    path = Path(name)
    match = re.search(r"\*\.(\w+)", selected or "")
    if match and path.suffix == "":
        path = path.with_suffix("." + match.group(1))
    return path


def ask_open(parent, file_filter: str) -> Path | None:
    name, _selected = QFileDialog.getOpenFileName(parent, "Abrir arquivo", "", file_filter)
    if not name:
        return None
    return Path(name)


def ask_directory(parent, current: str) -> Path | None:
    name = QFileDialog.getExistingDirectory(parent, "Escolher pasta", current)
    if not name:
        return None
    return Path(name)
