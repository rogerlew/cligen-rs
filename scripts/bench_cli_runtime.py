#!/usr/bin/env python3
"""Benchmark the public Rust runspec CLI against equivalent legacy CLIGEN.

The benchmark is intentionally process-level: each measurement includes YAML
intake/validation or legacy argv/stdin intake, input reads, generation, and
writing the complete `.cli` file. It accepts a manifest of pre-adjudicated
equivalent workloads and refuses to report a timing if an output hash differs
from the named golden.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs/work-packages/20260710-cli-runtime-benchmark/artifacts/benchmark-cases.json"
DEFAULT_RESULTS = ROOT / "docs/work-packages/20260710-cli-runtime-benchmark/artifacts/results.json"
DEFAULT_CSV = ROOT / "docs/work-packages/20260710-cli-runtime-benchmark/artifacts/results.csv"
LEGACY_SOURCE = ROOT / "reference/cligen532/cligen.f"
LEGACY_INCLUDE = ROOT / "reference/cligen532"


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


def build_legacy(binary: Path, compiler: str) -> list[str]:
    binary.parent.mkdir(parents=True, exist_ok=True)
    command = [
        compiler,
        "-O3",
        "-ffp-contract=off",
        "-fprotect-parens",
        "-fno-fast-math",
        "-I",
        str(LEGACY_INCLUDE),
        str(LEGACY_SOURCE),
        "-o",
        str(binary),
    ]
    subprocess.run(command, check=True)
    return command


def remove_output(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def prepare_legacy_workdir(root: Path, case: dict[str, Any]) -> tuple[Path, Path]:
    workdir = root / case["name"]
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    legacy = case["legacy"]
    for input_file in legacy["inputs"]:
        source = ROOT / input_file["source"]
        destination = workdir / input_file["name"]
        destination.symlink_to(source)
    return workdir, workdir / legacy["output"]


def check_output(path: Path, expected_sha256: str, label: str) -> None:
    if not path.exists():
        raise RuntimeError(f"{label}: did not create {path}")
    actual_sha256 = sha256(path)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"{label}: SHA-256 {actual_sha256} != expected {expected_sha256}; timing rejected"
        )


def run_rust(binary: Path, case: dict[str, Any], output_dir: Path, expected_sha256: str) -> float:
    output = output_dir / f"{case['name']}.cli"
    remove_output(output)
    command = [str(binary), "run", str(ROOT / case["runspec"])]
    start = time.perf_counter_ns()
    completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    elapsed = (time.perf_counter_ns() - start) / 1_000_000_000
    if completed.returncode != 0:
        raise RuntimeError(f"rust {case['name']}: {completed.stderr.decode(errors='replace')}")
    check_output(output, expected_sha256, f"rust {case['name']}")
    return elapsed


def run_legacy(binary: Path, work_root: Path, case: dict[str, Any], expected_sha256: str) -> float:
    workdir, output = prepare_legacy_workdir(work_root, case)
    legacy = case["legacy"]
    command = [str(binary), *legacy["argv"]]
    start = time.perf_counter_ns()
    completed = subprocess.run(
        command,
        cwd=workdir,
        input=legacy["stdin"].encode(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    elapsed = (time.perf_counter_ns() - start) / 1_000_000_000
    if completed.returncode != 0:
        raise RuntimeError(f"legacy {case['name']}: {completed.stderr.decode(errors='replace')}")
    check_output(output, expected_sha256, f"legacy {case['name']}")
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
    parser.add_argument("--legacy-bin", type=Path, default=ROOT / "target/cli-runtime-benchmark/cligen532")
    parser.add_argument("--compiler", default="gfortran")
    parser.add_argument("--build-legacy", action="store_true")
    parser.add_argument("--samples", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--work-root", type=Path, default=ROOT / "target/cli-runtime-benchmark/work")
    parser.add_argument("--case", action="append", dest="case_names")
    parser.add_argument("--keep-workdirs", action="store_true")
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
    if args.build_legacy:
        legacy_build_command = build_legacy(args.legacy_bin, args.compiler)
    else:
        legacy_build_command = None
    if not args.rust_bin.is_file():
        raise RuntimeError(f"Rust binary missing: {args.rust_bin}; run cargo build --release --bin cligen")
    if not args.legacy_bin.is_file():
        raise RuntimeError(f"legacy binary missing: {args.legacy_bin}; pass --build-legacy")

    output_dir = ROOT / manifest["runspec_output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    args.work_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for case in cases:
        expected_sha256 = sha256(ROOT / case["golden"])
        for _ in range(args.warmups):
            run_rust(args.rust_bin, case, output_dir, expected_sha256)
            run_legacy(args.legacy_bin, args.work_root, case, expected_sha256)
        timings = {"rust_s": [], "legacy_s": []}
        for sample in range(args.samples):
            order = ("rust", "legacy") if sample % 2 == 0 else ("legacy", "rust")
            for implementation in order:
                if implementation == "rust":
                    timings["rust_s"].append(run_rust(args.rust_bin, case, output_dir, expected_sha256))
                else:
                    timings["legacy_s"].append(
                        run_legacy(args.legacy_bin, args.work_root, case, expected_sha256)
                    )
        rust = summarize(timings["rust_s"])
        legacy = summarize(timings["legacy_s"])
        results.append(
            {
                "case": case["name"],
                "golden_sha256": expected_sha256,
                "rust_s": timings["rust_s"],
                "legacy_s": timings["legacy_s"],
                "rust": rust,
                "legacy": legacy,
                "legacy_to_rust_median_ratio": legacy["median_s"] / rust["median_s"],
            }
        )

    output = {
        "benchmark": "cligen-rs process-level CLI runtime",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "measurement": {
            "samples": args.samples,
            "warmups": args.warmups,
            "order": "alternating Rust-first and legacy-first per sample",
            "scope": "process startup, declared-input reads, generation, and complete .cli write",
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
        "reference_source": {"path": str(LEGACY_SOURCE), "sha256": sha256(LEGACY_SOURCE)},
        "legacy_build_command": legacy_build_command,
        "compiler": command_version([args.compiler, "--version"]),
        "rust_binary": binary_metadata(args.rust_bin),
        "legacy_binary": binary_metadata(args.legacy_bin),
        "cases": results,
    }
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=[
                "case",
                "rust_median_s",
                "legacy_median_s",
                "legacy_to_rust_median_ratio",
                "rust_mean_s",
                "legacy_mean_s",
                "rust_stdev_s",
                "legacy_stdev_s",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "case": result["case"],
                    "rust_median_s": result["rust"]["median_s"],
                    "legacy_median_s": result["legacy"]["median_s"],
                    "legacy_to_rust_median_ratio": result["legacy_to_rust_median_ratio"],
                    "rust_mean_s": result["rust"]["mean_s"],
                    "legacy_mean_s": result["legacy"]["mean_s"],
                    "rust_stdev_s": result["rust"]["stdev_s"],
                    "legacy_stdev_s": result["legacy"]["stdev_s"],
                }
            )
    if not args.keep_workdirs:
        shutil.rmtree(args.work_root)
    print(f"wrote {args.results}")
    print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"benchmark failed: {error}", file=sys.stderr)
        raise SystemExit(1)
