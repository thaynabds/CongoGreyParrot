from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class AppBus(QObject):
    open_page = Signal(str)
    import_files = Signal(list)
    open_speech_text = Signal(str)
    open_subtitles = Signal(object)
    history_changed = Signal()
    theme_changed = Signal(str)
