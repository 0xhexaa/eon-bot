import requests

from eon_bot.auth.client import BASE


def get_user_party(client, account_id: str):
    resp = requests.get(
        f"{BASE}/party/api/v1/Fortnite/user/{account_id}",
        headers=client._auth_header(),
    )
    resp.raise_for_status()
    return resp.json()

