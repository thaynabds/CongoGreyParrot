from __future__ import annotations

import importlib.util
from pathlib import Path

from congo_discord.persistence.store import Store


def load_plugins(folder: Path, store: Store, bot) -> list[str]:
    if not folder.is_dir():
        return []
    loaded: list[str] = []
    for path in sorted(folder.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"congo_plugin_{path.stem}", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        key = str(getattr(module, "FEATURE", path.stem))
        description = str(getattr(module, "DESCRIPTION", "Função adicionada na pasta plugins."))
        store.add_custom(key, description)
        setup = getattr(module, "setup", None)
        if callable(setup):
            setup(bot)
        loaded.append(key)
    return loaded
