from __future__ import annotations

import sys
from pathlib import Path

from congo_reunioes.main import _data_file
from congo_reunioes.parse import parse_transcript, render_notes
from congo_reunioes.platforms import PLATFORMS, platform_label
from congo_reunioes.store import NoteStore

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "mcp") not in sys.path:
    sys.path.insert(0, str(_REPO / "mcp"))

from runtime import guarded_path, make_server, serve, user_errors  # noqa: E402

TRANSCRIPT_SUFFIXES = {".vtt", ".txt", ".srt"}
MAX_TRANSCRIPT_BYTES = 20 * 1024 * 1024


def build_server():
    server = make_server("Congo Grey Parrot Reunioes")

    @server.tool()
    def listar_plataformas() -> str:
        """Lista Teams, Meet, Zoom e as outras reuniões conhecidas. Não entra na conta delas."""
        lines = []
        for item in PLATFORMS:
            lines.append(f"{item.key}: {item.name}. {item.site} {item.note}")
        return "\n".join(lines)

    @server.tool()
    @user_errors(ValueError, OSError)
    def importar_transcricao(caminho: str, plataforma: str = "outra") -> str:
        """Importa um VTT, SRT ou TXT com falas, da pasta pessoal e fora de pastas ocultas."""
        path = guarded_path(caminho, TRANSCRIPT_SUFFIXES)
        if not path.is_file():
            return f"Não achei o arquivo: {path}"
        if path.stat().st_size > MAX_TRANSCRIPT_BYTES:
            return "O arquivo passou de 20 MB."
        raw = path.read_text(encoding="utf-8")
        lines = parse_transcript(raw)
        label = platform_label(plataforma)
        store = NoteStore(_data_file())
        try:
            count = store.add(label, lines)
        finally:
            store.close()
        return f"{count} falas guardadas.\n{render_notes(lines, label)}"

    @server.tool()
    def listar_notas(plataforma: str = "") -> str:
        """Mostra as anotações já importadas neste computador."""
        label = platform_label(plataforma) if plataforma.strip() else None
        store = NoteStore(_data_file())
        try:
            lines = store.lines(label)
        finally:
            store.close()
        return render_notes(lines, label or "todas")

    return server


def main() -> None:
    serve(build_server(), default_port=8766)


if __name__ == "__main__":
    main()
