from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

    HAS_MEDIA = True
except ImportError:
    HAS_MEDIA = False


class DropFrame(QFrame):
    files_dropped = Signal(list)

    def __init__(self, text: str):
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("drop")
        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setMinimumHeight(90)

    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):  # noqa: N802
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        if paths:
            self.files_dropped.emit(paths)


class PlayerBar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.play_button = QPushButton("Reproduzir")
        self.stop_button = QPushButton("Parar")
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(50, 200)
        self.speed.setValue(100)
        self.speed_label = QLabel("1,0x")
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(QLabel("Velocidade"))
        layout.addWidget(self.speed, 1)
        layout.addWidget(self.speed_label)
        self._path: Path | None = None
        self.player = None
        self.audio = None
        self.play_button.clicked.connect(self.toggle)
        self.stop_button.clicked.connect(self.stop)
        self.speed.valueChanged.connect(self._on_speed)

    def _ensure_player(self) -> bool:
        if not HAS_MEDIA:
            return False
        if self.player is None:
            self.player = QMediaPlayer(self)
            self.audio = QAudioOutput(self)
            self.player.setAudioOutput(self.audio)
            self.audio.setVolume(1.0)
        return True

    def set_file(self, path: Path | None) -> None:
        self._path = path
        self.play_button.setText("Reproduzir")

    def toggle(self) -> None:
        if self._path is None or not self._ensure_player():
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("Continuar")
            return
        self.player.setSource(QUrl.fromLocalFile(str(self._path)))
        self.player.setPlaybackRate(self.speed.value() / 100)
        self.player.play()
        self.play_button.setText("Pausar")

    def stop(self) -> None:
        if self.player is not None:
            self.player.stop()
        self.play_button.setText("Reproduzir")

    def _on_speed(self, value: int) -> None:
        self.speed_label.setText(f"{value / 100:.1f}x".replace(".", ","))
        if self.player is not None:
            self.player.setPlaybackRate(value / 100)


class TaskPanel(QWidget):
    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        layout = QVBoxLayout(self)
        title = QLabel("Tarefas")
        title.setStyleSheet("font-weight: 700;")
        self.list = QListWidget()
        self.cancel_button = QPushButton("Cancelar selecionada")
        self.cancel_button.clicked.connect(self._cancel)
        layout.addWidget(title)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.cancel_button)
        self.tasks.updated.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for item in self.tasks.items:
            self.list.addItem(f"{item.title}: {item.message} ({item.progress}%)")
            self.list.item(self.list.count() - 1).setData(Qt.ItemDataRole.UserRole, item.id)

    def _cancel(self) -> None:
        current = self.list.currentItem()
        if current is not None:
            self.tasks.cancel(current.data(Qt.ItemDataRole.UserRole))
