import base64
import uuid

import requests

HOST = "services.eonfn.net"
BASE = f"https://{HOST}"

BASIC_AUTH = base64.b64encode(
    b"ec684b8c687f479fadea3cb2ad83f5c6:e1f31c211f28413186262d37a13fc84d"
).decode()

USER_AGENT = "Fortnite/++Fortnite+Release-17.50-CL-17388565 Windows/6.2.9200.1.256.64bit"


class EonClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.access_token = None
        self.account_id = None
        self.display_name = None
        self.device_id = uuid.uuid4().hex
        self.xmpp = None
        self.party_id = None

    def _headers(self, auth: str | None = None) -> dict:
        h = {
            "User-Agent": USER_AGENT,
            "X-Epic-Correlation-ID": f"FN-{uuid.uuid4()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if auth:
            h["Authorization"] = auth
        return h

    def login(self):
        requests.post(
            f"{BASE}/account/api/oauth/token",
            headers=self._headers(f"basic {BASIC_AUTH}"),
            data={"grant_type": "client_credentials", "token_type": "eg1"},
        )

        headers = self._headers(f"basic {BASIC_AUTH}")
        headers["X-Epic-Device-ID"] = self.device_id

        resp = requests.post(
            f"{BASE}/account/api/oauth/token",
            headers=headers,
            data={
                "grant_type": "password",
                "username": self.email,
                "password": self.password,
                "token_type": "eg1",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        self.access_token = data["access_token"]
        self.account_id = data["account_id"]
        self.display_name = data.get("displayName")
        return data

    def _auth_header(self) -> dict:
        return {
            "Authorization": f"bearer {self.access_token}",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        }

    def get_account(self, account_id: str | None = None):
        account_id = account_id or self.account_id
        resp = requests.get(
            f"{BASE}/account/api/public/account/{account_id}",
            headers=self._auth_header(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_account_for(self, account_id: str):
        return self.get_account(account_id)

    def query_profile(self, profile_id: str = "athena", account_id: str | None = None):
        account_id = account_id or self.account_id
        resp = requests.post(
            f"{BASE}/fortnite/api/game/v2/profile/{account_id}/client/QueryProfile",
            headers=self._auth_header(),
            params={"profileId": profile_id, "rvn": -1},
            json={},
        )
        resp.raise_for_status()
        return resp.json()

    def get_profile_for(self, account_id: str, profile_id: str = "athena"):
        return self.query_profile(profile_id, account_id)

    def search(self, prefix: str, platform: str = "epic"):
        from eon_bot.friends.search import search_accounts

        return search_accounts(self, prefix, platform)

    def add_friend(self, target_account_id: str):
        from eon_bot.friends.add import add_friend

        return add_friend(self, target_account_id)

    def remove_friend(self, target_account_id: str):
        from eon_bot.friends.remove import remove_friend

        return remove_friend(self, target_account_id)

    def invite(self, username: str):
        from eon_bot.party.invite import send_invite

        matches = self.search(username)
        if not matches:
            raise ValueError(f"no account found matching {username!r}")

        return send_invite(self, matches[0]["accountId"])

    def join(self, username: str, leave_party_id: str | None = None):
        from eon_bot.party.join import join_party

        matches = self.search(username)
        if not matches:
            raise ValueError(f"no account found matching {username!r}")

        target_id = matches[0]["accountId"]
        parties = self.get_user_party(target_id)
        current = parties.get("current") or []
        if not current:
            raise ValueError(f"{username} isn't currently in a party")

        party_id = current[0]["id"]
        result = join_party(self, party_id, leave_party_id)
        self.party_id = party_id
        return result

    def leave(self, party_id: str | None = None):
        from eon_bot.party.join import leave_party

        party_id = party_id or self.party_id
        result = leave_party(self, party_id)
        if party_id == self.party_id:
            self.party_id = None
        return result

    def get_party(self, party_id: str | None = None):
        from eon_bot.party.join import get_party

        return get_party(self, party_id or self.party_id)

    def get_user_party(self, account_id: str):
        from eon_bot.party.lookup import get_user_party

        return get_user_party(self, account_id)

    def get_party_id(self):
        current = self.get_user_party(self.account_id).get("current") or []
        if not current:
            raise RuntimeError("Your account is not currently in a party")
        self.party_id = current[0]["id"]
        return self.party_id

    def list_members(self, party_id: str | None = None):
        from eon_bot.party.join import list_members

        return list_members(self, party_id or self.party_id)

    def get_friends(self):
        from eon_bot.friends.search import get_friends

        return get_friends(self)

    def kick_member(self, target_account_id: str, party_id: str | None = None):
        from eon_bot.party.kick import kick_member

        return kick_member(self, party_id or self.party_id, target_account_id)

    def kick_username(self, username: str, party_id: str | None = None):
        from eon_bot.party.kick import kick_username

        return kick_username(self, username, party_id or self.party_id)

    async def play(
        self,
        playlist_name: str,
        tournament_id: str = "",
        event_window_id: str = "",
        region: str = "EU",
        party_id: str | None = None,
        queue_timeout: float = 300.0,
    ):
        from eon_bot.matchmaking.flow import start_matchmaking

        party_id = party_id or self.party_id
        if not party_id:
            raise RuntimeError(
                "no party_id given and client isn't tracking a current party"
            )

        return await start_matchmaking(
            self,
            party_id,
            playlist_name,
            tournament_id,
            event_window_id,
            region,
            queue_timeout=queue_timeout,
        )

    def spoof_invite(self, sender: str, target: str, amount: int = 1):
        from eon_bot.troll.friend import spoof_invite
                
        return spoof_invite(self, sender, target, amount)

    def kick(self, username: str, party_id: str | None = None):
        from eon_bot.party.kick import kick_username
    
        return kick_username(self, username, party_id)

    def spam_friend(self, target_account_id: str):
        from eon_bot.troll.friend import spam_friend

        return spam_friend(self, target_account_id)

    async def connect(self, platform: str = "WIN"):
        from eon_bot.xmpp.party import EonXMPP

        self.xmpp = EonXMPP(self, platform)
        await self.xmpp.connect()
        return self.xmpp