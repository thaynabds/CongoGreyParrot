from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from congo_grey_parrot.files.naming import classify
from congo_grey_parrot.ui.extra_pages import (
    ConvertPage,
    DocumentsPage,
    HistoryPage,
    LibraryPage,
    ModelsPage,
    SettingsPage,
)
from congo_grey_parrot.ui.marks import icon_color, nav_icon
from congo_grey_parrot.ui.widgets import TaskPanel
from congo_grey_parrot.ui.work_pages import HomePage, SpeechPage, SubtitlePage, TranscribePage, TranslatePage


class MainWindow(QMainWindow):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Project Congo Grey Parrot")
        self.resize(1200, 760)
        self.stack = QStackedWidget()
        self.home = HomePage(session)
        self.transcribe = TranscribePage(session)
        self.speech = SpeechPage(session)
        self.translate = TranslatePage(session)
        self.subtitles = SubtitlePage(session)
        self.pages = {
            "home": self.home,
            "transcribe": self.transcribe,
            "speech": self.speech,
            "translate": self.translate,
            "subtitles": self.subtitles,
            "convert": ConvertPage(session),
            "documents": DocumentsPage(session),
            "library": LibraryPage(session),
            "models": ModelsPage(session),
            "history": HistoryPage(session),
            "settings": SettingsPage(session),
        }
        labels = (
            ("home", "Início"),
            ("transcribe", "Transcrever"),
            ("speech", "Texto para voz"),
            ("translate", "Traduzir"),
            ("subtitles", "Legendas"),
            ("convert", "Converter mídia"),
            ("documents", "Documentos"),
            ("library", "Biblioteca"),
            ("models", "Modelos e vozes"),
            ("history", "Histórico"),
            ("settings", "Configurações"),
        )
        nav = QFrame()
        nav.setObjectName("nav")
        nav_layout = QVBoxLayout(nav)
        group = QButtonGroup(self)
        group.setExclusive(True)
        self._buttons = {}
        for key, label in labels:
            self.stack.addWidget(self.pages[key])
            button = QPushButton(label)
            button.setCheckable(True)
            button.setAccessibleName(label)
            button.setIconSize(QSize(22, 22))
            button.clicked.connect(lambda _checked=False, name=key: self.show_page(name))
            group.addButton(button)
            nav_layout.addWidget(button)
            self._buttons[key] = button
        nav_layout.addStretch(1)
        self._buttons["home"].setChecked(True)
        tasks = QFrame()
        tasks.setObjectName("tasks")
        task_layout = QVBoxLayout(tasks)
        task_layout.addWidget(TaskPanel(session.tasks))
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.addWidget(nav)
        layout.addWidget(self.stack, 1)
        layout.addWidget(tasks)
        nav.setFixedWidth(236)
        self._apply_nav_icons()
        session.bus.theme_changed.connect(self._apply_nav_icons)
        tasks.setFixedWidth(260)
        self.setCentralWidget(root)
        self._apply_saved_filter()
        session.bus.open_page.connect(self.show_page)
        session.bus.import_files.connect(self._import)
        session.bus.open_speech_text.connect(self._speech_text)
        session.bus.open_subtitles.connect(self._subtitles)
        session.bus.history_changed.connect(self.home.refresh)

    def _apply_saved_filter(self) -> None:
        from PySide6.QtWidgets import QApplication

        from congo_grey_parrot.ui.theme import apply_theme

        mode = self.session.db.get_setting("theme", "light") or "light"
        scale = float(self.session.db.get_setting("font_scale", "1") or "1")
        color_filter = self.session.db.get_setting("color_filter", "none") or "none"
        apply_theme(QApplication.instance(), mode, scale, color_filter, self.centralWidget())

    def _apply_nav_icons(self, mode: str | None = None) -> None:
        chosen = mode or self.session.db.get_setting("theme", "light") or "light"
        color_filter = self.session.db.get_setting("color_filter", "none") or "none"
        color = icon_color(chosen, color_filter)
        for key, button in self._buttons.items():
            button.setIcon(nav_icon(key, color))

    def show_page(self, name: str) -> None:
        page = self.pages.get(name)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        button = self._buttons.get(name)
        if button is not None:
            button.setChecked(True)
        if name == "library":
            page.refresh()
        if name == "speech":
            page.reload_voices()
        if name == "home":
            page.refresh()
        if name == "models":
            page.refresh()

    def _import(self, paths: list) -> None:
        grouped = {"audio": [], "video": [], "text": [], "subtitle": [], "unknown": []}
        for raw in paths:
            path = Path(raw)
            grouped[classify(path)].append(str(path))
        media = grouped["audio"] + grouped["video"]
        if media:
            self.transcribe.add_files(media)
            self.show_page("transcribe")
            return
        if grouped["subtitle"]:
            self._open_subtitle_file(Path(grouped["subtitle"][0]))
            return
        if grouped["text"]:
            self.show_page("documents")

    def _open_subtitle_file(self, path: Path) -> None:
        from congo_grey_parrot.core.errors import AppError
        from congo_grey_parrot.subtitles.codec import load_subtitle_file
        from congo_grey_parrot.ui.dialogs import warn

        try:
            transcript = load_subtitle_file(path)
        except AppError as exc:
            warn(self, str(exc))
            return
        self.subtitles.load_transcript(transcript)
        self.show_page("subtitles")

    def _speech_text(self, text: str) -> None:
        self.speech.set_text(text)
        self.show_page("speech")

    def _subtitles(self, transcript) -> None:
        self.subtitles.load_transcript(transcript)
        self.show_page("subtitles")

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.show_page("home")
            return
        super().keyPressEvent(event)
