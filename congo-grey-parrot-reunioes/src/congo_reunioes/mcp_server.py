from __future__ import annotations

import json
import sys
from pathlib import Path

from congo_reunioes.importer import download_dir, import_file, import_folder, results_text
from congo_reunioes.main import _data_file, transcribe
from congo_reunioes.parse import TRANSCRIPT_SUFFIXES, SpokenLine, render_notes
from congo_reunioes.platforms import PLATFORMS, platform_label
from congo_reunioes.resumo import resumir, resumir_falas, resumo_texto
from congo_reunioes.store import NoteStore

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "mcp") not in sys.path:
    sys.path.insert(0, str(_REPO / "mcp"))

from runtime import guarded_dir, guarded_path, make_server, serve, user_errors  # noqa: E402


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
        """Importa um VTT, SRT, TXT ou DOCX (transcrição do Meet baixada do Google Docs), da pasta pessoal e fora de pastas ocultas."""
        path = guarded_path(caminho, TRANSCRIPT_SUFFIXES)
        if not path.is_file():
            return f"Não achei o arquivo: {path}"
        label = platform_label(plataforma)
        store = NoteStore(_data_file())
        try:
            result = import_file(store, path, label)
            if result.status != "importado":
                return f"{path.name}: {result.status}"
            lines = store.lines(label)[-result.count :]
        finally:
            store.close()
        return f"{result.count} falas guardadas.\n{render_notes(lines, label)}"

    @server.tool()
    @user_errors(ValueError, OSError)
    def importar_pasta(pasta: str = "", plataforma: str = "meet") -> str:
        """Importa as transcrições novas de uma pasta (padrão: Downloads), sem subpastas, sem repetir arquivo."""
        folder = guarded_dir(pasta) if pasta.strip() else download_dir()
        label = platform_label(plataforma)
        store = NoteStore(_data_file())
        try:
            return results_text(import_folder(store, folder, label))
        finally:
            store.close()

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

    @server.tool()
    def resumir_reuniao(plataforma: str = "", frases: int = 0) -> str:
        """Resume as falas guardadas: frases principais (tiradas do próprio texto), decisões, tarefas e perguntas."""
        label = platform_label(plataforma) if plataforma.strip() else None
        store = NoteStore(_data_file())
        try:
            lines = store.lines(label)
        finally:
            store.close()
        if not lines:
            return "Ainda não há falas guardadas. Importe uma transcrição antes."
        result = resumir_falas(((line.speaker, line.text) for line in lines), _clamp(frases))
        return resumo_texto(result, f"Resumo da reunião ({label or 'todas'})")

    @server.tool()
    def resumir_texto(texto: str, frases: int = 0) -> str:
        """Resume um texto colado, sem guardar nada. Aceita linhas no formato Nome: fala."""
        return resumo_texto(resumir(texto, _clamp(frases)))

    @server.tool()
    def notas_json(plataforma: str = "") -> str:
        """As falas guardadas em JSON (pessoa, fala, quando), para a IA analisar com precisão."""
        label = platform_label(plataforma) if plataforma.strip() else None
        store = NoteStore(_data_file())
        try:
            lines = store.lines(label)
        finally:
            store.close()
        rows = [{"pessoa": line.speaker, "fala": line.text, "quando": line.when} for line in lines]
        return json.dumps({"reuniao": label or "todas", "falas": rows}, ensure_ascii=False)

    @server.tool()
    @user_errors(ValueError, OSError)
    def transcrever_audio(caminho: str, plataforma: str = "audio-local") -> str:
        """Transcreve um áudio ou vídeo da pasta pessoal (fora de pastas ocultas) e guarda o texto nas notas."""
        path = guarded_path(caminho, MEDIA_SUFFIXES)
        if path.stat().st_size > MAX_MEDIA_BYTES:
            raise ValueError("O arquivo passa de 2 GB.")
        text = transcribe(path)
        label = platform_label(plataforma)
        lines = [SpokenLine("Gravação local", text, "")]
        store = NoteStore(_data_file())
        try:
            store.add(label, lines)
        finally:
            store.close()
        return render_notes(lines, label) + "\nUm áudio sozinho não diz o nome de cada pessoa."

    @server.tool()
    def limpar_notas(plataforma: str = "", confirmar: bool = False) -> str:
        """Apaga as anotações guardadas (de uma plataforma ou todas). Só apaga com confirmar=true, depois de perguntar à pessoa."""
        label = platform_label(plataforma) if plataforma.strip() else None
        alvo = "todas as anotações" if label is None else f"as anotações de {label}"
        if confirmar is not True:
            return f"Nada foi apagado. Pergunte à pessoa se quer mesmo apagar {alvo} e chame de novo com confirmar=true."
        store = NoteStore(_data_file())
        try:
            store.clear(label)
        finally:
            store.close()
        return f"Apaguei {alvo}."

    return server


MEDIA_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus", ".mp4", ".mkv", ".mov", ".webm"}
MAX_MEDIA_BYTES = 2 * 1024 * 1024 * 1024


def _clamp(frases) -> int:
    try:
        return max(0, min(30, int(frases)))
    except (TypeError, ValueError):
        return 0


def main() -> None:
    serve(build_server(), default_port=8766)


if __name__ == "__main__":
    main()
