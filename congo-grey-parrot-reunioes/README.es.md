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
congo-reunioes importar-pasta
congo-reunioes notas --formato json
congo-reunioes resumo
```

## Idiomas

El archivo VTT ya trae el texto en el idioma de la reunión. Cuando la transcripción parte de un audio, Whisper cubre más de 90 idiomas, entre ellos portugués, inglés, español, francés, italiano, ruso, chino, japonés, árabe, bengalí, indonesio y urdu.

## Google Meet

Meet no deja que un programa externo entre a la reunión. El camino oficial es la transcripción que graba el propio Meet (Google Workspace con transcripción activada, [ayuda de Google](https://support.google.com/meet/answer/12849897)). Queda como documento en la carpeta Meet Recordings de Google Drive.

1. En Google Docs, abra la transcripción y use Archivo, Descargar, Microsoft Word (.docx) o Texto sin formato (.txt).
2. Ejecute `./congo-reunioes importar-pasta`. Busca en Descargas los archivos con Transcript, Transcrição o Transcripción en el nombre, importa los nuevos y salta los que ya entraron. Otra carpeta: `./congo-reunioes importar-pasta ~/Documentos/Reuniones`.
3. `./congo-reunioes resumo --plataforma meet` muestra el resumen: frases principales de la propia reunión, decisiones, tareas y preguntas. `./congo-reunioes notas --plataforma meet` muestra quién dijo qué.

El archivo original no se modifica. Nada sale de la computadora. El resumen no usa IA: elige frases que ya están en la transcripción, así que no inventa nada. `--frases 5` define el tamaño y `--formato json` sirve para otro programa. Desde Claude, use las herramientas MCP `resumir_reuniao` y `resumir_texto`.

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
