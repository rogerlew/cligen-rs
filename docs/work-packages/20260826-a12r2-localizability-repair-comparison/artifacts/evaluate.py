#!/usr/bin/env python3
"""Source-bound A12R2 localizability-versus-repair evaluation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
BASE_PATH = ROOT / "docs/work-packages/20260826-a12-station-selection-heuristic-evaluation/artifacts/evaluate.py"
FAILURE_PATH = ROOT / "docs/work-packages/20260826-a12-station-selection-heuristic-evaluation/artifacts/execution-failure-receipt-v1.json"
LOCALIZE_PATH = ROOT / "crates/cligen/src/prism/localize.rs"
RUN_PATH = ROOT / "crates/cligen/src/prism/run.rs"
FROZEN_PREDECESSORS = {
    "a12_evaluator_sha256_at_source_commit": "a8bcc227e4ce5d894a6c789093f93523b1f55e6cb10366d1471926b8aaa8921c",
    "a12_failure_receipt_sha256": "ba103ab7d50fbc510910f980181aec9f3a8c188a05cdbee2b7780f7ce567fa7f",
    "a12_source_commit": "d94f6eab53c9103c797b332ae51aea3a87341bcb",
    "a12r1_localize_rs_sha256_at_source_commit": "2391ab452b52aeceec0f39720c5fd74c6c8494c95963905bad4afab77e33d60a",
    "a12r1_run_rs_sha256_at_source_commit": "78f3a58375d7aae88063c7935b3befe6e81a06721739c57f1aebf4a9ea2c31c1",
    "a12r1_source_commit": "de1502ad4d80a7205ac128c24e1851a42380f5b7",
}


def raw_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def raw_git_show(commit: str, path: Path) -> bytes:
    relative = path.relative_to(ROOT).as_posix()
    result = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=ROOT,
                            check=False, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"cannot authenticate predecessor {commit}:{relative}")
    return result.stdout


def authenticate_predecessors() -> dict[str, str]:
    checks = (
        (FROZEN_PREDECESSORS["a12_source_commit"], BASE_PATH,
         FROZEN_PREDECESSORS["a12_evaluator_sha256_at_source_commit"]),
        (FROZEN_PREDECESSORS["a12r1_source_commit"], LOCALIZE_PATH,
         FROZEN_PREDECESSORS["a12r1_localize_rs_sha256_at_source_commit"]),
        (FROZEN_PREDECESSORS["a12r1_source_commit"], RUN_PATH,
         FROZEN_PREDECESSORS["a12r1_run_rs_sha256_at_source_commit"]),
    )
    for commit, path, expected in checks:
        if raw_digest(raw_git_show(commit, path)) != expected or raw_digest(path.read_bytes()) != expected:
            raise RuntimeError(f"predecessor dependency identity differs: {path}")
    if raw_digest(FAILURE_PATH.read_bytes()) != FROZEN_PREDECESSORS["a12_failure_receipt_sha256"]:
        raise RuntimeError("A12 failure receipt identity differs")
    return dict(FROZEN_PREDECESSORS)


AUTHENTICATED_PREDECESSORS = authenticate_predecessors()
BASE_SPEC = importlib.util.spec_from_file_location("a12_base_evaluate", BASE_PATH)
if BASE_SPEC is None or BASE_SPEC.loader is None:
    raise RuntimeError("cannot load A12 evaluator")
BASE = importlib.util.module_from_spec(BASE_SPEC)
sys.modules[BASE_SPEC.name] = BASE
BASE_SPEC.loader.exec_module(BASE)

EvaluationError = BASE.EvaluationError


class EvaluationHold(EvaluationError):
    """A frozen scientific feasibility gate did not pass."""

    def __init__(self, disposition: str, point_id: str, detail: str):
        super().__init__(f"{disposition}: {point_id}: {detail}")
        self.disposition = disposition
        self.point_id = point_id
        self.detail = detail
MANIFEST_PATH = PACKAGE / "evaluation-manifest-v1.json"
SCHEMA_PATH = PACKAGE / "evaluation-manifest-v1.schema.json"
SPEC_PATH = ROOT / "docs/specifications/SPEC-A12R2-LOCALIZABILITY-REPAIR-COMPARISON.md"
PACKAGE_PATH = PACKAGE.parent / "package.md"
PLAN_PATH = ROOT / "docs/exec-plans/20260826-a12r2-localizability-repair-comparison.md"
REVIEW_PATH = PACKAGE / "review.md"
TEST_RESULTS_PATH = PACKAGE / "test-results.md"

SELECTORS = ("closest", "current", "reference")
STRATEGIES = ("repair", "localizable")
POLICIES = (
    "closest_independent_repair_v1",
    "cligen_prism_rank_sum_independent_repair_v1",
    "elevation_prism_reference_independent_repair_v1",
    "closest_localizable_v1",
    "cligen_prism_rank_sum_localizable_v1",
    "elevation_prism_reference_localizable_v1",
)
ARM = {
    ("repair", "closest"): POLICIES[0],
    ("repair", "current"): POLICIES[1],
    ("repair", "reference"): POLICIES[2],
    ("localizable", "closest"): POLICIES[3],
    ("localizable", "current"): POLICIES[4],
    ("localizable", "reference"): POLICIES[5],
}
RAW_BASE_KEYS = {
    "closest": "closest_v1",
    "current": "cligen_prism_rank_sum_v1",
    "reference": "wepppy_elevation_prism_reference_v1",
}
METRICS = BASE.METRICS
REPAIR_METHOD_ID = "degenerate_occurrence_independent_prism_v1"
REPAIR_PROFILE_ID = "stochastic_prism_localized_par_degenerate_occurrence_independent_v1"


def validate_manifest(value: Any) -> dict[str, Any]:
    expected_fields = {
        "bootstrap", "corpus", "decision", "evaluation_id", "input_hashes",
        "metrics", "policies", "predecessors", "runtime", "schema_version",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise EvaluationError("evaluation manifest fields differ")
    if value["schema_version"] != 1 or value["evaluation_id"] != "a12r2-localizability-repair-comparison-v1":
        raise EvaluationError("evaluation identity differs")
    if tuple(value["metrics"]) != METRICS or tuple(value["policies"]) != POLICIES:
        raise EvaluationError("metric or policy roster differs")
    if value["predecessors"] != AUTHENTICATED_PREDECESSORS:
        raise EvaluationError("predecessor identity differs")
    if value["bootstrap"] != {
        "algorithm": "numpy_philox", "common_resamples": True,
        "domain": "a12r2_localizability_repair_site_median_v1",
        "quantile_method": "linear", "replicates": 10000,
        "seed": 1201202,
        "seed_derivation": "numpy_seedsequence_u32le_sha256_domain_plus_integer_seed",
    }:
        raise EvaluationError("bootstrap contract differs")
    if value["decision"] != {
        "family_worsening_limit_fraction": 0.05,
        "support_rule": "paired_composite_median_lt_0_and_bootstrap_upper_lt_0_and_site_win_fraction_gt_0.5_and_no_family_median_more_than_5pct_above_baseline",
        "strategy_preference_rule": "all_three_localizable_else_all_three_repair_else_any_support_mixed_else_no_uniform_advantage",
    }:
        raise EvaluationError("decision contract differs")
    if value["runtime"] != {"python": "3.12.13", "numpy": "2.3.5"}:
        raise EvaluationError("runtime contract differs")
    expected_corpus = {
        "calendar_axis_rows": 10958,
        "masked_dates": [f"{year}-12-31" for year in range(1980, 2010) if year % 4 == 0],
        "observed_rows": 10950, "period_end_inclusive": "2009-12-31",
        "period_start": "1980-01-01", "role": "fit_validation", "site_count": 240,
        "source_transform": "daymet_official_365_v1",
    }
    if value["corpus"] != expected_corpus:
        raise EvaluationError("corpus contract differs")
    return value


def verify_inputs(manifest: dict[str, Any]) -> dict[str, str]:
    return BASE.verify_inputs(manifest)


def source_paths() -> list[Path]:
    return [
        Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_evaluate.py",
        SPEC_PATH, PACKAGE_PATH, PLAN_PATH, REVIEW_PATH, TEST_RESULTS_PATH,
        BASE_PATH, FAILURE_PATH,
        ROOT / "docs/specifications/SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION.md",
        ROOT / "docs/specifications/SPEC-A12-STATION-SELECTION-EVALUATION.md",
        BASE.A10_SPEC, BASE.A10_PRISM_SPEC, ROOT / "docs/cli-guide.md", ROOT / "README.md",
        ROOT / "docs/ROADMAP.md", ROOT / "docs/specifications/README.md",
        ROOT / "docs/work-packages/README.md", BASE.LOCALIZE_RS, BASE.RUN_RS,
        BASE.PRISM_DISTRIBUTION, BASE.STATION_MANIFESTS, ROOT / "Cargo.lock",
        ROOT / "rust-toolchain.toml",
    ]


def verify_source(source_commit: str) -> dict[str, str]:
    if len(source_commit) != 40 or source_commit != BASE.git("rev-parse", "origin/main").decode().strip():
        raise EvaluationError("source commit is not exact origin/main")
    result = {}
    for path in source_paths():
        current = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        committed = BASE.git("show", f"{source_commit}:{relative}")
        if current != committed:
            raise EvaluationError(f"working source differs from commit: {relative}")
        result[relative] = BASE.digest_bytes(current)
    return result


def build_release(source_commit: str) -> None:
    source_hashes = verify_source(source_commit)
    if BASE.git("rev-parse", "HEAD").decode().strip() != source_commit or BASE.git("status", "--porcelain"):
        raise EvaluationError("release build requires the exact clean published source commit")
    command = ["cargo", "build", "--release", "--locked", "--bin", "cligen"]
    if subprocess.run(command, cwd=ROOT, check=False).returncode != 0:
        raise EvaluationError("release build failed")
    binary = ROOT / "target/release/cligen"
    receipt = {
        "schema_version": "a12r2-build-receipt-1", "source_commit": source_commit,
        "source_hashes": source_hashes, "cargo_lock_sha256": BASE.digest(ROOT / "Cargo.lock"),
        "rust_toolchain_sha256": BASE.digest(ROOT / "rust-toolchain.toml"),
        "rustc_verbose": BASE.command_output("rustc", "-vV"),
        "cargo_version": BASE.command_output("cargo", "--version"), "build_command": command,
        "features": "default", "binary_path": str(binary.relative_to(ROOT)),
        "cligen_binary_sha256": BASE.digest(binary),
    }
    BASE.atomic_json(PACKAGE / "build-receipt-v1.json", receipt)


def verify_build_receipt(source_commit: str, source_hashes: dict[str, str], binary: Path,
                         path: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text())
    expected = {
        "schema_version": "a12r2-build-receipt-1", "source_commit": source_commit,
        "source_hashes": source_hashes, "cargo_lock_sha256": BASE.digest(ROOT / "Cargo.lock"),
        "rust_toolchain_sha256": BASE.digest(ROOT / "rust-toolchain.toml"),
        "rustc_verbose": BASE.command_output("rustc", "-vV"),
        "cargo_version": BASE.command_output("cargo", "--version"),
        "build_command": ["cargo", "build", "--release", "--locked", "--bin", "cligen"],
        "features": "default", "binary_path": str(binary.relative_to(ROOT)),
        "cligen_binary_sha256": BASE.digest(binary),
    }
    if receipt != expected:
        raise EvaluationError("build receipt identity differs")
    return receipt


def repair_parameters(par: dict[str, Any], normals: dict[str, Any]) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    old_mean = par["mean"].astype(np.float64)
    old_pww = par["pww"].astype(np.float64)
    old_pwd = par["pwd"].astype(np.float64)
    targets = np.array(normals["monthly_ppt_in"], dtype=np.float64)
    intensity = par["intensity"].astype(np.float64)
    output = {name: np.zeros(12) for name in ("mean", "pww", "pwd", "intensity")}
    repairs = []
    for month in range(12):
        denominator = 1.0 - old_pww[month] + old_pwd[month]
        q = old_pwd[month] / denominator
        current = BASE.DAYS[month] * q * old_mean[month]
        if (old_pww[month] == 0.0 and old_pwd[month] == 0.0
                and math.isfinite(old_mean[month]) and old_mean[month] > 0.0
                and math.isfinite(targets[month]) and targets[month] > 0.0):
            continuous_count = min(max(targets[month] / (2.0 * old_mean[month]), 0.1), BASE.DAYS[month] - 0.25)
            encoded_q_f64 = min(max(float(f"{continuous_count / BASE.DAYS[month]:.2f}"), 0.01), 0.99)
            values = (targets[month] / (BASE.DAYS[month] * encoded_q_f64), encoded_q_f64,
                      encoded_q_f64, intensity[month] * 2.0)
            repairs.append({
                "method_id": REPAIR_METHOD_ID, "month": month + 1,
                "original_pww": float(str(np.float32(old_pww[month]))),
                "original_pwd": float(str(np.float32(old_pwd[month]))),
                "source_mean_wet_day_in": float(str(np.float32(old_mean[month]))),
                "prism_target_ppt_in": targets[month],
                "precipitation_ratio_undefined_reason": "source_expected_monthly_precipitation_is_zero",
                "continuous_limit_wet_day_count": continuous_count,
                "continuous_limit_wet_fraction": continuous_count / BASE.DAYS[month],
                "derived_wet_day_count": BASE.DAYS[month] * encoded_q_f64,
                "derived_wet_fraction": encoded_q_f64,
                "persistence_assumption": "independent_days_pww_equals_pwd_equals_q",
                "encoded_mean_wet_day_in": float(str(np.float32(BASE.f6_2_f32(values[0])))),
                "encoded_pww": float(str(np.float32(BASE.f6_2_f32(values[1])))),
                "encoded_pwd": float(str(np.float32(BASE.f6_2_f32(values[2])))),
                "encoded_intensity_in_per_hour": float(str(np.float32(BASE.f6_2_f32(values[3])))),
            })
        else:
            if not math.isfinite(current) or current <= 0.0 or not math.isfinite(q) or not 0.0 < q < 1.0:
                raise EvaluationError(f"month {month + 1} cannot be localized")
            delta = targets[month] / current
            old_count = BASE.DAYS[month] * q
            count = old_count
            if targets[month] >= 0.05 and current >= 0.05:
                count = min(max(old_count * (1.0 + delta) / 2.0, old_count / 2.0), old_count * 2.0)
                count = min(max(count, 0.1), BASE.DAYS[month] - 0.25)
            new_q = count / BASE.DAYS[month]
            persistence = old_pwd[month] / old_pww[month]
            new_pww = 1.0 / (1.0 - persistence + persistence / new_q)
            new_pwd = ((new_pww - 1.0) * new_q) / (new_q - 1.0)
            values = (targets[month] / (BASE.DAYS[month] * new_q), new_pww, new_pwd,
                      intensity[month] * (min(max(delta, 0.5), 2.0)
                                          if targets[month] >= 0.05 and current >= 0.05 else 1.0))
        for name, value in zip(("mean", "pww", "pwd", "intensity"), values):
            output[name][month] = BASE.f6_2_f32(value)
    output["tmax"] = np.array([BASE.f6_2_f32(value) for value in normals["monthly_tmax_f"]])
    output["tmin"] = np.array([BASE.f6_2_f32(value) for value in normals["monthly_tmin_f"]])
    for month in range(12):
        if (not all(math.isfinite(output[name][month])
                    for name in ("mean", "pww", "pwd", "tmax", "tmin", "intensity"))
                or targets[month] > 0.0 and output["mean"][month] <= 0.0
                or not 0.0 < output["pww"][month] < 1.0
                or not 0.0 < output["pwd"][month] < 1.0
                or output["tmax"][month] < output["tmin"][month]):
            raise EvaluationError(f"encoded constraints fail in month {month + 1}")
    return output, repairs


def failure_details(error: EvaluationError) -> tuple[int | None, str]:
    match = re.search(r"month (\d+)", str(error))
    return (None if match is None else int(match.group(1)), str(error))


def select_arms(rows: list[dict[str, Any]], target: dict[str, Any], normals: dict[str, Any],
                par_cache: dict[Path, dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    raw, diagnostics = BASE.select_policies(rows, target, normals, par_cache)
    by_id = {row["id"]: row for row in rows}
    eligible = []
    matrix = []
    for diagnostic in diagnostics:
        station = by_id[diagnostic["station_id"]]
        try:
            BASE.localized_parameters(par_cache[station["path"]], normals)
            ok, month, reason = True, None, None
            eligible.append(diagnostic)
        except EvaluationError as error:
            month, reason = failure_details(error)
            ok = False
        matrix.append({**diagnostic, "ordinary_localizable": ok,
                       "failure_month": month, "failure_reason": reason})
    arms = {}
    displacements = {}
    for selector in SELECTORS:
        raw_station = raw[RAW_BASE_KEYS[selector]]
        arms[ARM[("repair", selector)]] = raw_station
    if not eligible:
        for selector in SELECTORS:
            displacements[selector] = {
                "raw_station_id": arms[ARM[("repair", selector)]]["id"],
                "filtered_station_id": None, "winner_changed": None,
                "distance_displacement_km": None,
            }
        return arms, matrix, displacements

    filtered = {
        "closest": min(eligible, key=lambda row: (row["distance_km"], row["station_id"])),
        "current": min(eligible, key=lambda row: (row["current_score"], row["distance_km"], row["station_id"])),
        "reference": min(eligible, key=lambda row: (row["reference_score"], row["distance_km"], row["station_id"])),
    }
    for selector in SELECTORS:
        raw_station = arms[ARM[("repair", selector)]]
        filtered_station = by_id[filtered[selector]["station_id"]]
        arms[ARM[("localizable", selector)]] = filtered_station
        displacements[selector] = {
            "raw_station_id": raw_station["id"], "filtered_station_id": filtered_station["id"],
            "winner_changed": raw_station["id"] != filtered_station["id"],
            "distance_displacement_km": filtered_station["distance_km"] - raw_station["distance_km"],
        }
    return arms, matrix, displacements


def runtime_repair_selection(binary: Path, data_root: Path, target: dict[str, Any]) -> dict[str, Any]:
    output = data_root / "runtime-selections" / target["point_id"]
    output.parent.mkdir(exist_ok=True)
    environment = os.environ.copy()
    environment["CLIGEN_DATA_DIR"] = str(data_root)
    command = [
        str(binary), "prism", "run", "--longitude", str(target["longitude"]),
        "--latitude", str(target["latitude"]), "--years", "1",
        "--degenerate-occurrence-repair", "independent-prism-v1", "--output-dir", str(output),
    ]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True, env=environment)
    if result.returncode != 0:
        raise EvaluationError(f"repair runtime probe failed: {result.stderr.strip()}")
    selection = json.loads((output / "station-selection.json").read_text())
    artifact = json.loads((output / "artifact-manifest.json").read_text())
    localization = json.loads((output / "localization.json").read_text())
    method = json.loads((output / "method.json").read_text())
    request = json.loads((output / "request.json").read_text())
    normals = json.loads((output / "prism-normals.json").read_text())
    binary_hash = BASE.digest(binary)
    source_hash = BASE.digest(output / "source-station.par")
    profile = REPAIR_PROFILE_ID
    method_id = REPAIR_METHOD_ID
    expected_artifacts = {
        "climate.cli", "climate.cli.provenance.json", "climate.cli.quality.json", "inp.yaml",
        "localization.json", "localized.par", "method.json", "prism-normals.json", "request.json",
        "source-station.par", "station-selection.json",
    }
    artifact_rows = {row["path"]: row for row in artifact.get("artifacts", [])}
    artifacts_valid = set(artifact_rows) == expected_artifacts
    for name, row in artifact_rows.items():
        path = output / name
        artifacts_valid = (artifacts_valid and path.is_file() and row.get("bytes") == path.stat().st_size
                           and row.get("sha256") == BASE.digest(path))
    if (selection.get("schema_version") != 2
            or selection.get("profile_id") != profile
            or selection.get("cligen_binary_sha256") != binary_hash
            or selection.get("selected_source_par_sha256") != source_hash
            or artifact.get("profile_id") != profile
            or artifact.get("executable", {}).get("sha256") != binary_hash
            or localization.get("schema_version") != 2
            or localization.get("source_par_sha256") != source_hash
            or localization.get("localized_par_sha256") != BASE.digest(output / "localized.par")
            or localization.get("degenerate_occurrence_repair_method_id") != method_id
            or localization.get("profile_id") != profile
            or method.get("schema_version") != 2 or method.get("method_id") != profile
            or method.get("active_extension", {}).get("method_id") != method_id
            or request.get("degenerate_occurrence_repair_method_id") != method_id
            or not artifacts_valid):
        raise EvaluationError("repair receipt provenance differs")
    repair_months = [row.get("month") for row in localization.get("occurrence_repairs", [])]
    precipitation_ratio = localization.get("precipitation_ratio")
    if (not isinstance(precipitation_ratio, list) or len(precipitation_ratio) != 12
            or any(precipitation_ratio[month - 1] is not None for month in repair_months)):
        raise EvaluationError("repair receipt null-ratio contract differs")
    warnings = [line for line in result.stderr.splitlines() if line.startswith("warning:")]
    normalized = normalize_selection_receipt(selection)

    return {
        "point_id": target["point_id"], "selected_station_id": selection["selected_station_id"],
        "selected_source_par_sha256": source_hash, "cligen_binary_sha256": binary_hash,
        "normalized_station_selection_sha256": BASE.canonical_digest(normalized),
        "localization_receipt_sha256": BASE.digest(output / "localization.json"),
        "method_sha256": BASE.digest(output / "method.json"),
        "repair_count": len(localization["occurrence_repairs"]),
        "warning_count": len(warnings),
        "selection_and_manifest_binary_sha256_equal": True,
        "_selection": selection, "_normals": normals,
        "_repair_events": localization["occurrence_repairs"], "_warnings": warnings,
        "_localized": BASE.parse_par(output / "localized.par"),
    }


def normalize_selection_receipt(selection: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(selection))
    normalized["selected_source_par_path"] = f"<station-cache>/{selection['selected_station_id']}"
    for candidate in normalized["candidates"]:
        candidate["path"] = f"<station-cache>/{candidate['station_id']}"
    return normalized


def runtime_repair_expected_failure(binary: Path, data_root: Path,
                                    target: dict[str, Any]) -> dict[str, Any]:
    output = data_root / "runtime-selections" / target["point_id"]
    output.parent.mkdir(exist_ok=True)
    environment = os.environ.copy()
    environment["CLIGEN_DATA_DIR"] = str(data_root)
    command = [
        str(binary), "prism", "run", "--longitude", str(target["longitude"]),
        "--latitude", str(target["latitude"]), "--years", "1",
        "--degenerate-occurrence-repair", "independent-prism-v1", "--output-dir", str(output),
    ]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True,
                            env=environment)
    if result.returncode == 0 or output.exists():
        raise EvaluationError("repair-ineligible production probe did not fail atomically")
    return {"point_id": target["point_id"], "returncode": result.returncode,
            "stderr_sha256": BASE.digest_bytes(result.stderr.encode()),
            "output_published": False, "expected_failure": True}


def assert_localized_parity(expected: dict[str, np.ndarray], actual: dict[str, Any]) -> None:
    for name in ("mean", "pww", "pwd", "tmax", "tmin", "intensity"):
        if not np.array_equal(expected[name].astype(np.float32), actual[name].astype(np.float32)):
            raise EvaluationError(f"Python/Rust repaired localization differs: {name}")


def assert_repair_receipt_parity(expected: list[dict[str, Any]], actual: list[dict[str, Any]],
                                 warnings: list[str]) -> None:
    if actual != expected or len(warnings) != len(expected):
        raise EvaluationError("Python/Rust structured repair receipt differs")
    for event, warning in zip(expected, warnings):
        if (REPAIR_METHOD_ID not in warning or f"month {event['month']}" not in warning
                or "source PWW=0 PWD=0" not in warning):
            raise EvaluationError("structured repair warning differs")


def verify_current_score_parity(selection: dict[str, Any], diagnostics: list[dict[str, Any]]) -> None:
    rust = {row["station_id"]: row for row in selection["candidates"]}
    for row in diagnostics:
        if not math.isclose(rust[row["station_id"]]["score"], row["current_score"],
                            rel_tol=0.0, abs_tol=0.0):
            raise EvaluationError("Python/Rust current-selector score differs")


def extracted_tree_identity(root: Path) -> tuple[int, str]:
    files = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files[path.relative_to(root).as_posix()] = {
            "bytes": path.stat().st_size, "sha256": BASE.digest(path),
        }
    return len(files), BASE.canonical_digest(files)


def arm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "median_composite": float(np.median([row["metrics"]["composite"] for row in rows])),
        "family_medians": {
            metric: float(np.median([row["metrics"][metric] for row in rows])) for metric in METRICS
        },
    }


def paired_comparison(candidate: list[dict[str, Any]], baseline: list[dict[str, Any]],
                      manifest: dict[str, Any]) -> dict[str, Any]:
    candidate_summary = arm_summary(candidate)
    baseline_summary = arm_summary(baseline)
    deltas = np.array([
        row["metrics"]["composite"] - baseline[index]["metrics"]["composite"]
        for index, row in enumerate(candidate)
    ])
    worsening = {
        metric: (None if baseline_summary["family_medians"][metric] == 0.0 else
                 (candidate_summary["family_medians"][metric] - baseline_summary["family_medians"][metric])
                 / baseline_summary["family_medians"][metric])
        for metric in METRICS
    }
    supported = (
        float(np.median(deltas)) < 0.0
        and BASE.bootstrap_interval(deltas, manifest)[1] < 0.0
        and float(np.mean(deltas < 0.0)) > 0.5
        and all(candidate_summary["family_medians"][metric]
                <= baseline_summary["family_medians"][metric]
                * (1.0 + manifest["decision"]["family_worsening_limit_fraction"])
                for metric in METRICS)
    )
    return {
        "paired_composite_median_delta": float(np.median(deltas)),
        "paired_bootstrap_95_interval": BASE.bootstrap_interval(deltas, manifest),
        "strict_site_win_fraction": float(np.mean(deltas < 0.0)),
        "paired_family_median_deltas": {
            metric: float(np.median([row["metrics"][metric] - baseline[index]["metrics"][metric]
                                     for index, row in enumerate(candidate)]))
            for metric in METRICS
        },
        "family_worsening_fractions": worsening, "supported": supported,
    }


def selector_disposition(current_supported: bool, reference_supported: bool,
                         summaries: dict[str, dict[str, Any]], strategy: str) -> str:
    current = ARM[(strategy, "current")]
    reference = ARM[(strategy, "reference")]
    if current_supported and (not reference_supported
                              or summaries[current]["median_composite"] <= summaries[reference]["median_composite"]):
        return "CURRENT_HEURISTIC_APPROPRIATE"
    if reference_supported:
        return "ELEVATION_REFERENCE_BETTER"
    return "CLOSEST_PREFERRED"


def strategy_disposition(localizable_supported: list[bool], repair_supported: list[bool]) -> str:
    if all(localizable_supported):
        return "LOCALIZABILITY_FILTER_PREFERRED"
    if all(repair_supported):
        return "SELECTED_DONOR_REPAIR_PREFERRED"
    if any(localizable_supported) or any(repair_supported):
        return "STRATEGY_EFFECT_MIXED"
    return "NO_UNIFORM_STRATEGY_ADVANTAGE"


def summarize(site_rows: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    by_arm = {arm: [row["policies"][arm] for row in site_rows] for arm in POLICIES}
    summaries = {arm: arm_summary(rows) for arm, rows in by_arm.items()}
    selector_comparisons = {}
    selector_dispositions = {}
    for strategy in STRATEGIES:
        baseline = ARM[(strategy, "closest")]
        selector_comparisons[strategy] = {}
        support = {}
        for selector in ("current", "reference"):
            arm = ARM[(strategy, selector)]
            comparison = paired_comparison(by_arm[arm], by_arm[baseline], manifest)
            selector_comparisons[strategy][selector] = comparison
            support[selector] = comparison["supported"]
        selector_dispositions[strategy] = selector_disposition(
            support["current"], support["reference"], summaries, strategy
        )
    strategy_comparisons = {}
    localizable_supported = []
    repair_supported = []
    for selector in SELECTORS:
        repaired = by_arm[ARM[("repair", selector)]]
        localizable = by_arm[ARM[("localizable", selector)]]
        toward_localizable = paired_comparison(localizable, repaired, manifest)
        toward_repair = paired_comparison(repaired, localizable, manifest)
        strategy_comparisons[selector] = {
            "localizable_over_repair": toward_localizable,
            "repair_over_localizable": toward_repair,
        }
        localizable_supported.append(toward_localizable["supported"])
        repair_supported.append(toward_repair["supported"])
    strategy_result = strategy_disposition(localizable_supported, repair_supported)
    decision = {
        "schema_version": "a12r2-station-selection-decision-1",
        "evaluation_id": manifest["evaluation_id"], "terminal": "EXECUTED-COMPLETE",
        "strategy_disposition": strategy_result,
        "selector_dispositions": selector_dispositions,
        "runtime_default_change_authorized": False, "confirmation_authorized": False,
    }
    return {
        "arm_summaries": summaries, "selector_comparisons": selector_comparisons,
        "strategy_comparisons": strategy_comparisons,
    }, decision


def execution_paths(replay: bool, root: Path = PACKAGE) -> dict[str, Path]:
    marker = "-replay" if replay else ""
    return {
        "preflight": root / f"calendar-preflight{marker}-v1.json",
        "feasibility": root / f"feasibility-evidence{marker}-v1.json",
        "evidence": root / f"station-selection-evidence{marker}-v1.json",
        "decision": root / f"station-selection-decision{marker}-v1.json",
        "receipt": root / f"execution{marker}-receipt-v1.json",
    }


def execute_science(source_commit: str, binary: Path, build_receipt_path: Path,
                    station_archive: Path, replay: bool = False,
                    output_root: Path = PACKAGE) -> None:
    started = time.perf_counter()
    paths = execution_paths(replay, output_root)
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if {"python": platform.python_version(), "numpy": np.__version__} != manifest["runtime"]:
        raise EvaluationError("scientific runtime identity differs")
    input_hashes = verify_inputs(manifest)
    source_hashes = verify_source(source_commit)
    binary = binary.resolve()
    if not binary.is_file():
        raise EvaluationError("cligen binary does not exist")
    binary_hash = BASE.digest(binary)
    verify_build_receipt(source_commit, source_hashes, binary, build_receipt_path)
    prism_identity = BASE.verify_prism_cache(BASE.cache_root())
    prism_runtime = Path(prism_identity.pop("_runtime_path"))
    with tempfile.TemporaryDirectory(prefix="cligen-a12r2-") as temporary:
        isolated = Path(temporary)
        collection_root, station_identity = BASE.extract_registered_station_archive(station_archive, isolated)
        isolated_prism = isolated / "prism" / prism_identity["bundle_id"] / prism_identity["bundle_version"]
        isolated_prism.parent.mkdir(parents=True)
        shutil.copytree(prism_runtime, isolated_prism, copy_function=shutil.copy2)
        copied_identity = BASE.verify_prism_cache(isolated)
        copied_identity.pop("_runtime_path")
        if copied_identity != prism_identity:
            raise EvaluationError("isolated PRISM identity differs")
        isolated_binary = isolated / "bin/cligen"
        isolated_binary.parent.mkdir()
        shutil.copy2(binary, isolated_binary)
        if BASE.digest(isolated_binary) != binary_hash:
            raise EvaluationError("isolated binary identity differs")
        rows = BASE.station_rows(collection_root)
        objects, preflight = BASE.load_fit_validation(manifest)
        preflight["schema_version"] = "a12r2-calendar-preflight-1"
        preflight_path = paths["preflight"]
        BASE.atomic_json(preflight_path, preflight)
        par_cache: dict[Path, dict[str, Any]] = {}
        prepared_sites = []
        feasibility_rows = []
        feasibility_failures = []
        runtime_receipts = []
        grid_identities = set()
        # Complete every feasibility and production-parity gate before reading
        # observed descriptors or computing a single quality metric.
        for value in objects:
            target = {"point_id": value["point_id"], "latitude": value["latitude"],
                      "longitude": value["longitude"], "elevation_m": value["elevation_m"]}
            normals = BASE.query_normals(isolated_binary, isolated, target["latitude"], target["longitude"])
            arms, matrix, displacements = select_arms(rows, target, normals, par_cache)
            arms = {name: dict(station) for name, station in arms.items()}
            if sum(row["ordinary_localizable"] for row in matrix) == 0:
                feasibility_failures.append({
                    "disposition": "HOLD-NO-ELIGIBLE-TEN", "point_id": target["point_id"],
                    "detail": "none of the nearest ten completes ordinary localization",
                })
            repair_failures = []
            for selector in SELECTORS:
                arm = ARM[("repair", selector)]
                station = arms[arm]
                try:
                    repair_parameters(par_cache[station["path"]], normals)
                except EvaluationError as error:
                    repair_failures.append({"selector": selector, "reason": str(error)})
                    feasibility_failures.append({
                        "disposition": "HOLD-REPAIR-INELIGIBLE", "point_id": target["point_id"],
                        "detail": f"{selector}: {error}",
                    })
            grid_identities.add((normals["bundle_id"], normals["bundle_version"],
                                 normals["grid_manifest_sha256"], normals["source_manifest_sha256"]))
            runtime_parity_complete = False
            runtime_failure_receipt = None
            if not any(row["selector"] == "current" for row in repair_failures):
                probe = runtime_repair_selection(isolated_binary, isolated, target)
                runtime_normals = probe.pop("_normals")
                runtime_localized = probe.pop("_localized")
                selection = probe.pop("_selection")
                runtime_events = probe.pop("_repair_events")
                runtime_warnings = probe.pop("_warnings")
                if runtime_normals != normals:
                    raise EvaluationError("query/run PRISM normals differ")
                raw_for_parity = {
                    RAW_BASE_KEYS[selector]: arms[ARM[("repair", selector)]] for selector in SELECTORS
                }
                BASE.verify_selector_parity(selection, raw_for_parity, matrix)
                verify_current_score_parity(selection, matrix)
                current = arms[ARM[("repair", "current")]]
                if probe["selected_station_id"] != current["id"]:
                    raise EvaluationError("repair runtime winner differs")
                if probe["selected_source_par_sha256"] != par_cache[current["path"]]["sha256"]:
                    raise EvaluationError("runtime/Python selected source identity differs")
                expected_current, current_repairs = repair_parameters(par_cache[current["path"]], normals)
                assert_localized_parity(expected_current, runtime_localized)
                assert_repair_receipt_parity(current_repairs, runtime_events, runtime_warnings)
                if (probe["repair_count"] != len(current_repairs)
                        or probe["warning_count"] != len(current_repairs)):
                    raise EvaluationError("repair receipt count differs")
                runtime_receipts.append(probe)
                runtime_parity_complete = True
            else:
                runtime_failure_receipt = runtime_repair_expected_failure(
                    isolated_binary, isolated, target
                )
                runtime_receipts.append(runtime_failure_receipt)
            feasibility_rows.append({
                "point_id": value["point_id"], "regime": value["regime"],
                "eligible_candidate_count": sum(row["ordinary_localizable"] for row in matrix),
                "candidate_pool": matrix, "policy_displacements": displacements,
                "repair_failures": repair_failures, "current_runtime_parity_complete": runtime_parity_complete,
                "current_runtime_expected_failure": runtime_failure_receipt,
            })
            prepared_sites.append((value, normals, arms, matrix, displacements))

        if (len(prepared_sites) != 240 or len(feasibility_rows) != 240
                or sum(len(row["candidate_pool"]) for row in feasibility_rows) != 2400):
            raise EvaluationError("feasibility pass site count differs")
        final_prism = BASE.verify_prism_cache(isolated)
        final_prism.pop("_runtime_path")
        final_count, final_tree = extracted_tree_identity(collection_root)
        if (BASE.digest(isolated_binary) != binary_hash or final_prism != prism_identity
                or BASE.digest(station_archive) != station_identity["archive_sha256"]
                or final_count != station_identity["extracted_file_count"]
                or final_tree != station_identity["extracted_tree_sha256"]):
            raise EvaluationError("isolated runtime input identity changed during feasibility")
        feasibility_evidence = {
            "schema_version": "a12r2-feasibility-evidence-1",
            "evaluation_id": manifest["evaluation_id"], "source_commit": source_commit,
            "cligen_binary_sha256": binary_hash, "station_collection": station_identity,
            "prism_cache_file_set_sha256": prism_identity["file_set_sha256"],
            "authenticated_predecessors": AUTHENTICATED_PREDECESSORS,
            "site_count": len(feasibility_rows), "candidate_count": 2400,
            "failures": feasibility_failures, "site_results": feasibility_rows,
            "quality_scoring_started": False, "confirmation_target_series_accessed": False,
        }
        feasibility_evidence["evidence_sha256"] = BASE.canonical_digest(feasibility_evidence)
        feasibility_path = paths["feasibility"]
        BASE.atomic_json(feasibility_path, feasibility_evidence)
        if feasibility_failures:
            first = feasibility_failures[0]
            raise EvaluationHold(first["disposition"], first["point_id"], first["detail"])
        site_rows = []
        for value, normals, arms, matrix, displacements in prepared_sites:
            observed = BASE.observed_descriptors(value)
            policy_rows = {}
            for strategy in STRATEGIES:
                for selector in SELECTORS:
                    arm = ARM[(strategy, selector)]
                    station = arms[arm]
                    par = par_cache[station["path"]]
                    if strategy == "repair":
                        localized, repairs = repair_parameters(par, normals)
                    else:
                        localized, repairs = BASE.localized_parameters(par, normals), []
                    policy_rows[arm] = {
                        "selected_station_id": station["id"],
                        "selected_source_par_sha256": par["sha256"],
                        "distance_km": station["distance_km"], "repair_count": len(repairs),
                        "metrics": BASE.errors(par, observed, normals, localized),
                    }
            site_rows.append({
                "point_id": value["point_id"], "regime": value["regime"],
                "eligible_candidate_count": sum(row["ordinary_localizable"] for row in matrix),
                "candidate_pool": matrix, "policy_displacements": displacements,
                "policies": policy_rows,
            })
    if (len(site_rows) != 240 or sum(len(row["candidate_pool"]) for row in site_rows) != 2400
            or len(grid_identities) != 1):
        raise EvaluationError("site/candidate count or PRISM identity differs")
    summaries, decision = summarize(site_rows, manifest)
    feasibility = {
        "candidate_count": sum(len(row["candidate_pool"]) for row in site_rows),
        "ordinary_localizable_count": sum(row["eligible_candidate_count"] for row in site_rows),
        "site_eligible_count_min": min(row["eligible_candidate_count"] for row in site_rows),
        "site_eligible_count_max": max(row["eligible_candidate_count"] for row in site_rows),
        "winner_change_counts": {
            selector: sum(row["policy_displacements"][selector]["winner_changed"] for row in site_rows)
            for selector in SELECTORS
        },
    }
    evidence = {
        "schema_version": "a12r2-station-selection-evidence-1",
        "evaluation_id": manifest["evaluation_id"], "source_commit": source_commit,
        "cligen_binary_sha256": binary_hash, "build_receipt_sha256": BASE.digest(build_receipt_path),
        "station_collection": station_identity, "prism_identity": list(next(iter(grid_identities))),
        "prism_cache_identity": prism_identity,
        "preflight_identity": {"sha256": BASE.digest(preflight_path),
                               "object_set_sha256": preflight["object_set_sha256"],
                               "shard_set_sha256": preflight["shard_set_sha256"]},
        "authenticated_predecessors": AUTHENTICATED_PREDECESSORS,
        "feasibility_evidence_sha256": BASE.digest(feasibility_path),
        "runtime_selection_receipts": runtime_receipts, "feasibility_summary": feasibility,
        "site_count": len(site_rows), "quality_summary": summaries, "site_results": site_rows,
        "confirmation_target_series_accessed": False,
    }
    evidence["evidence_sha256"] = BASE.canonical_digest(evidence)
    evidence_path = paths["evidence"]
    decision_path = paths["decision"]
    BASE.atomic_json(evidence_path, evidence)
    BASE.atomic_json(decision_path, decision)
    receipt = {
        "schema_version": "a12r2-execution-receipt-1", "evaluation_id": manifest["evaluation_id"],
        "source_commit": source_commit, "cligen_binary_sha256": binary_hash,
        "input_hashes": input_hashes, "build_receipt_sha256": BASE.digest(build_receipt_path),
        "station_archive_sha256": BASE.digest(station_archive),
        "prism_cache_file_set_sha256": prism_identity["file_set_sha256"],
        "source_hashes": source_hashes, "authenticated_predecessors": AUTHENTICATED_PREDECESSORS,
        "outputs": {path.name: {"sha256": BASE.digest(path), "bytes": path.stat().st_size}
                    for path in (preflight_path, feasibility_path, evidence_path, decision_path)},
        "elapsed_seconds": time.perf_counter() - started,
        "confirmation_target_series_accessed": False,
    }
    BASE.atomic_json(paths["receipt"], receipt)


def hold_receipt(hold: EvaluationHold, source_commit: str, binary: Path,
                 build_receipt_path: Path, station_archive: Path) -> dict[str, Any]:
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    input_hashes = verify_inputs(manifest)
    source_hashes = verify_source(source_commit)
    binary = binary.resolve()
    verify_build_receipt(source_commit, source_hashes, binary, build_receipt_path)
    prism = BASE.verify_prism_cache(BASE.cache_root())
    prism.pop("_runtime_path")
    station_manifest = json.loads(BASE.STATION_MANIFESTS.read_text())
    registered = next(row for row in station_manifest["collections"] if row["name"] == "us-2015")
    if (BASE.digest(station_archive) != registered["archive"]["sha256"]
            or station_archive.stat().st_size != registered["archive"]["bytes"]):
        raise EvaluationError("station archive identity differs while writing HOLD receipt")
    preflight = PACKAGE / "calendar-preflight-v1.json"
    feasibility = PACKAGE / "feasibility-evidence-v1.json"
    return {
        "schema_version": "a12r2-execution-failure-receipt-1",
        "evaluation_id": "a12r2-localizability-repair-comparison-v1",
        "terminal": hold.disposition, "point_id": hold.point_id, "detail": hold.detail,
        "source_commit": source_commit, "source_hashes": source_hashes,
        "input_hashes": input_hashes, "cligen_binary_sha256": BASE.digest(binary),
        "build_receipt_sha256": BASE.digest(build_receipt_path),
        "station_archive_sha256": BASE.digest(station_archive),
        "manifest_sha256": BASE.digest(MANIFEST_PATH),
        "prism_cache_file_set_sha256": prism["file_set_sha256"],
        "calendar_preflight_sha256": BASE.digest(preflight) if preflight.is_file() else None,
        "feasibility_evidence_sha256": BASE.digest(feasibility) if feasibility.is_file() else None,
        "authenticated_predecessors": AUTHENTICATED_PREDECESSORS,
        "quality_scoring_started": False, "quality_disposition_emitted": False,
        "confirmation_target_series_accessed": False,
    }


def execute(source_commit: str, binary: Path, build_receipt_path: Path,
            station_archive: Path) -> None:
    first = execution_paths(False)
    failure_path = PACKAGE / "execution-failure-receipt-v1.json"
    existence = {name: path.exists() for name, path in first.items()}
    if failure_path.exists():
        raise EvaluationError("a terminal A12R2 HOLD already exists")
    if not any(existence.values()):
        with tempfile.TemporaryDirectory(prefix="a12r2-publish-") as temporary:
            staging_root = Path(temporary)
            staged = execution_paths(False, staging_root)
            try:
                execute_science(source_commit, binary, build_receipt_path, station_archive,
                                False, staging_root)
            except EvaluationHold as hold:
                for name in ("preflight", "feasibility"):
                    if staged[name].is_file():
                        shutil.copy2(staged[name], first[name])
                BASE.atomic_json(failure_path, hold_receipt(
                    hold, source_commit, binary, build_receipt_path, station_archive
                ))
                raise
            for name, staged_path in staged.items():
                shutil.copy2(staged_path, first[name])
        return
    if not all(existence.values()):
        raise EvaluationError("partial existing A12R2 terminal artifact set")
    replay = execution_paths(True)
    if any(path.exists() for path in replay.values()) or (PACKAGE / "replay-receipt-v1.json").exists():
        raise EvaluationError("A12R2 replay artifacts already exist")
    with tempfile.TemporaryDirectory(prefix="a12r2-replay-") as temporary:
        staging_root = Path(temporary)
        staged = execution_paths(True, staging_root)
        execute_science(source_commit, binary, build_receipt_path, station_archive, True,
                        staging_root)
        comparisons = {}
        for name in ("preflight", "feasibility", "evidence", "decision"):
            first_hash, replay_hash = BASE.digest(first[name]), BASE.digest(staged[name])
            comparisons[name] = {"first_sha256": first_hash, "replay_sha256": replay_hash,
                                 "identical": first_hash == replay_hash}
        if not all(row["identical"] for row in comparisons.values()):
            raise EvaluationError("scientific replay differs from preserved first execution")
        for name, staged_path in staged.items():
            shutil.copy2(staged_path, replay[name])
    BASE.atomic_json(PACKAGE / "replay-receipt-v1.json", {
        "schema_version": "a12r2-replay-receipt-1", "source_commit": source_commit,
        "comparisons": comparisons, "scientific_replay_identical": True,
        "first_execution_receipt_sha256": BASE.digest(first["receipt"]),
        "replay_execution_receipt_sha256": BASE.digest(replay["receipt"]),
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-manifest", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--cligen-binary", type=Path)
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--station-archive", type=Path)
    arguments = parser.parse_args()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if arguments.validate_manifest:
        verify_inputs(manifest)
        print(BASE.canonical_digest(manifest))
        return
    if arguments.build and arguments.source_commit:
        build_release(arguments.source_commit)
        return
    if (arguments.execute and arguments.source_commit and arguments.cligen_binary
            and arguments.build_receipt and arguments.station_archive):
        execute(arguments.source_commit, arguments.cligen_binary, arguments.build_receipt,
                arguments.station_archive)
        return
    parser.error("select one complete operation")


if __name__ == "__main__":
    main()
