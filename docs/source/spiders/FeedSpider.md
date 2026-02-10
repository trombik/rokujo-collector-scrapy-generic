# FeedSpider

This spider is a helper spider to generate Atom/RSS feeds for other spiders.
It collects links to the latest article URLs and generates feeds defined in a configuration file.

The spider is useful when the website to crawl does not provide RSS feed.
The spider visits the URL, scrapes URLs to latest article pages with the given XPath expression and generates an RSS feed file.
The RSS feed file can then be used by other spiders to collects ArticleItem from the URLs.

1. Visit the website.
1. Find a page that lists the latest articles.
1. Figure out how to filter the URLs with XPath.

The configuration file looks like this:

```yaml
---
feed_config:
  "http://foo.example.org/latest.html":
    file_name: "latest.xml"
    feed_type: "atom"
    xpath_href: "//li[@class='articles-list__item']/a/@href"
    xpath_title: "//li[@class='articles-list__item']/a/text()"
```

* `feed_config`: The root element of the configuration. Mandatory.
    It is a hash of URLs as key and their configuration values as value.
* `file_name`: The filename of the generated RSS feed for the URL.
* `xpath_href`: A XPath expression to filter URLs to articles.
* `xpath_title`: A XPath expression to filter titles of articles.
* `feed_type`: The type of RSS feed, either `atom` or `rss`.
