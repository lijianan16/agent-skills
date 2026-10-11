#!/usr/bin/env python3
"""Search public Chinese sources. JSON array on stdout, errors on stderr."""

from __future__ import annotations

import argparse
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from common import TIMEOUT, USER_AGENT, dedupe, emit, warn

import requests
from bs4 import BeautifulSoup

DEFAULT_SOURCES = ("bilibili", "weibo", "sogou")


def headers(referer: str | None = None, cookie: str | None = None):
    data = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
    }
    if referer:
        data["Referer"] = referer
    if cookie:
        data["Cookie"] = cookie
    return data


def clean_title(text: str) -> str:
    return re.sub(r"</?em[^>]*>", "", text or "").strip()


def search_bilibili(query: str, limit: int) -> list:
    response = requests.get(
        "https://api.bilibili.com/x/web-interface/search/type",
        params={
            "keyword": query,
            "search_type": "video",
            "order": "pubdate",
            "page": 1,
            "pagesize": limit,
        },
        headers=headers(
            referer="https://search.bilibili.com/",
            cookie=f"buvid3={uuid.uuid4()}infoc",
        ),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 0:
        raise RuntimeError(f"bilibili code {payload.get('code')}")
    videos = (payload.get("data") or {}).get("result") or []
    items = []
    for video in videos[:limit]:
        title = clean_title(video.get("title") or "")
        bvid = video.get("bvid")
        published = video.get("pubdate")
        items.append(
            {
                "title": title,
                "content": clean_title(video.get("description") or title)[:500],
                "url": f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                "source": "bilibili",
                "publishedAt": (
                    datetime.fromtimestamp(published, tz=timezone.utc).isoformat()
                    if published
                    else None
                ),
                "authorName": video.get("author"),
                "viewCount": video.get("play"),
                "likeCount": video.get("like"),
                "commentCount": video.get("review"),
            }
        )
    return [item for item in items if item["url"]]


def search_bilibili_account(keyword: str, limit: int) -> list:
    response = requests.get(
        "https://api.bilibili.com/x/web-interface/search/type",
        params={"keyword": keyword, "search_type": "bili_user", "page": 1, "pagesize": 5},
        headers=headers(referer="https://search.bilibili.com/"),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    users = ((response.json().get("data") or {}).get("result")) or []
    matched = next(
        (
            user
            for user in users
            if (user.get("uname") or "").lower() == keyword.lower()
            or (
                user.get("fans", 0) > 1000
                and keyword.lower() in (user.get("uname") or "").lower()
            )
        ),
        None,
    )
    if not matched:
        warn("bilibili account: no match")
        return []
    mid = matched.get("mid")
    warn(f"bilibili account: {matched.get('uname')} mid={mid}")
    time.sleep(1)
    videos = requests.get(
        "https://api.bilibili.com/x/space/arc/search",
        params={"mid": mid, "pn": 1, "ps": limit, "order": "pubdate"},
        headers=headers(referer=f"https://space.bilibili.com/{mid}"),
        timeout=TIMEOUT,
    )
    videos.raise_for_status()
    vlist = (((videos.json().get("data") or {}).get("list") or {}).get("vlist")) or []
    items = []
    for video in vlist[:limit]:
        created = video.get("created")
        bvid = video.get("bvid")
        title = video.get("title") or ""
        items.append(
            {
                "title": title,
                "content": (video.get("description") or title)[:500],
                "url": f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                "source": "bilibili",
                "publishedAt": (
                    datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
                    if created
                    else None
                ),
                "authorName": video.get("author") or matched.get("uname"),
                "viewCount": video.get("play"),
                "likeCount": None,
                "commentCount": video.get("comment"),
            }
        )
    return [item for item in items if item["url"]]


def search_weibo(query: str, limit: int) -> list:
    response = requests.get(
        "https://weibo.com/ajax/side/hotSearch",
        headers=headers(referer="https://weibo.com/"),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("ok") != 1:
        raise RuntimeError("weibo hot search unavailable")
    board = (payload.get("data") or {}).get("realtime") or []
    query_lower = query.lower().strip()
    words = [part for part in re.split(r"\s+", query_lower) if part]
    items = []
    for row in board:
        topic = (row.get("note") or row.get("word") or "").strip()
        topic_lower = topic.lower()
        matched = (
            query_lower in topic_lower
            or topic_lower in query_lower
            or any(word in topic_lower or topic_lower in word for word in words)
        )
        if not matched or not topic:
            continue
        items.append(
            {
                "title": f"微博热搜: {topic}",
                "content": f"微博热搜话题「{topic}」，热度 {row.get('num') or '未知'}",
                "url": f"https://s.weibo.com/weibo?q={quote('#' + topic + '#')}",
                "source": "weibo",
                "publishedAt": None,
                "authorName": None,
                "viewCount": row.get("num"),
                "likeCount": None,
                "commentCount": None,
            }
        )
        if len(items) >= limit:
            break
    if not items:
        warn(f"weibo: no hot-search topic matched {query!r}")
    return items


def search_sogou(query: str, limit: int) -> list:
    response = requests.get(
        "https://www.sogou.com/web",
        params={"query": query, "ie": "utf-8"},
        headers=headers(),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    for node in soup.select(".vrwrap, .rb"):
        link = node.select_one("h3 a")
        if not link:
            continue
        title = link.get_text(" ", strip=True)
        url = link.get("href") or ""
        if url.startswith("/link?"):
            url = "https://www.sogou.com" + url
        snippet_node = node.select_one("p")
        content = snippet_node.get_text(" ", strip=True) if snippet_node else title
        if not title or "大家还在搜" in title:
            continue
        items.append(
            {
                "title": title,
                "content": content[:500],
                "url": url,
                "source": "sogou",
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
    "bilibili": search_bilibili,
    "weibo": search_weibo,
    "sogou": search_sogou,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Search public Chinese hot sources")
    parser.add_argument("query")
    parser.add_argument("--sources", default=",".join(DEFAULT_SOURCES))
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument(
        "--detect-account",
        action="store_true",
        help="If the keyword matches a Bilibili creator, include that creator's latest videos",
    )
    args = parser.parse_args()

    items = []
    if args.detect_account:
        try:
            items.extend(search_bilibili_account(args.query, args.limit))
        except Exception as exc:  # noqa: BLE001
            warn(f"bilibili account failed: {exc}")

    selected = [name.strip().lower() for name in args.sources.split(",") if name.strip()]
    for index, name in enumerate(selected):
        searcher = SEARCHERS.get(name)
        if not searcher:
            warn(f"unknown source: {name}")
            continue
        if index or items:
            time.sleep(1)
        try:
            found = searcher(args.query, args.limit)
            warn(f"{name}: {len(found)}")
            items.extend(found)
        except Exception as exc:  # noqa: BLE001
            warn(f"{name} failed: {exc}")
    emit(dedupe(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
