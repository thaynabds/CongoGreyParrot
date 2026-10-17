#!/bin/bash
# Congo Grey Parrot — instalador principal
set -euo pipefail

# ── cores ─────────────────────────────────────────────────────────────────────
VERDE='\033[0;32m'; AMARELO='\033[1;33m'; VERMELHO='\033[0;31m'
AZUL='\033[0;34m'; NEGRITO='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${VERDE}  OK${RESET}  $*"; }
info() { echo -e "${AZUL}  >>>${RESET} $*"; }
aviso(){ echo -e "${AMARELO}  AVISO${RESET} $*"; }
erro() { echo -e "${VERMELHO}  ERRO${RESET} $*" >&2; }

banner() {
  echo ""
  echo -e "${NEGRITO}${AZUL}╔══════════════════════════════════════════════╗${RESET}"
  echo -e "${NEGRITO}${AZUL}║     Congo Grey Parrot — Instalador           ║${RESET}"
  echo -e "${NEGRITO}${AZUL}║     github.com/thaynabds/CongoGreyParrot      ║${RESET}"
  echo -e "${NEGRITO}${AZUL}╚══════════════════════════════════════════════╝${RESET}"
  echo ""
}

# ── menu ──────────────────────────────────────────────────────────────────────
mostrar_menu() {
  echo -e "${NEGRITO}Qual programa você quer instalar?${RESET}"
  echo ""
  echo -e "  ${NEGRITO}1${RESET}  Computador (Linux)"
  echo -e "     Transcreve fala, lê texto em voz alta, edita legendas."
  echo -e "     Funciona offline depois de baixar o modelo de IA."
  echo ""
  echo -e "  ${NEGRITO}2${RESET}  Celular Android"
  echo -e "     Grava áudio e lê texto em voz alta no Android 8 ou mais novo."
  echo -e "     Instale o APK diretamente no celular."
  echo ""
  echo -e "  ${NEGRITO}3${RESET}  Bot de Discord"
  echo -e "     Entra em chamadas de voz, transcreve ao vivo, rola dados e muito mais."
  echo -e "     Precisa de um token do Discord Developer Portal."
  echo ""
  echo -e "  ${NEGRITO}4${RESET}  Anotações de reunião"
  echo -e "     Lê arquivos VTT do Teams, Meet ou Zoom e organiza as falas."
  echo ""
  echo -e "  ${NEGRITO}0${RESET}  Sair"
  echo ""
}

root="$(cd "$(dirname "$0")" && pwd)"
choice="${1:-}"
banner

if [[ -z "$choice" ]]; then
  mostrar_menu
  read -r -p "Digite o número e pressione Enter: " choice
fi

case "$choice" in
  1|computador)
    info "Iniciando instalação do programa de computador..."
    exec "$root/congo-grey-parrot-desktop/instalar.sh"
    ;;
  2|celular|android)
    apk="$root/congo-grey-parrot-android/CongoGreyParrot-debug.apk"
    echo ""
    echo -e "${NEGRITO}Instalação no celular Android${RESET}"
    echo ""
    echo -e "  ${NEGRITO}Passo 1${RESET}: Conecte o celular ao computador via cabo USB"
    echo -e "           ou copie o arquivo abaixo para o celular via Bluetooth ou e-mail:"
    echo ""
    echo -e "           ${AMARELO}$apk${RESET}"
    echo ""
    echo -e "  ${NEGRITO}Passo 2${RESET}: Abra o arquivo no celular."
    echo ""
    echo -e "  ${NEGRITO}Passo 3${RESET}: Se aparecer um aviso de bloqueio, toque em"
    echo -e "           'Configurações' e ative 'Instalar apps desconhecidos'."
    echo -e "           Mais detalhes: https://support.google.com/android/answer/2664792"
    echo ""
    ok "Instrucoes exibidas. Copie o arquivo para o celular e siga os passos."
    ;;
  3|discord)
    info "Iniciando instalação do bot de Discord..."
    exec "$root/congo-grey-parrot-discord/instalar.sh"
    ;;
  4|reunioes|reuniões)
    info "Iniciando instalação do programa de reuniões..."
    exec "$root/congo-grey-parrot-reunioes/instalar.sh"
    ;;
  0|sair)
    echo "Saindo."
    exit 0
    ;;
  *)
    erro "Opção inválida: '$choice'. Use 0, 1, 2, 3 ou 4."
    exit 1
    ;;
esac
