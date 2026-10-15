#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"
chmod +x "$root/congo-reunioes"

mkdir -p "${HOME}/.local/bin"
ln -sfn "$root/congo-reunioes" "${HOME}/.local/bin/congo-reunioes"

echo "Pronto. Estes comandos já funcionam, sem instalar biblioteca:"
echo "  congo-reunioes plataformas"
echo "  congo-reunioes importar exemplo-teams.vtt --plataforma teams"
echo "  congo-reunioes notas"
echo "Se o terminal disser que não achou o comando, use o caminho completo:"
echo "  $root/congo-reunioes plataformas"
echo
echo "Para transcrever um áudio, o Ubuntu precisa do pacote python3.12-venv."
echo "Documentação: https://docs.python.org/3/library/venv.html"
if python3 -c 'import ensurepip' >/dev/null 2>&1; then
  # shellcheck source=../garantir-python.sh
  source "$root/../garantir-python.sh"
  garantir_python
  python3 -m venv .venv
  .venv/bin/pip install -U pip
  .venv/bin/pip install -e ".[transcribe]"
  echo "A transcrição de áudio também ficou instalada."
else
  echo "Ainda não instalei a transcrição de áudio. Quando quiser, rode:"
  echo "  sudo apt install python3.12-venv python3-pip"
  echo "  $root/instalar.sh"
fi
echo "O comando importar usa o arquivo que o Teams ou o Meet deixam baixar. Este programa não entra na reunião."
