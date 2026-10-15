#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
choice="${1:-}"

if [[ -z "$choice" ]]; then
  echo "Qual solução você quer instalar?"
  echo "  1  Computador, a janela no Linux"
  echo "  2  Celular Android"
  echo "  3  Bot de Discord"
  echo "  4  Anotações de reunião"
  read -r -p "Digite 1, 2, 3 ou 4: " choice
fi

case "$choice" in
  1|computador)
    exec "$root/congo-grey-parrot-desktop/instalar.sh"
    ;;
  2|celular)
    apk="$root/congo-grey-parrot-android/CongoGreyParrot-debug.apk"
    echo "O celular não se instala por este script."
    echo "1. Copie o arquivo para o Android 8 ou mais novo:"
    echo "   $apk"
    echo "2. Abra o arquivo no celular."
    echo "3. Se o Android bloquear, permita a instalação por esse aplicativo:"
    echo "   https://support.google.com/android/answer/2664792?hl=pt-BR"
    echo "É um APK de teste, assinado com a chave de depuração, não o pacote da Play Store."
    ;;
  3|discord)
    exec "$root/congo-grey-parrot-discord/instalar.sh"
    ;;
  4|reunioes|reuniões)
    exec "$root/congo-grey-parrot-reunioes/instalar.sh"
    ;;
  *)
    echo "Use 1, 2, 3 ou 4."
    exit 1
    ;;
esac
