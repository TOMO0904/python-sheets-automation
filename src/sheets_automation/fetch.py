"""Load posts and users from the JSONPlaceholder demo API, or from bundled dummy data."""
from __future__ import annotations

import json
from importlib import resources

import requests

API_BASE = "https://jsonplaceholder.typicode.com"
TIMEOUT_SECONDS = 15


class FetchError(RuntimeError):
    """Raised when the API cannot be reached or returns unusable data."""


def _get_json(session: requests.Session, path: str) -> list[dict]:
    url = f"{API_BASE}{path}"
    try:
        resp = session.get(url, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise FetchError(f"request to {url} failed: {exc}") from exc
    if not isinstance(data, list):
        raise FetchError(f"unexpected response shape from {url}")
    return data


def fetch_api(session: requests.Session | None = None) -> tuple[list[dict], list[dict]]:
    """Return (posts, users) from the public demo API."""
    session = session or requests.Session()
    return _get_json(session, "/posts"), _get_json(session, "/users")


def load_demo() -> tuple[list[dict], list[dict]]:
    """Return (posts, users) from the dummy data bundled with the package (works offline)."""
    base = resources.files("sheets_automation") / "demo_data"
    posts = json.loads((base / "posts.json").read_text(encoding="utf-8"))
    users = json.loads((base / "users.json").read_text(encoding="utf-8"))
    return posts, users
