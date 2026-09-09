import json
import pathlib

STORAGE_PATH = pathlib.Path(__file__).parent / "accounts.json"


def _load():
    if STORAGE_PATH.exists():
        return json.loads(STORAGE_PATH.read_text())
    return {}


def _save(data):
    STORAGE_PATH.write_text(json.dumps(data, indent=2))


def save_account(discord_id: int, label: str, email: str, password: str):
    data = _load()
    accounts = [a for a in data.get(str(discord_id), []) if a["label"] != label]
    accounts.append({"label": label, "email": email, "password": password})
    data[str(discord_id)] = accounts
    _save(data)


def get_accounts(discord_id: int):
    return _load().get(str(discord_id), [])


def get_account(discord_id: int, label: str):
    for account in get_accounts(discord_id):
        if account["label"] == label:
            return account
    return None