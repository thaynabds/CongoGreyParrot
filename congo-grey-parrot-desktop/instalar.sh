#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"

# shellcheck source=../garantir-python.sh
source "$root/../garantir-python.sh"
garantir_python

if command -v dpkg >/dev/null 2>&1; then
  missing=()
  for pkg in libxcb-cursor0 ffmpeg espeak-ng; do
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
