# Congo Grey Parrot，电脑版

> 语言: [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | **中文**

Linux 桌面程序。用 Whisper 把语音转成文字，用 Piper 或 espeak-ng 朗读文字，翻译文本，编辑字幕，用 FFmpeg 转换媒体，并打开 TXT、Markdown、DOCX 和 PDF。处理都在本机完成。

## 安装

```bash
cd congo-grey-parrot-desktop
./instalar.sh
```

脚本会检查 Python，安装系统软件包，创建独立环境，安装程序，并询问是否下载 Whisper 的 `base` 模型。

## 转写语言

一个多语言模型支持 90 多种语言，包括葡萄牙语、英语、西班牙语、法语、意大利语、俄语、中文、日语、阿拉伯语、孟加拉语、印尼语和乌尔都语。在“转写”页面选择语言，或使用自动检测。

## 界面

| 页面 | 作用 |
|---|---|
| 首页 | 快捷入口和拖放文件区域 |
| 转写 | 把音频或视频变成文字 |
| 文字转语音 | 朗读文字并保存音频 |
| 翻译 | 翻译书面文字 |
| 字幕 | 编辑时间并烧录到视频 |
| 转换媒体 | 用 FFmpeg 更换格式 |
| 文档 | 打开并保存 TXT、Markdown、DOCX、PDF |
| 模型和声音 | 下载 Whisper 模型和 Piper 声音 |
| 设置 | 主题、颜色滤镜和字号 |

## 命令行

```bash
source .venv/bin/activate
python -m congo_grey_parrot transcribe audio.mp3 --output_dir ./output --output_format txt
python -m congo_grey_parrot speak "你好。" --output output.wav
python -m congo_grey_parrot translate audio.mp3 --output_dir ./output
```

测试：`pytest`
