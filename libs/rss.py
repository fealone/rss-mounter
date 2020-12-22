from typing import Dict, List, Optional

import feedparser

import yaml


class RSS(object):

    def __init__(self, rss_config_path: str) -> None:
        self.rss_config_path = rss_config_path
        self.rss_config = yaml.load(open(self.rss_config_path), Loader=yaml.BaseLoader)
        self.rss_feeds: Dict[str, feedparser.FeedParserDict] = {}
        self.load_feeds()

    def reload(self) -> None:
        self.rss_config = yaml.load(open(self.rss_config), Loader=yaml.BaseLoader)
        self.load_feeds()

    def load_feeds(self) -> None:
        self.rss_feeds = {
                root_name: self.get_feeds(url)
                for root_name, url in self.rss_config.items()}

    def get_feeds(self, url: str) -> List[feedparser.FeedParserDict]:
        feed = feedparser.parse(url)
        return feed.entries

    def get_content(self, feed: feedparser.FeedParserDict) -> Optional[str]:
        if feed:
            return feed.content[0].value
        return None

    def get_root(self) -> List[str]:
        return list(self.rss_config.keys())

    def get_titles(self, root_name: str) -> List[str]:
        return [feed.title for feed in self.rss_feeds[root_name]]


if __name__ == "__main__":
    rss = RSS("rss_config.yaml")
    print(rss.get_root())
    print(rss.get_titles(rss.get_root()[0]))
