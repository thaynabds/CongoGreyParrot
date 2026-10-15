# Project Congo Grey Parrot

Dois programas locais, independentes, com o nome científico *Psittacus erithacus*. Um roda no computador. O outro é o aplicativo de celular. Nenhum dos dois exige conta nem servidor próprio.

O bot de Discord faz parte deste mesmo projeto e deste mesmo repositório, mas é um programa separado. Ele tem pasta, ambiente e dados próprios. Abrir o programa de computador ou o celular não liga o bot, e ligar o bot não abre esses programas. O token fica só na máquina, fora do Git.

O repositório e o commit estão em [github.com/thaynabds/CongoGreyParrot](https://github.com/thaynabds/CongoGreyParrot).

Nesta máquina já existem o programa de Linux e um APK de teste. Não há instalador de Windows, porque esse pacote só pode ser gerado no próprio Windows. Fonte: [PyInstaller](https://pyinstaller.org/en/stable/usage.html).

| Programa | Onde roda | Arquivo |
|---|---|---|
| Congo Grey Parrot para computador | Linux | Pasta local `congo-grey-parrot-desktop/dist/congo-grey-parrot/`. O instalador está em [instalar-linux.sh](https://github.com/thaynabds/CongoGreyParrot/blob/main/congo-grey-parrot-desktop/instalar-linux.sh). |
| Congo Grey Parrot para celular | Android 8 ou mais novo | [CongoGreyParrot-debug.apk](https://github.com/thaynabds/CongoGreyParrot/blob/main/congo-grey-parrot-android/CongoGreyParrot-debug.apk). É um APK de teste, assinado com a chave de depuração, não o pacote da Play Store. |
| Bot de Discord, separado dos dois programas | Servidor de Discord, processo próprio no computador | Pasta `congo-grey-parrot-discord`. Não faz parte da janela nem do aplicativo de celular. |

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

No Windows, o ambiente é `.venv\Scripts\activate`. No Linux, a janela exige `libxcb-cursor0` a partir do Qt 6.5. FFmpeg e espeak-ng são opcionais e vêm do sistema. O instalador do FFmpeg está em [ffmpeg.org/download.html](https://ffmpeg.org/download.html). A exigência da biblioteca do cursor está em [Linux Requirements](https://doc.qt.io/qt-6/linux-requirements.html).

```bash
sudo apt install libxcb-cursor0 ffmpeg espeak-ng
```

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

## Discord

O bot faz parte do Project Congo Grey Parrot, na pasta `congo-grey-parrot-discord`, e não é a janela do computador nem o aplicativo de celular. Ele entra na chamada, transcreve ao vivo com o nome de quem falou e resume o que cada pessoa disse e quando. Com `/vtt conectar` ele guarda o link ou o webhook de uma mesa virtual, esteja ela na lista ou não. O bot não entra na conta dessas plataformas. Também rola dados, guarda ficha, iniciativa, presença, inventário e XP, toca sons locais e envia imagens. Cada função liga e desliga. A transcrição ao vivo começa desligada.

A consulta de magia e monstro não copia o livro. Ela pergunta à [Open5e](https://open5e.com/) e cita a fonte. O aplicativo do bot é criado em [Discord Developer Portal](https://discord.com/developers/applications). A recepção de áudio da chamada usa [discord-ext-voice-recv](https://github.com/imayhaveborkedit/discord-ext-voice-recv).

```bash
cd congo-grey-parrot-discord
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[voz,transcribe]"
cp .env.example .env
```

Preencha `DISCORD_TOKEN` e `CONGO_DISCORD_OWNER_ID` no `.env` e exporte essas variáveis antes de `congo-discord`. Não commite o `.env`. Para uma função nova, coloque um arquivo `.py` na pasta `plugins`, reinicie o bot e use `/funcoes ativar`.

## Onde os arquivos vão

| Ação | Computador | Celular |
|---|---|---|
| Salvar texto, áudio, legenda, documento ou conversão | Seletor com nome e pasta | Seletor do Android com nome e pasta |
| Baixar modelo ou voz | Seletor de pasta, antes do download | Esta versão não baixa modelo nem voz |
| Cópia interna | A pasta padrão fica em Configurações | A lista Arquivos guarda uma cópia na pasta privada do aplicativo |

## Licenças e fontes

O código destes programas ainda não tem uma licença de distribuição escolhida.

- Whisper, licença MIT: [github.com/openai/whisper](https://github.com/openai/whisper)
- faster-whisper: [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Piper, GPL-3.0 ou posterior: [github.com/OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)
- Vozes, cada uma com o próprio MODEL_CARD: [huggingface.co/rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)
- Parolu, referência de leitura local: [github.com/wbernard/parolu](https://github.com/wbernard/parolu)
- FFmpeg: [ffmpeg.org](https://ffmpeg.org/)
- Seletor de arquivo do Android: [CreateDocument](https://developer.android.com/reference/androidx/activity/result/contract/ActivityResultContracts.CreateDocument)
- Discord, comandos de aplicativo: [discord.py interactions](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
- Open5e: [open5e.com](https://open5e.com/)
