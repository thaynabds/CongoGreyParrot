# Congo Grey Parrot MCP

> Language: [Português](README.md) | **English** | [Español](README.es.md) | [中文](README.zh.md)

Each program has a real MCP server, using the official `mcp` package. The protocol is documented at [modelcontextprotocol.io](https://modelcontextprotocol.io/). The Python package is on [PyPI](https://pypi.org/project/mcp/).

The phone does not speak MCP by itself. The Android bridge runs on this computer.

## Connect Cursor

The example without secrets is [mcp.json](../mcp.json) at the repository root. Copy those four blocks into Cursor's MCP settings. The transport is stdio: Cursor starts the program and talks to it, with no network port.

First, in each Python program folder:

```bash
pip install -e ".[mcp]"
```

Commands:

```bash
congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

HTTP ports, if you switch transport: computer 8765, meetings 8766, Discord 8767, phone bridge 8768.

## Connect a website or another server

```bash
CONGO_MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8765 \
  congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

This package version serves streamable HTTP at `/mcp`. Set `CONGO_MCP_TRANSPORT=sse` only if you need the older `/sse` route.

If `MCP_TOKEN` is missing, the program creates a secret once in `~/.local/share/congo-grey-parrot/mcp.token`, mode 600, and prints only that path. Requests need the header `Authorization: Bearer` with the file contents. Otherwise the response is 401.

`MCP_HOST` defaults to `127.0.0.1`, so another computer cannot connect. To open it on a network, set the host and keep the secret. Do not publish the token file.

Audio and transcript paths must stay inside the home folder of the account that runs the server.
