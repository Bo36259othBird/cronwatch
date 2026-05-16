"""Tests for ledger_formatter."""
import json
import pytest
from cronwatch.run_ledger import LedgerEntry
from cronwatch.ledger_formatter import format_ledger


def _entry(name="backup", runs=10, ok=8, fail=2, first="2024-01-01T00:00:00", last="2024-06-01T00:00:00"):
    return LedgerEntry(
        job_name=name,
        total_runs=runs,
        total_successes=ok,
        total_failures=fail,
        first_run_at=first,
        last_run_at=last,
    )


def test_text_contains_header():
    out = format_ledger([_entry()], fmt="text")
    assert "Run Ledger" in out


def test_text_contains_job_name():
    out = format_ledger([_entry(name="mybackup")], fmt="text")
    assert "mybackup" in out


def test_text_shows_run_counts():
    out = format_ledger([_entry(runs=10, ok=8, fail=2)], fmt="text")
    assert "runs=10" in out
    assert "ok=8" in out
    assert "fail=2" in out


def test_text_shows_success_rate():
    out = format_ledger([_entry(runs=4, ok=3, fail=1)], fmt="text")
    assert "75.0%" in out


def test_text_shows_first_and_last():
    out = format_ledger([_entry(first="2024-01-01T00:00:00", last="2024-06-01T00:00:00")], fmt="text")
    assert "2024-01-01" in out
    assert "2024-06-01" in out


def test_text_empty_entries():
    out = format_ledger([], fmt="text")
    assert "no entries" in out


def test_json_format_is_valid_json():
    out = format_ledger([_entry()], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1


def test_json_contains_expected_fields():
    out = format_ledger([_entry(name="sync")], fmt="json")
    data = json.loads(out)
    entry = data[0]
    assert entry["job_name"] == "sync"
    assert "total_runs" in entry
    assert "total_successes" in entry
    assert "total_failures" in entry
    assert "success_rate" in entry


def test_json_multiple_entries():
    entries = [_entry(name="a"), _entry(name="b")]
    out = format_ledger(entries, fmt="json")
    data = json.loads(out)
    assert len(data) == 2
    names = {d["job_name"] for d in data}
    assert names == {"a", "b"}


def test_text_na_when_no_runs():
    entry = LedgerEntry(
        job_name="ghost",
        total_runs=0,
        total_successes=0,
        total_failures=0,
        first_run_at=None,
        last_run_at=None,
    )
    out = format_ledger([entry], fmt="text")
    assert "N/A" in out
