#!/bin/bash
# Congo Grey Parrot — instalador do programa de computador (Linux)
set -euo pipefail

# ── cores ─────────────────────────────────────────────────────────────────────
VERDE='\033[0;32m'; AMARELO='\033[1;33m'; VERMELHO='\033[0;31m'
AZUL='\033[0;34m'; NEGRITO='\033[1m'; RESET='\033[0m'

ok()    { echo -e "${VERDE}  [OK]${RESET}  $*"; }
info()  { echo -e "${AZUL}  [...]${RESET} $*"; }
aviso() { echo -e "${AMARELO}  [!]${RESET}  $*"; }
erro()  { echo -e "${VERMELHO}  [X]${RESET}  $*" >&2; }
titulo(){ echo -e "\n${NEGRITO}${AZUL}=== $* ===${RESET}\n"; }

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"

titulo "Congo Grey Parrot — Instalação (Linux)"
echo "  Este script instala o programa de transcrição, leitura em voz alta,"
echo "  edição de legendas e conversão de mídia."
echo "  Nenhuma configuração manual é necessária."
echo ""

# ── 1. Python ─────────────────────────────────────────────────────────────────
titulo "Verificando Python"

# shellcheck source=../garantir-python.sh
source "$root/../garantir-python.sh"
garantir_python
ok "Python pronto."

# ── 2. Dependências do sistema ────────────────────────────────────────────────
titulo "Verificando dependências do sistema"

if command -v dpkg >/dev/null 2>&1; then
  missing=()
  for pkg in libxcb-cursor0 ffmpeg espeak-ng; do
    dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
  done
  if ((${#missing[@]})); then
    aviso "Pacotes do sistema que faltam: ${missing[*]}"
    info  "Pedindo senha para instalar os pacotes necessários..."
    sudo apt install -y "${missing[@]}"
    ok "Pacotes instalados."
  else
    ok "Todos os pacotes do sistema já estão instalados."
  fi
else
  aviso "Sistema não é Ubuntu/Debian. Instale manualmente: ffmpeg espeak-ng libxcb-cursor0"
fi

# ── 3. Ambiente Python e dependências ─────────────────────────────────────────
titulo "Instalando o programa"
info "Criando ambiente isolado (isso garante que nada no seu computador seja alterado)..."

python3 -m venv .venv
info "Atualizando gerenciador de pacotes..."
.venv/bin/pip install -U pip --quiet

info "Baixando e instalando o Congo Grey Parrot e suas dependências..."
info "(Este passo pode demorar alguns minutos na primeira vez)"
.venv/bin/pip install -e ".[transcribe,speech]" --quiet
ok "Programa instalado."

# ── 4. Atalho no menu do sistema ──────────────────────────────────────────────
titulo "Criando atalho no menu"

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
Comment=Transcrição, leitura em voz alta, legendas e conversão de mídia
Exec=${root}/.venv/bin/congo-grey-parrot
Icon=${icon_dest}
Terminal=false
Categories=AudioVideo;Audio;
StartupWMClass=congo-grey-parrot
EOF

ln -sfn "${root}/.venv/bin/congo-grey-parrot" "${HOME}/.local/bin/congo-grey-parrot"
update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true
ok "Atalho criado no menu de aplicativos."

# ── 5. Download opcional do modelo Whisper ────────────────────────────────────
titulo "Modelo de transcrição (Whisper)"

echo "  Para transcrever áudio em texto o programa usa o Whisper,"
echo "  um modelo de IA que fica no seu computador e funciona offline."
echo "  Ele suporta mais de 90 idiomas, incluindo:"
echo "  Português, Inglês, Espanhol, Francês, Italiano, Russo,"
echo "  Chinês, Japonês, Árabe, Bengali, Indonésio e Urdu."
echo ""
echo -e "  Modelos disponíveis (qualidade e tamanho crescentes):"
echo -e "    ${NEGRITO}tiny${RESET}   — 74 MB   — mais rápido, qualidade básica"
echo -e "    ${NEGRITO}base${RESET}   — 142 MB  — recomendado para a maioria dos casos"
echo -e "    ${NEGRITO}small${RESET}  — 461 MB  — boa qualidade"
echo -e "    ${NEGRITO}medium${RESET} — 1,4 GB  — alta qualidade"
echo -e "    ${NEGRITO}large${RESET}  — 2,9 GB  — máxima qualidade"
echo ""

whisper_dir="${HOME}/.local/share/congo-grey-parrot/whisper"
mkdir -p "$whisper_dir"

# Verifica se já tem algum modelo instalado
has_model=false
if ls "$whisper_dir"/*.bin 2>/dev/null | grep -q .; then
  has_model=true
  ok "Modelo Whisper já instalado em: $whisper_dir"
fi

if [[ "$has_model" == false ]]; then
  read -r -p "  Quer baixar o modelo 'base' agora? (recomendado) [S/n]: " resp
  resp="${resp:-S}"
  if [[ "$resp" =~ ^[Ss]$ ]]; then
    info "Baixando modelo 'base' (142 MB). Pode demorar alguns minutos..."
    .venv/bin/python3 - <<'PYEOF'
import sys
from pathlib import Path
from congo_grey_parrot.transcription.service import TranscriptionService
from congo_grey_parrot.models.service import ModelService
import os

whisper_dir = Path.home() / ".local" / "share" / "congo-grey-parrot" / "whisper"
whisper_dir.mkdir(parents=True, exist_ok=True)

def progress(pct, msg):
    bar = "=" * (pct // 5) + "-" * (20 - pct // 5)
    print(f"\r  [{bar}] {pct:3d}%  {msg:<40}", end="", flush=True)

import threading
cancel = threading.Event()
svc = TranscriptionService(whisper_dir)
try:
    svc.preload("base", "cpu", progress, cancel)
    print()
    print("\033[0;32m  [OK]\033[0m  Modelo 'base' instalado.")
except Exception as e:
    print()
    print(f"\033[0;31m  [X]\033[0m  Falha ao baixar: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
  else
    aviso "Modelo não baixado. Você pode baixar depois em 'Modelos e vozes' dentro do programa."
  fi
fi

# ── 6. Conclusão ──────────────────────────────────────────────────────────────
titulo "Instalação concluída"
echo -e "  ${VERDE}${NEGRITO}Congo Grey Parrot foi instalado com sucesso!${RESET}"
echo ""
echo "  Para abrir o programa:"
echo "    — Procure 'Congo Grey Parrot' no menu de aplicativos"
echo "    — Ou rode no terminal: congo-grey-parrot"
echo ""
echo "  Idiomas suportados para transcrição (modelo base):"
echo "  Português, Inglês, Espanhol, Francês, Italiano, Russo,"
echo "  Chinês, Japonês, Árabe, Bengali, Indonésio, Urdu e mais 80 idiomas."
echo ""
