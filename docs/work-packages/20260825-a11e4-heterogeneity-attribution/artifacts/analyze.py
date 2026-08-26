#!/usr/bin/env python3
"""Execute the source-bound A11E4 metadata attribution analysis."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
MANIFEST_PATH = PACKAGE / "analysis-manifest-v1.json"
SCHEMA_PATH = PACKAGE / "analysis-manifest-v1.schema.json"
SPEC_PATH = ROOT / "docs/specifications/SPEC-A11-HETEROGENEITY-ATTRIBUTION.md"
PACKAGE_PATH = PACKAGE.parent / "package.md"
PLAN_PATH = ROOT / "docs/exec-plans/20260825-a11e4-heterogeneity-attribution.md"
A11E3 = ROOT / "docs/work-packages/20260825-a11e3-multi-member-forcing-stability/artifacts"
A11E3_EVIDENCE = A11E3 / "development-evidence-v1.json"
A11E3_DECISION = A11E3 / "development-decision-v1.json"
A11E3_RECEIPT = A11E3 / "execution-receipt-v1.json"
A11E3_MANIFEST = A11E3 / "execution-manifest-v1.json"
A11E3_EXECUTOR = A11E3 / "execute.py"
A11E3_CALENDAR = A11E3 / "calendar-rng-preflight-v1.json"
A11E3_FIT = A11E3 / "fit-authentication-v1.json"
A11E3_REVIEW = A11E3 / "review.md"
A11E3_TEST_RESULTS = A11E3 / "test-results.md"
A11E2_SELECTION = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts/selection-receipt-v1.json"
A11E2_DECISION = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts/development-decision-v1.json"
A11E2_RECEIPT = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts/execution-receipt-v1.json"
REGION_ARM = "circular_fixed_block_physical_core_v1"
NEAREST_ARM = "circular_fixed_block_nearest_candidate_forcing_v1"
MEMBERS = tuple(range(8))
PRIMARY_METRICS = (
    "monthly_equivalent_precipitation_mean_relative_absolute_error",
    "monthly_temperature_mean_absolute_error_c",
)
EXPECTED_INPUTS = {
    "a11e2_closure_commit": "65ed7ac7c54a67014e33358c64147bc686cd9327",
    "a11e2_decision_sha256": "8ba4757b817453c4be5d7a706aa321a9786a66425a9285584d94f49c0d205dc5",
    "a11e2_execution_receipt_sha256": "24c8aa6391fedb900f3376842c37c56442c91473bee54d823f1e4afc84267235",
    "a11e2_selection_receipt_sha256": "26e33ca30e0e64fa0dba1913f56ecaec12fbb5d1cc95aeb0a341af9ae52b31d6",
    "a11e2_source_commit": "e15369ad26f4e0b646f5f4665912dd6a37e35e3a",
    "a11e3_calendar_preflight_sha256": "49d86f2da3a00ad05a115c17b91a5c820a740f5b8acbbf0127a0b192bb5eb6a4",
    "a11e3_closure_commit": "cc85b4dc56040116cfcef1e1f721a971b0cb6b54",
    "a11e3_decision_sha256": "06537916809199ed0857ce8d8af2dab77f86975bb67bb536f41651ce5d424d37",
    "a11e3_evidence_self_sha256": "c8e302b31690efaeb58af710fb9ab4a7301bea661dc4017a0568f6c5ddd93d2f",
    "a11e3_evidence_sha256": "834d9af57679a0a252622d7c29fb223985833b85022a8bc55656f7a24daaa930",
    "a11e3_execution_manifest_sha256": "e3e925dae4b9df6ab2e2fed958873a7fb51a26374cb27fd29b0d77f2fab71044",
    "a11e3_execution_receipt_sha256": "00464e2e2b4b96f2ff71e35c6aed8f543f2215b43c207b3bcaea55ff0937f314",
    "a11e3_executor_sha256": "4572b45c21eb9d4b3d7ec0f1c264817228aaa92ca632af23bd75533529a2d543",
    "a11e3_fit_authentication_sha256": "5cdcddec1e411e1b0a726439ea0944db2141462de451dcebe7d04e28e232d523",
    "a11e3_review_sha256": "9857a23d2daf586cf2d94afa43a20c75ef56bbbd3d3a3cc57735f9ed4ceae18d",
    "a11e3_source_commit": "ac254ee4fc2bc0073a4f4c351e555cc517c49f3d",
    "a11e3_test_results_sha256": "2cf7e8f6a67b1cab86d0b611206ec6876f2249c9e8da9c40dcfba072e6b5795f",
}


class AnalysisError(RuntimeError):
    """The prospective A11E4 analysis contract was violated."""


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
    expected = {
        "analysis_id": "a11e4-heterogeneity-attribution-v1",
        "confirmation_target_access": False,
        "decision": {"alpha_familywise": 0.05, "dispositions": ["SUPPORTED_BOTH_METADATA_ASSOCIATIONS", "SUPPORTED_DISTANCE_ASSOCIATION", "SUPPORTED_REGIME_MISMATCH_ASSOCIATION", "NO_STABLE_METADATA_ASSOCIATION"], "support_rule": "max_t_adjusted_p_at_most_alpha_and_full_sign_preserved_in_all_lomo_and_loso_fits"},
        "inputs": EXPECTED_INPUTS,
        "model": {"distance_transform": "ascending_average_rank_centered_scaled_population_sd", "exact_assignment_count": 1327104, "familywise_statistic": "max_abs_t_distance_mismatch", "max_t_comparison_relative_tolerance": 1e-12, "mismatch": "station_regime_not_equal_candidate_regime", "outcome": "station_fraction_of_eight_members_with_both_primary_metrics_strictly_improved", "permutation": "exhaustive_outcome_label_permutation_within_station_regime_including_identity", "permutation_degenerate_fit_rule": "sse_at_or_below_ols_tolerance_maps_nonzero_selected_beta_to_signed_infinity_and_counts_as_extreme", "predictors": ["station_regime_fixed_effects", "ranked_distance", "regime_mismatch"], "reference_regime": "arid_boundary", "station_regime_levels": ["arid_boundary", "cold", "hot_arid", "humid", "monsoonal_transition", "non_monsoonal_semi_arid"], "station_regime_sizes": [2, 4, 4, 2, 4, 4]},
        "outcome": {"member_ids": list(MEMBERS), "station_count": 20},
        "runtime": {"numpy": "2.3.5", "python": "3.12.13"},
        "schema_version": 1,
        "stability": {"leave_one_member_out_fits": 8, "leave_one_station_out_fits": 20, "rule": "coefficient_retains_full_fit_strict_sign_in_every_fit"},
    }
    if value != expected:
        raise AnalysisError("analysis manifest identity differs")
    return value


def verify_runtime(manifest: dict[str, Any]) -> dict[str, str]:
    actual = {"numpy": np.__version__, "python": platform.python_version()}
    if actual != manifest["runtime"]:
        raise AnalysisError("scientific runtime identity differs")
    return actual


def git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if result.returncode != 0:
        raise AnalysisError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def git_blob(commit: str, path: Path) -> bytes:
    return git("show", f"{commit}:{path.relative_to(ROOT).as_posix()}")


def verify_file_at_commit(path: Path, expected: str, commit: str) -> None:
    if digest(path) != expected or digest_bytes(git_blob(commit, path)) != expected:
        raise AnalysisError(f"input dependency drifted: {path.name}")


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if len(source_commit) != 40 or source_commit != git("rev-parse", "origin/main").decode().strip():
        raise AnalysisError("analysis source is not the exact published origin/main commit")
    required = [Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_analyze.py", SPEC_PATH, PACKAGE_PATH, PLAN_PATH]
    hashes = {}
    for path in required:
        working = path.read_bytes()
        if working != git_blob(source_commit, path):
            raise AnalysisError(f"working source differs from analysis commit: {path.name}")
        hashes[path.relative_to(ROOT).as_posix()] = digest_bytes(working)
    inputs = manifest["inputs"]
    for path, key, commit_key in (
        (A11E3_MANIFEST, "a11e3_execution_manifest_sha256", "a11e3_source_commit"),
        (A11E3_EXECUTOR, "a11e3_executor_sha256", "a11e3_source_commit"),
        (A11E3_CALENDAR, "a11e3_calendar_preflight_sha256", "a11e3_closure_commit"),
        (A11E3_FIT, "a11e3_fit_authentication_sha256", "a11e3_closure_commit"),
        (A11E3_EVIDENCE, "a11e3_evidence_sha256", "a11e3_closure_commit"),
        (A11E3_DECISION, "a11e3_decision_sha256", "a11e3_closure_commit"),
        (A11E3_RECEIPT, "a11e3_execution_receipt_sha256", "a11e3_closure_commit"),
        (A11E3_REVIEW, "a11e3_review_sha256", "a11e3_closure_commit"),
        (A11E3_TEST_RESULTS, "a11e3_test_results_sha256", "a11e3_closure_commit"),
        (A11E2_SELECTION, "a11e2_selection_receipt_sha256", "a11e2_closure_commit"),
        (A11E2_DECISION, "a11e2_decision_sha256", "a11e2_closure_commit"),
        (A11E2_RECEIPT, "a11e2_execution_receipt_sha256", "a11e2_closure_commit"),
    ):
        verify_file_at_commit(path, inputs[key], inputs[commit_key])
    return {"analysis_source_commit": source_commit, "published_ref": "origin/main", "source_hashes": hashes}


def average_ranks(values: np.ndarray) -> np.ndarray:
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise AnalysisError("rank input must be a finite vector")
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=np.float64)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    return ranks


def design_matrix(stations: list[dict[str, Any]], manifest: dict[str, Any], require_full_roster: bool = True) -> tuple[np.ndarray, list[str]]:
    levels = manifest["model"]["station_regime_levels"]
    regimes = [row["station_regime"] for row in stations]
    if sorted(set(regimes)) != levels:
        raise AnalysisError("station regime levels differ")
    if require_full_roster:
        sizes = [regimes.count(level) for level in levels]
        if sizes != manifest["model"]["station_regime_sizes"]:
            raise AnalysisError("station regime sizes differ")
    distances = np.asarray([row["great_circle_distance_km"] for row in stations], dtype=np.float64)
    ranks = average_ranks(distances)
    scale = float(np.std(ranks, ddof=0))
    if scale <= 0.0:
        raise AnalysisError("ranked distance has zero scale")
    ranked_distance = (ranks - np.mean(ranks)) / scale
    mismatch = np.asarray([not row["same_regime"] for row in stations], dtype=np.float64)
    columns = [np.ones(len(stations), dtype=np.float64)]
    names = ["intercept"]
    for level in levels[1:]:
        columns.append(np.asarray([regime == level for regime in regimes], dtype=np.float64))
        names.append(f"station_regime={level}")
    columns.extend([ranked_distance, mismatch])
    names.extend(["ranked_distance", "regime_mismatch"])
    matrix = np.column_stack(columns)
    if np.linalg.matrix_rank(matrix) != matrix.shape[1]:
        raise AnalysisError("joint attribution design is not full rank")
    return matrix, names


def ols_fit(matrix: np.ndarray, outcomes: np.ndarray) -> dict[str, Any]:
    if matrix.ndim != 2 or outcomes.shape != (matrix.shape[0],) or not np.isfinite(matrix).all() or not np.isfinite(outcomes).all():
        raise AnalysisError("OLS inputs are invalid")
    rows, columns = matrix.shape
    if rows <= columns or np.linalg.matrix_rank(matrix) != columns:
        raise AnalysisError("OLS design lacks residual degrees of freedom or rank")
    inverse = np.linalg.inv(matrix.T @ matrix)
    beta = inverse @ matrix.T @ outcomes
    residual = outcomes - matrix @ beta
    sse = float(residual @ residual)
    zero_tolerance = float(residual_zero_tolerance(outcomes.reshape(1, -1))[0])
    if not math.isfinite(sse) or sse <= zero_tolerance:
        raise AnalysisError("OLS residual variance is not finite and positive")
    sigma2 = sse / (rows - columns)
    standard_error = np.sqrt(np.diag(inverse) * sigma2)
    t_values = beta / standard_error
    centered = outcomes - np.mean(outcomes)
    total = float(centered @ centered)
    if total <= 0.0:
        raise AnalysisError("OLS outcome variance is not positive")
    return {"beta": beta, "t": t_values, "sse": sse, "r_squared": 1.0 - sse / total,
            "residual_df": rows - columns, "inverse_xtx": inverse}


def incremental_r_squared(matrix: np.ndarray, outcomes: np.ndarray, full_r_squared: float, column_index: int) -> float:
    reduced = np.delete(matrix, column_index, axis=1)
    reduced_fit = ols_fit(reduced, outcomes)
    return float(full_r_squared - reduced_fit["r_squared"])


def residual_zero_tolerance(outcome_matrix: np.ndarray) -> np.ndarray:
    if outcome_matrix.ndim != 2 or not np.isfinite(outcome_matrix).all():
        raise AnalysisError("residual-tolerance outcomes are invalid")
    return np.finfo(np.float64).eps * np.maximum(1.0, np.sum(outcome_matrix * outcome_matrix, axis=1)) * outcome_matrix.shape[1] * 10.0


def permutation_groups(stations: list[dict[str, Any]], manifest: dict[str, Any]) -> list[np.ndarray]:
    groups = []
    for level, expected_size in zip(manifest["model"]["station_regime_levels"], manifest["model"]["station_regime_sizes"]):
        indices = np.asarray([index for index, row in enumerate(stations) if row["station_regime"] == level], dtype=np.int64)
        if len(indices) != expected_size:
            raise AnalysisError("permutation stratum size differs")
        groups.append(indices)
    return groups


def selected_t_batch(matrix: np.ndarray, outcome_matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    inverse = np.linalg.inv(matrix.T @ matrix)
    projection = inverse @ matrix.T
    df = matrix.shape[0] - matrix.shape[1]
    diagonal = np.diag(inverse)[-2:]
    betas = outcome_matrix @ projection.T
    residuals = outcome_matrix - betas @ matrix.T
    sse = np.sum(residuals * residuals, axis=1)
    degenerate = sse <= residual_zero_tolerance(outcome_matrix)
    scales = np.sqrt(np.maximum(sse, 0.0)[:, None] / df * diagonal[None, :])
    selected_beta = betas[:, -2:]
    zero_scale = np.where(selected_beta == 0.0, 0.0, np.copysign(np.full_like(selected_beta, np.inf), selected_beta))
    t_values = np.divide(selected_beta, scales, out=zero_scale.copy(), where=scales > 0.0)
    t_values[degenerate] = zero_scale[degenerate]
    return t_values, degenerate


def exact_max_t(matrix: np.ndarray, outcomes: np.ndarray, groups: list[np.ndarray], observed_abs_t: tuple[float, float], expected_count: int, relative_tolerance: float) -> dict[str, Any]:
    if not math.isfinite(relative_tolerance) or not 0.0 < relative_tolerance < 1e-6:
        raise AnalysisError("max-t comparison tolerance is invalid")
    permutations = [list(itertools.permutations(outcomes[group].tolist())) for group in groups]
    assignment_count = math.prod(len(values) for values in permutations)
    if assignment_count != expected_count:
        raise AnalysisError("exact permutation assignment count differs")
    extreme = np.zeros(2, dtype=np.int64)
    processed = 0
    batch = []
    thresholds = np.asarray(observed_abs_t, dtype=np.float64)
    comparison_limits = thresholds - relative_tolerance * np.maximum(1.0, thresholds)
    identity_values, identity_degenerate = selected_t_batch(matrix, outcomes.reshape(1, -1))
    if bool(identity_degenerate[0]):
        raise AnalysisError("observed identity fit is degenerate")
    identity_t = identity_values[0]
    identity_maximum = float(np.max(np.abs(identity_t)))
    identity_counted = identity_maximum >= comparison_limits
    if not bool(np.all(identity_counted)):
        raise AnalysisError("identity assignment is not counted by max-t comparison")

    def process(values: list[np.ndarray]) -> None:
        nonlocal processed, extreme, degenerate_count
        if not values:
            return
        outcome_matrix = np.vstack(values)
        t_values, degenerate = selected_t_batch(matrix, outcome_matrix)
        maximum = np.max(np.abs(t_values), axis=1)
        extreme += np.asarray([np.count_nonzero(maximum >= limit) for limit in comparison_limits], dtype=np.int64)
        degenerate_count += int(np.count_nonzero(degenerate))
        processed += len(values)

    degenerate_count = 0
    for combination in itertools.product(*permutations):
        permuted = outcomes.copy()
        for indices, values in zip(groups, combination):
            permuted[indices] = values
        batch.append(permuted)
        if len(batch) == 4096:
            process(batch)
            batch = []
    process(batch)
    if processed != assignment_count:
        raise AnalysisError("exact permutation processing count differs")
    return {
        "assignment_count": assignment_count, "identity_included": True,
        "identity_max_t": identity_maximum, "identity_counted_for_both_thresholds": bool(np.all(identity_counted)),
        "comparison_relative_tolerance": relative_tolerance,
        "degenerate_assignment_count": degenerate_count,
        "distance_extreme_count": int(extreme[0]), "mismatch_extreme_count": int(extreme[1]),
        "distance_adjusted_p": float(extreme[0] / assignment_count),
        "mismatch_adjusted_p": float(extreme[1] / assignment_count),
    }


def predictor_supported(adjusted_p: float, full_beta: float, lomo: np.ndarray, loso: np.ndarray, alpha: float) -> tuple[bool, bool, bool]:
    if not all(math.isfinite(value) for value in (adjusted_p, full_beta, alpha)) or not np.isfinite(lomo).all() or not np.isfinite(loso).all():
        raise AnalysisError("predictor support inputs are nonfinite")
    if lomo.shape != (8,) or loso.shape != (20,) or not 0.0 <= adjusted_p <= 1.0 or not 0.0 < alpha < 1.0:
        raise AnalysisError("predictor support inputs differ from the frozen design")
    lomo_same = bool(full_beta != 0.0 and np.all(lomo * full_beta > 0.0))
    loso_same = bool(full_beta != 0.0 and np.all(loso * full_beta > 0.0))
    return adjusted_p <= alpha and lomo_same and loso_same, lomo_same, loso_same


def joint_attribution(stations: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    matrix, names = design_matrix(stations, manifest)
    outcomes = np.asarray([row["both_improvement_fraction"] for row in stations], dtype=np.float64)
    full = ols_fit(matrix, outcomes)
    observed_abs_t = (abs(float(full["t"][-2])), abs(float(full["t"][-1])))
    exact = exact_max_t(matrix, outcomes, permutation_groups(stations, manifest), observed_abs_t,
                        manifest["model"]["exact_assignment_count"], manifest["model"]["max_t_comparison_relative_tolerance"])
    lomo_coefficients = []
    for member_id in MEMBERS:
        lomo_outcome = np.asarray([
            sum(value for index, value in enumerate(row["both_improvement_by_member"]) if index != member_id) / 7.0
            for row in stations
        ], dtype=np.float64)
        lomo_coefficients.append(ols_fit(matrix, lomo_outcome)["beta"][-2:])
    loso_coefficients = []
    for station_index in range(20):
        subset = [row for index, row in enumerate(stations) if index != station_index]
        subset_matrix, _ = design_matrix(subset, manifest, require_full_roster=False)
        subset_outcome = np.asarray([row["both_improvement_fraction"] for row in subset], dtype=np.float64)
        loso_coefficients.append(ols_fit(subset_matrix, subset_outcome)["beta"][-2:])
    lomo = np.asarray(lomo_coefficients)
    loso = np.asarray(loso_coefficients)
    results = {}
    for offset, (name, p_key) in enumerate((("ranked_distance", "distance_adjusted_p"), ("regime_mismatch", "mismatch_adjusted_p"))):
        beta = float(full["beta"][-2 + offset])
        supported, lomo_same, loso_same = predictor_supported(
            exact[p_key], beta, lomo[:, offset], loso[:, offset], manifest["decision"]["alpha_familywise"]
        )
        results[name] = {
            "coefficient": beta, "studentized_t": float(full["t"][-2 + offset]),
            "incremental_r_squared": incremental_r_squared(matrix, outcomes, full["r_squared"], matrix.shape[1] - 2 + offset),
            "max_t_adjusted_p": exact[p_key],
            "leave_one_member_out_coefficient_min": float(np.min(lomo[:, offset])),
            "leave_one_member_out_coefficient_max": float(np.max(lomo[:, offset])),
            "leave_one_member_out_sign_stable": lomo_same,
            "leave_one_station_out_coefficient_min": float(np.min(loso[:, offset])),
            "leave_one_station_out_coefficient_max": float(np.max(loso[:, offset])),
            "leave_one_station_out_sign_stable": loso_same,
            "supported": supported,
        }
    return {
        "column_names": names, "design_rank": int(np.linalg.matrix_rank(matrix)),
        "residual_degrees_of_freedom": full["residual_df"], "full_r_squared": float(full["r_squared"]),
        "exact_max_t": exact, "predictors": results,
    }


def build_station_summaries(evidence: dict[str, Any], selection: dict[str, Any]) -> list[dict[str, Any]]:
    if evidence.get("schema_version") != "a11e3-development-evidence-1" or evidence.get("source_commit") != EXPECTED_INPUTS["a11e3_source_commit"]:
        raise AnalysisError("A11E3 evidence identity differs")
    if evidence.get("confirmation_target_series_accessed") is not False or evidence.get("paired_row_count") != 160 or evidence.get("cell_count") != 320:
        raise AnalysisError("A11E3 evidence scope differs")
    without_self_hash = dict(evidence)
    claimed_self_hash = without_self_hash.pop("evidence_sha256", None)
    if claimed_self_hash != EXPECTED_INPUTS["a11e3_evidence_self_sha256"] or canonical_digest(without_self_hash) != claimed_self_hash:
        raise AnalysisError("A11E3 evidence self-hash differs")
    selection_rows = selection.get("rows")
    if selection.get("confirmation_target_series_accessed") is not False or not isinstance(selection_rows, list) or len(selection_rows) != 20:
        raise AnalysisError("A11E2 selector scope differs")
    by_station = {row.get("station_id"): row for row in selection_rows}
    if len(by_station) != 20:
        raise AnalysisError("selector station roster differs")
    rows = evidence.get("rows")
    keys = {(row.get("station_id"), row.get("member_id")) for row in rows} if isinstance(rows, list) else set()
    expected_keys = {(station, member) for station in by_station for member in MEMBERS}
    if len(rows or []) != 160 or keys != expected_keys:
        raise AnalysisError("evidence is not the exact selector-station by member grid")
    grouped = {station: [] for station in by_station}
    for row in rows:
        station = row["station_id"]
        selected = by_station[station]
        if row.get("region_strategy_id") != REGION_ARM or row.get("nearest_strategy_id") != NEAREST_ARM:
            raise AnalysisError("strategy identity differs")
        if row.get("station_regime") != selected.get("station_regime") or row.get("candidate_point_id") != selected.get("candidate_point_id") or row.get("great_circle_distance_km") != selected.get("great_circle_distance_km"):
            raise AnalysisError("selector join differs")
        for metrics_name in ("region_metrics", "nearest_metrics"):
            metrics = row.get(metrics_name)
            if not isinstance(metrics, dict) or not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) for value in metrics.values()):
                raise AnalysisError("metric row is nonfinite")
            if metrics.get("daily_invariant_failures") != 0:
                raise AnalysisError("metric row contains invariant failure")
        grouped[station].append(row)
    summaries = []
    for station in sorted(grouped):
        selected, member_rows = by_station[station], sorted(grouped[station], key=lambda row: row["member_id"])
        if [row["member_id"] for row in member_rows] != list(MEMBERS):
            raise AnalysisError("station member roster differs")
        precip = [row["nearest_metrics"][PRIMARY_METRICS[0]] < row["region_metrics"][PRIMARY_METRICS[0]] for row in member_rows]
        temperature = [row["nearest_metrics"][PRIMARY_METRICS[1]] < row["region_metrics"][PRIMARY_METRICS[1]] for row in member_rows]
        both = [left and right for left, right in zip(precip, temperature)]
        summaries.append({
            "station_id": station, "station_regime": selected["station_regime"],
            "candidate_point_id": selected["candidate_point_id"], "candidate_regime": selected["candidate_regime"],
            "same_regime": selected["station_regime"] == selected["candidate_regime"],
            "great_circle_distance_km": selected["great_circle_distance_km"],
            "precipitation_improvement_count": sum(precip), "temperature_improvement_count": sum(temperature),
            "both_improvement_count": sum(both), "both_improvement_fraction": sum(both) / 8.0,
            "both_improvement_by_member": both,
        })
    return summaries


def disposition(distance_signal: bool, regime_signal: bool) -> str:
    if distance_signal and regime_signal:
        return "SUPPORTED_BOTH_METADATA_ASSOCIATIONS"
    if distance_signal:
        return "SUPPORTED_DISTANCE_ASSOCIATION"
    if regime_signal:
        return "SUPPORTED_REGIME_MISMATCH_ASSOCIATION"
    return "NO_STABLE_METADATA_ASSOCIATION"


def execute(source_commit: str) -> None:
    started = time.monotonic()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    runtime = verify_runtime(manifest)
    source_receipt = verify_source(source_commit, manifest)
    evidence = json.loads(A11E3_EVIDENCE.read_text())
    decision_input = json.loads(A11E3_DECISION.read_text())
    receipt_input = json.loads(A11E3_RECEIPT.read_text())
    selection = json.loads(A11E2_SELECTION.read_text())
    a11e2_decision = json.loads(A11E2_DECISION.read_text())
    a11e2_receipt = json.loads(A11E2_RECEIPT.read_text())
    if decision_input.get("disposition") != "STABLE_FOR_EXPLORATION" or decision_input.get("confirmation_authorized") is not False or receipt_input.get("confirmation_target_series_accessed") is not False or receipt_input.get("execution_source_commit") != manifest["inputs"]["a11e3_source_commit"]:
        raise AnalysisError("closed A11E3 terminal identity differs")
    if a11e2_decision.get("disposition") != "SUPPORTED_FOR_EXPLORATION" or a11e2_decision.get("confirmation_authorized") is not False or a11e2_receipt.get("confirmation_target_series_accessed") is not False or a11e2_receipt.get("execution_source_commit") != manifest["inputs"]["a11e2_source_commit"]:
        raise AnalysisError("closed A11E2 confirmation identity differs")
    stations = build_station_summaries(evidence, selection)
    distances = np.asarray([row["great_circle_distance_km"] for row in stations], dtype=np.float64)
    same_regime = np.asarray([row["same_regime"] for row in stations], dtype=np.bool_)
    joint = joint_attribution(stations, manifest)
    distance_signal = joint["predictors"]["ranked_distance"]["supported"]
    mismatch_signal = joint["predictors"]["regime_mismatch"]["supported"]
    result = disposition(distance_signal, mismatch_signal)
    attribution = {
        "schema_version": "a11e4-attribution-evidence-1", "analysis_id": manifest["analysis_id"],
        "source_commit": source_commit, "station_count": len(stations), "member_ids": list(MEMBERS),
        "station_summaries": stations, "joint_attribution": joint,
        "descriptive_predictor_context": {
            "same_regime_mean_distance_km": float(np.mean(distances[same_regime])),
            "cross_regime_mean_distance_km": float(np.mean(distances[~same_regime])),
        },
        "disposition": result,
        "limitations": [
            "association is not causal attribution",
            "twenty development stations and eight members",
            "mismatch varies within only three station-regime strata",
            "ranked distance discards distance magnitude and includes two points above 250 km",
            "within-station-regime exchangeability is an assumption",
            "development evidence was reused adaptively across A11 stages",
        ],
        "confirmation_target_series_accessed": False,
    }
    attribution["evidence_sha256"] = canonical_digest(attribution)
    atomic_json(PACKAGE / "attribution-evidence-v1.json", attribution)
    decision = {
        "schema_version": "a11e4-attribution-decision-1", "analysis_id": manifest["analysis_id"],
        "terminal": "EXECUTED-COMPLETE", "science_status": "EXPLORATORY_ATTRIBUTION_EVALUATED",
        "disposition": result, "distance_association_supported": distance_signal,
        "regime_mismatch_association_supported": mismatch_signal,
        "scope": "closed development evidence only; no selector change, confirmation, nomination, or promotion authority",
        "confirmation_authorized": False, "production_authorized": False,
    }
    atomic_json(PACKAGE / "attribution-decision-v1.json", decision)
    outputs = [PACKAGE / "attribution-evidence-v1.json", PACKAGE / "attribution-decision-v1.json"]
    receipt = {
        "schema_version": "a11e4-execution-receipt-1", "analysis_id": manifest["analysis_id"],
        **source_receipt, "runtime": runtime,
        "input_hashes": {"a11e3_evidence": digest(A11E3_EVIDENCE), "a11e3_decision": digest(A11E3_DECISION),
                         "a11e3_execution_receipt": digest(A11E3_RECEIPT), "a11e2_selection_receipt": digest(A11E2_SELECTION)},
        "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in outputs},
        "elapsed_seconds": time.monotonic() - started, "station_count": len(stations),
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
