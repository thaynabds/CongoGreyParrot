# Congo Grey Parrot, Discord

> Language: [Português](README.md) | **English** | [Español](README.es.md) | [中文](README.zh.md)

Bot for a Discord server. It can join a voice channel, transcribe live with the speaker's name, play audio, roll dice and store character sheets. Each feature turns on or off with `/funcoes ativar` and `/funcoes desativar`. Live transcription starts off.

## Install

From the repository folder:

```bash
./instalar.sh 3
```

The script creates the environment, installs dependencies and creates `.env` if it does not exist yet.

1. Open `congo-grey-parrot-discord/.env`.
2. Paste `DISCORD_TOKEN` and `CONGO_DISCORD_OWNER_ID`.
3. Create the bot app in the [Discord Developer Portal](https://discord.com/developers/applications).
4. Start the bot with `congo-grey-parrot-discord/iniciar.sh`.

Slash commands are typed in Discord, inside the server, after the bot is online. They are not terminal commands.

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

Do not commit the `.env` file.
