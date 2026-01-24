# ReadMoreSpider

This spider is a versatile spider that collects texts from websites. It supports multiple pages in an article, a landing page to the main article page, and articles with sources, e.g., English version of the article.

This spider is suitable for:

* A single page article
* A multi-pages article with a navigation bar with a link to `Next` page
* An article with links to source articles, e.g., links to original English articles

## How It Works

Some websites have a landing page for each article, notably, Yahoo! News. The structure is:

* A landing page (`/pickup/${PICKUP_ID}`) with a link to the first article page (`記事全文を読む`, or `read_more` link)
* The first page of the article (`/articles/${ARTICLE_ID}`) with a link to optional, subsequent article pages (`次へ`, or `read_next` link)
* Optional article pages (`/article/${ARTICLE_ID}?page=${N}`) with a link to the next article page (`次へ`).

```{mermaid}
---
title: ReadMoreSpider State Diagram
---
stateDiagram-v2

    [*] --> LandingPage
    LandingPage --> MainArticle
    MainArticle --> FindSourceArticle: read_next is not found
    MainArticle --> NextPage: read_next is found
    NextPage --> NextPage: read_next is found
    NextPage --> FindSourceArticle: read_next is not found
    FindSourceArticle --> GenerateItem: source is not found
    FindSourceArticle --> LandingPage: A source is found
    GenerateItem --> [*]
```

Given a URL, or URLs, the spider crawls the URL, finds a link to the first page of the article until there is no article pages while collecting texts from the article pages.

If the landing page has a `read_more` link, the spider follows the link. Because the landing page contains just a summary of the article, the spider does not collect texts from the landing page. However, if the landing page does not have `read_more` link, the spider considers the page is the first page of the article and collects text from the page.

After following the `read_more` link, the spider collects texts from the article page, looks for a `read_next` link. If it finds the link, repeat this step until no `read_next` link is found in the pages.

When no more `read_next` link is found, the spider looks for links to source articles. If it finds one, repeat the entire process.

When no source link is found, it finishes crawling.

When it finishes crawling and scraping article texts, it generates [ArticleItem], an object that represents an article. The `ArticleItem` has an attribute, `body`, which includes all the texts from the article, among other metadata attributes. The object can be exported to a file, such as JSONL or CSV files.

## Usage

```console
uv run scrapy crawl -a'urls=https://example.org/pickup/6567310' -O foo.jsonl read-more
```

The above command will crawl the URL, any pages the spider finds, and generate a JSONL file.

The human-friendly name of the spider is `read-more`. `urls` is a mandatory argument, a comma-separated list of URLs. `-O` option tells the spider to create, or overwrite, a JSONL file and store the collected `ArticleItem` in it. To append new article to the JSONL later, use `-o foo.jsonl`, which appends `ArticleItem` instead of overwriting the file.

To see the result in the file, open it with a text editor, or use [jq](https://jqlang.org/).

```console
jq < foo.jsonl
```

`-O` and `-o` options support other formats, such as `.csv`.

```console
uv run scrapy crawl -a'urls=https://example.org/pickup/6567310' -O foo.csv read-more
```
