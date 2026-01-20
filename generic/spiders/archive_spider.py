from typing import Optional, Type

import scrapy

from generic.mixins.read_more import ReadMoreMixin
from generic.spiders.base import GenericSpider
from generic.spiders.read_more import ReadMoreSpiderConfig


class ArchiveSpiderConfig(ReadMoreSpiderConfig):
    """
    A spider configuration class for ArchiveSpider.

    Attributes:
        archive_article_xpath (Optional[str]):
            XPath expression to extract article links from the archive page.
        archive_next_xpath (Optional[str]):
            XPath expression to extract the link to the next archive page.
    """
    archive_article_xpath: Optional[str] = (
        "//main//li[@class!=' pr']//h2[@class='title']//a/@href"
    )
    archive_next_xpath: Optional[str] = (
        "//div[contains(@class, 'pagination')]//a[contains(text(), '次へ')]/@href"  # noqa E501
    )
    pass


class ArchiveSpider(
        GenericSpider[ArchiveSpiderConfig],
        ReadMoreMixin,
        ):
    """
    Parse archive pages, follow links to articles, and proceed to the next
    archive page if any.

    A typical archive page consists of:

    * A list of articles with links
    * A paginated navigation bar to "Next"

    The spider collects links to articles with `archive_article_xpath`,
    follows the "Next" link with `archive_next_xpath`, and processes the next
    archive page.

    The spider's configuration is `ArchiveSpiderConfig`, which inherits
    `ReadMoreSpiderConfig`.

    * `archive_article_xpath`
        A XPath expression to the href attribute of an <a> tag for articles.
    * `archive_next_xpath`
        A XPath expression to the href attribute of an <a> tag for the "Next"
        archive page.
    """
    name = "archive_spider"
    allowed_domains = ["bunshun.jp"]
    start_urls = ["https://bunshun.jp/category/latest?page=300"]

    @classmethod
    def get_config_class(cls) -> Type[ArchiveSpiderConfig]:
        """
        Returns the config class for this spider.
        """
        return ArchiveSpiderConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start(self):
        for url in self.args.urls:
            yield scrapy.Request(url, self.parse_archive_index)

    def parse_archive_index(self, response):
        """
        Parse the index page of an archive, yielding requests for articles and
        the next archive page.

        Args:
            response (scrapy.http.Response):
                The response object containing the archive page content.

        Yields:
            scrapy.http.Request:
                Requests for individual articles and the next archive page.
        """
        self.logger.debug(
            "Looking for a tag with archive_article_xpath"
            f"archive_article_xpath:\n{self.args.archive_article_xpath}"
        )
        article_hrefs = response.xpath(
            self.args.archive_article_xpath
        ).getall()

        for article_href in article_hrefs:
            self.logger.debug(f"Found href: {article_href}")
            yield response.follow(
                article_href,
                callback=self.parse_article
            )

        self.logger.debug(
            "Looking for a tag with archive_next_xpath"
            f"archive_article_xpath:\n{self.args.archive_next_xpath}"
        )
        archive_next_href = response.xpath(
            self.args.archive_next_xpath
        ).get()
        if archive_next_href:
            self.logger.debug(f"Found href: {archive_next_href}")
            yield response.follow(
                archive_next_href,
                callback=self.parse_archive_index
            )
