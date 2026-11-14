import pytest

from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QTextEdit, QVBoxLayout, QWidget

from congo_grey_parrot.ui.screen_text import selected_text, visible_text


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _page(app):
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel("Título visível"))
    layout.addWidget(QLabel("<b>Negrito</b> e <i>itálico</i>"))
    hidden = QLabel("Escondido")
    hidden.setVisible(False)
    layout.addWidget(hidden)
    editor = QPlainTextEdit("Corpo do texto")
    layout.addWidget(editor)
    summary = QTextEdit()
    summary.setPlainText("Resumo: <p>sem HTML aqui</p>")
    layout.addWidget(summary)
    layout.addWidget(QLabel("   "))
    return page, editor


def test_visible_text_keeps_order_skips_hidden_and_strips_html(app):
    page, _ = _page(app)
    text = visible_text(page)
    assert text.splitlines() == [
        "Título visível",
        "Negrito e itálico",
        "Corpo do texto",
        "Resumo: <p>sem HTML aqui</p>",
    ]


def test_visible_text_of_nothing_is_empty(app):
    assert visible_text(None) == ""
    assert visible_text(QWidget()) == ""


def test_selected_text_reads_only_an_actual_selection(app):
    editor = QPlainTextEdit("abcdef")
    assert selected_text(editor) == ""
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(3, cursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    assert selected_text(editor) == "abc"
    assert selected_text(QLabel("x")) == ""


def test_ler_a_tela_manda_o_texto_visivel_para_a_leitura(tmp_path, monkeypatch):
    from congo_grey_parrot.ui.session import Session
    from congo_grey_parrot.ui.window import MainWindow

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Session(tmp_path / "dados"))
    window.show_page("summary")
    window.summary.set_text("Decisão: publicar na sexta.")
    spoken = []
    monkeypatch.setattr(window.speech, "read_text", lambda text: spoken.append(text))
    monkeypatch.setattr("congo_grey_parrot.ui.window.warn", lambda *_: spoken.append("AVISO"))
    window.read_screen()
    assert window.stack.currentWidget() is window.speech
    assert spoken and "Decisão: publicar na sexta." in spoken[0]
    assert "AVISO" not in spoken
    assert window._read_screen_button.text() == "Ler a tela"
    window.close()
