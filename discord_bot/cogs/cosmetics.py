import discord
from discord import app_commands
from discord.ext import commands
import json

from .. import sessions
from eon_bot.cosmetics.cosmetics import (
    BACKPACK_PATH,
    CHARACTER_PATH,
    EMTOTE_PATH,
    PICKAXE_PATH,
    cache,
    set_backpack,
    set_emote,
    set_outfit,
    set_outfit_style,
    set_pickaxe,
    set_level,
)
from eon_bot.meta.meta import PartyMemberMeta
from .common import error_embed, fancy_embed, not_logged_in_embed, run_in_thread, value_text

NONE_CHOICE = "None"
ASSET_PATHS = {
    "outfit": CHARACTER_PATH,
    "backpack": BACKPACK_PATH,
    "pickaxe": PICKAXE_PATH,
    "emote": EMTOTE_PATH,
}


def cosmetic_embed(cosmetic: dict) -> discord.Embed:
    cosmetic_id = cosmetic.get("id", "Unknown")
    cosmetic_type = (cosmetic.get("type") or {}).get("value")
    introduction = (cosmetic.get("introduction") or {}).get("text") or "No introduction available."
    asset_template = ASSET_PATHS.get(cosmetic_type)
    asset_path = asset_template.format(id=cosmetic_id) if asset_template else "Not available"

    embed = fancy_embed(cosmetic.get("name", "Cosmetic"), introduction)
    small_icon = (cosmetic.get("images") or {}).get("smallIcon")
    if small_icon:
        embed.set_thumbnail(url=small_icon)
    embed.add_field(name="Cosmetic ID", value=value_text(cosmetic_id), inline=True)
    embed.add_field(name="Asset path", value=value_text(asset_path), inline=False)
    return embed


async def outfit_autocomplete(interaction: discord.Interaction, current: str):
    await cache.ensure_loaded()
    matches = cache.search(cache.outfits, current)
    return [app_commands.Choice(name=c["name"][:100], value=c["id"]) for c in matches]


async def backpack_autocomplete(interaction: discord.Interaction, current: str):
    await cache.ensure_loaded()
    matches = cache.search(cache.backpacks, current)
    choices = [app_commands.Choice(name=NONE_CHOICE, value=NONE_CHOICE)]
    choices += [app_commands.Choice(name=c["name"][:100], value=c["id"]) for c in matches]
    return choices[:25]


async def pickaxe_autocomplete(interaction: discord.Interaction, current: str):
    await cache.ensure_loaded()
    matches = cache.search(cache.pickaxes, current)
    return [app_commands.Choice(name=c["name"][:100], value=c["id"]) for c in matches]

async def emote_autocomplete(interaction: discord.Interaction, current: str):
    await cache.ensure_loaded()
    matches = cache.search(cache.emotes, current)
    return [app_commands.Choice(name=c["name"][:100], value=c["id"]) for c in matches]


class VariantSelect(discord.ui.Select):
    def __init__(self, cosmetic: dict, member_meta: PartyMemberMeta):
        self.cosmetic = cosmetic
        self.member_meta = member_meta

        options = []
        for channel in cosmetic.get("variants", []):
            for variant in channel.get("options", []):
                options.append(
                    discord.SelectOption(
                        label=variant["name"][:100],
                        value=f"{channel['channel']}/{variant['tag']}",
                    )
                )
        super().__init__(placeholder="Choose a style", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        channel, tag = self.values[0].split("/", 1)
        try:
            await run_in_thread(set_outfit_style, self.member_meta, channel, tag)
        except Exception as exc:
            await interaction.response.send_message(embed=error_embed(exc), ephemeral=True)
            return
        await interaction.response.edit_message(content=f"Style set to **{tag}**.", view=None)


class VariantView(discord.ui.View):
    def __init__(self, cosmetic: dict, member_meta: PartyMemberMeta, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(VariantSelect(cosmetic, member_meta))

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user_id


class Cosmetics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_client(self, interaction: discord.Interaction):
        return sessions.get_session(interaction.user.id)

    @app_commands.command(name="cosmetics", description="Change the bot's outfit, backpack, or pickaxe")
    @app_commands.describe(
        outfit="Outfit to equip",
        backpack="Backpack to equip (pick None to remove it)",
        pickaxe="Pickaxe to equip",
    )
    @app_commands.autocomplete(
        outfit=outfit_autocomplete,
        backpack=backpack_autocomplete,
        pickaxe=pickaxe_autocomplete,
    )
    async def cosmetics(
        self,
        interaction: discord.Interaction,
        outfit: str = None,
        backpack: str = None,
        pickaxe: str = None,
    ):
        client = self.get_client(interaction)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
            return

        if not any([outfit, backpack, pickaxe]):
            await interaction.response.send_message(
                embed=fancy_embed("Nothing to change", "Pass at least one of outfit, backpack or pickaxe."),
                ephemeral=True,
            )
            return

        member_meta = getattr(client, "party_meta", None)
        if member_meta is None:
            await interaction.response.send_message(
                embed=error_embed("The bot needs to be in a party before its cosmetics can change."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        await cache.ensure_loaded()

        try:
            if outfit:
                await run_in_thread(set_outfit, member_meta, outfit)
            if backpack:
                backpack_id = None if backpack == NONE_CHOICE else backpack
                await run_in_thread(set_backpack, member_meta, backpack_id)
            if pickaxe:
                await run_in_thread(set_pickaxe, member_meta, pickaxe)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        embeds = []
        if outfit:
            cosmetic = cache.by_id.get(outfit, {"id": outfit, "name": outfit, "type": {"value": "outfit"}})
            embeds.append(cosmetic_embed(cosmetic))
        if backpack:
            if backpack == NONE_CHOICE:
                embeds.append(fancy_embed("Backpack removed", "The bot's backpack was removed."))
            else:
                cosmetic = cache.by_id.get(backpack, {"id": backpack, "name": backpack, "type": {"value": "backpack"}})
                embeds.append(cosmetic_embed(cosmetic))
        if pickaxe:
            cosmetic = cache.by_id.get(pickaxe, {"id": pickaxe, "name": pickaxe, "type": {"value": "pickaxe"}})
            embeds.append(cosmetic_embed(cosmetic))
        await interaction.followup.send(embeds=embeds)

        outfit_cosmetic = cache.by_id.get(outfit) if outfit else None
        if outfit_cosmetic and outfit_cosmetic.get("variants"):
            await interaction.followup.send(
                f"**{outfit_cosmetic['name']}** has styles you can pick from:",
                view=VariantView(outfit_cosmetic, member_meta, interaction.user.id),
                ephemeral=True,
            )

    @app_commands.command(name="emote", description="Change the bot's emote")
    @app_commands.describe(emote="Emote to equip")
    @app_commands.autocomplete(emote=emote_autocomplete)
    async def emote(
        self,
        interaction: discord.Interaction,
        emote: str,
    ):
        client = self.get_client(interaction)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
            return

        member_meta = getattr(client, "party_meta", None)
        if member_meta is None:
            await interaction.response.send_message(
                embed=error_embed("The bot needs to be in a party before its emote can change."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        await cache.ensure_loaded()

        try:
            await run_in_thread(set_emote, member_meta, emote)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        cosmetic = cache.by_id.get(emote, {"id": emote, "name": emote, "type": {"value": "emote"}})
        await interaction.followup.send(embed=cosmetic_embed(cosmetic))

    @app_commands.command(name="setlevel", description="Set the bot's season level")
    @app_commands.describe(amount="Season level to display")
    async def level(self, interaction: discord.Interaction, amount: int):
        client = self.get_client(interaction)
        if client is None:
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
            return

        member_meta = getattr(client, "party_meta", None)
        if member_meta is None:
            await interaction.response.send_message(
                embed=error_embed("The bot needs to be in a party before its emote can change."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        await cache.ensure_loaded()
        
        try:
            await run_in_thread(set_level, member_meta, amount)
        except Exception as exc:
            await interaction.followup.send(embed=error_embed(exc))
            return

        await interaction.followup.send(
            embed=fancy_embed("Season level updated", f"The bot's season level is now **{amount}**.")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Cosmetics(bot))