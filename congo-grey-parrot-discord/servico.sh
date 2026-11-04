#!/bin/bash
# Mantém o bot ligado com um serviço systemd do próprio usuário (sem sudo).
# Uso: ./servico.sh instalar | remover | status | log
set -euo pipefail

root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
unit="$unit_dir/congo-discord.service"

case "${1:-status}" in
  instalar)
    if ! grep -Eq '^DISCORD_TOKEN=.{50,}' "$root/.env" 2>/dev/null; then
      echo "O .env ainda não tem DISCORD_TOKEN. Cole o token no arquivo $root/.env e rode de novo."
      exit 1
    fi
    mkdir -p "$unit_dir"
    cat > "$unit" <<UNIT
[Unit]
Description=Congo Grey Parrot, bot de Discord
After=network-online.target
Wants=network-online.target

[Service]
ExecStart="$root/iniciar.sh"
Restart=on-failure
RestartSec=15
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
UNIT
    chmod 600 "$unit"
    systemctl --user daemon-reload
    systemctl --user enable --now congo-discord.service
    echo "Bot ligado. Ele volta sozinho depois de uma falha e ao entrar na sessão."
    ;;
  remover)
    systemctl --user disable --now congo-discord.service 2>/dev/null || true
    rm -f "$unit"
    systemctl --user daemon-reload
    echo "Serviço removido. O bot só liga com ./iniciar.sh."
    ;;
  status)
    systemctl --user status congo-discord.service --no-pager || true
    ;;
  log)
    journalctl --user -u congo-discord.service -n 100 --no-pager -o cat
    ;;
  *)
    echo "Uso: $0 instalar | remover | status | log"
    exit 1
    ;;
esac
