#!/usr/bin/env python3
"""Search Twitter via twitterapi.io. Requires TWITTER_API_KEY. JSON on stdout."""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from common import TIMEOUT, dedupe, emit, warn

import requests

API_BASE = "https://api.twitterapi.io"


def since_date(days: int) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return moment.strftime("%Y-%m-%d")


def search(query: str, limit: int) -> list:
    api_key = os.environ.get("TWITTER_API_KEY", "").strip()
    if not api_key:
        warn("TWITTER_API_KEY is not set; twitter skipped")
        return []

    advanced = f"{query} -filter:retweets -filter:replies since:{since_date(3)}"
    response = requests.get(
        f"{API_BASE}/twitter/tweet/advanced_search",
        params={"query": advanced, "queryType": "Latest"},
        headers={"X-API-Key": api_key},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    tweets = response.json().get("tweets") or []
    items = []
    for tweet in tweets[:limit]:
        author = tweet.get("author") or {}
        text = tweet.get("text") or ""
        items.append(
            {
                "title": text[:100],
                "content": text[:500],
                "url": tweet.get("url") or "",
                "source": "twitter",
                "publishedAt": tweet.get("createdAt"),
                "authorName": author.get("userName") or author.get("name"),
                "viewCount": tweet.get("viewCount"),
                "likeCount": tweet.get("likeCount"),
                "commentCount": tweet.get("replyCount"),
            }
        )
    return [item for item in items if item["url"]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Search recent original tweets")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    try:
        items = search(args.query, args.limit)
    except Exception as exc:  # noqa: BLE001
        warn(f"twitter failed: {exc}")
        items = []
    warn(f"twitter: {len(items)}")
    emit(dedupe(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
