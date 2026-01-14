from typing import List
from urllib.parse import urlparse

import scrapy
from pydantic import BaseModel
from scrapy_spider_metadata import Args

from generic.items import ArticleItem, ArticleWithSourceItem
from generic.utils import idn2ascii


class MyParams(BaseModel):
    urls: str
    """ Comma separated list of URLs."""

    parent_contains_text: str = None
    """
        Matches <a> tag whose parent contains `parent_contains_text`.

        An example:

        When `parent_contains_text` is `英語記事`, the spider picks all the
        following <a> tags.

        ```html
        <main>
            <p>英語記事: <a href="#">foo</a> / <a href="#">bar</a></p>
        </main>
        ```
    """

    contains_text: str = None
    """
        Matches <a> tag, whose text contains `contains_text`.

        An example:

        When `contains_text` is `US版`, the spider picks all the following <a>
        tags.

        ```html
        <main>
            <a>US版</a>
            <p><a>US版</a></a>
        </main>
        ```
    """


class WithSourceSpider(Args[MyParams], scrapy.Spider):
    """
    Yields an ArticleWithSourceItem from URLs.

    The spider crawls given URLs and scrapes the article and source articles
    if it finds them.

    The spider assumes that articles are a child of `<main>`.

    Args:
        urls: Comma-separated string of summary page URLs. Mandatory.

    Yields:
        ArticleWithSourceItem
    """

    name = "with-source"
    allowed_domains = []
    start_urls = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # parse urls argument
        for url in self.args.urls.split(","):
            domain = urlparse(idn2ascii(url)).netloc
            self.allowed_domains.append(domain)
            self.logger.debug(f"allowed_domains: {self.allowed_domains}")
        if self.args.parent_contains_text and self.args.contains_text:
            raise ValueError(
                "parent_contains_text and contains_text are muturally "
                "exclusive."
            )

    async def start(self):
        for url in self.args.urls.split(","):
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        """
        Parse the target page. If the target page has sources, fetch and
        extract them as ArticleItem. The sources are appended to
        ArticleWithSourceItem.

        Yields:
            ArticleWithSourceItem

        """
        item = ArticleWithSourceItem.from_response(response)

        if self.args.contains_text:
            query = (
                "//main//a[contains(., $arg)]/@href"
            )
            arg = self.args.contains_text
        elif self.args.parent_contains_text:
            query = (
                "//main//a[contains(parent::*, $arg)]/@href"
            )
            arg = self.args.parent_contains_text
        else:
            ValueError(
                "Neither contains_text nor parent_contains_text is specified. "
                "Use either of them."
            )

        self.logger.debug(f"query: {query}\narg: {arg}\n")
        source_hrefs = response.xpath(
            query,
            arg=arg
        ).getall()

        # ensure URLs are absolute.
        source_urls = [response.urljoin(href) for href in source_hrefs]

        # no source URLs, yield the item.
        if not source_urls:
            yield item
            return

        # ensure unique URLs and pass a list for destructive pop()
        unique_urls = list(dict.fromkeys(source_urls))
        yield from self._request_sources(item, list(unique_urls))

    def _request_sources(self, item, urls):
        if not urls:
            # no remaining URLs. yield the item.
            yield item
            return

        # urls is not empty. yield another Request and create an ArticleItem.
        next_url = urls.pop(0)

        yield scrapy.Request(
            next_url,
            callback=self.parse_source,
            cb_kwargs={
                "parent_item": item,
                "remaining_urls": urls,
            },
            dont_filter=True,
        )

    def parse_source(
        self,
        res: scrapy.http.Response,
        parent_item: ArticleWithSourceItem,
        remaining_urls: List[str],
    ):
        """
        Parse a source of an article and append a ArticleItem to the parent
        ArticleWithSourceItem.

        Args:
            res: The HTTP response
            parent_item: The article that refers this source article.
            remaining_urls: A list of remaining URLs.

        """

        # res is a source article. create an ArticleItem.
        source_item = ArticleItem.from_response(res)

        # append the source article to the parent item.
        parent_item.sources.append(source_item)
        yield from self._request_sources(parent_item, remaining_urls)
