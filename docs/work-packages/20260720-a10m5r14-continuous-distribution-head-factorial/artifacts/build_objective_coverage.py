#!/usr/bin/env python3
"""Build or verify the prospective 188-metric objective coverage report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPORT = PACKAGE / "artifacts/objective-selector-coverage.json"


def metric_keys() -> tuple[str, ...]:
    precipitation = (
        "mean", "standard_deviation", "coefficient_of_variation", "skew",
        "dry_frequency", "q10", "q50", "q90", "q95",
    )
    temperature = (
        "tmax_mean", "tmax_standard_deviation", "tmin_mean",
        "tmin_standard_deviation", "tmax_tmin_correlation",
    )
    annual = (
        "precipitation_mean", "precipitation_standard_deviation",
        "precipitation_q95", "tmax_mean", "tmax_standard_deviation",
        "tmin_mean", "tmin_standard_deviation", "precipitation_lag1",
        "tmax_lag1", "tmin_lag1", "precipitation_tmax_correlation",
        "precipitation_tmin_correlation", "tmax_tmin_correlation",
    )
    occurrence = (
        "p_wet_given_wet", "p_wet_given_dry", "wet_spell_survival_3",
        "wet_spell_survival_7", "dry_spell_survival_3",
        "dry_spell_survival_7", "seasonal_wet_frequency_range",
    )
    rows = [f"monthly.{month:02d}.precipitation_{name}" for month in range(1, 13) for name in precipitation]
    rows.extend(f"monthly.{month:02d}.{name}" for month in range(1, 13) for name in temperature)
    rows.extend(f"annual.{name}" for name in annual)
    rows.extend(f"occurrence.{name}" for name in occurrence)
    return tuple(rows)


def scale_kind(key: str) -> str:
    if "precipitation_" in key and any(name in key for name in ("mean", "standard_deviation", "q10", "q50", "q90", "q95")):
        return "log_precipitation"
    if "coefficient_of_variation" in key:
        return "coefficient_of_variation"
    if "skew" in key:
        return "skew"
    if key.startswith("occurrence.") or "dry_frequency" in key:
        return "probability"
    if "correlation" in key or "lag1" in key:
        return "correlation"
    if "tmax_mean" in key or "tmin_mean" in key:
        return "temperature_mean_c"
    if "tmax_standard_deviation" in key or "tmin_standard_deviation" in key:
        return "temperature_standard_deviation_c"
    raise RuntimeError(f"unregistered scale: {key}")


def counterpart(key: str) -> str:
    if "dry_frequency" in key:
        return "smooth_sigmoid_monthly_total_below_1mm"
    if "spell_survival" in key:
        return "continuous_wet_indicator_run_start_survival_ratio"
    if key.startswith("occurrence."):
        return "continuous_wet_indicator_selector_formula"
    return "torch_differentiable_selector_formula"


def required_heads(key: str) -> list[int]:
    if key.startswith("occurrence.") or ".precipitation_" in key:
        return [0, 1, 2]
    if "tmax" in key or "tmin" in key:
        return [3, 4, 5, 6]
    raise RuntimeError(f"unclassified selector metric: {key}")


def build() -> dict:
    rows = []
    access = {
        "A": [0, 1, 3, 5],
        "B": [0, 1, 3, 5],
        "C": [0, 1, 2, 3, 4, 5, 6],
        "D": [0, 1, 2, 3, 4, 5, 6],
    }
    for key in metric_keys():
        needed = required_heads(key)
        rows.append({
            "differentiable": True,
            "metric_key": key,
            "selector_scale": scale_kind(key),
            "training_counterpart": counterpart(key),
            "weather_distribution_head_indices": needed,
            "trainable_head_reachability": {
                arm: {
                    "direct_indices": sorted(set(indices) & set(needed)),
                    "frozen_p2_completes_distribution": True,
                }
                for arm, indices in access.items()
            },
        })
    counts = {
        "annual": sum(row["metric_key"].startswith("annual.") for row in rows),
        "monthly_precipitation": sum("monthly." in row["metric_key"] and ".precipitation_" in row["metric_key"] for row in rows),
        "monthly_temperature": sum("monthly." in row["metric_key"] and ".precipitation_" not in row["metric_key"] for row in rows),
        "occurrence": sum(row["metric_key"].startswith("occurrence.") for row in rows),
        "total": len(rows),
    }
    return {
        "candidate_head_access": {
            "A": {"smooth_uncentered_climatology": False, "centered_scale_ou": False, "trainable_head_indices": access["A"]},
            "B": {"smooth_uncentered_climatology": True, "centered_scale_ou": False, "trainable_head_indices": access["B"]},
            "C": {"smooth_uncentered_climatology": False, "centered_scale_ou": True, "trainable_head_indices": access["C"]},
            "D": {"smooth_uncentered_climatology": True, "centered_scale_ou": True, "trainable_head_indices": access["D"]},
        },
        "counts": counts,
        "daily_proper_nll_weight": 0.0,
        "metric_reduction": "unweighted_mean_of_188_absolute_scaled_metric_residuals",
        "metrics": rows,
        "paired_daily_pattern_weight": 0.0,
        "schema_version": "a10m5r14-objective-selector-coverage-1",
        "selector_contract": "inherited_A10M5R13_temporal_protocol",
        "wet_semantics": "realized_precipitation_ge_1mm_hard_forward_soft_backward",
    }


def verify(value: dict) -> None:
    if value["counts"] != {
        "annual": 13,
        "monthly_precipitation": 108,
        "monthly_temperature": 60,
        "occurrence": 7,
        "total": 188,
    }:
        raise RuntimeError("objective-versus-selector metric counts drift")
    rows = value["metrics"]
    if len(rows) != 188 or len({row["metric_key"] for row in rows}) != 188:
        raise RuntimeError("objective-versus-selector coverage is not bijective")
    if any(not row["differentiable"] or not row["selector_scale"] or not row["training_counterpart"] for row in rows):
        raise RuntimeError("objective-versus-selector coverage field missing")
    if any(set(row["trainable_head_reachability"]) != {"A", "B", "C", "D"} for row in rows):
        raise RuntimeError("candidate head reachability matrix incomplete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    value = build()
    verify(value)
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if args.write:
        REPORT.write_text(payload, encoding="utf-8")
    elif not REPORT.is_file() or REPORT.read_text(encoding="utf-8") != payload:
        raise RuntimeError("committed objective-selector coverage report is stale")
    print("A10M5R14-OBJECTIVE-COVERAGE-PASS")


if __name__ == "__main__":
    main()
