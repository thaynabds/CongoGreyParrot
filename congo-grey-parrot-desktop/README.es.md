# Congo Grey Parrot, computadora

> Idioma: [Português](README.md) | [English](README.en.md) | **Español** | [中文](README.zh.md)

Programa de escritorio para Linux. Transcribe voz a texto con Whisper, lee texto en voz alta con Piper o espeak-ng, traduce texto, edita subtítulos, convierte medios con FFmpeg y abre TXT, Markdown, DOCX y PDF. El procesamiento queda en esta computadora.

## Instalar

```bash
cd congo-grey-parrot-desktop
./instalar.sh
```

El script revisa Python, instala paquetes del sistema, crea un entorno aislado, instala el programa y ofrece descargar el modelo Whisper `base`.

## Idiomas de transcripción

Un solo modelo cubre más de 90 idiomas, entre ellos portugués, inglés, español, francés, italiano, ruso, chino, japonés, árabe, bengalí, indonesio y urdu. En la pantalla Transcribir, elija el idioma o deje la detección automática.

## Pantallas

| Pantalla | Qué hace |
|---|---|
| Inicio | Atajos y zona para soltar archivos |
| Transcribir | Audio o video a texto |
| Texto a voz | Lee el texto y guarda el audio |
| Traducir | Traduce texto escrito |
| Subtítulos | Edita tiempos y graba subtítulos en el video |
| Convertir medios | Cambia el formato con FFmpeg |
| Documentos | Abre y guarda TXT, Markdown, DOCX y PDF |
| Modelos y voces | Descarga modelos Whisper y voces Piper |
| Ajustes | Tema, filtro de color y tamaño de letra |

## Línea de comandos

```bash
source .venv/bin/activate
python -m congo_grey_parrot transcribe audio.mp3 --output_dir ./salida --output_format txt
python -m congo_grey_parrot speak "Hola." --output salida.wav
python -m congo_grey_parrot translate audio.mp3 --output_dir ./salida
```

Pruebas: `pytest`

## MCP

El programa también habla MCP, con el paquete oficial `mcp`. En Cursor, transporte stdio:

```bash
congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

Antes, en `congo-grey-parrot-desktop`: `pip install -e ".[mcp]"`.

Para un sitio u otro servidor:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8765 congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

El secreto queda en `~/.local/share/congo-grey-parrot/mcp.token` y no se imprime. Sin `Authorization: Bearer` la dirección rechaza el pedido. Los audios tienen que estar en la carpeta personal. Detalles en [mcp/README.es.md](../mcp/README.es.md).
