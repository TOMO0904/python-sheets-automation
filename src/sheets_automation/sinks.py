"""Output targets: CSV file or Google Sheets."""
from __future__ import annotations

import csv
import os
from pathlib import Path

import gspread

CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"


class SinkError(RuntimeError):
    """Raised when output cannot be written (bad configuration or API failure)."""


def write_csv(header: list[str], rows: list[list], path: str | Path) -> Path:
    path = Path(path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def write_sheet(
    header: list[str],
    rows: list[list],
    spreadsheet_id: str,
    worksheet: str = "Summary",
    client: gspread.Client | None = None,
) -> str:
    """Replace the contents of a worksheet with header + rows. Returns the spreadsheet URL.

    The service-account key file path is read from GOOGLE_APPLICATION_CREDENTIALS.
    Share the spreadsheet with the service account's e-mail address first.
    """
    if not spreadsheet_id:
        raise SinkError("spreadsheet id is required (--spreadsheet-id or SPREADSHEET_ID)")
    if client is None:
        key_path = os.environ.get(CREDENTIALS_ENV)
        if not key_path:
            raise SinkError(f"{CREDENTIALS_ENV} is not set; point it to your service-account key file")
        if not Path(key_path).is_file():
            raise SinkError(f"{CREDENTIALS_ENV} points to a file that does not exist")
        client = gspread.service_account(filename=key_path)
    try:
        sheet = client.open_by_key(spreadsheet_id)
        try:
            ws = sheet.worksheet(worksheet)
        except gspread.WorksheetNotFound:
            ws = sheet.add_worksheet(title=worksheet, rows=max(len(rows) + 1, 10), cols=len(header))
        ws.clear()
        ws.update(values=[header, *rows], range_name="A1")
    except gspread.GSpreadException as exc:
        raise SinkError(f"Google Sheets error: {exc}") from exc
    return sheet.url
