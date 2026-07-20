#!/usr/bin/env python3
"""Materialize R14 contracts from the exact executed R13 authorities."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

PARENT_PORTFOLIO_SHA256 = "c3ab065b1ba94d68ade314863e390909fe9d73286396f3b4f0192675eb11259b"
PARENT_TEMPORAL_SHA256 = "e207c89332c0a712325d592dfeef543b7a12d59100ddf9bda3ab32fd67bc4277"
PACKAGE_ID = "20260720-a10m5r14-continuous-distribution-head-factorial"
SEEDS = [147031, 271828, 314159]
ROLES = (
    ("continuous-location-ou-k2", "centered_location_ou", False, False),
    ("continuous-location-ou-smooth-climatology-k2", "centered_location_ou_smooth_climatology", True, False),
    ("continuous-location-scale-ou-k2", "centered_location_and_scale_ou", False, True),
    ("continuous-location-scale-ou-smooth-climatology-k2", "centered_location_and_scale_ou_smooth_climatology", True, True),
)
PARAMETER_COUNTS = {
    "centered_location_ou": 278667,
    "centered_location_ou_smooth_climatology": 278747,
    "centered_location_and_scale_ou": 279819,
    "centered_location_and_scale_ou_smooth_climatology": 279899,
}


def aligned_metric_keys() -> list[str]:
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
    keys = [f"monthly.{month:02d}.precipitation_{name}" for month in range(1, 13) for name in precipitation]
    keys.extend(f"monthly.{month:02d}.{name}" for month in range(1, 13) for name in temperature)
    keys.extend(f"annual.{name}" for name in annual)
    keys.extend(f"occurrence.{name}" for name in occurrence)
    if len(keys) != 188:
        raise RuntimeError("aligned metric registry drift")
    return keys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_exact(path: Path, expected: str) -> dict:
    if digest(path) != expected:
        raise RuntimeError(f"parent contract identity mismatch: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def architecture(parent: dict, climatology: bool, scale: bool) -> dict:
    value = copy.deepcopy(parent["architectures"]["selector_aligned_continuous_hierarchy"])
    value.update({
        "centered_scale_ou": scale,
        "deterministic_climatology_context": [
            "sin_day_of_year", "cos_day_of_year", "latitude", "longitude", "elevation",
        ] if climatology else [],
        "deterministic_climatology_head_indices": [0, 1, 3, 5] if climatology else [],
        "deterministic_climatology_member_centered": False if climatology else None,
        "deterministic_climatology_basis": "bias_free_5_by_4_outer_product_20_to_4" if climatology else None,
        "deterministic_climatology_parameter_count": 80 if climatology else 0,
        "differentiable_selector_metric_count": 188,
        "location_ou_head_indices": [0, 1, 3, 5],
        "scale_ou_head_indices": [2, 4, 6] if scale else [],
    })
    return value


def portfolio(parent: dict) -> dict:
    value = copy.deepcopy(parent)
    value["package_id"] = PACKAGE_ID
    value["specification"] = "A10M5R14-package-science-contract"
    value["architectures"] = {
        name: architecture(parent, climatology, scale)
        for _, name, climatology, scale in ROLES
    }
    for name, count in PARAMETER_COUNTS.items():
        value["architectures"][name]["parameter_count"] = count
    value["roles"] = [
        {"role_id": role, "architecture": name, "capacity": "K2", "seeds": SEEDS}
        for role, name, _, _ in ROLES
    ]
    value["capacity_shapes"]["K2"]["candidate_parameter_ceiling"] = 340000
    value["objective"].update({
        "aligned_metric_count": 188,
        "aligned_metric_reduction": "unweighted_mean_absolute_scaled_residual",
        "checkpoint_uses_same_aligned_components": True,
        "wet_semantics": "exact_hard_forward_relaxed_soft_backward",
        "fixed_regularization_registry": {
            "state_terms_summed_once": ["medium_daily_states", "slow_daily_states"],
            "offset_terms_summed": ["location_ou_offsets", "scale_ou_offsets", "climatology_offsets"],
            "absent_factor_value": 0.0,
        },
    })
    value["objective"]["climate_blocks"] = {
        key: 1.0 for key in aligned_metric_keys()
    }
    value["execution"].update({
        "portfolio_role_count": 4,
        "portfolio_role_minutes_each": 240,
        "portfolio_roles_concurrent": True,
        "total_gpu_minute_ceiling": 995,
    })
    value["evidence_profile"] = {
        "path": "research/a10/lemhi_toolkit/profiles/lemhi-v2-xlarge-evidence.json",
        "sha256": "ebf36a6cda19491a00bf6f56ec64cec30ca28f60eaa2b07fa5bd92dd8c668629",
    }
    value["terminals"] = {
        "ready": "A10M5R14-TEMPORAL-READY",
        "single": "A10M5R14-TEMPORAL-READY",
        "none": "HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
    }
    return value


def temporal(parent: dict) -> dict:
    value = copy.deepcopy(parent)
    value["contract_id"] = "a10m5r14-continuous-distribution-head-factorial-v1"
    value["predecessor_terminal"] = "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"
    value["roles"] = [
        {
            "role_id": role, "configuration_id": f"{name}-k2",
            "architecture": name, "capacity": "K2", "backbone_capacity": "P2",
            "seeds": SEEDS,
        }
        for role, name, _, _ in ROLES
    ]
    value["resources"].update({
        "candidate_role_count": 4,
        "candidate_minutes_each": 240,
        "gpu_jobs": 5,
        "gpu_minute_ceiling": 995,
        "maximum_concurrent_candidates": 4,
    })
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-portfolio", type=Path, required=True)
    parser.add_argument("--parent-temporal", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write(args.output_dir / "portfolio-contract.json", portfolio(load_exact(args.parent_portfolio, PARENT_PORTFOLIO_SHA256)))
    write(args.output_dir / "temporal-contract.json", temporal(load_exact(args.parent_temporal, PARENT_TEMPORAL_SHA256)))


if __name__ == "__main__":
    main()
