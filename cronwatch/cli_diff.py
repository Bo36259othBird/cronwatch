"""CLI sub-command: cronwatch diff <job> <run_id_a> <run_id_b>."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.diff_formatter import format_diff
from cronwatch.run_comparator import RunComparator
from cronwatch.store import JobStore


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff", help="Compare two runs of the same job")
    p.add_argument("job", help="Job name")
    p.add_argument("run_a", type=int, help="First run ID")
    p.add_argument("run_b", type=int, help="Second run ID")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )
    p.add_argument("--config", default="cronwatch.toml")


def cmd_diff(args: argparse.Namespace) -> int:
    try:
        load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    store = JobStore()
    run_a = store.get_run(args.run_a)
    run_b = store.get_run(args.run_b)

    if run_a is None:
        print(f"Run ID {args.run_a} not found.", file=sys.stderr)
        return 3
    if run_b is None:
        print(f"Run ID {args.run_b} not found.", file=sys.stderr)
        return 3
    if run_a.job_name != args.job or run_b.job_name != args.job:
        print("One or both runs do not belong to the specified job.", file=sys.stderr)
        return 4

    diff = RunComparator().compare(run_a, run_b)
    print(format_diff(diff, fmt=args.fmt))
    return 0
