#!/usr/bin/env python3
"""Solve and replay the frozen A5d1b nested integer-count matrix."""

from __future__ import annotations

import math
import resource
import sys
import time

import numpy as np
import scipy
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from a5d1b_common import (
    A5D1_CONTRACT,
    CONTRACT,
    COUNT_DIR,
    COUNT_RESULTS,
    ROOT,
    ANNUAL_COMPONENTS,
    annual_means,
    a5d1_modules,
    certificate_path,
    count_only_replay,
    feature_path,
    freeze_identity,
    identity,
    load_json,
    station_ids,
    validate_counts,
    write_json,
)


def component_mean_product(name: str, means: tuple[float, float, float]) -> float:
    p, x, t = means
    return {
        "precip_total_mm.variance": p * p,
        "tmax_mean_c.variance": x * x,
        "tmin_mean_c.variance": t * t,
        "precip_total_mm_x_tmax_mean_c.covariance": p * x,
        "precip_total_mm_x_tmin_mean_c.covariance": p * t,
        "tmax_mean_c_x_tmin_mean_c.covariance": x * t,
    }[name]


def solver_record(result, wall_seconds: float, incumbent_replay: dict) -> dict:
    raw_gap = getattr(result, "mip_gap", None)
    gap = float(raw_gap) if raw_gap is not None and math.isfinite(float(raw_gap)) else None
    raw_nodes = getattr(result, "mip_node_count", None)
    nodes = int(raw_nodes) if raw_nodes is not None else None
    return {
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "objective": float(result.fun) if result.fun is not None and math.isfinite(float(result.fun)) else None,
        "mip_gap": gap,
        "mip_node_count": nodes,
        "wall_seconds": round(wall_seconds, 6),
        "incumbent_present": result.x is not None,
        "incumbent_replay": incumbent_replay,
    }


def validated_incumbent(result, model: dict) -> tuple[np.ndarray | None, dict]:
    """Independently validate a HiGHS incumbent, regardless of solve status."""
    if result.x is None:
        return None, {
            "pass": False,
            "reason": "no_incumbent",
            "maximum_integrality_residual": None,
            "maximum_bound_violation": None,
            "maximum_constraint_violation": None,
        }
    raw = np.asarray(result.x, dtype=np.float64)
    expected_size = len(model["objective"])
    if raw.shape != (expected_size,) or not np.all(np.isfinite(raw)):
        return None, {
            "pass": False,
            "reason": "invalid_incumbent_shape_or_nonfinite_value",
            "maximum_integrality_residual": None,
            "maximum_bound_violation": None,
            "maximum_constraint_violation": None,
        }
    candidate = raw.copy()
    integer_indices = np.flatnonzero(np.asarray(model["integrality"]) != 0)
    integrality_residual = (
        float(np.max(np.abs(candidate[integer_indices] - np.rint(candidate[integer_indices]))))
        if integer_indices.size
        else 0.0
    )
    candidate[integer_indices] = np.rint(candidate[integer_indices])
    bounds = model["bounds"]
    bound_violation = float(
        max(
            np.max(np.maximum(np.asarray(bounds.lb) - candidate, 0.0)),
            np.max(np.maximum(candidate - np.asarray(bounds.ub), 0.0)),
        )
    )
    constraints = model["constraints"]
    values = np.asarray(constraints.A @ candidate, dtype=np.float64)
    constraint_violation = float(
        max(
            np.max(np.maximum(np.asarray(constraints.lb) - values, 0.0)),
            np.max(np.maximum(values - np.asarray(constraints.ub), 0.0)),
        )
    )
    tolerance = 2.0e-7
    passed = (
        integrality_residual <= 1.0e-7
        and bound_violation <= tolerance
        and constraint_violation <= tolerance
    )
    replay = {
        "pass": passed,
        "reason": "accepted" if passed else "independent_primal_replay_failed",
        "maximum_integrality_residual": integrality_residual,
        "maximum_bound_violation": bound_violation,
        "maximum_constraint_violation": constraint_violation,
    }
    return (candidate if passed else None), replay


def add_row(rows: list[dict[int, float]], lower: list[float], upper: list[float], coefficients: dict[int, float], lb: float, ub: float) -> None:
    rows.append({index: value for index, value in coefficients.items() if value != 0.0})
    lower.append(lb)
    upper.append(ub)


def sparse_rows(rows: list[dict[int, float]], variable_count: int):
    data = []
    row_index = []
    column_index = []
    for rid, row in enumerate(rows):
        for column, value in row.items():
            row_index.append(rid)
            column_index.append(column)
            data.append(value)
    return coo_matrix((data, (row_index, column_index)), shape=(len(rows), variable_count)).tocsr()


def build_joint_model(blocks: list[dict], weights: list[float], problem: dict, contract: dict, means: dict[int, tuple[float, float, float]] | None) -> dict:
    n = len(blocks)
    if n != 256:
        raise ValueError("joint model requires the 256-year pool")
    count_offsets = {30: 0, 100: n}
    deviation_offsets = {30: 2 * n, 100: 3 * n}
    centered_offsets = {30: 4 * n, 100: 4 * n + len(ANNUAL_COMPONENTS)}
    variable_count = 4 * n + 2 * len(ANNUAL_COMPONENTS)
    objective = np.zeros(variable_count, dtype=np.float64)
    lower_bounds = np.zeros(variable_count, dtype=np.float64)
    upper_bounds = np.full(variable_count, np.inf, dtype=np.float64)
    threshold = contract["nested_count_constraints"]["positive_weight_threshold"]
    for horizon in (30, 100):
        offset = count_offsets[horizon]
        for index, weight in enumerate(weights):
            upper_bounds[offset + index] = 2.0 if weight > threshold else 0.0
            objective[offset + index] = 1.0e-10 * (index + 1) / n
        objective[deviation_offsets[horizon] : deviation_offsets[horizon] + n] = 1.0
    objective[4 * n :] = 1.0e-6
    integrality = np.zeros(variable_count, dtype=np.uint8)
    integrality[: 2 * n] = 1
    rows: list[dict[int, float]] = []
    lower: list[float] = []
    upper: list[float] = []
    preservation_count = problem["preservation_ub_count"]
    preservation = problem["a_ub"][:preservation_count, :n]
    preservation_bound = problem["b_ub"][:preservation_count]
    for horizon in (30, 100):
        count_offset = count_offsets[horizon]
        deviation_offset = deviation_offsets[horizon]
        for rid in range(preservation_count):
            coefficients = {
                count_offset + index: float(value) / horizon
                for index, value in enumerate(preservation[rid])
                if value != 0.0
            }
            add_row(rows, lower, upper, coefficients, -np.inf, float(preservation_bound[rid]))
        for index, weight in enumerate(weights):
            add_row(
                rows,
                lower,
                upper,
                {count_offset + index: 1.0 / horizon, deviation_offset + index: -1.0},
                -np.inf,
                float(weight),
            )
            add_row(
                rows,
                lower,
                upper,
                {count_offset + index: -1.0 / horizon, deviation_offset + index: -1.0},
                -np.inf,
                -float(weight),
            )
        common = {
            count_offset + index: 1.0
            for index, block in enumerate(blocks)
            if block["calendar_class"] == "common"
        }
        leap = {
            count_offset + index: 1.0
            for index, block in enumerate(blocks)
            if block["calendar_class"] == "leap"
        }
        expected = contract["nested_count_constraints"]["calendar_counts"][str(horizon)]
        add_row(rows, lower, upper, common, expected["common"], expected["common"])
        add_row(rows, lower, upper, leap, expected["leap"], expected["leap"])
    for index in range(n):
        add_row(rows, lower, upper, {index: 1.0, n + index: -1.0}, -np.inf, 0.0)
    solver, _ = a5d1_modules()
    if means is not None:
        for horizon in (30, 100):
            count_offset = count_offsets[horizon]
            centered_offset = centered_offsets[horizon]
            for component_index, name in enumerate(ANNUAL_COMPONENTS):
                raw_name = solver.RAW_COMPONENTS[name]
                raw = np.asarray(
                    [float(block["annual"][raw_name]) for block in blocks],
                    dtype=np.float64,
                )
                target_raw = problem["centered_target_values"][name] + component_mean_product(name, means[horizon])
                scale = problem["scales"][name]
                z = centered_offset + component_index
                positive = {count_offset + index: float(value) / horizon for index, value in enumerate(raw)}
                positive[z] = -scale
                add_row(rows, lower, upper, positive, -np.inf, target_raw)
                negative = {count_offset + index: -float(value) / horizon for index, value in enumerate(raw)}
                negative[z] = -scale
                add_row(rows, lower, upper, negative, -np.inf, -target_raw)
                baseline = abs(
                    problem["centered_baseline_values"][name]
                    - problem["centered_target_values"][name]
                ) / scale
                upper_bounds[z] = baseline + 1.0e-7 + 2.0e-12
            add_row(
                rows,
                lower,
                upper,
                {centered_offset + index: 1.0 for index in range(len(ANNUAL_COMPONENTS))},
                -np.inf,
                0.95
                * math.fsum(
                    abs(problem["centered_baseline_values"][name] - problem["centered_target_values"][name])
                    / problem["scales"][name]
                    for name in ANNUAL_COMPONENTS
                )
                + 2.0e-12,
            )
    matrix = sparse_rows(rows, variable_count)
    return {
        "objective": objective,
        "integrality": integrality,
        "bounds": Bounds(lower_bounds, upper_bounds),
        "constraints": LinearConstraint(matrix, np.asarray(lower), np.asarray(upper)),
        "count_offsets": count_offsets,
        "variable_count": variable_count,
        "constraint_count": len(rows),
    }


def build_single_model(blocks: list[dict], weights: list[float], problem: dict, contract: dict, horizon: int, means: tuple[float, float, float] | None) -> dict:
    n = len(blocks)
    count_offset = 0
    deviation_offset = n
    centered_offset = 2 * n
    variable_count = 2 * n + len(ANNUAL_COMPONENTS)
    objective = np.zeros(variable_count, dtype=np.float64)
    lower_bounds = np.zeros(variable_count, dtype=np.float64)
    upper_bounds = np.full(variable_count, np.inf, dtype=np.float64)
    threshold = contract["nested_count_constraints"]["positive_weight_threshold"]
    for index, weight in enumerate(weights):
        upper_bounds[index] = 2.0 if weight > threshold else 0.0
        objective[index] = 1.0e-10 * (index + 1) / n
    objective[deviation_offset : deviation_offset + n] = 1.0
    objective[centered_offset:] = 1.0e-6
    integrality = np.zeros(variable_count, dtype=np.uint8)
    integrality[:n] = 1
    rows: list[dict[int, float]] = []
    lower: list[float] = []
    upper: list[float] = []
    preservation_count = problem["preservation_ub_count"]
    preservation = problem["a_ub"][:preservation_count, :n]
    preservation_bound = problem["b_ub"][:preservation_count]
    for rid in range(preservation_count):
        add_row(
            rows,
            lower,
            upper,
            {index: float(value) / horizon for index, value in enumerate(preservation[rid]) if value != 0.0},
            -np.inf,
            float(preservation_bound[rid]),
        )
    for index, weight in enumerate(weights):
        add_row(rows, lower, upper, {index: 1.0 / horizon, deviation_offset + index: -1.0}, -np.inf, float(weight))
        add_row(rows, lower, upper, {index: -1.0 / horizon, deviation_offset + index: -1.0}, -np.inf, -float(weight))
    for calendar_class in ("common", "leap"):
        expected = contract["nested_count_constraints"]["calendar_counts"][str(horizon)][calendar_class]
        add_row(
            rows,
            lower,
            upper,
            {index: 1.0 for index, block in enumerate(blocks) if block["calendar_class"] == calendar_class},
            expected,
            expected,
        )
    solver, _ = a5d1_modules()
    if means is not None:
        for component_index, name in enumerate(ANNUAL_COMPONENTS):
            raw_name = solver.RAW_COMPONENTS[name]
            raw = np.asarray([float(block["annual"][raw_name]) for block in blocks], dtype=np.float64)
            target_raw = problem["centered_target_values"][name] + component_mean_product(name, means)
            scale = problem["scales"][name]
            z = centered_offset + component_index
            positive = {index: float(value) / horizon for index, value in enumerate(raw)}
            positive[z] = -scale
            add_row(rows, lower, upper, positive, -np.inf, target_raw)
            negative = {index: -float(value) / horizon for index, value in enumerate(raw)}
            negative[z] = -scale
            add_row(rows, lower, upper, negative, -np.inf, -target_raw)
            baseline = abs(problem["centered_baseline_values"][name] - problem["centered_target_values"][name]) / scale
            upper_bounds[z] = baseline + 1.0e-7 + 2.0e-12
        add_row(
            rows,
            lower,
            upper,
            {centered_offset + index: 1.0 for index in range(len(ANNUAL_COMPONENTS))},
            -np.inf,
            0.95
            * math.fsum(
                abs(problem["centered_baseline_values"][name] - problem["centered_target_values"][name])
                / problem["scales"][name]
                for name in ANNUAL_COMPONENTS
            )
            + 2.0e-12,
        )
    return {
        "objective": objective,
        "integrality": integrality,
        "bounds": Bounds(lower_bounds, upper_bounds),
        "constraints": LinearConstraint(sparse_rows(rows, variable_count), np.asarray(lower), np.asarray(upper)),
        "count_offset": count_offset,
    }


def solve_single_horizon(
    blocks: list[dict],
    weights: list[float],
    problem: dict,
    contract: dict,
    a5d1_contract: dict,
    horizon: int,
    station_deadline: float,
) -> dict:
    seconds = min(
        contract["resource_ceilings"]["count_solver_seconds_per_call"],
        max(0.0, station_deadline - time.monotonic()),
    )
    attempts = []
    if seconds <= 0.0:
        return {
            "horizon": horizon,
            "initial_solver_status": None,
            "initial_solver_success": False,
            "initial_incumbent_present": False,
            "linear_necessary_system_witness": False,
            "exact_witness": None,
            "exact_pass": False,
            "attempts": [
                {
                    "iteration": 0,
                    "stage": "single_linear_necessary",
                    "resource_exhausted_before_call": True,
                }
            ],
        }
    linear_model = build_single_model(blocks, weights, problem, contract, horizon, None)
    linear_result, wall = solve_model(linear_model, seconds)
    linear_candidate, linear_replay = validated_incumbent(linear_result, linear_model)
    initial_attempt = {
        "iteration": 0,
        "stage": "single_linear_necessary",
        "solver": solver_record(linear_result, wall, linear_replay),
    }
    best = None
    if linear_candidate is not None:
        counts = [int(value) for value in linear_candidate[:256]]
        initial = evaluate_single_candidate(
            blocks, weights, problem, contract, a5d1_contract, horizon, counts, 0
        )
        initial_attempt.update(
            {
                "exact_pass": initial["exact_pass"],
                "exact_violation": initial["score"],
            }
        )
        best = initial
    attempts.append(initial_attempt)
    if best is not None and not best["exact_pass"]:
        means = annual_means(blocks, counts, horizon)
        for iteration in range(1, contract["algorithm"]["count_iterations"] + 1):
            seconds = min(
                contract["resource_ceilings"]["count_solver_seconds_per_call"],
                max(0.0, station_deadline - time.monotonic()),
            )
            if seconds <= 0.0:
                attempts.append(
                    {
                        "iteration": iteration,
                        "stage": "single_sequential_centering",
                        "resource_exhausted_before_call": True,
                    }
                )
                break
            model = build_single_model(blocks, weights, problem, contract, horizon, means)
            result, wall = solve_model(model, seconds)
            candidate_vector, candidate_replay = validated_incumbent(result, model)
            attempt = {
                "iteration": iteration,
                "stage": "single_sequential_centering",
                "solver": solver_record(result, wall, candidate_replay),
            }
            if candidate_vector is None:
                attempts.append(attempt)
                break
            counts = [int(value) for value in candidate_vector[:256]]
            candidate = evaluate_single_candidate(
                blocks, weights, problem, contract, a5d1_contract, horizon, counts, iteration
            )
            attempt.update(
                {
                    "exact_pass": candidate["exact_pass"],
                    "exact_violation": candidate["score"],
                }
            )
            attempts.append(attempt)
            if (not best["exact_pass"], best["score"]) > (
                not candidate["exact_pass"],
                candidate["score"],
            ):
                best = candidate
            if candidate["exact_pass"]:
                break
            means = annual_means(blocks, counts, horizon)
    return {
        "horizon": horizon,
        "initial_solver_status": int(linear_result.status),
        "initial_solver_success": bool(linear_result.success),
        "initial_incumbent_present": linear_result.x is not None,
        "linear_necessary_system_witness": linear_candidate is not None,
        "exact_witness": best,
        "exact_pass": bool(best is not None and best["exact_pass"]),
        "attempts": attempts,
    }


def evaluate_single_candidate(
    blocks: list[dict],
    weights: list[float],
    problem: dict,
    contract: dict,
    a5d1_contract: dict,
    horizon: int,
    counts: list[int],
    iteration: int,
) -> dict:
    replay = count_only_replay(problem, blocks, counts, horizon, a5d1_contract)
    calendar_class_counts = {
        value: sum(
            count
            for count, block in zip(counts, blocks)
            if block["calendar_class"] == value
        )
        for value in ("common", "leap")
    }
    invariants = {
        "total": sum(counts) == horizon,
        "maximum_reuse": max(counts) <= 2,
        "positive_support": all(
            count == 0
            or weights[index]
            > contract["nested_count_constraints"]["positive_weight_threshold"]
            for index, count in enumerate(counts)
        ),
        "calendar": calendar_class_counts
        == contract["nested_count_constraints"]["calendar_counts"][str(horizon)],
    }
    exact_pass = all(invariants.values()) and replay["pass"]
    return {
        "counts": counts,
        "replay": replay,
        "invariants": invariants,
        "iteration": iteration,
        "score": replay["violation_objective"],
        "exact_pass": exact_pass,
    }


def solve_model(model: dict, seconds: float):
    started = time.monotonic()
    result = milp(
        model["objective"],
        integrality=model["integrality"],
        bounds=model["bounds"],
        constraints=model["constraints"],
        options={"time_limit": seconds, "mip_rel_gap": 0.0, "presolve": True},
    )
    return result, time.monotonic() - started


def extract_counts(candidate: np.ndarray, model: dict) -> tuple[list[int], list[int]]:
    values = []
    for horizon in (30, 100):
        offset = model["count_offsets"][horizon]
        values.append([int(value) for value in candidate[offset : offset + 256]])
    return values[0], values[1]


def evaluate_joint_candidate(
    blocks: list[dict],
    weights: list[float],
    problem: dict,
    contract: dict,
    a5d1_contract: dict,
    counts30: list[int],
    counts100: list[int],
    iteration: int,
) -> dict:
    validation = validate_counts(
        blocks,
        weights,
        counts30,
        counts100,
        contract["nested_count_constraints"]["positive_weight_threshold"],
    )
    replay30 = count_only_replay(problem, blocks, counts30, 30, a5d1_contract)
    replay100 = count_only_replay(problem, blocks, counts100, 100, a5d1_contract)
    exact_pass = validation["pass"] and replay30["pass"] and replay100["pass"]
    return {
        "counts_30": counts30,
        "counts_100": counts100,
        "validation": validation,
        "replay": {"30": replay30, "100": replay100},
        "iteration": iteration,
        "score": replay30["violation_objective"]
        + replay100["violation_objective"],
        "exact_pass": exact_pass,
    }


def solve_station(station_id: str, contract: dict, a5d1_contract: dict, freeze_sha256: str) -> dict:
    feature = load_json(feature_path(station_id))
    certificate = load_json(certificate_path(station_id))
    if not isinstance(feature, dict) or not isinstance(certificate, dict):
        raise ValueError(f"invalid A5d1 inputs: {station_id}")
    blocks = feature["blocks"][:256]
    weights = [float(value) for value in certificate["weights"]]
    solver, _ = a5d1_modules()
    problem = solver.build_problem(blocks, feature["targets"], a5d1_contract)
    per_call = contract["resource_ceilings"]["count_solver_seconds_per_call"]
    station_started = time.monotonic()
    station_deadline = (
        station_started
        + contract["resource_ceilings"]["count_solver_seconds_per_station"]
    )
    attempts = []
    linear_model = build_joint_model(blocks, weights, problem, contract, None)
    linear_result, linear_wall = solve_model(linear_model, per_call)
    linear_candidate, linear_replay = validated_incumbent(linear_result, linear_model)
    initial_attempt = {
        "stage": "joint_linear_necessary",
        "iteration": 0,
        "solver": solver_record(linear_result, linear_wall, linear_replay),
    }
    best = None
    if linear_candidate is not None:
        counts30, counts100 = extract_counts(linear_candidate, linear_model)
        best = evaluate_joint_candidate(
            blocks,
            weights,
            problem,
            contract,
            a5d1_contract,
            counts30,
            counts100,
            0,
        )
        initial_attempt.update(
            {"exact_pass": best["exact_pass"], "exact_violation": best["score"]}
        )
    attempts.append(initial_attempt)
    if best is not None and not best["exact_pass"]:
        means = {
            30: annual_means(blocks, counts30, 30),
            100: annual_means(blocks, counts100, 100),
        }
        for iteration in range(1, contract["algorithm"]["count_iterations"] + 1):
            seconds = min(per_call, max(0.0, station_deadline - time.monotonic()))
            if seconds <= 0.0:
                attempts.append(
                    {
                        "stage": "joint_sequential_centering",
                        "iteration": iteration,
                        "resource_exhausted_before_call": True,
                    }
                )
                break
            model = build_joint_model(blocks, weights, problem, contract, means)
            result, wall = solve_model(model, seconds)
            candidate_vector, candidate_replay = validated_incumbent(result, model)
            attempt = {
                "stage": "joint_sequential_centering",
                "iteration": iteration,
                "solver": solver_record(result, wall, candidate_replay),
            }
            if candidate_vector is None:
                attempts.append(attempt)
                break
            counts30, counts100 = extract_counts(candidate_vector, model)
            candidate = evaluate_joint_candidate(
                blocks,
                weights,
                problem,
                contract,
                a5d1_contract,
                counts30,
                counts100,
                iteration,
            )
            attempt.update(
                {
                    "exact_pass": candidate["exact_pass"],
                    "exact_violation": candidate["score"],
                }
            )
            attempts.append(attempt)
            if (not best["exact_pass"], best["score"]) > (
                not candidate["exact_pass"],
                candidate["score"],
            ):
                best = candidate
            if candidate["exact_pass"]:
                break
            means = {
                30: annual_means(blocks, counts30, 30),
                100: annual_means(blocks, counts100, 100),
            }
    separate = None
    if best is None or not best["exact_pass"]:
        separate = {
            str(horizon): solve_single_horizon(
                blocks,
                weights,
                problem,
                contract,
                a5d1_contract,
                horizon,
                station_deadline,
            )
            for horizon in (30, 100)
        }
    station_wall = time.monotonic() - station_started
    certificate_value = {
        "count_certificate_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "station_id": station_id,
        "pool_size": 256,
        "source_feature": identity(feature_path(station_id)),
        "source_marginal_certificate": identity(certificate_path(station_id)),
        "solver": {"scipy_version": scipy.__version__, "method": "milp-highs", "attempts": attempts},
        "initial_solver_status": int(linear_result.status),
        "initial_solver_success": bool(linear_result.success),
        "initial_incumbent_present": linear_result.x is not None,
        "linear_necessary_system_witness": linear_candidate is not None,
        "count_witness": best,
        "separate_horizon_diagnostics": separate,
        "count_pass": bool(best is not None and best["exact_pass"]),
        "station_budget_scheduler_pass": station_wall
        <= contract["resource_ceilings"]["count_solver_seconds_per_station"]
        + 1.0,
        "wall_seconds": round(station_wall, 6),
    }
    output = COUNT_DIR / f"{station_id}-nested-count-certificate-v1.json"
    write_json(output, certificate_value)
    return {
        "station_id": station_id,
        "initial_solver_status": certificate_value["initial_solver_status"],
        "initial_solver_success": certificate_value["initial_solver_success"],
        "initial_incumbent_present": certificate_value["initial_incumbent_present"],
        "linear_necessary_system_witness": certificate_value["linear_necessary_system_witness"],
        "count_pass": certificate_value["count_pass"],
        "first_exact_iteration": best["iteration"] if best is not None and best["exact_pass"] else None,
        "certificate": identity(output),
        "station_budget_scheduler_pass": certificate_value[
            "station_budget_scheduler_pass"
        ],
        "wall_seconds": certificate_value["wall_seconds"],
    }


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: solve-count-feasibility.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    a5d1_contract = load_json(A5D1_CONTRACT)
    if not isinstance(contract, dict) or not isinstance(a5d1_contract, dict):
        raise ValueError("invalid count-solver inputs")
    COUNT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    records = [solve_station(station_id, contract, a5d1_contract, freeze_sha256) for station_id in station_ids()]
    status_counts = {
        str(status): sum(row["initial_solver_status"] == status for row in records)
        for status in sorted({row["initial_solver_status"] for row in records})
    }
    separate_summary = {}
    for horizon in (30, 100):
        rows = [
            load_json(ROOT / row["certificate"]["path"])[
                "separate_horizon_diagnostics"
            ][str(horizon)]
            for row in records
            if load_json(ROOT / row["certificate"]["path"])[
                "separate_horizon_diagnostics"
            ]
            is not None
        ]
        separate_summary[str(horizon)] = {
            "attempted_station_count": len(rows),
            "optimal_status_count": sum(
                row["initial_solver_success"] and row["initial_solver_status"] == 0
                for row in rows
            ),
            "incumbent_present_count": sum(
                row["initial_incumbent_present"] for row in rows
            ),
            "linear_necessary_system_witness_count": sum(
                row["linear_necessary_system_witness"] for row in rows
            ),
            "exact_pass_count": sum(row["exact_pass"] for row in rows),
        }
    value = {
        "count_feasibility_results_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "expected_station_count": 17,
        "actual_station_count": len(records),
        "unique_station_count": len({row["station_id"] for row in records}),
        "initial_solver_status_counts": status_counts,
        "initial_solver_optimal_count": sum(
            row["initial_solver_success"] and row["initial_solver_status"] == 0
            for row in records
        ),
        "initial_incumbent_present_count": sum(
            row["initial_incumbent_present"] for row in records
        ),
        "linear_necessary_system_witness_count": sum(row["linear_necessary_system_witness"] for row in records),
        "count_pass_count": sum(row["count_pass"] for row in records),
        "separate_horizon_summary": separate_summary,
        "station_budget_scheduler_pass_count": sum(
            row["station_budget_scheduler_pass"] for row in records
        ),
        "maximum_station_wall_seconds": max(row["wall_seconds"] for row in records),
        "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "peak_rss_unit": "bytes_on_macos",
        "records": records,
        "total_wall_seconds": round(time.monotonic() - started, 6),
    }
    if sys.platform != "darwin":
        value["peak_rss_bytes"] *= 1024
        value["peak_rss_unit"] = "normalized_bytes_from_kibibytes"
    if value["total_wall_seconds"] > contract["resource_ceilings"]["total_wall_seconds"]:
        raise RuntimeError("count solver exceeded total resource ceiling")
    write_json(COUNT_RESULTS, value)
    print(f"A5d1b count matrix: {value['count_pass_count']}/17 exact witnesses")


if __name__ == "__main__":
    main()
