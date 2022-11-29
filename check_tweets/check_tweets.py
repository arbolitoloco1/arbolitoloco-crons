import os
import re
import time
from datetime import date, timedelta

import tweepy
from tweepy import TooManyRequests

from mwrogue.esports_client import AuthCredentials
from mwrogue.esports_client import EsportsClient

check_from_date = date.today() - timedelta(days=7)

TWEET_NOT_FOUND_ERROR = "Not Found Error"


def main():
    twitter_client = tweepy.Client(os.environ.get('TWITTER_BEARER_TOKEN'))

    credentials = AuthCredentials(user_file="me")
    site = EsportsClient("lol", credentials=credentials)

    response = site.cargo_client.query(
        tables="NewsItems=NI",
        fields="NI.Source, NI._pageName=pageName, NI.N_LineInDate",
        where=f'NI.Source IS NOT NULL AND NI.Date_Sort >= "{check_from_date}"',
        order_by="NI.Date_Sort DESC"
    )

    for item in response:
        source_list = item["Source"].split(":::")
        data_page = item["pageName"]
        line_in_date = item["N LineInDate"]
        for source_string in source_list:
            if not source_string:
                continue
            source = source_string.split(";;;")
            link = source[0]
            if source[2] != "twitter.com":
                continue
            link_re_match = re.search(r"status/([0-9]+)", link)
            if not link_re_match:
                site.log_error_content("Can't get tweet id", text=f"Link: {link}")
                continue
            tweet_id = link_re_match[1]
            try:
                r = twitter_client.get_tweet(tweet_id, user_auth=False)
            except TooManyRequests:
                time.sleep(60 * 15)
                r = twitter_client.get_tweet(tweet_id, user_auth=False)

            if not r.errors:
                continue
            if r.errors[0]["title"] == TWEET_NOT_FOUND_ERROR:
                site.log_error_content(f"{data_page}",
                                       text=f"Tweet not found! Link: {link} - Line {line_in_date}")
            else:
                site.log_error_content("Failure trying to get tweet",
                                       text="Other error! Link: {}, Status Id: {}, Error title: {}".format(
                                           str(link), str(tweet_id), str(r.errors[0]["title"])))

    site.report_all_errors("Deleted Tweets")


if __name__ == '__main__':
    main()
