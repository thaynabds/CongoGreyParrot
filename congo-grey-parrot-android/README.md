# Congo Grey Parrot, celular

> Idioma: **Português** | [English](README.en.md) | [Español](README.es.md) | [中文](README.zh.md)

Aplicativo Android 8 ou mais novo. Grava áudio pelo microfone e lê texto em voz alta com uma voz já instalada no aparelho. Não usa a internet e não transcreve com Whisper. Para transcrever, abra a gravação no programa de computador.

## Instalar

1. Copie o arquivo [CongoGreyParrot-debug.apk](CongoGreyParrot-debug.apk) para o celular.
2. Abra o arquivo.
3. Se o Android bloquear, permita a instalação por esse aplicativo: [instalar apps desconhecidos](https://support.google.com/android/answer/2664792?hl=pt-BR).

Para gerar o APK de novo, nesta pasta: `./gradlew assembleDebug`.

## Telas

| Tela | O que faz |
|---|---|
| Início | Atalhos para gravar, ler e ver arquivos |
| Gravar | Grava pelo microfone e pede pasta e nome ao salvar |
| Ler | Lê texto com voz offline e ajusta a velocidade |
| Arquivos | Lista, compartilha ou exclui cópias guardadas no app |
| Ajustes | Tema e filtro de cor |

O microfone só é pedido quando a gravação começa.
