"""Monta o bot de verdade com todos os comandos e plugins, sem conectar no Discord.

Pega erro que só aparecia ao ligar o bot, como anotação de tipo sem import.
"""
from pathlib import Path

from congo_discord.persistence.store import Store
from congo_discord.presentation.bot import CongoBot, register
from congo_discord.service.plugins import load_plugins

ROOT = Path(__file__).resolve().parents[1]


def test_all_commands_and_plugins_register(tmp_path):
    import asyncio

    store = Store(tmp_path / "bot.sqlite3")

    async def build():
        bot = CongoBot(store, ROOT, tmp_path, ROOT / "plugins")
        await bot._async_setup_hook()  # o mesmo preparo que o discord.py faz antes do setup_hook
        register(bot)
        loaded = load_plugins(ROOT / "plugins", store, bot)
        await bot.close()
        return bot, loaded

    bot, loaded = asyncio.run(build())
    assert {"navegador", "eco", "musica"} <= set(loaded)
    names = {command.name for command in bot.tree.get_commands()}
    assert {"reuniao", "arquivo", "navegador"} <= names
    reuniao = next(c for c in bot.tree.get_commands() if c.name == "reuniao")
    assert {"resumo", "transcricao"} <= {c.name for c in reuniao.commands}
