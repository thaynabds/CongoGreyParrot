# Congo Grey Parrot, Discord

> Idioma: [Português](README.md) | [English](README.en.md) | **Español** | [中文](README.zh.md)

Bot para un servidor de Discord. Entra en el canal de voz, puede transcribir en vivo con el nombre de quien habla, reproducir audio, tirar dados y guardar fichas. Cada función se enciende o apaga con `/funcoes ativar` y `/funcoes desativar`. La transcripción en vivo empieza apagada.

## Instalar

En la carpeta del repositorio, un comando:

```bash
./instalar.sh 3
```

El script instala el programa, el audio, la voz, la transcripción y la música. Crea `.env` para que solo usted pueda leerlo. Si el token está vacío, explica los clics en [discord.com/developers/applications](https://discord.com/developers/applications) y pide el token en silencio en la terminal, junto con el ID del dueño. También crea el acceso Congo Grey Parrot Discord en el menú y el comando `congo-discord`. Si el token ya está en el archivo, enciende el bot al final.

El sitio de Discord sigue siendo necesario para crear la aplicación, copiar el token e invitar al bot. El token no entra en Git.

Los comandos con `/` se escriben en Discord, dentro del servidor, cuando el bot ya está en línea. No son comandos de la terminal.

## MCP

El bot también abre un servidor MCP, con el paquete oficial `mcp`. En Cursor, el transporte es stdio:

```bash
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
```

Para un sitio u otro servidor, en esta carpeta:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8767 .venv/bin/congo-discord-mcp
```

El secreto queda en `~/.local/share/congo-grey-parrot/mcp.token`. La dirección rechaza pedidos sin `Authorization: Bearer`. Detalles en [mcp/README.es.md](../mcp/README.es.md).

## Idiomas de la transcripción en vivo

Whisper cubre más de 90 idiomas, entre ellos portugués, inglés, español, francés, italiano, ruso, chino, japonés, árabe, bengalí, indonesio y urdu. El modelo se descarga una vez. La transcripción corre con faster-whisper en la computadora que hospeda el bot.

## Comandos principales

| Grupo | Función |
|---|---|
| `/dados` | Tiradas de dados |
| `/ficha` | Atributos del personaje |
| `/iniciativa` | Orden de turno |
| `/reuniao` | Entra en la llamada y transcribe en vivo |
| `/musica` | Reproduce YouTube, Spotify, una lista o un archivo |
| `/funcoes` | Enciende o apaga funciones |
| `/arquivo` | Transcribe un audio enviado o lee un texto |
| `/handout` | Envía imagen, vídeo o archivo de hasta 8 MB al canal o a un jugador |
| `/navegador` | Conecta Discord con Foundry VTT y Roll20 en esta computadora |

## Foundry VTT

En la pantalla inicial de Foundry, abra Módulos, pulse Instalar módulo y pegue:

```
https://raw.githubusercontent.com/thaynabds/CongoGreyParrot/main/congo-grey-parrot-discord/foundry/congo-grey-parrot/module.json
```

Foundry descarga el paquete. Ese instalador está descrito en [Add-on Modules](https://foundryvtt.com/article/modules/). Después active Congo Grey Parrot dentro del mundo. La versión 1.1.1 también pasa imagen, vídeo y otros archivos de hasta 8 MB en los dos sentidos. No entran ejecutables, HTML ni SVG. Una copia antigua se actualiza en la misma pantalla de Módulos. El bot queda en la computadora donde el navegador está abierto, y el módulo solo llama a `http://127.0.0.1:7477`.

No suba el archivo `.env` a Git.
