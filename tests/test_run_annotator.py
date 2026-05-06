"""Tests for RunAnnotator."""
from __future__ import annotations

import pytest

from cronwatch.store import JobStore
from cronwatch.run_annotator import Annotation, AnnotatedRun, RunAnnotator


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "cw.db"))


@pytest.fixture()
def annotator(store):
    return RunAnnotator(store)


@pytest.fixture()
def run_id(store):
    return store.record_start("backup", start_time=None)


# ---------------------------------------------------------------------------


def test_get_returns_empty_dict_for_unknown_run(annotator):
    assert annotator.get(9999) == {}


def test_annotate_and_get(annotator, run_id):
    annotator.annotate(run_id, "env", "prod")
    result = annotator.get(run_id)
    assert result == {"env": "prod"}


def test_annotate_multiple_keys(annotator, run_id):
    annotator.annotate(run_id, "env", "staging")
    annotator.annotate(run_id, "version", "1.2.3")
    result = annotator.get(run_id)
    assert result["env"] == "staging"
    assert result["version"] == "1.2.3"


def test_annotate_overwrites_existing_key(annotator, run_id):
    annotator.annotate(run_id, "env", "dev")
    annotator.annotate(run_id, "env", "prod")
    assert annotator.get(run_id)["env"] == "prod"


def test_delete_existing_annotation(annotator, run_id):
    annotator.annotate(run_id, "env", "prod")
    removed = annotator.delete(run_id, "env")
    assert removed is True
    assert annotator.get(run_id) == {}


def test_delete_missing_annotation_returns_false(annotator, run_id):
    removed = annotator.delete(run_id, "nonexistent")
    assert removed is False


def test_annotated_run_dataclass(annotator, run_id):
    annotator.annotate(run_id, "region", "us-east-1")
    ar = annotator.annotated_run(run_id, "backup")
    assert isinstance(ar, AnnotatedRun)
    assert ar.run_id == run_id
    assert ar.job_name == "backup"
    assert ar.annotations["region"] == "us-east-1"


def test_annotations_isolated_per_run(annotator, store):
    r1 = store.record_start("job_a", start_time=None)
    r2 = store.record_start("job_b", start_time=None)
    annotator.annotate(r1, "k", "v1")
    annotator.annotate(r2, "k", "v2")
    assert annotator.get(r1)["k"] == "v1"
    assert annotator.get(r2)["k"] == "v2"
