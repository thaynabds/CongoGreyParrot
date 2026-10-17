# Congo Grey Parrot，手机版

> 语言: [Português](README.md) | [English](README.en.md) | [Español](README.es.md) | **中文**

适用于 Android 8 或更新版本。用麦克风录音，并用手机上已安装的语音朗读文字。不联网，也不使用 Whisper 转写。要转写时，请在电脑版中打开录音文件。

## 安装

1. 把 [CongoGreyParrot-debug.apk](CongoGreyParrot-debug.apk) 复制到手机。
2. 打开该文件。
3. 如果系统拦截，请允许该来源安装应用：[安装未知应用](https://support.google.com/android/answer/2664792?hl=zh-Hans)。

重新生成 APK，在本目录运行：`./gradlew assembleDebug`。

## 界面

| 页面 | 作用 |
|---|---|
| 首页 | 录音、朗读和文件的入口 |
| 录音 | 用麦克风录音，保存时选择文件夹和文件名 |
| 朗读 | 用离线语音朗读，并可调节速度 |
| 文件 | 列出、分享或删除应用内副本 |
| 设置 | 主题和颜色滤镜 |

只有开始录音时才会请求麦克风权限。

## MCP

手机上的应用本身不开服务器。桥接程序在电脑上运行，使用官方 `mcp` 包：

```bash
congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

它会给出 APK 路径和安装步骤。如果安装了 `adb`，还可以在已连接的手机上安装并打开应用。HTTP：

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8768 congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

说明见 [mcp/README.zh.md](../mcp/README.zh.md)。
