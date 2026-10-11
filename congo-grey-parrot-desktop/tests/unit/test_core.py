from pathlib import Path

import pytest

from congo_grey_parrot.core.errors import AppError
from congo_grey_parrot.core.transcript import Transcript, Segment
from congo_grey_parrot.files.export_service import ExportService
from congo_grey_parrot.files.naming import assert_inside, classify, prepare_output, suggest_name
from congo_grey_parrot.media.ffmpeg_service import build_burn_command, build_convert_command
from congo_grey_parrot.models.downloader import validate_download_url
from congo_grey_parrot.persistence.database import Database
from congo_grey_parrot.speech.service import SpeechService, espeak_command, piper_length_scale
from congo_grey_parrot.subtitles.codec import (
    CaptionOptions,
    parse_srt,
    parse_timestamp,
    render_json,
    render_srt,
    render_tsv,
    render_vtt,
    wrap_caption,
)
from congo_grey_parrot.subtitles.edit import merge_with_next, shift_segments, split_segment
from congo_grey_parrot.transcription.languages import LANGUAGES
from congo_grey_parrot.transcription.options import TranscribeOptions, validate_options
from congo_grey_parrot.transcription.service import TranscriptionService
from congo_grey_parrot.translation.service import TranslationService


def sample() -> Transcript:
    return Transcript(
        text="olá mundo",
        language="pt",
        task="transcribe",
        model="tiny",
        segments=(Segment(0, 1.2, "olá"), Segment(1.2, 2.4, "mundo")),
        source_name="amostra.wav",
    )


def test_language_catalog_has_whisper_codes():
    codes = [code for code, _label in LANGUAGES]
    assert len(codes) == len(set(codes))
    assert "pt" in codes
    assert "en" in codes
    assert len(codes) == 100


def test_validate_translation_models():
    validate_options(TranscribeOptions(model="medium", task="translate", language="pt"))
    with pytest.raises(AppError):
        validate_options(TranscribeOptions(model="turbo", task="translate"))
    with pytest.raises(AppError):
        validate_options(TranscribeOptions(model="small.en", language="pt"))
    with pytest.raises(AppError):
        validate_options(TranscribeOptions(clip_start=4, clip_end=2))


def test_timestamps_and_captions(tmp_path: Path):
    assert parse_timestamp("00:00:01,250") == pytest.approx(1.25)
    assert parse_timestamp("1.5") == pytest.approx(1.5)
    text = render_srt(sample(), CaptionOptions(max_line_width=3))
    parsed = parse_srt(text)
    assert parsed.segments[0].text
    assert "WEBVTT" in render_vtt(sample())
    assert render_tsv(sample()).splitlines()[1].startswith("0\t")
    wrapped = wrap_caption("um dois tres", width=None, max_lines=None, max_words=2)
    assert wrapped == "um dois\ntres"
    payload = render_json(sample())
    assert "olá mundo" in payload
    target = tmp_path / "saida.srt"
    saved = ExportService().export_transcript(target, sample())
    assert saved.read_text(encoding="utf-8").startswith("1\n")


def test_plain_exports(tmp_path: Path):
    exporter = ExportService()
    txt = exporter.export_text(tmp_path / "a.txt", "linha")
    md = exporter.export_text(tmp_path / "a.md", "linha", "Titulo")
    docx = exporter.export_text(tmp_path / "a.docx", "linha", "Titulo")
    pdf = exporter.export_text(tmp_path / "a.pdf", "linha", "Titulo")
    assert "linha" in txt.read_text(encoding="utf-8")
    assert md.read_text(encoding="utf-8").startswith("# Titulo")
    assert docx.is_file() and pdf.is_file()
    with pytest.raises(AppError):
        exporter.export_text(tmp_path / "vazio.txt", "  ")


def test_subtitle_edits():
    segments = sample().segments
    shifted = shift_segments(segments, -5)
    assert shifted[0].start == 0
    split = split_segment(segments, 0)
    assert len(split) == 3
    merged = merge_with_next(segments, 0)
    assert len(merged) == 1
    assert "olá" in merged[0].text and "mundo" in merged[0].text


def test_paths_and_commands(tmp_path: Path):
    source = tmp_path / "audio.wav"
    source.write_bytes(b"RIFF")
    command = build_convert_command("ffmpeg", source, tmp_path / "out.mp3", 128)
    assert command[0] == "ffmpeg"
    assert "-vn" in command
    assert "shell" not in command
    subtitle = tmp_path / "legenda.srt"
    subtitle.write_text("1\n", encoding="utf-8")
    burn = build_burn_command("ffmpeg", source, subtitle, tmp_path / "out.mp4")
    assert burn[burn.index("-vf") + 1].startswith("subtitles=")
    assert classify(source) == "audio"
    assert suggest_name("aula:1.mp4", ".srt") == "aula_1.srt"
    with pytest.raises(AppError):
        prepare_output(tmp_path)
    with pytest.raises(AppError):
        assert_inside(tmp_path, tmp_path.parent)


def test_download_url_policy():
    validate_download_url("https://huggingface.co/rhasspy/piper-voices/resolve/main/x.onnx")
    with pytest.raises(AppError):
        validate_download_url("http://huggingface.co/arquivo")
    with pytest.raises(AppError):
        validate_download_url("https://example.com/arquivo.onnx")


def test_database_roundtrip(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    db.set_setting("theme", "dark")
    assert db.get_setting("theme") == "dark"
    db.add_history("transcrição", "a.wav", str(tmp_path / "a.txt"), "ok", "txt")
    assert db.list_history()[0]["kind"] == "transcrição"
    db.clear_history()
    assert db.list_history() == []
    db.close()


def test_speech_and_missing_engines(tmp_path: Path):
    assert piper_length_scale(1) == pytest.approx(0.8)
    command = espeak_command("espeak-ng", tmp_path / "a.wav", 1, 1)
    assert command[-1] == "--stdin"
    assert "--stdin" in command
    speech = SpeechService()
    if not speech.available_engines():
        with pytest.raises(AppError):
            speech.synthesize("olá", tmp_path / "a.wav")
    service = TranscriptionService(tmp_path / "modelos")
    if service.engine_name() == "":
        with pytest.raises(AppError):
            service.transcribe_file(tmp_path / "nao-existe.wav", TranscribeOptions(), lambda *_args: None, None)
    translation = TranslationService()
    if translation.engine_name() == "":
        with pytest.raises(AppError):
            translation.translate("olá", "pt", "en")


def test_documents_roundtrip(tmp_path: Path):
    from congo_grey_parrot.documents.service import read_document

    path = tmp_path / "nota.txt"
    path.write_text("conteúdo", encoding="utf-8")
    assert read_document(path) == "conteúdo"
    with pytest.raises(AppError):
        read_document(tmp_path / "arquivo.bin")
