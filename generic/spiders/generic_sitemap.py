from typing import Type
from urllib.parse import urljoin, urlparse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from generic.mixins.read_more import ReadMoreMixin, ReadMoreMixinConfig
from generic.spiders.base import GenericSpider
from generic.utils import idn2ascii


class GenericSitemapSpiderConfig(ReadMoreMixinConfig):
    pass


class GenericSitemapSpider(
    SitemapSpider,
    GenericSpider[GenericSitemapSpiderConfig],
    ReadMoreMixin,
):
    """
    A spider that scrapes all the articles within a sitemap.xml. The
    sitemap.xml may contain another sitemap.xml (nested sitemap.xml).

    The spider uses ReadMoreMixin and automatically scrapes articles of
    multiple pages (and implements other goodies like scraping sources).
    """

    name = "sitemap"
    custom_settings = {}

    @classmethod
    def get_config_class(cls) -> Type[GenericSitemapSpiderConfig]:
        """
        Returns the config class for this spider.
        """
        return GenericSitemapSpiderConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sitemap_urls = [
            urljoin(idn2ascii(url), "sitemap.xml") for url in self.args.urls
        ]
        self.allowed_domains = [
            urlparse(url).netloc for url in self.sitemap_urls
        ]
        self.logger.debug(f"urls: {self.args.urls}")
        self.logger.debug(f"sitemap_urls: {self.sitemap_urls}")
        self.logger.debug(f"allowed_domains: {self.allowed_domains}")

    def sitemap_filter(self, entries):
        for entry in entries:
            yield entry

    def parse(self, response: Response):
        yield from self.parse_summary_page(response)
