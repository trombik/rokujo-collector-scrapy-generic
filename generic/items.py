# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Self

from scrapy.http import Response
from scrapy.selector import Selector
from trafilatura import extract

from generic.utils import count_xml_character, get_metadata


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
    character_count: int = 0
    """ The number of characters in the article."""

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
    def from_response(cls, res: Response) -> Self:
        """
        Create an ArticleItem from a scrapy.http.Response.

        Args:
            res: scrapy.http.Response.
            lang: The language of the Response. When None, the language is
                guessed from the content.

        Returns:
            Self: An instance of ArticleItem or its subclass.
        """

        acquired_time = datetime.now(timezone.utc).isoformat()
        metadata = get_metadata(res)
        extracted = extract(
            res.text,
            url=metadata["url"],
            with_metadata=True,
            target_language=metadata["lang"],
            include_formatting=True,
            output_format="xml",
        )
        if extracted is None:
            raise ValueError(
                "Failed to extract content with trafilatura:\n"
                f"URL: {res.url}\n"
            )

        xml_sel = Selector(text=extracted)
        body = xml_sel.xpath("//doc/main").get()
        if body is None:
            raise ValueError(
                (
                    f"trafilatura XML does not contain //doc/main\n"
                    f"URL: {res.url}"
                )
            )
        character_count = count_xml_character(body)

        return cls(
            url=metadata["url"],
            title=metadata["title"],
            lang=metadata["lang"],
            author=metadata["author"],
            body=body,
            character_count=character_count,
            kind=metadata["kind"],
            site_name=metadata["site_name"],
            description=metadata["description"],
            acquired_time=acquired_time,
            published_time=metadata["published_time"],
            modified_time=metadata["modified_time"],
        )


@dataclass
class ArticleWithSourceItem(ArticleItem):
    """
    An ArticleItem that includes a list of related ArticleItems as sources.
    """

    sources: List[ArticleItem] = field(default_factory=list)
    """ A list of sources. """
