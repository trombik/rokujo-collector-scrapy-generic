# RSS Reader Overview

`rss_reader.py` is a simple RSS reader for spiders.
When feeds have new entries, it crawls the new entries and save the collected ArticleItem in a file.

## Usage

```console
usage: rss_reader.py [-h] [-c CONFIG] [-i INTERVAL] [-d DATABASE] [-o OUTPUT] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Simple RSS reader for rokujo-collector-scrapy

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to RSS feed configuration file
  -i INTERVAL, --interval INTERVAL
                        Update interval in minutes
  -d DATABASE, --database DATABASE
                        Path to RSS feed database
  -o OUTPUT, --output OUTPUT
                        Path to output JSONL file
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Log level, one of choices in upper case or lower case
```

## Configuration file, `rss.yml`

The main configuration file is a YAML file, `rss.yml`. Use `--config` option
to specify the path. The default is `rss.yml` in the current working
directory.

```yaml
---
feed_urls:
  - "https://news.example.org/rss/categories/it.xml"
  - "https://news.example.org/rss/categories/domestic.xml"

rules:
  - name: Example News
    url_pattern: "://news\\.example\\.org/(pickup|articles)/"
    spider_name: read-more
    args:
      - "read_more=記事全文を読む"
      - "read_next=次へ"
```

### `feed_urls`

The is a list of RSS feed URLs.
The RSS reader polls the RSS feeds and crawls new entires in the feeds.
It can be path to a local RSS feed file.
To create a local RSS feed file, use `FeedSpider`.

### `rules`

This is a list of rules for URLs.
When the URL of a unread URL matches `url_pattern`, the RSS reader runs `spider_name` with `args`.
With `rules`, one can run different spiders with different arguments.

| Attribute | Optional or Required | Description |
|-----------|----------------------|-------------|
| `name` | Optional | Name of the feed |
| `url_pattern` | Required | A regular expression to match the URL |
| `spider_name` | Required | The name of spider to run for the matched URLs |
| `args` | Required | A list of arguments to pass to the spider |

### Interval, `--interval`

Interval to poll RSS feeds in minutes. The default is 15 minutes.

### Database, `--database`

Path to RSS database file. When the database file does not exist, the RSS
reader creates one. The database is for maintaining feeds, entries and their
status.

### Log Level, `--loglevel`

The log level of the RSS reader and spiders. The default is `info`.

### Output file, `--output`

The output file to save collected ArticleItem.
The default is `rss.jsonl`.
The RSS reader appends Unix time to the specified filename.
The actual file name is `rss-1769820942.jsonl` for instance.
The output file is atomically created and it is safe to assume that the file is always ready for further processing.
