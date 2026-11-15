# Congo Grey Parrot — Computador

> Selecione o idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Programa de desktop para Linux. Transcreve fala para texto com Whisper, lê texto em voz alta com Piper ou espeak-ng, traduz fala para inglês, edita legendas, converte mídia com FFmpeg e trabalha com documentos TXT, Markdown, DOCX e PDF. Todo o processamento acontece no seu computador, sem enviar dados para a internet.

## Instalar

```bash
cd congo-grey-parrot-desktop
./instalar.sh
```

O script faz tudo automaticamente: verifica o Python, instala as dependências do sistema, cria o ambiente isolado, instala o programa e oferece o download do modelo Whisper.

### Pelo Flatpak

Este programa também vem como pacote Flatpak, na página da [versão 0.4.0](https://github.com/thaynabds/CongoGreyParrot/releases/tag/desktop-v0.4.0). Baixe o arquivo `CongoGreyParrot-0.4.0-x86_64.flatpak` e instale com:

```bash
flatpak install --user CongoGreyParrot-0.4.0-x86_64.flatpak
```

O Flatpak baixa sozinho do Flathub o runtime KDE de que o programa precisa. O Flathub ainda não aceitou o programa na loja porque o projeto é novo; ele volta a ser enviado mais adiante.

No Flatpak o programa enxerga só as pastas Música, Vídeos, Documentos e Downloads. Os arquivos de manifesto ficam em [flatpak](flatpak).

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
| Ler a tela | Botão **Ler a tela** ou Ctrl+Shift+L. Lê a seleção ou o texto visível na tela atual. |

### Ler a janela ativa em qualquer programa

O comando `congo-grey-parrot ler-janela` lê em voz alta o texto da janela que está em foco, seja navegador, editor ou outro programa. Não é preciso instalar nada em cada aplicação: a leitura usa a árvore de acessibilidade do sistema (AT-SPI, no Linux).

1. Instale o pacote de ligação do AT-SPI: `sudo apt install gir1.2-atspi-2.0` (no Debian e Ubuntu).
2. Ative a acessibilidade nas configurações do sistema. Em navegadores baseados em Chromium, o texto da página só aparece para a acessibilidade quando ela está ativa.
3. Crie o atalho do sistema. No GNOME, o comando faz isso sozinho: `congo-grey-parrot instalar-atalho` registra Ctrl+Alt+R como atalho de `ler-janela`, sem apagar os atalhos que já existem. Em outros ambientes, crie um atalho manual em Configurações do sistema que rode `congo-grey-parrot ler-janela` (no KDE: Configurações do sistema, Atalhos, Atalho personalizado).

Não testei o `instalar-atalho` em um GNOME real: a montagem dos comandos gsettings foi verificada nos testes, mas não a aplicação no sistema.

Campos de senha nunca são lidos. O texto é limitado a 20 mil caracteres. Se o programa em foco não expuser texto, o comando avisa e não lê nada. Fontes: [documentação do AT-SPI](https://gitlab.gnome.org/GNOME/at-spi2-core) e [documentação de acessibilidade do Chromium](https://www.chromium.org/developers/accessibility/). Não testei a leitura de um navegador real: a verificação foi feita com a árvore simulada nos testes.
| Traduzir | Traduz texto entre idiomas. |
| Legendas | Edita tempos e texto, grava legenda no vídeo. |
| Resumir | Resume o texto colado, um documento ou a transcrição: frases principais do próprio texto, decisões, tarefas e perguntas. Sem internet e sem IA. Os botões Resumir de Transcrever e Documentos mandam o texto para cá. |
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

**AI Conector:** abra o item **AI Conector** no menu lateral. O botão *Conectar ao Claude Desktop e Cursor* registra este programa na IA, *Copiar comando do Claude Code* copia o `claude mcp add` pronto e a página lista tudo o que a IA pode fazer aqui. A lista completa e as travas de segurança estão em [mcp/README.md](../mcp/README.md#ai-conector).

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
