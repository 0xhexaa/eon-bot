import requests

from eon_bot.auth.client import BASE


def iter_friend_records(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    for key in ("friends", "summary", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = iter_friend_records(value)
            if nested:
                return nested

    friends = payload.get("friends")
    if isinstance(friends, dict):
        for value in friends.values():
            if isinstance(value, list):
                return value

    return []


def search_accounts(client, prefix: str, platform: str = "epic"):
    resp = requests.get(
        f"{BASE}/api/v1/search/{client.account_id}",
        headers=client._auth_header(),
        params={"prefix": prefix, "platform": platform},
    )
    resp.raise_for_status()
    return resp.json()


def get_friends(client):
    resp = requests.get(
        f"{BASE}/friends/api/v1/{client.account_id}/summary",
        headers=client._auth_header(),
    )

    resp.raise_for_status()
    return resp.json()