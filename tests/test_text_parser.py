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
