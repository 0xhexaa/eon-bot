import discord
from discord import app_commands
from discord.ext import commands

from .. import sessions
from .common import error_embed, fancy_embed, not_logged_in_embed, run_in_thread


REGIONS = ["EU", "NAE", "NAW", "OCE", "BR", "ASIA"]
PLAYLISTS = [
    app_commands.Choice(
        name="Playlist Showdown Alt Solo",
        value="playlist_showdownalt_solo",
    ),
    app_commands.Choice(
        name="Playlist Showdown Alt Duo",
        value="playlist_showdownalt_duo",
    ),
]


class Matchmaking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="matchmake", description="Queue your party into a playlist")
    @app_commands.describe(playlist="Playlist", server="Region")
    @app_commands.choices(playlist=PLAYLISTS)
    @app_commands.choices(
        server=[app_commands.Choice(name=region, value=region) for region in REGIONS]
    )
    async def matchmake(
        self,
        interaction: discord.Interaction,
        playlist: str,
        server: app_commands.Choice[str] | None = None,
    ):
        client = sessions.get_session(interaction.user.id)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
            return

        region = server.value if server else "EU"
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            party_id = await run_in_thread(client.get_party_id)
            result = await run_in_thread(
                client.play,
                playlist,
                region=region,
                party_id=party_id,
            )
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        embed = fancy_embed("Match found", "Your party has joined a game session.")
        embed.add_field(name="Playlist", value=playlist, inline=True)
        embed.add_field(name="Region", value=region, inline=True)
        embed.add_field(
            name="Match ID",
            value=str(result.get("match_id") or "Not available"),
            inline=False,
        )
        embed.add_field(
            name="Server",
            value=f"{result.get('server_address')}:{result.get('server_port')}",
            inline=False,
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Matchmaking(bot))
