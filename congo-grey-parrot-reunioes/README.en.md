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
