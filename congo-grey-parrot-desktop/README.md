# Congo Grey Parrot — Computador

> Selecione o idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Programa de desktop para Linux. Transcreve fala para texto com Whisper, lê texto em voz alta com Piper ou espeak-ng, traduz fala para inglês, edita legendas, converte mídia com FFmpeg e trabalha com documentos TXT, Markdown, DOCX e PDF. Todo o processamento acontece no seu computador, sem enviar dados para a internet.

## Instalar

```bash
cd congo-grey-parrot-desktop
./instalar.sh
```

O script faz tudo automaticamente: verifica o Python, instala as dependências do sistema, cria o ambiente isolado, instala o programa e oferece o download do modelo Whisper.

## Idiomas suportados para transcrição

O modelo Whisper suporta mais de 90 idiomas, incluindo:

| Idioma | Código |
|---|---|
| Português | `pt` |
| Inglês | `en` |
| Espanhol | `es` |
| Francês | `fr` |
| Italiano | `it` |
| Russo | `ru` |
| Chinês | `zh` |
| Japonês | `ja` |
| Árabe | `ar` |
| Bengali | `bn` |
| Indonésio | `id` |
| Urdu | `ur` |

Para usar outro idioma: abra a tela **Transcrever**, selecione o idioma no menu ou deixe em **Detectar automaticamente**.

## Telas

| Tela | O que faz |
|---|---|
| Início | Atalhos para as outras telas e área de arrastar arquivos. |
| Transcrever | Transcreve áudio ou vídeo para texto em qualquer idioma suportado. |
| Texto para voz | Lê qualquer texto em voz alta e salva o áudio. |
| Traduzir | Traduz texto entre idiomas. |
| Legendas | Edita tempos e texto, grava legenda no vídeo. |
| Converter mídia | Converte áudio ou vídeo para outro formato via FFmpeg. |
| Documentos | Abre e salva TXT, Markdown, DOCX e PDF. |
| Modelos e vozes | Baixa ou remove modelos Whisper e vozes Piper. |
| Configurações | Tema, filtro de cor e tamanho da letra. |

## Usar pela linha de comando

```bash
cd congo-grey-parrot-desktop
source .venv/bin/activate

# Transcrever um arquivo
python -m congo_grey_parrot transcribe audio.mp3 --output_dir ./saida --output_format txt

# Ler texto em voz alta
python -m congo_grey_parrot speak "Olá, mundo." --output saida.wav

# Traduzir fala para inglês
python -m congo_grey_parrot translate audio.mp3 --output_dir ./saida
```

## Testes

```bash
pytest
```

## MCP

O programa também fala MCP, com o pacote oficial `mcp`. No Cursor, transporte stdio:

```bash
congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

Antes, instale o extra: `pip install -e ".[mcp]"` dentro de `congo-grey-parrot-desktop`.

Para um site ou outro servidor:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8765 congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

O segredo fica em `~/.local/share/congo-grey-parrot/mcp.token` e não é impresso. Sem `Authorization: Bearer` o endereço recusa o pedido. Caminhos de áudio precisam estar na pasta pessoal. Detalhes em [mcp/README.md](../mcp/README.md).
