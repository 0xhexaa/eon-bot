import requests

from eon_bot.auth.client import BASE


def get_ticket(
    client,
    party_id: str,
    playlist_name: str,
    tournament_id: str = "",
    event_window_id: str = "",
    region: str = "EU",
    build_id: int = 17227462,
    platform: str = "Windows",
):
    bucket_id = f"{build_id}:1:{region}:{playlist_name.lower()}"
    params = {
        "partyPlayerIds": client.account_id,
        "bucketId": bucket_id,
        "player.platform": platform,
        "player.subregions": region,
        "player.option.tournamentId": tournament_id,
        "player.option.windowId": event_window_id,
        "player.option.crossplayOptOut": "false",
        "player.option.partyId": party_id,
        "player.option.splitScreen": "false",
        "party.WIN": "true",
        "input.KBM": "true",
        "player.input": "KBM",
        "player.option.microphoneEnabled": "true",
        "player.option.uiLanguage": "en",
    }
    resp = requests.get(
        f"{BASE}/fortnite/api/game/v2/matchmakingservice/ticket/player/{client.account_id}",
        headers=client._auth_header(),
        params=params,
    )
    resp.raise_for_status()
    return resp.json()