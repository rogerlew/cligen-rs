#!/usr/bin/env python3
"""Execute the source-bound A11E8 deterministic cohort experiment."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import importlib.util
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
MANIFEST = PACKAGE / "execution-manifest-v1.json"
SCHEMA = PACKAGE / "execution-manifest-v1.schema.json"
CONTRACT = PACKAGE / "contract.py"
SPEC = ROOT / "docs/specifications/SPEC-A11-DETERMINISTIC-COHORT-JOINT-FOUNDATION.md"
PACKAGE_DOC = PACKAGE.parent / "package.md"
PLAN = ROOT / "docs/exec-plans/20260904-a11e8-deterministic-cohort-joint-foundation.md"
PANEL = ROOT / "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json"
A11E2_DIR = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts"
A11E2 = A11E2_DIR / "execute.py"
A11E2_MANIFEST = A11E2_DIR / "execution-manifest-v1.json"
A11E5 = ROOT / "docs/work-packages/20260827-a11e5-interannual-family-stability/artifacts/execute.py"
A11E7_DIR = ROOT / "docs/work-packages/20260828-a11e7-faithful-temperature-qc-attribution/artifacts"
A11E7_EVIDENCE = A11E7_DIR / "development-evidence-v1.json"
A11E7_DECISION = A11E7_DIR / "development-decision-v1.json"
A11E7_PROVENANCE = A11E7_DIR / "cryptographic-provenance-receipt-v1.json"
A5F0_DIR = ROOT / "docs/work-packages/20260714-a5f0-annual-state-failure-attribution/artifacts"
A5F0_DECISION = A5F0_DIR / "a5f0-decision-v1.json"
A5F0_FINDINGS = A5F0_DIR / "a5f0-findings.md"
RUNTIME_ROOT = ROOT / "target/a11e8-deterministic-cohort-runtime"
TEMPERATURE_METRICS = (
    "monthly_temperature_dispersion_error",
    "annual_temperature_dispersion_error",
    "temperature_cross_month_correlation_rmse",
    "annual_temperature_lag1_error",
    "annual_temperature_low_frequency_error",
    "monthly_temperature_mean_absolute_error_c",
)
NONINFERIOR_TEMPERATURE_METRICS = (
    "monthly_temperature_dispersion_error",
    "temperature_cross_month_correlation_rmse",
    "annual_temperature_lag1_error",
    "annual_temperature_low_frequency_error",
    "monthly_temperature_mean_absolute_error_c",
)
SCORECARD_METRICS = (
    "monthly_precipitation_dispersion_error",
    "monthly_temperature_dispersion_error",
    "annual_precipitation_dispersion_error",
    "annual_temperature_dispersion_error",
    "precipitation_cross_month_correlation_rmse",
    "temperature_cross_month_correlation_rmse",
    "annual_precipitation_lag1_error",
    "annual_temperature_lag1_error",
    "annual_precipitation_low_frequency_error",
    "annual_temperature_low_frequency_error",
    "monthly_temperature_mean_absolute_error_c",
)


class ExecutionError(RuntimeError):
    """The prospective A11E8 execution contract was violated."""


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ExecutionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


contract = load_module("a11e8_contract", CONTRACT)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    partial.replace(path)


def git(*arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True
    )
    if result.returncode:
        raise ExecutionError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def validate_manifest(value: Any) -> dict[str, Any]:
    try:
        return contract.validate_manifest(value)
    except contract.ContractError as error:
        raise ExecutionError(str(error)) from error


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    published = git("rev-parse", "origin/main").decode().strip()
    head = git("rev-parse", "HEAD").decode().strip()
    if len(source_commit) != 40 or source_commit != published or source_commit != head:
        raise ExecutionError("execution source is not exact published origin/main")
    build_inputs = ("crates", "Cargo.toml", "Cargo.lock", "rust-toolchain.toml")
    if git("diff", "--name-only", source_commit, "--", *build_inputs).strip():
        raise ExecutionError("working build inputs differ from the published source")
    required = (
        Path(__file__),
        PACKAGE / "test_execute.py",
        CONTRACT,
        PACKAGE / "test_contract.py",
        PACKAGE / "scaffold-validation.md",
        MANIFEST,
        SCHEMA,
        SPEC,
        PACKAGE_DOC,
        PLAN,
    )
    source_hashes = {}
    for path in required:
        relative = path.relative_to(ROOT).as_posix()
        blob = git("show", f"{source_commit}:{relative}")
        if blob != path.read_bytes():
            raise ExecutionError(f"working source differs: {relative}")
        source_hashes[relative] = digest_bytes(blob)
    dependencies = manifest["dependencies"]
    checks = (
        (PANEL, "panel_sha256"),
        (A11E7_EVIDENCE, "a11e7_evidence_sha256"),
        (A11E7_DECISION, "a11e7_decision_sha256"),
        (A11E7_PROVENANCE, "a11e7_provenance_sha256"),
        (A5F0_DECISION, "a5f0_decision_sha256"),
        (A5F0_FINDINGS, "a5f0_findings_sha256"),
        (A11E2, "a11e2_executor_sha256"),
        (A11E5, "a11e5_executor_sha256"),
        (ROOT / "Cargo.lock", "cargo_lock_sha256"),
        (ROOT / "Cargo.toml", "cargo_toml_sha256"),
        (ROOT / "rust-toolchain.toml", "rust_toolchain_sha256"),
    )
    for path, name in checks:
        if digest(path) != dependencies[name]:
            raise ExecutionError(f"dependency drifted: {path}")
    return {
        "source_commit": source_commit,
        "source_tree": git("rev-parse", f"{source_commit}^{{tree}}").decode().strip(),
        "published_ref": "origin/main",
        "source_hashes": source_hashes,
    }


def parse_cli(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    precipitation = np.zeros((16, 12), dtype=np.float64)
    temperature = np.zeros((16, 12), dtype=np.float64)
    daily_range = np.zeros((16, 12), dtype=np.float64)
    wet_fraction = np.zeros((16, 12), dtype=np.float64)
    counts = np.zeros((16, 12), dtype=np.int64)
    rows = 0
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) != 13:
            continue
        try:
            day, month, year = map(int, fields[:3])
            values = list(map(float, fields[3:]))
        except ValueError:
            continue
        if not (
            1 <= year <= 16
            and 1 <= month <= 12
            and 1 <= day <= calendar.monthrange(year, month)[1]
        ):
            raise ExecutionError("invalid generated date")
        y, m = year - 1, month - 1
        precipitation[y, m] += values[0]
        temperature[y, m] += (values[4] + values[5]) / 2.0
        daily_range[y, m] += values[4] - values[5]
        wet_fraction[y, m] += float(values[0] > 0.0)
        counts[y, m] += 1
        rows += 1
    if rows != 5844:
        raise ExecutionError(f"expected 5844 daily rows, found {rows}")
    for year in range(1, 17):
        for month in range(1, 13):
            if counts[year - 1, month - 1] != calendar.monthrange(year, month)[1]:
                raise ExecutionError("generated calendar is incomplete")
    precipitation *= 30.4375 / counts
    temperature /= counts
    daily_range /= counts
    wet_fraction /= counts
    return precipitation, temperature, daily_range, wet_fraction


def covariance_chronological(values: np.ndarray) -> np.ndarray:
    if values.shape != (16, 12) or not np.isfinite(values).all():
        raise ExecutionError("covariance input must be a finite 16x12 matrix")
    mean = np.zeros(12, dtype=np.float64)
    for row in values:
        mean += row
    mean /= 16.0
    covariance = np.zeros((12, 12), dtype=np.float64)
    for row in values:
        difference = row - mean
        covariance += np.outer(difference, difference)
    covariance /= 15.0
    return covariance


def fit_thermal_loading(
    observed: np.ndarray, faithful: list[np.ndarray]
) -> dict[str, Any]:
    if len(faithful) != 32:
        raise ExecutionError("thermal fit requires 32 faithful streams")
    observed_covariance = covariance_chronological(observed)
    faithful_covariance = np.zeros((12, 12), dtype=np.float64)
    for generated in faithful:
        faithful_covariance += covariance_chronological(generated)
    faithful_covariance /= 32.0
    residual = observed_covariance - faithful_covariance
    residual = (residual + residual.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(residual)
    maximum = float(eigenvalues[-1])
    tolerance = 1e-12 * max(1.0, abs(maximum))
    tied = [index for index, value in enumerate(eigenvalues) if maximum - float(value) <= tolerance]
    vector = np.zeros(12, dtype=np.float64)
    if maximum > 0.0:
        if len(tied) != 1:
            raise ExecutionError("positive leading eigenpair is ambiguous")
        vector = np.asarray(eigenvectors[:, tied[0]], dtype=np.float64)
        if float(np.sum(vector)) < 0.0:
            vector *= -1.0
        elif float(np.sum(vector)) == 0.0:
            nonzero = np.flatnonzero(vector)
            if nonzero.size and vector[int(nonzero[0])] < 0.0:
                vector *= -1.0
    loading = np.zeros(12, dtype=np.float64)
    if maximum > 0.0:
        loading = math.sqrt(maximum) * vector
    if not np.isfinite(loading).all():
        raise ExecutionError("thermal loading is nonfinite")
    return {
        "observed_covariance": observed_covariance.tolist(),
        "mean_faithful_covariance": faithful_covariance.tolist(),
        "residual_covariance": residual.tolist(),
        "selected_eigenvalue": maximum,
        "eigenvalue_tolerance": tolerance,
        "selected_eigenvector": vector.tolist(),
        "loading_c": loading.tolist(),
    }


def integer_tenths(value: str) -> int:
    parsed = Decimal(value) * 10
    integral = parsed.to_integral_value()
    if parsed != integral:
        raise ExecutionError("source temperature is not exact integer tenths")
    return int(integral)


def render_tenths(value: int) -> str:
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    rendered = f"{sign}{absolute // 10}.{absolute % 10}"
    if len(rendered) > 5:
        raise ExecutionError("candidate temperature overflows F5.1")
    return rendered.rjust(5)


def rounded_delta_tenths(value: float) -> int:
    if not math.isfinite(value):
        raise ExecutionError("candidate temperature delta is nonfinite")
    return int(
        (Decimal.from_float(value) * 10).to_integral_value(rounding=ROUND_HALF_EVEN)
    )


def overlay_cli(
    faithful_path: Path, candidate_path: Path, loading: np.ndarray, states: list[float]
) -> dict[str, Any]:
    if loading.shape != (12,) or len(states) != 16:
        raise ExecutionError("candidate overlay shape differs")
    deltas = np.zeros((16, 12), dtype=np.int64)
    for year in range(16):
        for month in range(12):
            deltas[year, month] = rounded_delta_tenths(float(loading[month]) * states[year])
    output: list[str] = []
    rows = 0
    started = False
    for line in faithful_path.read_text().splitlines(keepends=True):
        body = line[:-1] if line.endswith("\n") else line
        ending = "\n" if line.endswith("\n") else ""
        if body.startswith(" da mo year  prcp"):
            started = True
            output.append(line)
            continue
        if not started or len(body) != 70:
            output.append(line)
            continue
        try:
            day = int(body[0:3])
            month = int(body[3:6])
            year = int(body[7:12])
            tmax = integer_tenths(body[37:42])
            tmin = integer_tenths(body[43:48])
            dewpoint = integer_tenths(body[65:70])
        except (ValueError, ExecutionError):
            output.append(line)
            continue
        if not (
            1 <= year <= 16
            and 1 <= month <= 12
            and 1 <= day <= calendar.monthrange(year, month)[1]
        ):
            raise ExecutionError("overlay encountered an invalid daily date")
        delta = int(deltas[year - 1, month - 1])
        replaced = (
            body[:37]
            + render_tenths(tmax + delta)
            + body[42:43]
            + render_tenths(tmin + delta)
            + body[48:65]
            + render_tenths(dewpoint + delta)
        )
        if len(replaced) != 70 or replaced[:37] != body[:37] or replaced[48:65] != body[48:65]:
            raise ExecutionError("overlay changed a non-temperature field")
        if integer_tenths(replaced[37:42]) - integer_tenths(replaced[43:48]) != tmax - tmin:
            raise ExecutionError("overlay changed Tmax-minus-Tmin")
        if integer_tenths(replaced[43:48]) - integer_tenths(replaced[65:70]) != tmin - dewpoint:
            raise ExecutionError("overlay changed Tmin-minus-dewpoint")
        output.append(replaced + ending)
        rows += 1
    if rows != 5844:
        raise ExecutionError(f"overlay expected 5844 daily rows, found {rows}")
    candidate_path.write_text("".join(output))
    return {
        "annual_states": states,
        "annual_states_sha256": canonical_digest(states),
        "delta_tenths_c": deltas.tolist(),
        "delta_tenths_sha256": canonical_digest(deltas.tolist()),
        "daily_rows": rows,
        "temperature_difference_invariant_failures": 0,
        "non_temperature_identity_failures": 0,
    }


def score_stream(
    precipitation: np.ndarray,
    temperature: np.ndarray,
    observed: dict[str, Any],
    weights: np.ndarray,
    metrics_module: Any,
) -> dict[str, float]:
    metrics = metrics_module.interannual_metrics(
        precipitation,
        temperature,
        observed["precipitation"],
        observed["tmean"],
        weights,
    )
    metrics["monthly_temperature_mean_absolute_error_c"] = float(
        np.mean(np.abs(np.mean(temperature, axis=0) - np.mean(observed["tmean"], axis=0)))
    )
    if set(metrics) != set(SCORECARD_METRICS) or not all(
        math.isfinite(value) and value >= 0.0 for value in metrics.values()
    ):
        raise ExecutionError("scorecard is incomplete or nonfinite")
    return metrics


def selector_record(
    model_id: str, candidate_index: int, metrics: dict[str, float]
) -> dict[str, Any]:
    ordinal = contract.MODEL_ORDER.index(model_id)
    return {
        "model_id": model_id,
        "model_ordinal": ordinal,
        "candidate_index": candidate_index,
        "physical_failure_count": 0,
        "monthly_temperature_mean_error_q": contract.quantize_score(
            metrics["monthly_temperature_mean_absolute_error_c"]
        ),
        "annual_temperature_dispersion_error_q": contract.quantize_score(
            metrics["annual_temperature_dispersion_error"]
        ),
        "temperature_cross_month_correlation_rmse_q": contract.quantize_score(
            metrics["temperature_cross_month_correlation_rmse"]
        ),
        "annual_temperature_lag1_error_q": contract.quantize_score(
            metrics["annual_temperature_lag1_error"]
        ),
        "annual_temperature_low_frequency_error_q": contract.quantize_score(
            metrics["annual_temperature_low_frequency_error"]
        ),
    }


def median_ratio(
    rows: list[dict[str, Any]], metric: str, numerator: str, denominator: str
) -> float:
    top = float(np.median([row["models"][numerator]["metrics"][metric] for row in rows]))
    bottom = float(np.median([row["models"][denominator]["metrics"][metric] for row in rows]))
    return top / max(bottom, 1e-12)


def build_decision(
    rows: list[dict[str, Any]], selections: list[dict[str, Any]], manifest: dict[str, Any]
) -> dict[str, Any]:
    if len(rows) != 640 or len({(row["station_id"], row["cohort_id"], row["candidate_index"]) for row in rows}) != 640:
        raise ExecutionError("decision requires the complete 20x4x8 paired grid")
    if len(selections) != 80 or len({(row["station_id"], row["cohort_id"]) for row in selections}) != 80:
        raise ExecutionError("decision requires 80 station/cohort selections")
    model_gate = manifest["model_gate"]
    metric_ratios = {
        metric: median_ratio(rows, metric, contract.MODEL_ORDER[1], contract.MODEL_ORDER[0])
        for metric in TEMPERATURE_METRICS
    }
    annual_metric = "annual_temperature_dispersion_error"
    improved = sum(
        row["models"][contract.MODEL_ORDER[1]]["metrics"][annual_metric]
        < row["models"][contract.MODEL_ORDER[0]]["metrics"][annual_metric]
        for row in rows
    )
    station_ratios = {}
    for station in sorted({row["station_id"] for row in rows}):
        station_rows = [row for row in rows if row["station_id"] == station]
        station_ratios[station] = median_ratio(
            station_rows, annual_metric, contract.MODEL_ORDER[1], contract.MODEL_ORDER[0]
        )
    component_passes = (
        metric_ratios[annual_metric] <= model_gate["annual_dispersion_error_ratio_max"]
        and all(
            metric_ratios[metric] <= model_gate["noninferiority_ratio_max"]
            for metric in NONINFERIOR_TEMPERATURE_METRICS
        )
        and improved / 640 >= model_gate["minimum_improvement_fraction"]
        and max(station_ratios.values()) <= model_gate["station_annual_error_ratio_max"]
    )
    selector_gate = manifest["selector_gate"]
    selection_ratios = {}
    for metric in SCORECARD_METRICS:
        mixed = float(np.median([row["mixed"]["metrics"][metric] for row in selections]))
        faithful = float(np.median([row["faithful_only"]["metrics"][metric] for row in selections]))
        selection_ratios[metric] = mixed / max(faithful, 1e-12)
    thermal_count = sum(row["mixed"]["model_id"] == contract.MODEL_ORDER[1] for row in selections)
    selector_useful = (
        selection_ratios[annual_metric] <= selector_gate["selected_annual_error_ratio_max"]
        and all(
            ratio <= selector_gate["complete_scorecard_ratio_max"]
            for ratio in selection_ratios.values()
        )
        and thermal_count / 80 >= selector_gate["minimum_thermal_selection_fraction"]
    )
    if not component_passes:
        disposition = "THERMAL_COMPONENT_REJECTED"
    elif selector_useful:
        disposition = "THERMAL_COMPONENT_RETAINED_SELECTOR_USEFUL"
    else:
        disposition = "THERMAL_COMPONENT_RETAINED_SELECTOR_NOT_USEFUL"
    return {
        "disposition": disposition,
        "component": {
            "passes": component_passes,
            "metric_median_ratios_candidate_over_faithful": metric_ratios,
            "annual_dispersion_improved_pairs": improved,
            "annual_dispersion_improvement_fraction": improved / 640,
            "station_annual_error_ratios": station_ratios,
        },
        "selector": {
            "useful": selector_useful,
            "metric_median_ratios_mixed_over_faithful_only": selection_ratios,
            "thermal_selections": thermal_count,
            "thermal_selection_fraction": thermal_count / 80,
        },
    }


def write_runspec(path: Path, burn: int) -> None:
    path.write_text(
        "cligen_runspec: 1\n"
        "station:\n"
        "  par: source.par\n"
        "mode: continuous\n"
        "simulation:\n"
        "  begin_year: 1\n"
        "  years: 16\n"
        "  interpolation: none\n"
        "rng:\n"
        f"  burn: {burn}\n"
        "generation_profile: faithful_5_32_3\n"
        "qc_filter: faithful\n"
        "output:\n"
        "  cli: faithful.cli\n"
        "  quality: true\n"
        "  overwrite: false\n"
        f"  command_echo: '-r{burn} -isource.par'\n"
    )


def execute(source_commit: str) -> None:
    started = time.monotonic()
    manifest = validate_manifest(json.loads(MANIFEST.read_text()))
    runtime = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "system": platform.system(),
        "machine": platform.machine(),
        "linear_algebra_threads": 1,
        "rustc": subprocess.run(
            ["rustc", "--version"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "cargo": subprocess.run(
            ["cargo", "--version"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
    }
    if runtime != manifest["runtime"]:
        raise ExecutionError(f"scientific runtime differs: {runtime}")
    source = verify_source(source_commit, manifest)
    if RUNTIME_ROOT.exists():
        raise ExecutionError(f"runtime root exists: {RUNTIME_ROOT}")
    for variable in ("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS"):
        if os.environ.get(variable):
            raise ExecutionError(f"unfrozen compiler flags are set: {variable}")
    try:
        station_root = Path(
            os.environ.get("CLIGEN_DATA_DIR", str(Path.home() / ".cache/cligen"))
        ) / "stations/us-2015/2026.07"
        database = station_root / "2015_stations.db"
        if digest(database) != manifest["dependencies"]["station_database_sha256"]:
            raise ExecutionError("station database differs")
        panel = json.loads(PANEL.read_text())
        stations = panel.get("stations")
        if panel.get("selected_station_count") != 20 or not isinstance(stations, list) or len(stations) != 20:
            raise ExecutionError("station panel differs")
        station_files = {}
        for station in stations:
            station_id = station["station_id"]
            path = station_root / f"{station_id}.par"
            if digest(path) != station["parameter_sha256"]:
                raise ExecutionError(f"source parameter differs: {station_id}")
            station_files[station_id] = path
        predecessor = load_module("a11e2_for_a11e8", A11E2)
        predecessor_manifest = predecessor.validate_manifest(json.loads(A11E2_MANIFEST.read_text()))
        inherited_hashes, development_rows, _ = predecessor.verify_inputs(predecessor_manifest)
        inherited = predecessor.ensure_base_loaded()
        development, observed_preflight = inherited.load_development(development_rows)
        observed_by_id = {row["point_id"]: row for row in development}
        if set(observed_by_id) != set(station_files):
            raise ExecutionError("observed and station rosters differ")
        metrics_module = load_module("a11e5_for_a11e8", A11E5)
        weights = np.asarray(
            [calendar.monthrange(2001, month)[1] for month in range(1, 13)],
            dtype=np.float64,
        )
        weights /= np.sum(weights)
        RUNTIME_ROOT.mkdir(parents=True)
        build_target = RUNTIME_ROOT / "build"
        build = subprocess.run(
            [
                "cargo", "build", "--release", "--locked", "--bin", "cligen",
                "--target-dir", str(build_target),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if build.returncode:
            raise ExecutionError(f"release build failed: {build.stderr[-4000:]}")
        binary = build_target / "release/cligen"
        binary_sha = digest(binary)
        build_provenance = {
            "command": "cargo build --release --locked --bin cligen --target-dir <runtime>/build",
            "rustc_vv": subprocess.run(
                ["rustc", "-vV"], cwd=ROOT, check=True, capture_output=True, text=True
            ).stdout.strip(),
            "cargo_version": subprocess.run(
                ["cargo", "--version"], cwd=ROOT, check=True, capture_output=True, text=True
            ).stdout.strip(),
            "rustflags": None,
            "cargo_encoded_rustflags": None,
        }
        rows: list[dict[str, Any]] = []
        selection_rows: list[dict[str, Any]] = []
        loading_rows: list[dict[str, Any]] = []
        for station in stations:
            station_id = station["station_id"]
            observed = observed_by_id[station_id]
            generated: list[dict[str, Any]] = []
            for cohort in manifest["cohorts"]:
                for candidate_index, burn in enumerate(cohort["burns"]):
                    run_dir = RUNTIME_ROOT / "runs" / station_id / str(cohort["cohort_id"]) / str(candidate_index)
                    run_dir.mkdir(parents=True)
                    source_par = run_dir / "source.par"
                    shutil.copyfile(station_files[station_id], source_par)
                    runspec = run_dir / "run.yaml"
                    write_runspec(runspec, burn)
                    run = subprocess.run(
                        [str(binary), "run", "run.yaml"],
                        cwd=run_dir,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if run.returncode:
                        raise ExecutionError(f"cligen failed {station_id}/{burn}: {run.stderr[-2000:]}")
                    faithful_cli = run_dir / "faithful.cli"
                    faithful_values = parse_cli(faithful_cli)
                    generated.append(
                        {
                            "cohort": cohort,
                            "candidate_index": candidate_index,
                            "burn": burn,
                            "run_dir": run_dir,
                            "source_par": source_par,
                            "runspec": runspec,
                            "faithful_cli": faithful_cli,
                            "faithful_values": faithful_values,
                        }
                    )
            loading = fit_thermal_loading(
                observed["tmean"], [item["faithful_values"][1] for item in generated]
            )
            loading_record = {"station_id": station_id, **loading}
            loading_rows.append(loading_record)
            loading_sha = canonical_digest(loading_record)
            loading_array = np.asarray(loading["loading_c"], dtype=np.float64)
            for item in generated:
                cohort = item["cohort"]
                index = item["candidate_index"]
                seed = contract.derive_thermal_seed(
                    station_id,
                    manifest["candidate_model_id"],
                    cohort["root_seed_hex"],
                    index,
                )
                states = contract.annual_states(seed, manifest["years"])
                candidate_cli = item["run_dir"] / "thermal.cli"
                latent = overlay_cli(item["faithful_cli"], candidate_cli, loading_array, states)
                candidate_values = parse_cli(candidate_cli)
                faithful_metrics = score_stream(
                    item["faithful_values"][0], item["faithful_values"][1], observed, weights, metrics_module
                )
                candidate_metrics = score_stream(
                    candidate_values[0], candidate_values[1], observed, weights, metrics_module
                )
                if not np.array_equal(candidate_values[0], item["faithful_values"][0]):
                    raise ExecutionError("candidate precipitation differs from faithful")
                faithful_score = selector_record(
                    manifest["control_model_id"], index, faithful_metrics
                )
                candidate_score = selector_record(
                    manifest["candidate_model_id"], index, candidate_metrics
                )
                models = {
                    manifest["control_model_id"]: {
                        "metrics": faithful_metrics,
                        "selector_score": faithful_score,
                        "provenance": {
                            "source_par_sha256": digest(item["source_par"]),
                            "runspec_sha256": digest(item["runspec"]),
                            "cli_sha256": digest(item["faithful_cli"]),
                            "provenance_sha256": digest(item["run_dir"] / "faithful.cli.provenance.json"),
                            "quality_report_sha256": digest(item["run_dir"] / "faithful.cli.quality.json"),
                            "cligen_binary_sha256": binary_sha,
                            "metrics_sha256": canonical_digest(faithful_metrics),
                            "selector_score_sha256": canonical_digest(faithful_score),
                        },
                    },
                    manifest["candidate_model_id"]: {
                        "metrics": candidate_metrics,
                        "selector_score": candidate_score,
                        "provenance": {
                            "paired_faithful_cli_sha256": digest(item["faithful_cli"]),
                            "candidate_cli_sha256": digest(candidate_cli),
                            "thermal_seed_u64": seed,
                            "annual_states_sha256": latent["annual_states_sha256"],
                            "delta_tenths_sha256": latent["delta_tenths_sha256"],
                            "loading_sha256": loading_sha,
                            "source_par_sha256": digest(item["source_par"]),
                            "cligen_binary_sha256": binary_sha,
                            "metrics_sha256": canonical_digest(candidate_metrics),
                            "selector_score_sha256": canonical_digest(candidate_score),
                        },
                    },
                }
                rows.append(
                    {
                        "station_id": station_id,
                        "station_regime": observed["regime"],
                        "cohort_id": cohort["cohort_id"],
                        "cohort_root_seed_hex": cohort["root_seed_hex"],
                        "candidate_index": index,
                        "burn": item["burn"],
                        "models": models,
                    }
                )
            station_rows = [row for row in rows if row["station_id"] == station_id]
            for cohort in manifest["cohorts"]:
                cohort_rows = [row for row in station_rows if row["cohort_id"] == cohort["cohort_id"]]
                mixed_scores = [
                    row["models"][model]["selector_score"]
                    for row in cohort_rows
                    for model in contract.MODEL_ORDER
                ]
                faithful_scores = [
                    row["models"][manifest["control_model_id"]]["selector_score"]
                    for row in cohort_rows
                ]
                mixed = contract.select_candidate(mixed_scores)
                faithful = contract.select_candidate(faithful_scores)
                by_identity = {
                    (score["model_id"], score["candidate_index"]): row["models"][score["model_id"]]
                    for row in cohort_rows
                    for score in [
                        row["models"][manifest["control_model_id"]]["selector_score"],
                        row["models"][manifest["candidate_model_id"]]["selector_score"],
                    ]
                }
                mixed_entry = by_identity[(mixed["model_id"], mixed["candidate_index"])]
                faithful_entry = by_identity[
                    (faithful["model_id"], faithful["candidate_index"])
                ]
                selection_rows.append(
                    {
                        "station_id": station_id,
                        "cohort_id": cohort["cohort_id"],
                        "mixed": {
                            **mixed,
                            "score_tuple": [mixed[name] for name in contract.SELECTOR_FIELDS],
                            "metrics": mixed_entry["metrics"],
                            "selected_cli_sha256": mixed_entry["provenance"].get(
                                "candidate_cli_sha256",
                                mixed_entry["provenance"].get("cli_sha256"),
                            ),
                        },
                        "faithful_only": {
                            **faithful,
                            "score_tuple": [faithful[name] for name in contract.SELECTOR_FIELDS],
                            "metrics": faithful_entry["metrics"],
                            "selected_cli_sha256": faithful_entry["provenance"]["cli_sha256"],
                        },
                    }
                )
        if len(rows) * 2 != manifest["resource_bound"]["scored_records_per_execution"]:
            raise ExecutionError("scored resource count differs")
        if len(selection_rows) != manifest["resource_bound"]["selection_cells_per_execution"]:
            raise ExecutionError("selection resource count differs")
        decision_body = build_decision(rows, selection_rows, manifest)
        preflight = {
            "schema_version": "a11e8-calendar-missingness-preflight-1",
            "valid": True,
            "source_transform": "daymet_official_365_v1",
            "normalized_statistic": "daymet_mask_normalized_month_v1",
            "observed": observed_preflight,
            "station_count": 20,
            "cohort_count": 4,
            "candidates_per_cohort": 8,
            "expected_daily_rows_per_stream": 5844,
            "confirmation_target_series_accessed": False,
        }
        loading_bundle = {
            "schema_version": "a11e8-thermal-loading-bundle-1",
            "fit": "observed_covariance_minus_mean_faithful_covariance_rank1",
            "station_count": 20,
            "stations": loading_rows,
            "confirmation_target_series_accessed": False,
        }
        evidence = {
            "schema_version": "a11e8-development-evidence-1",
            "execution_id": manifest["execution_id"],
            "source_commit": source_commit,
            "paired_rows": len(rows),
            "scored_records": len(rows) * 2,
            "rows": rows,
            "selections": selection_rows,
            "decision": decision_body,
            "limitations": [
                "sixteen-year development targets make covariance and spectral metrics noisy",
                "the loading and selector use the same exposed development target "
                "and are not deployable runtime estimators",
                "development observations have been reused throughout the A11 campaign",
                "the temperature-only component does not yet test hydroclimate coupling",
            ],
            "confirmation_target_series_accessed": False,
        }
        evidence["evidence_sha256"] = canonical_digest(evidence)
        decision = {
            "schema_version": "a11e8-development-decision-1",
            "execution_id": manifest["execution_id"],
            "terminal": "EXECUTED-COMPLETE",
            "science_status": "DETERMINISTIC_COHORT_JOINT_FOUNDATION_EVALUATED",
            **decision_body,
            "confirmation_authorized": False,
            "production_authorized": False,
            "public_runtime_authorized": False,
        }
        outputs = {
            "calendar-missingness-preflight-v1.json": preflight,
            "thermal-loading-bundle-v1.json": loading_bundle,
            "development-evidence-v1.json": evidence,
            "development-decision-v1.json": decision,
        }
        for name, value in outputs.items():
            atomic_json(PACKAGE / name, value)
        scientific_paths = [PACKAGE / name for name in outputs]
        receipt = {
            "schema_version": "a11e8-execution-receipt-1",
            "execution_id": manifest["execution_id"],
            **source,
            "runtime": runtime,
            "build": build_provenance,
            "manifest_sha256": digest(MANIFEST),
            "contract_sha256": digest(CONTRACT),
            "inherited_input_hashes": inherited_hashes,
            "outputs": {
                path.name: {"sha256": digest(path), "bytes": path.stat().st_size}
                for path in scientific_paths
            },
            "faithful_streams": len(rows),
            "derived_candidates": len(rows),
            "scored_records": len(rows) * 2,
            "selection_cells": len(selection_rows),
            "mixed_model_selections": len(selection_rows),
            "faithful_only_selections": len(selection_rows),
            "elapsed_seconds": time.monotonic() - started,
            "confirmation_target_series_accessed": False,
        }
        atomic_json(PACKAGE / "execution-receipt-v1.json", receipt)
        provenance = {
            "schema_version": "a11e8-cryptographic-provenance-receipt-1",
            "source_commit": source_commit,
            "source_tree": source["source_tree"],
            "cligen_binary_sha256": binary_sha,
            "cargo_lock_sha256": digest(ROOT / "Cargo.lock"),
            "cargo_toml_sha256": digest(ROOT / "Cargo.toml"),
            "rust_toolchain_sha256": digest(ROOT / "rust-toolchain.toml"),
            "build": build_provenance,
            "station_database_sha256": digest(database),
            "source_parameter_sha256": {
                station_id: digest(path) for station_id, path in sorted(station_files.items())
            },
            "observed_target_identity": inherited_hashes,
            "manifest_sha256": digest(MANIFEST),
            "selector_contract_sha256": digest(CONTRACT),
            "loading_bundle_sha256": digest(PACKAGE / "thermal-loading-bundle-v1.json"),
            "full_cohort_identity_container": "development-evidence-v1.json rows[*].models.*.provenance",
            "selection_identity_container": "development-evidence-v1.json selections[*]",
            "development_evidence_sha256": digest(PACKAGE / "development-evidence-v1.json"),
            "development_decision_sha256": digest(PACKAGE / "development-decision-v1.json"),
            "execution_receipt_sha256": digest(PACKAGE / "execution-receipt-v1.json"),
            "all_inputs_candidates_scores_and_selections_sha256_bound": True,
            "confirmation_target_series_accessed": False,
        }
        atomic_json(PACKAGE / "cryptographic-provenance-receipt-v1.json", provenance)
    finally:
        if RUNTIME_ROOT.exists():
            shutil.rmtree(RUNTIME_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit")
    parser.add_argument("--validate-manifest", action="store_true")
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args()
    manifest = validate_manifest(json.loads(MANIFEST.read_text()))
    if arguments.validate_manifest:
        print(canonical_digest(manifest))
        return
    if not arguments.execute or not arguments.source_commit:
        parser.error("--execute requires --source-commit")
    execute(arguments.source_commit)


if __name__ == "__main__":
    main()
