from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from congo_reunioes.parse import TRANSCRIPT_SUFFIXES, parse_transcript, read_transcript_file
from congo_reunioes.store import NoteStore

MAX_TRANSCRIPT_BYTES = 20 * 1024 * 1024
# Nomes que o Meet, o Teams e o Zoom dão ao arquivo da transcrição, em pt, en e es.
_TRANSCRIPT_WORDS = ("transcri", "transcript", "legenda", "captions")


@dataclass(frozen=True)
class FileResult:
    name: str
    status: str
    count: int = 0


def download_dir() -> Path:
    """Pasta Downloads do usuário, lida de ~/.config/user-dirs.dirs quando existe."""
    config = Path.home() / ".config" / "user-dirs.dirs"
    if config.is_file():
        for line in config.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("XDG_DOWNLOAD_DIR="):
                value = line.split("=", 1)[1].strip().strip('"')
                return Path(value.replace("$HOME", str(Path.home())))
    return Path.home() / "Downloads"


def looks_like_transcript(path: Path) -> bool:
    if path.suffix.lower() == ".vtt":
        return True
    name = path.name.lower()
    return any(word in name for word in _TRANSCRIPT_WORDS)


def import_file(store: NoteStore, path: Path, label: str) -> FileResult:
    if path.suffix.lower() not in TRANSCRIPT_SUFFIXES:
        return FileResult(path.name, "tipo não aceito")
    if path.stat().st_size > MAX_TRANSCRIPT_BYTES:
        return FileResult(path.name, "maior que 20 MB")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if store.already_imported(digest):
        return FileResult(path.name, "já importado")
    try:
        lines = parse_transcript(read_transcript_file(path))
    except ValueError as exc:
        return FileResult(path.name, str(exc))
    if not lines:
        return FileResult(path.name, "sem falas com nome")
    count = store.add(label, lines)
    store.mark_imported(digest, path.name)
    return FileResult(path.name, "importado", count)


def import_folder(store: NoteStore, folder: Path, label: str, every_file: bool = False) -> list[FileResult]:
    """Importa as transcrições de uma pasta, sem entrar em subpastas e sem repetir arquivo."""
    if not folder.is_dir():
        raise ValueError(f"Não achei a pasta: {folder}")
    results = []
    for path in sorted(folder.iterdir()):
        if path.name.startswith(".") or not path.is_file() or path.is_symlink():
            continue
        if path.suffix.lower() not in TRANSCRIPT_SUFFIXES:
            continue
        if not every_file and not looks_like_transcript(path):
            continue
        results.append(import_file(store, path, label))
    return results


def results_text(results: list[FileResult]) -> str:
    if not results:
        return (
            "Nenhuma transcrição nessa pasta. O nome do arquivo precisa ter Transcript, Transcrição ou "
            "ser .vtt. Para pegar qualquer arquivo de texto, use --todos."
        )
    lines = [f"{item.name}: {item.status}" + (f", {item.count} falas" if item.count else "") for item in results]
    total = sum(item.count for item in results)
    lines.append(f"Total: {total} falas novas.")
    return os.linesep.join(lines)
