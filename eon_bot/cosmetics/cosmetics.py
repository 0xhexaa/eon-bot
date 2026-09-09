import asyncio
import json
import time

import aiohttp

from eon_bot.meta.meta import PartyMemberMeta

COSMETICS_URL = "https://fortnite-api.com/v2/cosmetics/br?responseFlags=1"
REFRESH_SECONDS = 60 * 60


class CosmeticCache:
    def __init__(self):
        self.outfits = []
        self.backpacks = []
        self.pickaxes = []
        self.emotes = []
        self.by_id = {}
        self.last_refresh = 0
        self._lock = asyncio.Lock()

    def _is_c2s8_or_earlier(self, cosmetic: dict) -> bool:
        intro = cosmetic.get("introduction") or {}
        chapter = intro.get("chapter")
        season = intro.get("season")
        if chapter is None or season is None:
            return False
        try:
            chapter_num = int(chapter)
            season_num = int(season)
        except ValueError:
            return False
        return chapter_num < 2 or (chapter_num == 2 and season_num <= 8)

    async def refresh(self, force: bool = False):
        if not force and time.time() - self.last_refresh < REFRESH_SECONDS:
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(COSMETICS_URL) as resp:
                resp.raise_for_status()
                payload = await resp.json()

        outfits, backpacks, pickaxes, emotes, by_id = [], [], [], [], {}
        for cosmetic in payload.get("data", []):
            if not self._is_c2s8_or_earlier(cosmetic):
                continue
            cosmetic_type = (cosmetic.get("type") or {}).get("value")
            by_id[cosmetic["id"]] = cosmetic
            if cosmetic_type == "outfit":
                outfits.append(cosmetic)
            elif cosmetic_type == "backpack":
                backpacks.append(cosmetic)
            elif cosmetic_type == "pickaxe":
                pickaxes.append(cosmetic)
            elif cosmetic_type == "emote":
                emotes.append(cosmetic)

        self.outfits = outfits
        self.backpacks = backpacks
        self.pickaxes = pickaxes
        self.emotes = emotes
        self.by_id = by_id
        self.last_refresh = time.time()

    async def ensure_loaded(self):
        if self.last_refresh:
            return
        async with self._lock:
            if not self.last_refresh:
                await self.refresh()

    def search(self, pool: list, query: str, limit: int = 25) -> list:
        query = query.lower().strip()
        if not query:
            return pool[:limit]
        starts = [c for c in pool if c["name"].lower().startswith(query)]
        contains = [c for c in pool if query in c["name"].lower() and c not in starts]
        return (starts + contains)[:limit]


cache = CosmeticCache()

CHARACTER_PATH = "/Game/Athena/Items/Cosmetics/Characters/{id}.{id}"
BACKPACK_PATH = "/Game/Athena/Items/Cosmetics/Backpacks/{id}.{id}"
PICKAXE_PATH = "/Game/Athena/Items/Cosmetics/Pickaxes/{id}.{id}"
EMTOTE_PATH = "/Game/Athena/Items/Cosmetics/Dances/{id}.{id}"   


def _asset_path(template: str, cosmetic_id: str) -> str:
    return template.format(id=cosmetic_id)


def set_outfit(member_meta: PartyMemberMeta, cosmetic_id: str):
    member_meta.loadout["characterDef"] = _asset_path(CHARACTER_PATH, cosmetic_id)
    member_meta.loadout["characterEKey"] = ""
    member_meta.variants.pop("athenaCharacter", None)
    _patch_loadout(member_meta)


def set_backpack(member_meta: PartyMemberMeta, cosmetic_id: str | None):
    member_meta.loadout["backpackDef"] = _asset_path(BACKPACK_PATH, cosmetic_id) if cosmetic_id else "None"
    member_meta.loadout["backpackEKey"] = ""
    _patch_loadout(member_meta)


def set_pickaxe(member_meta: PartyMemberMeta, cosmetic_id: str):
    member_meta.loadout["pickaxeDef"] = _asset_path(PICKAXE_PATH, cosmetic_id)
    member_meta.loadout["pickaxeEKey"] = ""
    _patch_loadout(member_meta)
    
def set_level(member_meta: PartyMemberMeta, amount: int):
    member_meta.patch({"Default:AthenaBannerInfo_j": json.dumps({"AthenaBannerInfo": {"bannerIconId": "", "bannerColorId": "", "seasonLevel": str(amount)}})})


def set_outfit_style(member_meta: PartyMemberMeta, channel: str, tag: str):
    entry = member_meta.variants.setdefault("athenaCharacter", {"i": []})
    entry["i"] = [c for c in entry["i"] if c.get("c") != channel]
    entry["i"].append({"c": channel, "v": tag, "dE": 0})
    _patch_variants(member_meta)

def set_emote(member_meta: PartyMemberMeta, cosmetic_id: str):
    member_meta.patch({"Default:FrontendEmote_j": json.dumps({"FrontendEmote": {"emoteItemDef": _asset_path(EMTOTE_PATH, cosmetic_id), "emoteEKey": "", "emoteSection": -2}})})


def _patch_loadout(member_meta: PartyMemberMeta):
    member_meta.patch({"Default:AthenaCosmeticLoadout_j": json.dumps({"AthenaCosmeticLoadout": member_meta.loadout})})


def _patch_variants(member_meta: PartyMemberMeta):
    member_meta.patch(
        {
            "Default:AthenaCosmeticLoadoutVariants_j": json.dumps(
                {"AthenaCosmeticLoadoutVariants": {"vL": member_meta.variants, "fT": False}}
            )
        }
    )