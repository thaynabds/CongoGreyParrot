#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"
# shellcheck source=../garantir-python.sh
source "$root/../garantir-python.sh"
garantir_python

python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e ".[voz,transcribe]"

if [[ ! -f "$root/.env" ]]; then
  cp "$root/.env.example" "$root/.env"
fi

echo
echo "Pronto."
echo "1. Abra este arquivo e cole o token do bot:"
echo "   $root/.env"
echo "   Crie o aplicativo em https://discord.com/developers/applications"
echo "   Não envie o arquivo .env para o Git."
echo "2. Ligue o bot neste terminal:"
echo "   $root/iniciar.sh"
echo "3. Os comandos /vtt se digitam no Discord, dentro do servidor, depois que o bot estiver online."
echo "   Eles não funcionam no terminal do Linux."
