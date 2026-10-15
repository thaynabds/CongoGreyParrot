FEATURE = "eco"
DESCRIPTION = "Repete um texto. Exemplo de função colocada na pasta plugins."


def setup(bot) -> None:
    import discord
    from discord import app_commands

    @bot.tree.command(name="eco", description="Repete o texto. Só responde se a função eco estiver ligada.")
    async def eco(interaction: discord.Interaction, texto: str) -> None:
        if not bot.store.enabled("eco"):
            await interaction.response.send_message("A função eco está desativada.", ephemeral=True)
            return
        await interaction.response.send_message(texto[:1800], ephemeral=True)
