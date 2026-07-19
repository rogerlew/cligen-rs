#!/usr/bin/env python3
"""Verify the immutable A10M5R4R2R1R2 temporal disposition."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
DECISION = PACKAGE / "temporal-decision.json"
EXPECTED_SHA256 = "d1f877f0dc298f129019dbf7d093de8033f9df10d5a694f3038c9e76b832e0a6"


def main() -> None:
    payload = DECISION.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256
    decision = json.loads(payload)
    assert decision["terminal"] == "HOLD-A10-NO-TEMPORALLY-ELIGIBLE-CAPACITY"
    assert decision["eligible_capacities"] == []
    assert decision["a10m5r5_authorized"] is False
    assert decision["protected_roles_opened"] == []
    assert decision["bootstrap"] == {"replicates": 1000, "seed": 410542}
    assert all(
        not value["temporally_eligible"]
        for value in decision["capacity_decisions"].values()
    )
    assert decision["p2_temporal_preference"] == {
        "bootstrap_probability_reduction_at_least_10_percent": 0.0,
        "preferred": False,
    }
    determinism = json.loads((PACKAGE / "determinism.json").read_text())
    assert determinism["byte_identical"] is True
    assert determinism["scoring_runs"] == 2
    assert determinism["first_output_sha256"] == EXPECTED_SHA256
    assert determinism["second_output_sha256"] == EXPECTED_SHA256
    package_text = (PACKAGE.parent / "package.md").read_text()
    assert "Status: `EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CAPACITY`" in package_text
    roadmap = (ROOT / "docs" / "ROADMAP.md").read_text()
    assert "**Not authorized:** A10M5R5" in roadmap
    print("A10M5R4R2R1R2-RESULT-VERIFIED")


if __name__ == "__main__":
    main()
