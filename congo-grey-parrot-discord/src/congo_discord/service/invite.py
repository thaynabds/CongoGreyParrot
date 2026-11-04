"""Convite OAuth2 do bot com as permissões que o código usa, e nada além delas."""

from __future__ import annotations

import re
import urllib.parse

# Cada bit vem de um uso real no código. O bot não lê mensagens (sem message_content),
# não usa embed nem histórico, e não modera nada: por isso não pede mais que isto.
PERMISSIONS = {
    "VIEW_CHANNEL": 1 << 10,  # ver o canal onde o comando foi usado
    "SEND_MESSAGES": 1 << 11,  # relay do Foundry e transcrição ao vivo postados no canal
    "ATTACH_FILES": 1 << 15,  # /handout, /arquivo ler, imagem e vídeo vindos do Foundry
    "CONNECT": 1 << 20,  # entrar no canal de voz em /reuniao e /som
    "SPEAK": 1 << 21,  # tocar som e música
}
ADMINISTRATOR = 1 << 3
SCOPES = ("bot", "applications.commands")
_APP_ID = re.compile(r"^\d{17,20}$")


def permission_value() -> int:
    total = 0
    for bit in PERMISSIONS.values():
        total |= bit
    return total


def invite_url(application_id: str, guild_id: str = "") -> str:
    """Endereço que a pessoa dona do servidor abre para adicionar o bot. O id da aplicação não é segredo."""
    app = application_id.strip()
    if not _APP_ID.match(app):
        raise ValueError("O id da aplicação tem de 17 a 20 dígitos. Ele fica em Developer Portal, General Information.")
    query = {"client_id": app, "scope": " ".join(SCOPES), "permissions": str(permission_value())}
    guild = guild_id.strip()
    if guild:
        if not _APP_ID.match(guild):
            raise ValueError("O id do servidor tem de 17 a 20 dígitos.")
        query["guild_id"] = guild
        query["disable_guild_select"] = "true"
    return "https://discord.com/oauth2/authorize?" + urllib.parse.urlencode(query, quote_via=urllib.parse.quote)


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Uso: congo-discord-convite ID_DA_APLICACAO [ID_DO_SERVIDOR]")
    try:
        print(invite_url(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""))
    except ValueError as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
