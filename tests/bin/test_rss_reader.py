import pytest

from bin.rss_reader import group_urls_to_commands


@pytest.fixture
def config():
    return {
        "rules": [
            {
                "name": "Yahoo",
                "url_pattern": r"news\.yahoo\.co\.jp",
                "spider_name": "read-more",
                "args": ["site=yahoo"]
            },
            {
                "name": "BBC",
                "url_pattern": r"bbc\.com",
                "spider_name": "generic",
                "args": ["site=bbc"]
            }
        ]
    }


def test_multiple_urls_grouping(config):
    unread_urls = [
        "https://news.yahoo.co.jp/a",
        "https://news.yahoo.co.jp/b",
        "https://www.bbc.com/c",
    ]

    cmds = group_urls_to_commands(unread_urls, config)

    assert len(cmds) == 2

    yahoo_cmd = next(c for c in cmds if "site=yahoo" in c)
    assert "urls=https://news.yahoo.co.jp/a,https://news.yahoo.co.jp/b" in yahoo_cmd # noqa E501
    assert yahoo_cmd[0:3] == ["scrapy", "crawl", "read-more"]

    bbc_cmd = next(c for c in cmds if "site=bbc" in c)
    assert "urls=https://www.bbc.com/c" in bbc_cmd
    assert bbc_cmd[0:3] == ["scrapy", "crawl", "generic"]


def test_empty_input(config):
    assert group_urls_to_commands([], config) == []


def test_no_matching_urls(config):
    urls = ["https://google.com", "https://github.com"]
    assert group_urls_to_commands(urls, config) == []
