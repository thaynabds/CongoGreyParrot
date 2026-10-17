# Congo Grey Parrot, meetings

> Language: [Português](README.md) | **English** | [Español](README.es.md) | [中文](README.zh.md)

Reads a transcript that Teams, Google Meet, Zoom, Webex or Jitsi already exported, and notes who said what. The program does not join the call.

An audio file recorded only from one microphone cannot separate speakers. That note stays as a local recording, without speaker names.

## Install

```bash
./instalar.sh 4
```

Listing platforms, importing and viewing notes needs no extra library. Transcribing an audio file uses the Whisper model, installed with the Python environment.

## Use

```bash
congo-reunioes plataformas
congo-reunioes importar exemplo-teams.vtt --plataforma teams
congo-reunioes notas
congo-reunioes notas --formato json
```

## Languages

The VTT file already contains the meeting text in whatever language it was written. When transcription starts from audio, Whisper covers more than 90 languages, including Portuguese, English, Spanish, French, Italian, Russian, Chinese, Japanese, Arabic, Bengali, Indonesian and Urdu.

## MCP

Meeting notes also start an MCP server, using the official `mcp` package. In Cursor:

```bash
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

Install first, in this folder: `pip install -e ".[mcp]"`.

For a website or another server:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8766 congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

The imported file must stay inside the home folder. Details in [mcp/README.en.md](../mcp/README.en.md).
