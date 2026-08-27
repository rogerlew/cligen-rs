#!/usr/bin/env python3
"""Replay A11E5 and retain directional dispersion/dependence diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
MANIFEST_PATH = PACKAGE / "analysis-manifest-v1.json"
SCHEMA_PATH = PACKAGE / "analysis-manifest-v1.schema.json"
SPEC_PATH = ROOT / "docs/specifications/SPEC-A11-DIRECTIONAL-ERROR-ATTRIBUTION.md"
PACKAGE_PATH = PACKAGE.parent / "package.md"
A11E5 = ROOT / "docs/work-packages/20260827-a11e5-interannual-family-stability/artifacts"
A11E5_EXECUTOR = A11E5 / "execute.py"
A11E5_MANIFEST = A11E5 / "execution-manifest-v1.json"
A11E5_EVIDENCE = A11E5 / "development-evidence-v1.json"
A11E5_DECISION = A11E5 / "development-decision-v1.json"
A11E5_RECEIPT = A11E5 / "execution-receipt-v1.json"
MEMBERS = tuple(range(8))
CONTROL = "gaussian_latent_ar1_physical_core_v1"
TREATMENT = "circular_fixed_block_physical_core_v1"


class AnalysisError(RuntimeError):
    """The A11E5D diagnostic contract was violated."""


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise AnalysisError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    partial.replace(path)


def git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if result.returncode:
        raise AnalysisError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def validate_manifest(value: Any) -> dict[str, Any]:
    expected = {
        "schema_version": 1,
        "analysis_id": "a11e5d-directional-error-attribution-v1",
        "member_ids": list(MEMBERS),
        "station_count": 20,
        "arms": [CONTROL, TREATMENT],
        "directional_metric_set_id": "a11e5d-signed-dispersion-dependence-v1",
        "material_ratio": 0.05,
        "confirmation_target_access": False,
        "runtime": {"python": "3.12.13", "numpy": "2.3.5"},
        "resource_bound": {"maximum_streams_per_execution": 320, "replays": 1},
        "a11e5": {
            "closure_commit": "067259220ceb0261daddf1e06ca42347278b04e5",
            "executor_sha256": "9bf3cab2752bc84235886deabe2f8b759de2cc320259999c5ccaccce15751ffc",
            "execution_manifest_sha256": "1d9373d77d4ae142d50f0b5ecd6452bc98c93dd31d74769efc2d4c3eb642cd8e",
            "development_evidence_sha256": "b85fc59a9925557565ba26163e165f834f6bd8d272122baebbb71b0da9673f47",
            "development_decision_sha256": "0d808f9ccc5cf5e9317ea328d1e480aff38861f2d30412ca4c1b1659cda5056d",
            "execution_receipt_sha256": "ab0337455b1082f222c5390b05f33c12a8327d2d061ead07b792d9f174224e44",
        },
    }
    if value != expected:
        raise AnalysisError("analysis manifest differs from frozen contract")
    return value


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if source_commit != git("rev-parse", "origin/main").decode().strip():
        raise AnalysisError("analysis source is not exact origin/main")
    required = (Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_analyze.py", SPEC_PATH, PACKAGE_PATH)
    source_hashes = {}
    for path in required:
        relative = path.relative_to(ROOT).as_posix()
        blob = git("show", f"{source_commit}:{relative}")
        if blob != path.read_bytes():
            raise AnalysisError(f"working source differs from published commit: {relative}")
        source_hashes[relative] = hashlib.sha256(blob).hexdigest()
    dependencies = (
        (A11E5_EXECUTOR, "executor_sha256"),
        (A11E5_MANIFEST, "execution_manifest_sha256"),
        (A11E5_EVIDENCE, "development_evidence_sha256"),
        (A11E5_DECISION, "development_decision_sha256"),
        (A11E5_RECEIPT, "execution_receipt_sha256"),
    )
    closure = manifest["a11e5"]
    for path, key in dependencies:
        expected = closure[key]
        relative = path.relative_to(ROOT).as_posix()
        if digest(path) != expected or hashlib.sha256(git("show", f"{closure['closure_commit']}:{relative}")).hexdigest() != expected:
            raise AnalysisError(f"closed A11E5 dependency drifted: {path.name}")
    return {"source_commit": source_commit, "published_ref": "origin/main", "source_hashes": source_hashes}


def variance_record(generated: np.ndarray, observed: np.ndarray) -> dict[str, float]:
    generated_variance = float(np.var(generated, ddof=1))
    observed_variance = float(np.var(observed, ddof=1))
    signed = math.log(max(generated_variance, 1e-12) / max(observed_variance, 1e-12))
    return {
        "generated_variance": generated_variance,
        "observed_variance": observed_variance,
        "signed_log_variance_ratio": signed,
        "absolute_log_variance_ratio": abs(signed),
    }


def directional_metrics(
    generated_precipitation: np.ndarray,
    generated_temperature: np.ndarray,
    observed_precipitation: np.ndarray,
    observed_temperature: np.ndarray,
    annual_weights: np.ndarray,
    inherited: Any,
) -> dict[str, Any]:
    gp = np.sum(generated_precipitation, axis=1)
    op = np.sum(observed_precipitation, axis=1)
    gt = generated_temperature @ annual_weights
    ot = observed_temperature @ annual_weights
    monthly = {}
    for name, generated, observed in (
        ("precipitation", generated_precipitation, observed_precipitation),
        ("temperature", generated_temperature, observed_temperature),
    ):
        monthly[name] = [
            {"month": month + 1, **variance_record(generated[:, month], observed[:, month])}
            for month in range(12)
        ]
    annual = {
        "precipitation": variance_record(gp, op),
        "temperature": variance_record(gt, ot),
    }
    lag_one = {}
    low_frequency = {}
    for name, generated, observed in (("precipitation", gp, op), ("temperature", gt, ot)):
        generated_correlation = inherited.safe_corr(generated[:-1], generated[1:])
        observed_correlation = inherited.safe_corr(observed[:-1], observed[1:])
        lag_one[name] = {
            "generated_correlation": generated_correlation,
            "observed_correlation": observed_correlation,
            "signed_residual": generated_correlation - observed_correlation,
        }
        generated_fraction = inherited.low_frequency_fraction(generated)
        observed_fraction = inherited.low_frequency_fraction(observed)
        low_frequency[name] = {
            "generated_power_fraction": generated_fraction,
            "observed_power_fraction": observed_fraction,
            "signed_residual": generated_fraction - observed_fraction,
        }
    value = {"monthly_variance": monthly, "annual_variance": annual, "annual_lag_one": lag_one, "annual_low_frequency": low_frequency}
    def finite(item: Any) -> bool:
        if isinstance(item, dict):
            return all(finite(member) for member in item.values())
        if isinstance(item, list):
            return all(finite(member) for member in item)
        return not isinstance(item, float) or math.isfinite(item)
    if not finite(value):
        raise AnalysisError("directional metric is nonfinite")
    return value


def signed_summary(entries: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    if not entries:
        raise AnalysisError("cannot summarize empty directional evidence")
    values = np.asarray([entry["signed_log_variance_ratio"] for entry in entries])
    mean = float(np.mean(values))
    mean_absolute = float(np.mean(np.abs(values)))
    boundary = math.log1p(threshold)
    def extreme(entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "station_id": entry["station_id"], "member_id": entry["member_id"],
            "month": entry.get("month"),
            "signed_log_variance_ratio": entry["signed_log_variance_ratio"],
            "variance_ratio": math.exp(entry["signed_log_variance_ratio"]),
            "generated_variance": entry["generated_variance"],
            "observed_variance": entry["observed_variance"],
        }
    return {
        "count": len(entries),
        "mean_signed_log_variance_ratio": mean,
        "median_signed_log_variance_ratio": float(np.median(values)),
        "geometric_mean_variance_ratio": math.exp(mean),
        "median_variance_ratio": math.exp(float(np.median(values))),
        "mean_absolute_log_variance_ratio": mean_absolute,
        "bias_fraction_abs_mean_over_mean_absolute": abs(mean) / mean_absolute if mean_absolute else 0.0,
        "counts": {
            "overdispersed_more_than_5pct": int(np.sum(values > boundary)),
            "within_5pct": int(np.sum(np.abs(values) <= boundary)),
            "underdispersed_more_than_5pct": int(np.sum(values < -boundary)),
        },
        "most_overdispersed": extreme(max(entries, key=lambda entry: entry["signed_log_variance_ratio"])),
        "most_underdispersed": extreme(min(entries, key=lambda entry: entry["signed_log_variance_ratio"])),
    }


def comparison_summary(control: list[dict[str, Any]], treatment: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    if len(control) != len(treatment):
        raise AnalysisError("control and treatment directional rows differ")
    entries = []
    for left, right in zip(control, treatment):
        key_left = (left["station_id"], left["member_id"], left.get("month"))
        key_right = (right["station_id"], right["member_id"], right.get("month"))
        if key_left != key_right:
            raise AnalysisError("directional comparison keys differ")
        signed = right["signed_log_variance_ratio"] - left["signed_log_variance_ratio"]
        entries.append({
            "station_id": right["station_id"], "member_id": right["member_id"],
            "month": right.get("month"), "signed_log_variance_ratio": signed,
            "generated_variance": right["generated_variance"], "observed_variance": left["generated_variance"],
        })
    summary = signed_summary(entries, threshold)
    summary["semantics"] = "positive means circular-block generated variance exceeds Gaussian generated variance"
    return summary


def collect_variance_entries(rows: list[dict[str, Any]], arm: str, scale: str, variable: str) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if scale == "annual":
            records = [row[arm]["annual_variance"][variable]]
        else:
            records = row[arm]["monthly_variance"][variable]
        for record in records:
            output.append({"station_id": row["station_id"], "member_id": row["member_id"], **record})
    return output


def residual_summary(rows: list[dict[str, Any]], surface: str, variable: str) -> dict[str, Any]:
    result = {}
    for arm in ("control", "treatment"):
        values = np.asarray([row[arm][surface][variable]["signed_residual"] for row in rows])
        result[arm] = {
            "mean_signed_residual": float(np.mean(values)),
            "median_signed_residual": float(np.median(values)),
            "mean_absolute_residual": float(np.mean(np.abs(values))),
            "positive_count": int(np.sum(values > 0.0)),
            "negative_count": int(np.sum(values < 0.0)),
        }
    return result


def build_summary(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    if len(rows) != 160:
        raise AnalysisError("summary requires 160 paired rows")
    dispersion = {}
    for scale in ("annual", "monthly"):
        for variable in ("precipitation", "temperature"):
            key = f"{scale}_{variable}_variance"
            control = collect_variance_entries(rows, "control", scale, variable)
            treatment = collect_variance_entries(rows, "treatment", scale, variable)
            dispersion[key] = {
                "gaussian_vs_observed": signed_summary(control, threshold),
                "circular_block_vs_observed": signed_summary(treatment, threshold),
                "circular_block_vs_gaussian": comparison_summary(control, treatment, threshold),
            }
    dependence = {}
    for surface in ("annual_lag_one", "annual_low_frequency"):
        dependence[surface] = {
            variable: residual_summary(rows, surface, variable) for variable in ("precipitation", "temperature")
        }
    return {"dispersion": dispersion, "dependence": dependence}


def execute(source_commit: str) -> None:
    started = time.monotonic()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    runtime = {"python": platform.python_version(), "numpy": np.__version__}
    if runtime != manifest["runtime"]:
        raise AnalysisError("scientific runtime differs")
    source = verify_source(source_commit, manifest)
    inherited = load_module("a11e5_execution_for_directional_replay", A11E5_EXECUTOR)
    predecessor = inherited.load_module("a11e2_execution_for_directional_replay", inherited.A11E2_EXECUTOR)
    predecessor_manifest = predecessor.validate_manifest(json.loads(inherited.A11E2_MANIFEST.read_text()))
    input_hashes, development_rows, _baseline = predecessor.verify_inputs(predecessor_manifest)
    base = predecessor.ensure_base_loaded()
    fit_summaries, fit_preflight = base.load_fit_corpus()
    development, development_preflight = base.load_development(development_rows)
    selection = predecessor.build_selection(
        json.loads(predecessor.PANEL.read_text()), json.loads(predecessor.COHORT_SELECTION.read_text()), development_rows
    )
    if selection != json.loads(inherited.A11E2_SELECTION.read_text()):
        raise AnalysisError("nearest selector mapping does not replay")
    candidate = [row for row in fit_summaries if row["role"] == "candidate_fit"]
    candidate_by_point = {row["point_id"]: row for row in candidate}
    adapters = base.adapter_parameters(candidate)
    models, fit_receipt = base.fit_regions(candidate, adapters)
    by_station = {row["station_id"]: row for row in selection["rows"]}
    nearest_locations = {}
    for observed in development:
        selected = by_station[observed["point_id"]]["candidate_point_id"]
        nearest_locations[observed["point_id"]] = predecessor.candidate_location(
            candidate_by_point[selected], observed["regime"], adapters
        )
    preflight = {
        "schema_version": "a11e5d-replay-preflight-1",
        "valid": True,
        "source_transform": "daymet_official_365_v1",
        "normalized_statistic": "daymet_mask_normalized_month_v1",
        "fit": fit_preflight,
        "development": development_preflight,
        "fit_sha256": fit_receipt["fit_sha256"],
        "nearest_locations_sha256": inherited.canonical_digest({key: value.tolist() for key, value in sorted(nearest_locations.items())}),
        "closed_a11e5_evidence_sha256": digest(A11E5_EVIDENCE),
        "confirmation_target_series_accessed": False,
    }
    atomic_json(PACKAGE / "replay-preflight-v1.json", preflight)

    closed_rows = {
        (row["station_id"], row["member_id"]): row
        for row in json.loads(A11E5_EVIDENCE.read_text())["rows"]
    }
    captured: dict[str, Any] | None = None
    original_metrics = inherited.interannual_metrics

    def capture_metrics(gp: np.ndarray, gt: np.ndarray, op: np.ndarray, ot: np.ndarray, weights: np.ndarray) -> dict[str, float]:
        nonlocal captured
        captured = directional_metrics(gp, gt, op, ot, weights, inherited)
        return original_metrics(gp, gt, op, ot, weights)

    inherited.interannual_metrics = capture_metrics
    rows = []
    try:
        for site_ordinal, observed in enumerate(development):
            point = observed["point_id"]
            regime = observed["regime"]
            closed = None
            for member_id in MEMBERS:
                closed = closed_rows[(point, member_id)]
                arms = {}
                for arm_name, strategy in (("control", CONTROL), ("treatment", TREATMENT)):
                    captured = None
                    generated = inherited.generate_arm(
                        observed, strategy, models[f"{regime}/{strategy}"], adapters[regime],
                        nearest_locations[point], site_ordinal, member_id, base,
                    )
                    if captured is None:
                        raise AnalysisError("directional capture did not execute")
                    expected_metrics = closed[f"{arm_name}_metrics"]
                    expected_stream = closed[f"{arm_name}_stream_summary_sha256"]
                    if generated["metrics"] != expected_metrics or generated["stream_summary_sha256"] != expected_stream:
                        raise AnalysisError(f"closed A11E5 replay differs: {point}/{member_id}/{arm_name}")
                    if generated["daily_invariant_failures"]:
                        raise AnalysisError(f"daily invariant failure: {point}/{member_id}/{arm_name}")
                    arms[arm_name] = captured
                rows.append({
                    "station_id": point, "station_regime": regime, "member_id": member_id,
                    "candidate_point_id": closed["candidate_point_id"], **arms,
                })
    finally:
        inherited.interannual_metrics = original_metrics
    if len(rows) * 2 != manifest["resource_bound"]["maximum_streams_per_execution"]:
        raise AnalysisError("replay stream count differs")
    summary = build_summary(rows, manifest["material_ratio"])
    evidence = {
        "schema_version": "a11e5d-directional-evidence-1",
        "analysis_id": manifest["analysis_id"],
        "source_commit": source_commit,
        "paired_rows": len(rows), "stream_count": len(rows) * 2,
        "exact_closed_a11e5_replay": True,
        "rows": rows, "summary": summary,
        "limitations": [
            "directional summaries remain 16-year development diagnostics",
            "signed bias does not establish a causal mechanism",
            "the package diagnoses but does not construct or authorize a hybrid",
        ],
        "confirmation_target_series_accessed": False,
    }
    evidence["evidence_sha256"] = canonical_digest(evidence)
    atomic_json(PACKAGE / "directional-evidence-v1.json", evidence)
    decision = {
        "schema_version": "a11e5d-directional-decision-1",
        "analysis_id": manifest["analysis_id"],
        "terminal": "EXECUTED-COMPLETE",
        "science_status": "DIRECTIONAL_ERROR_ATTRIBUTED",
        "summary": summary,
        "a11e5_disposition_unchanged": "NOT_VIABLE_ON_FROZEN_CRITERION",
        "hybrid_authorized": False, "confirmation_authorized": False, "production_authorized": False,
    }
    atomic_json(PACKAGE / "directional-decision-v1.json", decision)
    outputs = [PACKAGE / name for name in ("replay-preflight-v1.json", "directional-evidence-v1.json", "directional-decision-v1.json")]
    receipt = {
        "schema_version": "a11e5d-execution-receipt-1",
        "analysis_id": manifest["analysis_id"], **source,
        "runtime": runtime, "inherited_input_hashes": input_hashes,
        "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in outputs},
        "paired_rows": len(rows), "stream_count": len(rows) * 2,
        "elapsed_seconds": time.monotonic() - started,
        "confirmation_target_series_accessed": False,
    }
    atomic_json(PACKAGE / "execution-receipt-v1.json", receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit")
    parser.add_argument("--validate-manifest", action="store_true")
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if arguments.validate_manifest:
        print(canonical_digest(manifest))
        return
    if not arguments.execute or not arguments.source_commit:
        parser.error("--execute requires --source-commit")
    execute(arguments.source_commit)


if __name__ == "__main__":
    main()
