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

if command -v dpkg >/dev/null 2>&1; then
  missing=()
  for pkg in python3-venv libxcb-cursor0 ffmpeg espeak-ng; do
    dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
  done
  if ((${#missing[@]})); then
    echo "Faltam pacotes do sistema: ${missing[*]}"
    echo "A janela do Qt 6.5 precisa de libxcb-cursor0: https://doc.qt.io/qt-6/linux-requirements.html"
    sudo apt install -y "${missing[@]}"
  fi
fi

python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e ".[transcribe,speech]"

mkdir -p "${HOME}/.local/share/icons" "${HOME}/.local/share/applications" "${HOME}/.local/bin"
icon_src="$root/src/congo_grey_parrot/ui/assets/icon.png"
icon_dest="${HOME}/.local/share/icons/congo-grey-parrot.png"
if [[ -f "$icon_src" ]]; then
  cp "$icon_src" "$icon_dest"
fi

cat > "${HOME}/.local/share/applications/congo-grey-parrot.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Congo Grey Parrot
Comment=Transcrição e leitura local
Exec=${root}/.venv/bin/congo-grey-parrot
Icon=${icon_dest}
Terminal=false
Categories=AudioVideo;Audio;
StartupWMClass=congo-grey-parrot
EOF

ln -sfn "${root}/.venv/bin/congo-grey-parrot" "${HOME}/.local/bin/congo-grey-parrot"
update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true

echo "Pronto. Abra Congo Grey Parrot no menu de aplicativos."
echo "Ou rode: ${root}/.venv/bin/congo-grey-parrot"
