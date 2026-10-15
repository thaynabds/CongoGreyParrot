import ctypes

from congo_grey_parrot.main import XCB_CURSOR_HINT, xcb_cursor_message


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
