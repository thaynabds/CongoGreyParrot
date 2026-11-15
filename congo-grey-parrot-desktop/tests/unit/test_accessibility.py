from dataclasses import dataclass, field
from pathlib import Path

import pytest

from congo_grey_parrot.screen import cli
from congo_grey_parrot.screen.accessibility import AccessibilityUnavailable, collect_text


@dataclass
class Node:
    role: str
    text: str = ""
    children: list = field(default_factory=list)


def _collect(root, limit=20000):
    return collect_text(
        root,
        children=lambda node: node.children,
        role_of=lambda node: node.role,
        text_of=lambda node: node.text,
        limit=limit,
    )


def test_coleta_textos_legiveis_em_ordem():
    page = Node("window", children=[
        Node("heading", "Relatório  trimestral"),
        Node("panel", children=[Node("paragraph", "Vendas subiram\n10%")]),
        Node("push button", "Enviar"),
    ])
    assert _collect(page) == "Relatório trimestral\nVendas subiram 10%\nEnviar"


def test_nunca_le_campo_de_senha():
    form = Node("window", children=[
        Node("label", "Senha"),
        Node("password text", "segredo123"),
        Node("label", "Entrar"),
    ])
    text = _collect(form)
    assert "segredo123" not in text
    assert text == "Senha\nEntrar"


def test_nao_repete_o_mesmo_trecho_em_sequencia():
    page = Node("window", children=[Node("label", "Oi"), Node("label", "Oi"), Node("label", "Tchau")])
    assert _collect(page) == "Oi\nTchau"


def test_respeita_o_limite_de_caracteres():
    page = Node("window", children=[Node("paragraph", "a" * 50), Node("paragraph", "b" * 50)])
    assert len(_collect(page, limit=30)) <= 30


def test_ignora_nos_sem_texto_legivel_mas_desce_nos_filhos():
    page = Node("window", children=[Node("filler", "", children=[Node("text", "achado")])])
    assert _collect(page) == "achado"


class FakeSpeech:
    def __init__(self):
        self.calls = []

    def synthesize(self, text, wav_path, *args, **kwargs):
        self.calls.append(text)
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        wav_path.write_bytes(b"RIFF")
        return "fake"


def test_cli_le_a_janela_ativa_e_entrega_o_audio(monkeypatch):
    monkeypatch.setattr(cli, "active_window_text", lambda: "Olá do navegador")
    speech = FakeSpeech()
    text, wav = cli.read_active_window(speech, play=lambda path: True)
    assert text == "Olá do navegador"
    assert speech.calls == ["Olá do navegador"]
    assert wav is None


def test_cli_sem_tocador_devolve_o_caminho_do_wav(monkeypatch):
    monkeypatch.setattr(cli, "active_window_text", lambda: "texto")
    _, wav = cli.read_active_window(FakeSpeech(), play=lambda path: False)
    assert isinstance(wav, Path) and wav.exists()


def test_cli_sem_texto_gera_erro_claro(monkeypatch):
    monkeypatch.setattr(cli, "active_window_text", lambda: "   ")
    with pytest.raises(AccessibilityUnavailable, match="não tem texto"):
        cli.read_active_window(FakeSpeech(), play=lambda path: True)


def test_sem_atspi_a_mensagem_explica_a_instalacao(monkeypatch):
    from congo_grey_parrot.screen import accessibility

    monkeypatch.setattr(accessibility, "_atspi_module", lambda: None)
    with pytest.raises(AccessibilityUnavailable, match="gir1.2-atspi-2.0"):
        accessibility.active_window_text()
