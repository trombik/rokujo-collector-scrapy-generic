from typing import Optional, Type

import scrapy

from generic.mixins.read_more import ReadMoreMixin
from generic.spiders.base import GenericSpider, GenericSpiderConfig


class ReadMoreSpiderConfig(GenericSpiderConfig):
    read_more: str = "記事全文を読む"
    read_more_xpath: Optional[str] = None
    read_next: str = "次へ"
    read_next_contains: Optional[str] = None
    source_contains: Optional[str] = None
    source_parent_contains: Optional[str] = None


class ReadMoreSpider(GenericSpider[ReadMoreSpiderConfig], ReadMoreMixin):
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
            yield scrapy.Request(url, self.parse_summary_page)

    def parse(self, res: scrapy.http.Response):
        yield from self.parse_summary_page(res)
