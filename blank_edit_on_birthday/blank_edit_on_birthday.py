from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials
from datetime import datetime
import pytz


def blank_edit_players(site, players):
    for player in players:
        page = site.client.pages[player["Page"]]
        if page.exists:
            site.save(page, page.text())
            site.purge(page)


def query_players(site, date):
    return site.cargo_client.query(
        tables="Players",
        fields="_pageName=Page",
        where=f"Birthdate LIKE \"%{date}\""
    )


def get_current_date():
    pst_object = pytz.timezone("PST8PDT")
    return datetime.now(pst_object).strftime("-%m-%d")


def run(site: EsportsClient):
    date = get_current_date()
    players = query_players(site, date)
    blank_edit_players(site, players)


if __name__ == "__main__":
    credentials = AuthCredentials(user_file="me")
    site = EsportsClient("lol", credentials=credentials)
    run(site)
