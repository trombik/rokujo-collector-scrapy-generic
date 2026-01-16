import pytest
import scrapy
from pytest_mock import MockerFixture
from scrapy.http import HtmlResponse

from generic.items import ArticleItem
from generic.spiders.read_more import ReadMoreSpider


class TestReadMoreSpider:
    @pytest.fixture
    def make_spider(self):
        """
        A factory to create the Class Under Test.
        """

        def _make(**kwargs):
            if "urls" not in kwargs:
                kwargs["urls"] = "http://example.org/summary"
            return ReadMoreSpider(**kwargs)

        return _make

    @pytest.fixture
    def url_default(self):
        return "http://example.org/summary/"

    @pytest.fixture
    def html_template(self):
        def _wrapper(content: str) -> str:
            return f"""
            <html lang="ja">
              <body>
                <h1>サマリーページ,</h1>
                {content}
              </body>
            </html>
            """

        return _wrapper

    class TestParse:
        class TestWhenDefaultIsGiven:
            def test_yields_request_to_article_page(
                self, make_spider, html_template, url_default
            ):
                body = html_template(
                    """
                    <a href='./article-001.html'>記事全文を読む</a>
                    """
                )
                response = HtmlResponse(
                    url=url_default, body=body, encoding="utf-8"
                )
                spider = make_spider()
                results = list(spider.parse(response))

                assert len(results) == 1
                request = results[0]
                assert isinstance(request, scrapy.Request)
                assert request.url == f"{url_default}article-001.html"
                assert request.callback == spider.parse_article

        class TestWhenReadMoreIsGiven:
            def test_yields_request_to_article_page(
                self, make_spider, html_template, url_default
            ):
                body = html_template(
                    """
                    <a href="./article-001.html">次へ</a>
                    """
                )
                response = HtmlResponse(
                    url=url_default, body=body, encoding="utf-8"
                )
                spider = make_spider(read_more="次へ")
                results = list(spider.parse(response))
                request = results[0]

                assert request.url == f"{url_default}article-001.html"

        class TestWhenReadMoreLinkIsNotFound:
            def test_deleates_to_parse_article(
                self,
                make_spider,
                html_template,
                mocker: MockerFixture,
                url_default,
            ):
                body = html_template(
                    """
                    <a href="./article-001.html">マッチしない</a>
                    """
                )
                response = HtmlResponse(
                    url=url_default, body=body, encoding="utf-8"
                )
                spider = make_spider(read_more="次へ")
                spy = mocker.spy(spider, "parse_article")
                list(spider.parse(response))

                spy.assert_called_once_with(response)

        class TestWhenReadMoreXpathIsGiven:
            def test_yields_request_to_article_page_using_xpath(
                self,
                url_default,
                html_template,
                make_spider,
            ):
                body = html_template(
                    """
                    <div class="special-link">
                      <a href="xpath-article.html">Pick Me</a>
                    </div>
                    """
                )
                response = HtmlResponse(
                    url=url_default, body=body, encoding="utf-8"
                )
                spider = make_spider(
                    read_more_xpath="//div[@class='special-link']/a"
                )
                results = list(spider.parse(response))

                assert results[0].url == f"{url_default}xpath-article.html"

        class TestWhenReadMoreXpatAndReadMoresGiven:
            def test_read_more_is_ignored(
                self,
                url_default,
                html_template,
                make_spider,
            ):
                body = html_template(
                    """
                    <a href="text-link.html">記事全文を読む</a>
                    <div class="special-link">
                      <a href="xpath-article.html">Pick Me</a>
                    </div>
                    """
                )
                response = HtmlResponse(
                    url=url_default, body=body, encoding="utf-8"
                )
                spider = make_spider(
                    read_more="記事全文を読む",
                    read_more_xpath="//div[@class='special-link']/a",
                )
                results = list(spider.parse(response))

                assert results[0].url == f"{url_default}xpath-article.html"

    class TestParseArticle:
        class TestWhenItemIsNone:
            def test_parses_response_and_yields_request_to_next_page(
                self,
                html_template,
                make_spider,
                url_default,
                mocker,
            ):
                spider = make_spider(read_next="次へ")
                body = html_template(
                    """
                    <main>
                      <p>ページ 1</p>
                      <p>本文です。</p>
                    </main>
                    <a href="p2.html">次へ</a>
                    """
                )
                response = HtmlResponse(
                    url=url_default, body=body, encoding="utf-8"
                )
                inner_item = ArticleItem(
                    url=url_default,
                    body="foo bar",
                    acquired_time="now",
                    lang="ja",
                )
                mocker.patch.object(
                    ArticleItem, "from_response", return_value=inner_item
                )

                results = list(spider.parse_article(response, None))

                # yields Request?
                assert len(results) == 1
                result = results[0]
                assert isinstance(result, scrapy.Request)
                # scraped the next page URL?
                assert result.url == f"{url_default}p2.html"

                # with collect args?
                assert result.callback == spider.parse_article
                assert result.cb_kwargs["item"] == inner_item
