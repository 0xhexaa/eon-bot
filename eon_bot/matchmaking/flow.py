from eon_bot.matchmaking.party_state import set_matchmaking, set_preloading
from eon_bot.matchmaking.queue import MatchmakingQueue
from eon_bot.matchmaking.session import get_session, get_session_key, join_session
from eon_bot.matchmaking.ticket import get_ticket


async def start_matchmaking(
    client,
    party_id: str,
    playlist_name: str,
    tournament_id: str = "",
    event_window_id: str = "",
    region: str = "EU",
    build_id: int = 17227462,
    hotfix_version: int = 1,
    queue_timeout: float = 300.0,
):
    set_preloading(client, party_id, playlist_name, tournament_id, event_window_id, region)

    ticket = get_ticket(client, party_id, playlist_name, tournament_id, event_window_id, region)

    set_matchmaking(
        client,
        party_id,
        playlist_name,
        tournament_id,
        event_window_id,
        region,
        build_id,
        hotfix_version,
    )

    queue = MatchmakingQueue(ticket)
    await queue.connect()
    play = await queue.wait_for_play(queue_timeout)

    session_id = play["sessionId"]
    server = get_session(client, session_id)
    key = get_session_key(client, session_id)["key"]
    join_session(client, session_id, key)

    return {
        "match_id": play.get("matchId"),
        "session_id": session_id,
        "server_address": server.get("serverAddress"),
        "server_port": server.get("serverPort"),
    }