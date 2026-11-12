"""Página AI Conector: liga uma IA (Claude Desktop, Cursor, Claude Code) a este programa por MCP."""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from congo_grey_parrot.aiconector import conector
from congo_grey_parrot.ui.dialogs import confirm, info, warn

NAME = "congo-desktop"
TITLE = "AI Conector"


def _prepare() -> None:
    from congo_grey_parrot.mcp_server import self_entry

    conector.use_entry(NAME, self_entry())


def _tools() -> list[str]:
    try:
        from congo_grey_parrot.mcp_server import build_server

        return conector.tool_lines(build_server())
    except Exception:  # sem o pacote mcp, a página ainda mostra como instalar
        return []


class AIConnectorPage(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        _prepare()
        layout = QVBoxLayout(self)
        heading = QLabel(TITLE)
        heading.setAccessibleName(TITLE)
        heading.setStyleSheet("font-weight: 700; font-size: 1.3em;")
        hint = QLabel(
            "Ligue uma IA a este programa por MCP. Conectada, ela transcreve, legenda, traduz, lê em voz alta, "
            "resume, converte mídia, salva documentos, baixa modelos e vozes, vê o histórico e muda as configurações. "
            "Tudo fica neste computador: só stdio, nenhuma porta de rede aberta, arquivos só da sua pasta pessoal "
            "e nada é apagado sem a IA pedir sua confirmação."
        )
        hint.setWordWrap(True)
        self.status = QLabel()
        self.status.setWordWrap(True)
        row = QHBoxLayout()
        connect = QPushButton("Conectar ao Claude Desktop e Cursor")
        connect.clicked.connect(self._connect)
        disconnect = QPushButton("Desconectar")
        disconnect.clicked.connect(self._disconnect)
        copy_json = QPushButton("Copiar configuração MCP")
        copy_json.clicked.connect(lambda: self._copy(conector.snippet(NAME)))
        copy_cli = QPushButton("Copiar comando do Claude Code")
        copy_cli.clicked.connect(lambda: self._copy(conector.claude_code_command(NAME)))
        for button in (connect, disconnect, copy_json, copy_cli):
            button.setAccessibleName(button.text())
            row.addWidget(button)
        row.addStretch(1)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setAccessibleName("Detalhes do AI Conector")
        layout.addWidget(heading)
        layout.addWidget(hint)
        layout.addWidget(self.status)
        layout.addLayout(row)
        layout.addWidget(self.details, 1)
        self.refresh()

    def refresh(self) -> None:
        state = conector.status(NAME)
        yes = {True: "conectado", False: "não conectado"}
        self.status.setText(f"Claude Desktop: {yes[state['claude_desktop']]} · Cursor: {yes[state['cursor']]}")
        tools = _tools()
        body = [
            "Claude Code (cole no terminal):",
            conector.claude_code_command(NAME),
            "",
            "Outro cliente MCP (cole na configuração dele):",
            conector.snippet(NAME),
            "",
        ]
        if tools:
            body += ["O que a IA pode fazer aqui:", *tools]
        else:
            body.append("O pacote mcp não está nesta instalação. No código-fonte: pip install '.[mcp]'.")
        self.details.setPlainText("\n".join(body))

    def _connect(self) -> None:
        if not confirm(self, "Registrar o Congo Grey Parrot no Claude Desktop e no Cursor deste computador?"):
            return
        try:
            info(self, conector.connect(NAME))
        except (OSError, ValueError) as exc:
            warn(self, f"Não consegui gravar a configuração: {exc}")
        self.refresh()

    def _disconnect(self) -> None:
        try:
            info(self, conector.disconnect(NAME))
        except (OSError, ValueError) as exc:
            warn(self, f"Não consegui gravar a configuração: {exc}")
        self.refresh()

    def _copy(self, text: str) -> None:
        if not text:
            warn(self, "O servidor MCP ainda não foi instalado.")
            return
        QGuiApplication.clipboard().setText(text)
        info(self, "Copiado.")
