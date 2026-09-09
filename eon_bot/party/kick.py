from eon_bot.friends.search import search_accounts
from eon_bot.party.join import remove_member


def kick_member(client, party_id: str, target_account_id: str):
    return remove_member(client, party_id, target_account_id)


def kick_username(client, username: str, party_id: str | None = None):
    matches = search_accounts(client, username)
    if not matches:
        raise ValueError(f"no account found matching {username!r}")

    target_id = matches[0]["accountId"]
    if party_id is None:
        parties = client.get_user_party(target_id)
        current = parties.get("current") or []
        if not current:
            raise ValueError(f"{username} isn't currently in a party")
        party_id = current[0]["id"]

    members = client.list_members(party_id)
    client_member = next(
        (member for member in members if member["account_id"] == client.account_id),
        None,
    )
    if not client_member or client_member.get("role") != "CAPTAIN":
        print("You need to be the party leader to kick members.")
        return

    if not any(member["account_id"] == target_id for member in members):
        raise ValueError(f"{username} isn't a member of party {party_id}")

    return remove_member(client, party_id, target_id)