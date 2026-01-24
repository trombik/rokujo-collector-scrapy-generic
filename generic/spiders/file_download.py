from typing import Type

import scrapy

from generic.mixins.file_downloader import (
    FileDownloaderMixin,
    FileDownloaderMixinConfig,
)
from generic.spiders.base import GenericSpider
from generic.utils import is_file_url, is_path_matched


class FileDownloadSpiderConfig(FileDownloaderMixinConfig):
    path_regexp: str = r"^/"
    """
    A regular expression for URL path part that the spider should crawls.
    """


class FileDownloadSpider(
    GenericSpider[FileDownloadSpiderConfig], FileDownloaderMixin
):
    """
    A spider that download files under a specific path.
    """

    name = "file-download"

    @classmethod
    def get_config_class(cls) -> Type[FileDownloadSpiderConfig]:
        """
        Returns the config class for this spider.
        """
        return FileDownloadSpiderConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start(self):
        for url in self.args.urls:
            yield scrapy.Request(url, self.parse_page)

    def parse_page(
        self,
        res: scrapy.http.Response,
    ):
        current_depth = res.meta.get("depth", 0)
        self.logger.info(f"Crawling (depth={current_depth}): {res.url}")
        # call parse_file_download_page() to download all the files that
        # matches file_regexp. the method yield scraped items.
        yield from self.parse_file_download_page(res)

        # we have done with all the available files on this page.
        # find links to other pages.
        xpath_query = "//a[@href]"
        selectors = res.xpath(xpath_query)
        for sel in selectors:
            href = sel.xpath("@href").get().strip()
            # ignore if the a tag has no href attribute
            if not href:
                continue

            abs_href = res.urljoin(href)
            # ignore links to files.
            if is_file_url(abs_href):
                continue

            # crawl the found links that match path_regexp by recursively
            # calling the method.
            if is_path_matched(abs_href, self.args.path_regexp):
                yield res.follow(href, callback=self.parse_page)
