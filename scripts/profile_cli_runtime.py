#!/usr/bin/env python3
"""Collect perf counters and sampled reports for the Jeogla seed-pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_MANIFEST = ROOT / "docs/work-packages/20260710-cli-runtime-benchmark/artifacts/benchmark-cases.json"
ARTIFACTS = ROOT / "docs/work-packages/20260710-cli-runtime-profile/artifacts"
LEGACY_SOURCE = ROOT / "reference/cligen532/cligen.f"
LEGACY_INCLUDE = ROOT / "reference/cligen532"
CASE_NAMES = ("jeogla-au-seed0", "jeogla-au-seed17")
EVENTS = (
    "task-clock",
    "cycles",
    "instructions",
    "branches",
    "branch-misses",
    "cache-misses",
    "context-switches",
    "cpu-migrations",
    "page-faults",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compiler_version(compiler: str) -> str:
    completed = subprocess.run([compiler, "--version"], check=True, capture_output=True, text=True)
    return completed.stdout.splitlines()[0]


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


def prepare_legacy(work_root: Path, case: dict[str, Any]) -> tuple[Path, Path]:
    workdir = work_root / case["name"]
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    legacy = case["legacy"]
    for input_file in legacy["inputs"]:
        (workdir / input_file["name"]).symlink_to(ROOT / input_file["source"])
    return workdir, workdir / legacy["output"]


def remove_output(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def verify_output(path: Path, expected_sha256: str, label: str) -> str:
    if not path.exists():
        raise RuntimeError(f"{label}: output missing at {path}")
    actual = sha256(path)
    if actual != expected_sha256:
        raise RuntimeError(f"{label}: output hash {actual} != golden {expected_sha256}")
    return actual


def rust_command(binary: Path, case: dict[str, Any], output_dir: Path) -> tuple[list[str], Path, Path]:
    output = output_dir / f"{case['name']}.cli"
    remove_output(output)
    return [str(binary), "run", str(ROOT / case["runspec"])], ROOT, output


def legacy_command(binary: Path, case: dict[str, Any], work_root: Path) -> tuple[list[str], Path, Path, bytes]:
    workdir, output = prepare_legacy(work_root, case)
    legacy = case["legacy"]
    return [str(binary), *legacy["argv"]], workdir, output, legacy["stdin"].encode()


def parse_stat(path: Path) -> dict[str, str]:
    counters: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) >= 3 and fields[2] in EVENTS:
            counters[fields[2]] = fields[0]
    if set(counters) != set(EVENTS):
        missing = sorted(set(EVENTS) - set(counters))
        raise RuntimeError(f"perf stat {path}: missing counters {missing}")
    return counters


def profile_stat(
    implementation: str,
    binary: Path,
    case: dict[str, Any],
    output_dir: Path,
    work_root: Path,
    expected_sha256: str,
    repetitions: int,
) -> list[dict[str, str]]:
    samples = []
    for repetition in range(repetitions):
        if implementation == "rust":
            command, cwd, output = rust_command(binary, case, output_dir)
            stdin = None
        else:
            command, cwd, output, stdin = legacy_command(binary, case, work_root)
        stat_file = work_root / f"{implementation}-{case['name']}-{repetition}.perf-stat.tsv"
        completed = subprocess.run(
            ["perf", "stat", "-x", "\t", "-e", ",".join(EVENTS), "-o", str(stat_file), "--", *command],
            cwd=cwd,
            input=stdin,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"perf stat {implementation} {case['name']}: {completed.stderr.decode()}")
        samples.append({"output_sha256": verify_output(output, expected_sha256, f"stat {implementation} {case['name']}"), **parse_stat(stat_file)})
    return samples


def profile_record(
    implementation: str,
    binary: Path,
    case: dict[str, Any],
    output_dir: Path,
    work_root: Path,
    expected_sha256: str,
) -> None:
    if implementation == "rust":
        command, cwd, output = rust_command(binary, case, output_dir)
        stdin = None
    else:
        command, cwd, output, stdin = legacy_command(binary, case, work_root)
    data = work_root / f"{implementation}-{case['name']}.data"
    completed = subprocess.run(
        ["perf", "record", "-o", str(data), "-F", "999", "-g", "--call-graph", "dwarf", "--", *command],
        cwd=cwd,
        input=stdin,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"perf record {implementation} {case['name']}: {completed.stderr.decode()}")
    verify_output(output, expected_sha256, f"record {implementation} {case['name']}")
    report = subprocess.run(
        ["perf", "report", "--stdio", "--no-children", "--sort", "symbol,dso", "--percent-limit", "0.5", "-i", str(data)],
        check=True,
        capture_output=True,
        text=True,
    )
    clean_report = "\n".join(line.rstrip() for line in report.stdout.splitlines()) + "\n"
    (ARTIFACTS / f"{implementation}-{'seed17' if case['name'].endswith('seed17') else 'seed0'}.perf.txt").write_text(
        clean_report, encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rust-bin", type=Path, default=ROOT / "target/release/cligen")
    parser.add_argument("--legacy-bin", type=Path, default=ROOT / "target/cli-runtime-profile/cligen532")
    parser.add_argument("--compiler", default="gfortran")
    parser.add_argument("--build-legacy", action="store_true")
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--work-root", type=Path, default=ROOT / "target/cli-runtime-profile")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    return args


def main() -> int:
    args = parse_args()
    manifest = json.loads(BENCHMARK_MANIFEST.read_text(encoding="utf-8"))
    by_name = {case["name"]: case for case in manifest["cases"]}
    cases = [by_name[name] for name in CASE_NAMES]
    if args.build_legacy:
        build_command = build_legacy(args.legacy_bin, args.compiler)
    else:
        build_command = None
    if not args.rust_bin.is_file() or not args.legacy_bin.is_file():
        raise RuntimeError("missing release Rust or legacy binary")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    args.work_root.mkdir(parents=True, exist_ok=True)
    output_dir = ROOT / manifest["runspec_output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "repetitions": args.repetitions,
        "events": EVENTS,
        "manifest_sha256": sha256(BENCHMARK_MANIFEST),
        "reference_source_sha256": sha256(LEGACY_SOURCE),
        "rust_binary_sha256": sha256(args.rust_bin),
        "legacy_binary_sha256": sha256(args.legacy_bin),
        "compiler": compiler_version(args.compiler),
        "legacy_build_command": build_command,
        "runs": {},
    }
    for case in cases:
        expected_sha256 = sha256(ROOT / case["golden"])
        for implementation, binary in (("rust", args.rust_bin), ("legacy", args.legacy_bin)):
            samples = profile_stat(
                implementation,
                binary,
                case,
                output_dir,
                args.work_root,
                expected_sha256,
                args.repetitions,
            )
            profile_record(implementation, binary, case, output_dir, args.work_root, expected_sha256)
            results["runs"][f"{implementation}-{case['name']}"] = {
                "golden_sha256": expected_sha256,
                "stat_samples": samples,
            }
    (ARTIFACTS / "perf-stat.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(args.work_root)
    print(f"wrote {ARTIFACTS / 'perf-stat.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"profile failed: {error}", file=sys.stderr)
        raise SystemExit(1)
