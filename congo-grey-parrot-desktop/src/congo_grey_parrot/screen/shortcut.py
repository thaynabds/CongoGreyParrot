"""Cria o atalho do sistema que chama `congo-grey-parrot ler-janela`.

GNOME e Cinnamon guardam atalhos personalizados em gsettings, cada um com o seu
esquema. Este módulo monta os comandos e executa o gsettings. Outros ambientes
recebem instruções para criar o atalho à mão.
"""

from __future__ import annotations

import ast
import os
import re
import shlex
import shutil
import subprocess
from collections.abc import Callable, Mapping

SHORTCUT_TITLE = "Ler janela ativa (Congo Grey Parrot)"
DEFAULT_BINDING = "<Control><Alt>r"
SUBCOMMAND = "ler-janela"
LAUNCHER = "congo-grey-parrot"
COMMAND = f"{LAUNCHER} {SUBCOMMAND}"

# GNOME
MEDIA_KEYS = "org.gnome.settings-daemon.plugins.media-keys"
CUSTOM_SCHEMA = f"{MEDIA_KEYS}.custom-keybinding"
KEY_LIST_SCHEMA = MEDIA_KEYS
KEY_LIST_KEY = "custom-keybindings"
SHORTCUT_NAME = "congo-ler-janela"

# Cinnamon
CINNAMON_LIST_SCHEMA = "org.cinnamon.desktop.keybindings"
CINNAMON_LIST_KEY = "custom-list"
CINNAMON_CUSTOM_SCHEMA = "org.cinnamon.desktop.keybindings.custom-keybinding"
CINNAMON_DUMMY = "__dummy__"

# Sem isto, navegadores e apps Electron não expõem a árvore de acessibilidade.
A11Y_SCHEMA = "org.gnome.desktop.interface"
A11Y_KEY = "toolkit-accessibility"

_CUSTOM_NAME = re.compile(r"^custom(\d+)$")
_BINDING = re.compile(r"^(<[A-Za-z0-9_]+>)*[A-Za-z0-9_]+$")

Runner = Callable[[list[str]], str]


def keybinding_path(name: str = SHORTCUT_NAME) -> str:
    return f"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/{name}/"


def cinnamon_path(name: str) -> str:
    return f"/org/cinnamon/desktop/keybindings/custom-keybindings/{name}/"


def parse_gsettings_list(raw: str) -> list[str]:
    """Lê a saída de `gsettings get`, como `@as []` ou `['/a/', '/b/']`."""
    value = raw.strip()
    if value.startswith("@as "):
        value = value[4:]
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, (list, tuple)):
        raise ValueError(f"lista inesperada do gsettings: {raw!r}")
    return [str(item) for item in parsed]


def _gvariant_list(items: list[str]) -> str:
    for item in items:
        if "'" in item or "\\" in item:
            raise ValueError(f"nome de atalho inválido: {item!r}")
    return "[" + ", ".join(f"'{item}'" for item in items) + "]"


def check_binding(binding: str) -> str:
    if not _BINDING.match(binding):
        raise ValueError(f"tecla inválida: {binding!r} (exemplo: <Control><Alt>r)")
    return binding


def detect_desktop(env: Mapping[str, str] | None = None) -> str:
    """'cinnamon', 'gnome' ou '' a partir de XDG_CURRENT_DESKTOP."""
    env = os.environ if env is None else env
    names = {part.strip().lower() for part in env.get("XDG_CURRENT_DESKTOP", "").split(":")}
    if names & {"x-cinnamon", "cinnamon"}:
        return "cinnamon"
    if names & {"gnome", "ubuntu", "gnome-classic", "unity"}:
        return "gnome"
    return ""


def shortcut_command(which: Callable[[str], str | None] | None = None) -> str:
    """Comando com o caminho absoluto do lançador, se ele estiver no PATH.

    O atalho roda fora do terminal, onde o PATH pode não ter ~/.local/bin.
    """
    found = (which or shutil.which)(LAUNCHER)
    if not found:
        return COMMAND
    return f"{shlex.quote(found)} {SUBCOMMAND}"


def _is_ours(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    return len(parts) == 2 and os.path.basename(parts[0]) == LAUNCHER and parts[1] == SUBCOMMAND


def build_commands(current: list[str], binding: str = DEFAULT_BINDING, command: str = COMMAND) -> list[list[str]]:
    """Comandos gsettings do GNOME que registram o atalho sem apagar os que já existem."""
    check_binding(binding)
    path = keybinding_path()
    paths = list(current)
    if path not in paths:
        paths.append(path)
    schema_path = f"{CUSTOM_SCHEMA}:{path}"
    return [
        ["gsettings", "set", KEY_LIST_SCHEMA, KEY_LIST_KEY, _gvariant_list(paths)],
        ["gsettings", "set", schema_path, "name", SHORTCUT_TITLE],
        ["gsettings", "set", schema_path, "command", command],
        ["gsettings", "set", schema_path, "binding", binding],
    ]


def build_cinnamon_commands(
    current: list[str],
    command_of: Callable[[str], str],
    binding: str = DEFAULT_BINDING,
    command: str = COMMAND,
) -> list[list[str]]:
    """Comandos gsettings do Cinnamon.

    Reaproveita um atalho nosso que já exista; senão usa o próximo `customN` livre.
    A lista é gravada por último, porque é a mudança nela que faz o Cinnamon recarregar.
    """
    check_binding(binding)
    names = [name for name in current if name != CINNAMON_DUMMY]
    slot = next((name for name in names if _is_ours(command_of(name))), None)
    if slot is None:
        used = {int(m.group(1)) for m in map(_CUSTOM_NAME.match, names) if m}
        slot = f"custom{next(i for i in range(len(used) + 1) if i not in used)}"
    schema_path = f"{CINNAMON_CUSTOM_SCHEMA}:{cinnamon_path(slot)}"
    commands = [
        ["gsettings", "set", schema_path, "name", SHORTCUT_TITLE],
        ["gsettings", "set", schema_path, "command", command],
        ["gsettings", "set", schema_path, "binding", _gvariant_list([binding])],
    ]
    final = names if slot in names else [*names, slot]
    if final == current:
        # A lista não mudaria; um item temporário força o Cinnamon a reler os atalhos.
        commands.append(["gsettings", "set", CINNAMON_LIST_SCHEMA, CINNAMON_LIST_KEY, _gvariant_list([*final, CINNAMON_DUMMY])])
    commands.append(["gsettings", "set", CINNAMON_LIST_SCHEMA, CINNAMON_LIST_KEY, _gvariant_list(final)])
    return commands


def _run(argv: list[str]) -> str:
    return subprocess.run(argv, check=True, capture_output=True, text=True).stdout


def _unquote(raw: str) -> str:
    value = raw.strip()
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value
    return parsed if isinstance(parsed, str) else value


def install_shortcut(
    binding: str = DEFAULT_BINDING,
    env: Mapping[str, str] | None = None,
    run: Runner = _run,
    which: Callable[[str], str | None] | None = None,
) -> tuple[str, list[list[str]]]:
    """Cria o atalho no GNOME ou no Cinnamon. Devolve o ambiente e os comandos aplicados."""
    which = which or shutil.which
    if which("gsettings") is None:
        raise RuntimeError("gsettings não encontrado: este não parece ser um sistema GNOME ou Cinnamon.")
    desktop = detect_desktop(env)
    command = shortcut_command(which)
    if desktop == "cinnamon":
        current = parse_gsettings_list(run(["gsettings", "get", CINNAMON_LIST_SCHEMA, CINNAMON_LIST_KEY]))

        def command_of(name: str) -> str:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
                return ""
            return _unquote(run(["gsettings", "get", f"{CINNAMON_CUSTOM_SCHEMA}:{cinnamon_path(name)}", "command"]))

        commands = build_cinnamon_commands(current, command_of, binding, command)
    elif desktop == "gnome":
        current = parse_gsettings_list(run(["gsettings", "get", KEY_LIST_SCHEMA, KEY_LIST_KEY]))
        commands = build_commands(current, binding, command)
    else:
        found = (env if env is not None else os.environ).get("XDG_CURRENT_DESKTOP", "") or "desconhecido"
        raise RuntimeError(f"ambiente gráfico {found} não suportado (só GNOME e Cinnamon).")
    commands.append(["gsettings", "set", A11Y_SCHEMA, A11Y_KEY, "true"])
    for argv in commands:
        run(argv)
    return desktop, commands


def install_gnome_shortcut(binding: str = DEFAULT_BINDING) -> list[str]:
    """Compatibilidade: aplica o atalho no ambiente detectado e devolve os comandos como texto."""
    _, commands = install_shortcut(binding)
    return [" ".join(argv) for argv in commands]
