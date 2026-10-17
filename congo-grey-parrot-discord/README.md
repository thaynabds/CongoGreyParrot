# Congo Grey Parrot, Discord

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Bot para um servidor de Discord. Entra no canal de voz, pode transcrever ao vivo com o nome de quem falou, tocar áudio, rolar dados e guardar fichas de mesa. Cada função liga e desliga com `/funcoes ativar` e `/funcoes desativar`. A transcrição ao vivo começa desligada.

## Instalar

Na pasta deste repositório:

```bash
./instalar.sh 3
```

O script cria o ambiente, instala as dependências e gera o arquivo `.env` se ele ainda não existir.

1. Abra `congo-grey-parrot-discord/.env`.
2. Cole `DISCORD_TOKEN` e `CONGO_DISCORD_OWNER_ID`.
3. O aplicativo do bot é criado em [Discord Developer Portal](https://discord.com/developers/applications).
4. Ligue o bot com `congo-grey-parrot-discord/iniciar.sh`.

Os comandos com `/` se digitam no Discord, dentro do servidor, depois que o bot estiver online. Não são comandos do terminal.

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

Não envie o arquivo `.env` para o Git.
