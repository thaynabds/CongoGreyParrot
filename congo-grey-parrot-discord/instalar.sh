#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Falta o Python. No Ubuntu: sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "Precisa do Python 3.11 ou mais novo."
  python3 --version
  exit 1
fi

if command -v dpkg >/dev/null 2>&1 && ! dpkg -s python3-venv >/dev/null 2>&1; then
  sudo apt install -y python3-venv
fi

python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e ".[voz,transcribe]"

if [[ ! -f "$root/.env" ]]; then
  cp "$root/.env.example" "$root/.env"
fi

echo "Pronto. Abra este arquivo e cole o token do bot:"
echo "  $root/.env"
echo "Crie o aplicativo em https://discord.com/developers/applications"
echo "Não envie o arquivo .env para o Git."
echo "Para ligar o bot: $root/iniciar.sh"
