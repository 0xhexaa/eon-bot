import json

import discord
from discord import app_commands
from discord.ext import commands

from .. import sessions
from eon_bot.meta.meta import PartyMemberMeta
from .common import error_embed, fancy_embed, not_logged_in_embed, run_in_thread, value_text


class Party(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_client(self, interaction: discord.Interaction):
        return sessions.get_session(interaction.user.id)

    async def require_client(self, interaction: discord.Interaction):
        client = self.get_client(interaction)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
        return client

    @app_commands.command(name="party", description="Show your current party members")
    async def party(self, interaction: discord.Interaction):
        client = await self.require_client(interaction)
        if client is None:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            members = await run_in_thread(client.list_members)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        embed = fancy_embed("Current party", f"Party ID: {value_text(client.party_id)}")
        if not members:
            embed.description = "No party members were found."
        for member in members[:25]:
            embed.add_field(
                name=value_text(member.get("display_name") or member.get("account_id"), 256),
                value=(
                    f"Account ID: {value_text(member.get('account_id'))}\n"
                    f"Role: {value_text(member.get('role'))}"
                ),
                inline=False,
            )
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="leave", description="Leave your current party")
    async def leave(self, interaction: discord.Interaction):
        client = await self.require_client(interaction)
        if client is None:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await run_in_thread(client.leave)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        await interaction.followup.send(
            embed=fancy_embed("Party left", "You left the current party.")
        )

    @app_commands.command(name="kick", description="Kick a member from your current party")
    @app_commands.describe(user="Party member account ID")
    async def kick(self, interaction: discord.Interaction, user: str):
        client = await self.require_client(interaction)
        if client is None:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await run_in_thread(client.kick_member, user)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        await interaction.followup.send(
            embed=fancy_embed("Member removed", f"Account ID: {user}")
        )

    @app_commands.command(name="join", description="Join a party by username")
    @app_commands.describe(user="Username to join")
    async def join(self, interaction: discord.Interaction, user: str):
        client = await self.require_client(interaction)
        if client is None:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await run_in_thread(client.join, user)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        await interaction.followup.send(
            embed=fancy_embed("Party joined", f"Joined {user}'s party.")
        )

    @app_commands.command(name="invite", description="Invite a username to your party")
    @app_commands.describe(user="Username to invite")
    async def invite(self, interaction: discord.Interaction, user: str):
        client = await self.require_client(interaction)
        if client is None:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await run_in_thread(client.invite, user)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        await interaction.followup.send(
            embed=fancy_embed("Invitation sent", f"Invited {user}.")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Party(bot))
