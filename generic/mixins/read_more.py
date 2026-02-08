from typing import List, Optional, Protocol

import scrapy
from lxml import etree

from generic.items import ArticleItem
from generic.spiders.base import GenericSpiderConfig
from generic.utils import get_url_without_fragment


class ReadMoreCompatible(Protocol):
    args: GenericSpiderConfig
    logger: any


class ReadMoreMixinConfig(GenericSpiderConfig):
    read_more: str = "記事全文を読む"
    """
    The text of ``<a>`` tag, the link to the main article.
    """
    read_more_xpath: Optional[str] = None
    """
    XPath expression that matches the link to the main article.
    """
    read_next: str = "次へ"
    """
    The text of ``<a>`` tag, the link to the next page.
    """
    read_next_contains: Optional[str] = None
    source_contains: Optional[str] = None
    source_parent_contains: Optional[str] = None


class ReadMoreMixin:
    """
    Provides recursive article parsing capability. See also: ReadMoreSpider.
    """

    def parse_summary_page(self, res: scrapy.http.Response):
        """
        Parse the summary article. If "Read more" link is not found, it
        assumes that the page is the main article and parse it as an article.

        Yields:
            Request to the main article if "Read more" link is found.
            ArticleItem if "Read more" link is not found.
        """
        href = self._find_read_more_link(res)
        if href:
            target_url = res.urljoin(href)
            self.logger.debug(f"Read more link is found. Parsing {target_url}")
            yield scrapy.Request(target_url, callback=self.parse_article)
        else:
            self.logger.debug(f"No read more link is found. Parsing {res.url}")
            yield from self.parse_article(res)

    def parse_article(
        self, res: scrapy.http.Response, item: ArticleItem = None
    ):
        """
        Parse an article.

        Yields:
            ArticleItem
        """

        if item is None:
            self.logger.debug(f"Parsing the first page: {res.url}")
            item = ArticleItem.from_response(res)
        else:
            self.logger.debug(
                f"Parsing another page, {res.url}, for {item.url}"
            )
            try:
                item = self._merge_article_body(item, res)

            except Exception as e:
                self.logger.error(f"_merge_article_body: {e}")
                return
        self.logger.debug(f"Created ArticleItem for: {item.url}")

        # we've done with parsing the response. find "Next page" link.
        read_next_href = self._find_next_page_link(res)
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

    def parse_source_only(
        self,
        res: scrapy.http.Response,
        parent_item: ArticleItem,
        remaining_urls: list[str],
    ):
        """
        Parse source pages and add the source article to the parent item.

        This method handles the extraction of source articles from response
        objects. It attempts to create an ArticleItem from the response and
        appends it to the parent item's sources list. If the extraction fails,
        it logs the error and continues processing the remaining URLs.

        Unlike Japanese news outlets, English ones avoid pagination in general
        for better UX. The method assumes that the source page is a
        single-page article. It does not crawl "Next page".
        """

        # avoid exceptions here to save the parent item even if it fails to
        # scrape the source article. Otherwise, an exception here causes the
        # entire process to fail, resulting data loss of the parent item.
        try:
            source_item = ArticleItem.from_response(res)
            parent_item.sources.append(source_item)
        except Exception as e:
            self.logger.error(
                f"Failed to scrape a source article at: {res.url} {e}"
            )

        yield from self._request_next_source(parent_item, remaining_urls)

    def _find_read_more_link(
        self: ReadMoreCompatible,
        res: scrapy.http.Response,
    ) -> str:
        """
        Find the "Read more..." link in the HTML response.

        This method searches for a "Read more..." link in the provided HTTP
        response. It first checks if a custom XPath expression is provided in
        the arguments. If so, it uses this XPath to find the link. Otherwise,
        it searches for a link with the default text "Read more..." using a
        predefined XPath expression.

        Args:
            res: The HTTP response to search for the link.

        Returns:
            str: The href attribute of the found link, or None if no link is found.
        """
        if self.args.read_more_xpath:
            self.logger.debug(
                f"Searching read_more_xpath with: {self.args.read_more_xpath}"
            )
            return res.xpath(f"{self.args.read_more_xpath}/@href").get()
        else:
            self.logger.debug(
                f"Searching read_more with: {self.args.read_more}"
            )
            return res.xpath(
                "//a[contains(., $text)]/@href", text=self.args.read_more
            ).get()

    def _find_next_page_link(
        self,
        res: scrapy.http.Response,
    ) -> str:
        """
        Find the "Next Page" link in the provided HTTP response.

        This method searches for a link that indicates the next page of
        content. It can use either a specific text pattern or a direct text
        match to locate the link.

        Args:
            res: The HTTP response to search for the
                next page link.

        Returns:
            str: The href attribute of the found link, or None if no link is
            found.
        """
        if self.args.read_next_contains:
            self.logger.debug(
                (
                    "Searching read_next_contains with: ",
                    f"{self.args.read_next_contains}",
                )
            )
            return res.xpath(
                "//a[contains(., $text)]/@href",
                text=self.args.read_next_contains,
            ).get()
        elif self.args.read_next:
            self.logger.debug(
                f"Searching read_next with: {self.args.read_next}"
            )
            return res.xpath(
                "//a[text()=$text]/@href", text=self.args.read_next
            ).get()

    def _merge_article_body(
        self,
        base_item: ArticleItem,
        next_res: scrapy.http.Response,
    ) -> ArticleItem:
        """
        Merge the content of an article from `next_res` into `base_item`.

        This method takes the HTTP response of an article from `next_res` and
        appends it to the existing content in `base_item`. The method ensures
        that the resulting XML structure remains valid by properly handling
        the <main> tags and merging the content without introducing duplicate
        <main> tags.

        Args:
            base_item: The base article item to which the
            content will be merged.
            next_res: The response containing the
            article content to be merged.

        Returns:
            ArticleItem: The merged article item with the content from
            `next_res` appended.

        Raises:
            ValueError: If the `base_item.body` does not contain a <main> tag.
            etree.XMLSyntaxError: If there is an error parsing the XML content.
        """
        # as we are not at the first page, parse the response and
        # append the parsed content to item. ArticleItem.body has <main>
        # and we don't want multiple <main> tags in ArticleItem.
        #
        # The item we are going to yield has a <main> which has inner
        # main of the first page + inner main of the next page (the
        # current response).
        inner_item = ArticleItem.from_response(next_res)

        try:
            # find the <main> tag to append inner_item to
            main = etree.fromstring(base_item.body.encode("utf-8"))

            if main is None:
                # should not happen
                raise ValueError(
                    f"ArticleItem.body does not have <main>\n{base_item.body}"
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
            base_item.body = etree.tostring(main, encoding="unicode")
        except (ValueError, etree.XMLSyntaxError) as e:
            self.logger.error(
                f"Failed to parse XML: {next_res.url}\n"
                f"Inner item:\n{inner_item.body}\n"
                f"Item:\n{base_item.body}\n"
            )
            raise e
        return base_item

    def _find_source_links(
        self,
        res: scrapy.http.Response,
    ) -> List[str]:
        """
        Find source links.
        """
        query = None
        arg = None
        if self.args.source_contains:
            query = "//a[contains(., $arg)]/@href"
            arg = self.args.source_contains
        elif self.args.source_parent_contains:
            # Matches <a> tags where an ancestor within 2 levels contains
            # specific text.
            query = "//a[ancestor::*[position() <= 2][contains(text(), $arg)]]/@href"  # noqa E501
            arg = self.args.source_parent_contains
        # no options for sources. yield item and finish.
        if not query:
            return

        self.logger.debug(f"query: {query}\narg: {arg}\n")
        source_hrefs = res.xpath(query, arg=arg).getall()

        # ensure URLs are absolute.
        source_urls = [res.urljoin(href) for href in source_hrefs]
        # and they are unique
        uniq_urls = list(set(get_url_without_fragment(u) for u in source_urls))
        return uniq_urls

    def _find_and_request_sources(
        self, res: scrapy.http.Response, item: ArticleItem
    ):
        """
        Find source articles.
        """
        unique_urls = self._find_source_links(res)
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
            callback=self.parse_source_only,
            cb_kwargs={
                "parent_item": item,
                "remaining_urls": urls,
            },
            dont_filter=True,
        )
