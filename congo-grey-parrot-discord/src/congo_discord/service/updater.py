from __future__ import annotations

import subprocess
from pathlib import Path


def update_report(repo: Path, allow_pull: bool) -> str:
    if not (repo / ".git").exists():
        return "Esta pasta não é um repositório Git. A atualização fica em https://github.com/thaynabds/CongoGreyParrot."
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "-sb"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [status.stdout.strip() or "Sem relatório do Git."]
    if not allow_pull:
        lines.append("Para baixar atualizações: git pull --ff-only, dentro da pasta do projeto.")
        lines.append("O bot só faz isso sozinho se CONGO_DISCORD_ALLOW_UPDATE=1.")
        return "\n".join(lines)
    pull = subprocess.run(
        ["git", "-C", str(repo), "pull", "--ff-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines.append(pull.stdout.strip() or pull.stderr.strip() or "git pull não devolveu texto.")
    lines.append("Reinicie o bot para carregar o código novo.")
    return "\n".join(lines)
