import discord
from discord import app_commands
from discord.ext import commands

from eon_bot.auth.client import EonClient

from .. import sessions, storage
from .common import error_embed, fancy_embed, not_logged_in_embed, run_in_thread


class LoginModal(discord.ui.Modal, title="Log into eon"):
    email = discord.ui.TextInput(label="Email")
    password = discord.ui.TextInput(label="Password")
    save_as = discord.ui.TextInput(label="Save as (optional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        client = EonClient(self.email.value, self.password.value)
        try:
            await run_in_thread(client.login)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc), ephemeral=True)
            return

        sessions.set_session(interaction.user.id, client)
        if self.save_as.value:
            await run_in_thread(
                storage.save_account,
                interaction.user.id,
                self.save_as.value,
                self.email.value,
                self.password.value,
            )

        await interaction.followup.send(
            embed=fancy_embed("Login successful", f"Authenticated as {client.display_name}."),
            ephemeral=True,
        )


class Accounts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="login", description="Log into an eon account")
    @app_commands.describe(saved="A previously saved account")
    async def login(self, interaction: discord.Interaction, saved: str | None = None):
        if saved is None:
            await interaction.response.send_modal(LoginModal())
            return

        account = await run_in_thread(storage.get_account, interaction.user.id, saved)
        if account is None:
            await interaction.response.send_message(
                embed=error_embed(f"No saved account called {saved!r}."), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        client = EonClient(account["email"], account["password"])
        try:
            await run_in_thread(client.login)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc), ephemeral=True)
            return

        sessions.set_session(interaction.user.id, client)
        await interaction.followup.send(
            embed=fancy_embed("Login successful", f"Authenticated as {client.display_name}."),
            ephemeral=True,
        )

    @app_commands.command(name="logout", description="Log out of your linked Eon account")
    async def logout(self, interaction: discord.Interaction):
        if sessions.get_session(interaction.user.id) is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
            return

        sessions.clear_session(interaction.user.id)
        await interaction.response.send_message(
            embed=fancy_embed("Logout successful", "Your Eon account has been unlinked."),
            ephemeral=True,
        )

    @login.autocomplete("saved")
    async def saved_autocomplete(self, interaction: discord.Interaction, current: str):
        accounts = await run_in_thread(storage.get_accounts, interaction.user.id)
        return [
            app_commands.Choice(name=account["label"], value=account["label"])
            for account in accounts
            if current.lower() in account["label"].lower()
        ][:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(Accounts(bot))
