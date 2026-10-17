# Congo Grey Parrot 的 MCP

> 语言: [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | **中文**

每个程序都有真正的 MCP 服务，使用官方 `mcp` 包。协议说明在 [modelcontextprotocol.io](https://modelcontextprotocol.io/)。Python 包在 [PyPI](https://pypi.org/project/mcp/)。

手机本身不会说 MCP。Android 桥接程序跑在这台电脑上。

## 连接 Cursor

不含密钥的示例在仓库根目录的 [mcp.json](../mcp.json)。把这四段复制到 Cursor 的 MCP 设置。传输方式是 stdio：Cursor 启动程序并直接对话，不开放网络端口。

先在每个 Python 程序文件夹里：

```bash
pip install -e ".[mcp]"
```

命令：

```bash
congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

如果改成 HTTP，端口是：电脑 8765，会议 8766，Discord 8767，手机桥 8768。

## 连接网站或其他服务器

```bash
CONGO_MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8765 \
  congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

这一版包的 HTTP 路径是 `/mcp`（streamable HTTP）。只有需要旧的 `/sse` 时才设置 `CONGO_MCP_TRANSPORT=sse`。

如果没有 `MCP_TOKEN`，程序会在 `~/.local/share/congo-grey-parrot/mcp.token` 生成一次密钥，权限 600，并且只打印这个路径。请求必须带 `Authorization: Bearer`，内容是该文件。否则返回 401。

`MCP_HOST` 默认是 `127.0.0.1`，别的电脑连不上。要在网络上开放，请设置主机并保管密钥。不要公开令牌文件。

音频和转写文件必须留在运行服务的账户的个人文件夹里。
