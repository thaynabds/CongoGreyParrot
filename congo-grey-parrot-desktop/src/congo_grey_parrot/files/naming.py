from __future__ import annotations

import re
from pathlib import Path

from congo_grey_parrot.core.errors import AppError

AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
VIDEO = {".mp4", ".mkv", ".mov", ".webm", ".avi"}
TEXT = {".txt", ".md", ".pdf", ".docx", ".srt", ".vtt", ".ass", ".ssa", ".json", ".jsonl", ".tsv"}


def classify(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in AUDIO:
        return "audio"
    if suffix in VIDEO:
        return "video"
    if suffix in {".srt", ".vtt", ".ass", ".ssa"}:
        return "subtitle"
    if suffix in TEXT:
        return "text"
    return "unknown"


def suggest_name(source: str, suffix: str) -> str:
    stem = Path(source).stem or "resultado"
    stem = re.sub(r'[<>:"/\\|?*\x00]+', "_", stem).strip().rstrip(".")
    stem = stem[:80] or "resultado"
    if not suffix.startswith("."):
        suffix = f".{suffix}"
    return f"{stem}{suffix}"


def prepare_output(path: Path) -> Path:
    if "\x00" in str(path):
        raise AppError("Caminho inválido.")
    target = path.expanduser()
    if not target.name or target.name in {".", ".."}:
        raise AppError("Informe o nome do arquivo.")
    if target.exists() and target.is_dir():
        raise AppError("Escolha um arquivo, não uma pasta.")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def assert_inside(root: Path, target: Path) -> Path:
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    if target_resolved != root_resolved and root_resolved not in target_resolved.parents:
        raise AppError("Esse caminho está fora da pasta permitida.")
    return target_resolved
