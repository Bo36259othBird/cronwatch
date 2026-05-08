"""Tests for profile_formatter."""
from __future__ import annotations

import json
import pytest

from cronwatch.run_profiler import RunProfile
from cronwatch.profile_formatter import format_profiles


def _profile(**kwargs) -> RunProfile:
    defaults = dict(
        job_name="backup",
        run_count=10,
        p50=5.123,
        p95=9.456,
        p99=12.789,
        mean=5.5,
        stddev=1.2,
    )
    defaults.update(kwargs)
    return RunProfile(**defaults)


def test_text_contains_job_name():
    out = format_profiles([_profile(job_name="nightly")])
    assert "nightly" in out


def test_text_contains_header():
    out = format_profiles([_profile()])
    assert "Run Profiles" in out


def test_text_shows_percentiles():
    out = format_profiles([_profile(p50=3.0, p95=8.0, p99=11.0)])
    assert "p50" in out
    assert "p95" in out
    assert "p99" in out


def test_text_shows_na_for_none_fields():
    p = _profile(p50=None, p95=None, p99=None, mean=None, stddev=None, run_count=0)
    out = format_profiles([p])
    assert "n/a" in out


def test_json_format_is_valid_json():
    out = format_profiles([_profile()], fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1


def test_json_contains_expected_keys():
    out = format_profiles([_profile()], fmt="json")
    data = json.loads(out)
    keys = data[0].keys()
    assert "job_name" in keys
    assert "p50_s" in keys
    assert "p95_s" in keys
    assert "mean_s" in keys


def test_multiple_profiles_in_text():
    profiles = [_profile(job_name="job_a"), _profile(job_name="job_b")]
    out = format_profiles(profiles)
    assert "job_a" in out
    assert "job_b" in out
