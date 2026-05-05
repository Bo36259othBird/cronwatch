"""Configuration loader for cronwatch."""

import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    name: str
    schedule: str
    timeout: int = 3600          # seconds before considered silent
    alert_email: Optional[str] = None
    alert_on_failure: bool = True
    alert_on_silence: bool = True


@dataclass
class CronwatchConfig:
    log_file: str = "/var/log/cronwatch.log"
    db_path: str = "/var/lib/cronwatch/jobs.db"
    check_interval: int = 60     # seconds between daemon checks
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_from: str = "cronwatch@localhost"
    jobs: List[JobConfig] = field(default_factory=list)


def load_config(path: str) -> CronwatchConfig:
    """Load configuration from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as fh:
        raw = json.load(fh)

    jobs = [
        JobConfig(
            name=j["name"],
            schedule=j["schedule"],
            timeout=j.get("timeout", 3600),
            alert_email=j.get("alert_email"),
            alert_on_failure=j.get("alert_on_failure", True),
            alert_on_silence=j.get("alert_on_silence", True),
        )
        for j in raw.get("jobs", [])
    ]

    return CronwatchConfig(
        log_file=raw.get("log_file", "/var/log/cronwatch.log"),
        db_path=raw.get("db_path", "/var/lib/cronwatch/jobs.db"),
        check_interval=raw.get("check_interval", 60),
        smtp_host=raw.get("smtp_host", "localhost"),
        smtp_port=raw.get("smtp_port", 25),
        smtp_from=raw.get("smtp_from", "cronwatch@localhost"),
        jobs=jobs,
    )
