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
congo-reunioes notas --formato json
```

## 语言

VTT 文件里已经是会议所用语言的文字。如果从音频开始转写，Whisper 支持 90 多种语言，包括葡萄牙语、英语、西班牙语、法语、意大利语、俄语、中文、日语、阿拉伯语、孟加拉语、印尼语和乌尔都语。
