import extruct
from dateutil import parser
from scrapy.http import Response


def get_meta_property(response: Response, name: str) -> str:
    """
    Extracts a meta property content from a response.

    Args:
        - response The response object.
        - name Name of the property.
    """
    path = f"//meta[@property='{name}']/@content"
    return response.xpath(path).get()


def extract_article(res: Response) -> dict:
    """
    Extracts an article, or the relevant texts in the Response, with
    trafilatura.

    Returns a dict. The dict has various metadata extracted from the Response.

    Args:
        - res The response object

    """
    import json

    from trafilatura import extract

    metadata = get_metadata(res)
    return json.loads(
        extract(
            res.text,
            url=res.url,
            with_metadata=True,
            target_language=metadata["lang"],
            output_format="json",
        )
    )


def idn2ascii(url_str: str) -> str:
    """
    Returns ascii URL from a URL containing IDN.
    """
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url_str.strip())
    puny_host = parsed.netloc.encode("idna").decode("ascii")
    new_parsed = parsed._replace(netloc=puny_host)
    return urlunparse(new_parsed)


def get_uniform_metadata(
    html: str,
    base_url: str,
):
    syntaxes = ["json-ld", "opengraph"]

    return extruct.extract(
        html,
        base_url=base_url,
        syntaxes=syntaxes,
        uniform=True,
    )


def str_to_isoformat(string: str):
    if str is None:
        return None
    try:
        dt = parser.parse(string)
        return dt.isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def get_metadata(res: Response) -> dict:
    """
    Generate metadata from Response.

    Returns: dict
    """
    data = get_uniform_metadata(res.text, res.url)

    og_list = data.get("opengraph", [])
    og = og_list[0] if og_list else {}

    ld_raw_list = data.get("json-ld", [])
    ld_raw = ld_raw_list[0] if ld_raw_list else {}

    ld = (
        ld_raw.get("@graph", [ld_raw])[0]
        if isinstance(ld_raw.get("@graph"), list)
        else ld_raw
    )

    def dig(d, *keys):
        for k in keys:
            d = d.get(k) if isinstance(d, dict) else None
        return d

    def locale_to_lang(locale) -> str:
        """
        Convert locale string to two-letter language code, e.g., from "ja-JP"
        to "ja".
        """
        if locale is None:
            return None

        return locale.split("-")[0]

    return {
        "url": (
            og.get("og:url")
            or ld.get("url")
            or dig(ld, "mainEntityOfPage", "@id")
            or res.url
        ),
        "title": (
            og.get("og:title")
            or ld.get("headline")
            or res.xpath("//title/text()").get()
        ),
        "lang": (locale_to_lang(res.xpath("/html/@lang").get()) or None),
        "site_name": (og.get("og:site_name") or dig(ld, "publisher", "name")),
        "kind": (og.get("og:type") or ld.get("@type")),
        "author": (
            og.get("og:author")
            or dig(ld, "author", "name")
            or dig(ld, "author", 0, "name")
        ),
        "modified_time": str_to_isoformat(
            og.get("article:modified_time") or ld.get("dateModified")
        ),
        "published_time": str_to_isoformat(
            og.get("article:published_time") or ld.get("datePublished")
        ),
        "description": (
            og.get("og:description")
            or (ld.get("description") or "")
            or None
        ),
    }


def count_xml_character(xml_string: str) -> int:
    """
    Count characters in XML string, excluding spaces (not words).
    """
    import re

    from scrapy import Selector

    sel = Selector(text=xml_string, type="xml")
    texts = sel.xpath("//text()").getall()
    full_text = "".join(texts)
    clean_text = re.sub(r"\s+", "", full_text)
    return len(clean_text)
