from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials
from bayesapiwrapper import BayesApiWrapper
import json


class PostGameDataUpload(object):
    METADATA_TEMPLATE = """{{{{PostgameJsonMetadata
|RiotPlatformId={}
|RiotGameId={}
|RiotHash={}
|GameId={}
|MatchId={}
|N_GameInMatch={}
|OverviewPage={}
|DataPage={}
}}}}"""

    def __init__(self, site: EsportsClient):
        self.site = site
        self.new_games = None
        self.bayes_api_wrapper = BayesApiWrapper()

    def run(self):
        self.query_new_games()
        self.upload_games_data()
        self.report_errors()

    def query_new_games(self):
        self.new_games = self.site.cargo_client.query(
            tables="MatchScheduleGame=MSG, PostgameJsonMetadata=PJM",
            where="MSG.RiotPlatformGameId IS NOT NULL AND MSG.HasRpgidInput = '1' AND (MSG.GameId != PJM.GameId "
                  "OR MSG.MatchId != PJM.MatchId OR MSG.N_GameInMatch != PJM.N_GameInMatch OR "
                  "MSG.OverviewPage != PJM.OverviewPage OR PJM.RiotPlatformGameId IS NULL)",
            join_on="MSG.VersionedRpgid=PJM.VersionedRpgid",
            fields="MSG.RiotPlatformGameId, MSG._pageName=Page, MSG.GameId, MSG.MatchId, MSG.RiotPlatformId, "
                   "MSG.RiotHash, MSG.N_GameInMatch, MSG.OverviewPage, MSG.RiotGameId"
        )

    def upload_games_data(self):
        for game in self.new_games:
            riot_platform_game_id = game["RiotPlatformGameId"].replace("_", " ")
            if not self.site.client.pages[f"V5 data:{riot_platform_game_id}"].exists:
                try:
                    data, timeline = self.bayes_api_wrapper.get_game(game["RiotPlatformGameId"])
                except Exception as e:
                    print(f"Skipping {game['RiotPlatformGameId']}")
                    print(e)
                    continue
                try:
                    self.site.save_title(title=f"V5 data:{riot_platform_game_id}",
                                         text=json.dumps(data))
                except:
                    self.site.log_error_content(f"V5 data:{riot_platform_game_id}",
                                                f"Data or timeline page could not be saved!")
                try:
                    self.site.save_title(title=f"V5 data:{riot_platform_game_id}/Timeline",
                                         text=json.dumps(timeline))
                except:
                    self.site.log_error_content(f"V5 data:{riot_platform_game_id}/Timeline",
                                                f"Data or timeline page could not be saved!")
            metadata_text = self.METADATA_TEMPLATE.format(game["RiotPlatformGameId"].split("_")[0],
                                                          game['RiotPlatformGameId'].split("_")[1],
                                                          "", game["GameId"], game["MatchId"],
                                                          game["N GameInMatch"], game["OverviewPage"], game["Page"])
            try:
                self.site.save_title(title=f"V5 metadata:{riot_platform_game_id}",
                                     text=metadata_text)
            except:
                self.site.log_error_content(f"V5 metadata:{riot_platform_game_id}",
                                            f"Metadata page could not be saved!")

    def report_errors(self):
        self.site.report_all_errors("PostGameData")


if __name__ == "__main__":
    credentials = AuthCredentials(user_file="bot")
    site = EsportsClient("lol", credentials=credentials)
    PostGameDataUpload(site).run()
