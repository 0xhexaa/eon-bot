import json

import discord
from discord import app_commands
from discord.ext import commands

from .. import sessions
from eon_bot.friends.search import iter_friend_records
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
    @app_commands.describe(user="Party member to kick")
    async def kick(self, interaction: discord.Interaction, user: str):
        client = await self.require_client(interaction)
        if client is None:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        members = await run_in_thread(client.list_members)

        myself = next(
            (p for p in members if p.get("display_name") == client.display_name),
            None,
        )

        if myself is None:
            await interaction.followup.send(embed=error_embed("You are not in this party."))
            return

        is_captain = myself.get("role", "").lower() == "captain"
        if not is_captain:
            await interaction.followup.send(
                embed=error_embed("You must be party leader to kick people.")
            )
            return

        try:
            await run_in_thread(client.kick_username, user)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        await interaction.followup.send(
            embed=fancy_embed("Member removed", f"Successfully kicked: {user}")
        )

    @kick.autocomplete("user")
    async def kick_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        client = await self.require_client(interaction)
        if not client:
            return []

        members = await run_in_thread(client.list_members)

        people = []
        for member in members:
            username = member.get("display_name", "")
            if not username or username == client.display_name:
                continue
            people.append(username)
            if len(people) >= 25:  
                break

        return [
            app_commands.Choice(name=name, value=name)
            for name in people
            if current.lower() in name.lower()
        ][:25]


    @app_commands.command(name="join", description="Join a party by username")
    @app_commands.describe(user="User to join")
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

    async def _friend_autocomplete_options(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        client = await self.require_client(interaction)
        if not client:
            return []

        names: list[str] = []

        try:
            data = await run_in_thread(client.get_friends)
            friends = iter_friend_records(data)
        except Exception:
            friends = []

        for friend in friends:
            account_id = friend.get("accountId") or friend.get("account_id") or friend.get("id")
            if not account_id:
                continue
            try:
                name = (await run_in_thread(client.get_account, account_id)).get("displayName", "")
            except Exception:
                name = friend.get("displayName") or friend.get("display_name") or ""
            if not name or name == client.display_name:
                continue
            if len(names) >= 25:
                break
            names.append(name)

        if not names and current:
            try:
                matches = await run_in_thread(client.search, current)
            except Exception:
                matches = []
            for match in matches[:25]:
                name = match.get("displayName") or match.get("display_name") or match.get("username") or ""
                if not name or name == client.display_name:
                    continue
                names.append(name)

        seen = set()
        ordered: list[str] = []
        for name in names:
            if name.lower() not in seen and (not current or current.lower() in name.lower()):
                seen.add(name.lower())
                ordered.append(name)
            if len(ordered) >= 25:
                break

        return [app_commands.Choice(name=name, value=name) for name in ordered]

    @join.autocomplete("user")
    async def join_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await self._friend_autocomplete_options(interaction, current)

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

    @invite.autocomplete("user")
    async def invite_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await self._friend_autocomplete_options(interaction, current)


async def setup(bot: commands.Bot):
    await bot.add_cog(Party(bot))
