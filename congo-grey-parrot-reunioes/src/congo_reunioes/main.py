from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from congo_reunioes.importer import download_dir, import_file, import_folder, results_text
from congo_reunioes.parse import SpokenLine, render_notes
from congo_reunioes.platforms import catalog_text, platform_label
from congo_reunioes.resumo import resumir_falas, resumo_texto
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
    folder_command = commands.add_parser(
        "importar-pasta",
        help="Importa as transcrições novas de uma pasta (padrão: Downloads) e pula as que já entraram.",
    )
    folder_command.add_argument("pasta", nargs="?", default="")
    folder_command.add_argument("--plataforma", default="meet")
    folder_command.add_argument("--todos", action="store_true", help="Inclui arquivos sem Transcript no nome.")
    notes = commands.add_parser("notas", help="Mostra quem falou o que.")
    notes.add_argument("--plataforma", default="")
    notes.add_argument("--formato", choices=("texto", "json"), default="texto", help="json serve para outro programa ou IA ler.")
    summary = commands.add_parser("resumo", help="Resume as falas guardadas: frases principais, decisões, tarefas e perguntas.")
    summary.add_argument("--plataforma", default="")
    summary.add_argument("--frases", type=int, default=0, help="Quantas frases no resumo (padrão: automático).")
    summary.add_argument("--formato", choices=("texto", "json"), default="texto")
    clear = commands.add_parser("limpar", help="Apaga as anotações guardadas.")
    clear.add_argument("--plataforma", default="")
    audio = commands.add_parser("transcrever", help="Transcreve um áudio local, sem inventar nomes.")
    audio.add_argument("arquivo")
    audio.add_argument("--plataforma", default="audio-local")
    connector = commands.add_parser("conector", help="AI Conector: liga uma IA a este programa por MCP.")
    connector.add_argument("--conectar", action="store_true", help="Registra no Claude Desktop e no Cursor.")
    connector.add_argument("--desconectar", action="store_true", help="Tira do Claude Desktop e do Cursor.")
    args = parser.parse_args()
    if args.command == "conector":
        raise SystemExit(_connector(args))
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
            label = platform_label(args.plataforma)
            result = import_file(store, path, label)
            if result.status != "importado":
                raise SystemExit(f"{path.name}: {result.status}")
            print(render_notes(store.lines(label)[-result.count :], label))
            print(f"\n{result.count} falas guardadas.")
            return
        if args.command == "importar-pasta":
            folder = Path(args.pasta).expanduser() if args.pasta else download_dir()
            try:
                results = import_folder(store, folder, platform_label(args.plataforma), args.todos)
            except ValueError as exc:
                raise SystemExit(str(exc)) from None
            print(results_text(results))
            return
        if args.command == "notas":
            label = platform_label(args.plataforma) if args.plataforma else None
            lines = store.lines(label)
            if args.formato == "json":
                rows = [{"pessoa": line.speaker, "fala": line.text, "quando": line.when} for line in lines]
                print(json.dumps({"reuniao": label or "todas", "falas": rows}, ensure_ascii=False, indent=2))
                return
            print(render_notes(lines, label or "todas"))
            return
        if args.command == "resumo":
            label = platform_label(args.plataforma) if args.plataforma else None
            lines = store.lines(label)
            result = resumir_falas(((line.speaker, line.text) for line in lines), max(0, args.frases))
            if args.formato == "json":
                print(json.dumps({"reuniao": label or "todas", **result.to_dict()}, ensure_ascii=False, indent=2))
                return
            if not lines:
                print("Ainda não há falas guardadas. Use importar ou importar-pasta antes.")
                return
            print(resumo_texto(result, f"Resumo da reunião ({label or 'todas'})"))
            return
        if args.command == "limpar":
            label = platform_label(args.plataforma) if args.plataforma else None
            store.clear(label)
            print("Anotações apagadas." if label is None else f"Anotações de {label} apagadas.")
            return
        if args.command == "transcrever":
            try:
                text = transcribe(Path(args.arquivo))
            except ValueError as exc:
                raise SystemExit(str(exc)) from None
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
    explicit = os.environ.get("CONGO_REUNIOES_DATA", "").strip()
    if explicit:
        return Path(explicit) / "notas.sqlite3"
    # Segue o padrão do Linux: XDG_DATA_HOME, se definido, senão ~/.local/share.
    base = os.environ.get("XDG_DATA_HOME", "").strip() or str(Path.home() / ".local" / "share")
    root = Path(base) / "congo-grey-parrot-reunioes"
    return root / "notas.sqlite3"


def _connector(args) -> int:
    import sys

    repo_mcp = Path(__file__).resolve().parents[3] / "mcp"
    if not (repo_mcp / "conector.py").is_file():
        print("Esta instalação não traz a pasta mcp do projeto. Instale pelo repositório com ./instalar.sh.")
        return 1
    if str(repo_mcp) not in sys.path:
        sys.path.insert(0, str(repo_mcp))
    import conector

    from congo_reunioes.mcp_server import build_server

    flags = ["--conectar"] if args.conectar else ["--desconectar"] if args.desconectar else []
    return conector.cli("congo-reunioes", build_server, flags)


def transcribe(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"Arquivo não encontrado: {path}")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ValueError(f"Instale o motor com: pip install faster-whisper\n{_WHISPER}") from None
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(path))
    return " ".join(segment.text.strip() for segment in segments) or "Não encontrei fala nesse arquivo."


if __name__ == "__main__":
    main()
