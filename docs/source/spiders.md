# Spiders

Spiders are programs that crawl websites and collect data.
They are a fundamental tool in web scraping and data extraction.

Spiders collects some kind of data. Either [ArticleItem](generic.items.ArticleItem) or files.

`ArticleItem` is a structured data such as text and metadata.
`ArticleItem` has many attributes, including `body`, which is the scraped text from pages, and metadata, such as title of the article page.

The spiders reside under `generic/spiders`.

```{toctree}
:maxdepth: 2
:caption: Contents

spiders/ReadMoreSpider
spiders/ArchiveSpider
spiders/FeedSpider
```

## Name

A spider has three names:

* Human-friendly name, e.g., `read-more`
* File name, e.g., `read_more.py` (under `generic/spiders` directory)
* Python class name, e.g., `ReadMoreSpider`

When running a spider from command line, use human-friendly name.
Human-friendly name is defined as a class variable.

```python
# generic/spiders/read_more.py

class ReadMoreSpider(GenericSpider[ReadMoreSpiderConfig], ReadMoreMixin):
    # ...
    name = "read-more"
```

`scrapy list` command displays a list of all available spiders.

```console
uv run scrapy list
```

## Arguments

Spiders accepts arguments. Arguments are passed with `-a` option.

```console
uv run scrapy crawl -a "arg1=value1" -a "arg2=value2" $SPIDER_NAME
```

```{caution}
Always quote the arguments.
```

### Common arguments

All spiders require a mandatory argument, `urls`. `urls` is where spiders start crawling.

The value of `urls` is a comma-separated list of URLs.

```console
uv run scrapy crawl -a "urls=http://example.org/,http://example.net/" read-more
```

Spiders apply the same arguments to multiple URLs. If different URLs need different arguments, run the spider multiple times with different arguments.

```console
uv run scrapy crawl -a "urls=http://example.org/" -a "arg=value1" read-more
uv run scrapy crawl -a "urls=http://example.net/" -a "arg=value2" read-more
```

## Output options

Spiders that collects `ArticleItem` can export the items in various format.
JSONL is the most recommended one.
`-O` and `-o` option specify the output file name and the format.
`-O` overwrites the specified file with the collected items while `-o` appends new items to the file.

```console
# -O overwrites and delete old items in the file
uv run scrapy crawl -a "urls=http://example.org/" -O items.jsonl read-more

# -o appends new items, preserving the existing items in the file
uv run scrapy crawl -a "urls=http://example.org/" -o items.jsonl read-more

# scrapy supports CSV format, too
uv run scrapy crawl -a "urls=http://example.org/" -o items.csv read-more
```

Spiders that collects files requires `output_dir` argument.
