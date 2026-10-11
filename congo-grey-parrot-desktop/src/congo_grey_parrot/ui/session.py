from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

from congo_grey_parrot.core.paths import app_data_dir, ensure_dir
from congo_grey_parrot.files.export_service import ExportService
from congo_grey_parrot.media.ffmpeg_service import FfmpegService
from congo_grey_parrot.models.service import ModelService
from congo_grey_parrot.persistence.database import Database
from congo_grey_parrot.speech.service import SpeechService
from congo_grey_parrot.transcription.service import TranscriptionService
from congo_grey_parrot.translation.service import TranslationService
from congo_grey_parrot.ui.bus import AppBus
from congo_grey_parrot.ui.tasks import TaskManager


class Session(QObject):
    def __init__(self, data_dir: Path):
        super().__init__()
        self.data_dir = ensure_dir(data_dir)
        self.db = Database(self.data_dir / "app.sqlite3")
        self.exporter = ExportService()
        self.media = FfmpegService()
        self.models = ModelService(self.data_dir / "vozes", self.data_dir / "whisper")
        self.models.extra_voices = self.places("voice_places")
        self.models.extra_whisper = self.places("whisper_places")
        self.transcription = TranscriptionService(self.models.whisper_root, roots=self.models.whisper_roots)
        self.speech = SpeechService()
        self.translation = TranslationService()
        self.tasks = TaskManager()
        self.bus = AppBus()
        ensure_dir(self.output_dir())
        ensure_dir(self.data_dir / "tmp")

    def places(self, key: str) -> list[Path]:
        raw = self.db.get_setting(key, "") or ""
        found = []
        for line in raw.splitlines():
            text = line.strip()
            if text:
                found.append(Path(text))
        return found

    def remember_place(self, key: str, path: Path) -> None:
        resolved = path.expanduser().resolve()
        current = []
        for item in self.places(key):
            try:
                current.append(item.expanduser().resolve())
            except OSError:
                continue
        if resolved not in current:
            current.append(resolved)
        self.db.set_setting(key, "\n".join(str(item) for item in current))
        if key == "voice_places":
            self.models.extra_voices = current
        if key == "whisper_places":
            self.models.extra_whisper = current

    def output_dir(self) -> Path:
        raw = self.db.get_setting("output_dir")
        path = Path(raw) if raw else self.data_dir / "saidas"
        return ensure_dir(path)

    def remember(self, kind: str, source_name: str, output_path: Path, detail: str = "") -> None:
        self.db.add_history(kind, source_name, str(output_path), "ok", detail)
        self.bus.history_changed.emit()


def build_session(data_dir: Path | None = None) -> Session:
    return Session(data_dir or app_data_dir())
