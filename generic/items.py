# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GenericItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ArticleItem(scrapy.Item):
    kind = scrapy.Field()
    text = scrapy.Field()
    title = scrapy.Field()
    site_name = scrapy.Field()
    description = scrapy.Field()
    author = scrapy.Field()
    uri = scrapy.Field()
    created_at = scrapy.Field()
    updated_at = scrapy.Field()
    acquired_at = scrapy.Field()
    text = scrapy.Field()
    meta = scrapy.Field()
