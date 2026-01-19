from typing import Optional, Type

import scrapy
from lxml import etree

from generic.items import ArticleItem
from generic.spiders.base import GenericSpider, GenericSpiderConfig


class ReadMoreSpiderConfig(GenericSpiderConfig):
    read_more: str = "記事全文を読む"
    read_more_xpath: Optional[str] = None
    read_next: str = "次へ"
    read_next_contains: Optional[str] = None
    source_contains: Optional[str] = None
    source_parent_contains: Optional[str] = None


class ReadMoreSpider(GenericSpider[ReadMoreSpiderConfig]):
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

        read_more_xpath:
            XPath query that matches <a> tag. '/@href' is automatically
            appended to the query.

            When `read_more_xpath` is not None, `read_more` is ignored.

            When the query matches multiple elements, the first one will be
            used.

            Default is None.

            An example:

            ```text
               //h3[contains(text(), "関連記事")]/following-sibling::ul[1]/li/a
            ```

            1. `//h3`
                * "Look everywhere": Search the entire document for any Level
                    3 Heading (<h3>).
            2. `[contains(text(), "関連記事")]`
                * "Filter by text": Out of all those headings, only keep the
                ones that contain the text "関連記事" (Related Articles).
            3. `/following-sibling::ul[1]`
                * "Find the next list": Look at the elements on the same level
                (siblings) immediately after that heading, and pick the first
                Unordered List (<ul>) you see.
            4. `/li/a`
                * "Go inside the list items": Navigate into each list item
                (<li>) and then into the link tag (<a>) found inside it.

        read_next: Text string of the <a> tag that links to the next page.

                   The spider finds the link to the next page that matches the
                   exact value of the argument.

                   Default is "次へ".

        read_next_contains: Text string of the <a> tag that links to the next
                            page.

                            The spider finds the link to the next page that
                            contains the value of the argument.

                            Default is "None"

        source_contains:
            Matches <a> tag, whose text contains `contains_text`.

            An example:

            When `contains_text` is `US版`, the spider picks all the following
            <a> tags.

            ```html
            <main>
                <a>US版</a>
                <p><a>US版</a></a>
            </main>
            ```

        source_parent_contains:
            Match <a> tags whose parent contains the value.

            An example:

            When `parent_contains_text` is `英語記事`, the spider picks all the
            following <a> tags.

            ```html
            <main>
                <p>英語記事: <a href="#">foo</a> / <a href="#">bar</a></p>
            </main>
            ```
    """

    name = "read-more"
    allowed_domains = ["news.yahoo.co.jp"]

    @classmethod
    def get_config_class(cls) -> Type[ReadMoreSpiderConfig]:
        """
        Returns the config class for this spider.
        """
        return ReadMoreSpiderConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start(self):
        for url in self.args.urls:
            yield scrapy.Request(url, self.parse)

    def parse(self, res: scrapy.Request):
        """
        Parse the summary article.

        Yields:
            Request to the main article.
        """
        if self.args.read_more_xpath:
            self.logger.debug(
                f"Searching read_more_xpath with: {self.args.read_more_xpath}"
            )
            href = res.xpath(f"{self.args.read_more_xpath}/@href").get()
        else:
            self.logger.debug(
                f"Searching read_more with: {self.args.read_more}"
            )
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
        self, res: scrapy.http.Response, item: ArticleItem = None
    ):
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

        if self.args.read_next_contains:
            self.logger.debug(
                (
                    "Searching read_next_contains with: ",
                    f"{self.args.read_next_contains}"
                )
            )
            read_next_href = res.xpath(
                "//a[contains(., $text)]/@href",
                text=self.args.read_next_contains,
            ).get()
        elif self.args.read_next:
            self.logger.debug(
                f"Searching read_next with: {self.args.read_next}"
            )
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
            # We are on the last page. Search for source articles here.
            self.logger.debug(f"Done with ArticleItem for {item.url}")
            yield from self._find_and_request_sources(res, item)

    def _find_and_request_sources(
        self,
        res: scrapy.http.Response,
        item: ArticleItem
    ):
        """
        Find source articles.
        """
        query = None
        arg = None
        if self.args.source_contains:
            query = "//a[contains(., $arg)]/@href"
            arg = self.args.source_contains
        elif self.args.source_parent_contains:
            query = "//a[contains(parent::*, $arg)]/@href"
            arg = self.args.source_parent_contains
        # no options for sources. yield item and finish.
        if not query:
            yield item
            return

        self.logger.debug(f"query: {query}\narg: {arg}\n")
        source_hrefs = res.xpath(query, arg=arg).getall()

        # ensure URLs are absolute.
        source_urls = [res.urljoin(href) for href in source_hrefs]
        unique_urls = list(dict.fromkeys(source_urls))
        self.logger.debug(f"Found unique_urls: {unique_urls}")

        # no source URLs, yield the item.
        if not unique_urls:
            self.logger.debug(f"No source URLs found in {res.url}")
            yield item
        else:
            self.logger.debug(f"Source URL(s) found: {unique_urls}")
            yield from self._request_next_source(item, unique_urls)

    def _request_next_source(
        self,
        item: ArticleItem,
        urls: list[str],
    ):
        if not urls:
            self.logger.debug("_request_next_source: Empty urls.")
            yield item
            return

        next_url = urls.pop(0)
        self.logger.debug(f"_request_next_source: next URL: {next_url}")
        yield scrapy.Request(
            next_url,
            callback=self._parse_source_only,
            cb_kwargs={
                "parent_item": item,
                "remaining_urls": urls,
            },
            dont_filter=True,
        )

    def _parse_source_only(
        self,
        res: scrapy.http.Response,
        parent_item: ArticleItem,
        remaining_urls: list[str],
    ):
        """
        Parse source pages and add the source article to the parent item.

        Unlike Japanese news outlets, English ones avoid pagenations in
        general for better UX. The method assumes that the source page is a
        single page article. It does not crawls "Next page".
        """

        # acoid exceptions here to save the parent item even if it fails to
        # scrape the source article. otherwise, an exception here causes the
        # entire process to fail, resulting data loss of the parent item.
        try:
            source_item = ArticleItem.from_response(res)
            parent_item.sources.append(source_item)
        except Exception as e:
            self.logger.error(
                f"Failed to scrape a source article at: {res.url} {e}"
            )

        yield from self._request_next_source(parent_item, remaining_urls)
