from urllib.parse import urlparse

import scrapy
from lxml import etree
from pydantic import BaseModel
from scrapy_spider_metadata import Args

from generic.items import ArticleItem
from generic.utils import idn2ascii


class MyParams(BaseModel):
    urls: str
    read_more: str = "記事全文を読む"
    read_next: str = "次へ"


class ReadMoreSpider(Args[MyParams], scrapy.Spider):
    """
    A spider to extract a main article from summary pages. It also supports a
    single page and multiple pages in an article. Useful when RSS feed does
    not return the link to the main article but a landing page.

    This spider processes summary pages that contain links to main articles.
    For example, a summary page might have a link like <a href="main.html">
    Read more...</a>.

    * First page -> Main article page
    * First page -> Main article page -> Next page(s)
    * First page -> Next page(s)

    The content of the first page will not be included in ArticleItem when the
    page contains a `read_more` link. Otherwise, the content is included as
    part of the article.

    When the main article is split into multiple pages, specify
    `read_next`. The spider crawls all the pages and returns a single
    ArticleItem.

    The spider accepts a comma-separated list of summary page URLs and returns
    ArticleItem of the main articles.

    When no link with `read_more` text is found, the spider parses the first
    page and proceeds next page if it finds one.

    The allowed_domains is automatically set to the domain name of the `urls`.
    It is recommended to pass URLs under the same domain.

    Args:
        urls: Comma-separated string of summary page URLs. Mandatory.
        read_more: Text string of the <a> tag that links to the main article.
                   Default is "記事全文を読む".
        read_next: Text string of the <a> tag that links to the next page.
                   Default is "次へ".
    """

    name = "read-more"
    allowed_domains = ["news.yahoo.co.jp"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for url in self.args.urls.split(","):
            domain = urlparse(idn2ascii(url)).netloc
            self.allowed_domains.append(domain)
            self.logger.debug(f"allowed_domains: {self.allowed_domains}")

    async def start(self):
        for url in self.args.urls.split(","):
            yield scrapy.Request(url, self.parse)

    def parse(self, res: scrapy.Request):
        """
        Parse the summary article.

        Yields:
            Request to the main article.
        """

        self.logger.debug(f"Searching read_more with: {self.args.read_more}")
        href = res.xpath(
            "//a[text()=$text]/@href", text=self.args.read_more
        ).get()
        if href:
            target_url = res.urljoin(href)
            self.logger.debug(f"Read more link is found. Parsing {target_url}")
            yield scrapy.Request(target_url, callback=self.parse_article)
        else:
            # the page does not have a link to main article. assume the page
            # is the main article.
            self.logger.debug(f"No read more link is found. Parsing {res.url}")
            yield from self.parse_article(res)

    def parse_article(
            self, res: scrapy.http.Response,
            item: ArticleItem = None):
        """
        Parse the main article.

        Yields:
            ArticleItem
        """

        if item is None:
            self.logger.debug(f"Parsing the first page: {res.url}")
            item = ArticleItem.from_response(res)
        else:
            # as we are not at the first page, parse the response and
            # append the parsed content to item. ArticleItem.boy has <main>
            # and we don't want multiple <main> tags in ArticleItem.
            #
            # The item we are going to yield has a <main> which has inner
            # main of the first page + inner main of the next page (the
            # current response).
            #
            # TODO: isolate this logic from parse_main_article.
            self.logger.debug(
                f"Parsing another page, {res.url}, for {item.url}"
            )
            try:
                inner_item = ArticleItem.from_response(res)

                # find the <main> tag to append inner_item to
                main = etree.fromstring(item.body.encode("utf-8"))

                if main is None:
                    # should not happen
                    raise ValueError(
                        f"ArticleItem.body does not have <main>\n{item.body}"
                    )

                # extract the content that will be appended to <main> in item.
                inner_main_xml_strings = (
                    scrapy.Selector(text=inner_item.body)
                    .xpath("//main/node()")
                    .getall()
                )

                for string in inner_main_xml_strings:
                    # convert string to XML. <root> is required as lxml
                    # complains.
                    xml_fragments = etree.fromstring(f"<root>{string}</root>")
                    # and append them to <main> in the item.
                    for child in xml_fragments:
                        main.append(child)
                # replace the body with new XML string.
                item.body = etree.tostring(main, encoding="unicode")

            except (ValueError, etree.XMLSyntaxError):
                self.logger.error(
                    f"Failed to parse XML: {res.url}\n"
                    f"Inner item:\n{inner_item.body}\n"
                    f"Item:\n{item.body}\n"
                )
                return
        self.logger.debug(f"Created ArticleItem for: {item.url}")

        # we've done with parsing the response. find "Next page" link.
        self.logger.debug(f"Searching read_next with: {self.args.read_next}")
        read_next_href = res.xpath(
            "//a[text()=$text]/@href", text=self.args.read_next
        ).get()

        if read_next_href:
            self.logger.debug(f"Found another page: {read_next_href}")
            # the response has a link to next page, recursively call this
            # method with the parsed item.
            yield scrapy.Request(
                res.urljoin(read_next_href),
                self.parse_article,
                cb_kwargs={"item": item},
            )
        else:
            # the response is the last page. Simply yield the item
            self.logger.debug(f"Done with ArticleItem for {item.url}")
            yield item
