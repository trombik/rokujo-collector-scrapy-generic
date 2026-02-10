from typing import Type

import scrapy

from generic.items import ArticleItem
from generic.spiders.base import GenericSpider, GenericSpiderConfig


class XmlSpiderConfig(GenericSpiderConfig):
    xml_link_xpath: str
    """
    XPath expression to extract URLs, e.g., "//link/text()".
    """
    pass


class XmlSpider(
    GenericSpider[XmlSpiderConfig],
):
    """
    A spider that scrapes ArticleItem from links in an XML file. The spider is
    useful when a list of links is in a dynamic XML response and the browser
    renders the list.
    """

    name = "xml"

    @classmethod
    def get_config_class(cls) -> Type[XmlSpiderConfig]:
        """
        Returns the config class for this spider.
        """
        return XmlSpiderConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start(self):
        for url in self.args.urls:
            yield scrapy.Request(url, self.parse_xml)

    def parse_xml(
            self,
            response: scrapy.http.Response
    ):
        """
        A handler to parse the XML.
        """
        self.logger.debug(f"finding links with: {self.args.xml_link_xpath}")

        links = response.xpath(self.args.xml_link_xpath).getall()
        absolute_links = [response.urljoin(link) for link in links]
        for absolute_link in absolute_links:
            yield scrapy.Request(absolute_link, self.parse_content)

    def parse_content(
            self,
            response: scrapy.http.Response
    ):
        """
        A handler to parse the article.

        Yields:
            ArticleItem

        """
        yield ArticleItem.from_response(response)
