"""Tests for cronwatch.cli_tags sub-commands."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.cli_tags import cmd_tags


class Args:
    def __init__(self, config: str, tags_cmd: str | None = None, tag: str = ""):
        self.config = config
        self.tags_cmd = tags_cmd
        self.tag = tag


@pytest.fixture()
def config_file(tmp_path: Path) -> str:
    cfg = tmp_path / "cw.toml"
    cfg.write_text(
        textwrap.dedent("""
            [cronwatch]
            db_path = ":memory:"
            check_interval = 60

            [[jobs]]
            name = "backup"
            schedule = "0 2 * * *"
            tags = ["daily", "critical"]

            [[jobs]]
            name = "report"
            schedule = "0 6 * * *"
            tags = ["daily"]
        """)
    )
    return str(cfg)


def test_list_tags_exits_zero(config_file: str) -> None:
    args = Args(config=config_file)
    assert cmd_tags(args) == 0


def test_list_tags_output(config_file: str, capsys: pytest.CaptureFixture) -> None:
    args = Args(config=config_file)
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "critical" in out
    assert "daily" in out


def test_show_known_tag_exits_zero(config_file: str) -> None:
    args = Args(config=config_file, tags_cmd="show", tag="daily")
    assert cmd_tags(args) == 0


def test_show_known_tag_lists_jobs(config_file: str, capsys: pytest.CaptureFixture) -> None:
    args = Args(config=config_file, tags_cmd="show", tag="daily")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "report" in out


def test_show_unknown_tag_exits_one(config_file: str) -> None:
    args = Args(config=config_file, tags_cmd="show", tag="nonexistent")
    assert cmd_tags(args) == 1


def test_missing_config_exits_two(tmp_path: Path) -> None:
    args = Args(config=str(tmp_path / "no.toml"))
    assert cmd_tags(args) == 2
