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

## Agregar el bot a sus servidores

El bot es una aplicación de Discord. Una vez agregado a un servidor, aparece igual en Discord del navegador y en la aplicación de escritorio, porque los dos usan la misma cuenta. Cada servidor necesita su propia invitación.

1. En [Discord Developer Portal](https://discord.com/developers/applications), abra la aplicación (o cree una) y copie el Application ID en General Information. En Bot, genere el token y péguelo en el archivo `.env` de esta carpeta, en la línea `DISCORD_TOKEN=`. Nunca pegue el token en un chat ni en Git.
2. Genere la invitación: `.venv/bin/congo-discord-convite ID_DE_LA_APLICACION`. Para un solo servidor: `.venv/bin/congo-discord-convite ID_DE_LA_APLICACION ID_DEL_SERVIDOR`.
3. Abra el enlace con la cuenta que administra el servidor y autorice. Repita para cada servidor suyo.

La invitación pide solo Ver canales, Enviar mensajes, Adjuntar archivos, Conectar y Hablar. El bot no lee el texto de los mensajes, no modera y no pide Administrador.

## Mantenerlo encendido

`./servico.sh instalar` crea un servicio systemd de su usuario (sin sudo). Enciende el bot al iniciar sesión y lo reinicia después de una falla. `./servico.sh status` muestra el estado, `./servico.sh log` muestra el registro y `./servico.sh remover` lo deshace. discord.py se reconecta solo cuando se cae internet. Para detener sin quitar: `systemctl --user stop congo-discord`.

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
| `/reuniao` | Entra en la llamada y transcribe en vivo. `resumo` muestra frases principales, decisiones, tareas y preguntas; `transcricao` muestra todo |
| `/musica` | Reproduce YouTube, Spotify, una lista o un archivo |
| `/funcoes` | Enciende o apaga funciones |
| `/arquivo` | Transcribe un audio enviado, resume un TXT, MD, VTT o SRT (`resumir`) o lee un texto |
| `/handout` | Envía imagen, vídeo o archivo de hasta 8 MB al canal o a un jugador |
| `/navegador` | Conecta Discord con Foundry VTT y Roll20 en esta computadora |

El resumen se hace en esta computadora con frases de la propia conversación, sin IA. La primera vez que se enciende, el bot se pone el ícono del loro del programa de computadora si todavía no tiene avatar.

## Foundry VTT

En la pantalla inicial de Foundry, abra Módulos, pulse Instalar módulo y pegue:

```
https://raw.githubusercontent.com/thaynabds/CongoGreyParrot/main/congo-grey-parrot-discord/foundry/congo-grey-parrot/module.json
```

Foundry descarga el paquete. Ese instalador está descrito en [Add-on Modules](https://foundryvtt.com/article/modules/). Después active Congo Grey Parrot dentro del mundo. La versión 1.2.1 cierra una falla: un nombre de archivo enviado desde Discord podía inyectar código en el chat de Foundry, y el navegador del máster ahora solo busca medios del propio Foundry. Desde la 1.2.0 el módulo exige el token del relay: use `/navegador token` (solo quien administra el servidor) y péguelo en el ajuste Token do relay del módulo. También pasa imagen, vídeo y otros archivos de hasta 8 MB en los dos sentidos. No entran ejecutables, HTML ni SVG. Una copia antigua se actualiza en la misma pantalla de Módulos. El bot queda en la computadora donde el navegador está abierto, y el módulo solo llama a `http://127.0.0.1:7477`.

No suba el archivo `.env` a Git.
