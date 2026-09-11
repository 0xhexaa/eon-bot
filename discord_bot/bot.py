import asyncio

import discord
from discord.ext import commands
from discord import app_commands

from discord_bot.cogs.common import error_embed

INTENTS = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=INTENTS)

COGS = [
    "discord_bot.cogs.accounts",
    "discord_bot.cogs.friends",
    "discord_bot.cogs.party",
    "discord_bot.cogs.matchmaking",
    "discord_bot.cogs.troll",
    "discord_bot.cogs.cosmetics",
]


@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")
    await bot.tree.sync()


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    embed = error_embed(error)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def main():
    token = ""

    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
        await bot.start(token)
