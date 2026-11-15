"""Lê o texto da janela ativa de qualquer programa que exponha a árvore de acessibilidade.

A árvore é percorrida em largura controlada: o texto é coletado de nós de leitura,
campos de senha nunca são lidos e a saída tem limite de caracteres.
A ligação com o AT-SPI fica isolada em `_atspi_*` e só é carregada quando usada.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

READABLE_ROLES = frozenset({
    "paragraph", "heading", "label", "static", "text", "link", "caption",
    "document web", "document text", "document frame", "list item", "table cell",
    "push button", "check box", "radio button", "menu item", "page tab", "section",
})
SECRET_ROLES = frozenset({"password text"})
DEFAULT_LIMIT = 20000
MAX_DEPTH = 80


class AccessibilityUnavailable(RuntimeError):
    """A árvore de acessibilidade não pôde ser lida; a mensagem diz como resolver."""


def collect_text(
    root: Any,
    children: Callable[[Any], Iterable[Any]],
    role_of: Callable[[Any], str],
    text_of: Callable[[Any], str],
    limit: int = DEFAULT_LIMIT,
) -> str:
    """Percorre a árvore em profundidade, em ordem, e junta os textos legíveis."""
    parts: list[str] = []
    size = 0
    stack: list[tuple[Any, int]] = [(root, 0)]
    while stack and size < limit:
        node, depth = stack.pop()
        role = role_of(node)
        if role in SECRET_ROLES:
            continue
        if role in READABLE_ROLES:
            text = " ".join(text_of(node).split())
            if text and (not parts or parts[-1] != text):
                parts.append(text)
                size += len(text) + 1
        if depth < MAX_DEPTH:
            stack.extend((child, depth + 1) for child in reversed(list(children(node))))
    joined = "\n".join(parts)
    return joined[:limit]


def _atspi_module():
    try:
        import gi  # type: ignore[import-not-found]
        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi  # type: ignore[import-not-found]
    except (ImportError, ValueError):
        return None
    return Atspi


def _atspi_children(node: Any) -> list[Any]:
    try:
        count = node.get_child_count()
    except Exception:  # noqa: BLE001 - nó morto ou sem interface: ignora o ramo
        return []
    result = []
    for index in range(count):
        try:
            child = node.get_child_at_index(index)
        except Exception:  # noqa: BLE001
            continue
        if child is not None:
            result.append(child)
    return result


def _atspi_role(node: Any) -> str:
    try:
        return node.get_role_name() or ""
    except Exception:  # noqa: BLE001
        return ""


def _atspi_text(node: Any) -> str:
    try:
        text_iface = node.get_text()
    except Exception:  # noqa: BLE001
        text_iface = None
    if text_iface is not None:
        try:
            return text_iface.get_text(0, text_iface.get_character_count()) or ""
        except Exception:  # noqa: BLE001
            pass
    try:
        return node.get_name() or ""
    except Exception:  # noqa: BLE001
        return ""


def _active_window(atspi: Any) -> Any | None:
    desktop = atspi.get_desktop(0)
    for app in _atspi_children(desktop):
        for window in _atspi_children(app):
            try:
                if window.get_state_set().contains(atspi.StateType.ACTIVE):
                    return window
            except Exception:  # noqa: BLE001
                continue
    return None


def active_window_text(limit: int = DEFAULT_LIMIT) -> str:
    """Texto da janela que tem o foco agora, em qualquer programa."""
    atspi = _atspi_module()
    if atspi is None:
        raise AccessibilityUnavailable(
            "Não encontrei o AT-SPI neste sistema. Instale o pacote gir1.2-atspi-2.0 "
            "e ative a acessibilidade do sistema."
        )
    window = _active_window(atspi)
    if window is None:
        raise AccessibilityUnavailable(
            "Não encontrei uma janela ativa exposta pela acessibilidade. "
            "Em navegadores, ative a acessibilidade do sistema (AT-SPI) antes de tentar de novo."
        )
    return collect_text(window, _atspi_children, _atspi_role, _atspi_text, limit)
