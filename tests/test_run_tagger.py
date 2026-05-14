"""Tests for cronwatch.run_tagger."""
from __future__ import annotations

import pytest

from cronwatch.store import JobStore
from cronwatch.run_tagger import RunTagger, RunTagSet


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path):
    db = tmp_path / "test.db"
    return JobStore(str(db))


@pytest.fixture()
def tagger(store):
    return RunTagger(store)


def _add_run(store: JobStore, job_name: str = "backup", exit_code: int = 0) -> int:
    run_id = store.record_start(job_name)
    store.record_finish(run_id, exit_code=exit_code)
    return run_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_tags_empty_for_unknown_run(tagger):
    ts = tagger.get_tags(999)
    assert ts.run_id == 999
    assert ts.tags == []


def test_add_and_get_tag(store, tagger):
    run_id = _add_run(store)
    tagger.add_tag(run_id, "nightly")
    ts = tagger.get_tags(run_id)
    assert "nightly" in ts.tags


def test_add_multiple_tags(store, tagger):
    run_id = _add_run(store)
    tagger.add_tag(run_id, "nightly")
    tagger.add_tag(run_id, "critical")
    ts = tagger.get_tags(run_id)
    assert sorted(ts.tags) == ["critical", "nightly"]


def test_duplicate_tag_is_ignored(store, tagger):
    run_id = _add_run(store)
    tagger.add_tag(run_id, "nightly")
    tagger.add_tag(run_id, "nightly")  # should not raise
    ts = tagger.get_tags(run_id)
    assert ts.tags.count("nightly") == 1


def test_remove_tag(store, tagger):
    run_id = _add_run(store)
    tagger.add_tag(run_id, "nightly")
    tagger.remove_tag(run_id, "nightly")
    ts = tagger.get_tags(run_id)
    assert "nightly" not in ts.tags


def test_remove_nonexistent_tag_does_not_raise(store, tagger):
    run_id = _add_run(store)
    tagger.remove_tag(run_id, "ghost")  # should not raise


def test_runs_with_tag(store, tagger):
    r1 = _add_run(store, "job_a")
    r2 = _add_run(store, "job_b")
    r3 = _add_run(store, "job_c")
    tagger.add_tag(r1, "important")
    tagger.add_tag(r2, "important")
    tagger.add_tag(r3, "low-priority")
    result = tagger.runs_with_tag("important")
    assert r1 in result
    assert r2 in result
    assert r3 not in result


def test_all_tags_returns_mapping(store, tagger):
    r1 = _add_run(store)
    r2 = _add_run(store)
    tagger.add_tag(r1, "alpha")
    tagger.add_tag(r1, "beta")
    tagger.add_tag(r2, "gamma")
    mapping = tagger.all_tags()
    assert sorted(mapping[r1]) == ["alpha", "beta"]
    assert mapping[r2] == ["gamma"]


def test_empty_tag_raises(store, tagger):
    run_id = _add_run(store)
    with pytest.raises(ValueError):
        tagger.add_tag(run_id, "   ")


def test_has_tag_helper(store, tagger):
    run_id = _add_run(store)
    tagger.add_tag(run_id, "urgent")
    ts = tagger.get_tags(run_id)
    assert ts.has_tag("urgent") is True
    assert ts.has_tag("routine") is False
