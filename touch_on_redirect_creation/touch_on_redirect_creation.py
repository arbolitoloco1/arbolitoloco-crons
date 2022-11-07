from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials


class TouchOnRedirectCreation(object):
    def __init__(self, site: EsportsClient):
        self.site = site
        self.new_redirects = []
        self.touched_targets = []

    def run(self):
        self.get_recent_changes()
        self.touch_targets()

    def get_recent_changes(self):
        recent_changes = self.site.recentchanges_by_interval(30, prop="title|tags")
        for change in recent_changes:
            if "mw-new-redirect" in change["tags"] or "mw-changed-redirect-target" in change["tags"]:
                if change["title"] not in self.new_redirects:
                    self.new_redirects.append(change["title"])

    def touch_targets(self):
        for title in self.new_redirects:
            target_title = self.site.cache.get_target(title)
            if target_title in self.touched_targets:
                continue
            target_page = self.site.client.pages[target_title]
            if not target_page.exists:
                continue
            target_page_text = target_page.text()
            self.site.save_title(title=target_title, text=target_page_text)
            self.site.purge_title(title=target_title)
            self.touched_targets.append(target_title)


if __name__ == "__main__":
    credentials = AuthCredentials(user_file="me")
    lol_site = EsportsClient("lol", credentials=credentials)
    TouchOnRedirectCreation(lol_site).run()
