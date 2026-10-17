# Congo Grey Parrot, Discord

> Language: [Português](README.md) | **English** | [Español](README.es.md) | [中文](README.zh.md)

Bot for a Discord server. It can join a voice channel, transcribe live with the speaker's name, play audio, roll dice and store character sheets. Each feature turns on or off with `/funcoes ativar` and `/funcoes desativar`. Live transcription starts off.

## Install

From the repository folder, one command:

```bash
./instalar.sh 3
```

The script installs the program, audio, voice, transcription and music. It creates `.env` so only you can read it. If the token is empty, it explains the clicks on [discord.com/developers/applications](https://discord.com/developers/applications) and asks for the token in the terminal without showing it, plus the owner id. It also adds the Congo Grey Parrot Discord menu shortcut and the `congo-discord` command. If the token is already in the file, it starts the bot at the end.

The Discord website is still required to create the application, copy the token and invite the bot. The token is not committed.

Slash commands are typed in Discord, inside the server, after the bot is online. They are not terminal commands.

## MCP

The bot also starts an MCP server, using the official `mcp` package. In Cursor, the transport is stdio:

```bash
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
```

For a website or another server, from this folder:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8767 .venv/bin/congo-discord-mcp
```

The secret is stored in `~/.local/share/congo-grey-parrot/mcp.token`. The address rejects requests without `Authorization: Bearer`. Details in [mcp/README.en.md](../mcp/README.en.md).

## Live transcription languages

Whisper covers more than 90 languages, including Portuguese, English, Spanish, French, Italian, Russian, Chinese, Japanese, Arabic, Bengali, Indonesian and Urdu. The model is downloaded once. Live transcription runs with faster-whisper on the computer that hosts the bot.

## Main commands

| Group | Role |
|---|---|
| `/dados` | Dice rolls |
| `/ficha` | Character attributes |
| `/iniciativa` | Turn order |
| `/reuniao` | Joins the call and transcribes live |
| `/musica` | Plays YouTube, Spotify, a saved list or an uploaded file |
| `/funcoes` | Turns features on or off |
| `/arquivo` | Transcribes an uploaded audio file or reads text |
| `/handout` | Sends an image, video or file, up to 8 MB, to the channel or to one player |
| `/navegador` | Connects Discord to Foundry VTT and Roll20 on this computer |

## Foundry VTT

On the Foundry setup screen, open Modules, choose Install Module, and paste:

```
https://raw.githubusercontent.com/thaynabds/CongoGreyParrot/main/congo-grey-parrot-discord/foundry/congo-grey-parrot/module.json
```

Foundry downloads the package. This is the installer described in [Add-on Modules](https://foundryvtt.com/article/modules/). Then enable Congo Grey Parrot inside the world. Version 1.1.1 also carries images, video and other files up to 8 MB both ways. Executables, HTML and SVG are refused. Update an older copy from the same Modules screen. The bot stays on the computer that has the browser open, and the module only calls `http://127.0.0.1:7477`.

Do not commit the `.env` file.
