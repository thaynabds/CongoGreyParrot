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

## Conectar un sitio u otro servidor

```bash
CONGO_MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8765 \
  congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

En esta versión del paquete la ruta HTTP es `/mcp` (streamable HTTP). Use `CONGO_MCP_TRANSPORT=sse` solo si necesita la ruta antigua `/sse`.

Si no existe `MCP_TOKEN`, el programa crea un secreto una vez en `~/.local/share/congo-grey-parrot/mcp.token`, modo 600, e imprime solo esa ruta. El pedido necesita `Authorization: Bearer` con el contenido del archivo. Si falta, la respuesta es 401.

`MCP_HOST` empieza en `127.0.0.1`, así que otra computadora no entra. Para abrirlo en la red, defina el host y guarde el secreto. No publique el archivo del token.

Los audios y las transcripciones tienen que quedar en la carpeta personal de quien ejecuta el servidor.
