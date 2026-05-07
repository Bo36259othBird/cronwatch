"""Tests for RunLabeler and label_formatter."""
from __future__ import annotations

import json
import pytest

from cronwatch.store import JobStore
from cronwatch.run_labeler import RunLabeler
from cronwatch.label_formatter import format_labels, format_label_runs


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def labeler(store):
    return RunLabeler(store)


# ------------------------------------------------------------------
# RunLabeler
# ------------------------------------------------------------------


def test_get_labels_empty_for_unknown_run(labeler):
    assert labeler.get_labels(999) == {}


def test_set_and_get_label(labeler):
    labeler.set_label(1, "backup", "env", "prod")
    labels = labeler.get_labels(1)
    assert labels == {"env": "prod"}


def test_multiple_labels_on_same_run(labeler):
    labeler.set_label(2, "backup", "env", "staging")
    labeler.set_label(2, "backup", "team", "ops")
    labels = labeler.get_labels(2)
    assert labels["env"] == "staging"
    assert labels["team"] == "ops"


def test_remove_label(labeler):
    labeler.set_label(3, "sync", "retry", "true")
    labeler.remove_label(3, "retry")
    assert labeler.get_labels(3) == {}


def test_remove_nonexistent_label_is_noop(labeler):
    # should not raise
    labeler.remove_label(99, "missing")


def test_runs_with_label_key_only(labeler):
    labeler.set_label(10, "nightly", "env", "prod")
    labeler.set_label(11, "nightly", "env", "staging")
    labeler.set_label(12, "nightly", "team", "ops")
    result = labeler.runs_with_label("nightly", "env")
    assert set(result) == {10, 11}


def test_runs_with_label_key_and_value(labeler):
    labeler.set_label(20, "daily", "env", "prod")
    labeler.set_label(21, "daily", "env", "staging")
    result = labeler.runs_with_label("daily", "env", "prod")
    assert result == [20]


def test_runs_with_label_empty_when_no_match(labeler):
    assert labeler.runs_with_label("ghost", "env") == []


# ------------------------------------------------------------------
# label_formatter
# ------------------------------------------------------------------


def test_format_labels_text_contains_run_id():
    out = format_labels(42, {"env": "prod"})
    assert "42" in out


def test_format_labels_text_shows_key_value():
    out = format_labels(1, {"env": "prod", "team": "ops"})
    assert "env: prod" in out
    assert "team: ops" in out


def test_format_labels_text_none_placeholder():
    out = format_labels(5, {})
    assert "(none)" in out


def test_format_labels_json_is_valid():
    out = format_labels(7, {"x": "y"}, fmt="json")
    data = json.loads(out)
    assert data["run_id"] == 7
    assert data["labels"] == {"x": "y"}


def test_format_label_runs_text_contains_job():
    out = format_label_runs("backup", "env", [1, 2])
    assert "backup" in out
    assert "env" in out


def test_format_label_runs_json():
    out = format_label_runs("sync", "team", [5, 6], fmt="json")
    data = json.loads(out)
    assert data["job"] == "sync"
    assert data["run_ids"] == [5, 6]
