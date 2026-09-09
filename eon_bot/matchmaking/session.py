import requests

from eon_bot.auth.client import BASE


def get_session(client, session_id: str):
    resp = requests.get(
        f"{BASE}/fortnite/api/matchmaking/session/{session_id}",
        headers=client._auth_header(),
    )
    resp.raise_for_status()
    return resp.json()


def get_session_key(client, session_id: str):
    resp = requests.get(
        f"{BASE}/fortnite/api/game/v2/matchmaking/account/{client.account_id}/session/{session_id}",
        headers=client._auth_header(),
    )
    resp.raise_for_status()
    return resp.json()


def join_session(client, session_id: str, session_key: str):
    resp = requests.post(
        f"{BASE}/fortnite/api/matchmaking/session/{session_id}/join",
        headers=client._auth_header(),
        params={"accountId": client.account_id, "sessionKey": session_key},
    )
    resp.raise_for_status()
    return resp.status_code