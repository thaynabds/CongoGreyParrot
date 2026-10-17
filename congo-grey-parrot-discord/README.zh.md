# Congo Grey Parrot，Discord

> 语言: [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | **中文**

用于 Discord 服务器的机器人。可以加入语音频道，按说话人姓名实时转写，播放音频，掷骰，并保存角色卡。每项功能用 `/funcoes ativar` 和 `/funcoes desativar` 开关。实时转写默认关闭。

## 安装

在仓库文件夹中：

```bash
./instalar.sh 3
```

脚本会创建环境、安装依赖，并在还没有 `.env` 时生成该文件。

1. 打开 `congo-grey-parrot-discord/.env`。
2. 填入 `DISCORD_TOKEN` 和 `CONGO_DISCORD_OWNER_ID`。
3. 在 [Discord Developer Portal](https://discord.com/developers/applications) 创建机器人应用。
4. 用 `congo-grey-parrot-discord/iniciar.sh` 启动。

斜杠命令要在 Discord 服务器里输入，而且机器人必须已经在线。它们不是终端命令。

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

不要把 `.env` 提交到 Git。
