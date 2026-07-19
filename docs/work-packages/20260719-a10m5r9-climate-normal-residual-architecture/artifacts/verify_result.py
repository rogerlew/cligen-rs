#!/usr/bin/env python3
"""Verify the committed A10M5R9 result and prospective decision."""

from __future__ import annotations

import json
import math
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)


def main() -> None:
    result = json.loads(
        (PACKAGE / "artifacts/comparison-summary.json").read_text(encoding="utf-8")
    )
    arms = result["arms"]
    baseline = arms["climate_normal_baseline"]
    residual = arms["climate_normal_plus_residual"]
    p1 = arms["accepted_p1_context"]
    decision = result["decision"]

    dispersion_keys = (
        "annual_interannual_dispersion",
        "monthly_interannual_dispersion",
    )
    baseline_dispersion = sum(baseline["block_scores"][key] for key in dispersion_keys) / 2
    residual_dispersion = sum(residual["block_scores"][key] for key in dispersion_keys) / 2
    dispersion_improvement = 1 - residual_dispersion / baseline_dispersion
    climate_improvement = 1 - (
        residual["family_balanced_climate_score"]
        / baseline["family_balanced_climate_score"]
    )
    require(close(dispersion_improvement, decision["dispersion_improvement_fraction"]), "dispersion delta drift")
    require(close(climate_improvement, decision["climate_score_improvement_fraction"]), "climate delta drift")
    require(dispersion_improvement >= 0.15, "dispersion gate should pass")
    require(climate_improvement < 0.05, "climate gate should fail")
    require(
        all(
            residual["block_scores"][key] <= 1.1 * value
            for key, value in baseline["block_scores"].items()
        ),
        "baseline block guard drift",
    )
    require(residual["daily_proper_nll"] <= 1.1 * baseline["daily_proper_nll"], "baseline NLL guard drift")
    require(residual["family_balanced_climate_score"] > p1["family_balanced_climate_score"], "P1 climate guard should fail")
    require(residual["daily_proper_nll"] > 1.1 * p1["daily_proper_nll"], "P1 NLL guard should fail")
    require(result["training"]["residual"]["baseline_state_sha256_before"] == result["training"]["residual"]["baseline_state_sha256_after"], "baseline mutation")
    require(result["calendar"]["valid"] is True, "calendar preflight failed")
    require(result["evidence"]["protected_roles_opened"] == [], "protected role opened")
    require(decision["advances"] is False and decision["selected_arm"] == "none", "selection drift")
    require(decision["terminal"] == "HOLD-A10M5R9-RESIDUAL-ARCHITECTURE-NOT-SUPPORTED", "terminal drift")
    print("A10M5R9-RESULT-VERIFIED")


if __name__ == "__main__":
    main()
