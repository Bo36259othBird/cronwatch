"""Tests for RunComparator and RunDiff."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronwatch.run_comparator import RunComparator, RunDiff, _duration
from cronwatch.store import JobRun


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _run(
    run_id: int,
    job_name: str = "backup",
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    exit_code: int | None = None,
) -> JobRun:
    return JobRun(
        id=run_id,
        job_name=job_name,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=exit_code,
    )


@pytest.fixture()
def comparator() -> RunComparator:
    return RunComparator()


def test_compare_returns_run_diff(comparator: RunComparator) -> None:
    a = _run(1, started_at=_utc(2024, 1, 1, 0, 0, 0), finished_at=_utc(2024, 1, 1, 0, 0, 10), exit_code=0)
    b = _run(2, started_at=_utc(2024, 1, 2, 0, 0, 0), finished_at=_utc(2024, 1, 2, 0, 0, 15), exit_code=0)
    result = comparator.compare(a, b)
    assert isinstance(result, RunDiff)


def test_duration_delta_is_positive_when_slower(comparator: RunComparator) -> None:
    a = _run(1, started_at=_utc(2024, 1, 1, 0, 0, 0), finished_at=_utc(2024, 1, 1, 0, 0, 10), exit_code=0)
    b = _run(2, started_at=_utc(2024, 1, 2, 0, 0, 0), finished_at=_utc(2024, 1, 2, 0, 0, 20), exit_code=0)
    diff = comparator.compare(a, b)
    assert diff.duration_delta == pytest.approx(10.0)
    assert diff.slower is True
    assert diff.faster is False


def test_duration_delta_is_negative_when_faster(comparator: RunComparator) -> None:
    a = _run(1, started_at=_utc(2024, 1, 1, 0, 0, 0), finished_at=_utc(2024, 1, 1, 0, 0, 20), exit_code=0)
    b = _run(2, started_at=_utc(2024, 1, 2, 0, 0, 0), finished_at=_utc(2024, 1, 2, 0, 0, 10), exit_code=0)
    diff = comparator.compare(a, b)
    assert diff.duration_delta == pytest.approx(-10.0)
    assert diff.faster is True
    assert diff.slower is False


def test_status_changed_when_exit_codes_differ(comparator: RunComparator) -> None:
    a = _run(1, started_at=_utc(2024, 1, 1, 0, 0, 0), finished_at=_utc(2024, 1, 1, 0, 0, 5), exit_code=0)
    b = _run(2, started_at=_utc(2024, 1, 2, 0, 0, 0), finished_at=_utc(2024, 1, 2, 0, 0, 5), exit_code=1)
    diff = comparator.compare(a, b)
    assert diff.status_changed is True


def test_status_not_changed_when_same_exit_code(comparator: RunComparator) -> None:
    a = _run(1, started_at=_utc(2024, 1, 1, 0, 0, 0), finished_at=_utc(2024, 1, 1, 0, 0, 5), exit_code=0)
    b = _run(2, started_at=_utc(2024, 1, 2, 0, 0, 0), finished_at=_utc(2024, 1, 2, 0, 0, 5), exit_code=0)
    diff = comparator.compare(a, b)
    assert diff.status_changed is False


def test_compare_raises_for_different_jobs(comparator: RunComparator) -> None:
    a = _run(1, job_name="backup")
    b = _run(2, job_name="cleanup")
    with pytest.raises(ValueError, match="Cannot compare runs for different jobs"):
        comparator.compare(a, b)


def test_duration_none_for_incomplete_run() -> None:
    run = _run(1, started_at=_utc(2024, 1, 1, 0, 0, 0), finished_at=None, exit_code=None)
    assert _duration(run) is None


def test_delta_none_when_either_run_incomplete(comparator: RunComparator) -> None:
    a = _run(1, started_at=_utc(2024, 1, 1, 0, 0, 0), finished_at=None, exit_code=None)
    b = _run(2, started_at=_utc(2024, 1, 2, 0, 0, 0), finished_at=_utc(2024, 1, 2, 0, 0, 5), exit_code=0)
    diff = comparator.compare(a, b)
    assert diff.duration_delta is None
