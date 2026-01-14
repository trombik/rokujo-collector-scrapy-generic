import os
import re
from urllib.parse import urlparse

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from generic.items import ArticleItem
from generic.utils import idn2ascii


class DirectorySpider(scrapy.spiders.CrawlSpider):
    """
    A spider that crawls pages under a directory. The directory is the base
    directory of the last component of the given URL.

    When the URL is "http://example.org/index.html", it crawls all the URLs.

    When the URL is "http://example.org/foo/index.html", it crawls pages under
    `/foo/`.

    When the URL is "http://example.org/foo/bar/index.html", it crawls pages
    under `/foo/bar/` but not "/foo/bar.html`.

    Examples:

    When start_urls is ["http://example.org/a/b/c.html"]:

    - it crawls `/a/b/index.html`.
    - it crawls `/a/b/foo.html`.
    - it crawls `/a/b/c/bar.html`.
    - it does not crawl "/index.html"
    - it does not crawl "/a/index.html"

    """

    name = "directory"
    custom_settings = {
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_EXPIRATION_SECS": 3600 * 24,
        "HTTPCACHE_DIR": "httpcache",
    }

    def parse_body(self, response):
        yield ArticleItem.from_response(response)

    def __init__(self, url=None, *args, **kwargs):
        self.start_urls = [idn2ascii(url)]
        self.allowed_domains = [urlparse(url).netloc]
        self.logger.debug(f"url: {url}")
        self.logger.debug(f"start_urls: {self.start_urls}")
        self.logger.debug(f"allowed_domains: {self.allowed_domains}")

        parsed = urlparse(url)
        path = (
            parsed.path
            if parsed.path.endswith("/")
            else os.path.dirname(parsed.path)
        )
        if not path.endswith("/"):
            path += "/"

        regex = rf"^https?://{re.escape(parsed.netloc)}{re.escape(path)}.*"
        self.rules = (
            Rule(
                LinkExtractor(allow=[regex], deny=(r"\.(pdf|docx)")),
                callback="parse_body",
                follow=True,
            ),
            Rule(
                LinkExtractor(deny=(r".*")),
            ),
        )
        super(DirectorySpider, self).__init__(*args, **kwargs)
        self._compile_rules()
