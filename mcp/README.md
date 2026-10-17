# MCP do Congo Grey Parrot

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Cada programa tem um servidor MCP de verdade, com o pacote oficial `mcp`. A documentação do protocolo está em [modelcontextprotocol.io](https://modelcontextprotocol.io/). O pacote Python está em [PyPI](https://pypi.org/project/mcp/).

O celular não fala MCP sozinho. A ponte do Android roda neste computador.

## Ligar no Cursor

O exemplo sem segredo está em [mcp.json](../mcp.json), na raiz do projeto. Copie esses quatro blocos para a configuração MCP do Cursor. O transporte é stdio: o Cursor abre o programa e conversa por ele, sem porta de rede.

Antes, na pasta de cada programa Python:

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

Portas, se você mudar para HTTP: computador 8765, reuniões 8766, Discord 8767, ponte do celular 8768.

## Ligar um site ou outro servidor

```bash
CONGO_MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8765 \
  congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

Nesta versão do pacote o caminho HTTP é `/mcp` (streamable HTTP). Troque `CONGO_MCP_TRANSPORT=sse` só se precisar da rota antiga `/sse`.

Se a variável `MCP_TOKEN` não existir, o programa cria um segredo uma vez em `~/.local/share/congo-grey-parrot/mcp.token`, com permissão 600, e imprime só esse caminho. O pedido precisa do cabeçalho `Authorization: Bearer` com o conteúdo do arquivo. Sem isso a resposta é 401.

`MCP_HOST` começa em `127.0.0.1`, então outro computador não entra. Para abrir na rede, defina o host e guarde o segredo. Não publique o arquivo do token.

Caminhos de áudio e de transcrição precisam ficar na pasta pessoal de quem roda o servidor.
