from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF


def nav_icon(key: str, color: str) -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.setBrush(QColor(color))
    _draw(painter, key)
    painter.end()
    return QIcon(pixmap)


_ICON = {
    "dark": "#d7f3e6",
    "high_contrast": "#ffff00",
    "kuro": "#d7c4f5",
    "pink_void": "#f7c4dc",
    "red_void": "#f7c4c4",
    "yellow_void": "#f3e0a0",
}
_ICON_SMART = {
    "dark": "#1b6b45",
    "high_contrast": "#0000ff",
    "kuro": "#4c2880",
    "pink_void": "#8a2460",
    "red_void": "#8a2424",
    "yellow_void": "#5c4808",
    "light": "#d7f3e6",
}


def icon_color(mode: str, color_filter: str = "none") -> str:
    if color_filter == "smart_invert":
        return _ICON_SMART.get(mode, "#d7f3e6")
    return _ICON.get(mode, "#1b6b45")


def _draw(painter: QPainter, key: str) -> None:
    if key == "home":
        painter.drawPolygon(QPolygonF([QPointF(16, 4), QPointF(28, 14), QPointF(24, 14), QPointF(24, 28), QPointF(8, 28), QPointF(8, 14), QPointF(4, 14)]))
    elif key == "transcribe":
        painter.drawRoundedRect(QRectF(12, 6, 8, 12), 4, 4)
        painter.drawArc(QRectF(8, 10, 16, 12), 0, -180 * 16)
        painter.drawLine(16, 22, 16, 27)
    elif key == "speech":
        painter.drawRoundedRect(QRectF(4, 6, 14, 20), 2, 2)
        painter.drawLine(22, 10, 28, 10)
        painter.drawLine(22, 16, 28, 16)
        painter.drawLine(22, 22, 28, 22)
    elif key == "translate":
        painter.drawLine(6, 12, 22, 12)
        painter.drawLine(16, 6, 24, 12)
        painter.drawLine(16, 18, 24, 12)
        painter.drawLine(26, 20, 10, 20)
        painter.drawLine(16, 14, 8, 20)
        painter.drawLine(16, 26, 8, 20)
    elif key == "subtitles":
        painter.drawRoundedRect(QRectF(4, 8, 24, 16), 2, 2)
        painter.drawLine(8, 14, 24, 14)
        painter.drawLine(8, 19, 18, 19)
    elif key == "convert":
        painter.drawArc(QRectF(6, 6, 20, 20), 40 * 16, 260 * 16)
        painter.drawPolygon(QPolygonF([QPointF(22, 4), QPointF(28, 10), QPointF(18, 10)]))
    elif key == "documents":
        painter.drawRoundedRect(QRectF(7, 4, 16, 24), 2, 2)
        painter.drawLine(11, 11, 19, 11)
        painter.drawLine(11, 16, 19, 16)
        painter.drawLine(11, 21, 16, 21)
    elif key == "library":
        painter.drawRect(QRectF(5, 8, 6, 18))
        painter.drawRect(QRectF(13, 6, 6, 20))
        painter.drawRect(QRectF(21, 10, 6, 16))
    elif key == "models":
        painter.drawRoundedRect(QRectF(6, 10, 20, 14), 2, 2)
        painter.drawLine(6, 16, 26, 16)
        painter.drawLine(16, 10, 16, 24)
    elif key == "history":
        painter.drawEllipse(QRectF(5, 5, 22, 22))
        painter.drawLine(16, 16, 16, 9)
        painter.drawLine(16, 16, 22, 18)
    else:
        painter.drawEllipse(QRectF(10, 10, 12, 12))
        painter.drawEllipse(QRectF(4, 4, 24, 24))
