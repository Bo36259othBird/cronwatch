"""Tests for cronwatch.run_verifier."""
from __future__ import annotations

import datetime
import pytest

from cronwatch.store import JobStore
from cronwatch.run_verifier import RunVerifier, VerificationResult


@pytest.fixture()
def store(tmp_path):
    return JobStore(str(tmp_path / "test.db"))


@pytest.fixture()
def verifier(store):
    return RunVerifier(store, max_duration_seconds=60.0, allowed_exit_codes=[0])


def _utc(**kw):
    return datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(**kw)


def _add_run(store, job_name, exit_code=0, duration_seconds=10.0):
    run_id = store.record_start(job_name, _utc())
    store.record_finish(run_id, _utc(seconds=duration_seconds), exit_code)
    return run_id


# --- VerificationResult helpers ---

def test_verification_result_passed_means_not_failed():
    r = VerificationResult(job_name="j", run_id=1, passed=True, reasons=[])
    assert r.failed is False


def test_verification_result_not_passed_means_failed():
    r = VerificationResult(job_name="j", run_id=1, passed=False, reasons=["bad"])
    assert r.failed is True


# --- verify() ---

def test_verify_returns_verification_result(store, verifier):
    run_id = _add_run(store, "backup")
    result = verifier.verify("backup", run_id)
    assert isinstance(result, VerificationResult)


def test_verify_passes_for_clean_run(store, verifier):
    run_id = _add_run(store, "backup", exit_code=0, duration_seconds=10.0)
    result = verifier.verify("backup", run_id)
    assert result.passed is True
    assert result.reasons == []


def test_verify_fails_for_nonzero_exit_code(store, verifier):
    run_id = _add_run(store, "backup", exit_code=1, duration_seconds=5.0)
    result = verifier.verify("backup", run_id)
    assert result.passed is False
    assert any("exit code" in r for r in result.reasons)


def test_verify_fails_when_duration_exceeds_max(store, verifier):
    run_id = _add_run(store, "backup", exit_code=0, duration_seconds=120.0)
    result = verifier.verify("backup", run_id)
    assert result.passed is False
    assert any("duration" in r for r in result.reasons)


def test_verify_unknown_run_id_returns_failure(store, verifier):
    result = verifier.verify("backup", 99999)
    assert result.passed is False
    assert any("not found" in r for r in result.reasons)


def test_verify_custom_allowed_exit_codes(store):
    v = RunVerifier(store, allowed_exit_codes=[0, 2])
    run_id = _add_run(store, "cleanup", exit_code=2, duration_seconds=5.0)
    result = v.verify("cleanup", run_id)
    assert result.passed is True


def test_verify_no_max_duration_allows_long_run(store):
    v = RunVerifier(store, max_duration_seconds=None)
    run_id = _add_run(store, "longrun", exit_code=0, duration_seconds=9999.0)
    result = v.verify("longrun", run_id)
    assert result.passed is True


# --- verify_all() ---

def test_verify_all_returns_list(store, verifier):
    _add_run(store, "myjob")
    _add_run(store, "myjob")
    results = verifier.verify_all("myjob")
    assert isinstance(results, list)
    assert len(results) == 2


def test_verify_all_empty_store_returns_empty(store, verifier):
    results = verifier.verify_all("nonexistent")
    assert results == []
