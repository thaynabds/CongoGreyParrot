"""Registra os servidores MCP do Congo no Claude Desktop, com caminho absoluto e só por stdio (nada de porta aberta).

Uso: python mcp/registrar_claude.py [--remover]
Mantém os outros servidores do arquivo e guarda uma cópia .bak antes da primeira mudança.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "congo-"


def host_config_home() -> Path:
    """Pasta de configuração do usuário. Dentro do Flatpak, XDG_CONFIG_HOME aponta para a caixa de areia."""
    if os.environ.get("FLATPAK_ID"):
        return Path(os.environ.get("HOST_XDG_CONFIG_HOME") or Path.home() / ".config")
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def desktop_config() -> Path:
    return host_config_home() / "Claude" / "claude_desktop_config.json"


def congo_servers(root: Path = ROOT) -> dict[str, dict]:
    """Lê mcp.json do repositório e devolve só os servidores cujo programa existe, com caminho absoluto."""
    if not (root / "mcp.json").is_file():
        return {}
    data = json.loads((root / "mcp.json").read_text(encoding="utf-8"))
    found = {}
    for name, spec in data["mcpServers"].items():
        command = root / spec["command"]
        if not command.exists():
            continue
        entry = {"command": str(command)}
        if spec.get("args"):
            entry["args"] = [str(root / item) if (root / item).exists() else item for item in spec["args"]]
        found[name] = entry
    return found


def cursor_config() -> Path:
    return Path.home() / ".cursor" / "mcp.json"


def _load(config: Path) -> dict:
    if not config.is_file():
        return {}
    data = json.loads(config.read_text(encoding="utf-8") or "{}")
    if not isinstance(data, dict) or not isinstance(data.get("mcpServers", {}), dict):
        raise ValueError(f"{config} não tem o formato esperado. Corrija o arquivo antes.")
    return data


def register(config: Path, servers: dict[str, dict], remove: bool = False) -> list[str]:
    current = _load(config)
    table = current.setdefault("mcpServers", {})
    before = json.dumps(current, sort_keys=True)
    for name in [key for key in table if key.startswith(PREFIX)]:
        del table[name]
    if not remove:
        table.update(servers)
    if json.dumps(current, sort_keys=True) == before:
        return []
    _write(config, current)
    return sorted(servers) if not remove else ["removidos"]


def register_one(config: Path, name: str, entry: dict | None) -> bool:
    """Liga (entry) ou desliga (None) um único servidor do Congo e mantém todo o resto do arquivo."""
    if not name.startswith(PREFIX):
        raise ValueError("Só mexo em servidores do Congo.")
    current = _load(config)
    table = current.setdefault("mcpServers", {})
    before = json.dumps(current, sort_keys=True)
    if entry is None:
        table.pop(name, None)
    else:
        table[name] = entry
    if json.dumps(current, sort_keys=True) == before:
        return False
    _write(config, current)
    return True


def is_registered(config: Path, name: str) -> bool:
    try:
        return name in _load(config).get("mcpServers", {})
    except (OSError, ValueError):
        return False


def _write(config: Path, current: dict) -> None:
    config.parent.mkdir(parents=True, exist_ok=True)
    backup = config.with_name(config.name + ".bak")
    if config.is_file() and not backup.exists():
        shutil.copy2(config, backup)
    temp = config.with_name(config.name + ".tmp")
    temp.unlink(missing_ok=True)
    # Nasce com 0600: o arquivo pode guardar tokens de outros servidores MCP.
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(current, ensure_ascii=False, indent=2) + "\n")
    temp.replace(config)


def main() -> None:
    remove = "--remover" in sys.argv[1:]
    servers = congo_servers()
    changed = register(desktop_config(), servers, remove)
    if remove:
        print("Servidores do Congo removidos do Claude Desktop." if changed else "Nada a remover.")
        return
    print("Registrados no Claude Desktop: " + ", ".join(sorted(servers)) if changed else "Já estava registrado.")
    missing = set(json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]) - set(servers)
    if missing:
        print("Faltam instalar: " + ", ".join(sorted(missing)) + ". Rode ./instalar.sh e repita.")
    print("Feche e abra o Claude Desktop para ele ler a mudança.")


if __name__ == "__main__":
    main()
