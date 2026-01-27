# Running a spider

After successful installation, run a spider, `ReadMoreSider`, `read-me` in short.

```console
uv run scrapy crawl -a'urls=https://www.example.org/' -O foo.jsonl read-more
```

The above command crawls the URL and stores the scraped texts into
`foo.jsonl`. The file is a JSONL file, a common format to process a large set of text data. Each line is a JSON object.

Open the file with your favorite text editor. You will see a line of JSON object.

With `jq`, the output is human friendly.

```console
jq < foo.jsonl
```

```json
{
  "acquired_time": "2026-01-24T16:12:38.376752+00:00",
  "body": "<main>\n    <p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p>\n    <p>Learn more</p>\n  </main>",
  "url": "https://www.example.org/",
  "lang": "en",
  "author": null,
  "description": null,
  "kind": null,
  "modified_time": null,
  "published_time": null,
  "site_name": null,
  "title": "Example Domain",
  "item_type": "ArticleItem",
  "character_count": 96,
  "sources": []
}
```
