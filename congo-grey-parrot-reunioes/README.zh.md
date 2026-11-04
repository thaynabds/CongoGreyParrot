# Congo Grey Parrot，会议

> 语言: [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | **中文**

读取 Teams、Google Meet、Zoom、Webex 或 Jitsi 已经导出的转写，并记下谁说了什么。程序不会加入通话。

只用一个麦克风录下的音频无法区分说话人。这种笔记会标成本地录音，没有姓名。

## 安装

```bash
./instalar.sh 4
```

列出平台、导入和查看笔记不需要额外库。从音频文件转写才会用到 Whisper 模型，它随 Python 环境一起安装。

## 使用

```bash
congo-reunioes plataformas
congo-reunioes importar exemplo-teams.vtt --plataforma teams
congo-reunioes notas
congo-reunioes importar-pasta
congo-reunioes notas --formato json
congo-reunioes resumo
```

## 语言

VTT 文件里已经是会议所用语言的文字。如果从音频开始转写，Whisper 支持 90 多种语言，包括葡萄牙语、英语、西班牙语、法语、意大利语、俄语、中文、日语、阿拉伯语、孟加拉语、印尼语和乌尔都语。

## Google Meet

Meet 不允许外部程序加入会议。官方方式是使用 Meet 自己生成的转写（需开启转写的 Google Workspace，[Google 帮助](https://support.google.com/meet/answer/12849897)）。转写会保存为 Google Drive 中 Meet Recordings 文件夹里的文档。

1. 在 Google Docs 打开转写，选择 文件、下载、Microsoft Word (.docx) 或 纯文本 (.txt)。
2. 运行 `./congo-reunioes importar-pasta`。它在“下载”文件夹中查找文件名含 Transcript 或 Transcrição 的文件，导入新文件并跳过已导入的文件。其他文件夹：`./congo-reunioes importar-pasta ~/文档/会议`。
3. `./congo-reunioes resumo --plataforma meet` 显示摘要：会议中的主要原句、决定、任务和问题。`./congo-reunioes notas --plataforma meet` 显示谁说了什么。

原始文件不会被修改，数据不会离开电脑。摘要不使用 AI：它只挑选转写中已有的句子，因此不会编造内容。`--frases 5` 设置长度，`--formato json` 供其他程序使用。在 Claude 中可使用 MCP 工具 `resumir_reuniao` 和 `resumir_texto`。

## MCP

会议笔记也可以启动 MCP 服务，使用官方 `mcp` 包。在 Cursor 里：

```bash
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

先在本文件夹安装：`pip install -e ".[mcp]"`。

给网站或其他服务器：

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8766 congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

导入的文件必须在个人文件夹里。说明见 [mcp/README.zh.md](../mcp/README.zh.md)。
