# Project Congo Grey Parrot

**Nome oficial:** Project Congo Grey Parrot  
**Referência científica do nome:** *Psittacus erithacus*  
**Produtos:** janela no Linux, APK Android, bot de Discord e anotações de reunião. Cada um é um programa separado, no mesmo repositório.  
**Princípio de arquivo:** toda operação que produzir um resultado em arquivo oferece salvar, exportar ou baixar, no nome e na pasta escolhidos pela pessoa. Nada é enviado à nuvem sem autorização explícita.

O Desktop e o Android não dependem um do outro, nem de conta, nem de servidor próprio. Depois que os modelos e as vozes necessários estiverem instalados, o uso básico é local.

Esta descrição cobre o que o Whisper e o Parolu fazem de fato, segundo a documentação e o código públicos, e define que o Congo Grey Parrot deve oferecer essas mesmas capacidades, com a opção de arquivo em cada uma.

## 1. Regra de salvamento e download

Salvar não é um extra. Ao terminar uma operação, ou enquanto o resultado ainda puder ser reaproveitado, a interface mostra as saídas disponíveis e deixa a pessoa:

1. Escolher nome e pasta.
2. Escolher o formato entre os que o componente instalado realmente gera.
3. Salvar um resultado ou vários.
4. Repetir a exportação sem refazer a transcrição ou a síntese, quando o resultado intermediário ainda existir.
5. Manter o arquivo original. A substituição só ocorre se a pessoa pedir.
6. Cancelar a gravação ou a tarefa quando isso for tecnicamente possível.
7. No Android, compartilhar o arquivo pelo seletor do sistema.

Se o formato pedido depender de um codec ou biblioteca ausente, a tela explica a falta e indica o componente. Não grava um arquivo vazio nem troca o formato em silêncio.

| Operação | Arquivos que a pessoa pode salvar |
|---|---|
| Transcrição Whisper | TXT, VTT, SRT, TSV, JSON, JSONL. Também MD, DOCX e PDF quando o módulo de documentos estiver instalado |
| Tradução de fala para inglês | Os mesmos formatos da transcrição, com o texto em inglês e a identificação da tarefa `translate` |
| Texto digitado ou aberto | TXT e, quando o módulo de documentos existir, MD, DOCX e PDF |
| Fala sintetizada | WAV. MP3, M4A, AAC ou OGG somente se o conversor instalado, em geral o FFmpeg, conseguir gerar |
| Trecho processado por intervalo de tempo | Áudio ou vídeo do trecho, mais a transcrição desse trecho |
| Legenda | SRT, VTT, ASS e SSA |
| Vídeo com legenda | Vídeo com faixa de legenda selecionável, ou vídeo com legenda desenhada na imagem |
| Conversão de mídia | O contêiner e o codec escolhidos, entre os suportados pelo FFmpeg instalado |
| Modelo ou voz | O pacote baixado fica no armazenamento local do aplicativo, com progresso, verificação e opção de remover |

O Whisper, na linha de comando, já grava a saída em uma pasta (`--output_dir`, padrão o diretório atual) e, por padrão, gera todos os formatos (`--output_format all`). O Parolu já oferece "Save Text to File" e "Save Audio to File" em WAV. O Congo Grey Parrot mantém essas saídas e torna a escolha visível na interface, em vez de gravar sem perguntar.

## 2. O que o Whisper faz e o que o projeto deve fazer

Fonte principal: repositório [openai/whisper](https://github.com/openai/whisper), [README](https://github.com/openai/whisper/blob/main/README.md), [whisper/transcribe.py](https://github.com/openai/whisper/blob/main/whisper/transcribe.py) e [whisper/tokenizer.py](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py). O código e os pesos são publicados sob licença MIT, conforme o [LICENSE](https://github.com/openai/whisper/blob/main/LICENSE) do repositório.

O README define o Whisper como modelo de reconhecimento de fala capaz de reconhecimento multilíngue, tradução de fala e identificação de idioma. O mesmo texto diz que o treinamento inclui reconhecimento multilíngue, tradução de fala, identificação do idioma falado e detecção de atividade de voz. Artigo: [Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356).

O aplicativo oficial é linha de comando e API Python. Ele exige FFmpeg instalado para ler o áudio. O Congo Grey Parrot cobre as funções abaixo na interface, sem obrigar a pessoa a usar o terminal.

### 2.1. Tarefas

| Função documentada | Comportamento no Congo Grey Parrot | Arquivo |
|---|---|---|
| Transcrever fala para o mesmo idioma (`--task transcribe`) | Tela de transcrição, com o texto editável | TXT, VTT, SRT, TSV, JSON, JSONL e documentos |
| Traduzir fala de outro idioma para inglês (`--task translate`) | Ação separada da transcrição. A tela informa que o destino do Whisper é inglês | Os mesmos formatos, com o texto traduzido |
| Identificar o idioma | Detecção automática quando a pessoa não escolhe o idioma. A API também expõe probabilidades em `detect_language` | O idioma detectado entra nos metadados do JSON |
| Processar um ou vários arquivos na mesma execução | Fila no Desktop. No Android, um arquivo ou uma gravação por vez quando a memória não comportar lote | Uma pasta de saída por arquivo |
| Ler áudio com FFmpeg | Importação de FLAC, MP3, WAV e dos demais formatos que o FFmpeg instalado abrir, inclusive áudio extraído de vídeo | Áudio extraído, se a pessoa pedir para guardá-lo |
| Processar em janelas de cerca de 30 segundos | Implementação interna. A pessoa vê progresso, não a janela técnica | Transcrição contínua do arquivo inteiro |
| Decodificar em nível mais baixo (`decode`) | Uso interno dos motores. Não é uma tela separada | Não gera arquivo próprio |

Limite documentado: o modelo `turbo` não é treinado para tradução. Se a tarefa for traduzir, a interface não oferece `turbo`. O README indica modelos multilíngues (`tiny`, `base`, `small`, `medium`, `large`) e recomenda `medium` ou `large` para melhor tradução. Se alguém selecionar `turbo` com tarefa de tradução, o modelo tende a devolver o idioma original.

Outro limite: a tradução do Whisper é para inglês. Tradução para outros idiomas fica em outro motor, identificado na tela e nos metadados. Não se apresenta essa tradução como resultado do Whisper.

O Whisper não faz diarização de locutores. O projeto não promete "quem falou" como função do Whisper.

### 2.2. Modelos

Tabela publicada no README. A VRAM é aproximada. A velocidade relativa foi medida em inglês numa GPU A100 e não vale como promessa para qualquer computador.

| Tamanho | Parâmetros | Só inglês | Multilíngue | VRAM aproximada | Velocidade relativa ao large |
|---|---|---|---|---|---|
| tiny | 39 M | `tiny.en` | `tiny` | cerca de 1 GB | cerca de 10x |
| base | 74 M | `base.en` | `base` | cerca de 1 GB | cerca de 7x |
| small | 244 M | `small.en` | `small` | cerca de 2 GB | cerca de 4x |
| medium | 769 M | `medium.en` | `medium` | cerca de 5 GB | cerca de 2x |
| large | 1550 M | não há | `large` | cerca de 10 GB | 1x |
| turbo | 809 M | não há | `turbo` | cerca de 6 GB | cerca de 8x |

O README descreve o `turbo` como versão otimizada do `large-v3`, mais rápida, com perda pequena de precisão na transcrição. Os modelos `.en` tendem a ir melhor em inglês, sobretudo `tiny.en` e `base.en`. A diferença diminui em `small.en` e `medium.en`. Um modelo `.en` não serve para outro idioma: o código avisa e força inglês.

Perfis na interface, ligados a modelos reais, não a nomes vazios:

- Leve: `tiny` ou `base`, e `.en` só se o áudio for inglês.
- Equilibrado: `small` ou `medium`.
- Rápido em hardware compatível: `turbo`, apenas para transcrever.
- Maior precisão ou tradução para inglês: `medium` ou `large`.

A pessoa baixa o modelo pela central, vê o tamanho, confirma, acompanha o progresso e pode remover. O cache padrão do Whisper fica em `~/.cache/whisper`, configurável por `--model_dir`. O aplicativo usa uma pasta própria e mostra o espaço ocupado.

No Android, entram só modelos que caibam na memória do aparelho. Se um modelo não couber, a tela diz isso antes do download.

### 2.3. Idiomas do tokenizer

O arquivo `tokenizer.py` publica os códigos abaixo. O README avisa que a qualidade varia muito conforme o idioma. Presença na lista não significa a mesma taxa de erro em todos.

afrikaans, albanês, amárico, árabe, armênio, assamês, azeri, basco, bashkir, bielorrusso, bengali, bósnio, bretão, búlgaro, canarês, cantonês, catalão, cazaque, chinês, cingalês, coreano, crioulo haitiano, croata, dinamarquês, eslovaco, esloveno, espanhol, estoniano, feroês, finlandês, francês, galego, georgiano, grego, gujarati, hauçá, havaiano, hebraico, hindi, holandês, húngaro, indonésio, inglês, islandês, italiano, japonês, javanês, khmer, lao, latim, letão, lingala, lituano, luxemburguês, macedônio, malaiala, malaio, malgaxe, maltes, maori, marata, mongol, myanmar, nepalês, norueguês, nynorsk, occitano, pashto, persa, polonês, português, punjabi, romeno, russo, sânscrito, sérvio, shona, sindi, somali, suaíli, sudanês, sueco, tagalo, tadjique, tailandês, tamil, tártaro, tcheco, telugo, tibetano, turco, turcomeno, ucraniano, urdu, uzbeque, vietnamita, iídiche, iorubá, galês.

Esperanto não aparece nessa lista. A leitura de texto em esperanto fica com as vozes do Piper, não com o reconhecimento do Whisper.

O código de português no Whisper é `pt`. Não há código separado para português do Brasil e português de Portugal.

### 2.4. Opções de reconhecimento que a interface deve expor

Valores e nomes seguem `transcribe.py`. Opções avançadas ficam recolhidas. O padrão da interface pode ser mais simples que o padrão da linha de comando, desde que a opção exista.

| Opção do Whisper | Uso na interface | Efeito no arquivo |
|---|---|---|
| `--language` | Lista de idiomas, ou detecção | Campo de idioma no JSON |
| `--task` | Transcrever ou traduzir para inglês | Texto no idioma de origem ou em inglês |
| `--output_format` | Escolha de TXT, VTT, SRT, TSV, JSON, JSONL ou todos | Arquivos pedidos |
| `--output_dir` | Pasta escolhida no seletor | Destino da gravação |
| `--device` | CPU ou CUDA, quando existir | Não muda o formato. Entra nos metadados |
| `--fp16` | Precisão reduzida quando a GPU permitir | Não muda o formato |
| `--temperature` | Amostragem. Padrão 0 | Pode mudar o texto |
| `--best_of` | Candidatos quando a temperatura não é zero. Padrão 5 | Pode mudar o texto |
| `--beam_size` | Feixe quando a temperatura é zero. Padrão 5 | Pode mudar o texto |
| `--patience` | Paciência da busca em feixe | Pode mudar o texto |
| `--length_penalty` | Penalidade de comprimento | Pode mudar o texto |
| `--initial_prompt` | Texto inicial opcional, glossário ou contexto | Pode mudar o texto |
| `--carry_initial_prompt` | Repete o prompt em cada janela | Pode mudar a consistência |
| `--condition_on_previous_text` | Liga ou desliga o uso do trecho anterior. Padrão ligado | Texto mais estável, ou menos propenso a repetir um erro |
| `--word_timestamps` | Marcação por palavra. O próprio argumento está marcado como experimental | JSON com palavra, início, fim e probabilidade. SRT e VTT podem usar essa marcação |
| `--highlight_words` | Sublinhar a palavra falada em SRT e VTT. Exige marcação por palavra | Legenda com destaque |
| `--max_line_width` | Máximo de caracteres por linha. Exige marcação por palavra | Quebra de linha da legenda |
| `--max_line_count` | Máximo de linhas por segmento. Só tem efeito junto com a largura | Quebra da legenda |
| `--max_words_per_line` | Máximo de palavras por linha. Não se soma à largura máxima | Quebra da legenda |
| `--prepend_punctuations` e `--append_punctuations` | Pontuação grudada na palavra seguinte ou anterior | Texto da marcação por palavra |
| `--clip_timestamps` | Início e fim, em segundos, de um ou mais trechos. O último fim pode ser o fim do arquivo | Transcrição e, se a pessoa pedir, mídia só daquele trecho |
| `--no_speech_threshold` | Limiar do token de não fala. Padrão 0,6 | Trechos tratados como silêncio quando a decodificação também falha no limiar de probabilidade |
| `--logprob_threshold` | Limiar de probabilidade média. Padrão -1,0 | Segmento tratado como falha de decodificação |
| `--compression_ratio_threshold` | Limiar de compressão gzip. Padrão 2,4 | Segmento tratado como falha, útil contra repetição |
| `--temperature_increment_on_fallback` | Sobe a temperatura quando a decodificação falha. Padrão 0,2 | Nova tentativa automática |
| `--hallucination_silence_threshold` | Pula silêncio longo quando há indício de alucinação. Exige marcação por palavra | Trechos omitidos segundo essa regra |
| `--suppress_tokens` | Tokens suprimidos. `-1` suprime a maior parte dos caracteres especiais e mantém pontuação comum | Menos anotações que não foram faladas |
| `--threads` | Número de threads na CPU | Não muda o formato |
| `--verbose` | Progresso visível | Não é arquivo. Vira barra e mensagens |
| `--model_dir` | Pasta local de modelos | Os pesos baixados |

A marcação por palavra em tradução para inglês é pouco confiável: o tempo acompanha o áudio de origem e o texto está em inglês. A interface avisa isso quando a tarefa for `translate`.

O resultado JSON inclui texto, segmentos, idioma e, com marcação por palavra, início, fim e probabilidade. A pessoa pode salvar esse JSON mesmo quando também salvar SRT ou TXT.

### 2.5. O que o Whisper não entrega sozinho

O projeto pode oferecer os itens abaixo com outros módulos. A tela não os atribui ao Whisper.

- Tradução para um idioma que não seja inglês.
- Síntese de voz.
- Leitura de PDF, DOCX ou Markdown.
- Diarização.
- Remoção de ruído como filtro de áudio.
- Controle de velocidade e tom na reprodução. Isso é função do reprodutor, não do modelo.

## 3. O que o Parolu faz e o que o projeto deve fazer

Fontes: [Flathub](https://flathub.org/en/apps/im.bernard.Parolu), [repositório wbernard/parolu](https://github.com/wbernard/parolu), [metainfo](https://github.com/wbernard/parolu/blob/main/data/im.bernard.Parolu.metainfo.xml.in), [window.ui](https://github.com/wbernard/parolu/blob/main/src/window.ui), [window.py](https://github.com/wbernard/parolu/blob/main/src/window.py), [reader.py](https://github.com/wbernard/parolu/blob/main/src/reader.py), [pipervoice.py](https://github.com/wbernard/parolu/blob/main/src/pipervoice.py) e [vocxpo.py](https://github.com/wbernard/parolu/blob/main/src/vocxpo.py). Licença do aplicativo: GPL-3.0 ou posterior. Versão publicada no Flathub consultada: 0.1.2, pacote de 177 MiB, desktop, arquiteturas x86_64 e aarch64.

O metainfo diz que o Parolu gera áudio a partir de texto, com vozes diferentes, só no aparelho, sem enviar o texto a terceiros, usando a biblioteca Piper. O README diz que duas vozes de esperanto vêm com o aplicativo porque não havia vozes de esperanto adequadas para baixar, e que os outros idiomas exigem baixar pelo menos uma voz antes do uso.

O código confirma recursos que a página do Flathub não descreve em detalhe.

| Função no código do Parolu | Comportamento no Congo Grey Parrot | Arquivo |
|---|---|---|
| Campo de texto | Digitar ou colar | TXT, e documentos se o módulo existir |
| Abrir arquivo de texto UTF-8 | Seletor de arquivo. Se a codificação não for UTF-8, a tela informa o erro, como o Parolu faz ao recusar o arquivo | O texto aberto pode ser salvo de novo |
| Salvar o texto (`text.txt` como nome inicial) | Salvar como, com nome e pasta livres | TXT |
| Ler o texto inteiro em voz alta | Botão de leitura | A pessoa pode ouvir sem salvar |
| Parar a leitura | O mesmo controle alterna entre ler e parar | Não apaga o texto |
| Esperanto, alemão, italiano, espanhol e francês | Esses cinco idiomas entram no catálogo inicial | Depende da voz instalada |
| Escolher a voz instalada | Lista por idioma | Metadado da voz no arquivo, quando o contêiner permitir |
| Baixar vozes, exceto esperanto | Central de vozes, com lista, botão de instalar e barra de progresso | Modelo `.onnx` e configuração `.onnx.json` no armazenamento local |
| Apagar voz, com confirmação | Remover, com confirmação | A pasta da voz sai do disco |
| Aviso sem rede | Não inicia download se não houver conexão | Nenhum |
| Aviso de que não há vozes novas | Quando o catálogo daquele idioma já foi instalado | Nenhum |
| Vozes inclusas `eo-gosia-medium` e `eo-ludoviko-medium` | Podem acompanhar o Desktop se a licença de cada voz permitir. Se não permitir, a tela oferece o download | Arquivos da voz |
| Tom | Controle de tom | O áudio salvo usa o tom escolhido |
| Velocidade | Controle de 0,5 a 2,0, valor inicial 1,0, no espírito do controle do Parolu | O áudio salvo usa a velocidade escolhida |
| Salvar áudio (`audio.wav` como nome inicial) | Salvar WAV sempre. Outros formatos só com conversor | WAV e conversões pedidas |
| Síntese fora da thread de interface, com diálogo de espera | Fila e progresso, sem travar a janela | O WAV temporário vira arquivo quando a pessoa salva |
| Reprodução local | Ouvir antes de salvar, ou ouvir o arquivo salvo | Opcional |
| Ajuste de pronúncia do esperanto antes da síntese | Manter para as vozes de esperanto que dependem dessa conversão | Não é um arquivo separado |
| Atalhos de teclado e diálogo sobre o aplicativo | Atalhos no Desktop e tela sobre, com licenças | Nenhum |
| Motor Piper | Piper no Desktop. No Android, um porte compatível, ou o motor nativo se a voz Piper não couber, com o nome do motor visível | WAV |

Implementação observada no Parolu, para não copiar um efeito colateral sem saber:

- A velocidade entra no Piper como `length_scale = 0.8 / speed`.
- O tom altera a taxa de amostragem com `sample_rate = pitch * 19000`. Isso não é um deslocamento de tom independente da duração. O Congo Grey Parrot pode usar o controle de tom do próprio Piper quando o modelo e a versão do motor expuserem esse controle. Enquanto usar o mesmo método do Parolu, a interface não promete tom de estúdio.

O seletor do Parolu não inclui português. O README antigo do Piper, hoje com o aviso de que o desenvolvimento foi para [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), listava vozes para português do Brasil e de Portugal (`pt_BR`, `pt_PT`) entre outros idiomas. O catálogo que o Parolu consulta é `https://raw.githubusercontent.com/rhasspy/piper/master/VOICES.md`. Antes de mostrar uma voz em português, o aplicativo precisa confirmar que o arquivo existe, que a licença permite o download e que o motor instalado abre aquele `.onnx`. Não se anuncia voz em português brasileiro só porque o Piper já teve essa entrada na documentação.

Cada voz baixada mostra idioma, nome, qualidade publicada no catálogo (por exemplo low, medium ou high, quando o catálogo trouxer), tamanho, licença e se funciona offline depois da instalação. O Parolu exige o par `.onnx` e `.onnx.json`. Sem os dois, a voz não aparece como instalada.

O Parolu é um programa de desktop Linux. O Android repete os resultados para a pessoa, com outra implementação: digitar, abrir texto, ler, parar, escolher idioma e voz, baixar e remover voz, ajustar velocidade, ajustar tom quando o motor permitir, ouvir e salvar WAV.

### 3.1. O que o Parolu não faz

Não há, no código consultado, leitura de PDF, DOCX, EPUB ou página web, OCR, tradução, transcrição, lote de documentos, atalho global em qualquer aplicativo, sincronização com celular nem exportação direta para MP3. O Congo Grey Parrot pode oferecer PDF, DOCX, Markdown e conversão do WAV por módulos próprios. Essas funções não são descritas como funções do Parolu.

## 4. Os dois juntos, na mesma sessão

A pessoa pode encadear as funções sem perder o arquivo de cada etapa.

1. Importar ou gravar áudio.
2. Transcrever com Whisper.
3. Salvar a transcrição.
4. Traduzir a fala para inglês com Whisper, ou traduzir o texto com outro motor.
5. Salvar a tradução.
6. Ouvir o texto com uma voz Piper, no idioma e na voz instalados.
7. Salvar o WAV.
8. Converter o WAV para outro formato de áudio, se o FFmpeg estiver instalado, e salvar de novo.

Cada etapa tem seu botão de salvar. A etapa seguinte não apaga a anterior.

## 5. Funções além do Whisper e do Parolu

Estas funções não substituem as das seções 2 e 3. Entram porque o produto também é central de mídia, legenda e documento.

- Editor de legendas: importar SRT, VTT, ASS e SSA, editar texto e tempos, dividir e unir segmentos, buscar e substituir, pré-visualizar com o vídeo, incorporar faixa ou desenhar a legenda na imagem, salvar a legenda e o vídeo.
- Conversão com FFmpeg: contêiner, codec, extração de áudio, corte, união, taxa de bits, resolução, taxa de quadros, normalização e lote. O original permanece, salvo pedido contrário.
- Reprodução: pausa, busca, volume, velocidade de 0,5x a 2,0x, e tom separado da velocidade quando o reprodutor conseguir fazer os dois.
- Documentos: TXT, Markdown, DOCX e PDF com texto selecionável. PDF escaneado fica para um módulo de OCR, especificado à parte.
- Três temas persistentes: claro, escuro e alto contraste. Fonte escalável, foco visível, teclado no Desktop e área de toque no Android.
- Histórico local, limpeza do histórico e fila com cancelamento.

Supressão de ruído, se existir, usa filtro ou modelo próprio. Não se promete voz intacta nem silêncio perfeito.

## 6. Onde cada função roda

| Função | Desktop | Android |
|---|---|---|
| Transcrição Whisper, inclusive lote e opções avançadas | Sim, com faster-whisper, whisper.cpp ou o pacote oficial, conforme desempenho | Sim, com build leve, por exemplo whisper.cpp via NDK, depois de teste de memória. Opções que não couberem ficam desligadas com aviso |
| Tradução de fala para inglês | Sim, fora do modelo turbo | Sim, se o modelo multilíngue couber |
| Marcação por segmento e por palavra, SRT, VTT, TSV, JSON, JSONL, TXT | Sim | Sim |
| Digitar, abrir texto, ler, parar, velocidade, salvar WAV | Sim | Sim |
| Tom | Sim. Preferir controle real do motor. O método de taxa de amostragem do Parolu fica como compatibilidade | Quando o motor do aparelho expuser tom |
| Baixar e remover modelo ou voz pela interface | Sim | Sim, com aviso de espaço e de rede móvel |
| FFmpeg, editor de legenda completo e lote pesado | Sim | Conversão e legenda simples. Hardcode de vídeo longo só se o aparelho aguentar, com aviso de bateria e aquecimento |
| Temas claro, escuro e alto contraste | Sim | Sim |

Stack fechada para começar:

- Desktop: Python, PySide6, faster-whisper ou whisper.cpp, FFmpeg, Piper, SQLite. Empacotamento com PyInstaller ou equivalente. Trabalho pesado fora da thread da interface.
- Android: Kotlin, Jetpack Compose, Media3, Storage Access Framework, Room, WorkManager, motor Whisper nativo validado e motor TTS local. Sem servidor obrigatório.

Módulos, nos dois aplicativos: transcrição, síntese, tradução, mídia, legendas, documentos, modelos, exportação, tarefas, acessibilidade, configurações. Motor de IA e FFmpeg são substituíveis por trás de uma interface estável. Não há microsserviço nem API Gateway obrigatórios: são dois aplicativos locais, e um serviço interno só aumentaria instalação e falha sem mudar o que a pessoa faz.

## 7. Interface

Desktop, barra lateral: Início, Transcrever, Texto para voz, Traduzir, Legendas, Converter, Documentos, Arquivos, Modelos e vozes, Histórico, Configurações. No centro, entrada, opções essenciais, opções avançadas fechadas, processar e resultado. Ao lado, a fila. Em todo resultado, Salvar.

Android, base: Início, Transcrever, Ler em voz alta, Arquivos, Configurações. Início com gravar, importar, transcrever e ler. Tradução, legenda e conversão saem da tela inicial. Arquivos do sistema entram e saem pelo seletor do Android, sem permissão ampla de armazenamento.

Os três temas valem nas duas interfaces e permanecem depois de fechar o aplicativo.

## 8. Modelos, licença e privacidade

- Download só depois de mostrar tamanho e pedir confirmação.
- HTTPS, verificação de hash ou assinatura quando a origem publicar.
- Licença do código do aplicativo, licença do Whisper (MIT), licença do Parolu (GPL-3.0 ou posterior), licença de cada voz Piper e licença do FFmpeg ficam separadas. Voz ou modelo só entra no instalador se a licença permitir. Caso contrário, a pessoa baixa pela interface.
- Operação local não cria conta e não envia áudio nem texto.
- Serviço remoto, se um dia existir, aparece desligado e pede consentimento na hora.
- Segredos ficam fora do código. `.gitignore` cobre `.env`, modelos grandes, cache e arquivos de teste com conteúdo pessoal.

## 9. Critérios para dizer que a paridade existe

1. Transcrever um áudio e salvar TXT, SRT, VTT, TSV e JSON.
2. Transcrever vários arquivos no Desktop e salvar uma saída por arquivo.
3. Detectar o idioma e também forçar o idioma.
4. Traduzir fala para inglês com modelo multilíngue e salvar o texto. O modelo turbo não aparece nessa tarefa.
5. Gerar marcação por palavra e uma legenda com limite de caracteres por linha.
6. Processar só um intervalo de tempo e salvar a transcrição desse intervalo.
7. Digitar um texto, ouvir, parar e salvar WAV.
8. Abrir um TXT em UTF-8 e salvar o texto de novo.
9. Baixar uma voz pela interface, usar offline e depois remover.
10. Ajustar velocidade e salvar um WAV diferente do áudio em velocidade 1,0.
11. Usar esperanto com voz disponível, ou baixar voz de alemão, italiano, espanhol ou francês.
12. Encadear transcrição, salvamento, leitura em voz alta e salvamento do WAV sem apagar a transcrição.
13. Aplicar tema claro, escuro e alto contraste.
14. Completar os fluxos locais sem conta e sem rede, depois dos componentes instalados.

Cada item vale na plataforma em que a função for anunciada.

## 10. Fontes

- Whisper, README e licença: https://github.com/openai/whisper
- Opções de linha de comando: https://github.com/openai/whisper/blob/main/whisper/transcribe.py
- Idiomas: https://github.com/openai/whisper/blob/main/whisper/tokenizer.py
- Artigo: https://arxiv.org/abs/2212.04356
- Parolu no Flathub: https://flathub.org/en/apps/im.bernard.Parolu
- Parolu, código: https://github.com/wbernard/parolu
- Piper, repositório atual: https://github.com/OHF-Voice/piper1-gpl
- FFmpeg, exigido pelo Whisper para ler mídia: https://ffmpeg.org/
