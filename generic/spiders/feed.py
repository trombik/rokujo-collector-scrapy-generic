from pathlib import Path
from typing import Type

import scrapy
import yaml
from feedgen.feed import FeedGenerator
from pydantic import BaseModel

from generic.items import FeedItem
from generic.spiders.base import GenericSpider, GenericSpiderConfig


class FeedEntry(BaseModel):
    id: str
    title: str
    link: str


class Feed(BaseModel):
    id: str
    """
    The URL of the page.
    """
    lang: str
    """
    The language of the page.
    """
    type: str
    """
    The type of the feed. Either "atom" or "rss"
    """
    title: str
    """
    Title of the page
    """


class FeedConfig(BaseModel):
    """
    Configuration for FeedSpider.

    Use a YAML file for configuration. Specify the path with
    `-a /path/to/config.yml`. Default is `feed.yml`.

    The top-level key must be `feed_config`.

    `feed_config` is a dictionary. The key is the page URL for the feed. The
    value is a dictionary with `file_name`, `feed_type`, `xpath_href`, and
    `xpath_title`.

    `file_name`: The name of the generated feed file. This must be unique per
                 URL. The file is overwritten when a feed is generated.

    `xpath_title` is the path to the feed title.

    `xpath_href` is the path to the `href` attribute of the link.

    `feed_type` is either `atom` or `rss`.

    Example:

    ```yaml
    ---
    feed_config:
      "http://foo.example.org/latest.html":
        file_name: "latest.xml"
        feed_type: "atom"
        xpath_href: "//li[@class='articles-list__item']/a/@href"
        xpath_title: "//li[@class='articles-list__item']/a/text()"
    ```

    """
    file_name: str
    xpath_href: str
    xpath_title: str
    feed_type: str = "atom"


class FeedSpiderConfig(GenericSpiderConfig):
    feed_config: dict[str, FeedConfig]
    config: Path


class FeedSpider(GenericSpider[FeedSpiderConfig]):
    """
    A spider that generates Atom/RSS feeds. The spider crawls URLs in a
    configuration file, scrape links, and geenrates a feed for the page.

    The spider has custom_settings. In `ITEM_PIPELINES`, `FeedStoragePipeline`
    is set at 900. The pipeline stores the generated feeds.

    Args:
        config (str): The path to configuration file.
            The default is `feed.yml`.

    """
    name = "feed"
    custom_settings = {
        "ITEM_PIPELINES": {
            "generic.pipelines.FeedStoragePipeline": 900,
        }
    }

    @classmethod
    def get_config_class(cls) -> Type[FeedSpiderConfig]:
        """
        Returns the config class for this spider.
        """
        return FeedSpiderConfig

    def __init__(self, *args, **kwargs):
        config_path = Path(kwargs.get("config", "feed.yml"))
        try:
            config_obj = self._load_config(config_path)
            kwargs.update(config_obj.model_dump())
        except Exception as e:
            self.logger.error(
                f"Failed to load config_path: {config_path.resolve()}"
            )
            raise e
        super().__init__(*args, **kwargs)
        self.args = config_obj

    def _load_config(self, path: Path):
        content = path.read_text(encoding="utf-8")
        raw_data = yaml.safe_load(content)
        return FeedSpiderConfig(
            urls=[],
            feed_config=raw_data.get("feed_config", {}),
            config=path
        )

    def start_requests(self):
        for url, cfg in self.args.feed_config.items():
            yield scrapy.Request(
                url,
                callback=self.parse,
            )

    def parse(self, response: scrapy.http.Response):
        url = response.url
        lang = response.xpath("/html/@lang").get() or "en"
        config = self.args.feed_config[url]
        xpath_title = config.xpath_title
        xpath_href = config.xpath_href
        page_title = response.xpath(
            "//title/text()"
        ).get() or f"Feed for {url}"

        titles = response.xpath(xpath_title).getall()
        hrefs = response.xpath(xpath_href).getall()

        feed_entries = []
        for title, href in zip(titles, hrefs):
            abs_url = response.urljoin(href)
            feed_entries.append(
                FeedEntry(id=abs_url, title=title.strip(), link=abs_url)
            )
        feed_meta = Feed(
            id=url,
            type=config.feed_type,
            lang=lang,
            title=page_title
        )
        yield self._generate_feed(
            url=url,
            feed=feed_meta,
            feed_entries=feed_entries,
            file_name=config.file_name,
        )

    def _generate_feed(
        self,
        url: str,
        feed: Feed,
        feed_entries: list[FeedEntry],
        file_name: str,
    ) -> FeedItem:
        fg = FeedGenerator()
        fg.id(feed.id)
        fg.language(feed.lang)
        fg.title(feed.title)
        fg.link(href=url, rel="self")

        for entry in feed_entries:
            feed_entry = fg.add_entry()
            feed_entry.id(entry.id)
            feed_entry.title(entry.title)
            feed_entry.link(href=entry.link)

        generated_feed = None
        match feed.type:
            case "atom":
                generated_feed = fg.atom_str(pretty=True)
            case "rss":
                generated_feed = fg.rss_str(pretty=True)
            case _:
                raise ValueError

        if generated_feed is None:
            raise RuntimeError("Failed to generate feed string.")
        return FeedItem(
            url=url,
            file_name=file_name,
            content=generated_feed.decode("utf-8"),
        )
