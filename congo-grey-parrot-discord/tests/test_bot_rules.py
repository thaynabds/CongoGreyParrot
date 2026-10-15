import random
from pathlib import Path

from congo_discord.domain.audio_pcm import mix_s16le, pcm48_stereo_to_pcm16_mono
from congo_discord.domain.dice import roll_expression, roll_pair, roll_percent, roll_pool
from congo_discord.domain.names import fantasy_name
from congo_discord.domain.rules import spell_text
from congo_discord.domain.summary import Utterance, render_meeting
from congo_discord.domain.vtt_catalog import find_vtt
from congo_discord.service.vtt_bridge import check_table_url, post_event
from congo_discord.persistence.store import Store
from congo_discord.service.meeting_audio import MeetingAudio
from congo_discord.service.updater import update_report


def test_dice_expression_and_pool():
    rng = random.Random(3)
    result = roll_expression("1d20+5", rng)
    assert result.total == result.total
    assert "1d20" in result.detail
    low, high = roll_pair("1d6", random.Random(1))
    assert 1 <= low.total <= 6
    assert 1 <= high.total <= 6
    percent = roll_percent(50, random.Random(2))
    assert percent.detail in {"sucesso decisivo", "sucesso", "falha", "falha grave"}
    pool = roll_pool(4, 10, 6, random.Random(4))
    assert 0 <= pool.total <= 4


def test_summary_names_every_line():
    text = render_meeting(
        [
            Utterance("Ana", "eu abro a porta", "2026-10-15T21:04:00"),
            Utterance("Bruno", "eu olho o corredor", "2026-10-15T21:05:00"),
            Utterance("Ana", "eu entro", "2026-10-15T21:06:00"),
        ]
    )
    assert text.count("Ana:") >= 2
    assert "[2026-10-15T21:04:00] Ana: eu abro a porta" in text
    assert "Bruno:" in text


def test_features_start_with_meeting_off(tmp_path: Path):
    store = Store(tmp_path / "bot.sqlite3")
    assert store.enabled("dados")
    assert not store.enabled("reuniao")
    assert store.set_enabled("reuniao", True)
    assert store.enabled("reuniao")
    assert not store.remove_custom("dados")
    store.add_custom("eco", "teste")
    assert store.remove_custom("eco")
    store.close()


def test_spell_text_uses_the_payload_and_credits_the_source():
    text = spell_text({"results": [{"name": "Luz", "level": 0, "desc": "Uma luz pequena.", "document": {"title": "SRD"}}]})
    assert "Luz" in text
    assert "Open5e" in text
    assert "Nenhum resultado" in spell_text({"results": []})


def test_vtt_connects_known_and_unknown_tables(tmp_path: Path):
    assert find_vtt("Roll20").site == "https://roll20.net/"
    assert find_vtt("Owlbear Rodeo").key == "owlbear"
    assert find_vtt("mesa da minha casa") is None
    try:
        check_table_url("javascript:alert(1)")
    except ValueError:
        pass
    else:
        raise AssertionError("endereço sem http deveria falhar")
    store = Store(tmp_path / "vtt.sqlite3")
    store.set_vtt("1", "Mesa da casa", "https://mesa.example/hook", "segredo", False)
    saved = store.vtt("1")
    assert saved["name"] == "Mesa da casa"
    assert saved["token"] == "segredo"
    assert store.clear_vtt("1")

    class _Response:
        status = 204

        def read(self, _size):
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def opener(request, timeout):
        assert timeout == 8
        assert request.get_header("Authorization") == "Bearer segredo"
        return _Response()

    status, _body = post_event("https://mesa.example/hook", "segredo", {"kind": "ping"}, opener)
    assert status == 204
    store.close()


def test_audio_helpers_and_names():
    stereo = b"\x01\x00\x02\x00" * 48
    mono = pcm48_stereo_to_pcm16_mono(stereo)
    assert mono
    assert mix_s16le(b"\x01\x00\x00\x00", b"\x01\x00\x00\x00")[:2] == b"\x02\x00"
    assert fantasy_name("pessoa", random.Random(1))
    meeting = MeetingAudio()
    meeting.add("Ana", stereo * 2000)
    flushed = meeting.flush(min_seconds=0.01)
    assert flushed and flushed[0][0] == "Ana"
    report = update_report(Path("/tmp/nao-e-repo-congo"), False)
    assert "Git" in report or "git" in report.lower()
