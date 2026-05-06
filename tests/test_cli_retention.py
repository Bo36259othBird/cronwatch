"""Tests for the retention CLI sub-command."""
from __future__ import annotations

import textwrap
from pathlib import Path
from datetime import datetime, timedelta

import pytest

from cronwatch.cli_retention import cmd_retention
from cronwatch.store import JobStore


@pytest.fixture()
def config_file(tmp_path):
    db = tmp_path / "cw.db"
    cfg = tmp_path / "cronwatch.toml"
    cfg.write_text(
        textwrap.dedent(
            f"""\
            db_path = "{db}"
            [jobs]
            [jobs.nightly]
            schedule = "0 2 * * *"
            silence_threshold_minutes = 60
            """
        )
    )
    return str(cfg)


def _make_args(config, retention_cmd="prune", max_age_days=None, max_runs=None):
    class Args:
        pass
    a = Args()
    a.config = config
    a.retention_cmd = retention_cmd
    a.max_age_days = max_age_days
    a.max_runs = max_runs
    return a


def test_prune_exits_zero(config_file):
    args = _make_args(config_file)
    assert cmd_retention(args) == 0


def test_prune_missing_config(tmp_path):
    args = _make_args(str(tmp_path / "missing.toml"))
    assert cmd_retention(args) == 2


def test_prune_unknown_subcommand(config_file):
    args = _make_args(config_file, retention_cmd="unknown")
    assert cmd_retention(args) == 1


def test_prune_deletes_old_records(config_file, tmp_path, capsys):
    from cronwatch.config import load_config
    cfg = load_config(config_file)
    store = JobStore(cfg.db_path)
    old_start = datetime.utcnow() - timedelta(days=60)
    run_id = store.record_start("nightly", old_start)
    store.record_finish(run_id, success=True, exit_code=0,
                        finished_at=old_start + timedelta(seconds=5))

    args = _make_args(config_file, max_age_days=30)
    result = cmd_retention(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "1" in captured.out
