"""Configuration loading for cronwatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class JobConfig:
    """Configuration for a single monitored cron job."""

    name: str
    schedule: str
    timeout: Optional[int] = None          # seconds; None means no limit
    silence_window: Optional[int] = None   # seconds before silence alert
    alert_on_failure: bool = True


@dataclass
class CronwatchConfig:
    """Top-level cronwatch configuration."""

    jobs: List[JobConfig] = field(default_factory=list)
    db_path: str = "cronwatch.db"
    log_level: str = "INFO"
    smtp: Optional[Dict[str, Any]] = None  # keys: host, port, from, to


def load_config(path: str | Path) -> CronwatchConfig:
    """Load and parse a YAML configuration file.

    Args:
        path: Path to the YAML config file.

    Returns:
        A populated :class:`CronwatchConfig` instance.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the config is structurally invalid.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open() as fh:
        raw: Dict[str, Any] = yaml.safe_load(fh) or {}

    jobs: List[JobConfig] = []
    for job_raw in raw.get("jobs", []):
        if "name" not in job_raw or "schedule" not in job_raw:
            raise ValueError(f"Job entry missing 'name' or 'schedule': {job_raw}")
        jobs.append(
            JobConfig(
                name=job_raw["name"],
                schedule=job_raw["schedule"],
                timeout=job_raw.get("timeout"),
                silence_window=job_raw.get("silence_window"),
                alert_on_failure=job_raw.get("alert_on_failure", True),
            )
        )

    smtp_raw = raw.get("smtp")

    return CronwatchConfig(
        jobs=jobs,
        db_path=raw.get("db_path", "cronwatch.db"),
        log_level=raw.get("log_level", "INFO"),
        smtp=smtp_raw if isinstance(smtp_raw, dict) else None,
    )
