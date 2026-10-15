from __future__ import annotations

import argparse
import os
from pathlib import Path

from congo_reunioes.parse import SpokenLine, parse_transcript, render_notes
from congo_reunioes.platforms import catalog_text, platform_label
from congo_reunioes.store import NoteStore

_WHISPER = "https://github.com/SYSTRAN/faster-whisper"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Anotações de reunião do Congo Grey Parrot. Programa separado do computador, do celular e do bot."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plataformas", help="Lista Teams, Meet e outras reuniões conhecidas.")
    import_command = commands.add_parser("importar", help="Importa uma transcrição com o nome de quem falou.")
    import_command.add_argument("arquivo")
    import_command.add_argument("--plataforma", default="outra")
    notes = commands.add_parser("notas", help="Mostra quem falou o que.")
    notes.add_argument("--plataforma", default="")
    clear = commands.add_parser("limpar", help="Apaga as anotações guardadas.")
    clear.add_argument("--plataforma", default="")
    audio = commands.add_parser("transcrever", help="Transcreve um áudio local, sem inventar nomes.")
    audio.add_argument("arquivo")
    audio.add_argument("--plataforma", default="audio-local")
    args = parser.parse_args()
    store = NoteStore(_data_file())
    try:
        if args.command == "plataformas":
            print(catalog_text())
            return
        if args.command == "importar":
            path = Path(args.arquivo)
            if not path.is_file():
                example = Path(__file__).resolve().parents[2] / "exemplo-teams.vtt"
                raise SystemExit(
                    f"Não achei o arquivo: {path}\n"
                    "Baixe a transcrição no Teams ou no Meet e use o caminho desse arquivo.\n"
                    f"Para testar, use: {example}"
                )
            raw = path.read_text(encoding="utf-8")
            lines = parse_transcript(raw)
            label = platform_label(args.plataforma)
            count = store.add(label, lines)
            print(render_notes(lines, label))
            print(f"\n{count} falas guardadas.")
            return
        if args.command == "notas":
            label = platform_label(args.plataforma) if args.plataforma else None
            lines = store.lines(label)
            print(render_notes(lines, label or "todas"))
            return
        if args.command == "limpar":
            label = platform_label(args.plataforma) if args.plataforma else None
            store.clear(label)
            print("Anotações apagadas." if label is None else f"Anotações de {label} apagadas.")
            return
        if args.command == "transcrever":
            text = _transcribe(Path(args.arquivo))
            label = platform_label(args.plataforma)
            lines = [SpokenLine("Gravação local", text, "")]
            store.add(label, lines)
            print(render_notes(lines, label))
            print(
                "\nUm arquivo de áudio sozinho não diz o nome de cada pessoa. "
                "Para Teams ou Meet, baixe a transcrição da própria reunião e use importar."
            )
    finally:
        store.close()


def _data_file() -> Path:
    root = Path(os.environ.get("CONGO_REUNIOES_DATA", Path.home() / ".local" / "share" / "congo-grey-parrot-reunioes"))
    return root / "notas.sqlite3"


def _transcribe(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"Arquivo não encontrado: {path}")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit(f"Instale o motor com: pip install faster-whisper\n{_WHISPER}") from None
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(path))
    return " ".join(segment.text.strip() for segment in segments) or "Não encontrei fala nesse arquivo."


if __name__ == "__main__":
    main()
