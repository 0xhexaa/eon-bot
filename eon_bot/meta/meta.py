import json

import requests

from eon_bot.auth.client import BASE


class PartyMemberMeta:
    def __init__(self, client, party_id: str):
        self.client = client
        self.party_id = party_id
        self.revision = 0
        self.loadout = {}
        self.variants = {}

    @property
    def _url(self):
        return f"{BASE}/party/api/v1/Fortnite/parties/{self.party_id}/members/{self.client.account_id}/meta"

    def patch(self, update: dict, delete: list = None):
        body = {"delete": delete or [], "revision": self.revision, "update": update}
        resp = requests.patch(self._url, headers=self.client._auth_header(), json=body)
        resp.raise_for_status()
        self.revision += 1
        return resp

    def mark_voice_unmuted(self):
        self.patch({"internal:voicechatmuted_b": "false"})

    def set_voice_status(self, status: str = "PartyVoice"):
        self.patch({"Default:VoiceChatStatus_s": status})

    def become_visible(
        self,
        character_def: str = "/Game/Athena/Items/Cosmetics/Characters/CID_556_Athena_Commando_F_RebirthDefaultA.CID_556_Athena_Commando_F_RebirthDefaultA",
        backpack_def: str = "None",
        pickaxe_def: str = "/Game/Athena/Items/Cosmetics/Pickaxes/DefaultPickaxe.DefaultPickaxe",
        contrail_def: str = "/Game/Athena/Items/Cosmetics/Contrails/DefaultContrail.DefaultContrail",
    ):
        self.loadout = {
            "characterDef": character_def,
            "characterEKey": "",
            "backpackDef": backpack_def,
            "backpackEKey": "",
            "pickaxeDef": pickaxe_def,
            "pickaxeEKey": "",
            "contrailDef": contrail_def,
            "contrailEKey": "",
            "scratchpad": [],
        }
        platform_data = {
            "PlatformData": {
                "platform": {
                    "platformDescription": {
                        "name": "WIN",
                        "platformType": "DESKTOP",
                        "onlineSubsystem": "None",
                        "sessionType": "",
                        "externalAccountType": "",
                        "crossplayPool": "DESKTOP",
                    }
                },
                "uniqueId": "INVALID",
                "sessionId": "",
            }
        }
        update = {
            "Default:Location_s": "PreLobby",
            "Default:CampaignHero_j": json.dumps({"CampaignHero": {"heroItemInstanceId": "", "heroType": ""}}),
            "Default:CampaignInfo_j": json.dumps(
                {"CampaignInfo": {"matchmakingLevel": 0, "zoneInstanceId": "", "homeBaseVersion": 1}}
            ),
            "Default:FrontendEmote_j": json.dumps(
                {"FrontendEmote": {"emoteItemDef": "None", "emoteEKey": "", "emoteSection": -1}}
            ),
            "Default:NumAthenaPlayersLeft_U": "0",
            "Default:SpectateAPartyMemberAvailable_b": "false",
            "Default:UtcTimeStartedMatchAthena_s": "0001-01-01T00:00:00.000Z",
            "Default:LobbyState_j": json.dumps(
                {
                    "LobbyState": {
                        "inGameReadyCheckStatus": "None",
                        "gameReadiness": "NotReady",
                        "readyInputType": "Count",
                        "currentInputType": "MouseAndKeyboard",
                        "hiddenMatchmakingDelayMax": 0,
                        "hasPreloadedAthena": False,
                    }
                }
            ),
            "Default:AssistedChallengeInfo_j": json.dumps(
                {"AssistedChallengeInfo": {"questItemDef": "None", "objectivesCompleted": 0}}
            ),
            "Default:FeatDefinition_s": "None",
            "Default:MemberSquadAssignmentRequest_j": json.dumps(
                {
                    "MemberSquadAssignmentRequest": {
                        "startingAbsoluteIdx": -1,
                        "targetAbsoluteIdx": -1,
                        "swapTargetMemberId": "INVALID",
                        "version": 0,
                    }
                }
            ),
            "Default:VoiceChatStatus_s": "Enabled",
            "Default:SidekickStatus_s": "None",
            "Default:FrontEndMapMarker_j": json.dumps(
                {"FrontEndMapMarker": {"markerLocation": {"x": 0, "y": 0}, "bIsSet": False}}
            ),
            "Default:AthenaCosmeticLoadout_j": json.dumps({"AthenaCosmeticLoadout": self.loadout}),
            "Default:AthenaCosmeticLoadoutVariants_j": json.dumps(
                {"AthenaCosmeticLoadoutVariants": {"vL": self.variants, "fT": False}}
            ),
            "Default:ArbitraryCustomDataStore_j": json.dumps({"ArbitraryCustomDataStore": []}),
            "Default:AthenaBannerInfo_j": json.dumps(
                {"AthenaBannerInfo": {"bannerIconId": "", "bannerColorId": "", "seasonLevel": 1}}
            ),
            "Default:BattlePassInfo_j": json.dumps(
                {
                    "BattlePassInfo": {
                        "bHasPurchasedPass": False,
                        "passLevel": 1,
                        "selfBoostXp": 0,
                        "friendBoostXp": 0,
                    }
                }
            ),
            "Default:PlatformData_j": json.dumps(platform_data),
            "Default:CrossplayPreference_s": "OptedIn",
        }
        self.patch(update)