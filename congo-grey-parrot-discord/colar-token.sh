#!/bin/bash
# Grava o token do bot no .env sem mostrar o valor na tela, no histórico ou em log.
# Uso: ./colar-token.sh   (cole o token quando pedir e aperte Enter)
set -euo pipefail
umask 077

root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
env_file="${CONGO_DISCORD_ENV_FILE:-$root/.env}"

if [ -t 0 ]; then
  printf 'Cole o token do bot e aperte Enter (ele não aparece na tela): '
  IFS= read -rs token
  printf '\n'
else
  IFS= read -r token || true
fi
# Tira espaços e aspas que vêm junto ao copiar.
token="$(printf '%s' "$token" | tr -d "[:space:]\"'")"

# Token de bot: três partes em base64url separadas por ponto.
if ! [[ "$token" =~ ^[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{20,}$ ]] || [ "${#token}" -lt 50 ] || [ "${#token}" -gt 120 ]; then
  echo "Isso não parece um token de bot do Discord. Nada foi gravado."
  exit 1
fi

tmp="$(mktemp "$(dirname "$env_file")/.env.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
if [ -f "$env_file" ]; then
  grep -v '^DISCORD_TOKEN=' "$env_file" > "$tmp" || true
fi
{ printf 'DISCORD_TOKEN=%s\n' "$token"; cat "$tmp"; } > "$tmp.new"
mv "$tmp.new" "$tmp"
chmod 600 "$tmp"
mv "$tmp" "$env_file"
trap - EXIT
unset token
echo "Token gravado em $env_file (só você pode ler)."
