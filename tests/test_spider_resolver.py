import pytest

from generic.spider_resolver import (
    SpiderResolver,
    SpiderResolverConfig,
    SpiderResolverNoRouteError,
    SpiderResolverRoute,
)


@pytest.fixture
def sample_resolver():
    route1 = SpiderResolverRoute(
        patterns=[r"https://example\.org"],
        spider_name="foo_spider",
        args=["arg1=value1", "arg2=value2"],
    )
    route2 = SpiderResolverRoute(
        patterns=[r"https://example\.net"],
        spider_name="foo_spider",
        args=["arg1=value1", "arg2=value2"],
    )
    route3 = SpiderResolverRoute(
        patterns=[r"https://example\.com"], spider_name="bar_spider", args=[]
    )
    config = SpiderResolverConfig(routes=[route1, route2, route3])
    return SpiderResolver(config)


@pytest.mark.parametrize(
    "url, expected_name, expected_args",
    [
        (
            "https://example.org/foo/bar",
            "foo_spider",
            ["arg1=value1", "arg2=value2"],
        ),
        ("https://example.net", "foo_spider", ["arg1=value1", "arg2=value2"]),
        ("https://example.com", "bar_spider", []),
    ],
)
def test_routees_matche_a_url(
    sample_resolver, url, expected_name, expected_args
):
    name, args = sample_resolver.resolve(url)

    assert name == expected_name
    assert args == expected_args


def test_resolve_raises_exception_when_no_match():
    config = SpiderResolverConfig(routes=[])
    resolver = SpiderResolver(config)
    url = "https://example.com/foo/bar"

    with pytest.raises(SpiderResolverNoRouteError):
        resolver.resolve(url)


def test_specific_rule_match_first():
    route_specific = SpiderResolverRoute(
        patterns=[r"/specific"],
        spider_name="specific",
    )
    route_generic = SpiderResolverRoute(
        patterns=[r"/.*"],
        spider_name="generic",
    )
    config = SpiderResolverConfig(routes=[route_specific, route_generic])
    resolver = SpiderResolver(config)
    url = "https://example.org/specific"
    spider, _ = resolver.resolve(url)

    assert spider == "specific"
