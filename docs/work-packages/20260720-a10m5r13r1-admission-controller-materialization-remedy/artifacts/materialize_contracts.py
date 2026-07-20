#!/usr/bin/env python3
"""Materialize R13 contracts from the exact R12R1 parent authorities."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

PARENT_PORTFOLIO_SHA256 = "48816017dece30684406a2e571e8b6fd1ae47df6e104b4caefbed369ea9619c1"
PARENT_TEMPORAL_SHA256 = "07cb797dde3a69ce87abd6add94f7d51b5e78723aae74129110a1a07da50ff71"
SEEDS = [147031, 271828, 314159]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_exact(path: Path, expected: str) -> dict:
    if digest(path) != expected:
        raise RuntimeError(f"parent contract identity mismatch: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def portfolio(parent: dict) -> dict:
    value = copy.deepcopy(parent)
    value.update({
        "package_id": "20260720-a10m5r13-selector-aligned-continuous-hierarchy",
        "specification": "A10M5R13-package-science-contract",
    })
    architectures = {}
    for name, shared in (
        ("selector_aligned_continuous_hierarchy", False),
        ("selector_aligned_shared_slow_climate_state", True),
    ):
        architectures[name] = copy.deepcopy(parent["architectures"]["continuous_hierarchical_latent_process"])
        architectures[name]["selector_aligned_annual_objective"] = True
        architectures[name]["explicit_rank_one_shared_slow_factor"] = shared
        architectures[name]["decoder_head_semantics"] = [
            "precipitation_occurrence", "positive_amount_location",
            "temperature_mean_location", "log_dtr_location",
        ]
        architectures[name]["additional_ou_state_dimension"] = 0
    value["architectures"] = architectures
    value["roles"] = [
        {"role_id": "selector-aligned-continuous-hierarchy-k2", "architecture": "selector_aligned_continuous_hierarchy", "capacity": "K2", "seeds": SEEDS},
        {"role_id": "selector-aligned-shared-slow-climate-state-k2", "architecture": "selector_aligned_shared_slow_climate_state", "capacity": "K2", "seeds": SEEDS},
    ]
    value["capacity_shapes"]["K2"]["candidate_parameter_ceiling"] = 340000
    value["calendar"]["representative_window"] = {
        "start_inclusive": "1980-01-01",
        "end_exclusive": "1996-01-01",
        "axis_rows": 5844,
        "core_observed_rows": 5840,
        "eligible_origins_per_point": 13,
    }
    value["stochastic"]["window_calendar_years"] = 16
    value["objective"]["climate_blocks"].pop("annual_location")
    value["objective"]["climate_blocks"].pop("annual_interannual_dispersion")
    value["objective"]["climate_blocks"].update({name: 1.0 for name in (
        "annual_location", "annual_dispersion", "annual_lag",
        "annual_cross_field_dependence",
    )})
    value["execution"].update({
        "portfolio_role_minutes_each": 240,
        "total_gpu_minute_ceiling": 515,
    })
    value["evidence_profile"] = {
        "path": "research/a10/lemhi_toolkit/profiles/lemhi-v2-large-evidence.json",
        "sha256": "fba24ee726285f2a0cba55d69ed9c4949145ac072514bc8e31ee4941d55d0b45",
    }
    value["terminals"] = {
        "ready": "A10M5R13-TEMPORAL-READY",
        "single": "A10M5R13-TEMPORAL-READY",
        "none": "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
    }
    return value


def temporal(parent: dict) -> dict:
    value = copy.deepcopy(parent)
    value["contract_id"] = "a10m5r13-selector-aligned-continuous-hierarchy-v1"
    value["predecessor_terminal"] = "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"
    value["roles"] = [
        {"role_id": "selector-aligned-continuous-hierarchy-k2", "configuration_id": "selector_aligned_continuous_hierarchy-k2", "architecture": "selector_aligned_continuous_hierarchy", "capacity": "K2", "backbone_capacity": "P2", "seeds": SEEDS},
        {"role_id": "selector-aligned-shared-slow-climate-state-k2", "configuration_id": "selector_aligned_shared_slow_climate_state-k2", "architecture": "selector_aligned_shared_slow_climate_state", "capacity": "K2", "backbone_capacity": "P2", "seeds": SEEDS},
    ]
    value["resources"].update({
        "candidate_role_count": 2,
        "candidate_minutes_each": 240,
        "gpu_minute_ceiling": 515,
        "maximum_concurrent_candidates": 2,
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
