"""Aggregate posts per author."""
from __future__ import annotations

from collections import defaultdict

HEADER = ["user_id", "name", "company", "posts", "avg_title_words", "avg_body_words"]


def _words(text: object) -> int:
    return len(str(text or "").split())


def aggregate(posts: list[dict], users: list[dict]) -> list[list]:
    """Return rows (without header) with one line per user, sorted by post count then name.

    Posts whose user is unknown are grouped under "(unknown)". Users with no posts get zeros.
    """
    by_user: dict[int, list[dict]] = defaultdict(list)
    for post in posts:
        by_user[post.get("userId")].append(post)

    rows: list[list] = []
    seen: set[int] = set()
    for user in users:
        uid = user.get("id")
        seen.add(uid)
        company = (user.get("company") or {}).get("name", "")
        rows.append(_row(uid, user.get("name", ""), company, by_user.get(uid, [])))
    for uid, items in by_user.items():
        if uid not in seen:
            rows.append(_row(uid, "(unknown)", "", items))

    rows.sort(key=lambda r: (-r[3], str(r[1])))
    return rows


def _row(uid: object, name: str, company: str, items: list[dict]) -> list:
    n = len(items)
    avg_title = round(sum(_words(p.get("title")) for p in items) / n, 2) if n else 0.0
    avg_body = round(sum(_words(p.get("body")) for p in items) / n, 2) if n else 0.0
    return [uid, name, company, n, avg_title, avg_body]
