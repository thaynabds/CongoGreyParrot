# Congo Grey Parrot, reuniones

> Idioma: [Português](README.md) | [English](README.en.md) | **Español** | [中文](README.zh.md)

Lee la transcripción que Teams, Google Meet, Zoom, Webex o Jitsi ya exportó, y anota quién dijo qué. El programa no entra en la llamada.

Un audio grabado solo con un micrófono no separa a las personas. En ese caso la nota queda como grabación local, sin nombre de hablante.

## Instalar

```bash
./instalar.sh 4
```

Listar plataformas, importar y ver notas no pide bibliotecas extra. Transcribir un archivo de audio sí usa el modelo Whisper, instalado con el entorno de Python.

## Usar

```bash
congo-reunioes plataformas
congo-reunioes importar exemplo-teams.vtt --plataforma teams
congo-reunioes notas
congo-reunioes notas --formato json
```

## Idiomas

El archivo VTT ya trae el texto en el idioma de la reunión. Cuando la transcripción parte de un audio, Whisper cubre más de 90 idiomas, entre ellos portugués, inglés, español, francés, italiano, ruso, chino, japonés, árabe, bengalí, indonesio y urdu.
