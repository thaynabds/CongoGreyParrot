# Project Congo Grey Parrot

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Quatro programas independentes, nomeados a partir do *Psittacus erithacus*. Cada um tem pasta, ambiente e dados próprios. Nenhum depende dos outros para funcionar.

**Autora:** [Thayná Batista da Silva](https://github.com/thaynabds)
**Repositório:** [github.com/thaynabds/CongoGreyParrot](https://github.com/thaynabds/CongoGreyParrot)

| Programa | Plataforma | Instalar |
|---|---|---|
| Computador | Linux | `./instalar.sh 1` |
| Celular | Android 8 ou mais novo | `./instalar.sh 2` |
| Bot de Discord | Servidor de Discord | `./instalar.sh 3` |
| Anotações de reunião | Linux, sobre arquivos exportados do Teams, Meet ou Zoom | `./instalar.sh 4` |

A descrição completa do que o Whisper e o Piper fazem, com as fontes, está em [docs/DESCRICAO.md](https://github.com/thaynabds/CongoGreyParrot/blob/main/docs/DESCRICAO.md).

## Instalar

Na pasta deste repositório, no Linux:

```bash
./instalar.sh
```

O script pergunta qual programa instalar. Também dá para escolher direto: `./instalar.sh 1` para o computador, `2` para o celular, `3` para o Discord e `4` para as reuniões.

## Computador

Programa de desktop para Linux. Transcreve fala para texto com faster-whisper, lê texto em voz alta com Piper ou espeak-ng, traduz fala para inglês, edita legendas, converte mídia com FFmpeg e lida com documentos TXT, Markdown, DOCX e PDF. O áudio e o texto ficam no computador. A rede só é usada quando a pessoa confirma o download de um modelo ou de uma voz.

`./instalar.sh 1` cria o ambiente Python, instala as dependências e coloca o atalho no menu do sistema. A janela exige `libxcb-cursor0` a partir do Qt 6.5, documentado em [Linux Requirements](https://doc.qt.io/qt-6/linux-requirements.html). FFmpeg e espeak-ng são instalados automaticamente se estiverem faltando.

| Tela | O que faz |
|---|---|
| Início | Abre as outras telas. |
| Transcrever | Transcreve um ou vários arquivos. Detecta o idioma ou usa o idioma definido. Salva TXT, MD, DOCX, PDF, SRT, VTT, ASS, TSV, JSON ou JSONL. |
| Texto para voz | Abre texto, lê em voz alta, pausa, ajusta velocidade e salva WAV. MP3 e outros formatos exigem FFmpeg. |
| Traduzir | Traduz fala para inglês com modelo multilíngue. O modelo turbo não aparece nessa tarefa. |
| Legendas | Edita tempos e texto, incorpora faixa de legenda no vídeo ou grava a legenda na imagem. |
| Converter mídia | Converte o arquivo para o formato escolhido via FFmpeg. |
| Documentos | Abre TXT, Markdown, DOCX ou PDF com texto selecionável e salva de novo. |
| Biblioteca | Lista a pasta de saída e permite copiar arquivos para outro lugar. |
| Modelos e vozes | Baixa ou remove modelo de transcrição e voz Piper. A pasta de destino é escolhida antes do download. |
| Histórico | Mostra as exportações feitas neste computador. Limpar o histórico não apaga os arquivos. |
| Configurações | Tema claro, escuro, alto contraste, Kuro, PinkVoid, RedVoid ou YellowVoid. Filtro de cor, tamanho da letra e pasta padrão de saída. |

Cada resultado abre o seletor de arquivo. O modelo de transcrição e a voz pedem a pasta antes de baixar.

Testes locais:

```bash
pytest
```

## Celular

Aplicativo Android para gravar áudio pelo microfone, ler texto em voz alta com uma voz offline e guardar arquivos no aparelho. Não transcreve com Whisper. Uma gravação salva pode ser aberta depois no programa de computador para transcrição.

Para instalar, copie [CongoGreyParrot-debug.apk](https://github.com/thaynabds/CongoGreyParrot/blob/main/congo-grey-parrot-android/CongoGreyParrot-debug.apk) para um Android 8 ou mais novo e abra o arquivo. Se o sistema bloquear, permita a instalação por esse aplicativo, conforme a [documentação do Google](https://support.google.com/android/answer/2664792?hl=pt-BR). `./instalar.sh 2` mostra o mesmo passo a passo.

O APK foi gerado pela linha de comando com o plugin Android Gradle 8.5.2. Para gerar de novo: `cd congo-grey-parrot-android && ./gradlew assembleDebug`. Documentação da montagem: [developer.android.com/build](https://developer.android.com/build).

| Tela | O que faz |
|---|---|
| Início | Atalhos para gravar, ler e ver arquivos. |
| Gravar | Grava pelo microfone. Depois da gravação, escolhe pasta e nome. |
| Ler | Lê texto com uma voz instalada que não usa a rede. Ajusta velocidade. Salvar texto e salvar áudio abrem o seletor do Android. |
| Arquivos | Lista as cópias guardadas no aplicativo, compartilha ou exclui. |
| Ajustes | Tema claro, escuro, alto contraste, Kuro, PinkVoid, RedVoid ou YellowVoid, e filtro de cor. |

O microfone só é pedido quando a gravação começa. O aplicativo não pede acesso amplo ao armazenamento e não tem permissão de internet. O backup automático está desligado.

## Discord

Bot para servidores de Discord. Entra no canal de voz, transcreve ao vivo com o nome de quem falou, resume reuniões, toca áudio de várias fontes, rola dados, guarda fichas, iniciativa, presença, inventário e XP, conecta mesas virtuais e consulta regras na Open5e.

Cada função liga e desliga individualmente com `/funcoes ativar` e `/funcoes desativar`. A transcrição ao vivo começa desligada.

`./instalar.sh 3` instala o bot, pede o token no terminal sem mostrá-lo e cria o atalho do menu. O aplicativo ainda é criado em [Discord Developer Portal](https://discord.com/developers/applications). O servidor MCP está em [mcp/README.md](mcp/README.md).

Os comandos com `/` se digitam no Discord, dentro do servidor, depois que o bot estiver online. Não são comandos do terminal.

Para adicionar uma função nova, coloque um arquivo `.py` na pasta `plugins`, reinicie o bot e use `/funcoes ativar`. Veja `plugins/eco.py` como exemplo mínimo.

### Funções principais

| Grupo de comando | Função |
|---|---|
| `/dados` | Rolagem de dados com expressões como `2d6+3`, vantagem, desvantagem, percentil e pool. |
| `/ficha` | Guarda e rola atributos por jogador. |
| `/iniciativa` | Ordem de turno com adicionar, próximo e limpar. |
| `/regra` | Consulta magia ou monstro na Open5e, com citação da fonte. |
| `/som` | Toca arquivos de áudio locais no canal de voz: fundo em repetição ou efeito sobre o fundo. |
| `/sessao` | Agenda sessões com botões de presença: confirmado, atrasado ou ausente. |
| `/grupo` | Inventário compartilhado: itens, ouro e XP. |
| `/reuniao` | Entra na chamada, transcreve ao vivo com o nome de cada pessoa e gera resumo. |
| `/arquivo` | Transcreve um áudio enviado ou lê um texto com espeak-ng. |
| `/vtt` | Conecta uma mesa virtual por link ou webhook. |
| `/funcoes` | Liga, desliga, adiciona ou remove funções. |
| `/musica` | Toca áudio no canal de voz: YouTube, Spotify, lista de reprodução salva ou arquivo enviado. |
| `/navegador` | Relay de rolagens do navegador para o Discord. Captura dados do Roll20 e do Foundry VTT em tempo real. |

### Música no canal de voz

O bot toca áudio do YouTube e do Spotify usando [yt-dlp](https://github.com/yt-dlp/yt-dlp). Para habilitar, instale o extra e ative a função:

```bash
pip install "congo-grey-parrot-discord[musica]"
```

Depois, no Discord:

```
/funcoes ativar musica
```

| Comando | O que faz |
|---|---|
| `/musica tocar <link ou busca>` | Toca um link do YouTube ou Spotify, ou busca por nome. Adiciona à fila se algo já estiver tocando. |
| `/musica arquivo` | Toca um arquivo de áudio enviado diretamente no comando. Formatos suportados pelo FFmpeg. |
| `/musica pular` | Pula a faixa atual. |
| `/musica parar` | Para tudo, esvazia a fila e sai do canal. |
| `/musica fila` | Mostra as faixas na fila. |
| `/musica playlist criar <nome>` | Cria uma lista de reprodução nomeada para este servidor. |
| `/musica playlist adicionar <nome> <link>` | Adiciona uma faixa a uma lista de reprodução. |
| `/musica playlist tocar <nome>` | Coloca todas as faixas de uma lista na fila e começa a tocar. |
| `/musica playlist ver <nome>` | Mostra as faixas de uma lista. |
| `/musica playlist remover <nome> <posicao>` | Remove uma faixa da lista pelo número de posição. |
| `/musica playlist apagar <nome>` | Apaga uma lista de reprodução inteira. |
| `/musica playlist listar` | Mostra todas as listas criadas neste servidor. |

As listas de reprodução são salvas por servidor em `playlists.json` na pasta de dados do bot. Cada lista pode ter quantas faixas quiser e ser editada a qualquer momento.

O Spotify não disponibiliza o áudio diretamente. O bot extrai o nome da faixa e busca no YouTube via yt-dlp. FFmpeg precisa estar instalado para reprodução: [ffmpeg.org/download.html](https://ffmpeg.org/download.html).

### Relay de rolagens do navegador

O bot e o Foundry precisam rodar no mesmo computador. O módulo do Foundry fica em `congo-grey-parrot-discord/foundry/congo-grey-parrot`. Copie essa pasta para `Data/modules` do Foundry e ative o módulo no mundo. A pasta Data está descrita em [Module Development](https://foundryvtt.com/article/module-development/). O acesso local do Foundry, na instalação padrão, é `http://127.0.0.1:30000`, conforme o [guia de instalação](https://foundryvtt.com/article/installation/).

O módulo usa a API do Foundry (`createChatMessage`, `ChatMessage.create` e `game.users.activeGM`) e fala só com `http://127.0.0.1:7477` ou `http://localhost`. O chat público e as rolagens vão para o canal do Discord. `/dados` e `/navegador falar` voltam para o chat da mesa. Rolagem oculta do Foundry e `/dados oculto` não atravessam.

Se o Foundry estiver em HTTPS, o navegador pode bloquear a chamada para o endereço HTTP local. Nesse caso use o Foundry em HTTP neste computador.

```
/funcoes ativar navegador
/navegador ligar
/navegador canal #rolagens
```

O comando `/navegador modulo` envia o zip do módulo. `/navegador userscript` continua disponível para o Roll20, pelo [Tampermonkey](https://www.tampermonkey.net/).

| Comando | O que faz |
|---|---|
| `/navegador ligar [porta]` | Inicia o servidor local (padrão: porta 7477). |
| `/navegador desligar` | Para o servidor. |
| `/navegador status` | Mostra se o relay está ativo e o canal configurado. |
| `/navegador canal #canal` | Define o canal do Discord onde as rolagens aparecem. |
| `/navegador falar` | Envia um texto do Discord para o chat do Foundry. |
| `/navegador modulo` | Envia o zip do módulo do Foundry. |
| `/navegador userscript` | Envia o arquivo `.user.js` para o Roll20 e para um Foundry sem o módulo. |

### Transcrição ao vivo

A recepção de áudio da chamada usa [discord-ext-voice-recv](https://github.com/imayhaveborkedit/discord-ext-voice-recv). Transcrição local com faster-whisper: [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper). Para habilitar:

```bash
pip install "congo-grey-parrot-discord[voz,transcribe]"
```

Depois ative no Discord:

```
/funcoes ativar reuniao
/reuniao entrar
```

## Reuniões

Anota quem falou o que em reuniões do Teams, Google Meet, Zoom, Webex, Jitsi ou qualquer plataforma que exporte transcrição. O programa não entra na chamada. Ele lê o arquivo de transcrição que a plataforma disponibiliza para download.

Um áudio gravado só pelo microfone não separa os participantes. Nesse caso, a anotação fica como gravação local sem identificação de locutor.

Listar, importar e ver notas não precisa de ambiente virtual. Na pasta `congo-grey-parrot-reunioes`:

```bash
./congo-reunioes plataformas
./congo-reunioes importar exemplo-teams.vtt --plataforma teams
./congo-reunioes notas
```

`./instalar.sh 4` também coloca `congo-reunioes` em `~/.local/bin`. A transcrição de áudio é que exige o ambiente virtual, como explica a documentação do [venv](https://docs.python.org/3/library/venv.html).

Ajuda para exportar a transcrição: [Teams](https://learn.microsoft.com/microsoftteams/meeting-transcription-captions) e [Google Meet](https://support.google.com/meet/answer/12849897).

## Acesso por IA

Todos os programas foram projetados para ser instalados, configurados e usados por agentes de IA ou por pessoas, sem diferença no fluxo.

### Instalação automatizada

```bash
# Instala todos os programas
./instalar.sh 1
./instalar.sh 3
./instalar.sh 4

# Ou todos de uma vez, sem interação
for i in 1 3 4; do echo $i | ./instalar.sh; done
```

### Computador, via linha de comando

```bash
cd congo-grey-parrot-desktop
source .venv/bin/activate

# Transcrever um arquivo
python -m congo_grey_parrot transcribe audio.mp3 --output_dir ./saida --output_format txt

# Ler texto em voz alta e salvar WAV
python -m congo_grey_parrot speak "Olá, mundo." --output saida.wav

# Traduzir fala para inglês
python -m congo_grey_parrot translate audio.mp3 --output_dir ./saida
```

### Anotações de reunião, via CLI

```bash
# Listar plataformas suportadas
./congo-reunioes plataformas

# Importar transcrição
./congo-reunioes importar reuniao.vtt --plataforma teams

# Ver notas salvas
./congo-reunioes notas

# Saída em JSON para processamento por IA
./congo-reunioes notas --formato json
```

### Bot de Discord, via API REST

O bot expõe os resultados no Discord, que tem API REST pública. Um agente de IA pode usar a API do Discord para enviar comandos de barra ao bot e ler as respostas, autenticando com um token de usuário ou de bot.

Referência: [Discord REST API](https://discord.com/developers/docs/reference).

### Android, via ADB

```bash
# Instalar o APK
adb install congo-grey-parrot-android/CongoGreyParrot-debug.apk

# Iniciar o aplicativo
adb shell am start -n io.github.thaynabds.congogreyparrot/.MainActivity

# Enviar arquivo de texto para o aplicativo
adb push texto.txt /sdcard/Download/texto.txt
```

## Onde os arquivos vão

| Ação | Computador | Celular |
|---|---|---|
| Salvar texto, áudio, legenda, documento ou conversão | Seletor com nome e pasta | Seletor do Android com nome e pasta |
| Baixar modelo ou voz | Seletor de pasta, antes do download | Esta versão não baixa modelo nem voz |
| Cópia interna | A pasta padrão fica em Configurações | A lista Arquivos guarda uma cópia na pasta privada do aplicativo |
| Listas de reprodução do bot | `~/.local/share/congo-grey-parrot-discord/playlists.json` | Não se aplica |

## Licenças e fontes

O código deste projeto ainda não tem uma licença de distribuição escolhida.

- Whisper, licença MIT: [github.com/openai/whisper](https://github.com/openai/whisper)
- faster-whisper: [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Piper, GPL-3.0 ou posterior: [github.com/OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)
- Vozes, cada uma com o próprio MODEL_CARD: [huggingface.co/rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)
- Parolu, referência de leitura local: [github.com/wbernard/parolu](https://github.com/wbernard/parolu)
- FFmpeg: [ffmpeg.org](https://ffmpeg.org/)
- yt-dlp: [github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Seletor de arquivo do Android: [CreateDocument](https://developer.android.com/reference/androidx/activity/result/contract/ActivityResultContracts.CreateDocument)
- Discord, comandos de aplicativo: [discord.py interactions](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
- Open5e: [open5e.com](https://open5e.com/)
