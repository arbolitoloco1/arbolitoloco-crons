from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials
from datetime import datetime
import pytz
import time

credentials = AuthCredentials(user_file="bot")
site = EsportsClient("lol", credentials=credentials)

time.sleep(10)

PST = pytz.timezone("PST8PDT")

months = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

current_month = months.get(datetime.now(PST).month)
current_year = datetime.now(PST).year

if not current_month:
    with open(file="errors.txt", mode="a+", encoding="utf8") as f:
        f.write(f"Month {datetime.now(PST).month} could not be found!\n")
        exit()

page = site.client.pages["Leaguepedia:News"]
text = f"#redirect [[Project:News/{current_year}/{current_month}]]"

if page.text() != str(text):
    if page.exists:
        page.edit(str(text), "Automatically changing month and year")
        with open(file="success.txt", mode="a+", encoding="utf8") as f:
            f.write(f"Success at {datetime.now()}! - Text = {text}\n")
elif not page.exists:
    with open(file="errors.txt", mode="a+", encoding="utf8") as f:
        f.write(f"Something went wrong - Page exists? {page.exists}\n")
else:
    print("Error editing the page!")
    with open(file="errors.txt", mode="a+", encoding="utf8") as f:
        f.write(f"Tried to edit page but text is the same!\n")
