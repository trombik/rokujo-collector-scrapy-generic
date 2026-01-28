import re
import subprocess
import time
from collections import defaultdict
from typing import Any

from reader import make_reader


def group_urls_to_commands(
    unread_urls: list[str],
    config: dict[str, Any],
) -> list[list[str]]:
    rules = config.get("rules", [])
    rule_matches = defaultdict(list)

    for url in unread_urls:
        for i, rule in enumerate(rules):
            if re.search(rule["url_pattern"], url):
                rule_matches[i].append(url)
                break

    commands = []
    for i, urls in rule_matches.items():
        rule = rules[i]
        spider = rule.get("spider_name", "read-more")
        cmd = ["scrapy", "crawl", spider]
        cmd.extend(["-a", f"urls={','.join(urls)}"])

        for arg in rule.get("args", []):
            cmd.extend(["-a", arg])
        commands.append(cmd)
    return commands


def run_spider(cmd):
    if cmd is None:
        return

    try:
        subprocess.run(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Spider execution failed: {e}")


def update_feeds_with_feed_spider():
    cmd = [
        "scrapy",
        "crawl",
        "feed"
    ]
    run_spider(cmd)


INTERVAL_SECONDS = 15 * 60
DB_PATH = "db/rss_reader.db"

if __name__ == "__main__":
    import yaml

    with open("rss.yml", "r") as f:
        conf = yaml.safe_load(f)

    reader = make_reader(
        url=DB_PATH,
        feed_root="",
    )
    for url in conf.get("feed_urls"):
        reader.add_feed(url, exist_ok=True)

    print(f"Starting RSS monitor. Interval: {INTERVAL_SECONDS / 60} min.")
    while True:
        update_feeds_with_feed_spider()
        print("Checking for new entries...")
        reader.update_feeds()
        unread_entries = list(reader.get_entries(read=False))
        if unread_entries:
            urls_to_process = [
                entry.link for entry in unread_entries if entry.link
            ]
            print(f"Found {len(urls_to_process)} unread entries.")
            for cmd in group_urls_to_commands(urls_to_process, conf):
                cmd.extend(["-o", "rss.jsonl"])
                run_spider(cmd)

            for entry in unread_entries:
                reader.mark_entry_as_read(entry)
        else:
            print("No new unread entries.")

        print(f"Sleeping for {INTERVAL_SECONDS / 60} minutes...")
        time.sleep(INTERVAL_SECONDS)
