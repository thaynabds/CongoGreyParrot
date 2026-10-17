# Congo Grey Parrot, celular

> Idioma: [Português](README.md) | [English](README.en.md) | **Español** | [中文](README.zh.md)

Aplicación para Android 8 o más nuevo. Graba audio con el micrófono y lee texto en voz alta con una voz ya instalada en el teléfono. No usa internet y no transcribe con Whisper. Para transcribir, abra la grabación en el programa de computadora.

## Instalar

1. Copie [CongoGreyParrot-debug.apk](CongoGreyParrot-debug.apk) al teléfono.
2. Abra el archivo.
3. Si Android lo bloquea, permita la instalación desde esa aplicación: [instalar apps desconocidas](https://support.google.com/android/answer/2664792?hl=es).

Para generar el APK de nuevo, en esta carpeta: `./gradlew assembleDebug`.

## Pantallas

| Pantalla | Qué hace |
|---|---|
| Inicio | Atajos para grabar, leer y ver archivos |
| Grabar | Graba con el micrófono y pide carpeta y nombre |
| Leer | Lee texto con voz sin red y ajusta la velocidad |
| Archivos | Lista, comparte o borra copias del app |
| Ajustes | Tema y filtro de color |

El micrófono se pide solo cuando empieza la grabación.

## MCP

La aplicación del teléfono no abre un servidor. El puente corre en la computadora, con el paquete oficial `mcp`:

```bash
congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

Informa la ruta del APK y los pasos. Si `adb` está instalado, también instala y abre la aplicación en el teléfono conectado. HTTP:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8768 congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

Detalles en [mcp/README.es.md](../mcp/README.es.md).
