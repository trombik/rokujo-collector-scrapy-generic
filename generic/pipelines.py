# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from generic.items import FeedItem


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


class FeedStoragePipeline:
    """
    Save FeedItem on local disk.
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if isinstance(item, FeedItem):
            file_name = adapter.get("file_name")
            content = adapter.get("content")
            if file_name and content:
                try:
                    file_path = Path(file_name).resolve()
                    file_path.write_text(content, encoding="utf-8")
                    spider.logger.info(f"Saved: {file_path}")
                except Exception as e:
                    raise DropItem(
                        f"failed to save file at: {file_path}\n"
                        f"{e}\n"
                    )
            else:
                raise DropItem(
                    "file_name and content must be present:\n"
                    f"file_name: {file_name}\n"
                    f"content: {content}\n"
                )
        return item
