"""Tests for cronwatch.cli_snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cronwatch.cli_snapshot import cmd_snapshot


CONFIG_CONTENT = """
[cronwatch]
db_path = "{db}"
check_interval = 60

[[jobs]]
name = "daily_backup"
schedule = "0 2 * * *"
silence_timeout = 90000
"""


@pytest.fixture()
def config_file(tmp_path):
    db = tmp_path / "cw.db"
    cfg = tmp_path / "cronwatch.toml"
    cfg.write_text(CONFIG_CONTENT.format(db=str(db)))
    return str(cfg)


def _make_args(**kwargs):
    defaults = dict(config=None, output=None, format="text")
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_snapshot_exits_zero(config_file):
    args = _make_args(config=config_file)
    assert cmd_snapshot(args) == 0


def test_snapshot_missing_config(tmp_path):
    args = _make_args(config=str(tmp_path / "no.toml"))
    assert cmd_snapshot(args) == 2


def test_snapshot_json_format(config_file, capsys):
    args = _make_args(config=config_file, format="json")
    rc = cmd_snapshot(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "captured_at" in data
    assert "jobs" in data
    assert data["jobs"][0]["name"] == "daily_backup"


def test_snapshot_text_format_contains_job_name(config_file, capsys):
    args = _make_args(config=config_file, format="text")
    cmd_snapshot(args)
    captured = capsys.readouterr()
    assert "daily_backup" in captured.out


def test_snapshot_writes_file(config_file, tmp_path):
    out_file = str(tmp_path / "snap.json")
    args = _make_args(config=config_file, output=out_file, format="json")
    rc = cmd_snapshot(args)
    assert rc == 0
    assert Path(out_file).exists()
    data = json.loads(Path(out_file).read_text())
    assert "jobs" in data
