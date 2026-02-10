# DirectorySpider

A spider that crawls pages under a directory.
This spider is useful when scraping ArticleItem from a part of website.

## How It Works

The directory to crawl is the base directory of the last component of the given URL.
When the URL is `http://example.org/index.html`, it crawls all the URLs.
When the URL is `http://example.org/foo/index.html`, it crawls pages under `/foo/`.
When the URL is `http://example.org/foo/bar/index.html`, it crawls pages under `/foo/bar/` but not `/foo/bar.html`.

When start_urls is `http://example.org/a/b/c.html`:

- it crawls `/a/b/index.html`.
- it crawls `/a/b/foo.html`.
- it crawls `/a/b/c/bar.html`.
- it does not crawl `/index.html`
- it does not crawl `/a/index.html`
