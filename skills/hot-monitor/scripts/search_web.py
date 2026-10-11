#!/usr/bin/env python3
"""Search public international sources. JSON array on stdout, errors on stderr."""

import argparse
import sys
import time

from common import TIMEOUT, USER_AGENT, dedupe, emit, warn

import requests
from bs4 import BeautifulSoup

DEFAULT_SOURCES = ("hackernews", "duckduckgo", "bing")


def headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6",
    }


def search_hackernews(query: str, limit: int) -> list:
    since = int(time.time()) - 7 * 24 * 3600
    response = requests.get(
        "https://hn.algolia.com/api/v1/search",
        params={
            "query": query,
            "tags": "story",
            "hitsPerPage": limit,
            "numericFilters": f"created_at_i>{since}",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    items = []
    for hit in response.json().get("hits") or []:
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        created = hit.get("created_at")
        items.append(
            {
                "title": hit.get("title") or "",
                "content": (hit.get("story_text") or hit.get("title") or "")[:500],
                "url": url,
                "source": "hackernews",
                "publishedAt": created,
                "authorName": hit.get("author"),
                "viewCount": None,
                "likeCount": hit.get("points"),
                "commentCount": hit.get("num_comments"),
            }
        )
    return items


def search_duckduckgo(query: str, limit: int) -> list:
    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers=headers(),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    for node in soup.select(".result"):
        link = node.select_one(".result__a")
        if not link:
            continue
        title = link.get_text(" ", strip=True)
        url = link.get("href") or ""
        if "uddg=" in url:
            from urllib.parse import parse_qs, urlparse

            url = parse_qs(urlparse(url).query).get("uddg", [url])[0]
        snippet = node.select_one(".result__snippet")
        content = snippet.get_text(" ", strip=True) if snippet else title
        if title and url.startswith("http"):
            items.append(
                {
                    "title": title,
                    "content": content[:500],
                    "url": url,
                    "source": "duckduckgo",
                    "publishedAt": None,
                    "authorName": None,
                    "viewCount": None,
                    "likeCount": None,
                    "commentCount": None,
                }
            )
        if len(items) >= limit:
            break
    return items


def search_bing(query: str, limit: int) -> list:
    response = requests.get(
        "https://www.bing.com/search",
        params={"q": query, "count": max(limit, 10)},
        headers=headers(),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    for node in soup.select("li.b_algo"):
        link = node.select_one("h2 a")
        if not link:
            continue
        title = link.get_text(" ", strip=True)
        url = link.get("href") or ""
        snippet = node.select_one(".b_caption p")
        content = snippet.get_text(" ", strip=True) if snippet else title
        if title and url.startswith("http"):
            items.append(
                {
                    "title": title,
                    "content": content[:500],
                    "url": url,
                    "source": "bing",
                    "publishedAt": None,
                    "authorName": None,
                    "viewCount": None,
                    "likeCount": None,
                    "commentCount": None,
                }
            )
        if len(items) >= limit:
            break
    return items


SEARCHERS = {
    "hackernews": search_hackernews,
    "duckduckgo": search_duckduckgo,
    "bing": search_bing,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Search public international hot sources")
    parser.add_argument("query")
    parser.add_argument("--sources", default=",".join(DEFAULT_SOURCES))
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    selected = [name.strip().lower() for name in args.sources.split(",") if name.strip()]
    items = []
    for index, name in enumerate(selected):
        searcher = SEARCHERS.get(name)
        if not searcher:
            warn(f"unknown source: {name}")
            continue
        if index:
            time.sleep(1)
        try:
            found = searcher(args.query, args.limit)
            warn(f"{name}: {len(found)}")
            items.extend(found)
        except Exception as exc:  # noqa: BLE001 - one source must not fail the rest
            warn(f"{name} failed: {exc}")
    emit(dedupe(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
