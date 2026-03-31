import pytest

from generic.utils.text_parser import ArticleTextParser


@pytest.fixture
def parser():
    return ArticleTextParser()


@pytest.mark.parametrize(
    "html_input, expected_sentences",
    [
        (
            "<main><p>これは第1文です。これは第2文です。</p></main>",
            ["これは第1文です。", "これは第2文です。"],
        ),
        (
            '<main><p>神戸村に位置する<hi rend="#sup">[1]</hi>居留地である。</p></main>',  # noqa E501
            ["神戸村に位置する居留地である。"],
        ),
        (
            "<main>短い<p>本文</p>神戸外国人居留地<p>本文2</p></main>",
            ["本文", "神戸外国人居留地", "本文2"],
        ),
        (
            "<main>歴史について[編集]<p>1868年に開港した</p></main>",
            ["歴史について", "1868年に開港した"],
        ),
        (
            "<main><p>開始</p><table><tr><td>消える文字</td></tr></table><pre>code</pre><p>終了</p></main>",  # noqa E501
            ["開始", "終了"],
        ),
        (
            '<main><p><hi rend="#b">神戸</hi>は港町です。</p></main>',
            ["神戸は港町です。"],
        ),
        ("<main><p><code>Code</code></p></main>", ["Code"]),
        (
            '<main><p>改行で\n\n  区切られた文章。</p></main>',
            ["改行で区切られた文章。"]
        ),
        (
            "<main><p>彼は「それは本当か」と言った[1][2]。</p></main>",
            ["彼は「それは本当か」と言った。"]
        ),
        (
            "<main><p>ヘディングの編集は削除される[編集]</p></main>",
            ["ヘディングの編集は削除される"]
        ),
        (
            "<main><p>1905年（明治38年）には「皇帝陛下御賞盃」[注 9]、1906年（明治39年）には「宮中御賞盃」と訳され[4]、1907年（明治40年）からは新聞報道で使われていた「帝室御賞典」の訳で統一されるようになった（後述）[4][22]。 </p></main>", # noqa E501
            ["1905年(明治38年)には「皇帝陛下御賞盃」、1906年(明治39年)には「宮中御賞盃」と訳され、1907年(明治40年)からは新聞報道で使われていた「帝室御賞典」の訳で統一されるようになった(後述)。"] # noqa E501
        ),
        (
            "<main><p>文末のISBNは削除される。ISBN 978-4-12-102052-9</p></main>", # noqa E501
            ["文末のISBNは削除される。"]
        ),
        (
            "<main><p>^Wikipedia 特有の出典は削除される。</p></main>",
            []
        ),
    ],
)
def test_parse_logic(parser, html_input, expected_sentences):
    results = parser.parse(html_input)
    assert results == expected_sentences


def test_empty_input(parser):
    assert parser.parse("") == []
    assert parser.parse(None) == []


def test_no_main_tag(parser):
    html = "<p>タグの外の文</p>"
    results = parser.parse(html)
    assert "タグの外の文" in results
