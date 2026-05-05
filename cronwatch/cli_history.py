"""CLI sub-command: cronwatch history — show job run trends."""
from __future__ import annotations

import argparse
import sys
from typing import List

from cronwatch.config import load_config
from cronwatch.history import HistoryAnalyzer
from cronwatch.history_formatter import format_trends
from cronwatch.store import JobStore


def add_history_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "history",
        help="Show job run history and trend analysis",
    )
    p.add_argument(
        "--config", "-c",
        required=True,
        metavar="FILE",
        help="Path to cronwatch config file",
    )
    p.add_argument(
        "--days", "-d",
        type=int,
        default=7,
        metavar="N",
        help="Analysis window in days (default: 7)",
    )
    p.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--job", "-j",
        metavar="NAME",
        help="Limit output to a single job",
    )
    p.set_defaults(func=cmd_history)


def cmd_history(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    store = JobStore(cfg.db_path)
    analyzer = HistoryAnalyzer(store)

    job_names: List[str] = (
        [args.job] if args.job
        else [j.name for j in cfg.jobs]
    )

    trends = analyzer.all_trends(job_names, window_days=args.days)
    print(format_trends(trends, fmt=args.fmt), end="")
    return 0
