"""CLI sub-command: cronwatch checkpoint."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.store import JobStore
from cronwatch.run_checkpoint import RunCheckpointer
from cronwatch.checkpoint_formatter import format_checkpoints


def add_checkpoint_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("checkpoint", help="Show checkpoints for a job run")
    p.add_argument("--config", required=True, help="Path to cronwatch config file")
    p.add_argument("--job", required=True, help="Job name")
    p.add_argument("--run-id", required=True, type=int, dest="run_id",
                   help="Run ID to inspect")
    p.add_argument("--format", choices=["text", "json"], default="text",
                   dest="fmt", help="Output format")


def cmd_checkpoint(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    store = JobStore(cfg.db_path)
    checkpointer = RunCheckpointer(store)
    summary = checkpointer.get_summary(run_id=args.run_id, job_name=args.job)
    print(format_checkpoints([summary], fmt=args.fmt), end="")
    return 0
