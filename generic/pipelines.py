# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class GenericPipeline:
    def process_item(self, item, spider):
        return item


class DropMissingTextPipeline:
    """
    Drops items without text.
    """

    def process_item(self, item):
        adapter = ItemAdapter(item)
        text = adapter.get("body")
        if text is None or text == "":
            raise DropItem("Missing text")
        return item
