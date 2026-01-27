# ArchiveSpider

This spider starts crawling the given URL, extract all the links to articles in the page, follows "Next" link to the next archive index page, and repeat the process until no link to "Next" page is found.
The spider is designed for a typical "Archive" pages commonly found on popular CMS.

## Usage

The spider requires two arguments: `archive_next_xpath` and `archive_article_xpath`.

`archive_next_xpath` is an XPath ([Wikipedia article](https://en.wikipedia.org/wiki/XPath)) to `href` attribute of the link to the next page.

`archive_article_xpath` is an XPath to `href` attribute of the links to archive pages.

Suppose, the archive index page has many links to archive pages under a `<ul>` tag.

```html
<ul>
  <li class="blog__post">
    <div class="post-date">
      <p>January 10, 2025</p>
    </div>
    <div class="post-container">
      <h3>
        <a href="/2025/1/10/this-week-in-rails">Sorted Columns in Schema Dumper, Deprecations, and lots of fixes!</a>
      </h3>
    </div>
  </li>
  <li class="blog__post">
    <!-- other link -->
  </li>
</ul>
```

One of possible XPath expressions for the links is:

```
//li[@class='blog__post']//h3/a/@href
```

This XPath returns an array of relative URL to archive post in the page.

* `//li[@class='blog__post']` finds all list items (`<li>`) anywhere in the document that have the exact class name `blog__post`.
* `//h3` searches inside those list items for any Level 3 Heading (`<h3>`), regardless of how deep they are nested.
* `/a` selects the anchor tag (`<a>`) that is a direct child of the `<h3>`.
* `/@href` extracts the value of the `href` attribute (the URL) from the link, rather than the text of the link itself.

Suppose, the page has a navigation to the next archive page.
The link text is "See more posts".

```html
<div class="blog__pagination">
  <a href="/blog/page/2"><span>See more posts…</span></a>
</div>
```

One of possible XPath expressions for the link is:

```
//div[@class='blog__pagination']//a[contains(., 'See more posts')]/@href
```

With these XPath, all the archive pages can be scraped with:

```console
uv run scrapy crawl -a'urls=https://rubyonrails.org/blog/' \
    -a "archive_article_xpath=//li[@class='blog__post']//h3/a/@href" \
    -a "archive_next_xpath="//div[@class='blog__pagination']//a[contains(., 'See more posts')]/@href" \
    -O foo.jsonl archive
```

## How It Works


```{mermaid}
---
title: ArchiveSpider State Diagram
---
flowchart TD

    StartUrls[urls] --> ArchiveIndexPage
    ArchiveIndexPage[Parse an archive index page] --> IfArchivePageFound{Archive page found?}
    IfArchivePageFound --> |Yes| ReadMore
    IfArchivePageFound --> |No| IfNextArchiveIndexPageFound{Next archive page found?}
    ReadMore --> ArchiveIndexPage
    IfNextArchiveIndexPageFound --> |Yes| ArchiveIndexPage
    IfNextArchiveIndexPageFound --> |No | End

```

The spider parse an index page of archive pages. When links to archive pages found, it scrapes the archives.

The spider internally use `ReadMore` to scrape an archive page.
That is, the spider collects all subsequent pages in the archive page when the archive page has a "Next" link.

The spider then follow the next archive index page, repeating the above process.

When no more "Next" link to archive index is found, the spider terminates.
