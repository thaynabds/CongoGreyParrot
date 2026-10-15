#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
bin="$root/.venv/bin/congo-discord"

if [[ ! -x "$bin" ]]; then
  echo "O bot ainda não está instalado. Rode: $root/instalar.sh"
  exit 1
fi

exec "$bin"
