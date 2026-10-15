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
