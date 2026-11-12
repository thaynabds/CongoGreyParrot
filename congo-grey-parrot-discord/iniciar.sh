#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
bin="$root/.venv/bin/congo-discord"

if [[ ! -x "$bin" ]]; then
  echo "O bot ainda não está instalado. Rode: $root/instalar.sh"
  exit 1
fi

if [[ "${1:-}" == "conector" ]]; then
  # AI Conector: mostra como ligar uma IA ao bot por MCP. --conectar registra no Claude Desktop e no Cursor.
  exec "$root/.venv/bin/python" -m congo_discord "$@"
fi

exec "$bin"
