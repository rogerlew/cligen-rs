#!/usr/bin/env python3
"""Verify the frozen A10M5R8 contract and executable sources locally."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
JOBS = PACKAGE / "artifacts/jobs"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    contract = json.loads((PACKAGE / "artifacts/climate-objective-contract.json").read_text(encoding="utf-8"))
    require(contract["fields"] == ["prcp", "tmax", "tmin"], "core field boundary drift")
    require(contract["objective"]["paired_daily_error_weight"] == 0.0, "paired-day loss is prohibited")
    require(contract["objective"]["daily_proper_nll_weight"] < contract["objective"]["climate_block_weight"], "climate objective must dominate")
    require(contract["stochastic"]["window_calendar_years"] == 8, "calendar window drift")
    require(contract["stochastic"]["minimum_observed_days_per_year_month"] == 28, "missingness support drift")
    require(contract["decision"]["minimum_climate_score_improvement_fraction"] == 0.15, "decision threshold drift")
    required = {
        "build_control_records.py", "climate_core.py", "experiment.py", "job-climate-objective.sh",
        "prepare_assets.py", "run_experiment.sh",
    }
    require(required == {path.name for path in JOBS.iterdir() if path.is_file()}, "job source roster drift")
    for path in JOBS.glob("*.py"):
        py_compile.compile(str(path), doraise=True)
    for path in JOBS.glob("*.sh"):
        subprocess.run(["sh", "-n", str(path)], check=True)
    source = (JOBS / "climate_core.py").read_text(encoding="utf-8")
    require("climate_components" in source and "annual_interannual_dispersion" in source, "dispersion implementation absent")
    require("paired_daily" not in source, "paired daily climate loss leaked into implementation")
    # The full self-test imports pinned remote NumPy/PyTorch dependencies and is
    # therefore executed after canonical environment reconstruction on Lemhi.
    print("A10M5R8-FREEZE-VERIFIED")


if __name__ == "__main__":
    main()
