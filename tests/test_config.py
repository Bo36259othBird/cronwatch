"""Tests for cronwatch configuration loader."""

import json
import pytest
from pathlib import Path

from cronwatch.config import load_config, CronwatchConfig, JobConfig


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    data = {
        "log_file": "/tmp/cronwatch.log",
        "db_path": "/tmp/cronwatch.db",
        "check_interval": 30,
        "smtp_host": "mail.example.com",
        "smtp_port": 587,
        "smtp_from": "alerts@example.com",
        "jobs": [
            {
                "name": "nightly-backup",
                "schedule": "0 2 * * *",
                "timeout": 7200,
                "alert_email": "ops@example.com",
                "alert_on_failure": True,
                "alert_on_silence": True,
            },
            {
                "name": "hourly-sync",
                "schedule": "0 * * * *",
            },
        ],
    }
    path = tmp_path / "cronwatch.json"
    path.write_text(json.dumps(data))
    return path


def test_load_config_returns_correct_type(config_file):
    cfg = load_config(str(config_file))
    assert isinstance(cfg, CronwatchConfig)


def test_load_config_top_level_fields(config_file):
    cfg = load_config(str(config_file))
    assert cfg.log_file == "/tmp/cronwatch.log"
    assert cfg.db_path == "/tmp/cronwatch.db"
    assert cfg.check_interval == 30
    assert cfg.smtp_host == "mail.example.com"
    assert cfg.smtp_port == 587
    assert cfg.smtp_from == "alerts@example.com"


def test_load_config_jobs_count(config_file):
    cfg = load_config(str(config_file))
    assert len(cfg.jobs) == 2


def test_load_config_job_fields(config_file):
    cfg = load_config(str(config_file))
    job = cfg.jobs[0]
    assert isinstance(job, JobConfig)
    assert job.name == "nightly-backup"
    assert job.schedule == "0 2 * * *"
    assert job.timeout == 7200
    assert job.alert_email == "ops@example.com"


def test_load_config_job_defaults(config_file):
    cfg = load_config(str(config_file))
    job = cfg.jobs[1]
    assert job.timeout == 3600
    assert job.alert_email is None
    assert job.alert_on_failure is True
    assert job.alert_on_silence is True


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/cronwatch.json")


def test_load_config_empty_jobs(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({}))
    cfg = load_config(str(path))
    assert cfg.jobs == []
    assert cfg.log_file == "/var/log/cronwatch.log"
