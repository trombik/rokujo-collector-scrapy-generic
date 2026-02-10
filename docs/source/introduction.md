# Introduction

A collection of [Scrapy](https://docs.scrapy.org/) spiders designed to crawl web pages, scrape text content, and generate structured JSONL entries.

These JSONL entries serve as a foundation for further processing, such as creating collocation databases and assisting in the development of tools for translators.

Use cases include:

* Creating a collocation database from web articles.
* Creating a database of source and target versions of web articles.
* Creating a database of commonly used technical terms by experts.

Additionally, some spiders collect files linked from pages, such as PDFs.

After scraping texts, pipelines process the collected texts by addding metadata, such as published date, site name, and URL,
The metadata can be used to filter search results, reference the source, and show the context.

## Rationale

When I translate documents, I often need to research how a term is used, what combinations of nouns and verbs are used, and which term is most commonly used in an industry.
Like many other translators, my research tool is a search engine.
However, the output and results are not ideal; search results often omit some keywords, tend to ignore a keyword in the query, and do not show the exact place where the term is used when opening the link.
Publicly available Japanese corpora are not an option because they are for general purposes and not specific enough to the industries I have been working in.

As I need my own corpora, I wrote spiders to create them.
