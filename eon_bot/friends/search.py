import requests

from eon_bot.auth.client import BASE


def search_accounts(client, prefix: str, platform: str = "epic"):
    resp = requests.get(
        f"{BASE}/api/v1/search/{client.account_id}",
        headers=client._auth_header(),
        params={"prefix": prefix, "platform": platform},
    )
    resp.raise_for_status()
    return resp.json()