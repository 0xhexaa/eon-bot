import discord
from discord import app_commands
from discord.ext import commands

from .. import sessions
from .common import error_embed, fancy_embed, not_logged_in_embed, run_in_thread, value_text


class Troll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_client(self, interaction: discord.Interaction):
        return sessions.get_session(interaction.user.id)

    async def require_client(self, interaction: discord.Interaction):
        client = self.get_client(interaction)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
        return client

    @app_commands.command(name="spoof-invite", description="Send invites from spoofed accounts.")
    @app_commands.describe(
        sender="The account to send the invite from",
        recipient="The account to send the invite to",
        amount="The number of invites to send (default: 1)",
    )
    async def spoof_invite(
        self,
        interaction: discord.Interaction,
        sender: str,
        recipient: str,
        amount: int = 1,
    ):
        client = await self.require_client(interaction)
        if client is None:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            result = await run_in_thread(client.spoof_invite, sender, recipient, amount)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        embed = fancy_embed("Spoof invite sent", "The invite has been sent successfully.")
        embed.add_field(name="Sender", value=value_text(sender), inline=True)
        embed.add_field(name="Recipient", value=value_text(recipient), inline=True)
        embed.add_field(name="Result", value=value_text(result), inline=False)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Troll(bot))
