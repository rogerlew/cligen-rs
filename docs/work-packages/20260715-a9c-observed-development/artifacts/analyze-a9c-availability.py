#!/usr/bin/env python3
"""Apply the frozen A9 storm-objective availability rules before ranking."""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
ARTIFACTS = PACKAGE / "artifacts"
SOURCE = ARTIFACTS / "observed-source-manifest-v1.json"
REGISTRY = ROOT / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts/objective-registry-v1.json"
OUTPUT = ARTIFACTS / "gate-calibration-availability-v1.json"
FIT_INVENTORY = ARTIFACTS / "fit-attempt-inventory-v1.json"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    source = load(SOURCE)
    registry = load(REGISTRY)
    event_rows = []
    by_stratum: dict[str, list[dict]] = defaultdict(list)
    development = [row for row in source["uscrn_normalized_objects"] if row["role"] == "development"]
    global_events = sum(row["event_count"] for row in development)
    global_sites = len(development)
    for row in development:
        with gzip.open(ROOT / row["path"], "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
        count = len(payload["events"])
        result = {
            "event_count": count,
            "station_id": row["station_id"],
            "storm_duration": count >= 150 or (count >= 50 and global_events >= 1000 and global_sites >= 5),
            "storm_joint_dependence": count >= 200,
            "storm_peak_ratio": count >= 150,
            "storm_time_to_peak": count >= 150,
            "stratum": row["stratum"],
        }
        event_rows.append(result)
        by_stratum[row["stratum"]].append(result)
    objective_ids = [row["id"] for row in registry["objectives"] if row["family"] == "storm_descriptor"]
    matrix = []
    failures = []
    for objective in objective_ids:
        for stratum, rows in sorted(by_stratum.items()):
            available = sum(bool(row[objective]) for row in rows)
            record = {
                "available_stations": available,
                "minimum_required": 2,
                "objective_id": objective,
                "status": "pass" if available >= 2 else "fail",
                "station_count": len(rows),
                "stratum": stratum,
            }
            matrix.append(record)
            if record["status"] == "fail":
                failures.append(record)
    fit_paths = sorted((ARTIFACTS / "fits").glob("*.fit.json"))
    detail_paths = sorted((ARTIFACTS / "fits/detail").glob("*.json"))
    fit_records = []
    for path in fit_paths:
        value = load(path)
        fit_records.append(
            {
                "candidate_class": value["candidate_class"]["id"],
                "configuration_id": path.name.removesuffix(".fit.json"),
                "content_sha256": value["content_sha256"],
                "fit_status": value["fit_status"],
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
            }
        )
    FIT_INVENTORY.write_bytes(
        canonical(
            {
                "candidate_development_scores_accessed": False,
                "complete_fit_artifacts": fit_records,
                "complete_fit_count": len(fit_records),
                "detail_artifact_count": len(detail_paths),
                "interrupted_configuration": "latent-k3-p150-q090" if len(fit_records) == 5 else None,
                "interruption_reason": "upstream mandatory availability hold; no ranking benefit can follow",
                "schema_version": 1,
            }
        )
    )
    terminal = "HOLD-A9C-GATE-CALIBRATION" if failures else "GATE-CALIBRATION-AVAILABLE"
    OUTPUT.write_bytes(
        canonical(
            {
                "candidate_development_scores_accessed": False,
                "confirmation_series_accessed": False,
                "event_global_count": global_events,
                "event_global_site_count": global_sites,
                "failed_cells": failures,
                "failure_count": len(failures),
                "horizons_years": [30, 100],
                "minimum_available_stations_per_mandatory_stratum": 2,
                "null_numeric_thresholds": {"path": str((ARTIFACTS / "null-thresholds-v1.json").relative_to(ROOT)), "sha256": sha(ARTIFACTS / "null-thresholds-v1.json"), "status": "complete"},
                "objective_registry_sha256": sha(REGISTRY),
                "selection_executed": False,
                "station_objective_availability": event_rows,
                "stratum_objective_matrix": matrix,
                "terminal": terminal,
            }
        )
    )
    print(f"{terminal}: {len(failures)} failed mandatory stratum/objective cells")


if __name__ == "__main__":
    main()
