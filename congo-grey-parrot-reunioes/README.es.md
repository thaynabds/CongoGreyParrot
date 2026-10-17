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

## MCP

Las notas también abren un servidor MCP, con el paquete oficial `mcp`. En Cursor:

```bash
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

Instale antes, en esta carpeta: `pip install -e ".[mcp]"`.

Para un sitio u otro servidor:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8766 congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

El archivo importado tiene que estar en la carpeta personal. Detalles en [mcp/README.es.md](../mcp/README.es.md).
