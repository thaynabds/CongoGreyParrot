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
        },
        "congo_reunioes.mcp_server": {
            "listar_plataformas",
            "importar_transcricao",
            "listar_notas",
        },
        "congo_discord.mcp_server": {
            "status_bot",
            "listar_funcoes",
            "ajuda_comandos",
            "enviar_comando",
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
