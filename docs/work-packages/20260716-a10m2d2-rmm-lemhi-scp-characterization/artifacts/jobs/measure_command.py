#!/usr/bin/env python3
"""Run one bounded command and append a monotonic timing/status row."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path


FIELDS = (
    "label",
    "direction",
    "logical_bytes",
    "trial",
    "compression",
    "status",
    "elapsed_ns",
    "elapsed_seconds",
    "mib_per_second",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--direction", required=True)
    parser.add_argument("--bytes", required=True, type=int)
    parser.add_argument("--trial", required=True, type=int)
    parser.add_argument("--compression", choices=("default", "enabled"), required=True)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    if args.bytes < 0 or args.trial < 1 or args.timeout < 1:
        parser.error("bytes must be nonnegative; trial and timeout must be positive")
    return args


def main() -> int:
    args = parse_args()
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter_ns()
    with args.log.open("wb") as log_handle:
        try:
            completed = subprocess.run(
                args.command,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                timeout=args.timeout,
                check=False,
            )
            status = completed.returncode
        except subprocess.TimeoutExpired:
            status = 124
            log_handle.write(b"command_timeout=1\n")
    elapsed_ns = time.perf_counter_ns() - started
    elapsed_seconds = elapsed_ns / 1_000_000_000
    mib_per_second = ""
    if args.bytes > 0 and elapsed_seconds > 0:
        mib_per_second = f"{args.bytes / 1_048_576 / elapsed_seconds:.6f}"

    needs_header = not args.results.exists()
    with args.results.open("a", encoding="utf-8", newline="") as results_handle:
        writer = csv.DictWriter(
            results_handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n"
        )
        if needs_header:
            writer.writeheader()
        writer.writerow(
            {
                "label": args.label,
                "direction": args.direction,
                "logical_bytes": args.bytes,
                "trial": args.trial,
                "compression": args.compression,
                "status": status,
                "elapsed_ns": elapsed_ns,
                "elapsed_seconds": f"{elapsed_seconds:.9f}",
                "mib_per_second": mib_per_second,
            }
        )

    return status


if __name__ == "__main__":
    sys.exit(main())
