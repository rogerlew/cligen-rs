#!/usr/bin/env python3
"""Execute the source-bound A11E3 multi-member forcing stability screen."""

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
SPEC_PATH = ROOT / "docs/specifications/SPEC-A11-MULTI-MEMBER-FORCING-STABILITY.md"
PACKAGE_PATH = PACKAGE.parent / "package.md"
PLAN_PATH = ROOT / "docs/exec-plans/20260825-a11e3-multi-member-forcing-stability.md"
A11E2 = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts"
A11E1 = ROOT / "docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts"
A11E2_EXECUTOR = A11E2 / "execute.py"
A11E2_MANIFEST = A11E2 / "execution-manifest-v1.json"
A11E2_SCHEMA = A11E2 / "execution-manifest-v1.schema.json"
A11E2_SELECTION = A11E2 / "selection-receipt-v1.json"
A11E2_FIT = A11E2 / "fit-summary-v1.json"
A11E2_EVIDENCE = A11E2 / "development-evidence-v1.json"
A11E2_DECISION = A11E2 / "development-decision-v1.json"
A11E2_RECEIPT = A11E2 / "execution-receipt-v1.json"
A11E1_EXECUTOR = A11E1 / "execute.py"
A11E1_MANIFEST = A11E1 / "execution-manifest-v1.json"
A11E1_FIT = A11E1 / "fit-summary-v1.json"
A11E1_EVIDENCE = A11E1 / "development-evidence-v1.json"
A11E1_DECISION = A11E1 / "development-decision-v1.json"
A11E1_RECEIPT = A11E1 / "execution-receipt-v1.json"
STRATEGY_PACKAGE = ROOT / "docs/work-packages/20260825-a11e-exploratory-strategy-lab/artifacts"
STRATEGY_LAB = STRATEGY_PACKAGE / "strategy_lab.py"
STRATEGY_MANIFEST = STRATEGY_PACKAGE / "strategy-manifest-v1.json"
REGION_ARM = "circular_fixed_block_physical_core_v1"
NEAREST_ARM = "circular_fixed_block_nearest_candidate_forcing_v1"
ANNUAL_STRATEGY = "circular_fixed_block_bootstrap_v1"
MEMBERS = tuple(range(8))
PRIMARY_METRICS = (
    "monthly_equivalent_precipitation_mean_relative_absolute_error",
    "monthly_temperature_mean_absolute_error_c",
)
EXPECTED_INPUTS = {
    "a11e1_closure_commit": "6a60ecc7bdeab39b00a00c1a707da8278695c8ba",
    "a11e1_decision_sha256": "b72ea78d5b4f2b446915aa64f263608091da76202d6dcc24f65dfcb1bfaf3398",
    "a11e1_evidence_sha256": "961e0bd524566535159a85a30fdaa17bb6b7fccaab763915ddcaa9197e2ea746",
    "a11e1_execution_manifest_sha256": "609ea61f40219f16c409f668763b77c8ed139cf2b78b9bf5f272396207b38fc3",
    "a11e1_execution_receipt_sha256": "12d2979f5ccfe20b5b082478c1914a0d05ced666497d2c3cd0642b28e8441218",
    "a11e1_executor_sha256": "8a41acf4521abb53a49c7a295a30643084e32650632dfe8f84178c55fd722dd7",
    "a11e1_fit_summary_sha256": "134b15b1aa61868cd90b5777621c0c5df580a2145a6edc727209e6ac5fd3ce45",
    "a11e1_source_commit": "105c29b0efa3feccd27db37914bcaa60693cd828",
    "a11e2_closure_commit": "65ed7ac7c54a67014e33358c64147bc686cd9327",
    "a11e2_decision_sha256": "8ba4757b817453c4be5d7a706aa321a9786a66425a9285584d94f49c0d205dc5",
    "a11e2_evidence_sha256": "fa3ad7a9df5be6c1350567182be5802646de26aabec68b32bf2411e813c729b4",
    "a11e2_execution_manifest_sha256": "1dc78ed31f695ccb64e8072cc7c52893b4ba44271704f9b2eca4118d54f1aa6e",
    "a11e2_execution_receipt_sha256": "24c8aa6391fedb900f3376842c37c56442c91473bee54d823f1e4afc84267235",
    "a11e2_executor_sha256": "c047eb20f1132c73045a1aaae91878e786bd200c08c82cdc0bab988a686b252f",
    "a11e2_fit_summary_sha256": "94a4742869d98e31a5478706e533c4d6ae38c22113d38a1d5378dd3829985b0a",
    "a11e2_schema_sha256": "9c060127494661e71f5446a83007dee57dc5063910e22555f91d6b3e1a7f4eaf",
    "a11e2_selection_receipt_sha256": "26e33ca30e0e64fa0dba1913f56ecaec12fbb5d1cc95aeb0a341af9ae52b31d6",
    "a11e2_source_commit": "e15369ad26f4e0b646f5f4665912dd6a37e35e3a",
}


class ExecutionError(RuntimeError):
    """The prospective A11E3 execution contract was violated."""


def load_module(name: str, path: Path) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ExecutionError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


a11e2: Any | None = None


def ensure_a11e2_loaded() -> Any:
    global a11e2
    if a11e2 is None:
        a11e2 = load_module("a11e2_execution_for_a11e3", A11E2_EXECUTOR)
    return a11e2


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
    fields = {
        "arms", "confirmation_target_access", "execution_id", "hypothesis",
        "inherited_contract", "inputs", "member_ids", "resource_bound", "rng",
        "runtime", "schema_version",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ExecutionError("execution manifest fields differ")
    constants = {
        "arms": [REGION_ARM, NEAREST_ARM],
        "confirmation_target_access": False,
        "execution_id": "a11e3-multi-member-forcing-stability-v1",
        "hypothesis": {
            "estimand": "member_metric_delta_is_median_nearest_minus_median_region",
            "primary_metrics": list(PRIMARY_METRICS),
            "rule": "all_member_metric_deltas_strictly_negative_and_zero_invariants_and_exact_member0_replay",
        },
        "inherited_contract": {
            "annual_strategy_id": ANNUAL_STRATEGY,
            "block_length_years": 5,
            "calendar_estimator": "daymet_mask_normalized_month_v1",
            "daily_adapter_id": "a11e_two_part_physical_core_36_v1",
            "evaluator_id": "a11e_mask_normalized_observed_diagnostics_v1",
            "forcing_selector_id": "a11e2-nearest-candidate-coordinate-v1",
            "metric_set_id": "a11e_mask_normalized_observed_metrics_v1",
            "rng_reference_strategy_id": REGION_ARM,
        },
        "member_ids": list(MEMBERS),
        "resource_bound": {"maximum_cells_per_execution": 320, "replays": 1},
        "runtime": {"numpy": "2.3.5", "python": "3.12.13"},
        "rng": {
            "algorithm": "numpy_philox", "daily_member_stride": 3840,
            "daily_site_stride": 192,
            "domains": ["annual_target", "month_hurdle", "wet_count", "occurrence", "amount", "temperature", "range"],
        },
        "schema_version": 1,
    }
    if any(value.get(name) != expected for name, expected in constants.items()):
        raise ExecutionError("execution identity differs")
    if value.get("inputs") != EXPECTED_INPUTS:
        raise ExecutionError("input identities differ")
    return value


def verify_runtime(manifest: dict[str, Any]) -> dict[str, str]:
    actual = {"numpy": np.__version__, "python": platform.python_version()}
    if actual != manifest["runtime"]:
        raise ExecutionError("scientific runtime identity differs")
    return actual


def git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if result.returncode != 0:
        raise ExecutionError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def git_blob(commit: str, path: Path) -> bytes:
    return git("show", f"{commit}:{path.relative_to(ROOT).as_posix()}")


def verify_file_at_commit(path: Path, expected: str, commit: str) -> None:
    if digest(path) != expected or digest_bytes(git_blob(commit, path)) != expected:
        raise ExecutionError(f"dependency drifted: {path.name}")


def verify_strategy_dependencies_before_import() -> dict[str, str]:
    base_manifest = json.loads(A11E1_MANIFEST.read_text())
    strategy = base_manifest.get("strategy_source")
    if not isinstance(strategy, dict) or set(strategy) != {"commit", "implementation_sha256", "manifest_sha256"}:
        raise ExecutionError("A11E1 strategy dependency identity differs")
    checks = {
        "strategy_lab.py": (STRATEGY_LAB, strategy["implementation_sha256"]),
        "strategy-manifest-v1.json": (STRATEGY_MANIFEST, strategy["manifest_sha256"]),
    }
    receipt = {"strategy_source_commit": strategy["commit"]}
    for name, (path, expected) in checks.items():
        verify_file_at_commit(path, expected, strategy["commit"])
        receipt[name] = expected
    return receipt


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if len(source_commit) != 40 or source_commit != git("rev-parse", "origin/main").decode().strip():
        raise ExecutionError("execution source is not the exact published origin/main commit")
    required = [Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_execute.py", SPEC_PATH, PACKAGE_PATH, PLAN_PATH]
    source_hashes = {}
    for path in required:
        working = path.read_bytes()
        if working != git_blob(source_commit, path):
            raise ExecutionError(f"working source differs from execution commit: {path.name}")
        source_hashes[path.relative_to(ROOT).as_posix()] = digest_bytes(working)
    inputs = manifest["inputs"]
    for path, key in ((A11E2_EXECUTOR, "a11e2_executor_sha256"), (A11E2_MANIFEST, "a11e2_execution_manifest_sha256"), (A11E2_SCHEMA, "a11e2_schema_sha256")):
        verify_file_at_commit(path, inputs[key], inputs["a11e2_source_commit"])
    for path, key in ((A11E1_EXECUTOR, "a11e1_executor_sha256"), (A11E1_MANIFEST, "a11e1_execution_manifest_sha256")):
        verify_file_at_commit(path, inputs[key], inputs["a11e1_source_commit"])
    for path, key in ((A11E2_SELECTION, "a11e2_selection_receipt_sha256"), (A11E2_FIT, "a11e2_fit_summary_sha256"), (A11E2_EVIDENCE, "a11e2_evidence_sha256"), (A11E2_DECISION, "a11e2_decision_sha256"), (A11E2_RECEIPT, "a11e2_execution_receipt_sha256")):
        verify_file_at_commit(path, inputs[key], inputs["a11e2_closure_commit"])
    for path, key in ((A11E1_FIT, "a11e1_fit_summary_sha256"), (A11E1_EVIDENCE, "a11e1_evidence_sha256"), (A11E1_DECISION, "a11e1_decision_sha256"), (A11E1_RECEIPT, "a11e1_execution_receipt_sha256")):
        verify_file_at_commit(path, inputs[key], inputs["a11e1_closure_commit"])
    strategy_dependencies = verify_strategy_dependencies_before_import()
    return {"execution_source_commit": source_commit, "published_ref": "origin/main", "source_hashes": source_hashes,
            "inherited_strategy_dependencies": strategy_dependencies}


def daily_ordinal(member_id: int, site_ordinal: int, year_index: int, month_index: int) -> int:
    values = (member_id, site_ordinal, year_index, month_index)
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        raise ExecutionError("daily RNG ordinal coordinates must be integers")
    if member_id not in MEMBERS or not 0 <= site_ordinal < 20 or not 0 <= year_index < 16 or not 0 <= month_index < 12:
        raise ExecutionError("daily RNG ordinal coordinate is outside the frozen grid")
    return member_id * 3840 + site_ordinal * 192 + year_index * 12 + month_index


def common_rng_contract(point_id: str, member_id: int, site_ordinal: int) -> dict[str, Any]:
    if not isinstance(point_id, str) or not point_id or member_id not in MEMBERS or not 0 <= site_ordinal < 20:
        raise ExecutionError("common RNG identity is invalid")
    return {
        "annual": {"experiment_id": f"a11e1-development-{point_id}", "strategy_id": ANNUAL_STRATEGY,
                   "member_id": member_id, "domain": "annual_target"},
        "hurdle": {"key_strategy_id": REGION_ARM, "member_id": member_id, "domain": "month_hurdle",
                   "blake2b_key": f"a11e1-integrated-v1\0{point_id}\0{REGION_ARM}\0{member_id}\0month_hurdle"},
        "daily": {"experiment_id": f"a11e1-core-{point_id}", "strategy_id": ANNUAL_STRATEGY,
                  "member_id_formula": f"{member_id}*3840 + {site_ordinal}*192 + year_index*12 + month_index",
                  "ordinal_start": daily_ordinal(member_id, site_ordinal, 0, 0),
                  "ordinal_end": daily_ordinal(member_id, site_ordinal, 15, 11),
                  "domains": ["wet_count", "occurrence", "amount", "temperature", "range"]},
    }


def rng_preflight(development: list[dict[str, Any]]) -> dict[str, Any]:
    if len(development) != 20 or len({row["point_id"] for row in development}) != 20:
        raise ExecutionError("RNG preflight requires 20 unique development stations")
    annual, hurdle, daily = set(), set(), set()
    contracts = {}
    for site_ordinal, observed in enumerate(development):
        point = observed["point_id"]
        for member_id in MEMBERS:
            contract = common_rng_contract(point, member_id, site_ordinal)
            contracts[f"{point}/{member_id}"] = contract
            annual.add((contract["annual"]["experiment_id"], member_id, "annual_target"))
            hurdle.add(contract["hurdle"]["blake2b_key"])
            for year_index in range(16):
                for month_index in range(12):
                    daily.add((contract["daily"]["experiment_id"], daily_ordinal(member_id, site_ordinal, year_index, month_index)))
    if (len(annual), len(hurdle), len(daily)) != (160, 160, 30720):
        raise ExecutionError("RNG identities collide")
    return {
        "schema_version": "a11e3-rng-preflight-1", "annual_identity_count": 160,
        "hurdle_identity_count": 160, "daily_ordinal_count": 30720,
        "daily_domain_stream_count": 153600, "paired_arm_cell_count": 160,
        "member_zero_preserves_a11e1_identity": True, "contracts_sha256": canonical_digest(contracts),
        "confirmation_target_series_accessed": False,
    }


def adapter_with_location(inherited_adapter: dict[str, Any], location: np.ndarray) -> dict[str, Any]:
    adapter = dict(inherited_adapter)
    adapter["location"] = location
    if set(adapter) != set(inherited_adapter) or any(adapter[name] is not inherited_adapter[name] for name in inherited_adapter if name != "location"):
        raise ExecutionError("forcing wrapper changed an inherited adapter surface")
    return adapter


def evaluate_member(observed: dict[str, Any], model: dict[str, Any], inherited_adapter: dict[str, Any],
                    location: np.ndarray, site_ordinal: int, member_id: int, inherited: Any) -> dict[str, Any]:
    adapter = adapter_with_location(inherited_adapter, location)
    point = observed["point_id"]
    target_rng = inherited.lab.domain_rng(f"a11e1-development-{point}", ANNUAL_STRATEGY, member_id, "annual_target")
    states, target_receipt = inherited.lab.generate_strategy_targets(
        model, 16, target_rng, adapter["location"], adapter["variances"],
        adapter["annual_weights"], adapter["annual_variance"],
    )
    positive_equivalent = adapter["floors"] + np.exp(states[:, :12])
    temperature, daily_range = states[:, 12:24], np.exp(states[:, 24:36])
    generated_equivalent = np.empty((16, 12))
    wet_fraction = np.empty((16, 12))
    failures, previous_wet = 0, False
    hurdle = inherited.hurdle_rng(point, REGION_ARM, member_id)
    texture = adapter["texture"]
    for year_index, year in enumerate(inherited.DEVELOPMENT_YEARS):
        for month in inherited.MONTHS:
            slot = month - 1
            days = calendar.monthrange(year, month)[1]
            dry = float(hurdle.random()) < float(adapter["dry_probability"][slot])
            equivalent_total = 0.0 if dry else float(positive_equivalent[year_index, slot])
            total = equivalent_total * days / inherited.EQUIVALENT_DAYS
            ordinal = daily_ordinal(member_id, site_ordinal, year_index, slot)
            streams = inherited.lab.domain_rngs(f"a11e1-core-{point}", ANNUAL_STRATEGY, ordinal)
            required = {name: streams[name] for name in ("wet_count", "occurrence", "amount", "temperature", "range")}
            counts = inherited.eligible_wet_counts(adapter["wet_counts"][slot], days)
            generated, receipt = inherited.lab.generate_core_month(
                ANNUAL_STRATEGY, total, days, counts, 1.0, previous_wet,
                float(texture["pww"][slot]), float(texture["pwd"][slot]),
                float(temperature[year_index, slot]), float(texture["temp_sd"][slot]),
                float(daily_range[year_index, slot]), float(texture["amount_phi"][slot]),
                float(texture["temp_phi"][slot]), float(texture["range_phi"][slot]), required,
            )
            previous_wet = bool(generated["wet"][-1])
            generated_equivalent[year_index, slot] = receipt["precipitation_total_mm"] * inherited.EQUIVALENT_DAYS / days
            wet_fraction[year_index, slot] = receipt["wet_count"] / days
            failures += int(abs(receipt["precipitation_total_mm"] - total) > 1e-8)
            failures += int(abs(float(np.mean(generated["temperature_mean"])) - temperature[year_index, slot]) > 1e-10)
            failures += int(abs(receipt["range_mean"] - daily_range[year_index, slot]) > 1e-10)
            failures += int(np.any(generated["temperature_max"] < generated["temperature_min"]))
            failures += int((total == 0.0) != (receipt["wet_count"] == 0))
    observed_p, observed_t, observed_r = observed["precipitation"], observed["tmean"], observed["dtr"]
    weights = adapter["annual_weights"][12:24]
    gp, op = np.sum(generated_equivalent, axis=1), np.sum(observed_p, axis=1)
    gt, ot = temperature @ weights, observed_t @ weights
    metrics = {
        "monthly_equivalent_precipitation_mean_relative_absolute_error": float(np.mean(np.abs(np.mean(generated_equivalent, axis=0) - np.mean(observed_p, axis=0)) / np.maximum(np.mean(observed_p, axis=0), 0.01))),
        "monthly_temperature_mean_absolute_error_c": float(np.mean(np.abs(np.mean(temperature, axis=0) - np.mean(observed_t, axis=0)))),
        "monthly_range_mean_relative_absolute_error": float(np.mean(np.abs(np.mean(daily_range, axis=0) - np.mean(observed_r, axis=0)) / np.maximum(np.mean(observed_r, axis=0), 0.01))),
        "monthly_wet_fraction_mean_absolute_error": float(np.mean(np.abs(np.mean(wet_fraction, axis=0) - np.mean(observed["wet_fraction"], axis=0)))),
        "annual_precipitation_variance_absolute_log_ratio": abs(math.log(max(float(np.var(gp, ddof=1)), 1e-12) / max(float(np.var(op, ddof=1)), 1e-12))),
        "annual_temperature_variance_absolute_log_ratio": abs(math.log(max(float(np.var(gt, ddof=1)), 1e-12) / max(float(np.var(ot, ddof=1)), 1e-12))),
        "annual_precipitation_lag1_absolute_error": abs(inherited.safe_corr(gp[:-1], gp[1:]) - inherited.safe_corr(op[:-1], op[1:])),
        "daily_invariant_failures": failures,
    }
    metrics["descriptive_composite_score"] = (
        metrics[PRIMARY_METRICS[0]] + metrics[PRIMARY_METRICS[1]] / 5.0
        + metrics["monthly_range_mean_relative_absolute_error"]
        + metrics["monthly_wet_fraction_mean_absolute_error"] * 3.0
        + metrics["annual_precipitation_variance_absolute_log_ratio"]
        + metrics["annual_temperature_variance_absolute_log_ratio"]
        + metrics["annual_precipitation_lag1_absolute_error"]
    )
    if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in metrics.values()):
        raise ExecutionError("member metrics are nonfinite")
    return {
        "member_id": member_id, "years": 16, "metrics": metrics,
        "target_receipt": target_receipt,
        "stream_summary_sha256": canonical_digest({
            "precipitation": generated_equivalent.tolist(), "temperature": temperature.tolist(),
            "range": daily_range.tolist(), "wet_fraction": wet_fraction.tolist(),
        }),
    }


def evaluate_hypothesis(rows: list[dict[str, Any]], expected_stations: list[str]) -> dict[str, Any]:
    station_set = set(expected_stations)
    if len(expected_stations) != 20 or len(station_set) != 20:
        raise ExecutionError("hypothesis station roster must contain 20 unique stations")
    keys = {(row.get("station_id"), row.get("member_id")) for row in rows}
    expected_keys = {(station, member_id) for station in station_set for member_id in MEMBERS}
    if len(rows) != 160 or keys != expected_keys:
        raise ExecutionError("hypothesis requires the exact 20-station by eight-member Cartesian grid")
    for row in rows:
        for arm in ("region_metrics", "nearest_metrics"):
            if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) for value in row[arm].values()):
                raise ExecutionError("hypothesis evidence contains a nonfinite metric")
    maximum_failures = max(max(row["region_metrics"]["daily_invariant_failures"], row["nearest_metrics"]["daily_invariant_failures"]) for row in rows)
    if maximum_failures != 0:
        raise ExecutionError("hypothesis evidence contains a daily invariant failure")
    members = {}
    for member_id in MEMBERS:
        member_rows = [row for row in rows if row["member_id"] == member_id]
        metrics = {}
        for metric in PRIMARY_METRICS:
            region = float(np.median([row["region_metrics"][metric] for row in member_rows]))
            nearest = float(np.median([row["nearest_metrics"][metric] for row in member_rows]))
            delta = nearest - region
            metrics[metric] = {"region_median": region, "nearest_median": nearest,
                               "delta_nearest_minus_region": delta, "strictly_negative": delta < 0.0}
        members[str(member_id)] = {"primary_metrics": metrics, "both_strictly_improve": all(value["strictly_negative"] for value in metrics.values())}
    supported = all(value["both_strictly_improve"] for value in members.values())
    return {
        "members": members, "all_16_primary_deltas_strictly_negative": supported,
        "maximum_daily_invariant_failures": maximum_failures,
        "disposition": "STABLE_FOR_EXPLORATION" if supported else "NOT_STABLE_FOR_EXPLORATION",
    }


def assert_member_zero(rows: list[dict[str, Any]], expected_stations: list[str]) -> dict[str, Any]:
    baseline = json.loads(A11E1_EVIDENCE.read_text())
    nearest = json.loads(A11E2_EVIDENCE.read_text())
    baseline_by_point = {row["point_id"]: row for row in baseline["rows"] if row["strategy_id"] == REGION_ARM}
    nearest_by_point = {row["station_id"]: row for row in nearest["rows"]}
    member_zero = [row for row in rows if row["member_id"] == 0]
    if len(expected_stations) != 20 or len(set(expected_stations)) != 20 or {row.get("station_id") for row in member_zero} != set(expected_stations):
        raise ExecutionError("member-0 replay roster differs")
    for row in member_zero:
        point = row["station_id"]
        if row["region_metrics"] != baseline_by_point[point]["metrics"] or row["region_stream_summary_sha256"] != baseline_by_point[point]["stream_summary_sha256"]:
            raise ExecutionError(f"regional member-0 replay differs: {point}")
        if row["nearest_metrics"] != nearest_by_point[point]["candidate_metrics"] or row["nearest_stream_summary_sha256"] != nearest_by_point[point]["stream_summary_sha256"]:
            raise ExecutionError(f"nearest member-0 replay differs: {point}")
    return {
        "regional_anchor_evidence_sha256": digest(A11E1_EVIDENCE),
        "nearest_anchor_evidence_sha256": digest(A11E2_EVIDENCE),
        "station_count": 20, "metrics_and_stream_summaries_exact": True,
    }


def execute(source_commit: str) -> None:
    started = time.monotonic()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    runtime = verify_runtime(manifest)
    source_receipt = verify_source(source_commit, manifest)
    predecessor = ensure_a11e2_loaded()
    predecessor_manifest = predecessor.validate_manifest(json.loads(A11E2_MANIFEST.read_text()))
    input_hashes, development_rows, _baseline = predecessor.verify_inputs(predecessor_manifest)
    fit_summaries, fit_preflight = predecessor.ensure_base_loaded().load_fit_corpus()
    inherited = predecessor.ensure_base_loaded()
    development, development_preflight = inherited.load_development(development_rows)
    selection = predecessor.build_selection(
        json.loads(predecessor.PANEL.read_text()), json.loads(predecessor.COHORT_SELECTION.read_text()), development_rows,
    )
    if selection != json.loads(A11E2_SELECTION.read_text()):
        raise ExecutionError("frozen selector mapping does not replay")
    rng_receipt = rng_preflight(development)
    calendar_rng = {
        "schema_version": "a11e3-calendar-rng-preflight-1", "valid": True,
        "source_transform": "daymet_official_365_v1",
        "normalized_statistic": "daymet_mask_normalized_month_v1",
        "fit": fit_preflight, "development": development_preflight, "rng": rng_receipt,
        "runtime": runtime,
        "confirmation_target_series_accessed": False,
    }
    atomic_json(PACKAGE / "calendar-rng-preflight-v1.json", calendar_rng)

    candidate = [row for row in fit_summaries if row["role"] == "candidate_fit"]
    candidate_by_point = {row["point_id"]: row for row in candidate}
    adapters = inherited.adapter_parameters(candidate)
    models, inherited_fit = inherited.fit_regions(candidate, adapters)
    selection_by_station = {row["station_id"]: row for row in selection["rows"]}
    nearest_locations = {}
    for observed in development:
        selected = selection_by_station[observed["point_id"]]["candidate_point_id"]
        nearest_locations[observed["point_id"]] = predecessor.candidate_location(candidate_by_point[selected], observed["regime"], adapters)
    frozen_fit = json.loads(A11E2_FIT.read_text())
    location_hash = canonical_digest({point: value.tolist() for point, value in sorted(nearest_locations.items())})
    if inherited_fit["fit_sha256"] != frozen_fit["inherited_fit_sha256"] or location_hash != frozen_fit["station_location_sha256"]:
        raise ExecutionError("frozen model or nearest locations do not replay")
    fit_receipt = {
        "schema_version": "a11e3-fit-authentication-1", "candidate_fit_only": True,
        "inherited_fit_sha256": inherited_fit["fit_sha256"],
        "regional_location_sha256": canonical_digest({name: adapters[name]["location"].tolist() for name in sorted(adapters)}),
        "nearest_station_location_sha256": location_hash,
        "selection_receipt_sha256": digest(A11E2_SELECTION), "candidate_fit_objects": len(candidate),
        "confirmation_target_series_accessed": False,
    }
    atomic_json(PACKAGE / "fit-authentication-v1.json", fit_receipt)

    rows = []
    for site_ordinal, observed in enumerate(development):
        point, regime = observed["point_id"], observed["regime"]
        model = models[f"{regime}/{REGION_ARM}"]
        for member_id in MEMBERS:
            region = evaluate_member(observed, model, adapters[regime], adapters[regime]["location"], site_ordinal, member_id, inherited)
            nearest = evaluate_member(observed, model, adapters[regime], nearest_locations[point], site_ordinal, member_id, inherited)
            if region["metrics"]["daily_invariant_failures"] or nearest["metrics"]["daily_invariant_failures"]:
                raise ExecutionError(f"daily invariant failure: {point}/{member_id}")
            rows.append({
                "station_id": point, "station_regime": regime, "member_id": member_id, "years": 16,
                "region_strategy_id": REGION_ARM, "nearest_strategy_id": NEAREST_ARM,
                "candidate_point_id": selection_by_station[point]["candidate_point_id"],
                "great_circle_distance_km": selection_by_station[point]["great_circle_distance_km"],
                "common_rng_contract": common_rng_contract(point, member_id, site_ordinal),
                "region_metrics": region["metrics"], "nearest_metrics": nearest["metrics"],
                "metric_differences_nearest_minus_region": {name: nearest["metrics"][name] - region["metrics"][name] for name in region["metrics"]},
                "region_stream_summary_sha256": region["stream_summary_sha256"],
                "nearest_stream_summary_sha256": nearest["stream_summary_sha256"],
            })
    if len(rows) * 2 != manifest["resource_bound"]["maximum_cells_per_execution"]:
        raise ExecutionError("development cell count differs from resource bound")
    expected_stations = [observed["point_id"] for observed in development]
    member_zero = assert_member_zero(rows, expected_stations)
    evaluation = evaluate_hypothesis(rows, expected_stations)
    evidence = {
        "schema_version": "a11e3-development-evidence-1", "execution_id": manifest["execution_id"],
        "source_commit": source_commit, "arms": manifest["arms"], "member_ids": list(MEMBERS),
        "paired_row_count": len(rows), "cell_count": len(rows) * 2, "rows": rows,
        "member_zero_replay": member_zero, "hypothesis": evaluation,
        "limitations": [
            "development targets reused across the adaptive A11 campaign",
            "coordinate-only selector with long Maine and Montana distances",
            "common RNG does not imply identical draw consumption or stationwise dominance",
            "eight fixed members and sixteen-year streams are an exploratory stability screen",
        ],
        "confirmation_target_series_accessed": False,
    }
    evidence["evidence_sha256"] = canonical_digest(evidence)
    atomic_json(PACKAGE / "development-evidence-v1.json", evidence)
    decision = {
        "schema_version": "a11e3-development-decision-1", "execution_id": manifest["execution_id"],
        "terminal": "EXECUTED-COMPLETE", "science_status": "EXPLORATORY_STABILITY_EVALUATED",
        **evaluation, "member_zero_replay": member_zero,
        "scope": "development only; no confirmation, selection, tuning, or promotion authority",
        "confirmation_authorized": False, "production_authorized": False,
    }
    atomic_json(PACKAGE / "development-decision-v1.json", decision)
    outputs = [PACKAGE / name for name in (
        "calendar-rng-preflight-v1.json", "fit-authentication-v1.json",
        "development-evidence-v1.json", "development-decision-v1.json",
    )]
    receipt = {
        "schema_version": "a11e3-execution-receipt-1", "execution_id": manifest["execution_id"],
        **source_receipt, "inherited_input_hashes": input_hashes,
        "runtime": runtime,
        "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in outputs},
        "elapsed_seconds": time.monotonic() - started, "fit_calendar_objects": len(fit_summaries),
        "candidate_fit_objects": len(candidate), "development_objects": len(development),
        "paired_rows": len(rows), "development_cells": len(rows) * 2,
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
