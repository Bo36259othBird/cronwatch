"""Tests for the cronwatch CLI."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.cli import build_parser, main


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "cronwatch.toml"
    cfg.write_text(
        """
        db_path = ":memory:"
        check_interval = 60

        [[jobs]]
        name = "backup"
        schedule = "0 2 * * *"
        expected_duration = 120
        silence_timeout = 90000
        """
    )
    return cfg


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser.prog == "cronwatch"


def test_no_command_returns_1():
    result = main([])
    assert result == 1


def test_missing_config_returns_2(tmp_path: Path):
    result = main(["--config", str(tmp_path / "missing.toml"), "start"])
    assert result == 2


def test_report_text_exits_zero(config_file: Path):
    with patch("cronwatch.cli.Reporter") as MockReporter:
        mock_report = MagicMock()
        MockReporter.return_value.generate.return_value = mock_report
        with patch("cronwatch.cli.format_report", return_value="report output"):
            result = main(["--config", str(config_file), "report", "--format", "text"])
    assert result == 0


def test_report_json_exits_zero(config_file: Path):
    with patch("cronwatch.cli.Reporter") as MockReporter:
        mock_report = MagicMock()
        MockReporter.return_value.generate.return_value = mock_report
        with patch("cronwatch.cli.format_report", return_value="{}"):
            result = main(["--config", str(config_file), "report", "--format", "json"])
    assert result == 0


def test_report_passes_days_to_generate(config_file: Path):
    with patch("cronwatch.cli.Reporter") as MockReporter:
        mock_instance = MockReporter.return_value
        mock_instance.generate.return_value = MagicMock()
        with patch("cronwatch.cli.format_report", return_value=""):
            main(["--config", str(config_file), "report", "--days", "14"])
    mock_instance.generate.assert_called_once_with(days=14)


def test_stop_command_exits_zero(config_file: Path):
    result = main(["--config", str(config_file), "stop"])
    assert result == 0


def test_start_calls_daemon(config_file: Path):
    with patch("cronwatch.cli.CronwatchDaemon") as MockDaemon:
        result = main(["--config", str(config_file), "start"])
    MockDaemon.return_value.start.assert_called_once()
    assert result == 0
