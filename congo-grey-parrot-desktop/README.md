# Congo Grey Parrot para computador

O quadro completo dos dois programas, com o que cada um faz, está no [README da pasta principal](../README.md).

Windows e Linux. Transcreve com faster-whisper, lê com Piper ou espeak-ng, exporta legendas e documentos, e converte mídia com FFmpeg. Salvar abre o seletor de nome e pasta. Baixar modelo ou voz também pede a pasta antes.

```bash
cd congo-grey-parrot-desktop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[transcribe,speech,dev]"
congo-grey-parrot
```

No Windows, ative o ambiente com `.venv\Scripts\activate`.

FFmpeg: [ffmpeg.org/download.html](https://ffmpeg.org/download.html)

Leitura sem voz Piper:

```bash
sudo apt install espeak-ng
```

Testes: `pytest`
