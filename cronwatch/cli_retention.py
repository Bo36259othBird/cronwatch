"""CLI sub-command: cronwatch retention prune."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.retention import RetentionManager, RetentionPolicy
from cronwatch.store import JobStore


def add_retention_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "retention",
        help="Manage job-run history retention",
    )
    sub = parser.add_subparsers(dest="retention_cmd")

    prune = sub.add_parser("prune", help="Delete records older than the retention window")
    prune.add_argument(
        "--max-age-days",
        type=int,
        default=None,
        help="Override max age in days (default: from config or 30)",
    )
    prune.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Keep at most N runs per job",
    )
    parser.set_defaults(func=cmd_retention)


def cmd_retention(args: argparse.Namespace) -> int:
    if args.retention_cmd != "prune":
        print("Usage: cronwatch retention prune [options]", file=sys.stderr)
        return 1

    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    max_age = args.max_age_days if args.max_age_days is not None else 30
    policy = RetentionPolicy(
        max_age_days=max_age,
        max_runs_per_job=args.max_runs,
    )

    store = JobStore(cfg.db_path)
    manager = RetentionManager(store, policy)
    deleted = manager.prune()
    print(f"Pruned {deleted} record(s).")
    return 0
