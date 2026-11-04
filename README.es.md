# Project Congo Grey Parrot

> Idioma: [Português](README.md) | [English](README.en.md) | **Español** | [中文](README.zh.md)

Cuatro programas separados, nombrados a partir de *Psittacus erithacus*. Cada uno tiene su carpeta, entorno y datos.

**Autora:** [Thayná Batista da Silva](https://github.com/thaynabds)

| Programa | Plataforma | Instalar |
|---|---|---|
| Computadora | Linux | `./instalar.sh 1` |
| Celular | Android 8 o más nuevo | `./instalar.sh 2` |
| Bot de Discord | Un servidor de Discord | `./instalar.sh 3` |
| Notas de reunión | Linux, a partir de archivos de Teams, Meet o Zoom | `./instalar.sh 4` |

En Linux, abra una terminal en esta carpeta y ejecute `./instalar.sh`. El menú pregunta qué programa instalar. No hace falta saber programar.

### Desde Flathub

El programa de computadora también se está publicando en [Flathub](https://flathub.org/apps/io.github.thaynabds.CongoGreyParrot), la tienda de aplicaciones de Linux. Cuando Flathub lo apruebe, aparece en GNOME Software y KDE Discover, o se instala con:

```bash
flatpak install flathub io.github.thaynabds.CongoGreyParrot
```

Dentro de Flatpak el programa solo ve las carpetas Música, Vídeos, Documentos y Descargas. Los archivos del manifiesto están en [congo-grey-parrot-desktop/flatpak](congo-grey-parrot-desktop/flatpak).

## Qué hace cada uno

* **Computadora.** Transcribe voz con Whisper (más de 90 idiomas, entre ellos portugués, inglés, español, francés, italiano, ruso, chino, japonés, árabe, bengalí, indonesio y urdu), lee texto, edita subtítulos y convierte medios. Detalle: [README de escritorio](congo-grey-parrot-desktop/README.es.md).
* **Celular.** Graba audio y lee texto sin internet. Detalle: [README de Android](congo-grey-parrot-android/README.es.md).
* **Discord.** Entra en un canal de voz, puede transcribir en vivo, reproducir audio y usar comandos de mesa. Detalle: [README de Discord](congo-grey-parrot-discord/README.es.md).
* **Reuniones.** Lee un archivo de transcripción que la plataforma ya exportó, incluida la transcripción de Google Meet descargada de Google Docs (`congo-reunioes importar-pasta`). Detalle: [README de reuniones](congo-grey-parrot-reunioes/README.es.md).
* **Resúmenes.** Todos los programas resumen: la pantalla Resumir de la computadora, la pantalla Leer del celular, `/reuniao resumo` y `/arquivo resumir` en Discord, `congo-reunioes resumo` y las herramientas MCP `resumir_texto`, `resumir_arquivo` y `resumir_reuniao`. El resumen elige las frases principales del propio texto y separa decisiones, tareas y preguntas. Funciona sin internet y no usa IA, así que no inventa nada.

La descripción técnica completa en portugués está en [README.md](README.md).

## Licencia

Este proyecto está bajo la licencia GPL-3.0 o posterior. Vea [LICENSE](LICENSE).
