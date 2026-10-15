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
.venv/bin/pip install -e ".[transcribe]"

mkdir -p "${HOME}/.local/bin"
ln -sfn "$root/.venv/bin/congo-reunioes" "${HOME}/.local/bin/congo-reunioes"

echo "Pronto. Se ~/.local/bin estiver no PATH, use congo-reunioes. Exemplos:"
echo "  congo-reunioes plataformas"
echo "  congo-reunioes importar transcricao.vtt --plataforma teams"
echo "  congo-reunioes notas"
echo "O comando importar usa o arquivo que o Teams ou o Meet deixam baixar. Este programa não entra na reunião."
