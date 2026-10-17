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
