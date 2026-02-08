import re
from typing import Type
from urllib.parse import urljoin, urlparse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from generic.items import ArticleItem
from generic.spiders.base import GenericSpider, GenericSpiderConfig
from generic.utils import idn2ascii


class GenericSitemapSpiderConfig(GenericSpiderConfig):
    sitemap_type: str = "all"
    """
    The option rejects certain URLs to sitemap XML files, such as archive,
    author, etc.

    "all" rejects nothing. This is the default.

    "wordpress" rejects certain known URLs which point to index pages of tags,
    authors, and taxonomy.
    """


class GenericSitemapSpider(
    SitemapSpider,
    GenericSpider[GenericSitemapSpiderConfig]
):
    """
    A spider that scrapes all the articles within a sitemap.xml. The
    sitemap.xml may contain another sitemap.xml (nested sitemap.xml).
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
        match self.args.sitemap_type:
            case "wordpress":
                self.logger.debug("sitemap_filter: wordpress")
                yield from self.sitemap_filter_wordpress(entries)
            case "all":
                self.logger.debug("sitemap_filter: all")
                yield from self.sitemap_filter_all(entries)
            case _:
                self.logger.error(
                    f"Unknown sitemap_type: {self.args.sitemap_type}"
                )
                self.logger.warn(
                    "yielding all the entries."
                )
                yield from self.sitemap_filter_all(entries)

    def sitemap_filter_all(self, entries):
        default_deny_patters = [
            re.compile(r"\.(pdf|docx)$", re.IGNORECASE)
        ]
        for entry in entries:
            loc = entry.get("loc", "")
            if any(pattern.search(loc) for pattern in default_deny_patters):
                self.logger.debug(f"Ignoring a sitemap URL: {loc}")
                continue
            yield entry

    def sitemap_filter_wordpress(self, entries):
        deny_patterns = [
            # general patterns
            re.compile(r"(?:taxonomy|taxonomies|author|category|archive)-.*\.xml"), # noqa E501
            # Yoast SEO
            re.compile(r"(?:post_tag|post_format)-.*\.xml"),
        ]
        entries = self.sitemap_filter_all(entries)
        for entry in entries:
            loc = entry.get("loc", "")
            if any(pattern.search(loc) for pattern in deny_patterns):
                self.logger.debug(f"Ignoring a sitemap.xml {loc}")
                continue
            else:
                self.logger.debug(f"Yielding a sitemap.xml {loc}")
                yield entry

    def parse(self, response: Response):
        content_type = response.headers.get(
            "Content-Type", b""
        ).decode("utf-8").lower()
        if "text/html" not in content_type:
            self.logger.debug(
                f"Skipping non-HTML content: {response.url} ({content_type})"
            )
            return
        return ArticleItem.from_response(response)
