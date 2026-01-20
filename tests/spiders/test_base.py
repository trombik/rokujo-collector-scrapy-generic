import re
import types

import pytest
from pydantic import ValidationError

from generic.spiders.base import GenericSpider, GenericSpiderConfig

VALID_URL_PARAMS = pytest.mark.parametrize(
    "valid_url",
    [
        "http://127.0.0.1/path/",
        "http://localhost/path/",
        "http://[fe80::a1b3:125d:c1f8:4781]:8080/path/",
        "http://user@password@example.org:8080/path/?query=string",
    ]
)
INVALID_URL_PARAMS = pytest.mark.parametrize(
    "invalid_url",
    [
        "",
        " ",
        "\u3000",
        "invalid",
        0,
        1,
        -1,
        None,
        True,
        False,
        {},
        "ttp://example.org",
        "://example.org",
        "file:///foo/bar",
        "mailto:foo.example.org",
        "ftp://example.org/",
    ],
)


class TestGenericSpiderConfig:
    def test_urls_accepts_empty_list(self):
        urls = []
        config = GenericSpiderConfig(urls=urls)

        assert config.urls == []

    def test_urls_is_a_list_of_string(self):
        urls = "http://example.org"
        config = GenericSpiderConfig(urls=urls)

        assert all(isinstance(url, str) for url in config.urls)

    @INVALID_URL_PARAMS
    def test_given_invalid_input_raise_exception(self, invalid_url):
        with pytest.raises(ValidationError):
            GenericSpiderConfig(urls=invalid_url)
        with pytest.raises(ValidationError):
            GenericSpiderConfig(urls=[invalid_url])

    @VALID_URL_PARAMS
    def test_given_invalid_input_not_to_raise_exception(self, valid_url):
        try:
            GenericSpiderConfig(urls=valid_url)
        except ValidationError:
            pytest.fail("Expected not to raise ValidationError but raised")
        try:
            GenericSpiderConfig(urls=[valid_url])
        except ValidationError:
            pytest.fail("Expected not to raise ValidationError but raised")

    def test_split_urls_splits_input(self):
        urls = ",".join(
            ["http://example.org\u3000 ", " \u3000http://example.net"]
        )
        config = GenericSpiderConfig(urls=urls)

        assert len(config.urls) == 2

    def test_split_urls_strips_spaces(self):
        urls = ",".join(
            ["http://example.org\u3000 ", " \u3000http://example.net"]
        )
        config = GenericSpiderConfig(urls=urls)

        assert all(not re.search(r"\s", url) for url in config.urls)


class TestGenericSpider:
    @pytest.fixture
    def spider_cls(self):
        cls = types.new_class(
            "UniqueSpider", (GenericSpider[GenericSpiderConfig],)
        )
        cls.name = "foo"
        cls.allowed_domains = []
        return cls

    def test_get_config_class_raises(self, spider_cls):
        spider = spider_cls(urls=[])

        with pytest.raises(NotImplementedError):
            spider.get_config_class()

    def test_accepts_idn_domains(self, spider_cls):
        urls = ["http://日本語.example.org/"]
        spider = spider_cls(urls=urls)

        assert spider.urls == urls

    def test_allowed_domains_has_same_length(self, spider_cls):
        urls = ["http://日本語.example.org/"]
        spider = spider_cls(urls=urls)

        assert len(spider.allowed_domains) == len(urls)

    def test_allowed_domains_is_in_ascii(self, spider_cls):
        urls = ["http://日本語.example.org/"]
        spider = spider_cls(urls=urls)

        assert "xn--wgv71a119e.example.org" in spider.allowed_domains

    def test_accepts_empty_urls(self, spider_cls):
        urls = []
        spider = spider_cls(urls=urls)

        assert spider.urls == []
        assert spider.allowed_domains == []

    @INVALID_URL_PARAMS
    def test_validate_urls_and_raise_exception(self, spider_cls, invalid_url):
        with pytest.raises(ValidationError):
            spider_cls(urls=invalid_url)
        with pytest.raises(ValidationError):
            spider_cls(urls=[invalid_url])

    @VALID_URL_PARAMS
    def test_validate_urls_and_not_to_raise_exception(
            self, spider_cls, valid_url
    ):
        try:
            spider_cls(urls=valid_url)
        except ValidationError:
            pytest.fail("Expected not to raise ValidationError but raised")
        try:
            spider_cls(urls=[valid_url])
        except ValidationError:
            pytest.fail("Expected not to raise ValidationError but raised")


class MockSpider(GenericSpider[GenericSpiderConfig]):
    name = "mock_spider"

    @classmethod
    def get_config_class(cls):
        return GenericSpiderConfig


def test_allowed_domains_isolation():
    config1 = GenericSpiderConfig(urls="https://first.example.org")
    spider1 = MockSpider(**vars(config1))

    config2 = GenericSpiderConfig(urls="https://second.example.org")
    spider2 = MockSpider(**vars(config2))

    assert spider1.allowed_domains == ["first.example.org"]
    assert spider2.allowed_domains == ["second.example.org"]
