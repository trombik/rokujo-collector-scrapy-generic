import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class SpiderResolverRoute:
    patterns: List[str]
    """
    A list of regular expressions as string. The list is evaluated in order
    and when one matches the URL, the `spider_name` is returned. the first
    match wins.

    """
    spider_name: str
    """
    The name of the spider to use when `patterns` matches.
    """

    args: List[str] = field(default_factory=list)
    """
    Arguments to pass spiders. Normally, a "key=value" pair.
    """


@dataclass
class SpiderResolverConfig:
    routes: List[SpiderResolverRoute]


class SpiderResolver:
    def __init__(self, config: SpiderResolverConfig):
        """
        The constructor.
        """
        self.config = config

    def resolve(self, url: str) -> tuple[str, List[str]]:
        """
        Resolve the spider to use.
        """

        for route in self.config.routes:
            for pattern in route.patterns:
                if re.search(pattern, url):
                    return route.spider_name, route.args
        raise SpiderResolverNoRouteError(url, self.config.routes)


class SpiderResolverError(Exception):
    """The base Exception class for SpiderResolver class."""

    pass


class SpiderResolverNoRouteError(SpiderResolverError):
    """
    Raised when no routes match the URL.
    """

    def __init__(self, url: str, routes):
        self.url = url
        super().__init__(
            f"No routes matches URL: {url}\nroutes:\n{routes}\n"
        )
