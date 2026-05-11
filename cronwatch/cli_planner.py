"""CLI sub-command: ``cronwatch plan`` — show upcoming / overdue runs."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.plan_formatter import format_plans
from cronwatch.run_planner import RunPlanner
from cronwatch.store import JobStore


def add_planner_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("plan", help="Show next expected run times for all jobs")
    p.add_argument("--config", required=True, help="Path to cronwatch config file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument("--db", default="cronwatch.db", help="Path to SQLite database")


def cmd_plan(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    store = JobStore(args.db)
    planner = RunPlanner(store)
    plans = planner.plan_all(cfg.jobs)
    print(format_plans(plans, fmt=args.format))
    return 0
