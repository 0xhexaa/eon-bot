import asyncio
import base64
import json
import uuid

import websockets

HOST = "services.eonfn.net"
PORT = 2087
WS_URL = f"wss://{HOST}:{PORT}//"
EPIC_DOMAIN = "prod.ol.epicgames.com"


class EonXMPP:
    def __init__(self, client, platform: str = "WIN"):
        self.client = client
        self.ws = None
        self.platform = platform
        self.resource = f"V2:Fortnite:{platform}::{uuid.uuid4().hex.upper()}"

    async def _open_stream(self):
        await self._send(
            f"<open xmlns='urn:ietf:params:xml:ns:xmpp-framing' "
            f"to='{EPIC_DOMAIN}' version='1.0'/>"
        )
        return await self._recv_until(lambda m: "stream:features" in m)

    async def connect(self, debug: bool = True, retries: int = 3, retry_delay: float = 2.0):
        last_exc = None
        for attempt in range(1, retries + 1):
            self.resource = f"V2:Fortnite:{self.platform}::{uuid.uuid4().hex.upper()}"
            try:
                await self._connect_once(debug)
                return
            except RuntimeError as exc:
                last_exc = exc
                if self.ws is not None:
                    try:
                        await self.ws.close()
                    except Exception:
                        pass
                if attempt < retries:
                    if debug:
                        print(f"connect attempt {attempt} failed ({exc}), retrying")
                    await asyncio.sleep(retry_delay)
        raise last_exc

    async def _connect_once(self, debug: bool):
        self.ws = await websockets.connect(
            WS_URL,
            subprotocols=["xmpp"],
            additional_headers={
                "Origin": f"http://{HOST}",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            },
        )
        self._debug = debug

        features = await self._open_stream()

        if "mechanisms" not in features and "starttls" in features:
            await self._send("<starttls xmlns='urn:ietf:params:xml:ns:xmpp-tls'/>")
            proceed = await self._recv_until(lambda m: "proceed" in m or "failure" in m)
            if "failure" in proceed:
                raise RuntimeError(f"STARTTLS rejected: {proceed}")
            features = await self._open_stream()

        if "mechanisms" not in features:
            raise RuntimeError(f"Server never offered SASL mechanisms: {features}")

        auth_str = f"\0{self.client.account_id}\0{self.client.access_token}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        await self._send(
            f"<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>"
            f"{auth_b64}</auth>"
        )
        result = await self._recv_until(lambda m: "success" in m or "failure" in m)
        if "failure" in result:
            raise RuntimeError(f"XMPP auth failed: {result}")

        await self._open_stream()

        bind_id = uuid.uuid4().hex
        await self._send(
            f"<iq id='{bind_id}' type='set'>"
            f"<bind xmlns='urn:ietf:params:xml:ns:xmpp-bind'>"
            f"<resource>{self.resource}</resource></bind></iq>"
        )
        bind_result = await self._recv_until(
            lambda m: f"id='{bind_id}'" in m or f'id="{bind_id}"' in m
        )
        if "type='error'" in bind_result or 'type="error"' in bind_result:
            raise RuntimeError(f"Resource bind failed: {bind_result}")

        session_id = uuid.uuid4().hex
        await self._send(
            f"<iq id='{session_id}' type='set'>"
            f"<session xmlns='urn:ietf:params:xml:ns:xmpp-session'/></iq>"
        )
        await self._recv_until(
            lambda m: f"id='{session_id}'" in m or f'id="{session_id}"' in m
        )

        await self.send_presence()

        self.client.xmpp = self

    async def send_presence(
        self,
        status_text: str = "Eon Lobby",
        party_size: int = 1,
        is_playing: bool = False,
    ):
        status = {
            "Status": status_text,
            "bIsPlaying": is_playing,
            "bIsJoinable": False,
            "bHasVoiceSupport": False,
            "SessionId": "",
            "ProductName": "Fortnite",
            "Properties": {
                "FortBasicInfo_j": {"homeBaseRating": 0},
                "FortLFG_I": "0",
                "FortPartySize_i": party_size,
                "FortSubGame_i": 1,
                "InUnjoinableMatch_b": False,
                "FortGameplayStats_j": {
                    "state": "",
                    "playlist": "None",
                    "numKills": 0,
                    "bFellToDeath": False,
                },
                "SocialStatus_j": {"attendingSocialEventIds": []},
            },
        }
        await self._send(f"<presence><status>{json.dumps(status)}</status></presence>")

    async def join_party_chat(self, party_id: str):
        nick = f"{self.client.display_name}:{self.client.account_id}:{self.resource}"
        to = f"Party-{party_id}@muc.{EPIC_DOMAIN}/{nick}"
        await self._send(
            f"<presence to='{to}'>"
            f"<x xmlns='http://jabber.org/protocol/muc'><history maxstanzas='50'/></x>"
            f"</presence>"
        )

    async def _send(self, xml: str):
        if getattr(self, "_debug", False):
            print(">>", xml)
        await self.ws.send(xml)

    async def _recv(self) -> str:
        try:
            msg = await self.ws.recv()
        except websockets.exceptions.ConnectionClosed as exc:
            raise RuntimeError(
                f"connection closed by server before a response arrived: {exc}"
            ) from exc
        if getattr(self, "_debug", False):
            print("<<", msg)
        return msg

    async def _recv_until(self, predicate, max_frames: int = 10) -> str:
        for _ in range(max_frames):
            msg = await self._recv()
            if "urn:ietf:params:xml:ns:xmpp-framing'/>" in msg and "<close" in msg:
                raise RuntimeError(f"Server closed the stream unexpectedly: {msg}")
            if predicate(msg):
                return msg
        raise RuntimeError(f"Didn't see an expected stanza within {max_frames} frames")

    async def listen(self, on_stanza):
        async for message in self.ws:
            on_stanza(message)