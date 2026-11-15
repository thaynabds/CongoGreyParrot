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


from congo_grey_parrot.screen import shortcut


def test_lista_vazia_do_gsettings_vira_lista_python():
    assert shortcut.parse_gsettings_list("@as []") == []
    assert shortcut.parse_gsettings_list("['/a/', '/b/']") == ["/a/", "/b/"]


def test_comandos_preservam_atalhos_existentes_e_nao_duplicam():
    existing = ["/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/outro/"]
    commands = shortcut.build_commands(existing)
    listed = commands[0][-1]
    assert "outro/" in listed and shortcut.keybinding_path() in listed
    again = shortcut.build_commands(shortcut.parse_gsettings_list(f"['{shortcut.keybinding_path()}']"))
    assert again[0][-1].count("congo-ler-janela") == 1


def test_comando_do_atalho_e_a_tecla_configurada():
    commands = shortcut.build_commands([], binding="<Super>k")
    assert ["gsettings", "set", shortcut.CUSTOM_SCHEMA + ":" + shortcut.keybinding_path(), "command", shortcut.COMMAND] in commands
    assert commands[-1][-1] == "<Super>k"


def test_sem_gsettings_a_instalacao_explica_o_motivo(monkeypatch):
    monkeypatch.setattr(shortcut.shutil, "which", lambda name: None)
    import pytest as _pytest
    with _pytest.raises(RuntimeError, match="gsettings"):
        shortcut.install_gnome_shortcut()


def test_cli_apaga_o_audio_depois_de_tocar(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "active_window_text", lambda: "texto da tela")
    monkeypatch.setattr(cli.tempfile, "mkdtemp", lambda prefix: str(tmp_path / "pasta"))
    (tmp_path / "pasta").mkdir()
    tocados = []
    _, wav = cli.read_active_window(FakeSpeech(), play=lambda path: tocados.append(path.exists()) or True)
    assert tocados == [True]
    assert wav is None
    assert not (tmp_path / "pasta").exists()


def test_gi_de_pasta_que_nao_e_do_sistema_nunca_e_carregado(tmp_path, monkeypatch):
    import sys
    import sysconfig

    from congo_grey_parrot.screen import accessibility

    falso = tmp_path / "gi"
    falso.mkdir()
    (falso / "__init__.py").write_text("raise SystemExit('carregou codigo de pasta do usuario')\n")
    (falso / f"_gi{sysconfig.get_config_var('EXT_SUFFIX')}").write_bytes(b"")
    monkeypatch.delitem(sys.modules, "gi", raising=False)
    assert accessibility._load_system_gi([tmp_path]) is False
    assert "gi" not in sys.modules


def test_deteccao_do_ambiente():
    assert shortcut.detect_desktop({"XDG_CURRENT_DESKTOP": "X-Cinnamon"}) == "cinnamon"
    assert shortcut.detect_desktop({"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"}) == "gnome"
    assert shortcut.detect_desktop({"XDG_CURRENT_DESKTOP": "KDE"}) == ""
    assert shortcut.detect_desktop({}) == ""


def test_comando_usa_o_caminho_absoluto_do_lancador():
    cmd = shortcut.shortcut_command(lambda name: "/home/a b/.local/bin/congo-grey-parrot")
    assert cmd == "'/home/a b/.local/bin/congo-grey-parrot' ler-janela"
    assert shortcut._is_ours(cmd)
    assert shortcut.shortcut_command(lambda name: None) == shortcut.COMMAND


def test_tecla_invalida_e_recusada():
    for ruim in ["", "<Control>'; rm", "<Control><Alt>r x"]:
        with pytest.raises(ValueError):
            shortcut.check_binding(ruim)


def test_cinnamon_usa_o_proximo_custom_livre_e_preserva_os_outros():
    commands = shortcut.build_cinnamon_commands(["custom0", "custom2"], lambda name: "outro")
    assert commands[-1] == ["gsettings", "set", "org.cinnamon.desktop.keybindings", "custom-list", "['custom0', 'custom2', 'custom1']"]
    assert any(c[2].endswith("/custom1/") and c[3] == "binding" and c[4] == "['<Control><Alt>r']" for c in commands)


def test_cinnamon_reaproveita_o_atalho_existente_sem_duplicar():
    commands = shortcut.build_cinnamon_commands(
        ["custom0", "custom1"], lambda name: "congo-grey-parrot ler-janela" if name == "custom1" else "x"
    )
    assert all("/custom2/" not in " ".join(c) for c in commands)
    listas = [c[-1] for c in commands if c[3] == "custom-list"]
    assert listas == ["['custom0', 'custom1', '__dummy__']", "['custom0', 'custom1']"]


def test_instalacao_no_cinnamon_ativa_a_acessibilidade():
    feitos = []

    def run(argv):
        feitos.append(argv)
        if argv[:2] == ["gsettings", "get"]:
            return "['custom0']" if argv[-1] == "custom-list" else "'outro'"
        return ""

    desktop, _ = shortcut.install_shortcut(
        env={"XDG_CURRENT_DESKTOP": "X-Cinnamon"}, run=run, which=lambda name: "/usr/bin/" + name
    )
    assert desktop == "cinnamon"
    assert ["gsettings", "set", "org.gnome.desktop.interface", "toolkit-accessibility", "true"] in feitos
    assert not any("org.gnome.settings-daemon" in " ".join(a) for a in feitos)


def test_ambiente_desconhecido_explica_e_nao_grava_nada():
    feitos = []
    with pytest.raises(RuntimeError, match="KDE"):
        shortcut.install_shortcut(env={"XDG_CURRENT_DESKTOP": "KDE"}, run=feitos.append, which=lambda n: "/x")
    assert feitos == []
