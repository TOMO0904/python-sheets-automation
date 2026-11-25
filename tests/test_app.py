import csv
from unittest.mock import MagicMock

import gspread
import pytest
import requests

from sheets_automation import fetch
from sheets_automation.aggregate import HEADER, aggregate
from sheets_automation.cli import main
from sheets_automation.sinks import SinkError, write_csv, write_sheet


def test_aggregate_counts_and_sorting():
    posts = [
        {"userId": 1, "title": "a b", "body": "one two three four"},
        {"userId": 1, "title": "c", "body": "one two"},
        {"userId": 2, "title": "x y z", "body": "hi"},
        {"userId": 99, "title": "orphan", "body": ""},
    ]
    users = [
        {"id": 1, "name": "Ann", "company": {"name": "A Co"}},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Cy"},
    ]
    rows = aggregate(posts, users)
    assert rows[0] == [1, "Ann", "A Co", 2, 1.5, 3.0]
    by_name = {r[1]: r for r in rows}
    assert by_name["Bob"][3] == 1
    assert by_name["Cy"][3:] == [0, 0.0, 0.0]
    assert by_name["(unknown)"][0] == 99


def test_demo_data_loads_and_aggregates():
    posts, users = fetch.load_demo()
    rows = aggregate(posts, users)
    assert len(posts) == 10
    assert sum(r[3] for r in rows) == 10


def test_write_csv(tmp_path):
    path = write_csv(HEADER, [[1, "Ann", "A", 2, 1.5, 3.0]], tmp_path / "out" / "s.csv")
    with path.open(encoding="utf-8") as fh:
        got = list(csv.reader(fh))
    assert got[0] == HEADER
    assert got[1][1] == "Ann"


def test_cli_demo_csv(tmp_path, capsys):
    out = tmp_path / "s.csv"
    assert main(["--source", "demo", "--output", "csv", "--csv-path", str(out)]) == 0
    assert out.exists()
    assert "Wrote 5 rows" in capsys.readouterr().out


def test_write_sheet_uses_client_and_replaces_contents():
    client = MagicMock()
    sheet = client.open_by_key.return_value
    sheet.url = "https://docs.google.com/spreadsheets/d/FAKE"
    url = write_sheet(HEADER, [[1, "Ann", "A", 2, 1.5, 3.0]], "FAKE_ID", "Summary", client=client)
    assert url.endswith("FAKE")
    client.open_by_key.assert_called_once_with("FAKE_ID")
    ws = sheet.worksheet.return_value
    ws.clear.assert_called_once()
    values = ws.update.call_args.kwargs["values"]
    assert values[0] == HEADER and len(values) == 2


def test_write_sheet_creates_missing_worksheet():
    client = MagicMock()
    sheet = client.open_by_key.return_value
    sheet.worksheet.side_effect = gspread.WorksheetNotFound("nope")
    write_sheet(HEADER, [], "FAKE_ID", "New", client=client)
    sheet.add_worksheet.assert_called_once()


def test_write_sheet_requires_id_and_credentials(monkeypatch):
    with pytest.raises(SinkError):
        write_sheet(HEADER, [], "", client=MagicMock())
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with pytest.raises(SinkError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        write_sheet(HEADER, [], "ID")


def test_cli_sheets_without_credentials_fails_cleanly(monkeypatch, capsys):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    assert main(["--source", "demo", "--output", "sheets", "--spreadsheet-id", "ID"]) == 1
    assert "error:" in capsys.readouterr().err


def test_fetch_api_wraps_network_errors():
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("boom")
    with pytest.raises(fetch.FetchError):
        fetch.fetch_api(session)


def test_fetch_api_returns_lists():
    session = MagicMock()
    resp = MagicMock()
    resp.json.return_value = [{"id": 1}]
    session.get.return_value = resp
    posts, users = fetch.fetch_api(session)
    assert posts == [{"id": 1}] and users == [{"id": 1}]
