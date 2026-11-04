# MCP de Congo Grey Parrot

> Idioma: [Português](README.md) | [English](README.en.md) | **Español** | [中文](README.zh.md)

Cada programa tiene un servidor MCP real, con el paquete oficial `mcp`. El protocolo está en [modelcontextprotocol.io](https://modelcontextprotocol.io/). El paquete Python está en [PyPI](https://pypi.org/project/mcp/).

El teléfono no habla MCP solo. El puente de Android corre en esta computadora.

## Conectar Cursor

El ejemplo sin secretos está en [mcp.json](../mcp.json), en la raíz. Copie esos cuatro bloques a la configuración MCP de Cursor. El transporte es stdio: Cursor abre el programa y habla con él, sin puerto de red.

Antes, en la carpeta de cada programa Python:

```bash
pip install -e ".[mcp]"
```

Comandos:

```bash
congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

Puertos HTTP, si cambia el transporte: computadora 8765, reuniones 8766, Discord 8767, puente del teléfono 8768.

## Conectar Claude

Claude Desktop y Claude Code corren en su computadora y hablan con estos servidores por stdio, sin abrir puertos.

* **Claude Desktop:** `python3 mcp/registrar_claude.py` escribe los cuatro servidores en `~/.config/Claude/claude_desktop_config.json` con ruta absoluta, mantiene sus otros servidores y guarda una copia `.bak`. Cierre y abra Claude Desktop. Para deshacer: `python3 mcp/registrar_claude.py --remover`.
* **Claude Code:** abra Claude Code en esta carpeta. Lee `.mcp.json` y pregunta si puede usar los servidores.
* **Claude en el navegador (claude.ai):** no ve programas de su computadora. Solo llegaría a un servidor publicado en internet, y este proyecto no publica ninguno.

Herramientas nuevas: `status_bot` (dice si el token está cargado, sin mostrarlo), `ver_log` (registro del servicio con tokens borrados), `link_convite` (invitación con permisos mínimos) e `importar_pasta` (transcripciones de Meet de la carpeta Descargas).

Resumen: `resumir_texto` y `resumir_arquivo` (computadora, archivo de la carpeta personal) y `resumir_reuniao` y `resumir_texto` (reuniones). Eligen frases del propio texto, sin IA y sin internet, y separan decisiones, tareas y preguntas. `frases` va de 0 (automático) a 30.

## Conectar un sitio u otro servidor

```bash
CONGO_MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8765 \
  congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

En esta versión del paquete la ruta HTTP es `/mcp` (streamable HTTP). Use `CONGO_MCP_TRANSPORT=sse` solo si necesita la ruta antigua `/sse`.

Si no existe `MCP_TOKEN`, el programa crea un secreto una vez en `~/.local/share/congo-grey-parrot/mcp.token`, modo 600, e imprime solo esa ruta. El pedido necesita `Authorization: Bearer` con el contenido del archivo. Si falta, la respuesta es 401.

`MCP_HOST` empieza en `127.0.0.1`, así que otra computadora no entra. Para abrirlo en la red, defina el host y guarde el secreto. No publique el archivo del token.

Los audios y las transcripciones tienen que quedar en la carpeta personal de quien ejecuta el servidor.
