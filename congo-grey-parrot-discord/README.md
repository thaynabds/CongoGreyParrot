# Congo Grey Parrot, Discord

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Bot para um servidor de Discord. Entra no canal de voz, pode transcrever ao vivo com o nome de quem falou, tocar áudio, rolar dados e guardar fichas de mesa. Cada função liga e desliga com `/funcoes ativar` e `/funcoes desativar`. A transcrição ao vivo começa desligada.

## Instalar

Na pasta deste repositório, um comando:

```bash
./instalar.sh 3
```

O script instala o programa, o áudio, a voz, a transcrição e a música. Cria o arquivo `.env` só com a sua permissão de leitura. Se o token ainda estiver vazio, explica os cliques em [discord.com/developers/applications](https://discord.com/developers/applications) e pede o token em silêncio no terminal, junto com o ID do dono. Também cria o atalho Congo Grey Parrot Discord no menu e o comando `congo-discord`. Se o token já estiver no arquivo, liga o bot no fim.

O site do Discord continua necessário para criar o aplicativo, copiar o token e convidar o bot. O token não entra no Git.

Os comandos com `/` se digitam no Discord, dentro do servidor, depois que o bot estiver online. Não são comandos do terminal.

## MCP

O bot também abre um servidor MCP, com o pacote oficial `mcp`. No Cursor, o transporte é stdio:

```bash
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
```

Para um site ou outro servidor, na mesma pasta:

```bash
CONGO_MCP_TRANSPORT=http MCP_PORT=8767 .venv/bin/congo-discord-mcp
```

O segredo fica em `~/.local/share/congo-grey-parrot/mcp.token`. O endereço não responde sem `Authorization: Bearer`. Detalhes em [mcp/README.md](../mcp/README.md).

## Idiomas da transcrição ao vivo

O modelo Whisper cobre mais de 90 idiomas, entre eles português, inglês, espanhol, francês, italiano, russo, chinês, japonês, árabe, bengali, indonésio e urdu. É preciso baixar o modelo uma vez. A transcrição ao vivo usa faster-whisper no computador que roda o bot.

## Comandos principais

| Grupo | Função |
|---|---|
| `/dados` | Rolagem de dados |
| `/ficha` | Atributos por jogador |
| `/iniciativa` | Ordem de turno |
| `/reuniao` | Entra na chamada e transcreve ao vivo |
| `/musica` | Toca YouTube, Spotify, lista salva ou arquivo enviado |
| `/funcoes` | Liga ou desliga funções |
| `/arquivo` | Transcreve um áudio enviado ou lê um texto |
| `/navegador` | Liga o Discord ao Foundry VTT e ao Roll20 neste computador |

## Foundry VTT

Dá para instalar sem entrar no Ubuntu da máquina virtual. Na página do Foundry, antes de abrir o mundo, abra Módulos, clique em Instalar módulo e cole este endereço:

```
https://raw.githubusercontent.com/thaynabds/CongoGreyParrot/main/congo-grey-parrot-discord/foundry/congo-grey-parrot/module.json
```

O Foundry baixa o pacote sozinho. Esse é o instalador da tela de configuração, descrito em [Add-on Modules](https://foundryvtt.com/article/modules/). Depois, entre no mundo e ative Congo Grey Parrot em Gerenciar módulos.

O bot de Discord fica no computador de quem abre a mesa, não na máquina da Oracle. O módulo só fala com esse computador, em `http://127.0.0.1:7477`.

Com o bot online, no Discord:

```
/funcoes ativar navegador
/navegador ligar
/navegador canal #rolagens
```

O chat público da mesa aparece nesse canal. `/dados`, `/navegador falar` e `/navegador arquivo` aparecem no chat do Foundry. Imagem, vídeo e outros arquivos de até 8 MB também atravessam nos dois sentidos. `/handout` manda o mesmo tipo de arquivo no Discord e, se for no canal, também no Foundry. Arquivo executável, HTML e SVG não entram. O módulo só conversa com `http://127.0.0.1` ou `http://localhost`. Foundry em HTTPS pode bloquear esse endereço. Quem já instalou a versão 1.0.0 atualiza o módulo na tela Módulos do Foundry.

Não envie o arquivo `.env` para o Git.
