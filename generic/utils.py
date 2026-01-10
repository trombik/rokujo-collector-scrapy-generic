from scrapy.http import Response

from generic.items import ArticleItem


def get_meta_property(response: Response, name: str) -> str:
    """
    Extracts a meta property content from a response.

    Args:
        - response The response object.
        - name Name of the property.
    """
    path = f"//meta[@property='{name}']/@content"
    return response.xpath(path).get()


def extract_article(res: Response, lang: str = "ja") -> dict:
    """
    Extracts an article, or the relevant texts in the Response, with
    trafilatura.

    Returns a dict. The dict has various metadata extracted from the Response.

    Args:
        - res The response object
        - lang Two-letter code of the language.

    """
    import json

    from trafilatura import extract

    return json.loads(
        extract(
            res.text,
            url=res.url,
            with_metadata=True,
            target_language=lang,
            output_format="json",
        )
    )


def extract_item(response: Response, extracted: dict) -> ArticleItem:
    """
    Build ArticleItem from Response
    """
    return ArticleItem.from_response(response)


def idn2ascii(url_str: str) -> str:
    """
    Returns ascii URL from a URL containing IDN.
    """
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url_str.strip())
    puny_host = parsed.netloc.encode("idna").decode("ascii")
    new_parsed = parsed._replace(netloc=puny_host)
    return urlunparse(new_parsed)
