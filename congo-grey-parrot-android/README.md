# Congo Grey Parrot para celular

O quadro completo dos dois programas está no [README da pasta principal](https://github.com/thaynabds/CongoGreyParrot/blob/main/README.md).

O APK de teste está em [CongoGreyParrot-debug.apk](https://github.com/thaynabds/CongoGreyParrot/blob/main/congo-grey-parrot-android/CongoGreyParrot-debug.apk). Copie esse arquivo para um Android 8 ou mais novo e abra. Se o sistema bloquear, permita a instalação por esse aplicativo: [instalar apps desconhecidos](https://support.google.com/android/answer/2664792?hl=pt-BR). Para gerar de novo sem o Android Studio, nesta pasta: `./gradlew assembleDebug`.

Esta versão grava áudio, lê texto com uma voz instalada que não usa a rede, e pede a pasta ao salvar. A transcrição Whisper fica no programa de computador.

Permissão pedida: microfone, só quando a gravação começa.
