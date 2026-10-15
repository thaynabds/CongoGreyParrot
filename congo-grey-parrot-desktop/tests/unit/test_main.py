import ctypes

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from congo_grey_parrot.main import XCB_CURSOR_HINT, xcb_cursor_message
from congo_grey_parrot.ui.session import Session
from congo_grey_parrot.ui.window import MainWindow


def test_xcb_cursor_message_when_library_is_missing(monkeypatch):
    monkeypatch.setattr("congo_grey_parrot.main.sys.platform", "linux")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def missing(_name):
        raise OSError("libxcb-cursor.so.0")

    monkeypatch.setattr(ctypes, "CDLL", missing)
    assert xcb_cursor_message() == XCB_CURSOR_HINT


def test_xcb_cursor_message_skips_offscreen(monkeypatch):
    monkeypatch.setattr("congo_grey_parrot.main.sys.platform", "linux")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    assert xcb_cursor_message() is None


def test_window_keeps_standard_controls_and_can_shrink(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Session(tmp_path))
    flags = window.windowFlags()
    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowMaximizeButtonHint
    assert flags & Qt.WindowType.WindowCloseButtonHint
    window.resize(800, 520)
    app.processEvents()
    assert window.width() <= 900
    assert window.height() <= 600
    assert window.minimumWidth() <= 720
    assert window.minimumHeight() <= 480
