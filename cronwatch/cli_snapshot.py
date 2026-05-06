"""CLI sub-command: snapshot — capture and display current job states."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace

from cronwatch.config import load_config
from cronwatch.silence_detector import SilenceDetector
from cronwatch.snapshot import SnapshotWriter, build_snapshot
from cronwatch.store import JobStore


def add_snapshot_subparser(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "snapshot", help="Capture a point-in-time snapshot of all job states"
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config file")
    p.add_argument(
        "--output",
        default=None,
        help="Write snapshot JSON to this file (default: print to stdout)",
    )
    p.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )


def cmd_snapshot(args: Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    store = JobStore(cfg.db_path)
    detector = SilenceDetector(cfg.jobs, store)
    snapshot = build_snapshot([j.name for j in cfg.jobs], store, detector)

    if args.format == "json":
        text = json.dumps(snapshot.to_dict(), indent=2)
    else:
        lines = [f"Snapshot captured at {snapshot.captured_at}", ""]
        for job in snapshot.jobs:
            status = "SILENT" if job.is_silent else "ok"
            dur = (
                f"{job.last_duration_seconds:.1f}s"
                if job.last_duration_seconds is not None
                else "n/a"
            )
            lines.append(
                f"  {job.name:<30} exit={job.last_exit_code!s:<5} dur={dur:<10} [{status}]"
            )
        text = "\n".join(lines)

    if args.output:
        writer = SnapshotWriter(args.output)
        writer.write(snapshot)
        print(f"Snapshot written to {args.output}")
    else:
        print(text)

    return 0
