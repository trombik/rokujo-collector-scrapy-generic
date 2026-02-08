import os
from urllib.parse import quote

import pytest

from generic.utils import (
    generate_hashed_filename,
    get_url_without_fragment,
    is_file_url,
    is_path_matched,
)


class TestGenerateHashedFilename:
    def test_basic_functionality(self):
        url = "https://example.org/files/report.pdf"
        domain_size = 8
        url_size = 32
        filename = generate_hashed_filename(
            url=url,
            domain_size=domain_size,
            url_size=url_size,
        )

        parts = filename.split("-")
        assert len(parts) >= 3
        assert filename.endswith(".pdf")
        assert len(parts[0]) == domain_size
        assert len(parts[1]) == url_size

    def test_japanese_filename_decoding(self):
        unquoted_string = "報告書"
        quoted_string = quote(unquoted_string)
        url = f"https://example.org/{quoted_string}.pdf"
        filename = generate_hashed_filename(url)

        assert filename.endswith(f"{unquoted_string}.pdf")

    def test_forbidden_characters_replacement(self):
        url = "https://example.org/path/with/invalid:char*?.pdf"
        filename = generate_hashed_filename(url)

        root_part = filename.split("-")[-1]
        assert ":" not in root_part
        assert "*" not in root_part
        assert "?" not in root_part

    def test_max_len_truncation(self):
        max_len = 100
        long_name = "あ" * 256
        url = f"https://example.org/{long_name}.pdf"
        filename = generate_hashed_filename(url=url, max_len=max_len)

        assert len(filename.encode("utf-8")) == max_len
        assert filename.endswith(".pdf")

    def test_empty_path_fallback(self):
        url = "https://example.org/"
        filename = generate_hashed_filename(url)

        assert filename.endswith("index")

    def test_value_error_on_invalid_sizes(self):
        url = "https://example.org/test.pdf"
        with pytest.raises(ValueError):
            generate_hashed_filename(url, domain_size=150, url_size=150)

    def test_domain_hash_consistency(self):
        url1 = "http://example.org/a.pdf"
        url2 = "http://example.org/b.pdf"
        filename1 = generate_hashed_filename(url1)
        filename2 = generate_hashed_filename(url2)
        domain_hash1 = filename1.split("-")[0]
        domain_hash2 = filename2.split("-")[0]

        assert domain_hash1 == domain_hash2

    def test_ext_is_safe_filename(self):
        ext = ".*foo"
        url = f"http://example.org/file{ext}"
        filename = generate_hashed_filename(url)
        _, generated_ext = os.path.splitext(filename)

        assert generated_ext == ".foo"

    def test_max_len_truncation_with_ext(self):
        max_hardcoded_ext_len = 10
        long_name = "あ" * 256
        url = f"https://example.org/foo.{long_name}"
        filename = generate_hashed_filename(url=url)
        _, generated_ext = os.path.splitext(filename)

        assert len(generated_ext.encode("utf-8")) == max_hardcoded_ext_len


class TestIsPathMatched:
    @pytest.mark.parametrize(
        "url, regexp, expected",
        [
            ("https://example.org/test.pdf", r"\.pdf$", True),
            ("https://example.org/test.PDF", r"\.pdf$", False),
            # ignore case pattern
            ("https://example.org/test.PDF", r"(?i)\.pdf$", True),
            # queries should not be included
            ("https://example.org/test.pdf?v=1.2", r"\.pdf$", True),
            ("https://example.org/test.pdf?file=other.jpg", r"\.jpg$", False),
            # handles slashes
            ("https://example.org/foo/bar/baz.pdf", r"^/foo/bar/", True),
            ("https://example.org/foo/barbuz/baz.pdf", r"^/foo/bar/", False),
            # handles URL encoded path
            (
                "https://example.org/%E5%A0%B1%E5%91%8A.pdf",
                r"報告\.pdf$",
                True,
            ),
            # does not match against domain part
            ("https://pdf.example.org/index.html", r"\.pdf$", False),
            # handles empth path
            ("https://example.org", r"^/$", True),
            ("https://example.org/", r"^/$", True),
            # handles None in arguments
            ("", r".*", False),
            (None, r".*", False),
        ],
    )
    def test_is_path_matched(self, url, regexp, expected):
        assert is_path_matched(url, regexp) == expected


class TestIsFileUrl:
    @pytest.mark.parametrize(
        "url, expected_is_file",
        [
            ("https://example.org/doc.pdf", True),
            ("https://example.org/image.png", True),
            ("https://example.org", False),
            ("https://example.org/", False),
            ("https://example.org/about_us", False),
            ("https://example.org/index.html", False),
        ],
    )
    def test_is_file_url(self, url, expected_is_file):
        assert is_file_url(url) == expected_is_file


class GetUrlWithoutFragment:
    @pytest.mark.parametrize(
        "input_url, expected",
        [
            (
                "https://example.org/page#main-article",
                "https://example.org/page",
            ),
            ("https://example.org/page#section-1", "https://example.org/page"),
            (
                "https://example.org/page?query=1#hash",
                "https://example.org/page?query=1",
            ),
            ("https://example.org/page", "https://example.org/page"),
            ("", ""),
        ],
    )
    def test_get_unique_url(self, input_url, expected):
        assert get_url_without_fragment(input_url) == expected

    def test_url_uniqueness_with_set(self):
        """複数の実質的に同じURLが、setによって1つに集約されることをテスト"""
        urls = [
            "https://example.org/article/1#intro",
            "https://example.org/article/1#main",
            "https://example.org/article/1",
        ]
        unique_urls = {get_url_without_fragment(u) for u in urls}

        assert len(unique_urls) == 1
        assert list(unique_urls)[0] == "https://example.org/article/1"
