#!/bin/bash
# Instalador do bot de Discord para quem não programa.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"
# shellcheck source=../garantir-python.sh
source "$root/../garantir-python.sh"

echo
echo "Congo Grey Parrot, bot de Discord"
echo "Este programa entra no seu servidor e responde aos comandos com barra."
echo

garantir_python

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Falta o programa que lê áudio e vídeo."
  echo "Vou pedir a senha do computador só para instalar o ffmpeg."
  echo "Documentação: https://ffmpeg.org/download.html"
  sudo apt-get update
  sudo apt-get install -y ffmpeg
fi

python3 -m venv .venv
.venv/bin/pip install -U pip
echo "Instalando o bot, a voz, a transcrição e a música. A primeira vez demora."
if ! .venv/bin/pip install -e ".[voz,transcribe,musica,mcp]"; then
  echo "Uma parte extra não instalou. Sigo com o bot e tento cada parte."
  .venv/bin/pip install -e ".[mcp]"
  for extra in voz transcribe musica; do
    .venv/bin/pip install -e ".[$extra]" || echo "Não instalei a parte ${extra}. O resto do bot continua."
  done
fi

if [[ ! -f "$root/.env" ]]; then
  cp "$root/.env.example" "$root/.env"
fi
chmod 600 "$root/.env"

explain_token() {
  echo
  echo "Ainda falta o token. Ele só existe no site do Discord, com a sua conta."
  echo "Abra https://discord.com/developers/applications"
  echo "1. Clique em New Application, dê um nome e confirme."
  echo "2. No menu, clique em Bot."
  echo "3. Clique em Reset Token, confirme e copie o token."
  echo "4. Para achar o seu número de usuário: no Discord, Ajustes do usuário, Avançado, ligue o Modo desenvolvedor. Depois clique com o botão direito no seu nome e em Copiar ID do usuário."
  echo "5. Para convidar o bot: OAuth2, URL Generator."
  echo "   Marque os escopos bot e applications.commands."
  echo "   Marque as permissões Ver canais, Enviar mensagens, Inserir links, Anexar arquivos, Ler histórico de mensagens, Conectar, Falar e Usar atividade de voz."
  echo "   Copie o link gerado, abra no navegador e escolha o servidor."
  echo "Documentação: https://discord.com/developers/docs/topics/oauth2"
}

has_token=0
if python3 - "$root/.env" << 'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
ok = any(line.startswith("DISCORD_TOKEN=") and line.split("=", 1)[1].strip().strip('"').strip("'") for line in text.splitlines())
raise SystemExit(0 if ok else 1)
PY
then
  has_token=1
fi

new_token=""
new_owner=""
new_app=""
if [[ "$has_token" -eq 0 ]]; then
  explain_token
  if [[ -t 0 ]]; then
    read -r -s -p "Cole o token e pressione Enter: " new_token
    echo
    read -r -p "Cole o ID do dono e pressione Enter: " new_owner
    read -r -p "Se tiver o ID do aplicativo, cole aqui. Se não tiver, só pressione Enter: " new_app
  else
    echo "Este terminal não aceita digitação agora. Rode de novo o instalador numa janela e cole o token lá."
  fi
fi

CONGO_NEW_TOKEN="$new_token" CONGO_NEW_OWNER="$new_owner" CONGO_NEW_APP="$new_app" python3 - "$root/.env" << 'PY'
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
values = {}
order = []
for raw in path.read_text(encoding="utf-8").splitlines():
    if not raw.strip() or raw.lstrip().startswith("#") or "=" not in raw:
        continue
    key, value = raw.split("=", 1)
    key = key.strip()
    if key not in values:
        order.append(key)
    values[key] = value.strip().strip('"').strip("'")

token = os.environ.get("CONGO_NEW_TOKEN", "").strip()
owner = os.environ.get("CONGO_NEW_OWNER", "").strip()
app_id = os.environ.get("CONGO_NEW_APP", "").strip()
if token:
    values["DISCORD_TOKEN"] = token
if owner:
    values["CONGO_DISCORD_OWNER_ID"] = owner
for key in ("DISCORD_TOKEN", "CONGO_DISCORD_OWNER_ID", "CONGO_DISCORD_GUILD_ID", "CONGO_DISCORD_ALLOW_UPDATE", "CONGO_DISCORD_DATA"):
    if key not in order:
        order.append(key)
    values.setdefault(key, "")
path.write_text("".join(f"{key}={values.get(key, '')}\n" for key in order), encoding="utf-8")
os.chmod(path, 0o600)
if app_id.isdigit():
    print(
        "Abra este link para colocar o bot no servidor:\n"
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={app_id}&permissions=36817920&scope=bot%20applications.commands"
    )
elif token and not app_id:
    print("Sem o ID do aplicativo, copie o link na tela OAuth2, URL Generator.")
PY
unset new_token new_owner new_app CONGO_NEW_TOKEN CONGO_NEW_OWNER CONGO_NEW_APP || true

mkdir -p "${HOME}/.local/share/applications" "${HOME}/.local/bin"
cat > "${HOME}/.local/share/applications/congo-grey-parrot-discord.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Congo Grey Parrot Discord
Comment=Liga o bot de Discord neste computador
Exec=x-terminal-emulator -e ${root}/iniciar.sh
Terminal=false
Categories=Network;
EOF
ln -sfn "${root}/iniciar.sh" "${HOME}/.local/bin/congo-discord"
update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true

echo
echo "Atalho no menu: Congo Grey Parrot Discord"
echo "Comando: congo-discord"
echo "Para uma IA local, veja a pasta mcp na raiz do projeto."

if python3 - "$root/.env" << 'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
ok = any(line.startswith("DISCORD_TOKEN=") and line.split("=", 1)[1].strip().strip('"').strip("'") for line in text.splitlines())
raise SystemExit(0 if ok else 1)
PY
then
  echo "Ligando o bot. Deixe esta janela aberta."
  exec "$root/iniciar.sh"
fi

echo "O bot ainda não liga porque o token está vazio. Quando tiver o token, rode este instalador de novo."
