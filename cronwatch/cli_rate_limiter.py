"""CLI helpers to inspect rate-limiter state (sub-command: rate-limit)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Optional

from cronwatch.rate_limiter import RateLimiter


def add_rate_limit_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *rate-limit* sub-command."""
    p = subparsers.add_parser(
        "rate-limit",
        help="Inspect or reset alert rate-limiter state",
    )
    p.add_argument("--key", metavar="JOB", help="Job name / alert key to inspect")
    p.add_argument(
        "--reset",
        metavar="JOB",
        help="Reset rate-limit state for the given job key",
    )
    p.set_defaults(func=cmd_rate_limit)


def _fmt_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        return "n/a"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def cmd_rate_limit(args: argparse.Namespace, limiter: RateLimiter) -> int:
    """Handle the *rate-limit* sub-command.

    Parameters
    ----------
    args:
        Parsed CLI arguments.
    limiter:
        The shared :class:`RateLimiter` instance from the running daemon.
        In tests this is injected directly; in production the daemon passes
        its own instance.
    """
    if args.reset:
        limiter.reset(args.reset)
        print(f"Rate-limit state cleared for '{args.reset}'.")
        return 0

    if args.key:
        count = limiter.get_count(args.key)
        next_ok = _fmt_dt(limiter.next_allowed(args.key))
        print(f"Key          : {args.key}")
        print(f"Alerts sent  : {count}")
        print(f"Next allowed : {next_ok}")
        return 0

    print("Specify --key <JOB> to inspect or --reset <JOB> to clear state.")
    return 1
