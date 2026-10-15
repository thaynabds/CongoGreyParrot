#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"

# shellcheck source=../garantir-python.sh
source "$root/../garantir-python.sh"
garantir_python

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
