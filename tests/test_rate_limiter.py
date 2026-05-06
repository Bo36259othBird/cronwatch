"""Tests for cronwatch.rate_limiter."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from cronwatch.rate_limiter import RateLimiter

NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def limiter() -> RateLimiter:
    return RateLimiter(cooldown_seconds=60)


def _patch_now(rl: RateLimiter, dt: datetime):
    return patch.object(rl, "_now", return_value=dt)


def test_first_alert_is_always_sent(limiter):
    with _patch_now(limiter, NOW):
        assert limiter.should_send("job_a") is True


def test_second_alert_within_cooldown_suppressed(limiter):
    with _patch_now(limiter, NOW):
        limiter.should_send("job_a")
    soon = NOW + timedelta(seconds=30)
    with _patch_now(limiter, soon):
        assert limiter.should_send("job_a") is False


def test_alert_allowed_after_cooldown(limiter):
    with _patch_now(limiter, NOW):
        limiter.should_send("job_a")
    later = NOW + timedelta(seconds=61)
    with _patch_now(limiter, later):
        assert limiter.should_send("job_a") is True


def test_different_keys_are_independent(limiter):
    with _patch_now(limiter, NOW):
        limiter.should_send("job_a")
    with _patch_now(limiter, NOW):
        assert limiter.should_send("job_b") is True


def test_reset_clears_state(limiter):
    with _patch_now(limiter, NOW):
        limiter.should_send("job_a")
    limiter.reset("job_a")
    with _patch_now(limiter, NOW):
        assert limiter.should_send("job_a") is True


def test_get_count_increments(limiter):
    with _patch_now(limiter, NOW):
        limiter.should_send("job_a")
    with _patch_now(limiter, NOW + timedelta(seconds=90)):
        limiter.should_send("job_a")
    assert limiter.get_count("job_a") == 2


def test_get_count_zero_for_unknown_key(limiter):
    assert limiter.get_count("unknown") == 0


def test_next_allowed_returns_none_for_unknown(limiter):
    assert limiter.next_allowed("unknown") is None


def test_next_allowed_returns_future_datetime(limiter):
    with _patch_now(limiter, NOW):
        limiter.should_send("job_a")
    expected = NOW + timedelta(seconds=60)
    assert limiter.next_allowed("job_a") == expected
