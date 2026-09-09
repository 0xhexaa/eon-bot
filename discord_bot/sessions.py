_sessions = {}


def set_session(discord_id: int, client):
    _sessions[discord_id] = client


def get_session(discord_id: int):
    return _sessions.get(discord_id)


def clear_session(discord_id: int):
    _sessions.pop(discord_id, None)