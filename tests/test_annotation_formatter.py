"""Tests for annotation_formatter."""
from __future__ import annotations

import json

import pytest

from cronwatch.run_annotator import AnnotatedRun
from cronwatch.annotation_formatter import (
    format_annotated_run,
    format_annotated_runs,
)


def _run(run_id: int = 1, job: str = "backup", **kw) -> AnnotatedRun:
    return AnnotatedRun(run_id=run_id, job_name=job, annotations=kw)


# ---------------------------------------------------------------------------
# text format
# ---------------------------------------------------------------------------


def test_text_contains_run_id():
    out = format_annotated_run(_run(42, "sync"), fmt="text")
    assert "42" in out


def test_text_contains_job_name():
    out = format_annotated_run(_run(1, "nightly"), fmt="text")
    assert "nightly" in out


def test_text_shows_annotations():
    out = format_annotated_run(_run(1, "backup", env="prod", region="eu"), fmt="text")
    assert "env: prod" in out
    assert "region: eu" in out


def test_text_shows_no_annotations_placeholder():
    out = format_annotated_run(_run(1, "backup"), fmt="text")
    assert "no annotations" in out


# ---------------------------------------------------------------------------
# json format
# ---------------------------------------------------------------------------


def test_json_is_valid():
    out = format_annotated_run(_run(5, "deploy", env="staging"), fmt="json")
    data = json.loads(out)
    assert data["run_id"] == 5
    assert data["job_name"] == "deploy"
    assert data["annotations"]["env"] == "staging"


def test_json_empty_annotations():
    out = format_annotated_run(_run(3, "check"), fmt="json")
    data = json.loads(out)
    assert data["annotations"] == {}


# ---------------------------------------------------------------------------
# list formatting
# ---------------------------------------------------------------------------


def test_format_list_text_contains_all_jobs():
    runs = [_run(1, "alpha"), _run(2, "beta")]
    out = format_annotated_runs(runs, fmt="text")
    assert "alpha" in out
    assert "beta" in out


def test_format_list_json_is_list():
    runs = [_run(1, "alpha", k="v"), _run(2, "beta")]
    data = json.loads(format_annotated_runs(runs, fmt="json"))
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["annotations"]["k"] == "v"
