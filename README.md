# Project Congo Grey Parrot

Dois programas locais, independentes, com o nome científico *Psittacus erithacus*. Um roda no computador. O outro é o aplicativo de celular. Nenhum dos dois exige conta nem servidor próprio.

O repositório e o commit estão em [github.com/thaynabds/CongoGreyParrot](https://github.com/thaynabds/CongoGreyParrot).

Nesta máquina já existem o programa de Linux e um APK de teste. Não há instalador de Windows, porque esse pacote só pode ser gerado no próprio Windows. Fonte: [PyInstaller](https://pyinstaller.org/en/stable/usage.html).

| Programa | Onde roda | Arquivo |
|---|---|---|
| Congo Grey Parrot para computador | Linux | Pasta local `congo-grey-parrot-desktop/dist/congo-grey-parrot/`. O instalador está em [instalar-linux.sh](https://github.com/thaynabds/CongoGreyParrot/blob/main/congo-grey-parrot-desktop/instalar-linux.sh). |
| Congo Grey Parrot para celular | Android 8 ou mais novo | [CongoGreyParrot-debug.apk](https://github.com/thaynabds/CongoGreyParrot/blob/main/congo-grey-parrot-android/CongoGreyParrot-debug.apk). É um APK de teste, assinado com a chave de depuração, não o pacote da Play Store. |

A descrição longa do que o projeto pretende cobrir, com as fontes do Whisper e do Parolu, está em [docs/DESCRICAO.md](https://github.com/thaynabds/CongoGreyParrot/blob/main/docs/DESCRICAO.md).

## Computador

Transcreve com faster-whisper, lê texto com Piper ou espeak-ng, traduz fala para inglês, edita legenda, converte mídia com FFmpeg e grava documentos. O áudio e o texto ficam no computador. A rede só entra quando a pessoa confirma o download de um modelo ou de uma voz.

Para abrir a partir do código:

```bash
cd congo-grey-parrot-desktop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[transcribe,speech,dev]"
congo-grey-parrot
```

No Windows, o ambiente é `.venv\Scripts\activate`. FFmpeg e espeak-ng são opcionais e vêm do sistema. O instalador do FFmpeg está em [ffmpeg.org/download.html](https://ffmpeg.org/download.html).

| Tela | O que faz |
|---|---|
| Início | Abre as outras funções. |
| Transcrever | Transcreve um ou vários arquivos. Detecta o idioma ou usa o idioma escolhido. Salva TXT, MD, DOCX, PDF, SRT, VTT, ASS, TSV, JSON ou JSONL. |
| Texto para voz | Abre texto, lê, para, ajusta velocidade e salva WAV. MP3 e outros formatos só se o FFmpeg estiver instalado. |
| Traduzir | Traduz fala para inglês com modelo multilíngue. O modelo turbo não entra nessa tarefa. |
| Legendas | Edita tempos e texto, e pode gravar a legenda no vídeo. |
| Converter mídia | Converte o arquivo para o formato escolhido. |
| Documentos | Abre TXT, Markdown, DOCX ou PDF com texto selecionável e salva de novo. |
| Biblioteca | Lista a pasta de saída e permite gravar uma cópia em outro lugar. |
| Modelos e vozes | Baixa ou remove modelo de transcrição e voz Piper. A pasta é escolhida antes do download. |
| Histórico | Mostra as exportações feitas neste computador. Limpar o histórico não apaga os arquivos. |
| Configurações | Tema claro, escuro, alto contraste, Kuro, PinkVoid, RedVoid ou YellowVoid. Também há filtro de cor, tamanho da letra e pasta padrão de saída. |

Cada resultado abre o seletor de arquivo. A pessoa escolhe nome e pasta. O modelo de transcrição e a voz também pedem a pasta antes de baixar.

Os testes locais:

```bash
pytest
```

## Celular

O aplicativo grava, lê e guarda arquivos no aparelho. Não transcreve com Whisper. A gravação pode ser salva e aberta depois no programa de computador.

| Tela | O que faz |
|---|---|
| Início | Atalhos para gravar, ler e ver arquivos. |
| Gravar | Grava pelo microfone. Depois da gravação, a pessoa escolhe a pasta e o nome. |
| Ler | Lê o texto com uma voz instalada que não usa a rede. Ajusta a velocidade. Salvar texto e salvar áudio abrem o seletor do Android. |
| Arquivos | Lista as cópias guardadas no aplicativo, compartilha ou exclui. |
| Ajustes | Tema claro, escuro, alto contraste, Kuro, PinkVoid, RedVoid ou YellowVoid, e filtro de cor. |

O microfone só é pedido quando a gravação começa. O aplicativo não pede acesso a todo o armazenamento e não tem permissão de internet. O backup automático está desligado.

Para gerar o APK, abra a pasta `congo-grey-parrot-android` no [Android Studio](https://developer.android.com/studio).

## Onde os arquivos vão

| Ação | Computador | Celular |
|---|---|---|
| Salvar texto, áudio, legenda, documento ou conversão | Seletor com nome e pasta | Seletor do Android com nome e pasta |
| Baixar modelo ou voz | Seletor de pasta, antes do download | Esta versão não baixa modelo nem voz |
| Cópia interna | A pasta padrão fica em Configurações | A lista Arquivos guarda uma cópia na pasta privada do aplicativo |

## Licenças e fontes

O código destes dois programas ainda não tem uma licença de distribuição escolhida.

- Whisper, licença MIT: [github.com/openai/whisper](https://github.com/openai/whisper)
- faster-whisper: [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Piper, GPL-3.0 ou posterior: [github.com/OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)
- Vozes, cada uma com o próprio MODEL_CARD: [huggingface.co/rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)
- Parolu, referência de leitura local: [github.com/wbernard/parolu](https://github.com/wbernard/parolu)
- FFmpeg: [ffmpeg.org](https://ffmpeg.org/)
- Seletor de arquivo do Android: [CreateDocument](https://developer.android.com/reference/androidx/activity/result/contract/ActivityResultContracts.CreateDocument)
