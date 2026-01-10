from urllib.parse import urljoin, urlparse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from generic.items import ArticleItem
from generic.utils import idn2ascii


class WordPressSpider(SitemapSpider):
    """
    A spider that scrapes all the articles with sitemap.xml.
    """

    name = "wordpress"
    custom_settings = {}

    def __init__(self, urls=None, *args, **kwargs):
        super(WordPressSpider, self).__init__(*args, **kwargs)

        self.sitemap_urls = [
            urljoin(idn2ascii(url), "sitemap.xml") for url in urls.split(",")
        ]
        self.allowed_domains = [
            urlparse(url).netloc for url in self.sitemap_urls
        ]
        self.logger.debug(f"urls: {urls}")
        self.logger.debug(f"sitemap_urls: {self.sitemap_urls}")
        self.logger.debug(f"allowed_domains: {self.allowed_domains}")

    def sitemap_filter(self, entries):
        for entry in entries:
            yield entry

    def parse(self, response: Response) -> ArticleItem:
        return ArticleItem.from_response(response)
