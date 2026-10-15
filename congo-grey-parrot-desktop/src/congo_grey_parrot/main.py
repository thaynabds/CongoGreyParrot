from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from congo_grey_parrot.ui.session import build_session
from congo_grey_parrot.ui.theme import apply_theme
from congo_grey_parrot.ui.window import MainWindow

XCB_CURSOR_HINT = (
    "Falta a biblioteca libxcb-cursor0. O Qt, a partir da versão 6.5, "
    "precisa dela para abrir a janela no Linux.\n"
    "sudo apt install libxcb-cursor0"
)


def xcb_cursor_message() -> str | None:
    if sys.platform != "linux":
        return None
    platform = os.environ.get("QT_QPA_PLATFORM", "").split(":", 1)[0]
    if platform in {"offscreen", "minimal", "minimalegl", "vnc", "eglfs", "linuxfb"}:
        return None
    if platform.startswith("wayland"):
        return None
    if not platform and os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
        return None
    try:
        ctypes.CDLL("libxcb-cursor.so.0")
    except OSError:
        return XCB_CURSOR_HINT
    return None


def application_icon() -> QIcon:
    path = Path(__file__).resolve().parent / "ui" / "assets" / "icon.png"
    if not path.is_file():
        return QIcon()
    return QIcon(str(path))


def main() -> int:
    notice = xcb_cursor_message()
    if notice:
        print(notice, file=sys.stderr)
        return 1
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
