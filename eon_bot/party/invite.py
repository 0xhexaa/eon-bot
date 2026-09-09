import requests

from eon_bot.auth.client import BASE


def send_invite(client, target_account_id: str):
    resp = requests.post(
        f"{BASE}/party/api/v1/Fortnite/user/{target_account_id}/pings/{client.account_id}",
        headers=client._auth_header(),
        json={
            "urn:epic:invite:platformdata_s": "",
            "urn:epic:conn:platform_s": "WIN",
        },
    )
    resp.raise_for_status()
    return resp.json()