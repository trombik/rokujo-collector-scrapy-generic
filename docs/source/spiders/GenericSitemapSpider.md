# GenericSitemapSpider

A spider that scrapes all the articles within `sitemap.xml`.
The sitemap.xml may contain other `sitemap.xml` (nested `sitemap.xml`).

The spider crawls almost entire sites and suitable for relatively small sites.
Do not use this spider when the site is large one.
In addition, scraped ArticleItem would contains noises.
If you prefer quality over quantity, use other focused spiders.

When `urls` argument includes a URL that does not end with `sitemap.xml`, the spider appends `sitemap.xml` to the URL.

## Usage

```console
uv run scrapy crawl -a "urls=http://example.org/" sitemap
```

The spider accepts an argument, `sitemap_type`.
By default, the spider crawls all the links in `sitemap.xml`.
When `sitemap_type` is `wordpress`, the spider skips certain URLs known to be useless pages, such as index pages of tags or categories.

```console
uv run scrapy crawl -a "urls=http://example.org/" -a "sitemap_type=wordpress" sitemap
```

## How It Works

1. The spider fetches `sitemap.xml`.
1. It parses the XML file and extract all the links.
1. If the file contains links to other `sitemap.xml`, the spider recursively parses other `sitemap.xml`.
1. It crawls all the links and collects ArticleItem.
