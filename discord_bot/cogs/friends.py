import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from .. import sessions
from .common import (
    add_result_fields,
    error_embed,
    fancy_embed,
    not_logged_in_embed,
    run_in_thread,
    value_text,
)


class Friends(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_client(self, interaction: discord.Interaction):
        return sessions.get_session(interaction.user.id)

    @app_commands.command(name="search", description="Search for an Epic account and show its details")
    @app_commands.describe(user="Username or prefix to search for")
    async def search(self, interaction: discord.Interaction, user: str):
        client = self.get_client(interaction)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        try:
            matches = await run_in_thread(client.search, user)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(str(exc)), ephemeral=True)
            return

        if not matches:
            await interaction.followup.send(
                embed=fancy_embed("Account search", f"No accounts matched {user!r}."),
                ephemeral=True,
            )
            return

        embeds = []
        for result in matches[:10]:
            account = profile = party = None
            account_id = result.get("accountId")
            try:
                account = await run_in_thread(client.get_account_for, account_id)
            except Exception as exc:
                print(f"Account details error: {exc}")
            try:
                profile = await run_in_thread(client.get_profile_for, account_id)
            except Exception as exc:
                print(f"Profile details error: {exc}")
            try:
                party = await run_in_thread(client.get_user_party, account_id)
            except Exception as exc:
                print(f"Party details error: {exc}")

            embed = fancy_embed("Account details", "Details returned by the Eon service.")
            add_result_fields(embed, result, account, profile, party)
            embeds.append(embed)

        await interaction.followup.send(embeds=embeds)

    @app_commands.command(name="addfriend", description="Send a friend request to an Epic account")
    @app_commands.describe(user="Username or account ID")
    async def add_friend(self, interaction: discord.Interaction, user: str):
        await self._friend_action(interaction, user, add=True)

    @app_commands.command(name="removefriend", description="Remove an Epic account from your friends")
    @app_commands.describe(user="Username or account ID")
    async def remove_friend(self, interaction: discord.Interaction, user: str):
        await self._friend_action(interaction, user, add=False)

    async def _friend_action(self, interaction: discord.Interaction, user: str, add: bool):
        client = self.get_client(interaction)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            account_id = user
            if not user.isalnum() or len(user) != 32:
                matches = await run_in_thread(client.search, user)
                if not matches:
                    raise ValueError(f"No account found matching {user!r}.")
                account_id = matches[0]["accountId"]
            if add:
                await run_in_thread(client.add_friend, account_id)
                title = "Friend request sent"
            else:
                await run_in_thread(client.remove_friend, account_id)
                title = "Friend removed"
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(str(exc)))
            return

        await interaction.followup.send(
            embed=fancy_embed(title, f"Account ID: {value_text(account_id)}")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Friends(bot))