#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
source="$root/dist/congo-grey-parrot"
dest="${HOME}/.local/opt/congo-grey-parrot"

if [[ ! -x "$source/congo-grey-parrot" ]]; then
  echo "A pasta dist/congo-grey-parrot ainda não existe. Gere o programa com PyInstaller antes."
  exit 1
fi

mkdir -p "${HOME}/.local/opt" "${HOME}/.local/share/applications" "${HOME}/.local/bin"
rm -rf "$dest"
cp -a "$source" "$dest"
chmod +x "$dest/congo-grey-parrot"
icon_src="$root/src/congo_grey_parrot/ui/assets/icon.png"
mkdir -p "${HOME}/.local/share/icons"
if [[ -f "$icon_src" ]]; then
  cp "$icon_src" "${HOME}/.local/share/icons/congo-grey-parrot.png"
  cp "$icon_src" "$dest/icon.png"
fi

cat > "${HOME}/.local/share/applications/congo-grey-parrot.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Congo Grey Parrot
Comment=Transcrição e leitura local
Exec=${dest}/congo-grey-parrot
Icon=${HOME}/.local/share/icons/congo-grey-parrot.png
Terminal=false
Categories=AudioVideo;Audio;
StartupWMClass=congo-grey-parrot
EOF

ln -sfn "$dest/congo-grey-parrot" "${HOME}/.local/bin/congo-grey-parrot"
update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true
echo "Instalado em ${dest}"
echo "Abra pelo menu ou com: ${dest}/congo-grey-parrot"
