from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
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


def icon_path() -> Path:
    return Path(__file__).resolve().parent / "ui" / "assets" / "icon.png"


def application_icon() -> QIcon:
    path = icon_path()
    if not path.is_file():
        return QIcon()
    source = QPixmap(str(path))
    if source.isNull():
        return QIcon()
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        icon.addPixmap(
            source.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    return icon


def desktop_path(path: Path) -> str:
    text = str(path)
    reserved = set(' \t\n"\'\\><~|&;$*?#()')
    if any(char in reserved for char in text):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def publish_launcher(icon: Path, root: Path | None = None) -> Path | None:
    if not icon.is_file():
        return None
    base = root or Path.home()
    icons = base / ".local" / "share" / "icons"
    apps = base / ".local" / "share" / "applications"
    icons.mkdir(parents=True, exist_ok=True)
    apps.mkdir(parents=True, exist_ok=True)
    stored = icons / "congo-grey-parrot.png"
    if icon.resolve() != stored.resolve():
        stored.write_bytes(icon.read_bytes())
    executable = Path(sys.argv[0]).resolve()
    if not os.access(executable, os.X_OK):
        executable = Path(sys.executable).resolve()
    desktop = apps / "congo-grey-parrot.desktop"
    desktop.write_text(
        "\n".join(
            (
                "[Desktop Entry]",
                "Type=Application",
                "Name=Congo Grey Parrot",
                "Comment=Transcrição e leitura local",
                f"Exec={desktop_path(executable)}",
                f"Icon={stored}",
                "Terminal=false",
                "Categories=AudioVideo;Audio;",
                "StartupWMClass=congo-grey-parrot",
                "",
            )
        ),
        encoding="utf-8",
    )
    return desktop


def main() -> int:
    notice = xcb_cursor_message()
    if notice:
        print(notice, file=sys.stderr)
        return 1
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Congo Grey Parrot")
    app.setDesktopFileName("congo-grey-parrot")
    icon = application_icon()
    app.setWindowIcon(icon)
    publish_launcher(icon_path())
    app.setStyle("Fusion")
    session = build_session()
    scale = float(session.db.get_setting("font_scale", "1") or "1")
    apply_theme(app, session.db.get_setting("theme", "light") or "light", scale)
    window = MainWindow(session)
    window.setWindowIcon(app.windowIcon())
    window.show()
    return app.exec()
