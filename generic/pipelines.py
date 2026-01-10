# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from dateutil import parser
from datetime import datetime, timezone


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


class DateStringConverterPipeline:
    """
    Ensures time attributes are a string in ISO 8601 format.
    """

    def process_item(self, item, spider):
        keys = {"published_time", "acquired_time", "modified_time"}
        adapter = ItemAdapter(item)
        for key in keys:
            value = adapter.get(key)
            try:
                adapter[key] = self._ensure_iso_format(value)
            except Exception:
                spider.logger.error(
                    f"Failed to _ensure_iso_format: value={value}"
                )
                raise DropItem
        return item

    def _ensure_iso_format(self, dt_input):
        """
        Ensure the given input is a string in ISO 8601 format.
        """
        if dt_input is None:
            return None

        if isinstance(dt_input, datetime):
            dt = dt_input
        else:
            dt = parser.parse(str(dt_input))

        return dt.astimezone(timezone.utc).isoformat()
