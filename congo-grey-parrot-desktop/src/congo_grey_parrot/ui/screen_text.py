"""Texto que está visível na tela, para ser lido em voz alta."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QTextEdit, QWidget

_TEXT_WIDGETS = (QLabel, QTextEdit, QPlainTextEdit)  # QTextBrowser herda de QTextEdit


def _label_text(label: QLabel) -> str:
    text = label.text()
    if label.textFormat() == Qt.TextFormat.PlainText or "<" not in text:
        return text
    document = QTextDocument()
    document.setHtml(text)
    return document.toPlainText()


def selected_text(widget: QWidget | None) -> str:
    """Seleção do campo de texto com foco, ou string vazia."""
    if isinstance(widget, (QTextEdit, QPlainTextEdit)):
        cursor = widget.textCursor()
        if cursor.hasSelection():
            return cursor.selectedText().replace(" ", "\n").strip()
    return ""


def visible_text(root: QWidget | None) -> str:
    """Textos visíveis dentro de `root`, na ordem em que aparecem, sem repetir."""
    if root is None:
        return ""
    parts: list[str] = []
    for widget in root.findChildren(QWidget):
        if not isinstance(widget, _TEXT_WIDGETS) or not widget.isVisibleTo(root):
            continue
        if isinstance(widget, QLabel):
            text = _label_text(widget)
        else:
            text = widget.toPlainText()
        text = text.strip()
        if text and text not in parts:
            parts.append(text)
    return "\n".join(parts)


def text_to_read(root: QWidget | None) -> str:
    """Seleção, se houver; senão, tudo o que está visível na tela."""
    return selected_text(QApplication.focusWidget()) or visible_text(root)
