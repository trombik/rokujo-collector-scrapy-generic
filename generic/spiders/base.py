from typing import Generic, List, Type, TypeVar, Union
from urllib.parse import urlparse

import scrapy
from pydantic import (
    BaseModel,
    HttpUrl,
    field_validator,
)
from scrapy_spider_metadata import Args

from generic.utils import idn2ascii


class GenericSpiderConfig(BaseModel):
    urls: Union[HttpUrl, List[HttpUrl]]
    """
    A string of comma-separated URLs or List of URL strings.
    """

    @field_validator("urls", mode="before")
    @classmethod
    def split_urls(cls, v):
        """
        Convert comma-separated URLs to a list of string
        """
        if isinstance(v, str):
            return [url.strip() for url in v.split(",")]
        return v

    @field_validator("urls")
    @classmethod
    def convert_to_string(cls, v):
        """
        Convert HttpUrl object to string after validation.
        """
        if isinstance(v, list):
            return [str(url) for url in v]
        return str(v)


# define generic type, T. T is either GenericSpiderConfig or its subclass.
T = TypeVar("T", bound=GenericSpiderConfig)


class GenericSpider(Args[T], scrapy.Spider, Generic[T]):
    """
    A base spider class that inherits scrapy.Spider.
    """

    allowed_domains = []

    @classmethod
    def get_config_class(cls) -> Type[T]:
        """
        Returns configuration class for the class. The configuration class
        must be either GenericSpiderConfig or its subclass.
        """
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # urls is either str or List[str]
        urls = (
            [self.args.urls]
            if isinstance(self.args.urls, str)
            else self.args.urls
        )

        # allowed_domains does not support IDN. fix it up.
        domains = []
        for url in urls:
            domains.append(urlparse(idn2ascii(url)).netloc)
        unique_domains = list(set(domains))
        self.allowed_domains.extend(unique_domains)
        self.logger.debug(f"allowed_domains: {self.allowed_domains}")
