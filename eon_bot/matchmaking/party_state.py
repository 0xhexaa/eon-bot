import json

import requests

from eon_bot.auth.client import BASE
from eon_bot.party.join import get_party


def set_preloading(
    client,
    party_id: str,
    playlist_name: str,
    tournament_id: str = "",
    event_window_id: str = "",
    region: str = "EU",
):
    revision = get_party(client, party_id)["revision"]
    body = {
        "config": {
            "discoverability": "INVITED_ONLY",
            "joinability": "INVITE_AND_FORMER",
        },
        "meta": {
            "delete": [],
            "update": {
                "urn:epic:cfg:not-accepting-members-reason_i": "2",
                "Default:PlaylistData_j": json.dumps(
                    {
                        "PlaylistData": {
                            "playlistName": playlist_name,
                            "tournamentId": tournament_id,
                            "eventWindowId": event_window_id,
                            "regionId": region,
                            "mnemonic": "",
                        }
                    }
                ),
                "Default:PartyState_s": "BattleRoyalePreloading",
            },
        },
        "revision": revision,
    }
    resp = requests.patch(
        f"{BASE}/party/api/v1/Fortnite/parties/{party_id}",
        headers=client._auth_header(),
        json=body,
    )
    return resp.status_code


def set_matchmaking(
    client,
    party_id: str,
    playlist_name: str,
    tournament_id: str = "",
    event_window_id: str = "",
    region: str = "EU",
    build_id: int = 17227462,
    hotfix_version: int = 1,
):
    revision = get_party(client, party_id)["revision"]
    body = {
        "config": {
            "discoverability": "INVITED_ONLY",
            "joinability": "INVITE_AND_FORMER",
        },
        "meta": {
            "delete": [],
            "update": {
                "urn:epic:cfg:not-accepting-members-reason_i": "7",
                "Default:PartyState_s": "BattleRoyaleMatchmaking",
                "Default:PartyMatchmakingInfo_j": json.dumps(
                    {
                        "PartyMatchmakingInfo": {
                            "buildId": build_id,
                            "hotfixVersion": hotfix_version,
                            "regionId": region,
                            "playlistName": playlist_name,
                            "playlistRevision": 1,
                            "tournamentId": tournament_id,
                            "eventWindowId": event_window_id,
                            "linkCode": "",
                        }
                    }
                ),
            },
        },
        "revision": revision,
    }
    resp = requests.patch(
        f"{BASE}/party/api/v1/Fortnite/parties/{party_id}",
        headers=client._auth_header(),
        json=body,
    )
    return resp.status_code