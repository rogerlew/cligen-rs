#!/usr/bin/env python3
"""Solve and independently replay the frozen A5d1 marginal LPs."""

from __future__ import annotations

import math
import sys
import time

import numpy as np
import scipy
from scipy.optimize import linprog

from a5d1_common import (
    CERTIFICATE_DIR,
    CONTRACT,
    FEATURE_DIR,
    FEATURE_MANIFEST,
    MARGINAL_RESULTS,
    MONTH_NAMES,
    freeze_identity,
    load_json,
    relative,
    sha256,
    station_records,
    write_json,
)


ANNUAL_COMPONENTS = [
    "precip_total_mm.variance",
    "tmax_mean_c.variance",
    "tmin_mean_c.variance",
    "precip_total_mm_x_tmax_mean_c.covariance",
    "precip_total_mm_x_tmin_mean_c.covariance",
    "tmax_mean_c_x_tmin_mean_c.covariance",
]
RAW_COMPONENTS = {
    "precip_total_mm.variance": "precip_total_mm.raw_second_moment",
    "tmax_mean_c.variance": "tmax_mean_c.raw_second_moment",
    "tmin_mean_c.variance": "tmin_mean_c.raw_second_moment",
    "precip_total_mm_x_tmax_mean_c.covariance": "precip_total_mm_x_tmax_mean_c.raw_cross_moment",
    "precip_total_mm_x_tmin_mean_c.covariance": "precip_total_mm_x_tmin_mean_c.raw_cross_moment",
    "tmax_mean_c_x_tmin_mean_c.covariance": "tmax_mean_c_x_tmin_mean_c.raw_cross_moment",
}


def vector(blocks: list[dict], getter) -> np.ndarray:
    return np.asarray([float(getter(block)) for block in blocks], dtype=np.float64)


def uniform_value(values: np.ndarray) -> float:
    return float(np.mean(values))


def add_upper(
    rows: list[np.ndarray], bounds: list[float], coefficient: np.ndarray, bound: float
) -> None:
    rows.append(coefficient)
    bounds.append(float(bound))


def add_ratio_bounds(
    rows: list[np.ndarray],
    bounds: list[float],
    numerator: np.ndarray,
    denominator: np.ndarray,
    lower: float,
    upper: float,
    variable_count: int,
) -> None:
    high = np.zeros(variable_count)
    high[: len(numerator)] = numerator - upper * denominator
    add_upper(rows, bounds, high, 0.0)
    low = np.zeros(variable_count)
    low[: len(numerator)] = -numerator + lower * denominator
    add_upper(rows, bounds, low, 0.0)


def relative_interval(value: float, tolerance: float) -> tuple[float, float]:
    scale = max(abs(value), 1.0e-12)
    return value - tolerance * scale, value + tolerance * scale


def centered_values(blocks: list[dict], weights: np.ndarray) -> dict[str, float]:
    p = vector(blocks, lambda block: block["annual"]["precip_total_mm"])
    x = vector(blocks, lambda block: block["annual"]["tmax_mean_c"])
    t = vector(blocks, lambda block: block["annual"]["tmin_mean_c"])
    p_mean, x_mean, t_mean = float(weights @ p), float(weights @ x), float(weights @ t)
    return {
        "precip_total_mm.variance": float(weights @ (p * p)) - p_mean * p_mean,
        "tmax_mean_c.variance": float(weights @ (x * x)) - x_mean * x_mean,
        "tmin_mean_c.variance": float(weights @ (t * t)) - t_mean * t_mean,
        "precip_total_mm_x_tmax_mean_c.covariance": float(weights @ (p * x)) - p_mean * x_mean,
        "precip_total_mm_x_tmin_mean_c.covariance": float(weights @ (p * t)) - p_mean * t_mean,
        "tmax_mean_c_x_tmin_mean_c.covariance": float(weights @ (x * t)) - x_mean * t_mean,
    }


def build_problem(blocks: list[dict], targets: dict, contract: dict) -> dict:
    n = len(blocks)
    m = len(ANNUAL_COMPONENTS)
    variable_count = n + m
    rows: list[np.ndarray] = []
    bounds: list[float] = []
    mtol = contract["monthly_tolerances"]
    utol = contract["unparameterized_tolerances"]

    for month_name in MONTH_NAMES:
        month_target = targets["monthly_station_surface"][month_name]
        month = lambda block: block["monthly"][month_name]
        days = vector(blocks, lambda block: month(block)["days"])
        wet = vector(blocks, lambda block: month(block)["wet_days"])
        wet_sum = vector(blocks, lambda block: month(block)["wet_sum"])
        wet_sq = vector(blocks, lambda block: month(block)["wet_sq_sum"])
        add_ratio_bounds(
            rows, bounds, wet, days,
            month_target["wet_fraction"] - mtol["precipitation_wet_fraction_absolute"],
            month_target["wet_fraction"] + mtol["precipitation_wet_fraction_absolute"],
            variable_count,
        )
        lower, upper = relative_interval(
            month_target["wet_mean_mm"], mtol["precipitation_wet_mean_relative"]
        )
        add_ratio_bounds(rows, bounds, wet_sum, wet, lower, upper, variable_count)
        lower, upper = relative_interval(
            month_target["wet_raw_second_mm2"],
            mtol["precipitation_wet_raw_second_relative"],
        )
        add_ratio_bounds(rows, bounds, wet_sq, wet, lower, upper, variable_count)
        dry_pred = vector(blocks, lambda block: month(block)["dry_predecessors"])
        wet_after_dry = vector(blocks, lambda block: month(block)["wet_after_dry"])
        add_ratio_bounds(
            rows, bounds, wet_after_dry, dry_pred,
            max(0.0, month_target["wet_given_dry"] - mtol["precipitation_transition_probability_absolute"]),
            min(1.0, month_target["wet_given_dry"] + mtol["precipitation_transition_probability_absolute"]),
            variable_count,
        )
        wet_pred = vector(blocks, lambda block: month(block)["wet_predecessors"])
        wet_after_wet = vector(blocks, lambda block: month(block)["wet_after_wet"])
        add_ratio_bounds(
            rows, bounds, wet_after_wet, wet_pred,
            max(0.0, month_target["wet_given_wet"] - mtol["precipitation_transition_probability_absolute"]),
            min(1.0, month_target["wet_given_wet"] + mtol["precipitation_transition_probability_absolute"]),
            variable_count,
        )
        for variable in ("tmax", "tmin"):
            total = vector(blocks, lambda block, v=variable: month(block)[f"{v}_sum"])
            square = vector(blocks, lambda block, v=variable: month(block)[f"{v}_sq_sum"])
            mean_target = month_target[f"{variable}_mean_c"]
            add_ratio_bounds(
                rows, bounds, total, days,
                mean_target - mtol["temperature_mean_c_absolute"],
                mean_target + mtol["temperature_mean_c_absolute"],
                variable_count,
            )
            raw_target = month_target[f"{variable}_raw_second_c2"]
            lower, upper = relative_interval(
                raw_target, mtol["temperature_raw_second_scale_relative"]
            )
            add_ratio_bounds(rows, bounds, square, days, lower, upper, variable_count)

        for bin_name in ("bin_0_1", "bin_1_5", "bin_5_20", "bin_20_inf"):
            numerator = vector(blocks, lambda block, b=bin_name: month(block)[b])
            wet_reference = uniform_value(wet)
            if wet_reference <= 0.0:
                raise ValueError(f"uniform wet-day denominator is zero: {month_name}")
            reference = uniform_value(numerator) / wet_reference
            tolerance = utol["precipitation_bin_fraction_absolute"]
            add_ratio_bounds(
                rows, bounds, numerator, wet,
                max(0.0, reference - tolerance),
                min(1.0, reference + tolerance),
                variable_count,
            )
        for cross_name in ("p_tmax_sum", "p_tmin_sum", "tmax_tmin_sum"):
            numerator = vector(blocks, lambda block, c=cross_name: month(block)[c])
            reference = uniform_value(numerator) / uniform_value(days)
            lower, upper = relative_interval(
                reference, utol["daily_cross_raw_moment_relative"]
            )
            add_ratio_bounds(rows, bounds, numerator, days, lower, upper, variable_count)
        for descriptor in ("duration", "time_to_peak", "peak_ratio"):
            for suffix in ("sum", "sq_sum"):
                numerator = vector(
                    blocks, lambda block, d=descriptor, s=suffix: month(block)[f"{d}_{s}"]
                )
                wet_reference = uniform_value(wet)
                if wet_reference <= 0.0:
                    raise ValueError(f"uniform wet-day denominator is zero: {month_name}")
                reference = uniform_value(numerator) / wet_reference
                lower, upper = relative_interval(
                    reference, utol["storm_descriptor_raw_moment_relative"]
                )
                add_ratio_bounds(rows, bounds, numerator, wet, lower, upper, variable_count)

    p = vector(blocks, lambda block: block["annual"]["precip_total_mm"])
    x = vector(blocks, lambda block: block["annual"]["tmax_mean_c"])
    t = vector(blocks, lambda block: block["annual"]["tmin_mean_c"])
    preservation = contract["preservation"]
    for values, tolerance, relative_tolerance in (
        (p, 0.0, preservation["annual_mean_precipitation_relative"]),
        (x, preservation["annual_mean_temperature_c_absolute"], 0.0),
        (t, preservation["annual_mean_temperature_c_absolute"], 0.0),
    ):
        reference = uniform_value(values)
        delta = tolerance + relative_tolerance * abs(reference)
        coefficients = np.zeros(variable_count)
        coefficients[:n] = values
        add_upper(rows, bounds, coefficients, reference + delta)
        add_upper(rows, bounds, -coefficients, -(reference - delta))

    preservation_ub_count = len(rows)
    uniform_weights = np.full(n, 1.0 / n)
    baseline_means = {
        "precip_total_mm": uniform_value(p),
        "tmax_mean_c": uniform_value(x),
        "tmin_mean_c": uniform_value(t),
    }
    centered_target_values = targets["annual_daymet_centered_targets"]
    centered_baseline_values = centered_values(blocks, uniform_weights)
    target_values = {
        "precip_total_mm.variance": baseline_means["precip_total_mm"] ** 2
        + centered_target_values["precip_total_mm.variance"],
        "tmax_mean_c.variance": baseline_means["tmax_mean_c"] ** 2
        + centered_target_values["tmax_mean_c.variance"],
        "tmin_mean_c.variance": baseline_means["tmin_mean_c"] ** 2
        + centered_target_values["tmin_mean_c.variance"],
        "precip_total_mm_x_tmax_mean_c.covariance": baseline_means["precip_total_mm"]
        * baseline_means["tmax_mean_c"]
        + centered_target_values["precip_total_mm_x_tmax_mean_c.covariance"],
        "precip_total_mm_x_tmin_mean_c.covariance": baseline_means["precip_total_mm"]
        * baseline_means["tmin_mean_c"]
        + centered_target_values["precip_total_mm_x_tmin_mean_c.covariance"],
        "tmax_mean_c_x_tmin_mean_c.covariance": baseline_means["tmax_mean_c"]
        * baseline_means["tmin_mean_c"]
        + centered_target_values["tmax_mean_c_x_tmin_mean_c.covariance"],
    }
    baseline_values = {
        name: uniform_value(
            vector(blocks, lambda block, key=RAW_COMPONENTS[name]: block["annual"][key])
        )
        for name in ANNUAL_COMPONENTS
    }
    scales = {
        name: max(
            abs(centered_target_values[name] - centered_baseline_values[name]),
            1.0e-8
            * max(abs(centered_target_values[name]), abs(centered_baseline_values[name]), 1.0),
        )
        for name in ANNUAL_COMPONENTS
    }
    objective = np.zeros(variable_count)
    for index, name in enumerate(ANNUAL_COMPONENTS):
        values = vector(
            blocks, lambda block, key=RAW_COMPONENTS[name]: block["annual"][key]
        )
        target = target_values[name]
        scale = scales[name]
        auxiliary = n + index
        objective[auxiliary] = 1.0
        upper_positive = np.zeros(variable_count)
        upper_positive[:n] = values / scale
        upper_positive[auxiliary] = -1.0
        add_upper(rows, bounds, upper_positive, target / scale)
        upper_negative = np.zeros(variable_count)
        upper_negative[:n] = -values / scale
        upper_negative[auxiliary] = -1.0
        add_upper(rows, bounds, upper_negative, -target / scale)
        baseline_distance = abs(baseline_values[name] - target) / scale
        noninferior_positive = np.zeros(variable_count)
        noninferior_positive[:n] = values / scale
        add_upper(rows, bounds, noninferior_positive, target / scale + baseline_distance + 1e-7)
        noninferior_negative = np.zeros(variable_count)
        noninferior_negative[:n] = -values / scale
        add_upper(rows, bounds, noninferior_negative, -target / scale + baseline_distance + 1e-7)

    a_eq = np.zeros((5, variable_count))
    a_eq[0, :n] = 1.0
    a_eq[1, :n] = p
    a_eq[2, :n] = x
    a_eq[3, :n] = t
    a_eq[4, :n] = np.asarray(
        [block["calendar_class"] == "leap" for block in blocks], dtype=np.float64
    )
    b_eq = np.asarray(
        [
            1.0,
            baseline_means["precip_total_mm"],
            baseline_means["tmax_mean_c"],
            baseline_means["tmin_mean_c"],
            contract["calendar"]["stationary_leap_weight"],
        ]
    )
    return {
        "objective": objective,
        "a_ub": np.vstack(rows),
        "b_ub": np.asarray(bounds),
        "a_eq": a_eq,
        "b_eq": b_eq,
        "bounds": [(0.0, contract["marginal_solver"]["max_weight"])] * n
        + [(0.0, None)] * m,
        "baseline_values": baseline_values,
        "target_values": target_values,
        "centered_baseline_values": centered_baseline_values,
        "centered_target_values": centered_target_values,
        "scales": scales,
        "baseline_means": baseline_means,
        "preservation_ub_count": preservation_ub_count,
        "january_transition_target": {
            name: targets["monthly_station_surface"]["jan"][name]
            for name in ("wet_given_dry", "wet_given_wet")
        },
    }


def finite_prefix_replay(
    problem: dict, blocks: list[dict], indices: list[int], horizon: int, contract: dict
) -> dict:
    weights = np.zeros(len(blocks), dtype=np.float64)
    for index in indices[:horizon]:
        weights[index] += 1.0 / horizon
    variables = np.concatenate((weights, np.zeros(len(ANNUAL_COMPONENTS))))
    count = problem["preservation_ub_count"]
    residuals = problem["a_ub"][:count] @ variables - problem["b_ub"][:count]
    row_scales = np.maximum(
        1.0,
        np.maximum(
            np.abs(problem["b_ub"][:count]),
            np.max(np.abs(problem["a_ub"][:count]), axis=1),
        ),
    )
    centered = centered_values(blocks, weights)
    components = {
        name: abs(centered[name] - problem["centered_target_values"][name])
        / problem["scales"][name]
        for name in ANNUAL_COMPONENTS
    }
    baseline_components = {
        name: abs(
            problem["centered_baseline_values"][name]
            - problem["centered_target_values"][name]
        )
        / problem["scales"][name]
        for name in ANNUAL_COMPONENTS
    }
    aggregate = math.fsum(components.values())
    baseline_aggregate = math.fsum(baseline_components.values())
    guard = 2.0e-12
    noninferiority = all(
        components[name] <= baseline_components[name] + 1.0e-7 + guard
        for name in ANNUAL_COMPONENTS
    )
    strict_improvement = aggregate <= 0.95 * baseline_aggregate + guard
    ordering_violations = sum(
        blocks[index]["monthly"][month]["temperature_ordering_violations"]
        for index in indices[:horizon]
        for month in MONTH_NAMES
    )
    preservation_pass = float(np.max(residuals)) <= contract["marginal_solver"][
        "independent_replay_tolerance"
    ]
    within_january_counts = {
        name: sum(
            blocks[index]["monthly"]["jan"][name]
            for index in indices[:horizon]
        )
        for name in (
            "dry_predecessors",
            "wet_after_dry",
            "wet_predecessors",
            "wet_after_wet",
        )
    }
    boundary_january_counts = {
        "dry_predecessors": 0,
        "wet_after_dry": 0,
        "wet_predecessors": 0,
        "wet_after_wet": 0,
    }
    for left, right in zip(indices[:horizon - 1], indices[1:horizon]):
        predecessor_wet = bool(blocks[left]["last_day_wet"])
        destination_wet = bool(blocks[right]["first_day_wet"])
        if predecessor_wet:
            boundary_january_counts["wet_predecessors"] += 1
            boundary_january_counts["wet_after_wet"] += int(destination_wet)
        else:
            boundary_january_counts["dry_predecessors"] += 1
            boundary_january_counts["wet_after_dry"] += int(destination_wet)
    transition_tolerance = contract["monthly_tolerances"][
        "precipitation_transition_probability_absolute"
    ]
    january = {}
    january_excesses = []
    for name, numerator_name, denominator_name in (
        ("wet_given_dry", "wet_after_dry", "dry_predecessors"),
        ("wet_given_wet", "wet_after_wet", "wet_predecessors"),
    ):
        within_denominator = within_january_counts[denominator_name]
        within_numerator = within_january_counts[numerator_name]
        boundary_denominator = boundary_january_counts[denominator_name]
        boundary_numerator = boundary_january_counts[numerator_name]
        denominator = within_denominator + boundary_denominator
        numerator = within_numerator + boundary_numerator
        actual = numerator / denominator if denominator else None
        target = problem["january_transition_target"][name]
        lower = max(0.0, target - transition_tolerance)
        upper = min(1.0, target + transition_tolerance)
        passed = actual is not None and lower <= actual <= upper
        excess = (
            max(lower - actual, actual - upper, 0.0)
            if actual is not None
            else 1.0
        )
        january_excesses.append(excess)
        january[name] = {
            "boundary": {
                "actual": boundary_numerator / boundary_denominator
                if boundary_denominator
                else None,
                "denominator": boundary_denominator,
                "numerator": boundary_numerator,
                "role": "diagnostic_only",
            },
            "combined": {
                "actual": actual,
                "denominator": denominator,
                "numerator": numerator,
                "pass": passed,
            },
            "lower": lower,
            "pass": passed,
            "target": target,
            "upper": upper,
            "within_block": {
                "actual": within_numerator / within_denominator
                if within_denominator
                else None,
                "denominator": within_denominator,
                "numerator": within_numerator,
            },
        }
    january_pass = all(value["pass"] for value in january.values())
    preservation_pass = preservation_pass and january_pass
    violation = float(np.sum(np.maximum(residuals / row_scales, 0.0)))
    violation += math.fsum(january_excesses)
    violation += math.fsum(
        max(0.0, components[name] - baseline_components[name] - 1.0e-7 - guard)
        for name in ANNUAL_COMPONENTS
    )
    violation += max(0.0, aggregate - 0.95 * baseline_aggregate - guard)
    violation += float(ordering_violations)
    return {
        "horizon": horizon,
        "preservation_maximum_residual": float(np.max(residuals)),
        "preservation_pass": preservation_pass,
        "january_transition": {
            "pass": january_pass,
            "probabilities": january,
        },
        "centered_target_values": problem["centered_target_values"],
        "centered_actual_values": centered,
        "baseline_components": baseline_components,
        "actual_components": components,
        "baseline_aggregate": baseline_aggregate,
        "actual_aggregate": aggregate,
        "noninferiority": noninferiority,
        "strict_improvement": strict_improvement,
        "temperature_ordering_violations": ordering_violations,
        "pass": preservation_pass
        and noninferiority
        and strict_improvement
        and ordering_violations == contract["preservation"]["temperature_ordering_violations"],
        "violation_objective": violation,
    }


def solve_one(station_id: str, pool_size: int, contract: dict, freeze_sha256: str) -> dict:
    feature_path = FEATURE_DIR / f"{station_id}-year-features-v1.json"
    feature = load_json(feature_path)
    if not isinstance(feature, dict) or feature["freeze_sha256"] != freeze_sha256:
        raise ValueError(f"feature identity mismatch: {station_id}")
    blocks = feature["blocks"][:pool_size]
    problem = build_problem(blocks, feature["targets"], contract)
    started = time.monotonic()
    result = linprog(
        problem["objective"],
        A_ub=problem["a_ub"],
        b_ub=problem["b_ub"],
        A_eq=problem["a_eq"],
        b_eq=problem["b_eq"],
        bounds=problem["bounds"],
        method="highs",
        options={"time_limit": contract["resource_ceilings"]["solver_seconds_per_station_pool"]},
    )
    tie_status = None
    if result.success:
        optimum = float(result.fun)
        tie_row = np.asarray([problem["objective"]])
        tie_bound = np.asarray([optimum + 1.0e-9])
        tie_objective = np.zeros_like(problem["objective"])
        tie_objective[:pool_size] = np.arange(1, pool_size + 1, dtype=np.float64) / pool_size
        tied = linprog(
            tie_objective,
            A_ub=np.vstack((problem["a_ub"], tie_row)),
            b_ub=np.concatenate((problem["b_ub"], tie_bound)),
            A_eq=problem["a_eq"],
            b_eq=problem["b_eq"],
            bounds=problem["bounds"],
            method="highs",
            options={"time_limit": contract["resource_ceilings"]["solver_seconds_per_station_pool"]},
        )
        tie_status = {
            "status": int(tied.status),
            "message": tied.message,
            "success": bool(tied.success),
        }
        solution = tied.x if tied.success else result.x
    else:
        optimum = None
        solution = np.concatenate((np.full(pool_size, 1.0 / pool_size), np.zeros(6)))
    wall_seconds = time.monotonic() - started
    solver_success = bool(result.success and tie_status is not None and tie_status["success"])
    weights = solution[:pool_size]
    ub_residual = problem["a_ub"] @ solution - problem["b_ub"]
    eq_residual = problem["a_eq"] @ solution - problem["b_eq"]
    actual_values = {}
    for name in ANNUAL_COMPONENTS:
        values = vector(
            blocks, lambda block, key=RAW_COMPONENTS[name]: block["annual"][key]
        )
        actual_values[name] = float(weights @ values)
    actual_centered_values = centered_values(blocks, weights)
    component_distances = {
        name: abs(
            actual_centered_values[name] - problem["centered_target_values"][name]
        )
        / problem["scales"][name]
        for name in ANNUAL_COMPONENTS
    }
    baseline_distances = {
        name: abs(
            problem["centered_baseline_values"][name]
            - problem["centered_target_values"][name]
        )
        / problem["scales"][name]
        for name in ANNUAL_COMPONENTS
    }
    actual_distance = math.fsum(component_distances.values())
    baseline_distance = math.fsum(baseline_distances.values())
    independent_replay_pass = (
        solver_success
        and float(np.max(ub_residual)) <= 2.0e-7
        and float(np.max(np.abs(eq_residual))) <= 2.0e-9
        and abs(float(np.sum(weights)) - 1.0) <= 2.0e-9
        and float(np.min(weights)) >= -1.0e-10
        and float(np.max(weights)) <= contract["marginal_solver"]["max_weight"] + 1.0e-9
    )
    strict_improvement = actual_distance <= 0.95 * baseline_distance + 1.0e-7
    noninferiority = all(
        component_distances[name] <= baseline_distances[name] + 1.0e-7 + 2.0e-12
        for name in ANNUAL_COMPONENTS
    )
    passed = independent_replay_pass and strict_improvement and noninferiority
    certificate = {
        "marginal_certificate_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "station_id": station_id,
        "pool_size": pool_size,
        "solver": {
            "scipy_version": scipy.__version__,
            "method": "highs",
            "status": int(result.status),
            "message": result.message,
            "success": bool(result.success),
            "tie_break": tie_status,
            "objective": optimum,
            "wall_seconds": round(wall_seconds, 6),
        },
        "weights": [float(value) for value in weights],
        "effective_support_inverse_simpson": float(1.0 / np.sum(weights * weights)),
        "maximum_weight": float(np.max(weights)),
        "positive_weight_count": int(np.sum(weights > contract["marginal_solver"]["positive_weight_threshold"])),
        "leap_weight_mass": float(
            np.sum(
                weights[
                    np.asarray(
                        [block["calendar_class"] == "leap" for block in blocks],
                        dtype=bool,
                    )
                ]
            )
        ),
        "constraint_count": int(problem["a_ub"].shape[0] + problem["a_eq"].shape[0]),
        "maximum_inequality_residual": float(np.max(ub_residual)),
        "maximum_equality_residual": float(np.max(np.abs(eq_residual))),
        "annual": {
            "target_values": problem["target_values"],
            "baseline_values": problem["baseline_values"],
            "actual_values": actual_values,
            "centered_target_values": problem["centered_target_values"],
            "centered_baseline_values": problem["centered_baseline_values"],
            "centered_actual_values": actual_centered_values,
            "scales": problem["scales"],
            "baseline_component_distances": baseline_distances,
            "actual_component_distances": component_distances,
            "baseline_aggregate_distance": baseline_distance,
            "actual_aggregate_distance": actual_distance,
            "strict_improvement": strict_improvement,
            "noninferiority": noninferiority,
        },
        "independent_replay_pass": independent_replay_pass,
        "marginal_pass": passed,
        "first_failed_criterion": next(
            (
                name
                for name, value in (
                    ("solver_status_and_tie_break", solver_success),
                    ("independent_residual_replay", independent_replay_pass),
                    ("component_noninferiority", noninferiority),
                    ("aggregate_strict_improvement", strict_improvement),
                )
                if not value
            ),
            None,
        ),
    }
    output = CERTIFICATE_DIR / f"{station_id}-pool-{pool_size}-marginal-certificate-v1.json"
    write_json(output, certificate)
    return {
        "station_id": station_id,
        "pool_size": pool_size,
        "marginal_pass": passed,
        "first_failed_criterion": certificate["first_failed_criterion"],
        "certificate": {"path": relative(output), "sha256": sha256(output)},
        "actual_aggregate_distance": actual_distance,
        "baseline_aggregate_distance": baseline_distance,
        "wall_seconds": round(wall_seconds, 6),
    }


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: solve-selector-feasibility.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    manifest = load_json(FEATURE_MANIFEST)
    if not isinstance(contract, dict) or not isinstance(manifest, dict):
        raise ValueError("invalid solver inputs")
    if manifest["freeze_sha256"] != freeze_sha256:
        raise ValueError("feature manifest freeze mismatch")
    CERTIFICATE_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for pool_size in contract["pool_sizes"]:
        for station in station_records():
            records.append(solve_one(station["station_id"], pool_size, contract, freeze_sha256))
    value = {
        "marginal_results_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "contract_sha256": sha256(CONTRACT),
        "feature_manifest_sha256": sha256(FEATURE_MANIFEST),
        "cell_count": len(records),
        "pass_count": sum(row["marginal_pass"] for row in records),
        "records": records,
    }
    write_json(MARGINAL_RESULTS, value)
    print(f"A5d1 marginal LPs: {value['pass_count']}/{len(records)} pass")


if __name__ == "__main__":
    main()
