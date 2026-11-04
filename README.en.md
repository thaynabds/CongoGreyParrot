# Project Congo Grey Parrot

> Language: [Português](README.md) | **English** | [Español](README.es.md) | [中文](README.zh.md)

Four separate programs, named after *Psittacus erithacus*. Each has its own folder, environment and data.

**Author:** [Thayná Batista da Silva](https://github.com/thaynabds)

| Program | Platform | Install |
|---|---|---|
| Computer | Linux | `./instalar.sh 1` |
| Phone | Android 8 or newer | `./instalar.sh 2` |
| Discord bot | A Discord server | `./instalar.sh 3` |
| Meeting notes | Linux, from Teams, Meet or Zoom exports | `./instalar.sh 4` |

On Linux, open a terminal in this folder and run `./instalar.sh`. The menu asks which program to install. You do not need to know programming.

### From Flathub

The computer app is also being published on [Flathub](https://flathub.org/apps/io.github.thaynabds.CongoGreyParrot), the Linux app store. Once Flathub approves it, it shows up in GNOME Software and KDE Discover, or install it with:

```bash
flatpak install flathub io.github.thaynabds.CongoGreyParrot
```

Inside Flatpak the app only sees the Music, Videos, Documents and Downloads folders. The manifest files are in [congo-grey-parrot-desktop/flatpak](congo-grey-parrot-desktop/flatpak).

## What each one does

* **Computer.** Transcribes speech with Whisper (more than 90 languages, including Portuguese, English, Spanish, French, Italian, Russian, Chinese, Japanese, Arabic, Bengali, Indonesian and Urdu), reads text aloud, edits subtitles and converts media. Details: [desktop README](congo-grey-parrot-desktop/README.en.md).
* **Phone.** Records audio and reads text offline. Details: [Android README](congo-grey-parrot-android/README.en.md).
* **Discord.** Joins a voice channel, can transcribe live, play audio and run tabletop commands. Details: [Discord README](congo-grey-parrot-discord/README.en.md).
* **Meetings.** Reads a transcript file the meeting app already exported, including the Google Meet transcript downloaded from Google Docs (`congo-reunioes importar-pasta`). Details: [meetings README](congo-grey-parrot-reunioes/README.en.md).

The full technical description in Portuguese is in [README.md](README.md).

## License

This project is licensed under GPL-3.0-or-later. See [LICENSE](LICENSE).
