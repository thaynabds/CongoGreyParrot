# Congo Grey Parrot, Discord

> Idioma: [Português](README.md) | [English](README.en.md) | **Español** | [中文](README.zh.md)

Bot para un servidor de Discord. Entra en el canal de voz, puede transcribir en vivo con el nombre de quien habla, reproducir audio, tirar dados y guardar fichas. Cada función se enciende o apaga con `/funcoes ativar` y `/funcoes desativar`. La transcripción en vivo empieza apagada.

## Instalar

En la carpeta del repositorio:

```bash
./instalar.sh 3
```

El script crea el entorno, instala las dependencias y genera `.env` si todavía no existe.

1. Abra `congo-grey-parrot-discord/.env`.
2. Pegue `DISCORD_TOKEN` y `CONGO_DISCORD_OWNER_ID`.
3. Cree la aplicación en el [Discord Developer Portal](https://discord.com/developers/applications).
4. Encienda el bot con `congo-grey-parrot-discord/iniciar.sh`.

Los comandos con `/` se escriben en Discord, dentro del servidor, cuando el bot ya está en línea. No son comandos de la terminal.

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

No suba el archivo `.env` a Git.
