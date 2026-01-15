# rokujo-collector-scrapy-generic

A collection of [Scrapy](https://docs.scrapy.org/) spiders designed to crawl
web pages, scrape text content, and generate structured JSONL entries.

These JSONL entries serve as a foundation for further processing, such as
creating collocation databases and assisting in the development of tools for
translators.

Use cases:

- Create a collocation database from web articles.
- Create a database of source and target versions of web articles.
- Create a database of commonly used technical terms by experts.

The spiders are focused, designed to crawl a specific website. They do not
crawl multiple websites. If you are looking for crawlers that crawl the entire
internet, they are not for you.

The spiders collects texts from an article, not images nor links.

## JSONL Data Structure

### ArticleItem

The JSONL data consists of records, each representing an article. Each record
is a JSON object with the following fields:

- `acquired_time`: The time when the webpage was acquired. (Required)
- `author`: The author of the article. (Optional)
- `body`: The main content of the article in XML. (Required)
- `character_count`: The number of characters in the article (not word). (Required)
- `description`: A brief description of the article. (Optional)
- `item_type`: The class name of the item. Automatically set by spiders.
- `kind`: The type or category of the article. (Optional)
- `lang`: The two-letter language code of the article. When the language is undetermined, "und" is returned. (Required)
- `modified_time`: The time when the article was last modified. (Optional)
- `published_time`: The time when the article was published. (Optional)
- `site_name`: The name of the website on which the article was published. (Optional)
- `title`: The title of the article. (Optional)
- `url`: The URL of the article. (Required)

The `lang` field follows the ISO 639-1:2002 standard for language codes, e.g.
`en`, `ja`, etc.

All time fields are in ISO 8601 format, e.g., `2026-01-13T11:12:43.874795+00:00`.

### ArticleWithSourceItem

This class is a subclass of `ArticleItem`. It has the following additional fields:

- `sources`: A list of `ArticleItem`. Each source is a source article of the `ArticleWithSourceItem`.

The class is useful when an article is a translated version and has sources, such as English version.

## Spiders

Arguments are passed from command line to spiders with `-a`:

```console
uv run scrapy crawl -a "arg1=value1" -a "arg2=value2" ${spider_name}

```

All spider accepts a set of common arguments:

- `urls`: Comma-separated list of URLs to start crawling.

### ReadMoreSpider

The `ReadMoreSpider` is a spider designed to extract main articles from
summary pages. It is particularly useful when an RSS feed does not provide a
direct link to the main article but instead points to a landing page.

The spider is versatile and can be used for a single page, a book of multiple
pages with "Next page" links, web articles splitted into multiple pages.

#### Features

- **Summary Page Processing**: The spider processes summary pages that contain
  links to main articles. For example, a summary page might have a link like
  `<a href="main.html">Read more...</a>`.

- **Article Extraction**: The spider supports three scenarios:
  1. **First page -> Main article page**: The spider navigates from the
     summary page to the main article page.
  2. **First page -> Main article page -> Next page(s)**: The spider navigates
     to the main article page and then to subsequent pages within the article.
  3. **First page -> Next page(s)**: The spider processes the fisrt page and
     any subsequent pages.

#### How it works

The spider fetches the start page from the `urls` argument.

When no link with `read_more` text is found, the spider parses the first page
as an article, adding the text to `ArticleItem`.

If the page contains a `read_more` link, the content of the first page is not
included in the `ArticleItem`.

When a `read_next` link is found, the spider navigates to the next page.

When a `read_next` link is not found, the spider finishes crawling and
generates an `ArticleItem`.
