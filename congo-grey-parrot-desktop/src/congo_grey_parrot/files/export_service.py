from __future__ import annotations

import shutil
from pathlib import Path

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.core.transcript import Transcript
from congo_grey_parrot.documents.service import write_docx, write_pdf
from congo_grey_parrot.files.naming import prepare_output
from congo_grey_parrot.subtitles.codec import (
    CaptionOptions,
    render_ass,
    render_json,
    render_jsonl,
    render_srt,
    render_tsv,
    render_vtt,
)


class ExportService:
    def export_text(self, path: Path, text: str, title: str = "") -> Path:
        target = prepare_output(path)
        suffix = target.suffix.lower()
        body = text.strip()
        if not body:
            raise AppError("Nada para salvar.")
        if suffix == ".txt":
            target.write_text(body + "\n", encoding="utf-8")
        elif suffix == ".md":
            content = f"# {title}\n\n{body}\n" if title else body + "\n"
            target.write_text(content, encoding="utf-8")
        elif suffix == ".docx":
            write_docx(target, body, title)
        elif suffix == ".pdf":
            write_pdf(target, body, title)
        else:
            raise AppError("Formato de texto não suportado. Use TXT, MD, DOCX ou PDF.")
        return target

    def export_transcript(
        self,
        path: Path,
        transcript: Transcript,
        plain_text: str | None = None,
        captions: CaptionOptions | None = None,
        title: str = "",
    ) -> Path:
        target = prepare_output(path)
        suffix = target.suffix.lower()
        captions = captions or CaptionOptions()
        if suffix in {".txt", ".md", ".docx", ".pdf"}:
            text = plain_text if plain_text is not None else transcript.text
            return self.export_text(target, text, title or transcript.source_name)
        if suffix == ".srt":
            target.write_text(render_srt(transcript, captions), encoding="utf-8")
        elif suffix == ".vtt":
            target.write_text(render_vtt(transcript, captions), encoding="utf-8")
        elif suffix == ".tsv":
            target.write_text(render_tsv(transcript), encoding="utf-8")
        elif suffix in {".ass", ".ssa"}:
            target.write_text(render_ass(transcript, captions), encoding="utf-8")
        elif suffix == ".json":
            target.write_text(render_json(transcript), encoding="utf-8")
        elif suffix == ".jsonl":
            target.write_text(render_jsonl(transcript), encoding="utf-8")
        else:
            raise AppError(
                "Formato não suportado. Use TXT, MD, DOCX, PDF, SRT, VTT, ASS, TSV, JSON ou JSONL."
            )
        return target

    def copy_file(self, source: Path, destination: Path) -> Path:
        if not source.is_file():
            raise AppError("O arquivo de origem não existe.")
        target = prepare_output(destination)
        if source.resolve() == target.resolve():
            return target
        shutil.copy2(source, target)
        return target
