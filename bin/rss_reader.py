import argparse
import os
import re
import subprocess
import tempfile
import time
from collections import defaultdict
from typing import Any

import yaml
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
    cmd = ["scrapy", "crawl", "feed"]
    run_spider(cmd)


def load_config(path):
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simple RSS reader for rokujo-collector-scrapy"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="rss.yml",
        help="Path to RSS feed configuration file",
    )
    parser.add_argument(
        "-i", "--interval", default=15, help="Update interval in minutes"
    )
    parser.add_argument(
        "-d",
        "--database",
        default="db/rss_reader.db",
        help="Path to RSS feed database",
    )
    parser.add_argument(
        "-o", "--output", default="rss.jsonl", help="Path to output JSONL file"
    )
    return parser.parse_args()


def filename_with_unix_timestamp(path: str) -> str:
    unix_timestamp = int(time.time())
    base, ext = os.path.splitext(path)
    return f"{base}-{unix_timestamp}{ext}"


def create_tmp_file(target_path: str) -> str:
    directory = os.path.dirname(os.path.abspath(target_path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    os.close(fd)
    return tmp_path


if __name__ == "__main__":
    args = parse_args()
    conf = load_config(args.config)

    reader = make_reader(
        url=args.database,
        feed_root="",
    )
    for url in conf.get("feed_urls"):
        reader.add_feed(url, exist_ok=True)

    print(f"Starting RSS monitor. Interval: {args.interval} min.")
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
                file = filename_with_unix_timestamp(args.output)
                tmp_file = create_tmp_file(file)
                cmd.extend(["-o", tmp_file])
                try:
                    run_spider(cmd)
                    if (
                        os.path.exists(tmp_file)
                        and os.path.getsize(tmp_file) > 0
                    ):
                        os.rename(tmp_file, file)
                finally:
                    if os.path.exists(tmp_file):
                        os.remove(tmp_file)

            for entry in unread_entries:
                reader.mark_entry_as_read(entry)
        else:
            print("No new unread entries.")

        print(f"Sleeping for {args.interval} minutes...")
        time.sleep(args.interval * 60)
