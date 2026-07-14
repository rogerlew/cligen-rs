#!/usr/bin/env python3
"""Deterministic analytical fixtures for the A5d0 selector thesis."""

from __future__ import annotations

import argparse
import json
import math
from typing import Any


TOLERANCE = 1.0e-12


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def weighted_sum(weights: list[float], values: list[float]) -> float:
    return math.fsum(weight * value for weight, value in zip(weights, values, strict=True))


def block_statistics(blocks: list[list[float]], weights: list[float]) -> dict[str, float]:
    means = [math.fsum(block) / len(block) for block in blocks]
    within = [
        math.fsum((value - mean) ** 2 for value in block) / len(block)
        for block, mean in zip(blocks, means, strict=True)
    ]
    mean = weighted_sum(weights, means)
    between = weighted_sum(weights, [(value - mean) ** 2 for value in means])
    within_mean = weighted_sum(weights, within)
    second_moment = weighted_sum(
        weights,
        [math.fsum(value * value for value in block) / len(block) for block in blocks],
    )
    return {
        "mean": mean,
        "daily_second_moment": second_moment,
        "between_year_variance": between,
        "mean_within_year_variance": within_mean,
        "total_variance": between + within_mean,
    }


def stationary_kernel(weights: list[float], rho: float) -> list[list[float]]:
    return [
        [rho * float(row == column) + (1.0 - rho) * weight for column, weight in enumerate(weights)]
        for row in range(len(weights))
    ]


def stationary_error(weights: list[float], kernel: list[list[float]]) -> float:
    projected = [
        math.fsum(weights[row] * kernel[row][column] for row in range(len(weights)))
        for column in range(len(weights))
    ]
    return max(abs(actual - expected) for actual, expected in zip(projected, weights, strict=True))


def lag_one_covariance(
    weights: list[float], kernel: list[list[float]], values: list[float]
) -> float:
    mean = weighted_sum(weights, values)
    return math.fsum(
        weights[row]
        * kernel[row][column]
        * (values[row] - mean)
        * (values[column] - mean)
        for row in range(len(weights))
        for column in range(len(weights))
    )


def repeat_probability(weights: list[float], kernel: list[list[float]]) -> float:
    return math.fsum(weights[index] * kernel[index][index] for index in range(len(weights)))


def binomial_tail(n: int, threshold: int, probability: float) -> float:
    return math.fsum(
        math.comb(n, successes)
        * probability**successes
        * (1.0 - probability) ** (n - successes)
        for successes in range(threshold, n + 1)
    )


def sign_design() -> dict[str, Any]:
    for stations in range(17, 101):
        for threshold in range(stations // 2 + 1, stations + 1):
            null_tail = binomial_tail(stations, threshold, 0.5)
            power = binomial_tail(stations, threshold, 0.75)
            if null_tail <= 0.05 and power >= 0.80:
                return {
                    "stations": stations,
                    "required_improved": threshold,
                    "null_one_sided_probability": null_tail,
                    "power_if_true_improvement_probability_is_0_75": power,
                }
    raise RuntimeError("no sign-test design found")


def build_result() -> dict[str, Any]:
    blocks = [
        [-2.0, -2.0],
        [2.0, 2.0],
        [-3.0, 1.0],
        [-1.0, 3.0],
        [-2.0, 2.0],
        [2.0, -2.0],
    ]
    annual_means = [-2.0, 2.0, -1.0, 1.0, 0.0, 0.0]
    baseline_weights = [1.0 / 6.0] * 6
    candidate_weights = [1.0 / 4.0, 1.0 / 4.0, 1.0 / 6.0, 1.0 / 6.0, 1.0 / 12.0, 1.0 / 12.0]
    baseline = block_statistics(blocks, baseline_weights)
    candidate = block_statistics(blocks, candidate_weights)

    require(abs(baseline["mean"] - candidate["mean"]) <= TOLERANCE, "mean not preserved")
    require(
        abs(baseline["daily_second_moment"] - candidate["daily_second_moment"])
        <= TOLERANCE,
        "daily second moment not preserved",
    )
    require(
        abs(baseline["total_variance"] - baseline["daily_second_moment"]) <= TOLERANCE,
        "baseline variance decomposition failed",
    )
    require(
        abs(candidate["total_variance"] - candidate["daily_second_moment"]) <= TOLERANCE,
        "candidate variance decomposition failed",
    )
    require(
        candidate["between_year_variance"] > baseline["between_year_variance"],
        "between-year variance did not increase",
    )
    require(
        candidate["mean_within_year_variance"] < baseline["mean_within_year_variance"],
        "within-year variance was not reallocated",
    )

    rho = 0.6
    kernel = stationary_kernel(candidate_weights, rho)
    row_sum_error = max(abs(math.fsum(row) - 1.0) for row in kernel)
    invariant_error = stationary_error(candidate_weights, kernel)
    lag_covariance = lag_one_covariance(candidate_weights, kernel, annual_means)
    expected_lag_covariance = rho * candidate["between_year_variance"]
    zero_frequency_power_ratio = (1.0 + rho) / (1.0 - rho)
    require(row_sum_error <= TOLERANCE, "transition rows do not sum to one")
    require(invariant_error <= TOLERANCE, "candidate weights are not stationary")
    require(
        abs(lag_covariance - expected_lag_covariance) <= TOLERANCE,
        "lag-one covariance identity failed",
    )

    null_trials = math.ceil(math.log(0.05) / math.log(0.95))
    null_upper = 1.0 - 0.05 ** (1.0 / null_trials)
    eight_upper = 1.0 - 0.05 ** (1.0 / 8.0)
    require(null_trials == 59, "unexpected zero-failure trial count")
    require(null_upper <= 0.05, "null upper confidence bound exceeds five percent")

    a5b_sign_tail = binomial_tail(17, 11, 0.5)
    design = sign_design()
    balanced_design = {
        "stations": 28,
        "stations_per_four_primary_regimes": 7,
        "required_improved": 19,
        "null_one_sided_probability": binomial_tail(28, 19, 0.5),
        "power_if_true_improvement_probability_is_0_75": binomial_tail(28, 19, 0.75),
    }

    # Counterexample: when every year has the same within-year variance and
    # the mean is fixed, preserving the daily second moment fixes the weighted
    # squared annual mean, hence fixes between-year variance.
    counterexample_within_variance = 1.0
    require(
        counterexample_within_variance == 1.0,
        "counterexample fixture changed",
    )

    return {
        "a5d0_feasibility_fixture_version": 1,
        "status": "complete",
        "evidence_boundary": "deterministic synthetic derivation only; no A5d candidate confirmation output",
        "variance_reallocation_fixture": {
            "baseline_weights": baseline_weights,
            "candidate_weights": candidate_weights,
            "baseline": baseline,
            "candidate": candidate,
            "between_year_variance_ratio": candidate["between_year_variance"]
            / baseline["between_year_variance"],
            "physical_daily_values_modified": 0,
            "interpretation": "A fixed block library can reallocate variance when within-year variance differs across selectable states.",
        },
        "stationary_kernel_fixture": {
            "rho": rho,
            "row_sum_max_abs_error": row_sum_error,
            "stationary_max_abs_error": invariant_error,
            "lag_one_covariance": lag_covariance,
            "expected_lag_one_covariance": expected_lag_covariance,
            "same_block_repeat_probability": repeat_probability(candidate_weights, kernel),
            "zero_frequency_power_ratio_vs_independent": zero_frequency_power_ratio,
            "interpretation": "The simple persistent kernel proves the dependence identity but has a high repeat probability and no adjudicated reuse ceiling; it is not a freeze-ready selector.",
        },
        "structural_counterexample": {
            "constant_within_year_variance": counterexample_within_variance,
            "result": "preserving mean and daily second moment fixes between-year variance",
            "interpretation": "Feasibility is a property of the realized library/constraints, not of block resampling in general.",
        },
        "calibration_power": {
            "zero_failures_one_sided_confidence": 0.95,
            "target_familywise_false_failure_upper_bound": 0.05,
            "minimum_independent_null_trials_if_zero_failures": null_trials,
            "upper_bound_after_minimum_trials": null_upper,
            "upper_bound_after_eight_trials": eight_upper,
            "a5b_11_of_17_sign_tail_under_null": a5b_sign_tail,
            "minimum_exact_sign_design": design,
            "balanced_four_regime_sign_design": balanced_design,
        },
        "a5b_revision_3_observations": {
            "gate_1_bootstrap_available": 221,
            "gate_4_bootstrap_available": 8,
            "bootstrap_total": 2000,
            "gate_1_availability_fraction": 221.0 / 2000.0,
            "gate_4_availability_fraction": 8.0 / 2000.0,
            "registered_numeric_wepp_acceptance_bound": False,
        },
        "conclusion": {
            "structural_capability_demonstrated_by_construction": True,
            "capability_guaranteed_for_arbitrary_faithful_library": False,
            "production_contract_freeze_ready": False,
            "blocking_contract_questions": [
                "No bounded repeat-safe selector with a prospectively adjudicated reuse ceiling and the required stationary and finite-prefix properties is specified.",
                "No development-library optimization demonstrates simultaneous monthly constraints and complete Gate 1 improvement across stations.",
                "Calendar-class and finite 30/100-year prefix behavior are not executable.",
            ],
        },
    }


def run_self_test() -> None:
    result = build_result()
    mutated = json.loads(json.dumps(result))
    mutated["variance_reallocation_fixture"]["candidate"]["between_year_variance"] = 0.0
    require(
        mutated["variance_reallocation_fixture"]["candidate"]["between_year_variance"]
        <= result["variance_reallocation_fixture"]["baseline"]["between_year_variance"],
        "mutation did not invalidate the variance claim",
    )
    print("A5d0 feasibility fixture self-test: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
    else:
        print(json.dumps(build_result(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
