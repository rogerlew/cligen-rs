#!/usr/bin/env python3
"""Verify the prospective A9c3 scaffold before candidate-blind calibration."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
ARTIFACTS = PACKAGE / "artifacts"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def strict_json(path: Path) -> dict[str, Any]:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"duplicate key {key!r}: {path}")
            value[key] = item
        return value

    value = json.loads(
        path.read_text(),
        object_pairs_hook=object_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"nonfinite token {token}: {path}")
        ),
    )
    require(isinstance(value, dict), f"object root required: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    dispatch = strict_json(ARTIFACTS / "execution-dispatch-v1.json")
    require(dispatch["execution_authorized"] is True, "execution authorization")
    require(dispatch["branch"] == "main", "starting branch")
    require(dispatch["target_branch"] == "main", "target branch")
    require(
        dispatch["source_commit"] == "a0e24f0866f4536c168bfd809cb957d91e6d8bf3",
        "source commit",
    )

    predecessor = strict_json(ARTIFACTS / "predecessor-manifest-v1.json")
    for record in predecessor["files"]:
        path = ROOT / record["path"]
        require(path.is_file(), f"missing predecessor: {path}")
        require(sha256(path) == record["sha256"], f"predecessor hash: {path}")
    require(
        predecessor["historical_terminals"]
        == {
            "a9c": "HOLD-A9C-GATE-CALIBRATION",
            "a9c2": "HOLD-A9C2-HOT-ARID-ROSTER",
        },
        "historical terminals",
    )

    freeze = strict_json(ARTIFACTS / "design-freeze-v1.json")
    grouped = freeze["grouped_storm_amendment"]
    require(
        grouped["observed_sites"] == ["az_yuma_27_ene", "ca_stovepipe_wells_1_sw"],
        "two-site identities",
    )
    require(
        grouped["site_weights"]
        == {"az_yuma_27_ene": 0.5, "ca_stovepipe_wells_1_sw": 0.5},
        "equal weights",
    )
    require(grouped["actual_event_frequencies_preserved"] is True, "event frequency")
    require(grouped["arbitrary_station_event_floors"] is False, "support floors")
    amendment = ARTIFACTS / "grouped-storm-objective-amendment-v1.json"
    require(
        sha256(amendment) == grouped["objective_amendment_sha256"],
        "objective amendment",
    )
    evaluator = freeze["objective_evaluator"]
    require(
        sha256(ROOT / evaluator["path"]) == evaluator["sha256"],
        "objective evaluator",
    )
    require(
        sum(len(sites) for sites in grouped["generated_contributors"].values()) == 20,
        "generated contributor count",
    )
    require(len(grouped["generated_contributors"]) == 6, "generated strata")
    require(
        freeze["precision_power_diagnostic"]["selection_role"].startswith("diagnostic"),
        "power role",
    )
    require(
        freeze["all_family_threshold_calibration"]["threshold_count"] == 14,
        "threshold count",
    )
    require(
        freeze["monthly_reconciliation"]["terminal"]
        == "HOLD-A9C3-MONTHLY-RECONCILIATION",
        "monthly terminal",
    )
    require(
        freeze["stage_promotion"]["ties"] == "ascending configuration_id",
        "promotion tie",
    )
    require(
        freeze["confirmation_series_access_allowed"] is False, "confirmation firewall"
    )
    require(len(freeze["stages"]) == 4, "stage count")
    require(freeze["horizons_years"] == [30, 100], "horizons")

    roles = strict_json(
        ROOT
        / "docs/work-packages/20260715-a9c-observed-development/artifacts/data-role-manifest-v1.json"
    )
    require(
        roles["confirmation_access_state"] == "metadata_only",
        "confirmation access state",
    )

    for forbidden in (
        "grouped-calibration-v1.json",
        "fit-execution-v1.json",
        "evaluation-v1.json",
        "candidate-freeze-v1.json",
    ):
        require(
            not (ARTIFACTS / forbidden).exists(),
            f"outcome exists before scaffold gate: {forbidden}",
        )

    subprocess.run(
        [
            sys.executable,
            "docs/work-packages/20260715-a9b-calibration-harness/artifacts/verify-a9b-replay.py",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            dispatch["source_commit"],
            "--",
            "crates",
            "reference/cligen532",
            "research/a9c",
            "research/a9_harness",
        ],
        cwd=ROOT,
        check=True,
    )
    print(
        "PASS: A9c3 prospective two-site grouped design; exact predecessors; "
        "A9b replay; zero candidate outcome; confirmation prohibited"
    )


if __name__ == "__main__":
    main()
