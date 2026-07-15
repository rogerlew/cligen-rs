#!/usr/bin/env python3
"""Build and execute the frozen A5e0 research matrix and conformance runs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time
from typing import Any


STATIONS = ("ca042319", "co051660", "ms227840")
ARMS = ("research_baseline", "candidate")
REPLICATES = tuple(range(1, 9))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def strict_json(path: Path) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate key {key} in {path}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"nonfinite token {token} in {path}")
        ),
    )


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def execute(command: list[str], stdout: Path | None = None) -> None:
    if stdout is None:
        completed = subprocess.run(command, cwd=repo_root(), capture_output=True, text=True)
    else:
        stdout.parent.mkdir(parents=True, exist_ok=True)
        with stdout.open("wb") as stream:
            completed = subprocess.run(command, cwd=repo_root(), stdout=stream, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        stderr = completed.stderr.decode() if isinstance(completed.stderr, bytes) else completed.stderr
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{stderr}")


def daily_rows(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 17 or not lines[13].startswith(" da mo year"):
        raise RuntimeError(f"unexpected CLI header: {path}")
    rows = lines[15:]
    while rows and not rows[-1].strip():
        rows.pop()
    if not rows:
        raise RuntimeError(f"CLI has no daily rows: {path}")
    return rows


def run_one(
    runner: Path,
    cligen: Path,
    coefficients: Path,
    par: Path,
    station: str,
    arm: str,
    replicate: int,
    output: Path,
    root: Path,
) -> dict[str, Any]:
    directory = output / "runs" / station / arm / f"rep{replicate:02d}"
    products: dict[int, dict[str, Path]] = {}
    for years in (100, 30):
        cli = directory / f"{years}yr.cli"
        diagnostics = directory / f"{years}yr.diagnostics.json"
        quality = directory / f"{years}yr.quality.json"
        execute(
            [
                str(runner),
                "--par",
                str(par),
                "--coefficients",
                str(coefficients),
                "--station",
                station,
                "--arm",
                arm,
                "--replicate",
                str(replicate),
                "--years",
                str(years),
                "--cli",
                str(cli),
                "--diagnostics",
                str(diagnostics),
            ]
        )
        execute([str(cligen), "quality", str(cli), "--par", str(par)], quality)
        products[years] = {"cli": cli, "diagnostics": diagnostics, "quality": quality}

    rows_100 = daily_rows(products[100]["cli"])
    rows_30 = daily_rows(products[30]["cli"])
    if rows_100[: len(rows_30)] != rows_30:
        raise RuntimeError(f"30-year typed-row prefix mismatch: {station}/{arm}/{replicate}")
    diag_100 = strict_json(products[100]["diagnostics"])
    diag_30 = strict_json(products[30]["diagnostics"])
    if diag_100["initial_seed_states"] != diag_30["initial_seed_states"]:
        raise RuntimeError(f"initial seed prefix mismatch: {station}/{arm}/{replicate}")
    if arm == "candidate":
        if diag_100["annual_states"][:30] != diag_30["annual_states"]:
            raise RuntimeError(f"annual state prefix mismatch: {station}/{replicate}")
        if len(diag_100["annual_states"]) != 100:
            raise RuntimeError(f"candidate did not consume one annual state/year: {station}/{replicate}")
    elif diag_100["annual_states"] or diag_30["annual_states"]:
        raise RuntimeError(f"baseline consumed extension state: {station}/{replicate}")
    if max(diag_100["actual_raw_updates"]) >= 500_000:
        raise RuntimeError(f"faithful stream exceeds segment: {station}/{arm}/{replicate}")
    return {
        "run_id": f"{station}-{arm}-rep{replicate:02d}",
        "station_id": station,
        "arm": arm,
        "replicate": replicate,
        "master_seed": diag_100["master_seed"],
        "faithful_segment": diag_100["faithful_segment"],
        "faithful_raw_skip": diag_100["faithful_raw_skip"],
        "annual_state_sha256": diag_100["annual_state_sha256"],
        "prefix_rows": len(rows_30),
        "full_rows": len(rows_100),
        "maximum_raw_updates": max(diag_100["actual_raw_updates"]),
        "products": {
            str(years): {
                name: artifact(path, root) for name, path in products[years].items()
            }
            for years in (30, 100)
        },
    }


def f32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def write_zero_bundle(coefficients: Path, output: Path, root: Path) -> Path:
    value = strict_json(coefficients)
    base_directory = root / "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/fit/evidence-v1/station-bundles"
    for station in value["stations"]:
        base = strict_json(base_directory / f"{station['station_id']}.a5b.station.json")["base_station"]["parameters"]
        for variable in ("occurrence", "amount", "tmax", "tmin"):
            station["loadings"][variable] = [0.0] * 12
        station["derived"]["amount_residual_sd_in"] = [
            f32(item) for item in base["precipitation"]["standard_deviation_daily"]
        ]
        station["derived"]["tmax_residual_sd_f"] = [
            f32(item) for item in base["temperature"]["maximum_standard_deviation"]
        ]
        station["derived"]["tmin_residual_sd_f"] = [
            f32(item) for item in base["temperature"]["minimum_standard_deviation"]
        ]
    path = output / "conformance" / "all-zero-coefficients.json"
    write_json(path, value)
    return path


def conformance(
    runner: Path,
    coefficients: Path,
    pars: dict[str, Path],
    output: Path,
    root: Path,
) -> dict[str, Any]:
    zero = write_zero_bundle(coefficients, output, root)
    directory = output / "conformance"
    products = {}
    for arm, bundle in (("research_baseline", coefficients), ("candidate", zero)):
        cli = directory / f"zero-{arm}.cli"
        diagnostics = directory / f"zero-{arm}.diagnostics.json"
        execute(
            [
                str(runner), "--par", str(pars["ca042319"]), "--coefficients", str(bundle),
                "--station", "ca042319", "--arm", arm, "--replicate", "1", "--years", "30",
                "--cli", str(cli), "--diagnostics", str(diagnostics),
            ]
        )
        products[arm] = (cli, diagnostics)
    base_rows = daily_rows(products["research_baseline"][0])
    candidate_rows = daily_rows(products["candidate"][0])
    base_diag = strict_json(products["research_baseline"][1])
    candidate_diag = strict_json(products["candidate"][1])
    if base_rows != candidate_rows:
        raise RuntimeError("all-zero candidate does not reproduce baseline typed rows")
    if base_diag["final_seed_states"] != candidate_diag["final_seed_states"]:
        raise RuntimeError("all-zero candidate does not reproduce baseline final seeds")
    if candidate_diag["annual_states"]:
        raise RuntimeError("all-zero candidate consumed annual RNG state")
    return {
        "status": "PASS",
        "typed_rows_equal": True,
        "final_seed_states_equal": True,
        "annual_rng_draws": 0,
        "zero_bundle": artifact(zero, root),
    }


def main() -> int:
    root = repo_root()
    package = root / "docs/work-packages/20260714-a5e0-direct-annual-state-pilot"
    coefficients = package / "artifacts/a5e0-coefficients-v1.json"
    output = root / "target/a5e0"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    pars = {
        station: root / f"target/a5b-candidate-v1/.a5b-input-snapshot/stations/{station}.par"
        for station in STATIONS
    }
    for station, path in pars.items():
        if not path.is_file():
            raise RuntimeError(f"missing station input for {station}: {path}")
    started = time.time()
    execute(["cargo", "build", "--locked", "--release", "--example", "a5e0_runner", "--bin", "cligen"])
    runner = root / "target/release/examples/a5e0_runner"
    cligen = root / "target/release/cligen"
    records = []
    workers = min(8, os.cpu_count() or 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                run_one, runner, cligen, coefficients, pars[station], station, arm,
                replicate, output, root
            ): (station, arm, replicate)
            for station in STATIONS
            for arm in ARMS
            for replicate in REPLICATES
        }
        for future in as_completed(futures):
            records.append(future.result())
    records.sort(key=lambda row: (STATIONS.index(row["station_id"]), ARMS.index(row["arm"]), row["replicate"]))
    for station in STATIONS:
        for replicate in REPLICATES:
            paired = [row for row in records if row["station_id"] == station and row["replicate"] == replicate]
            if paired[0]["faithful_segment"] != paired[1]["faithful_segment"]:
                raise RuntimeError(f"paired arm segment mismatch: {station}/{replicate}")
            left = strict_json(root / paired[0]["products"]["100"]["diagnostics"]["path"])
            right = strict_json(root / paired[1]["products"]["100"]["diagnostics"]["path"])
            if left["initial_seed_states"] != right["initial_seed_states"]:
                raise RuntimeError(f"paired arm initial seeds mismatch: {station}/{replicate}")
    segments = [
        row["faithful_segment"] for row in records if row["arm"] == "research_baseline"
    ]
    if sorted(segments) != list(range(24)):
        raise RuntimeError("faithful segment assignment is not exactly 0..23")
    result = {
        "matrix_index_schema": "a5e0_matrix_index_v1",
        "status": "complete",
        "workers": workers,
        "wall_time_seconds": time.time() - started,
        "coefficients": artifact(coefficients, root),
        "runner": artifact(runner, root),
        "cligen": artifact(cligen, root),
        "station_inputs": [artifact(pars[station], root) for station in STATIONS],
        "conformance": conformance(runner, coefficients, pars, output, root),
        "runs": records,
    }
    write_json(output / "matrix-index-v1.json", result)
    print(json.dumps({"status": "complete", "runs": len(records), "wall_time_seconds": result["wall_time_seconds"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
