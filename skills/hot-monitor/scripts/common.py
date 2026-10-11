"""Shared helpers for hot-monitor search scripts."""

import json
import sys
import warnings

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
TIMEOUT = 15


def warn(message: str) -> None:
    print(message, file=sys.stderr)


def emit(items: list) -> None:
    json.dump(items, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def empty_item() -> dict:
    return {
        "title": "",
        "content": "",
        "url": "",
        "source": "",
        "publishedAt": None,
        "authorName": None,
        "viewCount": None,
        "likeCount": None,
        "commentCount": None,
    }


def dedupe(items: list) -> list:
    seen = set()
    unique = []
    for item in items:
        url = (item.get("url") or "").rstrip("/")
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(item)
    return unique
