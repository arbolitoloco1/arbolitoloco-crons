import requests
from bs4 import BeautifulSoup

from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials

from datetime import datetime
from datetime import timedelta
import pytz
import time

import json
import get_roster_differences


class LVPRostersParser(object):
    LOLESPORTS_ENDPOINT = "https://esports-api.lolesports.com/persisted/gw/getTeams?hl=es-MX&id={}"
    LOLESPORTS_HEADERS = {"x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"}

    def __init__(self, site, pst_timezone):
        self.site = site
        self.pst_timezone = pst_timezone
        self.date = str
        self.errors = []
        self.output = "{{TOCRight}}\n\n"
        self.saved_rosters = None
        self.current_rosters = {}
        self.teams = None
        self.roster_differences = ""

    def run(self):
        self.get_date()
        self.get_saved_rosters_and_teams()
        self.parse_rosters()
        self.get_roster_differences()
        self.save_to_wiki()

    def get_date(self):
        datetime_object = datetime.now(self.pst_timezone)
        year = str(datetime_object.year).zfill(4)
        month = str(datetime_object.month).zfill(2)
        day = str(datetime_object.day).zfill(2)

        self.date = f"{year}-{month}-{day}"

        yesterday_object = datetime_object - timedelta(days=1)
        yesterday = yesterday_object.strftime("%Y-%m-%d")

        self.output += f"[[Data:News/{yesterday}|News Page to Edit]]\n\n"

    def get_saved_rosters_and_teams(self):
        with open(file="saved_rosters.json", mode="r+", encoding="utf8") as f:
            self.saved_rosters = json.load(f)
        with open(file="teams.json", mode="r+", encoding="utf8") as f:
            self.teams = json.load(f)

    def add_player_to_team(self, player, team):
        if team not in self.current_rosters.keys():
            self.current_rosters[team] = {"players": {}}
        self.current_rosters[team]["players"][player["nick"]] = player

    def parse_lvp(self, web):
        languages_dict = {"ligamaster": "/ar", "ligadehonor": "/cl", "golden": "/co", "volcano": "/ec", "stars": "/pe",
                          "ddh": "/mx", "elements": "", "superliga": ""}

        self.output += f"== {web} ==\n\n"
        language = languages_dict[web]
        for team in self.teams[web]:
            try:
                self.output += f"=== {team} ===\n\nhttps://{web}.lvp.global{language}/equipo/{team}/\n\n"

                html = requests.get(f"https://{web}.lvp.global{language}/equipo/{team}/")
                html = html.text
                parsed_html = BeautifulSoup(html, "html.parser")
                page = parsed_html.find("div", "squad-container-outer")

                if not page:
                    self.output += "The team doesn't have any players!\n\n"
                    if team not in self.current_rosters.keys():
                        self.current_rosters[team] = {"players": {}}
                    continue

                squad = page.find("div", "players-container-inner")
                players = squad.find_all("a", "player-card")

                if not players:
                    raise Exception("No players could be found")

                i = 0
                for player in players:
                    player_info = player.find("div", "upper-player-info-container")
                    player_nick = player_info.find("span", "player-nickname").text
                    player_position = player_info.find("span", "player-position").text

                    if not player_nick:
                        raise Exception(f"Information for a player could not be found")

                    i += 1

                    self.add_player_to_team({"nick": player_nick, "position": player_position, "order": i}, team)

                    self.output += f"{player_nick} - {player_position}\n\n"

                self.output += "\n"
            except Exception as e:
                self.output += f"ERROR: {e}\n\n"
                with open(file="errores.txt", mode="a+", encoding="utf8") as f:
                    f.write(f"{e}\n")
                self.errors.append(f"ERROR: {web} - {team} - {e}\n\n")
                continue

    def parse_lolesports(self):
        try:
            self.output += f"== LLA ==\n\n"
            try:
                for team in self.teams["lolesports"]:
                    response = requests.get(self.LOLESPORTS_ENDPOINT.format(team), headers=self.LOLESPORTS_HEADERS)
                    if not response:
                        raise Exception("Response from LoLEsports API is empty")
                    response = response.json()
                    players = response["data"]["teams"][0]["players"]
                    if not players:
                        raise Exception("No players could be found")
                    self.output += f"=== {team} ===\n\n"
                    for player in players:
                        player_nick = player["summonerName"]
                        player_position = player["role"]
                        self.output += f"{player_nick} - {player_position}\n\n"
                    self.output += "\n"
            except Exception as e:
                self.output += f"ERROR: {e}\n\n"
                with open(file="errores.txt", mode="a+", encoding="utf8") as f:
                    f.write(f"{e}\n")
                self.errors.append(f"ERROR: lolesports - {e}\n\n")
        except Exception as e:
            self.output += f"ERROR: {e}\n\n"
            with open(file="errores.txt", mode="a+", encoding="utf8") as f:
                f.write(f"{e}\n")
                self.errors.append(f"ERROR: lolesports - {e}\n\n")

    def parse_rosters(self):
        for web in self.teams.keys():
            if web != "lolesports":
                self.parse_lvp(web)
            else:
                self.parse_lolesports()

    def get_roster_differences(self):
        with open(file="saved_rosters.json", mode="w+", encoding="utf8") as f:
            json.dump(self.current_rosters, f, ensure_ascii=False, indent=4)

        if self.saved_rosters != self.current_rosters:
            self.roster_differences = get_roster_differences.run(self.saved_rosters, self.current_rosters)

    def save_to_wiki(self):
        while True:
            try:
                self.site.save_title(title=f"User:Arbolitoloco/RostersLVP", text=str(self.output),
                                     summary=f"{datetime.now(self.pst_timezone)}")
                self.site.save_title(title=f"User:Arbolitoloco/RostersLVP/{self.date}", text=str(self.output),
                                     summary=f"{datetime.now(self.pst_timezone)}")
                if self.roster_differences:
                    self.site.save_title(title=f"User:Arbolitoloco/RostersLVP/{self.date}/Cambios",
                                         text=str(self.roster_differences),
                                         summary=f"{datetime.now(self.pst_timezone)}")
                if self.errors:
                    self.site.save_title(title=f"User:Arbolitoloco/RostersLVP/Errors", text=str("".join(self.errors)),
                                         summary=f"{datetime.now(self.pst_timezone)}")
                break
            except Exception as e:
                with open(file="errores.txt", mode="a+", encoding="utf8") as f:
                    f.write(f"{e}\n")
                time.sleep(120)
                continue


if __name__ == "__main__":
    credentials = AuthCredentials(user_file="bot")
    site = EsportsClient("lol", credentials=credentials)
    pst_timezone = pytz.timezone('PST8PDT')
    LVPRostersParser(site, pst_timezone).run()
