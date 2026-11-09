from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QGraphicsEffect

from congo_grey_parrot.ui.color_filter import FILTERS, invert_hex_colors

THEMES = (
    "light",
    "dark",
    "high_contrast",
    "high_contrast_light",
    "kuro",
    "kuro_light",
    "pink_void",
    "pink_void_light",
    "red_void",
    "red_void_light",
    "yellow_void",
    "yellow_void_light",
    "green_void",
    "green_void_light",
    "blue_void",
    "blue_void_light",
)

# bg, surface, text, accent, primary, nav, field, border, text on accent
_DARK_SHEETS = {
    "dark": ("#121816", "#1b2621", "#eef5f1", "#9fd8bc", "#2f9e6b", "#17382c", "#0d1210", "#2a3b34", "#ffffff"),
    "kuro": ("#100e16", "#1c1730", "#f4eefe", "#6d46c2", "#5534a8", "#171228", "#0c0a12", "#3a2d58", "#ffffff"),
    "pink_void": ("#160e12", "#2a1520", "#fbeff4", "#b43b78", "#9a2864", "#241018", "#100a0e", "#5a3048", "#ffffff"),
    "red_void": ("#160e0e", "#2a1515", "#fbeeee", "#b43b3b", "#8e2424", "#240f0f", "#100a0a", "#5a3030", "#ffffff"),
    "yellow_void": ("#14120c", "#262014", "#fbf6e8", "#e6c200", "#c9a227", "#221e12", "#100e0a", "#5a4c28", "#1a1404"),
    "green_void": ("#0c140e", "#142a1a", "#eefbf1", "#2f9e5a", "#237a44", "#0f2416", "#0a100c", "#2c5a3a", "#ffffff"),
    "blue_void": ("#0c1016", "#14202f", "#eef4fb", "#3b78b4", "#285f9a", "#101c28", "#0a0e12", "#2f4a66", "#ffffff"),
}

_LIGHT_SHEETS = {
    "kuro_light": ("#f5f1fd", "#ffffff", "#1f1833", "#5534a8", "#5534a8", "#ebe3fa", "#faf7ff", "#d9cdf0", "#ffffff"),
    "pink_void_light": ("#fdf1f6", "#ffffff", "#2f1420", "#9a2864", "#9a2864", "#fae3ec", "#fff8fb", "#f0cfde", "#ffffff"),
    "red_void_light": ("#fdf1f1", "#ffffff", "#2f1414", "#8e2424", "#8e2424", "#fae3e3", "#fff8f8", "#f0cfcf", "#ffffff"),
    "yellow_void_light": ("#fdf8e6", "#ffffff", "#2b2408", "#6b5600", "#6b5600", "#f8efcb", "#fffcf0", "#ecdfae", "#ffffff"),
    "green_void_light": ("#effaf1", "#ffffff", "#12291a", "#1a6b35", "#1a6b35", "#dff3e5", "#f7fdf8", "#c6e8d0", "#ffffff"),
    "blue_void_light": ("#eff5fd", "#ffffff", "#12203a", "#1f55a8", "#1f55a8", "#deeafa", "#f7faff", "#c8d9f2", "#ffffff"),
}


def build_stylesheet(mode: str) -> str:
    if mode in _DARK_SHEETS:
        return _sheet(*_DARK_SHEETS[mode])
    if mode in _LIGHT_SHEETS:
        return _sheet(*_LIGHT_SHEETS[mode])
    if mode == "high_contrast_light":
        return _contrast_sheet("#ffffff", "#000000", "#0000ff", "#ffffff")
    if mode == "high_contrast":
        return _contrast_sheet("#000000", "#ffffff", "#ffff00", "#000000")
    return _sheet("#f4f7f5", "#ffffff", "#1c2420", "#1b6b45", "#1b6b45", "#e5f3ec", "#f7faf8", "#d5e4dc")


def _contrast_sheet(bg: str, text: str, accent: str, on_accent: str) -> str:
    return f"""
        QWidget {{ background: {bg}; color: {text}; }}
        QLabel, QCheckBox, QRadioButton {{ background: transparent; color: {text}; }}
        QLineEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget, QSpinBox, QDoubleSpinBox {{
            background: {bg}; color: {text}; border: 2px solid {accent};
        }}
        QPushButton {{
            background: {bg}; color: {text}; border: 2px solid {accent}; padding: 8px 12px;
        }}
        QPushButton:checked, QPushButton#primary {{ background: {accent}; color: {on_accent}; }}
        QFrame#nav QPushButton {{ text-align: left; padding: 8px 10px; }}
        QFrame#nav QPushButton:checked {{ background: transparent; color: {text}; border: 2px solid {accent}; }}
        QHeaderView::section {{ background: {bg}; color: {text}; border: 1px solid {accent}; }}
        QScrollBar {{ background: {bg}; }}
        """


def _sheet(bg: str, surface: str, text: str, accent: str, primary: str, nav: str, field: str, border: str, on_accent: str = "#ffffff") -> str:
    return f"""
    QWidget {{ background: {bg}; color: {text}; }}
    QMainWindow, QDialog {{ background: {bg}; }}
    QFrame#nav, QFrame#tasks {{ background: {nav}; }}
    QLabel {{ background: transparent; }}
    QLineEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget, QSpinBox, QDoubleSpinBox {{
        background: {field}; color: {text}; border: 1px solid {border}; padding: 6px;
    }}
    QPushButton {{
        background: {surface}; color: {text}; border: 1px solid {border}; padding: 8px 12px;
    }}
    QPushButton:checked {{ background: {accent}; color: {on_accent}; }}
    QFrame#nav QPushButton {{ text-align: left; padding: 8px 10px; }}
    QFrame#nav QPushButton:checked {{ background: transparent; color: {text}; border: 2px solid {primary}; }}
    QPushButton#primary {{ background: {primary}; color: {on_accent}; border: none; }}
    QHeaderView::section {{ background: {surface}; color: {text}; border: 1px solid {border}; padding: 4px; }}
    QTableWidget {{ gridline-color: {border}; }}
    """


class _ScreenFilter(QGraphicsEffect):
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def draw(self, painter: QPainter) -> None:
        offset = QPoint()
        pixmap = self.sourcePixmap(Qt.CoordinateSystem.LogicalCoordinates, offset)
        if pixmap.isNull():
            return
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        painted, hold = _recolor(image, self._name)
        self._hold = hold
        painter.drawImage(offset, painted)


def _recolor(image: QImage, name: str):
    import numpy as np

    width = image.width()
    height = image.height()
    stride = image.bytesPerLine()
    raw = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(height, stride).copy()
    frame = raw[:, : width * 4].reshape(height, width, 4)
    matrix, shift = _matrix_of(name)
    mixed = frame[:, :, :3].astype(np.float32) / 255.0
    mixed = mixed @ matrix.T + shift
    np.clip(mixed, 0.0, 1.0, out=mixed)
    frame[:, :, :3] = np.rint(mixed * 255.0).astype(np.uint8)
    painted = QImage(raw.data, width, height, stride, QImage.Format.Format_RGBA8888)
    return painted, raw


def _matrix_of(name: str):
    import numpy as np

    from congo_grey_parrot.ui.color_filter import android_color_matrix

    values = android_color_matrix(name)
    if values is None:
        return np.eye(3, dtype=np.float32), np.zeros(3, dtype=np.float32)
    matrix = np.array(
        [
            [values[0], values[1], values[2]],
            [values[5], values[6], values[7]],
            [values[10], values[11], values[12]],
        ],
        dtype=np.float32,
    )
    offset = np.array([values[4], values[9], values[14]], dtype=np.float32) / 255.0
    return matrix, offset


def install_color_filter(root, name: str) -> None:
    if root is None:
        return
    if name not in _PIXEL_FILTERS:
        root._color_filter_effect = None
        root.setGraphicsEffect(None)
        return
    effect = _ScreenFilter(name)
    root._color_filter_effect = effect
    root.setGraphicsEffect(effect)


_PIXEL_FILTERS = {"invert", "protanopia", "deuteranopia", "tritanopia", "grayscale"}


def apply_theme(app, mode: str, scale: float, color_filter: str = "none", root=None) -> None:
    if mode not in THEMES:
        mode = "light"
    if color_filter not in FILTERS:
        color_filter = "none"
    sheet = build_stylesheet(mode)
    if color_filter == "smart_invert":
        sheet = invert_hex_colors(sheet)
    app.setStyleSheet(sheet)
    base = app.property("base_point_size")
    if not base:
        base = app.font().pointSizeF()
        if base <= 0:
            base = 11.0
        app.setProperty("base_point_size", float(base))
        base = float(base)
    font = app.font()
    font.setPointSizeF(float(base) * float(scale))
    app.setFont(font)
    install_color_filter(root, color_filter)
