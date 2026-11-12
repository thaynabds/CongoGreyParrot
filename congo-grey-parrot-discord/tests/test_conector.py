from pathlib import Path

from congo_discord.presentation import bot


def test_discord_conector_hides_home_folder(monkeypatch):
    home = str(Path.home())
    monkeypatch.setattr(bot, "connector_report", lambda: f"AI Conector\n{home}/projeto/.venv/bin/congo-discord-mcp")
    text = bot.public_connector_report()
    assert home not in text
    assert "~/projeto/.venv/bin/congo-discord-mcp" in text


def test_real_conector_report_mentions_tools():
    text = bot.public_connector_report()
    assert text.startswith("AI Conector")
    assert str(Path.home()) not in text
