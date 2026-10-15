#!/bin/bash

garantir_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Falta o Python. No Ubuntu: sudo apt install python3 python3-pip"
    return 1
  fi

  if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "Precisa do Python 3.11 ou mais novo."
    python3 --version
    return 1
  fi

  local pyver
  pyver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

  if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then
    echo "Falta o pacote que cria o ambiente Python."
    echo "Vou pedir a senha do sistema para instalar python${pyver}-venv e python3-pip."
    echo "No Ubuntu esse pacote é o que o próprio Python pede: https://docs.python.org/3/library/venv.html"
    sudo apt install -y "python${pyver}-venv" python3-pip
  fi

  if [[ -d .venv && ! -x .venv/bin/pip ]]; then
    echo "O ambiente anterior ficou incompleto. Vou apagar e criar de novo."
    rm -rf .venv
  fi
}
