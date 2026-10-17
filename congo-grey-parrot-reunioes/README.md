# Congo Grey Parrot, reuniões

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Lê a transcrição que o Teams, o Google Meet, o Zoom, o Webex ou o Jitsi já exportou, e anota quem falou o quê. O programa não entra na chamada.

Um áudio gravado só pelo microfone não separa as pessoas. Nesse caso a nota fica como gravação local, sem nome de locutor.

## Instalar

```bash
./instalar.sh 4
```

Listar plataformas, importar e ver notas não precisa de biblioteca extra. A transcrição de um arquivo de áudio é que usa o modelo Whisper, instalado junto com o ambiente Python.

## Usar

```bash
congo-reunioes plataformas
congo-reunioes importar exemplo-teams.vtt --plataforma teams
congo-reunioes notas
congo-reunioes notas --formato json
```

## Idiomas

O arquivo VTT já traz o texto no idioma da reunião. Quando a transcrição parte de um áudio, o Whisper cobre mais de 90 idiomas, entre eles português, inglês, espanhol, francês, italiano, russo, chinês, japonês, árabe, bengali, indonésio e urdu.

Ajuda para exportar a transcrição: [Teams](https://support.microsoft.com/office) e [Google Meet](https://support.google.com/meet).
