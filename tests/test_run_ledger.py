"""Tests for RunLedger."""
import pytest
from cronwatch.store import JobStore
from cronwatch.run_ledger import RunLedger, LedgerEntry


@pytest.fixture
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture
def ledger(store):
    return RunLedger(store)


def _add_run(store, job, exit_code=0, start="2024-01-01T10:00:00", end="2024-01-01T10:01:00"):
    run_id = store.record_start(job, start)
    store.record_finish(run_id, exit_code, end)
    return run_id


def test_entry_returns_ledger_entry_instance(store, ledger):
    entry = ledger.entry("myjob")
    assert isinstance(entry, LedgerEntry)


def test_entry_no_runs_returns_zeros(store, ledger):
    entry = ledger.entry("ghost")
    assert entry.total_runs == 0
    assert entry.total_successes == 0
    assert entry.total_failures == 0


def test_entry_no_runs_success_rate_is_none(store, ledger):
    entry = ledger.entry("ghost")
    assert entry.success_rate is None
    assert entry.failure_rate is None


def test_entry_counts_successes(store, ledger):
    _add_run(store, "backup", exit_code=0)
    _add_run(store, "backup", exit_code=0)
    entry = ledger.entry("backup")
    assert entry.total_runs == 2
    assert entry.total_successes == 2
    assert entry.total_failures == 0


def test_entry_counts_failures(store, ledger):
    _add_run(store, "sync", exit_code=0)
    _add_run(store, "sync", exit_code=1)
    entry = ledger.entry("sync")
    assert entry.total_failures == 1
    assert entry.total_successes == 1


def test_entry_success_rate(store, ledger):
    _add_run(store, "job", exit_code=0)
    _add_run(store, "job", exit_code=0)
    _add_run(store, "job", exit_code=1)
    entry = ledger.entry("job")
    assert abs(entry.success_rate - 2 / 3) < 1e-9


def test_entry_failure_rate(store, ledger):
    _add_run(store, "job", exit_code=1)
    _add_run(store, "job", exit_code=1)
    entry = ledger.entry("job")
    assert entry.failure_rate == 1.0


def test_entry_first_and_last_run(store, ledger):
    _add_run(store, "nightly", start="2024-01-01T00:00:00", end="2024-01-01T00:01:00")
    _add_run(store, "nightly", start="2024-01-02T00:00:00", end="2024-01-02T00:01:00")
    entry = ledger.entry("nightly")
    assert entry.first_run_at is not None
    assert entry.last_run_at is not None
    assert entry.first_run_at < entry.last_run_at


def test_all_entries_returns_list(store, ledger):
    _add_run(store, "a")
    _add_run(store, "b")
    entries = ledger.all_entries(["a", "b"])
    assert len(entries) == 2
    names = {e.job_name for e in entries}
    assert names == {"a", "b"}


def test_incomplete_runs_excluded(store, ledger):
    run_id = store.record_start("partial", "2024-01-01T10:00:00")
    # no record_finish — run is still active
    entry = ledger.entry("partial")
    assert entry.total_runs == 0
