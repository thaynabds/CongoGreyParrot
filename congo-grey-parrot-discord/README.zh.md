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

## 把机器人加入你的服务器

机器人是一个 Discord 应用。加入某个服务器后，浏览器版 Discord 和电脑应用里都会显示，因为两者用的是同一个账号。每个服务器都需要单独的邀请。

1. 在 [Discord Developer Portal](https://discord.com/developers/applications) 打开（或新建）应用，在 General Information 复制 Application ID。在 Bot 页面生成令牌，粘贴到本文件夹 `.env` 文件的 `DISCORD_TOKEN=` 一行。不要把令牌发到聊天或 Git 里。
2. 生成邀请：`.venv/bin/congo-discord-convite 应用ID`。只针对一个服务器：`.venv/bin/congo-discord-convite 应用ID 服务器ID`。
3. 用管理该服务器的账号打开链接并授权。每个服务器重复一次。

邀请只请求 查看频道、发送消息、附加文件、连接 和 说话 权限。机器人不读取消息文字，不做管理，也不请求管理员权限。

## 保持运行

`./servico.sh instalar` 为当前用户创建 systemd 服务（无需 sudo），登录时启动机器人，出错后自动重启。`./servico.sh status` 查看状态，`./servico.sh log` 查看日志，`./servico.sh remover` 撤销。网络断开时 discord.py 会自动重连。只停止不删除：`systemctl --user stop congo-discord`。

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
| `/reuniao` | 加入通话并实时转写。`resumo` 显示主要句子、决定、任务和问题；`transcricao` 显示全部内容 |
| `/musica` | 播放 YouTube、Spotify、已存列表或上传的文件 |
| `/funcoes` | 打开或关闭功能 |
| `/arquivo` | 转写上传的音频，为 TXT、MD、VTT 或 SRT 做摘要（`resumir`），或朗读文字 |
| `/handout` | 向频道或某位玩家发送不超过 8 MB 的图片、视频或其他文件 |
| `/navegador` | 在这台电脑上把 Discord 接到 Foundry VTT 和 Roll20 |

摘要在本机完成，只使用对话中的原句，不使用 AI。机器人第一次启动时，如果还没有头像，会自动使用电脑版的鹦鹉图标。

## Foundry VTT

在 Foundry 的初始页面打开模块，点击安装模块，粘贴：

```
https://raw.githubusercontent.com/thaynabds/CongoGreyParrot/main/congo-grey-parrot-discord/foundry/congo-grey-parrot/module.json
```

Foundry 会自己下载安装包。这个安装方式见 [Add-on Modules](https://foundryvtt.com/article/modules/)。然后在世界里启用 Congo Grey Parrot。1.2.1 版修复了一个漏洞：从 Discord 发来的文件名可能向 Foundry 聊天注入代码；主持人的浏览器现在只获取 Foundry 自身的媒体。自 1.2.0 起需要中继令牌：运行 `/navegador token`（仅服务器管理员可见），粘贴到模块设置 Token do relay。它也会双向传递不超过 8 MB 的图片、视频和其他文件。可执行文件、HTML 和 SVG 不会进入。旧版本在同一模块页面更新。机器人留在打开浏览器的那台电脑上，模块只访问 `http://127.0.0.1:7477`。

不要把 `.env` 提交到 Git。
