#!/usr/bin/env python3
"""Benchmark the declared fast-batch profile against faithful Rust CLI runs.

This runner deliberately separates the two acceptance contracts. Faithful
samples must retain golden SHA-256 identity. The experimental `fast_batch_v0`
samples must be deterministic across every run and satisfy a structural CLI
check, but they are not compared to legacy goldens.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs/work-packages/20260710-cli-runtime-benchmark/artifacts/benchmark-cases.json"
DEFAULT_RESULTS = ROOT / "docs/work-packages/20260710-fast-batch-rng-spike/artifacts/fast-batch-results.json"
DEFAULT_CSV = ROOT / "docs/work-packages/20260710-fast-batch-rng-spike/artifacts/fast-batch-results.csv"
PROFILE_MARKER = "--generation-profile fast-batch-v0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_version(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip().splitlines()[0]


def read_cpu_model() -> str | None:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists():
        return None
    for line in cpuinfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return None


def binary_metadata(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256(path), "size_bytes": path.stat().st_size}


def remove_output(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def check_faithful_output(path: Path, expected_sha256: str, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label}: did not create {path}")
    actual_sha256 = sha256(path)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(f"{label}: SHA-256 {actual_sha256} != expected {expected_sha256}")


def check_fast_output(path: Path, label: str) -> str:
    if not path.is_file():
        raise RuntimeError(f"{label}: did not create {path}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise RuntimeError(f"{label}: output is not UTF-8") from error
    if len(lines) < 10 or PROFILE_MARKER not in "\n".join(lines[:5]):
        raise RuntimeError(f"{label}: missing fast-profile header marker")
    try:
        header_index = lines.index(" da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew")
    except ValueError as error:
        raise RuntimeError(f"{label}: missing CLI daily-column header") from error
    daily_rows = 0
    for line in lines[header_index + 2 :]:
        if not line.strip():
            break
        fields = line.split()
        if len(fields) != 13:
            raise RuntimeError(f"{label}: malformed daily row {daily_rows + 1}: {line!r}")
        try:
            int(fields[0])
            int(fields[1])
            int(fields[2])
            values = [float(field) for field in fields[3:]]
        except ValueError as error:
            raise RuntimeError(f"{label}: nonnumeric daily row {daily_rows + 1}") from error
        if not all(math.isfinite(value) for value in values):
            raise RuntimeError(f"{label}: non-finite daily row {daily_rows + 1}")
        daily_rows += 1
    if daily_rows == 0:
        raise RuntimeError(f"{label}: no daily rows")
    return sha256(path)


def fast_runspec_text(original: str, output: Path) -> str:
    if "generation_profile:" in original:
        raise RuntimeError("benchmark source runspec already declares a generation profile")
    marker = "cligen_runspec: 1\n"
    if original.count(marker) != 1:
        raise RuntimeError("runspec must contain exactly one cligen_runspec: 1 line")
    lines = original.replace(marker, f"{marker}generation_profile: fast_batch_v0\n", 1).splitlines(
        keepends=True
    )
    output_lines = [index for index, line in enumerate(lines) if line.startswith("  cli:")]
    if len(output_lines) != 1:
        raise RuntimeError("runspec must contain exactly one block-style output.cli line")
    lines[output_lines[0]] = f"  cli: {json.dumps(str(output))}\n"
    return "".join(lines)


def run_process(binary: Path, runspec: Path, output: Path, label: str) -> float:
    remove_output(output)
    command = [str(binary), "run", str(runspec)]
    start = time.perf_counter_ns()
    completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    elapsed = (time.perf_counter_ns() - start) / 1_000_000_000
    if completed.returncode != 0:
        message = completed.stderr.decode(errors="replace")
        raise RuntimeError(f"{label}: {message}")
    return elapsed


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "min_s": min(samples),
        "median_s": statistics.median(samples),
        "mean_s": statistics.fmean(samples),
        "stdev_s": statistics.stdev(samples),
        "max_s": max(samples),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--rust-bin", type=Path, default=ROOT / "target/release/cligen")
    parser.add_argument("--samples", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--fast-output-dir", type=Path, default=ROOT / "target/fast-batch-benchmark")
    parser.add_argument("--case", action="append", dest="case_names")
    args = parser.parse_args()
    if args.samples < 2:
        parser.error("--samples must be at least 2 for standard deviation")
    if args.warmups < 0:
        parser.error("--warmups must not be negative")
    return args


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise RuntimeError("unsupported benchmark manifest schema version")
    cases = manifest["cases"]
    if args.case_names:
        requested = set(args.case_names)
        cases = [case for case in cases if case["name"] in requested]
        missing = requested - {case["name"] for case in cases}
        if missing:
            raise RuntimeError(f"unknown case(s): {', '.join(sorted(missing))}")
    if not cases:
        raise RuntimeError("no benchmark cases selected")
    if not args.rust_bin.is_file():
        raise RuntimeError(f"Rust binary missing: {args.rust_bin}; run cargo build --release --bin cligen")

    faithful_output_dir = ROOT / manifest["runspec_output_dir"]
    faithful_output_dir.mkdir(parents=True, exist_ok=True)
    args.fast_output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for case in cases:
        name = case["name"]
        faithful_output = faithful_output_dir / f"{name}.cli"
        expected_sha256 = sha256(ROOT / case["golden"])
        original_runspec = ROOT / case["runspec"]
        fast_output = args.fast_output_dir / f"{name}.cli"
        fast_runspec = original_runspec.with_name(f".{original_runspec.stem}.fast-batch-v0.bench.yaml")
        fast_runspec.write_text(fast_runspec_text(original_runspec.read_text(encoding="utf-8"), fast_output), encoding="utf-8")
        try:
            fast_sha256: str | None = None

            def run_faithful() -> float:
                elapsed = run_process(args.rust_bin, original_runspec, faithful_output, f"faithful {name}")
                check_faithful_output(faithful_output, expected_sha256, f"faithful {name}")
                return elapsed

            def run_fast() -> float:
                nonlocal fast_sha256
                elapsed = run_process(args.rust_bin, fast_runspec, fast_output, f"fast {name}")
                actual_sha256 = check_fast_output(fast_output, f"fast {name}")
                if fast_sha256 is None:
                    fast_sha256 = actual_sha256
                elif actual_sha256 != fast_sha256:
                    raise RuntimeError(f"fast {name}: output hash changed between repeated executions")
                return elapsed

            for _ in range(args.warmups):
                run_faithful()
                run_fast()
            timings = {"faithful_s": [], "fast_batch_s": []}
            for sample in range(args.samples):
                order = ("faithful", "fast") if sample % 2 == 0 else ("fast", "faithful")
                for profile in order:
                    if profile == "faithful":
                        timings["faithful_s"].append(run_faithful())
                    else:
                        timings["fast_batch_s"].append(run_fast())
            faithful = summarize(timings["faithful_s"])
            fast_batch = summarize(timings["fast_batch_s"])
            results.append(
                {
                    "case": name,
                    "golden_sha256": expected_sha256,
                    "fast_output_sha256": fast_sha256,
                    "faithful_s": timings["faithful_s"],
                    "fast_batch_s": timings["fast_batch_s"],
                    "faithful": faithful,
                    "fast_batch": fast_batch,
                    "faithful_to_fast_batch_median_ratio": faithful["median_s"] / fast_batch["median_s"],
                }
            )
        finally:
            try:
                fast_runspec.unlink()
            except FileNotFoundError:
                pass

    output = {
        "benchmark": "cligen-rs faithful versus fast_batch_v0 process-level CLI runtime",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "measurement": {
            "samples": args.samples,
            "warmups": args.warmups,
            "order": "alternating faithful-first and fast-first per sample",
            "scope": "process startup, YAML intake, input reads, generation, and complete .cli write",
            "fast_profile_contract": "structural output plus repeat-hash identity; no legacy-output parity claim",
        },
        "host": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": sys.version,
            "cpu_model": read_cpu_model(),
            "cpu_count": os.cpu_count(),
            "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        },
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "rust_binary": binary_metadata(args.rust_bin),
        "cases": results,
    }
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=[
                "case",
                "faithful_median_s",
                "fast_batch_median_s",
                "faithful_to_fast_batch_median_ratio",
                "faithful_stdev_s",
                "fast_batch_stdev_s",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "case": result["case"],
                    "faithful_median_s": result["faithful"]["median_s"],
                    "fast_batch_median_s": result["fast_batch"]["median_s"],
                    "faithful_to_fast_batch_median_ratio": result[
                        "faithful_to_fast_batch_median_ratio"
                    ],
                    "faithful_stdev_s": result["faithful"]["stdev_s"],
                    "fast_batch_stdev_s": result["fast_batch"]["stdev_s"],
                }
            )
    print(f"wrote {args.results}")
    print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"benchmark failed: {error}", file=sys.stderr)
        raise SystemExit(1)
