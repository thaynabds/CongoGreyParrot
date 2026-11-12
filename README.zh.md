# Project Congo Grey Parrot

> 语言: [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | **中文**

四个互不依赖的程序，名称来自非洲灰鹦鹉 *Psittacus erithacus*。每个程序有自己的文件夹、环境和数据。

**作者：** [Thayná Batista da Silva](https://github.com/thaynabds)

| 程序 | 平台 | 安装 |
|---|---|---|
| 电脑 | Linux | `./instalar.sh 1` |
| 手机 | Android 8 或更新 | `./instalar.sh 2` |
| Discord 机器人 | Discord 服务器 | `./instalar.sh 3` |
| 会议笔记 | Linux，读取 Teams、Meet 或 Zoom 导出的文件 | `./instalar.sh 4` |

在 Linux 上，进入本文件夹打开终端，运行 `./instalar.sh`。菜单会询问要安装哪一个。不需要会编程。

### 通过 Flathub

电脑程序也正在发布到 Linux 应用商店 [Flathub](https://flathub.org/apps/io.github.thaynabds.CongoGreyParrot)。Flathub 审核通过后，可在 GNOME Software 和 KDE Discover 中找到，或运行：

```bash
flatpak install flathub io.github.thaynabds.CongoGreyParrot
```

在 Flatpak 中，程序只能访问音乐、视频、文档和下载文件夹。清单文件在 [congo-grey-parrot-desktop/flatpak](congo-grey-parrot-desktop/flatpak)。

## AI Conector

每个程序都有一个明确标出的 **AI Conector** 入口，AI（Claude Desktop、Cursor、Claude Code 或其他 MCP 客户端）可以由此连接并使用程序：电脑版侧边菜单的 **AI Conector**、手机版的 **AI Conector** 标签页、Discord 的 `/conector`，以及终端里的 `congo-reunioes conector`。

```bash
python3 mcp/registrar_claude.py
```

这会把四个程序都注册到 Claude Desktop 和 Cursor。重启 AI 应用后，让它“列出 congo-desktop 的工具”即可确认。只用 stdio，不开网络端口；只读写个人文件夹中的文件，不碰隐藏文件夹；删除、在 Discord 发帖或收听通话都需要 AI 先问你，再用 `confirmar=true`。完整工具列表：[mcp/README.md](mcp/README.md)。

## 各自做什么

* **电脑。** 用 Whisper 转写语音（90 多种语言，包括葡萄牙语、英语、西班牙语、法语、意大利语、俄语、中文、日语、阿拉伯语、孟加拉语、印尼语和乌尔都语），朗读文字，编辑字幕，转换媒体。详见 [电脑版说明](congo-grey-parrot-desktop/README.zh.md)。
* **手机。** 录音并用离线语音朗读。详见 [手机版说明](congo-grey-parrot-android/README.zh.md)。
* **Discord。** 加入语音频道，可以实时转写、播放音频并使用桌游命令。详见 [Discord 说明](congo-grey-parrot-discord/README.zh.md)。
* **会议。** 读取会议软件已经导出的转写文件，包括从 Google Docs 下载的 Google Meet 转写（`congo-reunioes importar-pasta`）。详见 [会议说明](congo-grey-parrot-reunioes/README.zh.md)。
* **摘要。** 每个程序都能做摘要：电脑版的“摘要”页面、手机版的“朗读”页面、Discord 的 `/reuniao resumo` 和 `/arquivo resumir`、`congo-reunioes resumo`，以及 MCP 工具 `resumir_texto`、`resumir_arquivo` 和 `resumir_reuniao`。摘要从原文中挑选主要句子，并列出决定、任务和问题。它离线运行，不使用 AI，因此不会编造内容。

完整的葡萄牙语技术说明在 [README.md](README.md)。

## 许可证

本项目采用 GPL-3.0 或更高版本许可证。见 [LICENSE](LICENSE)。
