import asyncio
import inspect
import json

import discord


def fancy_embed(
    title: str,
    description: str,
    color: discord.Colour = discord.Colour.green(),
) -> discord.Embed:
    return discord.Embed(title=title, description=description, colour=color)


def value_text(value, limit: int = 1024) -> str:
    if value is None or value == "":
        text = "Not available"
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=True, separators=(", ", ": "))
    else:
        text = str(value)
    return text[: limit - 3] + "..." if len(text) > limit else text


def error_embed(error: Exception | str) -> discord.Embed:
    message = str(error)
    print(f"Discord command error: {message}")
    return fancy_embed("Request failed", message, discord.Colour.red())


def not_logged_in_embed() -> discord.Embed:
    return fancy_embed(
        "You need to be logged in",
        "Use `/login` to sync your Eon account with your Discord client.",
        discord.Colour.red(),
    )


async def run_in_thread(function, *args, **kwargs):
    def call():
        result = function(*args, **kwargs)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result

    return await asyncio.to_thread(call)


def add_result_fields(embed: discord.Embed, result: dict, account=None, profile=None, party=None):
    display_name = result.get("displayName") or result.get("display_name")
    account_id = result.get("accountId") or result.get("account_id")
    embed.add_field(name="Display name", value=value_text(display_name), inline=True)
    embed.add_field(name="Account ID", value=value_text(account_id), inline=True)

    if account:
        embed.add_field(
            name="Account details",
            value=value_text(
                {
                    "name": account.get("displayName"),
                    "id": account.get("id"),
                    "externalAuths": account.get("externalAuths"),
                }
            ),
            inline=False,
        )

    if profile:
        profile_data = profile.get("profileChanges", profile)
        embed.add_field(name="Profile details", value=value_text(profile_data), inline=False)

    if party:
        current = party.get("current") or []
        embed.add_field(name="Current party", value=value_text(current), inline=False)
