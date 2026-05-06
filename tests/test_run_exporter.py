"""Tests for cronwatch.run_exporter."""

from __future__ import annotations

import csv
import io
import json
import pytest

from cronwatch.store import JobStore
from cronwatch.run_exporter import RunExporter


JOB = "backup"


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def exporter(store):
    return RunExporter(store)


def _add_run(store: JobStore, job: str = JOB, exit_code: int = 0) -> int:
    run_id = store.record_start(job)
    store.record_finish(run_id, exit_code=exit_code, error=None)
    return run_id


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def test_export_json_empty_store(exporter):
    result = exporter.export_json(JOB)
    data = json.loads(result)
    assert data == []


def test_export_json_returns_list(store, exporter):
    _add_run(store)
    data = json.loads(exporter.export_json(JOB))
    assert isinstance(data, list)
    assert len(data) == 1


def test_export_json_contains_expected_fields(store, exporter):
    _add_run(store)
    record = json.loads(exporter.export_json(JOB))[0]
    for field in ("id", "job_name", "started_at", "exit_code"):
        assert field in record


def test_export_json_job_name_matches(store, exporter):
    _add_run(store)
    record = json.loads(exporter.export_json(JOB))[0]
    assert record["job_name"] == JOB


def test_export_json_limit(store, exporter):
    for _ in range(5):
        _add_run(store)
    data = json.loads(exporter.export_json(JOB, limit=2))
    assert len(data) == 2


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def test_export_csv_empty_store(exporter):
    result = exporter.export_csv(JOB)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert rows == []


def test_export_csv_has_header(store, exporter):
    _add_run(store)
    result = exporter.export_csv(JOB)
    assert "job_name" in result.splitlines()[0]


def test_export_csv_row_count(store, exporter):
    _add_run(store)
    _add_run(store)
    result = exporter.export_csv(JOB)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 2


def test_export_csv_limit(store, exporter):
    for _ in range(4):
        _add_run(store)
    result = exporter.export_csv(JOB, limit=3)
    reader = csv.DictReader(io.StringIO(result))
    assert len(list(reader)) == 3
