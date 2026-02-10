# Overview of Spiders

Spiders are programs that crawl websites and collect data.
They are a fundamental tool in web scraping and data extraction.

Spiders collects some kind of data. Either [ArticleItem](generic.items.ArticleItem) or files.

`ArticleItem` is a structured data such as text and metadata.
`ArticleItem` has many attributes, including `body`, which is the scraped text from pages, and metadata, such as title of the article page.

```json
{
  "acquired_time": "2026-01-29T03:18:20.300844+00:00",
  "body": "<main> ... </main>",
  "url": "https://example.org/articles/d74c1662a8cd4ba0146d7f334c3058685320f611",
  "lang": "ja",
  "author": "Someone",
  "description": "A description ... ",
  "kind": "article",
  "modified_time": "2026-01-29T11:05:09+09:00",
  "published_time": "2026-01-29T11:05:09+09:00",
  "site_name": "Foo website",
  "title": "A title ...",
  "item_type": "ArticleItem",
  "character_count": 42,
  "sources": []
}
```

There are several spiders for different purposes.
They are different in two points:

* What they collect
* How they collect the data

Most spiders collect `ArticleItem`, a text article from web pages.
Others collect files, such as PDF files.
For example:

* `read-more` spider collects an article of pages, ignoring a landing page commonly found in news websites.
* `directory` spiders collects `ArticleItem` but only scrapes text of pages under a specific URL path.
* `sitemap` spiders collects `ArticleItem` by following links in `sitemap.xml`.
* `file-download` spider collects files linked in web pages, such as PDF files.

The collected data, or items, are passed to item pipelines for further processing and the items are eventually saved, usually in JSONL format.
The result is a structured JSONL file that can be fed into a database.
The spiders reside under `generic/spiders`.


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
> uv run scrapy list
directory
feed
file-download
read-more
sitemap
...

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

Spiders that collect `ArticleItem` can export the items in various format.
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
