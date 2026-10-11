#!/usr/bin/env python3
"""Search public GitHub repos for new and still-hot AI application projects.

Uses the public search API. Ranking uses the repository's current star count
inside a created/pushed window. No token required.
Unauthenticated search allows about 10 requests per minute.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone

from common import TIMEOUT, dedupe, emit, warn

import requests

API = "https://api.github.com/search/repositories"
NEW_TOPICS = ("llm", "ai-agents", "mcp", "agent-skills")
HOT_TOPICS = ("llm", "ai-agents")


def day_offset(days: int) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return moment.strftime("%Y-%m-%d")


def windows() -> dict:
    return {
        "new_since": day_offset(30),
        "hot_start": day_offset(90),
        "hot_end": day_offset(31),
        "pushed_since": day_offset(14),
    }


def preset_queries(span: dict) -> list:
    queries = []
    for topic in NEW_TOPICS:
        queries.append(
            (
                f"created:>{span['new_since']} stars:>50 topic:{topic} -topic:awesome-list",
                "github-new",
            )
        )
    for topic in HOT_TOPICS:
        hot = (
            "created:{hot_start}..{hot_end} stars:>400 pushed:>{pushed_since} "
            "topic:{topic} -topic:awesome-list"
        ).format(topic=topic, **span)
        queries.append((hot, "github-hot"))
    return queries


def keyword_queries(query: str, span: dict) -> list:
    text = " ".join(query.split())
    hot = (
        "created:{hot_start}..{hot_end} stars:>100 pushed:>{pushed_since} "
        "{text} in:name,description -topic:awesome-list"
    ).format(text=text, **span)
    return [
        (
            f"created:>{span['new_since']} stars:>30 {text} in:name,description -topic:awesome-list",
            "github-new",
        ),
        (hot, "github-hot"),
    ]


def search(query: str, limit: int) -> list:
    response = requests.get(
        API,
        params={"q": query, "sort": "stars", "order": "desc", "per_page": limit},
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "hot-monitor",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=TIMEOUT,
    )
    if response.status_code in (403, 422, 429):
        message = ""
        try:
            message = response.json().get("message") or ""
        except Exception:  # noqa: BLE001
            message = response.text[:200]
        raise RuntimeError(f"{response.status_code} {message}".strip())
    response.raise_for_status()
    return response.json().get("items") or []


def to_item(repo: dict, source: str) -> dict:
    description = (repo.get("description") or "").replace("\n", " ").strip()
    topics = ",".join((repo.get("topics") or [])[:8])
    created = repo.get("created_at") or ""
    pushed = repo.get("pushed_at") or ""
    stars = repo.get("stargazers_count") or 0
    language = repo.get("language") or "unknown"
    content = (
        f"{description} | {stars} stars | {language} | "
        f"created {created[:10] or '?'} | pushed {pushed[:10] or '?'} | topics: {topics}"
    )
    return {
        "title": repo.get("full_name") or "",
        "content": content[:500],
        "url": repo.get("html_url") or "",
        "source": source,
        "publishedAt": created if source == "github-new" else pushed,
        "authorName": (repo.get("owner") or {}).get("login"),
        "viewCount": repo.get("forks_count"),
        "likeCount": stars,
        "commentCount": repo.get("open_issues_count"),
    }


def cap_by_source(items: list, limit: int) -> list:
    grouped = {"github-new": [], "github-hot": []}
    for item in items:
        grouped.setdefault(item.get("source") or "", []).append(item)
    kept = []
    for source in ("github-new", "github-hot"):
        ranked = sorted(grouped.get(source) or [], key=lambda item: item.get("likeCount") or 0, reverse=True)
        kept.extend(ranked[:limit])
    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description="Search GitHub for new and hot AI application repos")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    span = windows()
    query = args.query.strip()
    selected = keyword_queries(query, span) if query else preset_queries(span)
    items = []
    for index, (text, source) in enumerate(selected):
        if index:
            time.sleep(1)
        try:
            repos = search(text, args.limit)
            warn(f"{source}: {len(repos)} | {text}")
            items.extend(to_item(repo, source) for repo in repos)
        except Exception as exc:  # noqa: BLE001 - one query must not fail the rest
            warn(f"github failed: {exc} | {text}")
            if str(exc).startswith("403") or str(exc).startswith("429"):
                break
    emit(cap_by_source(dedupe(items), args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
