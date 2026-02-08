# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


import io
from pathlib import Path

import pikepdf
import scrapy
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from generic.items import ArticleItem, FeedItem, FileItem


class GenericPipeline:
    def process_item(self, item, spider):
        return item


class DropMissingTextPipeline:
    """
    Drops items without text.
    """

    def process_item(self, item):
        if not isinstance(item, ArticleItem):
            return item

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
        if not isinstance(item, FeedItem):
            return item

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
                        f"failed to save file at: {file_path}\n{e}\n"
                    )
            else:
                raise DropItem(
                    "file_name and content must be present:\n"
                    f"file_name: {file_name}\n"
                    f"content: {content}\n"
                )
        return item


class FileItemPipeline:
    """
    Process FileItem. This pipeline should be placed before
    FileItemStoragePipeline.

    This pipeline expects FileItem to have `filename` with a proper file
    extention.

    The purpose of the pipeline is:

    * Generate a unique, hashed file name.
    * Process FileItems if necessary, e.g., adding contexts or metadata to the
      FileItem.
    """

    def process_item(self, item: FileItem, spider: scrapy.Spider) -> FileItem:
        """
        Process FileItem.

        1. Call a specific method to process the FileItem.
        2. Generate a unique, hashed file name
        3. Create a new FileItem with the generated file name.
        """
        if not isinstance(item, FileItem):
            return item

        import os

        from generic.utils import generate_hashed_filename

        adapter = ItemAdapter(item)
        filename = adapter.get("filename")
        if not filename:
            raise DropItem("Failed to process FileItem: missing filename")

        _, ext = os.path.splitext(adapter.get("filename", "").lower())
        if ext == "":
            raise DropItem(
                "filename does not have an extention: ",
                f"{adapter.get('filename')}",
            )

        try:
            match ext:
                case ".pdf":
                    spider.logger.debug(f"Processing PDF file: {filename}")
                    new_item = self.process_pdf_item(item, spider).deepcopy()
                case _:
                    spider.logger.debug(
                        f"No additional processing required: {filename}"
                    )
                    new_item = item.deepcopy()
        except Exception as e:
            raise DropItem(f"Failed to process FileItem: {e}")

        try:
            new_item["filename"] = generate_hashed_filename(
                new_item.get("url")
            )
        except Exception as e:
            raise DropItem(f"generate_hashed_filename: {e}")
        return new_item

    def process_pdf_item(
        self,
        item: FileItem,
        spider: scrapy.Spider,
    ) -> FileItem:
        """
        Process PDF FileItem.

        1. Adding metadata to the PDF
        """

        adapter = ItemAdapter(item)
        try:
            with pikepdf.open(io.BytesIO(adapter.get("content"))) as pdf:
                pdf.docinfo["/FileURL"] = adapter.get("url") or ""
                pdf.docinfo["/OriginalFilename"] = (
                    adapter.get("filename") or ""
                )

                meta = adapter.get("metadata")
                if meta:
                    pdf.docinfo["/AcquiredTime"] = adapter.get(
                        "acquired_time"
                    ) or ""
                    pdf.docinfo["/SourceURL"] = meta.get("url") or ""
                    pdf.docinfo["/SourceSiteName"] = (
                        meta.get("site_name") or ""
                    )
                    pdf.docinfo["/SourceDescription"] = (
                        meta.get("description") or ""
                    )
                    pdf.docinfo["/SourceTitle"] = meta.get("title") or ""
                    pdf.docinfo["/SourceAuthor"] = meta.get("author") or ""

                with pdf.open_metadata() as xmp:
                    xmp["AcquiredTime"] = adapter.get("acquired_time") or ""
                    xmp["FileURL"] = (adapter.get("url")) or ""
                    xmp["OriginalFilename"] = adapter.get("filename") or ""

                    if meta:
                        xmp["SourceURL"] = meta.get("url") or ""
                        xmp["SourceSiteName"] = meta.get("site_name") or ""
                        xmp["SourceDescription"] = (
                            meta.get("description") or ""
                        )
                        xmp["SourceTitle"] = meta.get("title") or ""
                        xmp["SourceAuthor"] = meta.get("author") or ""
                output_stream = io.BytesIO()
                pdf.save(output_stream)
                adapter["content"] = output_stream.getvalue()
        except Exception as e:
            spider.logger.error(f"Failed to process PDF: {e}", exc_info=True)
            raise DropItem(f"Failed to process PDF: {e}")

        return item


class FileItemStoragePipeline:
    """
    Save FileItem on local disk. This pipeline should be at the end of
    ITEM_PIPELINES.
    """

    def process_item(self, item, spider):
        if not isinstance(item, FileItem):
            return item

        adapter = ItemAdapter(item)

        if not adapter.get("content"):
            raise DropItem("Missing item.content")

        if adapter.get("filename") and adapter.get("output_dir"):
            try:
                filename = adapter.get("filename")
                output_dir = adapter.get("output_dir")

                file_path = (Path(output_dir) / filename).resolve()
                file_path.write_bytes(adapter.get("content"))
                spider.logger.info(f"Saved: {file_path}")
            except Exception as e:
                raise DropItem(
                    f"failed to save file:\n"
                    f"filename: {filename}\n"
                    f"output_dir: {output_dir}\n"
                    f"{e}\n"
                )
        else:
            raise DropItem(
                f"Missing filename or output_dir\n"
                f"filename: {adapter.get('filename')}\n"
                f"output_dir: {adapter.get('output_dir')}\n"
            )
