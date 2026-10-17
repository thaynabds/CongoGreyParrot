# Congo Grey Parrot, Desktop

> Language: [Português](README.md) | **English** | [Español](README.es.md) | [中文](README.zh.md)

Linux desktop app. It turns speech into text with Whisper, reads text aloud with Piper or espeak-ng, translates text, edits subtitles, converts media with FFmpeg, and opens TXT, Markdown, DOCX and PDF files. Processing stays on this computer.

## Install

```bash
cd congo-grey-parrot-desktop
./instalar.sh
```

The script checks Python, installs system packages, creates an isolated environment, installs the app, and offers to download the Whisper `base` model.

## Transcription languages

One multilingual model covers more than 90 languages, including Portuguese, English, Spanish, French, Italian, Russian, Chinese, Japanese, Arabic, Bengali, Indonesian and Urdu. On the Transcribe screen, pick a language or leave it on automatic detection.

## Screens

| Screen | What it does |
|---|---|
| Home | Shortcuts and a drop area for files |
| Transcribe | Audio or video to text |
| Text to speech | Reads text and saves audio |
| Translate | Translates written text |
| Subtitles | Edits timing and burns captions into video |
| Convert media | Changes the file format with FFmpeg |
| Documents | Opens and saves TXT, Markdown, DOCX and PDF |
| Models and voices | Downloads Whisper models and Piper voices |
| Settings | Theme, color filter and font size |

## Command line

```bash
source .venv/bin/activate
python -m congo_grey_parrot transcribe audio.mp3 --output_dir ./output --output_format txt
python -m congo_grey_parrot speak "Hello." --output output.wav
python -m congo_grey_parrot translate audio.mp3 --output_dir ./output
```

Tests: `pytest`
