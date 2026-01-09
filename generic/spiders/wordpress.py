from urllib.parse import urlparse, urlunparse, urljoin
from datetime import datetime, timezone
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from trafilatura import extract
import json

from generic.items import ArticleItem


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

    def parse(self, response: Response):
        extracted = json.loads(
            extract(
                response.text,
                url=response.url,
                with_metadata=True,
                target_language="ja",
                output_format="json",
            )
        )

        now = datetime.now(timezone.utc)
        title = extracted.get("title", None)
        author = extracted.get("author", None)
        extracted_date = extracted.get("date", None)
        text = extracted.get("text", None)
        extracted_time = (
            datetime.fromisoformat(extracted_date) if extracted_date else None
        )

        site_name = get_meta_property(response, "og:site_name")
        description = get_meta_property(response, "og:description")
        kind = get_meta_property(response, "og:type")
        published_time = (
            get_meta_property(response, "article:published_time")
            or extracted_time
        )
        modified_time = (
            get_meta_property(response, "article:modified_time")
            or published_time
        )

        item = ArticleItem(
            kind=kind,
            site_name=site_name,
            description=description,
            title=title,
            author=author,
            uri=response.url,
            created_at=published_time,
            updated_at=modified_time,
            acquired_at=now,
            text=text,
        )
        yield item


def idn2ascii(url_str: str) -> str:
    parsed = urlparse(url_str.strip())
    puny_host = parsed.netloc.encode("idna").decode("ascii")
    new_parsed = parsed._replace(netloc=puny_host)
    return urlunparse(new_parsed)


def get_meta_property(response: Response, name: str) -> str:
    """
    Extracts a meta property content from a response.

    Args:
        - response The response object.
        - name Name of the property.
    """
    path = f"//meta[@property='{name}']/@content"
    return response.xpath(path).get()
