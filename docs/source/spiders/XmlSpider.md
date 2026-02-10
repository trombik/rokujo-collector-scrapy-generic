# XmlSpider

A spider that scrapes ArticleItem from links in an XML file.
The spider is useful when a list of links is in a dynamic XML response and the browser renders the list.

## Usage

In addition to `urls`, `xml_link_xpath` is required.

```console
uv run scrapy -a "urls=http://example.org/latest.xml" -a "xml_link_xpath=//link/text()" xml
```

## How It Works

The spider:

* fetches the XML file
* parses the file and extract URLs with the given XPath expression
* generates ArticleItem

Although the spider can be used to collect ArticleItem from RSS feeds (they are XML), `feed` spider does a better job for that purpose.
