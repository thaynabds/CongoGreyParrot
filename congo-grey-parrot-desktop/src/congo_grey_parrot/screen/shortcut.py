"""Cria o atalho do sistema que chama `congo-grey-parrot ler-janela` (GNOME).

O GNOME guarda atalhos personalizados em gsettings. Este módulo só monta os
comandos e, se pedido, executa o gsettings. Outros ambientes recebem instruções.
"""

from __future__ import annotations

import ast
import shutil
import subprocess

MEDIA_KEYS = "org.gnome.settings-daemon.plugins.media-keys"
CUSTOM_SCHEMA = f"{MEDIA_KEYS}.custom-keybinding"
KEY_LIST_SCHEMA = MEDIA_KEYS
KEY_LIST_KEY = "custom-keybindings"
SHORTCUT_NAME = "congo-ler-janela"
DEFAULT_BINDING = "<Control><Alt>r"
COMMAND = "congo-grey-parrot ler-janela"


def keybinding_path(name: str = SHORTCUT_NAME) -> str:
    return f"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/{name}/"


def parse_gsettings_list(raw: str) -> list[str]:
    """Lê a saída de `gsettings get`, como `@as []` ou `['/a/', '/b/']`."""
    value = raw.strip()
    if value.startswith("@as "):
        value = value[4:]
    parsed = ast.literal_eval(value)
    return [str(item) for item in parsed]


def build_commands(current: list[str], binding: str = DEFAULT_BINDING) -> list[list[str]]:
    """Comandos gsettings que registram o atalho sem apagar os que já existem."""
    path = keybinding_path()
    paths = list(current)
    if path not in paths:
        paths.append(path)
    listed = "[" + ", ".join(f"'{item}'" for item in paths) + "]"
    schema_path = f"{CUSTOM_SCHEMA}:{path}"
    return [
        ["gsettings", "set", KEY_LIST_SCHEMA, KEY_LIST_KEY, listed],
        ["gsettings", "set", schema_path, "name", "Ler janela ativa (Congo Grey Parrot)"],
        ["gsettings", "set", schema_path, "command", COMMAND],
        ["gsettings", "set", schema_path, "binding", binding],
    ]


def install_gnome_shortcut(binding: str = DEFAULT_BINDING) -> list[str]:
    """Aplica o atalho no GNOME. Devolve as linhas de status. Lança erro se não houver gsettings."""
    if shutil.which("gsettings") is None:
        raise RuntimeError("gsettings não encontrado: este não parece ser um sistema GNOME.")
    raw = subprocess.run(
        ["gsettings", "get", KEY_LIST_SCHEMA, KEY_LIST_KEY],
        check=True, capture_output=True, text=True,
    ).stdout
    commands = build_commands(parse_gsettings_list(raw), binding)
    for argv in commands:
        subprocess.run(argv, check=True)
    return [" ".join(argv) for argv in commands]
