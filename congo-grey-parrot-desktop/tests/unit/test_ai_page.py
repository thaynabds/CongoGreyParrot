import json

from PySide6.QtWidgets import QApplication, QPushButton

from congo_grey_parrot.ui.session import Session
from congo_grey_parrot.ui.window import MainWindow


def test_ai_conector_page_is_in_the_menu_and_connects(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    monkeypatch.setattr("congo_grey_parrot.ui.ai_page.confirm", lambda *_: True)
    monkeypatch.setattr("congo_grey_parrot.ui.ai_page.info", lambda *_: None)
    QApplication.instance() or QApplication([])
    window = MainWindow(Session(tmp_path / "dados"))
    assert window._buttons["ai"].text() == "AI Conector"
    page = window.pages["ai"]
    assert "não conectado" in page.status.text()
    assert "gerar_legenda" in page.details.toPlainText()
    connect = next(b for b in page.findChildren(QPushButton) if b.text().startswith("Conectar"))
    connect.click()
    assert "Claude Desktop: conectado" in page.status.text()
    data = json.loads((tmp_path / "cfg" / "Claude" / "claude_desktop_config.json").read_text(encoding="utf-8"))
    assert "congo-desktop" in data["mcpServers"]
    assert "congo-desktop" in json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]
