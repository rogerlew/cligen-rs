#!/usr/bin/env python3
"""Replay the frozen A10M5R8 terminal decision from committed evidence."""

from __future__ import annotations

import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
CONTRACT = REPO / "docs/work-packages/20260719-a10m5r8-climate-statistics-objective/artifacts/climate-objective-contract.json"


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    evidence = json.loads((PACKAGE / "artifacts/comparison-summary.json").read_text(encoding="utf-8"))
    control = evidence["arms"]["proper_nll_control"]
    treatment = evidence["arms"]["climate_statistics_treatment"]
    limits = contract["decision"]
    improvement = 1.0 - treatment["family_balanced_climate_score"] / control["family_balanced_climate_score"]
    blocks = {
        name: treatment["block_scores"][name]
        <= (1.0 + limits["maximum_block_degradation_fraction"]) * control["block_scores"][name]
        for name in control["block_scores"]
    }
    nll = treatment["daily_proper_nll"] <= (
        1.0 + limits["maximum_daily_nll_degradation_fraction"]
    ) * control["daily_proper_nll"]
    advances = bool(
        control["support"] and treatment["support"]
        and improvement >= limits["minimum_climate_score_improvement_fraction"]
        and all(blocks.values()) and nll
    )
    decision = evidence["decision"]
    if abs(improvement - decision["climate_score_improvement_fraction"]) > 1e-15:
        raise RuntimeError("improvement replay mismatch")
    if blocks != decision["block_non_degradation"] or nll != decision["daily_proper_nll_guard"]:
        raise RuntimeError("guard replay mismatch")
    if advances != decision["advances"] or decision["terminal"] != "HOLD-A10M5R8-CORE-OBJECTIVE-NOT-SUPPORTED":
        raise RuntimeError("terminal replay mismatch")
    if evidence["protected_roles_opened"] != [] or evidence["fit_validation_points"] != 240:
        raise RuntimeError("surface replay mismatch")
    print("A10M5R8R3-RESULT-VERIFIED")


if __name__ == "__main__":
    main()
