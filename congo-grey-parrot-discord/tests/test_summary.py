import asyncio

import pytest

from congo_discord.domain.summary import Utterance, summarize_meeting, summarize_text, text_from_upload
from congo_discord.presentation.bot import ICON_PATH, apply_icon


def test_upload_accepts_text_and_strips_subtitle_timing():
    vtt = (
        "WEBVTT\n\n1\n00:00:01.000 --> 00:00:02.000\n<v Ana>Ficou decidido lançar na sexta.</v>\n\n"
        "2\n00:00:03.000 --> 00:00:04.000\n<v Bruno>Eu vou preparar o relatório.</v>\n"
    )
    text = text_from_upload("reuniao.vtt", vtt.encode())
    assert "-->" not in text and "WEBVTT" not in text
    assert "Ana: Ficou decidido lançar na sexta." in text
    assert text_from_upload("notas.txt", "\ufeffolá".encode()) == "olá"


def test_upload_refuses_other_types_and_big_files():
    with pytest.raises(ValueError):
        text_from_upload("virus.exe", b"MZ")
    with pytest.raises(ValueError):
        text_from_upload("notas.txt.png", b"x")
    with pytest.raises(ValueError):
        text_from_upload("grande.txt", b"a" * (2 * 1024 * 1024 + 1))


def test_meeting_summary_uses_speaker_names():
    lines = [
        Utterance("Ana", "Ficou decidido que o mapa novo entra na próxima sessão.", "20:01"),
        Utterance("Bruno", "Eu vou preparar as fichas dos personagens até sexta.", "20:02"),
        Utterance("Carla", "Quem leva os dados para a sessão?", "20:03"),
    ]
    text = summarize_meeting(lines)
    assert "Resumo da reunião" in text and "Ana: Ficou decidido" in text and "Perguntas:" in text
    assert summarize_meeting([]) == "Ainda não há falas registradas nesta reunião."
    assert summarize_text("") == "Não há texto para resumir."


class _User:
    def __init__(self, avatar):
        self.avatar = avatar
        self.sent = None

    async def edit(self, avatar):
        self.sent = avatar


def test_bot_icon_is_the_desktop_parrot_and_is_set_only_once():
    assert ICON_PATH.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    empty = _User(None)
    assert asyncio.run(apply_icon(empty)) is True
    assert empty.sent == ICON_PATH.read_bytes()
    custom = _User("hash-que-ja-existe")
    assert asyncio.run(apply_icon(custom)) is False
    assert custom.sent is None
    assert asyncio.run(apply_icon(None)) is False
