from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
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

_NAV_HIDE_THRESHOLD = 620
_TASKS_HIDE_THRESHOLD = 860
_NAV_WIDTH = 200
_TASKS_WIDTH = 220


class MainWindow(QMainWindow):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self._nav_visible = True
        self._tasks_visible = True
        self.setWindowTitle("Project Congo Grey Parrot")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(520, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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

        # Nav sidebar
        self._nav_frame = QFrame()
        self._nav_frame.setObjectName("nav")
        nav_layout = QVBoxLayout(self._nav_frame)
        nav_layout.setContentsMargins(4, 8, 4, 8)
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

        # Tasks sidebar
        self._tasks_frame = QFrame()
        self._tasks_frame.setObjectName("tasks")
        task_layout = QVBoxLayout(self._tasks_frame)
        task_layout.addWidget(TaskPanel(session.tasks))

        # Toggle buttons for sidebars
        self._nav_toggle = QPushButton("☰")
        self._nav_toggle.setFixedSize(34, 34)
        self._nav_toggle.setToolTip("Mostrar/ocultar menu lateral")
        self._nav_toggle.clicked.connect(self._toggle_nav)

        self._tasks_toggle = QPushButton("✦")
        self._tasks_toggle.setFixedSize(34, 34)
        self._tasks_toggle.setToolTip("Mostrar/ocultar painel de tarefas")
        self._tasks_toggle.clicked.connect(self._toggle_tasks)

        # Top bar with toggle buttons
        top_bar = QWidget()
        top_bar.setFixedHeight(42)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(4, 4, 4, 4)
        top_layout.addWidget(self._nav_toggle)
        top_layout.addStretch(1)
        top_layout.addWidget(self._tasks_toggle)

        # Splitter: nav | content | tasks
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(self._nav_frame)
        self._splitter.addWidget(self.stack)
        self._splitter.addWidget(self._tasks_frame)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 0)
        self._splitter.setSizes([_NAV_WIDTH, 600, _TASKS_WIDTH])
        self._splitter.setCollapsible(0, True)
        self._splitter.setCollapsible(1, False)
        self._splitter.setCollapsible(2, True)
        self._splitter.setChildrenCollapsible(True)

        # Root layout
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(top_bar)
        root_layout.addWidget(self._splitter, 1)

        self.setCentralWidget(root)
        self._apply_nav_icons()
        session.bus.theme_changed.connect(self._apply_nav_icons)
        self._fit_to_screen()
        self._apply_saved_filter()
        session.bus.open_page.connect(self.show_page)
        session.bus.import_files.connect(self._import)
        session.bus.open_speech_text.connect(self._speech_text)
        session.bus.open_subtitles.connect(self._subtitles)
        session.bus.history_changed.connect(self.home.refresh)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(520, 400)

    def _fit_to_screen(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            self.resize(1100, 700)
            return
        area = screen.availableGeometry()
        w = min(1100, max(self.minimumWidth(), area.width() - 48))
        h = min(700, max(self.minimumHeight(), area.height() - 48))
        self.resize(w, h)
        self._update_panels_for_width(w)

    def _toggle_nav(self) -> None:
        sizes = self._splitter.sizes()
        if sizes[0] > 0:
            self._splitter.setSizes([0, sizes[1] + sizes[0], sizes[2]])
            self._nav_visible = False
        else:
            total = sum(sizes)
            nav_w = min(_NAV_WIDTH, total // 4)
            self._splitter.setSizes([nav_w, total - nav_w - sizes[2], sizes[2]])
            self._nav_visible = True

    def _toggle_tasks(self) -> None:
        sizes = self._splitter.sizes()
        if sizes[2] > 0:
            self._splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
            self._tasks_visible = False
        else:
            total = sum(sizes)
            tasks_w = min(_TASKS_WIDTH, total // 4)
            self._splitter.setSizes([sizes[0], total - sizes[0] - tasks_w, tasks_w])
            self._tasks_visible = True

    def _update_panels_for_width(self, w: int) -> None:
        sizes = self._splitter.sizes()
        if w < _TASKS_HIDE_THRESHOLD and sizes[2] > 0:
            self._splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
            self._tasks_visible = False
        elif w >= _TASKS_HIDE_THRESHOLD and sizes[2] == 0 and self._tasks_visible:
            total = sum(sizes)
            tasks_w = _TASKS_WIDTH
            self._splitter.setSizes([sizes[0], total - sizes[0] - tasks_w, tasks_w])
        if w < _NAV_HIDE_THRESHOLD and sizes[0] > 0:
            self._splitter.setSizes([0, sizes[1] + sizes[0], self._splitter.sizes()[2]])
            self._nav_visible = False
        elif w >= _NAV_HIDE_THRESHOLD and sizes[0] == 0 and self._nav_visible:
            total = sum(self._splitter.sizes())
            nav_w = _NAV_WIDTH
            curr = self._splitter.sizes()
            self._splitter.setSizes([nav_w, total - nav_w - curr[2], curr[2]])

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_panels_for_width(event.size().width())

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
