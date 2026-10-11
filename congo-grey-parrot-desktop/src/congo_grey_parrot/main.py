from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from congo_grey_parrot.ui.session import build_session
from congo_grey_parrot.ui.theme import apply_theme
from congo_grey_parrot.ui.window import MainWindow


def application_icon() -> QIcon:
    path = Path(__file__).resolve().parent / "ui" / "assets" / "icon.png"
    if not path.is_file():
        return QIcon()
    return QIcon(str(path))


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Project Congo Grey Parrot")
    app.setWindowIcon(application_icon())
    app.setStyle("Fusion")
    session = build_session()
    scale = float(session.db.get_setting("font_scale", "1") or "1")
    apply_theme(app, session.db.get_setting("theme", "light") or "light", scale)
    window = MainWindow(session)
    window.setWindowIcon(app.windowIcon())
    window.show()
    return app.exec()
