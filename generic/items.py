# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Self

from dateutil import parser
from scrapy.http import Response
from scrapy.selector import Selector
from trafilatura import extract


@dataclass
class ArticleItem:
    """
    Represents an article.
    """

    acquired_time: datetime
    """ The time when the webpage was acquired. """
    body: str
    """ The main content of the webpage. """
    url: str
    """ The URL of the webpage. """

    lang: str
    """
    The two letter language code of the article. When the language is
    undetermined, "und" is returned.

    See also: ISO 639-1:2002; Part 1: Alpha-2 code (JIS X 0412-1:2004)
    """

    author: Optional[str] = None
    """ The author of the webpage. """
    description: Optional[str] = None
    """ A brief description of the webpage. """
    fingerprint: Optional[str] = None
    """ A fingerprint. """
    kind: Optional[str] = None
    """ The type or category of the webpage. """
    modified_time: Optional[str] = None
    """ The time when the webpage was last modified. """
    published_time: Optional[str] = None
    """ The time when the webpage was published. """
    site_name: Optional[str] = None
    """ The name of the website. """
    title: Optional[str] = None
    """ The title of the webpage. """
    item_type: str = field(init=False)
    """ The class name of the item. Automatically set in __post_init__."""

    def __post_init__(self):
        self.item_type = self.__class__.__name__

    @staticmethod
    def get_json_ld(res: Response) -> Dict[str, Any]:
        """Extracts and parses JSON-LD from the response."""
        raw_json = res.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).get()
        if not raw_json:
            return {}
        try:
            data = json.loads(raw_json)
            # return the first item when data is a list and ignore others.
            return data[0] if isinstance(data, list) else data
        except (json.JSONDecodeError, IndexError):
            return {}

    @classmethod
    def from_response(cls, res: Response, lang: str = None) -> Self:
        """
        Create an ArticleItem from a scrapy.http.Response.

        Args:
            res: scrapy.http.Response.
            lang: The language of the Response. When None, the language is
                guessed from the content.

        Returns:
            Self: An instance of ArticleItem or its subclass.
        """

        def get_meta_property(name: str) -> str:
            """
            Extracts a meta property content from a response.

            Args:
                - name Name of the property.
            """
            path = f"//meta[@property='{name}']/@content"
            return res.xpath(path).get()

        def get_meta_name(name: str) -> str:
            query = f"//meta[@name='{name}']/@content"
            return res.xpath(query).get()

        def str_to_isoformat(string: str):
            if str is None:
                return None
            try:
                dt = parser.parse(string)
                return dt.isoformat()
            except (ValueError, TypeError, OverflowError):
                return None

        extracted = extract(
            res.text,
            url=res.url,
            with_metadata=True,
            target_language=lang,
            include_formatting=True,
            output_format="xml",
        )

        if extracted is None:
            raise ValueError(
                "Failed to extract content with trafilatura:\n"
                f"URL: {res.url}\n"
            )

        acquired_time = datetime.now(timezone.utc).isoformat()
        xml_sel = Selector(text=extracted)
        x_title = xml_sel.xpath("//doc/@title").get()
        x_lang = xml_sel.xpath("//doc/@language").get() or "und"
        x_author = xml_sel.xpath("//doc/@author").get()
        x_description = xml_sel.xpath("//doc/@description").get()
        x_fingerprint = xml_sel.xpath("//doc/@fingerprint").get()
        x_body = xml_sel.xpath("//doc/main").get()
        if x_body is None:
            raise ValueError(
                (
                    f"trafilatura XML does not contain //doc/main\n"
                    f"URL: {res.url}"
                )
            )
        x_site_name = xml_sel.xpath("//doc/@sitename").get()

        ld = cls.get_json_ld(res)
        match ld.get("author"):
            case {"name": name}:
                ld_author = name
            case [{"name": name}]:
                ld_author = name
            case _:
                ld_author = None

        match ld.get("datePublished"):
            case str(dt):
                ld_published_time = dt
            case _:
                ld_published_time = None

        match ld.get("dateModified"):
            case str(dt):
                ld_modified_time = dt
            case _:
                ld_modified_time = None

        published_time = str_to_isoformat(
            (get_meta_property("article:published_time"))
            or (get_meta_name("article:published_time"))
            or (ld_published_time)
        )
        modified_time = str_to_isoformat(
            (get_meta_property("article:modified_time"))
            or (get_meta_name("article:modified_time"))
            or (ld_modified_time)
        )
        author = (
            (x_author)
            or (get_meta_name("article:author"))
            or (get_meta_property("article:author"))
            or (ld_author)
        )

        return cls(
            url=res.url,
            title=x_title,
            lang=x_lang,
            author=author,
            fingerprint=x_fingerprint,
            body=x_body,
            kind=get_meta_property("og:type"),
            site_name=x_site_name or get_meta_property("og:site_name"),
            description=x_description or get_meta_property("og:description"),
            acquired_time=acquired_time,
            published_time=published_time,
            modified_time=modified_time,
        )


@dataclass
class ArticleWithSourceItem(ArticleItem):
    """
    An ArticleItem that includes a list of related ArticleItems as sources.
    """

    sources: List[ArticleItem] = field(default_factory=list)
    """ A list of sources. """
