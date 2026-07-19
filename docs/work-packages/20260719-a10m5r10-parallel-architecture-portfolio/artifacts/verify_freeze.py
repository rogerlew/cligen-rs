#!/usr/bin/env python3
"""Verify the prospective A10M5R10 portfolio freeze."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
CONTRACT = PACKAGE / "artifacts/portfolio-contract.json"
CALENDAR = REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json"
R3_RESULTS = (
    REPO
    / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee"
    / "artifacts/toolkit-recovered/evidence/results"
)

CANDIDATES = {
    "monthly_residual_adapter",
    "annual_monthly_residual_adapter",
    "hierarchical_joint_factor_adapter",
    "climate_normal_hierarchical_state_space",
    "physics_conditioned_hierarchical_adapter",
}
CAPACITIES = {"K1": "P1", "K2": "P2"}
SEEDS = [147031, 271828, 314159]
BLOCKS = {
    "monthly_location",
    "monthly_interannual_dispersion",
    "within_month_daily_dispersion",
    "annual_location",
    "annual_interannual_dispersion",
    "wet_occurrence_and_amount",
    "precipitation_temperature_dependence",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def source_model(row: dict[str, Any]) -> dict[str, Any]:
    root = R3_RESULTS / row["row_id"]
    checkpoint = json.loads((root / "checkpoint-record.json").read_text(encoding="utf-8"))
    export = json.loads((root / "export-metadata.json").read_text(encoding="utf-8"))
    return {
        "capacity_id": export["capacity_id"],
        "checkpoint_epoch": checkpoint["epoch"],
        "checkpoint_global_step": checkpoint["global_step"],
        "checkpoint_payload_bytes": checkpoint["payload_bytes"],
        "checkpoint_payload_sha256": checkpoint["payload_sha256"],
        "checkpoint_record_sha256": export["checkpoint_record_sha256"],
        "corpus_cursor_epoch_order_sha256": checkpoint["corpus_cursor"]["epoch_order_sha256"],
        "corpus_cursor_next_batch": checkpoint["corpus_cursor"]["next_batch"],
        "export_sha256": export["export_sha256"],
        "family": export["family"],
        "hidden_size": export["hidden_size"],
        "model_record_sha256": export["model_record_sha256"],
        "parameter_count": export["parameter_count"],
        "training_seed": export["training_seed"],
        "validation_primary_nll": export["validation_primary_nll"],
        "validation_stability": export["validation_stability"],
        "validation_tail_score": export["validation_tail_score"],
    }


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    calendar = json.loads(CALENDAR.read_text(encoding="utf-8"))
    controls = contract["controls"]
    require(set(contract["architectures"]) == CANDIDATES, "candidate set drift")
    require(controls["seeds"] == SEEDS, "seed drift")
    require(
        {
            key: value["accepted_capacity_id"]
            for key, value in controls["capacities"].items()
        }
        == CAPACITIES,
        "capacity mapping drift",
    )
    expected_models = {(capacity, seed) for capacity in CAPACITIES.values() for seed in SEEDS}
    actual_models = {
        (row["capacity_id"], row["training_seed"])
        for row in controls["models"]
    }
    require(actual_models == expected_models and len(controls["models"]) == 6, "control matrix drift")
    for row in controls["models"]:
        expected = source_model(row)
        require(
            all(row[key] == value for key, value in expected.items()),
            f"control identity drift: {row['row_id']}",
        )

    roles = contract["roles"]
    require(len(roles) == 10, "role count drift")
    require(
        {
            (row["architecture"], row["capacity"])
            for row in roles
        }
        == {(candidate, capacity) for candidate in CANDIDATES for capacity in CAPACITIES},
        "role matrix drift",
    )
    require(all(row["seeds"] == SEEDS for row in roles), "role seed drift")
    objective = contract["objective"]
    require(set(objective["climate_blocks"]) == BLOCKS, "climate block drift")
    require(all(weight == 1.0 for weight in objective["climate_blocks"].values()), "block weight drift")
    require(objective["daily_proper_nll_weight"] == 0.2, "NLL weight drift")
    require(objective["paired_daily_pattern_weight"] == 0.0, "daily pattern loss introduced")
    require(contract["stochastic"]["training_members"] == 8, "training-member drift")
    require(contract["stochastic"]["evaluation_members"] == 16, "evaluation-member drift")
    checkpoint = contract["checkpoint"]
    require(
        checkpoint["minimum_epochs"] == 24
        and checkpoint["maximum_epochs"] == 96
        and checkpoint["early_stop_patience"] == 16
        and checkpoint["final_fit_validation_points"] == 240,
        "checkpoint drift",
    )
    selection = checkpoint["selection_scalar"]
    require(
        selection["core_family_balanced_climate_weight"] == 1.0
        and selection["daily_proper_nll_weight"] == 0.2
        and selection["physics_solar_family_weight"] == 0.25
        and selection["physics_solar_term_applies_only_to_physics_candidate"] is True
        and selection["training_regularizers_excluded"]
        == ["latent_stability", "residual_size_and_centering"],
        "checkpoint scalar drift",
    )
    execution = contract["execution"]
    require(
        execution["portfolio_role_count"] == 10
        and execution["portfolio_roles_concurrent"] is True
        and execution["gpus_per_role"] == 1
        and execution["distributed_training"] is False
        and execution["total_gpu_minute_ceiling"] == 935,
        "execution drift",
    )
    physics = contract["architectures"]["physics_conditioned_hierarchical_adapter"]
    require(physics["observed_weather_inputs"] == [], "observed weather input introduced")
    require(physics["fit_validation_target_inputs"] == [], "validation target input introduced")
    require(
        physics["astronomical_envelope"]["inputs"] == ["latitude", "day_of_year"],
        "physics input drift",
    )
    require(contract["pareto"]["maximum_retained"] == 3, "retention ceiling drift")
    require(contract["pareto"]["minimum_retained_for_ready"] == 2, "READY threshold drift")
    require(contract["data_roles"]["fit_validation_gradient"] is False, "validation gradient introduced")
    require(contract["calendar"]["profile_id"] == calendar["profile_id"], "calendar profile drift")
    require(calendar["fit_period_example"]["calendar_axis_rows"] == 10958, "calendar axis drift")
    require(calendar["fit_period_example"]["observed_rows"] == 10950, "calendar observation drift")
    require(calendar["window_example"]["calendar_axis_rows"] == 2922, "window axis drift")
    require(calendar["window_example"]["observed_rows"] == 2920, "window observation drift")
    print("A10M5R10-PORTFOLIO-FREEZE-VERIFIED")


if __name__ == "__main__":
    main()
