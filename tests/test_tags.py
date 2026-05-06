"""Tests for cronwatch.tags module."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.tags import TagGroup, TagIndex


def _make_config(*job_defs) -> CronwatchConfig:
    """Build a minimal CronwatchConfig from (name, tags) pairs."""
    jobs = []
    for name, tags in job_defs:
        j = MagicMock(spec=JobConfig)
        j.name = name
        j.tags = tags
        jobs.append(j)
    cfg = MagicMock(spec=CronwatchConfig)
    cfg.jobs = jobs
    return cfg


@pytest.fixture()
def index() -> TagIndex:
    cfg = _make_config(
        ("backup", ["daily", "critical"]),
        ("report", ["daily"]),
        ("cleanup", ["weekly"]),
        ("ping", []),
    )
    return TagIndex(cfg)


def test_tags_returns_sorted_list(index: TagIndex) -> None:
    assert index.tags() == ["critical", "daily", "weekly"]


def test_jobs_for_known_tag(index: TagIndex) -> None:
    names = [j.name for j in index.jobs_for_tag("daily")]
    assert sorted(names) == ["backup", "report"]


def test_jobs_for_unknown_tag_is_empty(index: TagIndex) -> None:
    assert index.jobs_for_tag("nonexistent") == []


def test_group_returns_tag_group(index: TagIndex) -> None:
    grp = index.group("weekly")
    assert isinstance(grp, TagGroup)
    assert grp.tag == "weekly"
    assert grp.job_names == ["cleanup"]


def test_group_returns_none_for_unknown_tag(index: TagIndex) -> None:
    assert index.group("missing") is None


def test_all_groups_count(index: TagIndex) -> None:
    groups = index.all_groups()
    assert len(groups) == 3


def test_jobs_matching_any_deduplicates(index: TagIndex) -> None:
    # "backup" has both "daily" and "critical"
    jobs = index.jobs_matching_any(["daily", "critical"])
    names = [j.name for j in jobs]
    assert names.count("backup") == 1
    assert len(names) == 2  # backup + report


def test_untagged_job_not_in_index(index: TagIndex) -> None:
    # "ping" has no tags; should not appear in any group
    for grp in index.all_groups():
        assert "ping" not in grp.job_names
