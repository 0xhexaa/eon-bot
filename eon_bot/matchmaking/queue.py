import asyncio
import json
import uuid

import websockets


class MatchmakingQueue:
    def __init__(self, ticket: dict):
        self.ticket = ticket
        self.ws = None

    async def connect(self, debug: bool = True):
        service_url = self.ticket["serviceUrl"]
        ticket_type = self.ticket["ticketType"]
        payload = self.ticket["payload"]
        signature = self.ticket["signature"]
        session_token = uuid.uuid4().hex.upper()[:16]

        auth = f"Epic-Signed {ticket_type} {payload} {signature} {session_token}"

        self.ws = await websockets.connect(
            service_url,
            subprotocols=["wss"],
            additional_headers={
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
                "Authorization": auth,
                "Accept-Version": "*",
            },
        )
        self._debug = debug

    async def wait_for_play(self, timeout: float = 300.0) -> dict:
        async def _wait():
            while True:
                raw = await self.ws.recv()
                if getattr(self, "_debug", False):
                    print("<<", raw)
                msg = json.loads(raw)
                if msg.get("name") == "Play":
                    return msg["payload"]

        return await asyncio.wait_for(_wait(), timeout=timeout)

    async def listen(self, on_message):
        async for raw in self.ws:
            on_message(json.loads(raw))