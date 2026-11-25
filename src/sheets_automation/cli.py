"""Command line interface."""
from __future__ import annotations

import argparse
import os
import sys

from .aggregate import HEADER, aggregate
from .fetch import FetchError, fetch_api, load_demo
from .sinks import SinkError, write_csv, write_sheet


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sheets-automation",
        description="Fetch posts/users, aggregate posts per author, write to CSV or Google Sheets.",
    )
    p.add_argument("--source", choices=["api", "demo"], default="api",
                   help="api = JSONPlaceholder public API; demo = bundled dummy data (offline). Default: api")
    p.add_argument("--output", choices=["csv", "sheets"], default="csv", help="Where to write. Default: csv")
    p.add_argument("--csv-path", default="summary.csv", help="CSV file path. Default: summary.csv")
    p.add_argument("--spreadsheet-id", default=os.environ.get("SPREADSHEET_ID", ""),
                   help="Google spreadsheet id (env SPREADSHEET_ID)")
    p.add_argument("--worksheet", default=os.environ.get("WORKSHEET_NAME", "Summary"),
                   help="Worksheet tab name (env WORKSHEET_NAME). Default: Summary")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        posts, users = load_demo() if args.source == "demo" else fetch_api()
        rows = aggregate(posts, users)
        if args.output == "csv":
            path = write_csv(HEADER, rows, args.csv_path)
            print(f"Wrote {len(rows)} rows to {path}")
        else:
            url = write_sheet(HEADER, rows, args.spreadsheet_id, args.worksheet)
            print(f"Wrote {len(rows)} rows to worksheet '{args.worksheet}': {url}")
    except (FetchError, SinkError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
