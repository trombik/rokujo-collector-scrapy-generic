# FeedSpider

This spider is a helper spider to generate Atom/RSS feeds for other spiders.
It collects links to the latest article URLs and generates feeds defined in a
configuration file.

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

See [FeedConfig](generic.spiders.feed.FeedConfig) for more details.
