from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials
from bayesapiwrapper import BayesApiWrapper, NotFoundError
import json
from riotwatcher import LolWatcher, ApiError
import os
from dotenv import load_dotenv


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
    RIOT_LIVE_PLATFORMS = ["BR1", "EUN1", "EUW1", "JP1", "KR", "LA1", "LA2", "NA1", "OC1", "TR1", "RU"]

    def __init__(self, site: EsportsClient):
        self.site = site
        self.changed_games = None
        self.bayes_api_wrapper = BayesApiWrapper()
        self.lol_watcher = None

    def run(self):
        self.load_lol_watcher()
        self.query_changed_games()
        self.process_changed_games()
        self.report_errors()

    def load_lol_watcher(self):
        load_dotenv()
        self.lol_watcher = LolWatcher(os.getenv('RIOT_API_KEY'))

    def query_changed_games(self):
        self.changed_games = self.site.cargo_client.query(
            tables="MatchScheduleGame=MSG, PostgameJsonMetadata=PJM",
            where="MSG.RiotPlatformGameId IS NOT NULL AND MSG.HasRpgidInput = '1' AND (MSG.GameId != PJM.GameId "
                  "OR MSG.MatchId != PJM.MatchId OR MSG.N_GameInMatch != PJM.N_GameInMatch OR "
                  "MSG.OverviewPage != PJM.OverviewPage OR PJM.RiotPlatformGameId IS NULL)",
            join_on="MSG.VersionedRpgid=PJM.VersionedRpgid",
            fields="MSG.RiotPlatformGameId, MSG._pageName=Page, MSG.GameId, MSG.MatchId, MSG.RiotPlatformId, "
                   "MSG.RiotHash, MSG.N_GameInMatch, MSG.OverviewPage, MSG.RiotGameId"
        )

    def get_metadata_text(self, game):
        return self.METADATA_TEMPLATE.format(game["RiotPlatformGameId"].split("_")[0],
                                             game['RiotPlatformGameId'].split("_")[1], "", game["GameId"],
                                             game["MatchId"], game["N GameInMatch"], game["OverviewPage"], game["Page"])

    def get_game_data(self, platform_game_id):
        try:
            data, timeline = self.bayes_api_wrapper.get_game(platform_game_id)
        except NotFoundError:
            try:
                platform = platform_game_id.split("_")[0]
                if platform not in self.RIOT_LIVE_PLATFORMS:
                    return None, None
                data = self.lol_watcher.match.by_id(platform, platform_game_id)
                timeline = self.lol_watcher.match.timeline_by_match(platform, platform_game_id)
            except ApiError:
                return None, None
        return json.dumps(data), json.dumps(timeline)

    def process_changed_games(self):
        for game in self.changed_games:
            platform_game_id = game["RiotPlatformGameId"]
            spaced_platform_game_id = platform_game_id.replace("_", " ")
            if not self.site.client.pages[f"V5 data:{spaced_platform_game_id}"].exists:
                try:
                    data, timeline = self.get_game_data(platform_game_id)
                except Exception as e:
                    self.site.log_error_script(error=e)
                    continue
                if data is None and timeline is None:
                    continue
                self.upload_game_data(spaced_platform_game_id, data, timeline)
            metadata_text = self.get_metadata_text(game)
            self.upload_game_metadata(spaced_platform_game_id, metadata_text)
            self.purge_overview_page(game["OverviewPage"])

    def upload_game_data(self, platform_game_id, data, timeline):
        try:
            self.site.save_title(title=f"V5 data:{platform_game_id}",
                                 text=data)
        except Exception as e:
            self.site.log_error_content(f"V5 data:{platform_game_id}",
                                        f"Data or timeline page could not be saved! {e}")

        try:
            self.site.save_title(title=f"V5 data:{platform_game_id}/Timeline",
                                 text=timeline)
        except Exception as e:
            self.site.log_error_content(f"V5 data:{platform_game_id}/Timeline",
                                        f"Data or timeline page could not be saved! {e}")

    def purge_overview_page(self, page_title):
        page = self.site.client.pages[page_title]
        if page.exists:
            page.purge()

    def upload_game_metadata(self, platform_game_id, metadata_text):
        try:
            self.site.save_title(title=f"V5 metadata:{platform_game_id}",
                                 text=metadata_text)
        except Exception as e:
            self.site.log_error_content(f"V5 metadata:{platform_game_id}",
                                        f"Metadata page could not be saved! {e}")

    def report_errors(self):
        self.site.report_all_errors("PostGameData")


if __name__ == "__main__":
    credentials = AuthCredentials(user_file="bot")
    lol_site = EsportsClient("lol", credentials=credentials)
    PostGameDataUpload(lol_site).run()
