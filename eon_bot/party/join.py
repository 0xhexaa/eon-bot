import json
import uuid

import requests

from eon_bot.auth.client import BASE
from eon_bot.meta.meta import PartyMemberMeta


def get_party(client, party_id: str):
    resp = requests.get(
        f"{BASE}/party/api/v1/Fortnite/parties/{party_id}",
        headers=client._auth_header(),
    )
    resp.raise_for_status()
    return resp.json()


def remove_member(client, party_id: str, account_id: str):
    resp = requests.delete(
        f"{BASE}/party/api/v1/Fortnite/parties/{party_id}/members/{account_id}",
        headers=client._auth_header(),
    )
    resp.raise_for_status()
    return resp.status_code


def leave_party(client, party_id: str):
    return remove_member(client, party_id, client.account_id)


def list_members(client, party_id: str):
    party = get_party(client, party_id)
    members = []
    for m in party.get("members", []):
        members.append(
            {
                "account_id": m.get("account_id"),
                "display_name": m.get("meta", {}).get("urn:epic:member:dn_s"),
                "role": m.get("role"),
            }
        )
    return members


def join_party(client, party_id: str, leave_party_id: str | None = None):
    if leave_party_id:
        leave_party(client, leave_party_id)

    conn_id = f"{client.account_id}@prod.ol.epicgames.com/V2:Fortnite:WIN::{uuid.uuid4().hex.upper()}"

    body = {
        "connection": {
            "id": conn_id,
            "meta": {
                "urn:epic:conn:platform_s": "WIN",
                "urn:epic:conn:type_s": "game",
            },
            "yield_leadership": False,
        },
        "meta": {
            "urn:epic:member:dn_s": client.display_name,
            "urn:epic:member:joinrequestusers_j": json.dumps(
                {
                    "users": [
                        {
                            "id": client.account_id,
                            "dn": client.display_name,
                            "plat": "WIN",
                            "data": json.dumps(
                                {"CrossplayPreference_i": "1", "SubGame_u": "1"}
                            ),
                        }
                    ]
                }
            ),
        },
    }

    resp = requests.post(
        f"{BASE}/party/api/v1/Fortnite/parties/{party_id}/members/{client.account_id}/join",
        headers=client._auth_header(),
        json=body,
    )
    resp.raise_for_status()
    result = resp.json()

    meta = PartyMemberMeta(client, party_id)
    meta.mark_voice_unmuted()
    meta.become_visible()
    client.party_meta = meta

    return result