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

## Adicionar o bot aos seus servidores

O bot é uma aplicação do Discord. Adicionado uma vez a um servidor, ele aparece igual no Discord do navegador e no aplicativo do computador, porque os dois usam a mesma conta. Cada servidor precisa do próprio convite.

1. Em [Discord Developer Portal](https://discord.com/developers/applications), abra a aplicação (ou crie uma) e copie o Application ID em General Information. Em Bot, gere o token e cole no arquivo `.env` desta pasta, na linha `DISCORD_TOKEN=`. Nunca cole o token num chat nem no Git.
2. Gere o convite: `.venv/bin/congo-discord-convite ID_DA_APLICACAO`. Para um servidor só: `.venv/bin/congo-discord-convite ID_DA_APLICACAO ID_DO_SERVIDOR`.
3. Abra o link logada na conta que administra o servidor e autorize. Repita para cada servidor seu.

O convite pede só Ver canais, Enviar mensagens, Anexar arquivos, Conectar e Falar. O bot não lê o texto das mensagens, não modera e não pede Administrador.

## Deixar ligado

`./servico.sh instalar` cria um serviço systemd do seu usuário (sem sudo). Ele liga o bot ao entrar na sessão e religa depois de uma falha. `./servico.sh status` mostra o estado, `./servico.sh log` mostra o log e `./servico.sh remover` desfaz. O próprio discord.py reconecta quando a internet cai. Para parar sem remover: `systemctl --user stop congo-discord`.

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
| `/reuniao` | Entra na chamada e transcreve ao vivo. `resumo` mostra frases principais, decisões, tarefas e perguntas; `transcricao` mostra tudo |
| `/musica` | Toca YouTube, Spotify, lista salva ou arquivo enviado |
| `/funcoes` | Liga ou desliga funções |
| `/arquivo` | Transcreve um áudio enviado, resume um TXT, MD, VTT ou SRT (`resumir`) ou lê um texto |
| `/handout` | Envia imagem, vídeo ou arquivo de até 8 MB no canal ou no privado |
| `/navegador` | Liga o Discord ao Foundry VTT e ao Roll20 neste computador |

O resumo é feito neste computador, com frases da própria conversa, sem IA. Na primeira vez que liga, o bot põe sozinho o ícone do papagaio, o mesmo do programa de computador, se ainda não tiver avatar.

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
/navegador token
```

O chat público da mesa aparece nesse canal. `/dados`, `/navegador falar` e `/navegador arquivo` aparecem no chat do Foundry. Imagem, vídeo e outros arquivos de até 8 MB também atravessam nos dois sentidos. `/handout` manda o mesmo tipo de arquivo no Discord e, se for no canal, também no Foundry. Arquivo executável, HTML e SVG não entram. O módulo só conversa com `http://127.0.0.1` ou `http://localhost`. Foundry em HTTPS pode bloquear esse endereço. Quem já instalou uma versão anterior atualiza o módulo na tela Módulos do Foundry. A versão publicada é a 1.2.1, que fecha uma falha: um nome de arquivo vindo do Discord podia injetar código no chat do Foundry, e o mestre só busca mídia do próprio Foundry, nunca de outro site. Desde a 1.2.0 o bot só aceita pedidos com o token do relay: rode `/navegador token` (só quem administra o servidor vê) e cole o valor em Configurações, Configurar módulos, Congo Grey Parrot, Token do relay. Sem o token, qualquer site aberto no navegador poderia postar no seu canal ou ler a fila do Foundry.

Não envie o arquivo `.env` para o Git.
