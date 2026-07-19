#!/usr/bin/env python3
"""Verify the prospective A10M5R9 architecture and calendar freeze."""

from __future__ import annotations

import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    contract = json.loads((PACKAGE / "artifacts/architecture-contract.json").read_text(encoding="utf-8"))
    calendar = json.loads((REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json").read_text(encoding="utf-8"))
    architecture = contract["architecture"]
    residual = architecture["residual"]
    require(contract["arms"] == ["accepted_p1_context", "climate_normal_baseline", "climate_normal_plus_residual"], "arm drift")
    require(architecture["training_seed"] == 147031, "seed drift")
    require(architecture["baseline"]["regime_cells"] == 6 and architecture["baseline"]["monthly_cells"] == 12, "baseline surface drift")
    require(residual["latent_dim"] == 6 and residual["state_step"] == "calendar_month", "residual state drift")
    require(residual["head_indices"] == [0, 1, 3, 5], "residual decoder drift")
    require(residual["center_innovations_across_members"] is True, "innovation centering drift")
    require(contract["objective"]["paired_daily_error_weight"] == 0.0, "paired daily error introduced")
    require(contract["roles"]["fit_validation_gradient"] is False, "validation gradient drift")
    require(contract["stochastic"] == {"evaluation_members": 8, "relaxed_wet_temperature": 0.5, "training_members": 4}, "member drift")
    require(contract["calendar"]["profile_id"] == calendar["profile_id"] == "daymet_official_365_v1", "calendar identity drift")
    require(calendar["fit_period_example"]["calendar_axis_rows"] == 10958, "fit axis drift")
    require(calendar["fit_period_example"]["observed_rows"] == 10950, "fit observations drift")
    require(calendar["window_example"]["calendar_axis_rows"] == 2922, "window axis drift")
    require(calendar["window_example"]["observed_rows"] == 2920, "window observations drift")
    require(all(date.endswith("-12-31") for date in calendar["fit_period_example"]["unobserved_dates"]), "Daymet missing-date drift")
    require(contract["successor"]["requires_core_architecture_ready"] is True, "solar gate drift")
    print("A10M5R9-FREEZE-VERIFIED")


if __name__ == "__main__":
    main()
