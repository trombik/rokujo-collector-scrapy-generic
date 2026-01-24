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
    author = res.xpath("//meta[@name='author']/@content").get()

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
        "kind": (og.get("og:type") or og.get("@type") or ld.get("@type")),
        "author": (
            author
            or og.get("og:author")
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
            og.get("og:description") or (ld.get("description") or "") or None
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


def generate_hashed_filename(
    url,
    domain_size: int = 8,
    url_size: int = 32,
    max_len: int = 255,
) -> str:
    """
    Generate a safe filename with a hashed prefix, keeping the file name
    human-friendly but sortable by URL-relevance.

    Supports URL-encoded file name.

    The generated file name is hashed by domain and path of the URL.

    The length of the generated file name is ensured to be less or equals to
    max_len.

    Args:
        domain_size: The size of domain hash characters.
        url_size: The size of URL hash characters.
        max_len: Max allowed bytes in file names. Defaults to 255.
    """
    import os
    from hashlib import shake_128
    from urllib.parse import unquote, urlparse

    from pathvalidate import sanitize_filename

    parsed = urlparse(url)
    domain = parsed.netloc

    raw_path = unquote(parsed.path)
    basename = os.path.basename(raw_path) or "index"

    root, ext = os.path.splitext(basename)
    ext = sanitize_filename(
        filename=ext,
        max_len=10,
    )

    domain_hash = shake_128(domain.encode()).hexdigest(domain_size // 2)
    url_hash = shake_128(url.encode()).hexdigest(url_size // 2)

    prefix = f"{domain_hash}-{url_hash}-"
    prefix_len = len(prefix.encode("utf-8"))
    ext_len = len(ext.encode("utf-8"))
    allowed_max_len_for_root = max_len - prefix_len - ext_len
    if allowed_max_len_for_root <= 0:
        raise ValueError(
            "domain_size and/or url_size too big. "
            "Reduce domain_size and/or url_size.\n"
            f"max_len: {max_len}\n"
            f"domain_size: {domain_size}\n"
            f"url_size: {url_size}\n"
        )

    root = sanitize_filename(
        filename=root,
        max_len=allowed_max_len_for_root,
    )
    return f"{prefix}{root}{ext}"


def is_path_matched(url: str, regexp: str) -> bool:
    if not url or not regexp:
        return False

    import re
    from urllib.parse import unquote, urlparse

    parsed_path = urlparse(url).path
    path = unquote(parsed_path) if parsed_path else "/"

    return bool(re.search(regexp, path))


def is_file_url(
    url: str, regexp: str = r"(?:/|\.html?|\.php|\.aspx?|/[^./]+)$"
) -> bool:
    """
    Returns bool whether if the givne url is a URL to a file, not HTML page.
    """
    if not url:
        return False

    return not is_path_matched(url, regexp)
