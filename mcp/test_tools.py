"""Confere a lista de ferramentas sem abrir HTTP e sem token do Discord."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "mcp"),
    str(ROOT / "congo-grey-parrot-desktop" / "src"),
    str(ROOT / "congo-grey-parrot-discord" / "src"),
    str(ROOT / "congo-grey-parrot-reunioes" / "src"),
    str(ROOT / "congo-grey-parrot-android"),
]


def test_tool_lists_import_without_network():
    expected = {
        "congo_grey_parrot.mcp_server": {
            "listar_idiomas",
            "listar_modelos",
            "transcrever_arquivo",
            "falar_texto",
            "traduzir_texto",
            "resumir_texto",
            "resumir_arquivo",
        },
        "congo_reunioes.mcp_server": {
            "listar_plataformas",
            "importar_transcricao",
            "importar_pasta",
            "listar_notas",
            "resumir_reuniao",
            "resumir_texto",
        },
        "congo_discord.mcp_server": {
            "status_bot",
            "listar_funcoes",
            "ajuda_comandos",
            "enviar_comando",
            "ver_log",
            "link_convite",
        },
        "mcp_server": {
            "instrucoes_apk",
            "caminho_apk",
            "instalar_apk",
            "iniciar_app",
        },
    }
    for module_name, names in expected.items():
        module = importlib.import_module(module_name)
        server = module.build_server()
        from runtime import tool_names

        assert set(tool_names(server)) == names


def test_path_guard_blocks_secrets_and_wrong_types(tmp_path, monkeypatch):
    import pytest
    from runtime import guarded_path

    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".ssh").mkdir()
    (tmp_path / "Documentos").mkdir()
    ok = guarded_path(str(tmp_path / "Documentos" / "reuniao.vtt"), {".vtt"})
    assert ok.name == "reuniao.vtt"
    for raw, suffixes in [
        (str(tmp_path / ".ssh" / "id_ed25519"), {".vtt"}),
        (str(tmp_path / ".ssh" / "chave.vtt"), {".vtt"}),
        (str(tmp_path / ".bashrc"), {".wav"}),
        (str(tmp_path / "Documentos" / "senhas.kdbx"), {".vtt"}),
        ("/etc/passwd", {".vtt"}),
        (str(tmp_path / "Documentos" / ".." / ".." / "fora.vtt"), {".vtt"}),
        (str(tmp_path), {".vtt"}),
    ]:
        with pytest.raises(ValueError):
            guarded_path(raw, suffixes)


def test_path_guard_used_by_file_tools(tmp_path, monkeypatch):
    import asyncio

    import pytest

    monkeypatch.setenv("HOME", str(tmp_path))
    secret = tmp_path / ".ssh" / "id_ed25519"
    secret.parent.mkdir()
    secret.write_text("PRIVATE KEY", encoding="utf-8")
    module = importlib.import_module("congo_reunioes.mcp_server")
    server = module.build_server()
    with pytest.raises(Exception) as caught:
        result = server.call_tool("importar_transcricao", {"caminho": str(secret)})
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    assert "PRIVATE KEY" not in str(caught.value)


def _call(server, name, args):
    import asyncio

    result = server.call_tool(name, args)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    return str(result)


def test_path_guard_for_folders(tmp_path, monkeypatch):
    import pytest
    from runtime import guarded_dir

    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "Downloads").mkdir()
    assert guarded_dir(str(tmp_path / "Downloads")).name == "Downloads"
    for raw in [str(tmp_path), str(tmp_path / ".ssh"), "/etc", str(tmp_path / "Downloads" / ".." / "..")]:
        with pytest.raises(ValueError):
            guarded_dir(raw)


def test_importar_pasta_tool_imports_meet_and_refuses_hidden_folder(tmp_path, monkeypatch):
    import pytest

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CONGO_REUNIOES_DATA", str(tmp_path / "dados"))
    folder = tmp_path / "Downloads"
    folder.mkdir()
    (folder / "Daily - Transcript.txt").write_text("00:00:00\nAna: bom dia\n", encoding="utf-8")
    hidden = tmp_path / ".config"
    hidden.mkdir()
    (hidden / "x - Transcript.txt").write_text("Segredo: abc\n", encoding="utf-8")
    server = importlib.import_module("congo_reunioes.mcp_server").build_server()
    assert "importado, 1 falas" in _call(server, "importar_pasta", {"pasta": str(folder)})
    assert "já importado" in _call(server, "importar_pasta", {"pasta": str(folder)})
    with pytest.raises(Exception) as caught:
        _call(server, "importar_pasta", {"pasta": str(hidden)})
    assert "abc" not in str(caught.value)


def test_discord_log_hides_tokens_and_invite_is_minimal(monkeypatch):
    import pytest

    module = importlib.import_module("congo_discord.mcp_server")
    # Falso e montado em partes, para o push protection do GitHub não confundir com um token real.
    leaked = ".".join(["M" + "x" * 25, "Gx" + "y" * 4, "z" * 38])
    assert leaked not in module.redact(f"login falhou com {leaked}")
    server = module.build_server()
    text = _call(server, "link_convite", {"id_aplicacao": "123456789012345678"})
    assert "permissions=3181568" in text and "Sem Administrador" in text
    with pytest.raises(Exception):
        _call(server, "link_convite", {"id_aplicacao": "123&scope=admin"})
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    assert "journalctl" in _call(server, "ver_log", {"linhas": 9999})


def test_discord_service_state_finds_user_bus_without_session_env(monkeypatch):
    module = importlib.import_module("congo_discord.mcp_server")
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    seen = {}

    class Done:
        stdout = "active\n"

    def fake_run(args, **kwargs):
        seen["env"] = kwargs.get("env") or {}
        return Done()

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/systemctl")
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    assert module._service_state() == "active"
    runtime = Path(f"/run/user/{module.os.getuid()}")
    if runtime.is_dir():
        assert seen["env"].get("XDG_RUNTIME_DIR") == str(runtime)


def test_registrar_keeps_other_servers_and_is_idempotent(tmp_path):
    import json

    from registrar_claude import congo_servers, register

    config = tmp_path / "Claude" / "claude_desktop_config.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"mcpServers": {"railway": {"command": "railway"}}, "outro": 1}), encoding="utf-8")
    fake = tmp_path / "repo"
    (fake / "bin").mkdir(parents=True)
    (fake / "bin" / "servidor").write_text("", encoding="utf-8")
    (fake / "mcp.json").write_text(json.dumps({"mcpServers": {
        "congo-um": {"command": "bin/servidor"},
        "congo-falta": {"command": "bin/nao-instalado"},
    }}), encoding="utf-8")
    servers = congo_servers(fake)
    assert servers == {"congo-um": {"command": str(fake / "bin" / "servidor")}}
    assert register(config, servers) == sorted(servers)
    data = json.loads(config.read_text(encoding="utf-8"))
    assert data["outro"] == 1 and "railway" in data["mcpServers"]
    assert set(servers) <= set(data["mcpServers"])
    assert (tmp_path / "Claude" / "claude_desktop_config.json.bak").is_file()
    assert oct(config.stat().st_mode & 0o777) == "0o600"
    assert register(config, servers) == []
    register(config, servers, remove=True)
    assert set(json.loads(config.read_text(encoding="utf-8"))["mcpServers"]) == {"railway"}


def test_resumo_copies_are_identical():
    """O resumo.py é o mesmo no computador, no bot e nas reuniões."""
    copies = [
        ROOT / "congo-grey-parrot-desktop" / "src" / "congo_grey_parrot" / "resumo.py",
        ROOT / "congo-grey-parrot-discord" / "src" / "congo_discord" / "resumo.py",
        ROOT / "congo-grey-parrot-reunioes" / "src" / "congo_reunioes" / "resumo.py",
    ]
    texts = {path.read_text(encoding="utf-8") for path in copies}
    assert len(texts) == 1


def test_resumir_arquivo_reads_home_text_and_refuses_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".ssh").mkdir()
    (tmp_path / ".ssh" / "notas.txt").write_text("segredo guardado aqui. outra frase secreta.", encoding="utf-8")
    docs = tmp_path / "Documentos"
    docs.mkdir()
    (docs / "ata.txt").write_text(
        "O projeto do aplicativo atrasou. Ficou decidido revisar o projeto do aplicativo. "
        "Vou mandar o relatório do projeto até sexta. Quem fala com o cliente?",
        encoding="utf-8",
    )
    module = importlib.import_module("congo_grey_parrot.mcp_server")
    server = module.build_server()

    def call(name, **kwargs):
        try:
            return _call(server, name, kwargs)
        except Exception as exc:  # o erro do guarda também não pode mostrar o conteúdo
            return str(exc)

    ok = call("resumir_arquivo", caminho=str(docs / "ata.txt"))
    assert "Resumo de ata.txt" in ok and "Ficou decidido" in ok
    for bad in (str(tmp_path / ".ssh" / "notas.txt"), "/etc/passwd", str(docs / "ata.exe")):
        assert "segredo" not in call("resumir_arquivo", caminho=bad)
    assert "Não há texto" in call("resumir_texto", texto="   ")
    many = "\n".join(f"Frase número {n} fala do projeto e do prazo novo." for n in range(80))
    assert "Resumo (30 de 80" in call("resumir_texto", texto=many, frases=999)
    assert "Resumo (" in call("resumir_texto", texto=many, frases=-5)
    assert "validation error" in call("resumir_texto", texto=many, frases="x")
