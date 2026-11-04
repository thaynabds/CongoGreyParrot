from pathlib import Path

from congo_reunioes.parse import parse_transcript, render_notes
from congo_reunioes.platforms import find_platform, platform_label
from congo_reunioes.store import NoteStore

TEAMS = """WEBVTT

00:00:06.000 --> 00:00:08.000
<v Ana Silva>Bom dia a todos.</v>

00:00:09.000 --> 00:00:11.000
<v Bruno Costa>Vou abrir o relatório.</v>
"""

MEET = """[00:01:02] Ana Silva: a pauta é o prazo
[00:01:10] Bruno Costa: eu entrego sexta
"""


def test_teams_and_meet_keep_speaker_names():
    teams = parse_transcript(TEAMS)
    assert [(line.speaker, line.text) for line in teams] == [
        ("Ana Silva", "Bom dia a todos."),
        ("Bruno Costa", "Vou abrir o relatório."),
    ]
    meet = parse_transcript(MEET)
    text = render_notes(meet, "Google Meet")
    assert "[00:01:02] Ana Silva: a pauta é o prazo" in text
    assert "Bruno Costa:" in text
    assert "eu entrego sexta" in text


def test_unknown_platform_is_only_a_label(tmp_path: Path):
    assert find_platform("Microsoft Teams").key == "teams"
    assert find_platform("Google Meet") is not None
    assert find_platform("sala da escola") is None
    assert platform_label("sala da escola") == "sala da escola"
    store = NoteStore(tmp_path / "notas.sqlite3")
    lines = parse_transcript("Lia: começamos agora")
    assert store.add("sala da escola", lines) == 1
    saved = store.lines("sala da escola")
    assert saved[0].speaker == "Lia"
    store.close()


def test_empty_transcript_explains_the_limit():
    text = render_notes([], "Microsoft Teams")
    assert "não traz esses nomes" in text


MEET_DOC = """Reunião de planejamento (2026-11-04 10:00 GMT-03:00) - Transcrição
Participantes
Ana Silva, Bruno Costa
Transcrição
00:00:00

Ana Silva: Bom dia, vamos começar.
Bruno Costa: Trouxe o cronograma.
00:05:00

Ana Silva: Fechamos o prazo para sexta.
A reunião terminou após 00:06:12
"""


def test_meet_doc_keeps_names_and_standalone_times():
    lines = parse_transcript(MEET_DOC)
    assert [(line.speaker, line.text, line.when) for line in lines] == [
        ("Ana Silva", "Bom dia, vamos começar.", "00:00:00"),
        ("Bruno Costa", "Trouxe o cronograma.", "00:00:00"),
        ("Ana Silva", "Fechamos o prazo para sexta.", "00:05:00"),
    ]
    text = render_notes(lines, "Google Meet")
    assert "Resumo: 3 falas de 2 pessoas. Falas por pessoa: Ana Silva (2), Bruno Costa (1). De 00:00:00 a 00:05:00." in text


def _write_docx(path: Path, paragraphs: list[str]) -> None:
    import zipfile
    from xml.sax.saxutils import escape

    body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(item)}</w:t></w:r></w:p>" for item in paragraphs)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)


def test_meet_docx_from_google_docs(tmp_path: Path):
    from congo_reunioes.parse import read_transcript_file

    path = tmp_path / "Reunião - Transcrição.docx"
    _write_docx(path, MEET_DOC.splitlines())
    lines = parse_transcript(read_transcript_file(path))
    assert [line.speaker for line in lines] == ["Ana Silva", "Bruno Costa", "Ana Silva"]
    assert lines[0].text == "Bom dia, vamos começar."


def test_docx_that_is_not_a_zip_is_refused(tmp_path: Path):
    import pytest
    from congo_reunioes.parse import read_transcript_file

    path = tmp_path / "falso.docx"
    path.write_text("não sou docx", encoding="utf-8")
    with pytest.raises(ValueError):
        read_transcript_file(path)


def test_importar_pasta_takes_new_transcripts_and_skips_repeats(tmp_path: Path):
    from congo_reunioes.importer import import_folder

    folder = tmp_path / "Downloads"
    folder.mkdir()
    _write_docx(folder / "Planejamento - Transcrição.docx", MEET_DOC.splitlines())
    (folder / "Daily - Transcript.txt").write_text("Lia: tudo certo\n", encoding="utf-8")
    (folder / "lista de compras.txt").write_text("Pão: dois\n", encoding="utf-8")
    (folder / "foto.png").write_bytes(b"x")
    store = NoteStore(tmp_path / "notas.sqlite3")
    try:
        first = {item.name: (item.status, item.count) for item in import_folder(store, folder, "Google Meet")}
        assert first == {
            "Daily - Transcript.txt": ("importado", 1),
            "Planejamento - Transcrição.docx": ("importado", 3),
        }
        second = import_folder(store, folder, "Google Meet")
        assert {item.status for item in second} == {"já importado"}
        assert len(store.lines("Google Meet")) == 4
        everything = {item.name for item in import_folder(store, folder, "Google Meet", every_file=True)}
        assert "lista de compras.txt" in everything
    finally:
        store.close()


def test_notas_formato_json_is_valid(tmp_path: Path, monkeypatch, capsys):
    import json
    import sys

    from congo_reunioes import main as cli

    monkeypatch.setenv("CONGO_REUNIOES_DATA", str(tmp_path))
    source = tmp_path / "Daily - Transcript.txt"
    source.write_text("00:01:00\nAna: oi\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["congo-reunioes", "importar", str(source), "--plataforma", "meet"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["congo-reunioes", "notas", "--plataforma", "meet", "--formato", "json"])
    cli.main()
    data = json.loads(capsys.readouterr().out)
    assert data == {"reuniao": "Google Meet", "falas": [{"pessoa": "Ana", "fala": "oi", "quando": "00:01:00"}]}
