from datetime import datetime, timezone
from os.path import basename
from urllib.parse import unquote, urlparse

import scrapy

from generic.items import FileItem
from generic.spiders.base import GenericSpiderConfig
from generic.utils import (
    get_metadata,
    is_file_url,
    is_path_matched,
)


class FileDownloaderMixinConfig(GenericSpiderConfig):
    """
    Config class for FileDownloaderMixin.
    """

    file_regexp: str = "\\.pdf$"
    output_dir: str = "./"


class FileDownloaderMixin:
    """
    Provides file download capability.
    """

    def parse_file_download_page(
        self,
        res: scrapy.http.Response,
    ):
        for href in self.extract_file_download_hrefs(res):
            if not is_file_url(res.urljoin(href)):
                continue

            yield scrapy.Request(
                href,
                callback=self.parse_file_download_file,
                cb_kwargs={"context_response": res},
            )

    def extract_file_download_hrefs(
        self,
        response: scrapy.http.Response,
    ) -> list:
        xpath_query = "//a[@href]"
        selectors = response.xpath(xpath_query)
        matched_hrefs = []
        for sel in selectors:
            href = sel.xpath("@href").get().strip()
            if not href:
                continue

            abs_href = response.urljoin(href)
            if is_path_matched(abs_href, self.args.file_regexp):
                matched_hrefs.append(abs_href)

        return matched_hrefs

    def parse_file_download_file(
        self,
        res: scrapy.http.Response,
        context_response: scrapy.http.Response,
    ):
        filename = basename(unquote(urlparse(res.url).path)) or "unknown"
        item = FileItem(
            acquired_time=datetime.now(timezone.utc),
            content=res.body,
            url=res.url,
            metadata=get_metadata(context_response),
            filename=filename,
            output_dir=self.args.output_dir,
        )
        yield item
