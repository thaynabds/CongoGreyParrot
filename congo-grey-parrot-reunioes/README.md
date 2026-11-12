# Congo Grey Parrot, reuniões

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Lê a transcrição que o Teams, o Google Meet, o Zoom, o Webex ou o Jitsi já exportou, e anota quem falou o quê. O programa não entra na chamada.

Um áudio gravado só pelo microfone não separa as pessoas. Nesse caso a nota fica como gravação local, sem nome de locutor.

## Instalar

```bash
./instalar.sh 4
```

Listar plataformas, importar e ver notas não precisa de biblioteca extra. A transcrição de um arquivo de áudio é que usa o modelo Whisper, instalado junto com o ambiente Python.

## Usar

```bash
congo-reunioes plataformas
congo-reunioes importar exemplo-teams.vtt --plataforma teams
congo-reunioes notas
congo-reunioes importar-pasta
congo-reunioes notas --formato json
congo-reunioes resumo
```

## Idiomas

O arquivo VTT já traz o texto no idioma da reunião. Quando a transcrição parte de um áudio, o Whisper cobre mais de 90 idiomas, entre eles português, inglês, espanhol, francês, italiano, russo, chinês, japonês, árabe, bengali, indonésio e urdu.

Ajuda para exportar a transcrição: [Teams](https://support.microsoft.com/office) e [Google Meet](https://support.google.com/meet).

## Google Meet

O Meet não deixa um programa de fora entrar na reunião. O caminho oficial é a transcrição que o próprio Meet grava (Google Workspace com transcrição ativada, [ajuda do Google](https://support.google.com/meet/answer/12849897)). Ela vira um documento na pasta Meet Recordings do Google Drive.

1. No Google Docs, abra a transcrição e use Arquivo, Fazer download, Microsoft Word (.docx) ou Texto simples (.txt).
2. Rode `./congo-reunioes importar-pasta`. Ele procura em Downloads os arquivos com Transcript ou Transcrição no nome, importa os novos e pula os que já entraram. Outra pasta: `./congo-reunioes importar-pasta ~/Documentos/Reunioes`.
3. `./congo-reunioes resumo --plataforma meet` mostra o resumo: frases principais da própria reunião, decisões, tarefas e perguntas. `./congo-reunioes notas --plataforma meet` mostra quem disse o quê.

O arquivo original não é alterado. Nada sai do computador. O resumo não usa IA: ele escolhe frases que já estão na transcrição, então não inventa nada. `--frases 5` escolhe o tamanho e `--formato json` serve para outro programa. Pelo Claude, use as ferramentas MCP `resumir_reuniao` e `resumir_texto`.

## MCP

**AI Conector:** `congo-reunioes conector` mostra como ligar uma IA a este programa e o que ela pode fazer. `congo-reunioes conector --conectar` registra no Claude Desktop e no Cursor. Detalhes em [mcp/README.md](../mcp/README.md#ai-conector).

As anotações também abrem um servidor MCP, com o pacote oficial `mcp`. No Cursor:

```bash
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

Instale antes, nesta pasta: `pip install -e ".[mcp]"`.

Para um site ou outro servidor:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8766 congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
```

O arquivo importado precisa estar na pasta pessoal. Detalhes em [mcp/README.md](../mcp/README.md).
