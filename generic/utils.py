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
    Build ArticleItem from Response and a dict of article returned by
    extract_article().
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    title = extracted.get("title", None)
    author = extracted.get("author", None)
    extracted_date = extracted.get("date", None)
    extracted_date = extracted_date if extracted_date == "" else None
    text = extracted.get("text", None)
    extracted_time = (
        datetime.fromisoformat(extracted_date) if extracted_date else None
    )

    site_name = get_meta_property(response, "og:site_name")
    description = get_meta_property(response, "og:description")
    kind = get_meta_property(response, "og:type")
    published_time = (
        get_meta_property(response, "article:published_time") or extracted_time
    )
    modified_time = (
        get_meta_property(response, "article:modified_time") or published_time
    )

    item = ArticleItem(
        kind=kind,
        site_name=site_name,
        description=description,
        title=title,
        author=author,
        uri=response.url,
        created_at=published_time,
        updated_at=modified_time,
        acquired_at=now,
        text=text,
    )
    return item


def idn2ascii(url_str: str) -> str:
    """
    Returns ascii URL from a URL containing IDN.
    """
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url_str.strip())
    puny_host = parsed.netloc.encode("idna").decode("ascii")
    new_parsed = parsed._replace(netloc=puny_host)
    return urlunparse(new_parsed)
