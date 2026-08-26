#!/usr/bin/env python3
"""Execute the source-bound A11E2 nearest candidate-fit forcing test."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
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
SPEC_PATH = ROOT / "docs/specifications/SPEC-A11-NEAREST-CANDIDATE-FORCING.md"
PREDECESSOR = ROOT / "docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts"
BASE_EXECUTOR = PREDECESSOR / "execute.py"
BASE_MANIFEST = PREDECESSOR / "execution-manifest-v1.json"
BASE_EVIDENCE = PREDECESSOR / "development-evidence-v1.json"
BASE_DECISION = PREDECESSOR / "development-decision-v1.json"
STRATEGY_PACKAGE = ROOT / "docs/work-packages/20260825-a11e-exploratory-strategy-lab/artifacts"
STRATEGY_LAB = STRATEGY_PACKAGE / "strategy_lab.py"
STRATEGY_MANIFEST = STRATEGY_PACKAGE / "strategy-manifest-v1.json"
PANEL = ROOT / "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json"
COHORT_SELECTION = ROOT / "docs/work-packages/20260721-a10m5r15r1-prism-eligible-cohort/artifacts/cohort-selection.json"
NORMALIZED_MANIFEST = ROOT / "docs/work-packages/20260721-a10m5r15r1-prism-eligible-cohort/artifacts/normalized-manifest-v1.json"
SHARD_MANIFEST = ROOT / "docs/work-packages/20260721-a10m5r15r1-prism-eligible-cohort/artifacts/daymet-shard-manifest-v1.json"
DEVELOPMENT_MANIFEST = ROOT / "docs/work-packages/20260715-a9c-observed-development/artifacts/observed-source-manifest-v1.json"
NEW_STRATEGY = "circular_fixed_block_nearest_candidate_forcing_v1"
REFERENCE_STRATEGY = "circular_fixed_block_physical_core_v1"
ANNUAL_STRATEGY = "circular_fixed_block_bootstrap_v1"
PRIMARY_METRICS = (
    "monthly_equivalent_precipitation_mean_relative_absolute_error",
    "monthly_temperature_mean_absolute_error_c",
)
EXPECTED_INPUTS = {
    "a11e1_decision_sha256": "b72ea78d5b4f2b446915aa64f263608091da76202d6dcc24f65dfcb1bfaf3398",
    "a11e1_evidence_sha256": "961e0bd524566535159a85a30fdaa17bb6b7fccaab763915ddcaa9197e2ea746",
    "a11e1_execution_manifest_sha256": "609ea61f40219f16c409f668763b77c8ed139cf2b78b9bf5f272396207b38fc3",
    "a11e1_executor_sha256": "8a41acf4521abb53a49c7a295a30643084e32650632dfe8f84178c55fd722dd7",
    "a11e1_source_commit": "105c29b0efa3feccd27db37914bcaa60693cd828",
    "cohort_selection_sha256": "af20d8b44cbbffced284b7f9a1105335567ae9cf924e897d54fa9bd8d4f39c5b",
    "development_manifest_sha256": "8c8e4c2dbcb70f40c0f4d0a6cfd3dd12f0fc1cbb6f0b47bc36653bc2c44fa46b",
    "normalized_manifest_sha256": "32edc2bf5dd14f5e7c7c47b5354f8d95dd4f601ea14f92fae734694177724f40",
    "shard_manifest_sha256": "552a88870014e5f50f1ad0acf17aa72495509b5ddc3f30461b7a744b0de6e7d9",
}


class ExecutionError(RuntimeError):
    """The prospective A11E2 execution contract was violated."""


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ExecutionError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


base: Any | None = None


def ensure_base_loaded() -> Any:
    global base
    if base is None:
        base = load_module("a11e1_execution", BASE_EXECUTOR)
    return base


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    partial.replace(path)


def validate_manifest(value: Any) -> dict[str, Any]:
    expected_fields = {
        "bootstrap", "confirmation_target_access", "execution_id", "forcing_selector",
        "hypothesis", "inputs", "inherited_contract", "schema_version", "strategy_id",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise ExecutionError("execution manifest fields differ")
    constants = {
        "bootstrap": {"replicates": 1000, "seed": 410543},
        "confirmation_target_access": False,
        "execution_id": "a11e2-nearest-candidate-forcing-v1",
        "forcing_selector": {
            "candidate_role": "candidate_fit", "distance": "haversine_mean_earth_radius_6371.0088_km",
            "panel_sha256": "1c60bed0dc1fe955c8ad0d72cb10d63f9753684ff1c5dcff370459980ad22e7d",
            "selection_id": "a11e2-nearest-candidate-coordinate-v1", "tie_break": "distance_then_point_id_utf8",
            "uses_candidate_regime": False,
        },
        "hypothesis": {
            "comparator_strategy_id": REFERENCE_STRATEGY, "primary_metrics": list(PRIMARY_METRICS),
            "rule": "both_across_site_medians_strictly_lower_and_zero_invariants",
        },
        "inherited_contract": {
            "adapter_id": "a11e_two_part_physical_core_36_v1", "annual_strategy_id": ANNUAL_STRATEGY,
            "block_length_years": 5, "calendar_estimator": "daymet_mask_normalized_month_v1",
            "evaluator_id": "a11e_mask_normalized_observed_diagnostics_v1",
            "metric_set_id": "a11e_mask_normalized_observed_metrics_v1",
            "rng_reference_strategy_id": REFERENCE_STRATEGY,
        },
        "schema_version": 1,
        "strategy_id": NEW_STRATEGY,
    }
    if any(value.get(name) != expected for name, expected in constants.items()):
        raise ExecutionError("execution identity differs")
    inputs = value.get("inputs")
    if inputs != EXPECTED_INPUTS:
        raise ExecutionError("input identities differ")
    return value


def git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if result.returncode != 0:
        raise ExecutionError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def git_blob(commit: str, path: Path) -> bytes:
    return git("show", f"{commit}:{path.relative_to(ROOT).as_posix()}")


def verify_strategy_dependencies(base_manifest: dict[str, Any]) -> dict[str, str]:
    strategy = base_manifest.get("strategy_source")
    if not isinstance(strategy, dict) or set(strategy) != {"commit", "implementation_sha256", "manifest_sha256"}:
        raise ExecutionError("A11E1 strategy dependency identity differs")
    checks = {
        "strategy_lab.py": (STRATEGY_LAB, strategy["implementation_sha256"]),
        "strategy-manifest-v1.json": (STRATEGY_MANIFEST, strategy["manifest_sha256"]),
    }
    receipt = {}
    for name, (path, expected) in checks.items():
        if digest(path) != expected or digest_bytes(git_blob(strategy["commit"], path)) != expected:
            raise ExecutionError(f"strategy dependency drifted: {name}")
        receipt[name] = expected
    receipt["strategy_source_commit"] = strategy["commit"]
    return receipt


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if len(source_commit) != 40 or source_commit != git("rev-parse", "origin/main").decode().strip():
        raise ExecutionError("execution source is not the exact published origin/main commit")
    required = [Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_execute.py", SPEC_PATH]
    source_hashes = {}
    for path in required:
        working = path.read_bytes()
        if working != git_blob(source_commit, path):
            raise ExecutionError(f"working source differs from execution commit: {path.name}")
        source_hashes[path.name] = digest_bytes(working)
    inputs = manifest["inputs"]
    predecessor = {
        BASE_EXECUTOR: inputs["a11e1_executor_sha256"],
        BASE_MANIFEST: inputs["a11e1_execution_manifest_sha256"],
        BASE_EVIDENCE: inputs["a11e1_evidence_sha256"],
        BASE_DECISION: inputs["a11e1_decision_sha256"],
    }
    for path, expected in predecessor.items():
        if digest(path) != expected:
            raise ExecutionError(f"predecessor artifact drifted: {path.name}")
    if digest_bytes(git_blob(inputs["a11e1_source_commit"], BASE_EXECUTOR)) != inputs["a11e1_executor_sha256"]:
        raise ExecutionError("A11E1 executor source binding failed")
    if digest_bytes(git_blob(inputs["a11e1_source_commit"], BASE_MANIFEST)) != inputs["a11e1_execution_manifest_sha256"]:
        raise ExecutionError("A11E1 manifest source binding failed")
    base_manifest = json.loads(BASE_MANIFEST.read_text())
    dependencies = verify_strategy_dependencies(base_manifest)
    return {"execution_source_commit": source_commit, "published_ref": "origin/main",
            "source_hashes": source_hashes, "inherited_strategy_dependencies": dependencies}


def haversine_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    values = (latitude_a, longitude_a, latitude_b, longitude_b)
    if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in values):
        raise ExecutionError("selector coordinates must be finite numbers")
    if not -90.0 <= latitude_a <= 90.0 or not -90.0 <= latitude_b <= 90.0 or not -180.0 <= longitude_a <= 180.0 or not -180.0 <= longitude_b <= 180.0:
        raise ExecutionError("selector coordinate is outside latitude/longitude bounds")
    first, second = math.radians(latitude_a), math.radians(latitude_b)
    delta_latitude = math.radians(latitude_b - latitude_a)
    delta_longitude = math.radians(longitude_b - longitude_a)
    square = math.sin(delta_latitude / 2.0) ** 2 + math.cos(first) * math.cos(second) * math.sin(delta_longitude / 2.0) ** 2
    return 6371.0088 * 2.0 * math.asin(math.sqrt(min(max(square, 0.0), 1.0)))


def build_selection(panel: dict[str, Any], cohort: dict[str, Any], development_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if panel.get("schema_version") != 1 or panel.get("daily_data_accessed") is not False or panel.get("selected_station_count") != 20:
        raise ExecutionError("panel identity differs")
    stations = panel.get("stations")
    candidates = [row for row in cohort.get("locations", []) if row.get("role") == "candidate_fit"]
    if not isinstance(stations, list) or len(stations) != 20 or len(candidates) != 1200:
        raise ExecutionError("selector roster differs")
    station_by_id = {row.get("station_id"): row for row in stations}
    if len(station_by_id) != 20:
        raise ExecutionError("panel station IDs are not unique")
    candidate_ids = [row.get("point_id") for row in candidates]
    if len(set(candidate_ids)) != 1200:
        raise ExecutionError("candidate point IDs are not unique")
    rows = []
    for identity in sorted(development_rows, key=lambda row: row["station_id"]):
        station_id = identity["station_id"]
        if station_id not in station_by_id or identity.get("role") != "development":
            raise ExecutionError(f"development metadata is not selectable: {station_id}")
        station = station_by_id[station_id]
        latitude, longitude = station.get("latitude"), station.get("longitude")
        ranked = []
        for candidate in candidates:
            distance = haversine_km(latitude, longitude, candidate.get("latitude"), candidate.get("longitude"))
            ranked.append((distance, candidate["point_id"].encode(), candidate))
        distance, _encoded, selected = min(ranked)
        rows.append({
            "station_id": station_id, "station_regime": identity["stratum"],
            "station_latitude": latitude, "station_longitude": longitude,
            "candidate_point_id": selected["point_id"], "candidate_regime": selected["regime"],
            "candidate_latitude": selected["latitude"], "candidate_longitude": selected["longitude"],
            "great_circle_distance_km": distance,
        })
    if len(rows) != 20 or len({row["station_id"] for row in rows}) != 20:
        raise ExecutionError("selector did not produce 20 unique station rows")
    return {
        "schema_version": "a11e2-selection-receipt-1", "selection_id": "a11e2-nearest-candidate-coordinate-v1",
        "candidate_role": "candidate_fit", "development_role": "development",
        "distance": "WGS84-coordinate haversine with mean Earth radius 6371.0088 km",
        "tie_break": "minimum (distance_km, point_id UTF-8 byte order); candidate regime is not a selector",
        "rows": rows, "maximum_distance_km": max(row["great_circle_distance_km"] for row in rows),
        "stations_over_250_km": [row["station_id"] for row in rows if row["great_circle_distance_km"] > 250.0],
        "confirmation_target_series_accessed": False,
    }


def verify_inputs(manifest: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    inputs = manifest["inputs"]
    direct = {
        "panel": (PANEL, manifest["forcing_selector"]["panel_sha256"]),
        "cohort_selection": (COHORT_SELECTION, inputs["cohort_selection_sha256"]),
        "normalized_manifest": (NORMALIZED_MANIFEST, inputs["normalized_manifest_sha256"]),
        "shard_manifest": (SHARD_MANIFEST, inputs["shard_manifest_sha256"]),
        "development_manifest": (DEVELOPMENT_MANIFEST, inputs["development_manifest_sha256"]),
    }
    hashes = {}
    for name, (path, expected) in direct.items():
        actual = digest(path)
        if actual != expected:
            raise ExecutionError(f"input hash mismatch: {name}")
        hashes[name] = actual
    inherited = ensure_base_loaded()
    base_manifest = inherited.validate_manifest(json.loads(BASE_MANIFEST.read_text()))
    inherited_hashes, development_rows = inherited.verify_inputs(base_manifest)
    hashes["inherited"] = inherited_hashes
    baseline = json.loads(BASE_EVIDENCE.read_text())
    reference_rows = [row for row in baseline.get("rows", []) if row.get("strategy_id") == REFERENCE_STRATEGY]
    keys = {(row.get("point_id"), row.get("member_id")) for row in reference_rows}
    if baseline.get("source_commit") != inputs["a11e1_source_commit"] or len(reference_rows) != 20 or len(keys) != 20:
        raise ExecutionError("A11E1 comparator evidence identity differs")
    if any(row.get("metrics", {}).get("daily_invariant_failures") != 0 for row in reference_rows):
        raise ExecutionError("A11E1 comparator contains invariant failure")
    return hashes, development_rows, {row["point_id"]: row for row in reference_rows}


def candidate_location(candidate: dict[str, Any], target_regime: str, adapters: dict[str, dict[str, Any]]) -> np.ndarray:
    adjusted = dict(candidate)
    adjusted["regime"] = target_regime
    location = np.mean(ensure_base_loaded().state_matrix(adjusted, adapters), axis=0)
    if location.shape != (36,) or not np.isfinite(location).all():
        raise ExecutionError("selected candidate forcing location is invalid")
    return location


def common_rng_contract(point_id: str, site_ordinal: int) -> dict[str, Any]:
    if not isinstance(point_id, str) or not point_id or not isinstance(site_ordinal, int) or isinstance(site_ordinal, bool) or site_ordinal < 0:
        raise ExecutionError("common RNG identity is invalid")
    return {
        "annual": {"experiment_id": f"a11e1-development-{point_id}", "strategy_id": ANNUAL_STRATEGY,
                   "member_id": 0, "domain": "annual_target"},
        "hurdle": {"key_strategy_id": REFERENCE_STRATEGY, "member_id": 0, "domain": "month_hurdle",
                   "blake2b_key": f"a11e1-integrated-v1\0{point_id}\0{REFERENCE_STRATEGY}\0{0}\0month_hurdle"},
        "daily": {"experiment_id": f"a11e1-core-{point_id}", "strategy_id": ANNUAL_STRATEGY,
                  "member_id_formula": f"{site_ordinal}*192 + year_index*12 + month_index",
                  "domains": ["wet_count", "occurrence", "amount", "temperature", "range"]},
    }


def evaluate_with_location(observed: dict[str, Any], inherited_adapter: dict[str, Any], location: np.ndarray,
                           model: dict[str, Any], site_ordinal: int, inherited: Any) -> dict[str, Any]:
    adapter = dict(inherited_adapter)
    adapter["location"] = location
    if set(adapter) != set(inherited_adapter) or any(adapter[name] is not inherited_adapter[name] for name in inherited_adapter if name != "location"):
        raise ExecutionError("forcing wrapper changed an inherited adapter surface")
    generated = inherited.evaluate_site(observed, REFERENCE_STRATEGY, model, adapter, site_ordinal)
    if generated.get("strategy_id") != REFERENCE_STRATEGY:
        raise ExecutionError("inherited evaluator RNG reference identity differs")
    return generated


def paired_bootstrap(differences: dict[str, float], manifest: dict[str, Any]) -> dict[str, Any]:
    points = sorted(differences)
    if len(points) != 20:
        raise ExecutionError("paired bootstrap requires 20 stations")
    values = np.asarray([differences[point] for point in points], dtype=np.float64)
    generator = np.random.Generator(np.random.Philox(manifest["bootstrap"]["seed"]))
    samples = np.empty(manifest["bootstrap"]["replicates"], dtype=np.float64)
    for index in range(len(samples)):
        samples[index] = float(np.mean(values[generator.integers(0, len(values), len(values))]))
    return {
        "contrast": "nearest-candidate minus A11E1 region-median composite; lower is better",
        "site_differences": dict(zip(points, values.tolist())), "mean_difference": float(np.mean(values)),
        "bootstrap_quantiles_05_50_95": np.quantile(samples, [0.05, 0.5, 0.95]).tolist(),
        "replicates": len(samples), "seed": manifest["bootstrap"]["seed"],
        "rng": "numpy_philox/a11e2_paired_site_bootstrap_v1", "interpretation": "descriptive only",
    }


def evaluate_hypothesis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != 20:
        raise ExecutionError("hypothesis evaluation requires 20 station rows")
    metrics = {}
    for metric in PRIMARY_METRICS:
        baseline = float(np.median([row["baseline_metrics"][metric] for row in rows]))
        candidate = float(np.median([row["candidate_metrics"][metric] for row in rows]))
        metrics[metric] = {"baseline_median": baseline, "candidate_median": candidate,
                           "improvement_baseline_minus_candidate": baseline - candidate,
                           "strictly_lower": candidate < baseline}
    maximum_failures = max(row["candidate_metrics"]["daily_invariant_failures"] for row in rows)
    if maximum_failures != 0:
        raise ExecutionError("hypothesis evidence contains a daily invariant failure")
    supported = all(value["strictly_lower"] for value in metrics.values())
    return {"primary_metrics": metrics, "maximum_daily_invariant_failures": maximum_failures,
            "hypothesis_supported": supported,
            "disposition": "SUPPORTED_FOR_EXPLORATION" if supported else "NOT_SUPPORTED"}


def execute(source_commit: str) -> None:
    started = time.monotonic()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    source_receipt = verify_source(source_commit, manifest)
    input_hashes, development_rows, baseline_by_point = verify_inputs(manifest)
    panel = json.loads(PANEL.read_text())
    cohort = json.loads(COHORT_SELECTION.read_text())
    selection = build_selection(panel, cohort, development_rows)
    atomic_json(PACKAGE / "selection-receipt-v1.json", selection)

    inherited = ensure_base_loaded()
    fit_summaries, fit_preflight = inherited.load_fit_corpus()
    development, development_preflight = inherited.load_development(development_rows)
    calendar_receipt = {
        "schema_version": "a11e2-calendar-preflight-1", "valid": True,
        "source_transform": "daymet_official_365_v1",
        "normalized_statistic": "inherited daymet_mask_normalized_month_v1",
        "fit": fit_preflight, "development": development_preflight,
        "confirmation_target_series_accessed": False,
    }
    atomic_json(PACKAGE / "calendar-preflight-v1.json", calendar_receipt)

    candidate = [row for row in fit_summaries if row["role"] == "candidate_fit"]
    candidate_by_point = {row["point_id"]: row for row in candidate}
    adapters = inherited.adapter_parameters(candidate)
    models, inherited_fit = inherited.fit_regions(candidate, adapters)
    selection_by_station = {row["station_id"]: row for row in selection["rows"]}
    location_receipts = {}
    for observed in development:
        selected = selection_by_station[observed["point_id"]]
        point = selected["candidate_point_id"]
        if point not in candidate_by_point:
            raise ExecutionError(f"selected candidate is absent from fit corpus: {point}")
        location = candidate_location(candidate_by_point[point], observed["regime"], adapters)
        location_receipts[observed["point_id"]] = {"candidate_point_id": point, "location": location}
    fit_receipt = {
        "schema_version": "a11e2-fit-summary-1", "candidate_fit_only": True,
        "annual_strategy_id": ANNUAL_STRATEGY,
        "inherited_fit_sha256": inherited_fit["fit_sha256"],
        "station_location_sha256": canonical_digest({point: value["location"].tolist() for point, value in sorted(location_receipts.items())}),
        "stations": {point: {"candidate_point_id": value["candidate_point_id"], "location_sha256": canonical_digest(value["location"].tolist())} for point, value in sorted(location_receipts.items())},
    }
    atomic_json(PACKAGE / "fit-summary-v1.json", fit_receipt)

    evidence_rows = []
    for site_ordinal, observed in enumerate(development):
        point = observed["point_id"]
        model = models[f"{observed['regime']}/{REFERENCE_STRATEGY}"]
        generated = evaluate_with_location(observed, adapters[observed["regime"]],
                                           location_receipts[point]["location"], model,
                                           site_ordinal, inherited)
        if generated["metrics"]["daily_invariant_failures"] != 0:
            raise ExecutionError(f"daily invariant failure: {point}")
        baseline = baseline_by_point[point]
        target = generated["target_receipt"]
        evidence_rows.append({
            "station_id": point, "station_regime": observed["regime"],
            "candidate_point_id": location_receipts[point]["candidate_point_id"],
            "candidate_regime": selection_by_station[point]["candidate_regime"],
            "great_circle_distance_km": selection_by_station[point]["great_circle_distance_km"],
            "strategy_id": NEW_STRATEGY, "annual_strategy_id": ANNUAL_STRATEGY,
            "rng_reference_strategy_id": REFERENCE_STRATEGY, "member_id": 0, "years": 16,
            "common_rng_contract": common_rng_contract(point, site_ordinal),
            "baseline_metrics": baseline["metrics"], "candidate_metrics": generated["metrics"],
            "metric_differences_candidate_minus_baseline": {name: generated["metrics"][name] - baseline["metrics"][name] for name in generated["metrics"]},
            "stream_summary_sha256": generated["stream_summary_sha256"],
            "target_receipt": {"strategy_id": target["strategy_id"], "region_id": target["region_id"],
                "fit_data_role": target["fit_data_role"], "reconciliation": target["reconciliation"],
                "maximum_realized_covariance_error": target["maximum_realized_covariance_error"],
                "moment_semantics": target["moment_semantics"]},
        })
    if len(evidence_rows) != 20 or len({row["station_id"] for row in evidence_rows}) != 20:
        raise ExecutionError("development stream roster is incomplete")
    evaluation = evaluate_hypothesis(evidence_rows)
    composite_differences = {row["station_id"]: row["metric_differences_candidate_minus_baseline"]["descriptive_composite_score"] for row in evidence_rows}
    bootstrap = paired_bootstrap(composite_differences, manifest)
    evidence = {
        "schema_version": "a11e2-development-evidence-1", "execution_id": manifest["execution_id"],
        "source_commit": source_commit, "strategy_id": NEW_STRATEGY,
        "comparator_strategy_id": REFERENCE_STRATEGY, "stream_count": len(evidence_rows),
        "rows": evidence_rows, "hypothesis": evaluation, "paired_bootstrap": bootstrap,
        "limitations": ["one common-random-number member per station", "coordinate-only selector", "candidate geography is sparse for Maine, Montana, and Oregon", "development-only uncalibrated metrics"],
        "confirmation_target_series_accessed": False,
    }
    evidence["evidence_sha256"] = canonical_digest(evidence)
    atomic_json(PACKAGE / "development-evidence-v1.json", evidence)
    decision = {
        "schema_version": "a11e2-development-decision-1", "execution_id": manifest["execution_id"],
        "terminal": "EXECUTED-COMPLETE", "science_status": "EXPLORATORY_EVALUATED",
        "strategy_id": NEW_STRATEGY, **evaluation, "paired_bootstrap": bootstrap,
        "scope": "development only; no confirmation, selection, or promotion authority",
        "confirmation_authorized": False, "production_authorized": False,
    }
    atomic_json(PACKAGE / "development-decision-v1.json", decision)
    outputs = [PACKAGE / name for name in (
        "selection-receipt-v1.json", "calendar-preflight-v1.json", "fit-summary-v1.json",
        "development-evidence-v1.json", "development-decision-v1.json",
    )]
    receipt = {
        "schema_version": "a11e2-execution-receipt-1", "execution_id": manifest["execution_id"],
        **source_receipt, "input_hashes": input_hashes,
        "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in outputs},
        "elapsed_seconds": time.monotonic() - started, "fit_calendar_objects": len(fit_summaries),
        "candidate_fit_objects": len(candidate), "development_objects": len(development),
        "development_streams": len(evidence_rows), "confirmation_target_series_accessed": False,
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
