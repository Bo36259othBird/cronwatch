"""Command-line interface for cronwatch."""

import argparse
import sys
from pathlib import Path

from cronwatch.config import load_config
from cronwatch.daemon import CronwatchDaemon
from cronwatch.formatter import format_report
from cronwatch.reporter import Reporter
from cronwatch.store import JobStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Monitor cron job execution and alert on failures or silences.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("cronwatch.toml"),
        help="Path to configuration file (default: cronwatch.toml)",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    subparsers.add_parser("start", help="Start the cronwatch daemon")
    subparsers.add_parser("stop", help="Stop the running cronwatch daemon")

    report_parser = subparsers.add_parser("report", help="Print a job execution report")
    report_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    report_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of past days to include (default: 7)",
    )

    return parser


def cmd_start(config_path: Path) -> int:
    cfg = load_config(config_path)
    daemon = CronwatchDaemon(cfg)
    print("Starting cronwatch daemon...")
    daemon.start()
    return 0


def cmd_report(config_path: Path, fmt: str, days: int) -> int:
    cfg = load_config(config_path)
    store = JobStore(cfg.db_path)
    reporter = Reporter(store, cfg)
    report = reporter.generate(days=days)
    print(format_report(report, fmt))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if not args.config.exists() and args.command != "stop":
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        return 2

    if args.command == "start":
        return cmd_start(args.config)
    if args.command == "stop":
        print("Stop signal sent (not yet implemented as IPC).")
        return 0
    if args.command == "report":
        return cmd_report(args.config, args.format, args.days)

    return 1


if __name__ == "__main__":
    sys.exit(main())
