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


def desktop_config() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "Claude" / "claude_desktop_config.json"


def congo_servers(root: Path = ROOT) -> dict[str, dict]:
    """Lê mcp.json do repositório e devolve só os servidores cujo programa existe, com caminho absoluto."""
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


def register(config: Path, servers: dict[str, dict], remove: bool = False) -> list[str]:
    current = {}
    if config.is_file():
        current = json.loads(config.read_text(encoding="utf-8") or "{}")
    table = current.setdefault("mcpServers", {})
    before = json.dumps(current, sort_keys=True)
    for name in [key for key in table if key.startswith(PREFIX)]:
        del table[name]
    if not remove:
        table.update(servers)
    if json.dumps(current, sort_keys=True) == before:
        return []
    config.parent.mkdir(parents=True, exist_ok=True)
    backup = config.with_name(config.name + ".bak")
    if config.is_file() and not backup.exists():
        shutil.copy2(config, backup)
    temp = config.with_name(config.name + ".tmp")
    temp.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temp, 0o600)
    temp.replace(config)
    return sorted(servers) if not remove else ["removidos"]


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
