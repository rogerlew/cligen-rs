#!/usr/bin/env python3
"""Verify the closed A9c4 completeness-hold evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "docs/work-packages/20260715-a9c4-context-support-completeness"
ARTIFACTS = PACKAGE / "artifacts"
A9C3 = ROOT / "docs/work-packages/20260715-a9c3-two-site-grouped-observed-comparison/artifacts"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    design = load(ARTIFACTS / "design-freeze-v1.json")
    predecessor = load(ARTIFACTS / "predecessor-manifest-v1.json")
    audit_path = ARTIFACTS / "availability-audit-v1.json"
    audit = load(audit_path)
    mask = load(ARTIFACTS / "evidence-mask-v1.json")
    for row in predecessor["files"]:
        assert sha256(ROOT / row["path"]) == row["sha256"], row["path"]
    assert audit["design_freeze_sha256"] == sha256(
        ARTIFACTS / "design-freeze-v1.json"
    )
    assert audit["predecessor_manifest_sha256"] == sha256(
        ARTIFACTS / "predecessor-manifest-v1.json"
    )
    assert mask["audit_sha256"] == sha256(audit_path)
    cells = audit["cells"]
    keys = {
        (row["objective_id"], row["stratum"], row["horizon_years"])
        for row in cells
    }
    assert len(cells) == len(keys) == audit["source_specific_cell_count"] == 111
    retained = [row for row in cells if row["retained_in_candidate_blind_mask"]]
    excluded = [row for row in cells if not row["retained_in_candidate_blind_mask"]]
    assert len(retained) == audit["retained_cell_count"] == 92
    assert len(excluded) == audit["excluded_cell_count"] == 19
    assert len(mask["retained_cells"]) == 92
    assert len(mask["excluded_cells"]) == 19
    assert all(
        row["observed_available_station_count"]
        == row["faithful_all_burn_available_station_count"]
        for row in cells
        if row["family"] != "storm_descriptor"
    )
    assert all(row["observed_available_station_count"] < 2 for row in excluded)
    assert mask["candidate_inputs_used"] is False
    missing = {
        (row["family"], row["stratum"])
        for row in mask["breadth_guard"]["missing_family_strata"]
    }
    assert missing == {
        (family, stratum)
        for family in ("compound_context", "wet_amount")
        for stratum in ("arid_boundary", "hot_arid", "monsoonal_transition")
    }
    assert mask["breadth_guard"]["status"] == "fail"
    assert mask["status"] == "hold"
    assert mask["terminal_if_hold"] == "HOLD-A9C4-COMPLETENESS-SURFACE"

    short = next(
        row
        for row in load(A9C3 / "evaluation-v1.json")["stages"]
        if row["stage"] == "short_screen"
    )
    expected = {
        (result["configuration_id"], row["objective_id"], row["stratum"]): row
        for result in short["results"]
        for row in result["objective_rows"]
        if row["selection_role"] == "mandatory"
    }
    statuses = []
    count_discrepancies = []
    for cell in cells:
        for identifier, status in cell["historical_a9c3_status"].items():
            accepted = expected[(identifier, cell["objective_id"], cell["stratum"])]
            statuses.append(status)
            assert status == accepted["status"]
            stored = cell["historical_a9c3_joint_available_station_count"][identifier]
            if stored != accepted["available_station_count"]:
                count_discrepancies.append((identifier, cell["objective_id"], cell["stratum"]))
    assert len(statuses) == 666
    assert statuses.count("available") == 552
    assert statuses.count("unavailable") == 114
    storm_status_count = sum(
        len(row["historical_a9c3_status"])
        for row in cells
        if row["family"] == "storm_descriptor"
    )
    assert storm_status_count == 144
    assert len(statuses) - storm_status_count == 522
    assert len(count_discrepancies) == 96
    assert all(
        next(
            row for row in cells
            if row["objective_id"] == objective and row["stratum"] == stratum
        )["family"]
        == "storm_descriptor"
        for _, objective, stratum in count_discrepancies
    )
    assert audit["a9c3_status_reproduction"] == {
        "mismatch_count": 0,
        "status": "pass",
    }
    assert design["confirmation_series_access_allowed"] is False
    assert not (ARTIFACTS / "fit-execution-v1.json").exists()
    assert not (ARTIFACTS / "evaluation-v1.json").exists()
    assert not (ARTIFACTS / "candidate-freeze-v1.json").exists()
    print(
        "A9c4 verified: 111 cells = 92 retained + 19 report-only; "
        "six breadth failures; 522 non-storm statuses recomputed; 144 storm "
        "statuses inherited; 96 disclosed storm-count labels; "
        "HOLD-A9C4-COMPLETENESS-SURFACE"
    )


if __name__ == "__main__":
    main()
