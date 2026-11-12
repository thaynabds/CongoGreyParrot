# MCP do Congo Grey Parrot

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Cada programa tem um servidor MCP de verdade, com o pacote oficial `mcp`. A documentação do protocolo está em [modelcontextprotocol.io](https://modelcontextprotocol.io/). O pacote Python está em [PyPI](https://pypi.org/project/mcp/).

O celular não fala MCP sozinho. A ponte do Android roda neste computador.

## Ligar no Cursor

O exemplo sem segredo está em [mcp.json](../mcp.json), na raiz do projeto. Copie esses quatro blocos para a configuração MCP do Cursor. O transporte é stdio: o Cursor abre o programa e conversa por ele, sem porta de rede.

Antes, na pasta de cada programa Python:

```bash
pip install -e ".[mcp]"
```

Comandos:

```bash
congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
congo-grey-parrot-reunioes/.venv/bin/congo-reunioes-mcp
congo-grey-parrot-discord/.venv/bin/congo-discord-mcp
congo-grey-parrot-desktop/.venv/bin/python congo-grey-parrot-android/mcp_server.py
```

Portas, se você mudar para HTTP: computador 8765, reuniões 8766, Discord 8767, ponte do celular 8768.

## Ligar no Claude

O Claude Desktop e o Claude Code rodam no seu computador e falam com estes servidores por stdio, sem abrir porta.

* **Claude Desktop:** `python3 mcp/registrar_claude.py` grava os quatro servidores em `~/.config/Claude/claude_desktop_config.json` com caminho absoluto, mantém os outros servidores e guarda uma cópia `.bak`. Feche e abra o Claude Desktop. Para desfazer: `python3 mcp/registrar_claude.py --remover`.
* **Claude Code:** abra o Claude Code nesta pasta. Ele lê `.mcp.json` e pergunta se pode usar os servidores.
* **Claude no navegador (claude.ai):** não enxerga programas do seu computador. Só alcançaria um servidor publicado na internet, e este projeto não publica nenhum.

## AI Conector

Cada programa mostra o AI Conector na própria interface: página no menu do computador, aba no celular, `/conector` no Discord (só para a dona do bot) e `congo-reunioes conector` no terminal. O botão ou a opção `--conectar` grava o servidor daquele programa no Claude Desktop e no Cursor sem mexer nos outros servidores, com o arquivo em permissão 600. O código comum está em [conector.py](conector.py).

O Flatpak do computador (0.4.0 ou mais novo) traz o próprio servidor: `flatpak run --command=congo-grey-parrot-mcp io.github.thaynabds.CongoGreyParrot`.

Se o Claude Code disser que o servidor demorou demais para conectar: o pacote `mcp` leva alguns segundos para carregar e os quatro abrem juntos. O arquivo `.claude/settings.json` do projeto sobe o limite para 120 s (`MCP_TIMEOUT`).

### Ferramentas

| Programa | Ferramentas |
|---|---|
| Computador (`congo-desktop`) | `transcrever_arquivo`, `gerar_legenda`, `converter_legenda`, `ajustar_tempo_legenda`, `falar_texto`, `traduzir_texto`, `resumir_texto`, `resumir_arquivo`, `ler_documento`, `salvar_texto`, `converter_midia`, `gravar_legenda_no_video`, `listar_saidas`, `listar_idiomas`, `listar_modelos`, `baixar_modelo`, `listar_vozes`, `baixar_voz`, `remover_voz`, `listar_historico`, `limpar_historico`, `ver_configuracoes`, `alterar_configuracao` |
| Reuniões (`congo-reunioes`) | `listar_plataformas`, `importar_transcricao`, `importar_pasta`, `transcrever_audio`, `listar_notas`, `notas_json`, `resumir_reuniao`, `resumir_texto`, `limpar_notas` |
| Discord (`congo-discord`) | `status_bot`, `ver_log`, `link_convite`, `listar_funcoes`, `ligar_funcao`, `ajuda_comandos`, `listar_servidores`, `enviar_mensagem`, `tocar_som`, `parar_som`, `sair_voz`, `listar_sons`, `marcar_sessao`, `sessoes`, `reuniao_entrar`, `reuniao`, `rolar_dados`, `rolar_percentil`, `rolar_pool`, `gerar_nome`, `consultar_regra`, `ficha_ver`, `ficha_definir`, `iniciativa`, `grupo` |
| Celular (`congo-android`) | `instrucoes_apk`, `caminho_apk`, `listar_aparelhos`, `instalar_apk`, `iniciar_app`, `status_celular`, `listar_arquivos`, `ler_arquivo`, `salvar_texto`, `excluir_arquivo`, `resumir_no_celular`, `ler_em_voz_alta`, `parar_leitura`, `salvar_audio` |

O bot ligado recebe os pedidos de voz, botões e mensagens por um socket Unix em `$XDG_RUNTIME_DIR/congo-discord/control.sock` (pasta 700, socket 600, uid conferido). As funções de mesa usam o banco do bot direto e funcionam com o bot desligado.

O celular recebe os pedidos pelo cabo USB (`adb shell content call`). O provider do app aceita só o usuário shell do adb, e o texto vai em base64, então nada do que a IA escreve vira comando no celular.

### Travas de segurança

Todo argumento é tratado como vindo de alguém hostil, porque um documento lido pela IA pode trazer instruções escondidas.

* Arquivos só dentro da pasta pessoal, fora de pastas ocultas, com tipo fixo e tamanho limitado.
* Nada é sobrescrito sem `sobrescrever=true`.
* Apagar (notas, histórico, voz, arquivo do celular, iniciativa, transcrição), publicar no Discord e ligar a escuta de uma chamada exigem `confirmar=true`, depois de a IA perguntar à pessoa.
* Mensagens do bot nunca chamam `@everyone`, cargos ou pessoas.
* Downloads de modelos e vozes só dos endereços do catálogo do programa.
* Os testes destas travas estão em [test_tools.py](test_tools.py).

## Ligar um site ou outro servidor

```bash
CONGO_MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8765 \
  congo-grey-parrot-desktop/.venv/bin/congo-grey-parrot-mcp
```

Nesta versão do pacote o caminho HTTP é `/mcp` (streamable HTTP). Troque `CONGO_MCP_TRANSPORT=sse` só se precisar da rota antiga `/sse`.

Se a variável `MCP_TOKEN` não existir, o programa cria um segredo uma vez em `~/.local/share/congo-grey-parrot/mcp.token`, com permissão 600, e imprime só esse caminho. O pedido precisa do cabeçalho `Authorization: Bearer` com o conteúdo do arquivo. Sem isso a resposta é 401.

`MCP_HOST` começa em `127.0.0.1`, então outro computador não entra. Para abrir na rede, defina o host e guarde o segredo. Não publique o arquivo do token.

Caminhos de áudio e de transcrição precisam ficar na pasta pessoal de quem roda o servidor.
