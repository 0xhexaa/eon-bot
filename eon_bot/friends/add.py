import requests

from eon_bot.auth.client import BASE


def add_friend(client, target_account_id: str):
    resp = requests.post(
        f"{BASE}/friends/api/v1/{client.account_id}/friends/{target_account_id}",
        headers=client._auth_header(),
    )
    resp.raise_for_status()
    return resp.status_code