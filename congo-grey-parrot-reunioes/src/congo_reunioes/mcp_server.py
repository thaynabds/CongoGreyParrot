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

from runtime import make_server, serve  # noqa: E402


def local_path(raw: str) -> Path:
    path = Path(raw).expanduser().resolve()
    home = Path.home().resolve()
    if path != home and home not in path.parents:
        raise ValueError("O caminho precisa ficar dentro da sua pasta pessoal.")
    return path


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
    def importar_transcricao(caminho: str, plataforma: str = "outra") -> str:
        """Importa um VTT ou um texto com falas. O arquivo precisa estar na pasta pessoal."""
        path = local_path(caminho)
        if not path.is_file():
            return f"Não achei o arquivo: {path}"
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
