#!/usr/bin/env python3
"""Fail closed on the prospective A10M5R7 scaffold."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
R4 = REPO / "docs/work-packages/20260718-a10m5r4r2-realized-temporal-adjudication"
R4_REMEDY = REPO / "docs/work-packages/20260718-a10m5r4r2r1-reconstruction-identity-remedy"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


contract = json.loads((PACKAGE / "artifacts/diagnostic-contract.json").read_text(encoding="utf-8"))
assert contract["diagnostic"]["modes"] == [
    "accepted_open_loop",
    "observation_conditioned",
    "generated_feedback",
]
assert contract["diagnostic"]["groups"] == [
    "monthly_climatology",
    "precipitation_distribution",
    "occurrence_spells",
    "temperature",
    "annual_dependence",
]
assert contract["full_temporal"]["bootstrap_seed"] == 410542
assert contract["full_temporal"]["bootstrap_replicates"] == 1000
assert contract["full_temporal"]["median_regime_ratio_upper_90_percent_limit"] == 1.25
assert contract["full_temporal"]["maximum_regime_ratio_limit"] == 1.5
assert contract["protected_roles_opened"] == []
assert len(json.loads((R4_REMEDY / "artifacts/reconstruction-contract.json").read_text())["models"]) == 6
assert digest(R4 / "artifacts/sites.json") == "f8415f74143f37e07b9936b4c3ecdc0a08908fc32b285e523c63ccfe12ad71dd"
for name in ("probe.py", "score.py", "prepare_assets.py"):
    compile((PACKAGE / "artifacts/jobs" / name).read_text(encoding="utf-8"), name, "exec")
assert "EXPECTED_COMPARATOR_TREE" in (PACKAGE / "artifacts/jobs/score.py").read_text(encoding="utf-8")
print("A10M5R7-FREEZE-READY")
