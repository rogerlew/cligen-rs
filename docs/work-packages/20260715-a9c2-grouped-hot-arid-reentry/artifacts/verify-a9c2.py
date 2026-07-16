#!/usr/bin/env python3
"""Verify the executed A9c2 metadata-roster hold and public report."""

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
    def reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"duplicate JSON key {key!r}: {path}")
            value[key] = item
        return value

    value = json.loads(
        path.read_text(),
        object_pairs_hook=reject_duplicate,
        parse_constant=lambda item: (_ for _ in ()).throw(
            ValueError(f"nonfinite JSON value {item}: {path}")
        ),
    )
    require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_bound_records(records: list[dict[str, Any]]) -> None:
    for record in records:
        path = ROOT / record["path"]
        require(path.is_file(), f"missing bound file: {path}")
        require(sha256(path) == record["sha256"], f"bound hash mismatch: {path}")


def main() -> None:
    dispatch = strict_json(ARTIFACTS / "execution-dispatch-v1.json")
    require(dispatch["execution_authorized"] is True, "execution authorization")
    require(dispatch["branch"] == "main" and dispatch["target_branch"] == "main", "branch")
    require(
        dispatch["source_commit"] == "493f8c4cb66f3db2b4eb227d615f33e31b2b5cf7",
        "source commit",
    )

    predecessor = strict_json(ARTIFACTS / "predecessor-manifest-v1.json")
    verify_bound_records(predecessor["files"])
    require(
        predecessor["a9c_historical_terminal"] == "HOLD-A9C-GATE-CALIBRATION",
        "A9c terminal",
    )

    freeze = strict_json(ARTIFACTS / "metadata-roster-freeze-v1.json")
    verify_bound_records(freeze["inputs"])
    require(freeze["frozen_before_inventory_evaluation"] is True, "prospective roster freeze")
    require(freeze["retention_rule"]["minimum_accepted_locations"] == 5, "roster minimum")
    require(freeze["retention_rule"]["accepted_station_cap"] is None, "roster cap")
    require(freeze["retention_rule"]["outcome_based_ranking_or_substitution"] is False, "selection")

    subprocess.run(
        [sys.executable, str(ARTIFACTS / "inventory-a9c2-roster.py")],
        cwd=ROOT,
        check=True,
    )
    roster = strict_json(ARTIFACTS / "hot-arid-roster-inventory-v1.json")
    require(roster["freeze_sha256"] == sha256(ARTIFACTS / "metadata-roster-freeze-v1.json"), "freeze hash")
    require(roster["metadata_base_station_count"] == 113, "metadata base count")
    require(roster["station_listing_row_count"] == 255, "station listing count")
    require(roster["accepted_station_count"] == 2, "accepted count")
    require(
        roster["accepted_station_ids"]
        == ["az_yuma_27_ene", "ca_stovepipe_wells_1_sw"],
        "accepted identities",
    )
    require(roster["missing_required_retained_station_ids"] == [], "required retained sites")
    require(roster["terminal"] == "HOLD-A9C2-HOT-ARID-ROSTER", "terminal")
    require(sum(roster["reason_counts"].values()) == len(roster["rows"]) == 113, "reason arithmetic")
    require(roster["reason_counts"]["passes_all_frozen_metadata_rules"] == 2, "pass count")
    require(roster["reason_counts"]["locked_confirmation_station_id"] == 17, "confirmation exclusions")
    require(
        sum(row["hot_arid_descriptor_match"] for row in roster["rows"]) == 3,
        "hot-arid descriptor match count",
    )
    station_ids = [row["station_id"] for row in roster["rows"]]
    require(len(station_ids) == len(set(station_ids)), "duplicate census station")
    for field in (
        "daily_or_subdaily_station_series_accessed",
        "candidate_development_outputs_accessed",
        "confirmation_series_accessed",
    ):
        require(roster[field] is False, field)

    distances = strict_json(ARTIFACTS / "accepted-site-distances-v1.json")
    require(
        distances["inventory_sha256"]
        == sha256(ARTIFACTS / "hot-arid-roster-inventory-v1.json"),
        "distance inventory hash",
    )
    require(distances["accepted_station_count"] == 2, "distance station count")
    require(distances["pair_count"] == 1, "distance pair count")
    require(
        distances["pairs"]
        == [
            {
                "distance_km": 498.859,
                "station_a": "az_yuma_27_ene",
                "station_b": "ca_stovepipe_wells_1_sw",
            }
        ],
        "accepted pair distance",
    )

    evidence_freeze = strict_json(ARTIFACTS / "report-evidence-freeze-v1.json")
    verify_bound_records(evidence_freeze["canonical_evidence"])
    require(evidence_freeze["report_id"] == "a9c2-hot-arid-roster-feasibility", "report ID")
    require(evidence_freeze["access_history"]["confirmation_series_accessed"] is False, "report access")

    disposition_text = (ARTIFACTS / "post-acceptance-operator-disposition.md").read_text()
    require(
        "Decision: `TWO-SITE-HOT-ARID-EVIDENCE-FUNCTIONALLY-ADEQUATE`"
        in disposition_text,
        "operator disposition",
    )
    require("A9c2 remains `HOLD-A9C2-HOT-ARID-ROSTER`" in disposition_text, "retained hold")
    require("does not authorize A9c3 execution" in disposition_text, "A9c3 authorization")

    package_text = (PACKAGE / "package.md").read_text()
    require("Status: `EXECUTED-HOLD-HOT-ARID-ROSTER`" in package_text, "package status")
    require("Terminal: `HOLD-A9C2-HOT-ARID-ROSTER`" in package_text, "package terminal")
    gate_text = (ARTIFACTS / "execution-gate-results.md").read_text()
    require("Final result: `EXECUTED-HOLD-HOT-ARID-ROSTER`" in gate_text, "gate result")
    catalog_text = (ROOT / "docs/work-packages/README.md").read_text()
    require(
        "| [20260715-a9c2-grouped-hot-arid-reentry]"
        "(20260715-a9c2-grouped-hot-arid-reentry/package.md) | "
        "EXECUTED-HOLD-HOT-ARID-ROSTER |" in catalog_text,
        "work-package catalog",
    )
    roadmap_text = (ROOT / "docs/ROADMAP.md").read_text()
    require("completed on 2026-07-15 with `HOLD-A9C2-HOT-ARID-ROSTER`" in roadmap_text, "roadmap")
    require("functionally adequate" in roadmap_text, "roadmap disposition")
    require("A9c3, a two-site grouped observed-development" in roadmap_text, "A9c3 roadmap")
    require((ARTIFACTS / "post-acceptance-gate-results.md").is_file(), "post-acceptance gates")
    require(not (ARTIFACTS / "large").exists(), "unexpected acquired evidence")
    require(not (ARTIFACTS / "a9c2-objective-registry-v1.json").exists(), "post-hold registry")

    subprocess.run(
        [
            sys.executable,
            "docs/reports/verify-report.py",
            "docs/reports/a9c2-hot-arid-roster-feasibility-report.manifest.json",
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
        ],
        cwd=ROOT,
        check=True,
    )
    attribute = subprocess.check_output(
        [
            "git",
            "check-attr",
            "filter",
            "--",
            str((PACKAGE / "artifacts/large/probe.bin").relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
    )
    require(attribute.rstrip().endswith(": lfs"), "package LFS rule")
    print(
        "PASS: 17 predecessors; 113-site metadata census; 2/5 accepted; "
        "registered roster hold; two-site successor disposition; "
        "zero station-series/candidate/confirmation access; report revision 2 accepted"
    )


if __name__ == "__main__":
    main()
