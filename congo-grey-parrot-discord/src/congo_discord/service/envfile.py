from __future__ import annotations

import os
import stat
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    _keep_private(path)
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def _keep_private(path: Path) -> None:
    """O .env guarda o token do bot. Se outra conta do computador consegue ler, fecha em 0600."""
    if os.name != "posix":
        return
    try:
        mode = path.stat().st_mode
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            path.chmod(0o600)
    except OSError:
        pass
