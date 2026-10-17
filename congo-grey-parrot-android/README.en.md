# Congo Grey Parrot, phone

> Language: [Português](README.md) | **English** | [Español](README.es.md) | [中文](README.zh.md)

Android 8 or newer. Records audio from the microphone and reads text aloud with a voice already installed on the phone. It does not use the internet and does not transcribe with Whisper. Open the recording in the desktop app to transcribe it.

## Install

1. Copy [CongoGreyParrot-debug.apk](CongoGreyParrot-debug.apk) to the phone.
2. Open the file.
3. If Android blocks it, allow installs from that app: [install unknown apps](https://support.google.com/android/answer/2664792).

To rebuild the APK, in this folder: `./gradlew assembleDebug`.

## Screens

| Screen | What it does |
|---|---|
| Home | Shortcuts to record, read and files |
| Record | Records from the microphone and asks for folder and name |
| Read | Reads text with an offline voice and speed control |
| Files | Lists, shares or deletes copies kept by the app |
| Settings | Theme and color filter |

The microphone is requested only when recording starts.

## MCP

The phone app does not open a server. The bridge runs on the computer, with the official `mcp` package:

```bash
congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

It reports the APK path and the install steps. If `adb` is installed, it can also install and open the app on a connected phone. HTTP:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8768 congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

Details in [mcp/README.en.md](../mcp/README.en.md).
