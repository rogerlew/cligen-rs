#!/usr/bin/env python3
"""Execute the source-bound A11E5 full interannual-family comparison."""

from __future__ import annotations

import argparse
import calendar
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
MANIFEST_PATH = PACKAGE / "execution-manifest-v1.json"
SCHEMA_PATH = PACKAGE / "execution-manifest-v1.schema.json"
SPEC_PATH = ROOT / "docs/specifications/SPEC-A11-INTERANNUAL-FAMILY-STABILITY.md"
PACKAGE_PATH = PACKAGE.parent / "package.md"
PLAN_PATH = ROOT / "docs/exec-plans/20260827-a11e5-interannual-family-stability.md"
A11E1 = ROOT / "docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts"
A11E2 = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts"
A11E1_EXECUTOR = A11E1 / "execute.py"
A11E2_EXECUTOR = A11E2 / "execute.py"
A11E2_MANIFEST = A11E2 / "execution-manifest-v1.json"
A11E2_SELECTION = A11E2 / "selection-receipt-v1.json"
CONTROL = "gaussian_latent_ar1_physical_core_v1"
TREATMENT = "circular_fixed_block_physical_core_v1"
BASE_BY_INTEGRATED = {
    CONTROL: "gaussian_latent_scalar_ar1_v1",
    TREATMENT: "circular_fixed_block_bootstrap_v1",
}
MEMBERS = tuple(range(8))
METRICS = (
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
)


class ExecutionError(RuntimeError):
    """The prospective A11E5 execution contract was violated."""


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ExecutionError(f"cannot load {path}")
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
        raise ExecutionError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def validate_manifest(value: Any) -> dict[str, Any]:
    expected = {
        "schema_version": 1,
        "execution_id": "a11e5-interannual-family-stability-v1",
        "control_strategy_id": CONTROL,
        "treatment_strategy_id": TREATMENT,
        "forcing_selector_id": "a11e2-nearest-candidate-coordinate-v1",
        "member_ids": list(MEMBERS),
        "station_count": 20,
        "years": 16,
        "material_ratio": 0.05,
        "minimum_improvement_fraction": 1.0 / 3.0,
        "metric_set_id": "a11e5-full-interannual-family-v1",
        "confirmation_target_access": False,
        "runtime": {"python": "3.12.13", "numpy": "2.3.5"},
        "resource_bound": {"maximum_streams_per_execution": 320, "replays": 1},
        "dependencies": {
            "a11e1_executor_sha256": "8a41acf4521abb53a49c7a295a30643084e32650632dfe8f84178c55fd722dd7",
            "a11e2_executor_sha256": "c047eb20f1132c73045a1aaae91878e786bd200c08c82cdc0bab988a686b252f",
            "a11e2_selection_sha256": "26e33ca30e0e64fa0dba1913f56ecaec12fbb5d1cc95aeb0a341af9ae52b31d6",
        },
    }
    if value != expected:
        raise ExecutionError("execution manifest differs from the frozen contract")
    return value


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if source_commit != git("rev-parse", "origin/main").decode().strip():
        raise ExecutionError("source commit is not exact origin/main")
    required = (Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_execute.py", SPEC_PATH, PACKAGE_PATH, PLAN_PATH)
    hashes = {}
    for path in required:
        relative = path.relative_to(ROOT).as_posix()
        blob = git("show", f"{source_commit}:{relative}")
        if blob != path.read_bytes():
            raise ExecutionError(f"working source differs from published commit: {relative}")
        hashes[relative] = hashlib.sha256(blob).hexdigest()
    dependencies = manifest["dependencies"]
    checks = (
        (A11E1_EXECUTOR, dependencies["a11e1_executor_sha256"]),
        (A11E2_EXECUTOR, dependencies["a11e2_executor_sha256"]),
        (A11E2_SELECTION, dependencies["a11e2_selection_sha256"]),
    )
    for path, expected in checks:
        if digest(path) != expected:
            raise ExecutionError(f"dependency drifted: {path}")
    return {"source_commit": source_commit, "published_ref": "origin/main", "source_hashes": hashes}


def safe_corr(left: np.ndarray, right: np.ndarray) -> float:
    if left.size != right.size or left.size < 2:
        raise ExecutionError("correlation inputs differ or are too short")
    if float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def variance_log_error(generated: np.ndarray, observed: np.ndarray) -> float:
    generated_variance = max(float(np.var(generated, ddof=1)), 1e-12)
    observed_variance = max(float(np.var(observed, ddof=1)), 1e-12)
    return abs(math.log(generated_variance / observed_variance))


def monthly_dispersion_error(generated: np.ndarray, observed: np.ndarray) -> float:
    if generated.shape != observed.shape or generated.ndim != 2 or generated.shape[1] != 12:
        raise ExecutionError("monthly dispersion arrays must have equal Nx12 shape")
    return float(np.mean([variance_log_error(generated[:, month], observed[:, month]) for month in range(12)]))


def cross_month_correlation_rmse(generated: np.ndarray, observed: np.ndarray) -> float:
    if generated.shape != observed.shape or generated.ndim != 2 or generated.shape[1] != 12:
        raise ExecutionError("cross-month arrays must have equal Nx12 shape")
    differences = []
    for left in range(12):
        for right in range(left + 1, 12):
            differences.append(safe_corr(generated[:, left], generated[:, right]) - safe_corr(observed[:, left], observed[:, right]))
    return float(np.sqrt(np.mean(np.square(differences))))


def low_frequency_fraction(values: np.ndarray) -> float:
    if values.ndim != 1 or values.size < 4:
        raise ExecutionError("low-frequency series must be one-dimensional and length >= 4")
    centered = values - np.mean(values)
    power = np.abs(np.fft.rfft(centered))[1:] ** 2
    frequencies = np.fft.rfftfreq(values.size, d=1.0)[1:]
    total = float(np.sum(power))
    if total == 0.0:
        return 0.0
    return float(np.sum(power[frequencies <= 0.25]) / total)


def interannual_metrics(
    generated_precipitation: np.ndarray,
    generated_temperature: np.ndarray,
    observed_precipitation: np.ndarray,
    observed_temperature: np.ndarray,
    annual_weights: np.ndarray,
) -> dict[str, float]:
    gp = np.sum(generated_precipitation, axis=1)
    op = np.sum(observed_precipitation, axis=1)
    gt = generated_temperature @ annual_weights
    ot = observed_temperature @ annual_weights
    metrics = {
        "monthly_precipitation_dispersion_error": monthly_dispersion_error(generated_precipitation, observed_precipitation),
        "monthly_temperature_dispersion_error": monthly_dispersion_error(generated_temperature, observed_temperature),
        "annual_precipitation_dispersion_error": variance_log_error(gp, op),
        "annual_temperature_dispersion_error": variance_log_error(gt, ot),
        "precipitation_cross_month_correlation_rmse": cross_month_correlation_rmse(generated_precipitation, observed_precipitation),
        "temperature_cross_month_correlation_rmse": cross_month_correlation_rmse(generated_temperature, observed_temperature),
        "annual_precipitation_lag1_error": abs(safe_corr(gp[:-1], gp[1:]) - safe_corr(op[:-1], op[1:])),
        "annual_temperature_lag1_error": abs(safe_corr(gt[:-1], gt[1:]) - safe_corr(ot[:-1], ot[1:])),
        "annual_precipitation_low_frequency_error": abs(low_frequency_fraction(gp) - low_frequency_fraction(op)),
        "annual_temperature_low_frequency_error": abs(low_frequency_fraction(gt) - low_frequency_fraction(ot)),
    }
    if set(metrics) != set(METRICS) or not all(math.isfinite(value) and value >= 0.0 for value in metrics.values()):
        raise ExecutionError("interannual metrics are incomplete or nonfinite")
    return metrics


def generate_arm(
    observed: dict[str, Any],
    integrated_id: str,
    model: dict[str, Any],
    adapter: dict[str, Any],
    location: np.ndarray,
    site_ordinal: int,
    member_id: int,
    inherited: Any,
) -> dict[str, Any]:
    base_id = BASE_BY_INTEGRATED[integrated_id]
    point = observed["point_id"]
    target_rng = inherited.lab.domain_rng(f"a11e1-development-{point}", base_id, member_id, "annual_target")
    states, target_receipt = inherited.lab.generate_strategy_targets(
        model, 16, target_rng, location, adapter["variances"], adapter["annual_weights"], adapter["annual_variance"]
    )
    positive_equivalent = adapter["floors"] + np.exp(states[:, :12])
    temperature = states[:, 12:24]
    daily_range = np.exp(states[:, 24:36])
    generated_equivalent = np.empty((16, 12))
    failures = 0
    previous_wet = False
    hurdle = inherited.hurdle_rng(point, integrated_id, member_id)
    texture = adapter["texture"]
    for year_index, year in enumerate(inherited.DEVELOPMENT_YEARS):
        for month in inherited.MONTHS:
            slot = month - 1
            days = calendar.monthrange(year, month)[1]
            dry = float(hurdle.random()) < float(adapter["dry_probability"][slot])
            equivalent_total = 0.0 if dry else float(positive_equivalent[year_index, slot])
            total = equivalent_total * days / inherited.EQUIVALENT_DAYS
            ordinal = member_id * 3840 + site_ordinal * 192 + year_index * 12 + slot
            streams = inherited.lab.domain_rngs(f"a11e1-core-{point}", base_id, ordinal)
            required = {name: streams[name] for name in ("wet_count", "occurrence", "amount", "temperature", "range")}
            counts = inherited.eligible_wet_counts(adapter["wet_counts"][slot], days)
            generated, receipt = inherited.lab.generate_core_month(
                base_id, total, days, counts, 1.0, previous_wet,
                float(texture["pww"][slot]), float(texture["pwd"][slot]),
                float(temperature[year_index, slot]), float(texture["temp_sd"][slot]),
                float(daily_range[year_index, slot]), float(texture["amount_phi"][slot]),
                float(texture["temp_phi"][slot]), float(texture["range_phi"][slot]), required,
            )
            previous_wet = bool(generated["wet"][-1])
            generated_equivalent[year_index, slot] = receipt["precipitation_total_mm"] * inherited.EQUIVALENT_DAYS / days
            failures += int(abs(receipt["precipitation_total_mm"] - total) > 1e-8)
            failures += int(abs(float(np.mean(generated["temperature_mean"])) - temperature[year_index, slot]) > 1e-10)
            failures += int(abs(receipt["range_mean"] - daily_range[year_index, slot]) > 1e-10)
            failures += int(np.any(generated["temperature_max"] < generated["temperature_min"]))
            failures += int((total == 0.0) != (receipt["wet_count"] == 0))
    metrics = interannual_metrics(
        generated_equivalent, temperature, observed["precipitation"], observed["tmean"], adapter["annual_weights"][12:24]
    )
    return {
        "metrics": metrics,
        "family_score": float(np.mean(list(metrics.values()))),
        "daily_invariant_failures": failures,
        "target_receipt_sha256": canonical_digest(target_receipt),
        "stream_summary_sha256": canonical_digest({"precipitation": generated_equivalent.tolist(), "temperature": temperature.tolist()}),
    }


def evaluate_decision(rows: list[dict[str, Any]], material_ratio: float, minimum_fraction: float) -> dict[str, Any]:
    if len(rows) != 160 or len({(row["station_id"], row["member_id"]) for row in rows}) != 160:
        raise ExecutionError("decision requires exact 20x8 paired rows")
    improved = []
    worse = []
    neutral = []
    for row in rows:
        control = row["control_family_score"]
        treatment = row["treatment_family_score"]
        key = f"{row['station_id']}/{row['member_id']}"
        if treatment <= (1.0 - material_ratio) * control:
            improved.append(key)
        elif treatment > (1.0 + material_ratio) * control:
            worse.append(key)
        else:
            neutral.append(key)
    family = {}
    for metric in METRICS:
        control_median = float(np.median([row["control_metrics"][metric] for row in rows]))
        treatment_median = float(np.median([row["treatment_metrics"][metric] for row in rows]))
        family[metric] = {
            "control_median": control_median,
            "treatment_median": treatment_median,
            "ratio_treatment_over_control": treatment_median / max(control_median, 1e-12),
            "aggregate_noninferior": treatment_median <= (1.0 + material_ratio) * control_median,
        }
    benefit = len(improved) / len(rows) >= minimum_fraction
    all_noninferior = all(value["aggregate_noninferior"] for value in family.values())
    if benefit and all_noninferior and not worse:
        disposition = "VIABLE_AS_UNIVERSAL_EXPLORATION"
    elif benefit and all_noninferior:
        disposition = "MIXED_REQUIRES_ROUTING"
    else:
        disposition = "NOT_VIABLE_ON_FROZEN_CRITERION"
    station_summaries = []
    for station in sorted({row["station_id"] for row in rows}):
        station_rows = [row for row in rows if row["station_id"] == station]
        station_summaries.append({
            "station_id": station,
            "materially_improved_members": sum(f"{station}/{row['member_id']}" in improved for row in station_rows),
            "neutral_members": sum(f"{station}/{row['member_id']}" in neutral for row in station_rows),
            "materially_worse_members": sum(f"{station}/{row['member_id']}" in worse for row in station_rows),
        })
    return {
        "disposition": disposition,
        "pair_counts": {"materially_improved": len(improved), "neutral": len(neutral), "materially_worse": len(worse)},
        "improvement_fraction": len(improved) / len(rows),
        "minimum_improvement_fraction_met": benefit,
        "all_metric_medians_aggregate_noninferior": all_noninferior,
        "metrics": family,
        "station_summaries": station_summaries,
    }


def execute(source_commit: str) -> None:
    started = time.monotonic()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    runtime = {"python": platform.python_version(), "numpy": np.__version__}
    if runtime != manifest["runtime"]:
        raise ExecutionError("scientific runtime differs")
    source = verify_source(source_commit, manifest)
    predecessor = load_module("a11e2_execution_for_a11e5", A11E2_EXECUTOR)
    predecessor_manifest = predecessor.validate_manifest(json.loads(A11E2_MANIFEST.read_text()))
    input_hashes, development_rows, _baseline = predecessor.verify_inputs(predecessor_manifest)
    inherited = predecessor.ensure_base_loaded()
    fit_summaries, fit_preflight = inherited.load_fit_corpus()
    development, development_preflight = inherited.load_development(development_rows)
    selection = predecessor.build_selection(
        json.loads(predecessor.PANEL.read_text()), json.loads(predecessor.COHORT_SELECTION.read_text()), development_rows
    )
    if selection != json.loads(A11E2_SELECTION.read_text()):
        raise ExecutionError("nearest selector mapping does not replay")
    preflight = {
        "schema_version": "a11e5-calendar-preflight-1",
        "valid": True,
        "source_transform": "daymet_official_365_v1",
        "normalized_statistic": "daymet_mask_normalized_month_v1",
        "fit": fit_preflight,
        "development": development_preflight,
        "confirmation_target_series_accessed": False,
    }
    atomic_json(PACKAGE / "calendar-preflight-v1.json", preflight)
    candidate = [row for row in fit_summaries if row["role"] == "candidate_fit"]
    candidate_by_point = {row["point_id"]: row for row in candidate}
    adapters = inherited.adapter_parameters(candidate)
    models, fit_receipt = inherited.fit_regions(candidate, adapters)
    by_station = {row["station_id"]: row for row in selection["rows"]}
    nearest_locations = {}
    for observed in development:
        selected = by_station[observed["point_id"]]["candidate_point_id"]
        nearest_locations[observed["point_id"]] = predecessor.candidate_location(
            candidate_by_point[selected], observed["regime"], adapters
        )
    fit_authentication = {
        "schema_version": "a11e5-fit-authentication-1",
        "candidate_fit_only": True,
        "fit_sha256": fit_receipt["fit_sha256"],
        "nearest_locations_sha256": canonical_digest({key: value.tolist() for key, value in sorted(nearest_locations.items())}),
        "selection_receipt_sha256": digest(A11E2_SELECTION),
        "confirmation_target_series_accessed": False,
    }
    atomic_json(PACKAGE / "fit-authentication-v1.json", fit_authentication)
    rows = []
    for site_ordinal, observed in enumerate(development):
        point = observed["point_id"]
        regime = observed["regime"]
        for member_id in MEMBERS:
            arms = {}
            for strategy in (CONTROL, TREATMENT):
                arms[strategy] = generate_arm(
                    observed, strategy, models[f"{regime}/{strategy}"], adapters[regime],
                    nearest_locations[point], site_ordinal, member_id, inherited,
                )
            if any(arm["daily_invariant_failures"] for arm in arms.values()):
                raise ExecutionError(f"daily invariant failure: {point}/{member_id}")
            rows.append({
                "station_id": point,
                "station_regime": regime,
                "member_id": member_id,
                "candidate_point_id": by_station[point]["candidate_point_id"],
                "control_metrics": arms[CONTROL]["metrics"],
                "treatment_metrics": arms[TREATMENT]["metrics"],
                "control_family_score": arms[CONTROL]["family_score"],
                "treatment_family_score": arms[TREATMENT]["family_score"],
                "metric_differences_treatment_minus_control": {
                    metric: arms[TREATMENT]["metrics"][metric] - arms[CONTROL]["metrics"][metric] for metric in METRICS
                },
                "control_stream_summary_sha256": arms[CONTROL]["stream_summary_sha256"],
                "treatment_stream_summary_sha256": arms[TREATMENT]["stream_summary_sha256"],
                "daily_invariant_failures": 0,
            })
    if len(rows) * 2 != manifest["resource_bound"]["maximum_streams_per_execution"]:
        raise ExecutionError("stream count differs from resource bound")
    decision_body = evaluate_decision(rows, manifest["material_ratio"], manifest["minimum_improvement_fraction"])
    evidence = {
        "schema_version": "a11e5-development-evidence-1",
        "execution_id": manifest["execution_id"],
        "source_commit": source_commit,
        "metric_set_id": manifest["metric_set_id"],
        "paired_rows": len(rows),
        "stream_count": len(rows) * 2,
        "rows": rows,
        "decision": decision_body,
        "limitations": [
            "sixteen-year streams make covariance, lag-one, and low-frequency diagnostics noisy",
            "eight paired member identifiers do not imply identical random-draw consumption across different laws",
            "development targets have been reused in the exploratory A11 campaign",
            "a mixed result does not supply or validate a prospective router",
        ],
        "confirmation_target_series_accessed": False,
    }
    evidence["evidence_sha256"] = canonical_digest(evidence)
    atomic_json(PACKAGE / "development-evidence-v1.json", evidence)
    decision = {
        "schema_version": "a11e5-development-decision-1",
        "execution_id": manifest["execution_id"],
        "terminal": "EXECUTED-COMPLETE",
        "science_status": "EXPLORATORY_INTERANNUAL_FAMILY_EVALUATED",
        **decision_body,
        "confirmation_authorized": False,
        "production_authorized": False,
    }
    atomic_json(PACKAGE / "development-decision-v1.json", decision)
    scientific = [PACKAGE / name for name in (
        "calendar-preflight-v1.json", "fit-authentication-v1.json", "development-evidence-v1.json", "development-decision-v1.json"
    )]
    receipt = {
        "schema_version": "a11e5-execution-receipt-1",
        "execution_id": manifest["execution_id"],
        **source,
        "runtime": runtime,
        "inherited_input_hashes": input_hashes,
        "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in scientific},
        "paired_rows": len(rows),
        "stream_count": len(rows) * 2,
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
