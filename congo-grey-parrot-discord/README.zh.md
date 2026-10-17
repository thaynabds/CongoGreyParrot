# Congo Grey Parrot，Discord

> 语言: [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | **中文**

用于 Discord 服务器的机器人。可以加入语音频道，按说话人姓名实时转写，播放音频，掷骰，并保存角色卡。每项功能用 `/funcoes ativar` 和 `/funcoes desativar` 开关。实时转写默认关闭。

## 安装

在仓库文件夹中，一条命令：

```bash
./instalar.sh 3
```

脚本会安装程序、音频、语音、转写和音乐。它创建只有你能读的 `.env`。如果令牌还是空的，脚本会说明 [discord.com/developers/applications](https://discord.com/developers/applications) 上的点击步骤，并在终端里隐藏输入令牌和主人 ID。它还会添加菜单快捷方式 Congo Grey Parrot Discord 和命令 `congo-discord`。如果文件里已经有令牌，最后会启动机器人。

仍然需要打开 Discord 网站来创建应用、复制令牌并邀请机器人。令牌不会进入 Git。

斜杠命令要在 Discord 服务器里输入，而且机器人必须已经在线。它们不是终端命令。

## MCP

机器人也可以启动 MCP 服务，使用官方 `mcp` 包。在 Cursor 里用 stdio：

```bash
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
```

给网站或其他服务器用时，在本文件夹运行：

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8767 .venv/bin/congo-discord-mcp
```

密钥保存在 `~/.local/share/congo-grey-parrot/mcp.token`。没有 `Authorization: Bearer` 的请求会被拒绝。说明见 [mcp/README.zh.md](../mcp/README.zh.md)。

## 实时转写的语言

Whisper 支持 90 多种语言，包括葡萄牙语、英语、西班牙语、法语、意大利语、俄语、中文、日语、阿拉伯语、孟加拉语、印尼语和乌尔都语。模型只需下载一次。实时转写在运行机器人的电脑上用 faster-whisper 完成。

## 主要命令

| 命令组 | 作用 |
|---|---|
| `/dados` | 掷骰 |
| `/ficha` | 角色属性 |
| `/iniciativa` | 回合顺序 |
| `/reuniao` | 加入通话并实时转写 |
| `/musica` | 播放 YouTube、Spotify、已存列表或上传的文件 |
| `/funcoes` | 打开或关闭功能 |
| `/arquivo` | 转写上传的音频或朗读文字 |
| `/handout` | 向频道或某位玩家发送不超过 8 MB 的图片、视频或其他文件 |
| `/navegador` | 在这台电脑上把 Discord 接到 Foundry VTT 和 Roll20 |

## Foundry VTT

在 Foundry 的初始页面打开模块，点击安装模块，粘贴：

```
https://raw.githubusercontent.com/thaynabds/CongoGreyParrot/main/congo-grey-parrot-discord/foundry/congo-grey-parrot/module.json
```

Foundry 会自己下载安装包。这个安装方式见 [Add-on Modules](https://foundryvtt.com/article/modules/)。然后在世界里启用 Congo Grey Parrot。1.1.1 版也会双向传递不超过 8 MB 的图片、视频和其他文件。可执行文件、HTML 和 SVG 不会进入。旧版本在同一模块页面更新。机器人留在打开浏览器的那台电脑上，模块只访问 `http://127.0.0.1:7477`。

不要把 `.env` 提交到 Git。
