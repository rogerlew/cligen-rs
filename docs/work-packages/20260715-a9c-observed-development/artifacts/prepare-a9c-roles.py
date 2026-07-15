#!/usr/bin/env python3
"""Materialize A9c predecessor, role, exposure, and fit-support evidence."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
ARTIFACTS = PACKAGE / "artifacts"
A9A = ROOT / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts"
A9B = ROOT / "docs/work-packages/20260715-a9b-calibration-harness"
SOURCE = ARTIFACTS / "observed-source-manifest-v1.json"
CONFIRMATION = A9A / "confirmation-metadata-selection-v1.json"
CAMPAIGN = ARTIFACTS / "campaign-freeze-v1.json"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name: str, value: object) -> None:
    path = ARTIFACTS / name
    if path.exists():
        raise FileExistsError(path)
    path.write_bytes(canonical(value))


def logical_record(row: dict, access_state: str = "available") -> dict:
    return {
        "access_state": access_state,
        "calendar": row["calendar"],
        "day_boundary": row["day_boundary"],
        "logical_sha256": row["logical_sha256"],
        "object_sha256": row["object_sha256"],
        "period_end": row["period_end"],
        "period_start": row["period_start"],
        "product_version": row["product_version"],
        "source_id": row["source_id"],
        "station_id": row["station_id"],
        "variables": row["variables"],
    }


def main() -> None:
    source = read(SOURCE)
    confirmation = read(CONFIRMATION)
    observed = source["daymet_normalized_objects"] + source["uscrn_normalized_objects"]
    by_role = {
        role: [logical_record(row) for row in observed if row["role"] == role]
        for role in ("coefficient_fit", "development")
    }
    campaign_hash = sha(CAMPAIGN)
    gate_record = {
        "access_state": "available",
        "calendar": "proleptic_gregorian",
        "day_boundary": "synthetic_identity",
        "logical_sha256": campaign_hash,
        "object_sha256": campaign_hash,
        "period_end": "2100-12-31",
        "period_start": "2001-01-01",
        "product_version": "synthetic_same_model_null_v1",
        "source_id": "synthetic_same_model_null",
        "station_id": "a9c_null_corpus",
        "variables": ["objective_vectors"],
    }
    confirmation_records = []
    for station in confirmation["stations"]:
        confirmation_records.append(
            {
                "access_state": "metadata_only",
                "calendar": "gregorian",
                "day_boundary": "local_standard_time",
                "logical_sha256": None,
                "object_sha256": None,
                "period_end": "2025-12-31",
                "period_start": "2010-01-01",
                "product_version": "Subhourly01 format 01 / target bytes unacquired",
                "source_id": "uscrn_subhourly01",
                "station_id": station["station_id"],
                "variables": ["air_temperature_c", "precip_5min_mm", "relative_humidity_pct", "solar_radiation_w_m2", "wetness", "wind_speed_1_5m_m_s"],
            }
        )
    role_manifest = {
        "access_log": [
            {
                "action": "metadata_read",
                "actor": "a9c-metadata-freeze",
                "object_sha256": sha(CONFIRMATION),
                "timestamp": "2026-07-15T22:00:00Z",
            }
        ],
        "confirmation_access_state": "metadata_only",
        "created_at": "2026-07-15T22:00:00Z",
        "exposed_logical_records": by_role["coefficient_fit"] + by_role["development"],
        "freeze_sha256": sha(ARTIFACTS / "data-role-freeze-v1.json"),
        "manifest_id": "a9c-data-roles-v1",
        "roles": [
            {"permitted_use": "estimate candidate parameters and fixed hierarchical pooling only", "records": by_role["coefficient_fit"], "role": "coefficient_fit"},
            {"permitted_use": "candidate tuning, comparison, and ranking only", "records": by_role["development"], "role": "development"},
            {"permitted_use": "candidate-blind same-model null calibration only", "records": [gate_record], "role": "gate_calibration"},
            {"permitted_use": "one-shot A9d use only after a sealed candidate freeze and separate dispatch", "records": confirmation_records, "role": "confirmation"},
        ],
        "schema_version": 1,
    }
    write("data-role-manifest-v1.json", role_manifest)

    a9a_exposure = read(A9A / "exposure-manifest-v1.json")
    write(
        "exposure-union-v1.json",
        {
            "a9a_exposure_manifest": {"path": str((A9A / "exposure-manifest-v1.json").relative_to(ROOT)), "sha256": sha(A9A / "exposure-manifest-v1.json")},
            "a9a_exposed_model_ids": a9a_exposure["exposed_model_ids"],
            "a9a_exposed_station_count": len(a9a_exposure["stations"]),
            "a9c_observed_source_manifest": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
            "a9c_records": by_role["coefficient_fit"] + by_role["development"],
            "confirmation_records_in_union": 0,
            "schema_version": 1,
            "union_id": "a9c-exposure-union-v1",
        },
    )

    event_objects = [row for row in source["uscrn_normalized_objects"] if row["role"] == "coefficient_fit"]
    event_rows = []
    total_events = 0
    for row in event_objects:
        with gzip.open(ROOT / row["path"], "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
        count = len(payload["events"])
        total_events += count
        event_rows.append(
            {
                "borrowing_eligible": count >= 50,
                "event_count": count,
                "station_direct_fit_eligible": count >= 150,
                "station_id": row["station_id"],
                "stratum": row["stratum"],
            }
        )
    global_borrow = total_events >= 1000 and len(event_rows) >= 5 and all(row["borrowing_eligible"] for row in event_rows)
    daymet_rows = []
    for row in source["daymet_normalized_objects"]:
        if row["role"] != "coefficient_fit":
            continue
        with gzip.open(ROOT / row["path"], "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
        records = payload["records"]
        wet = sum(float(record["prcp_mm"]) > 0.0 for record in records)
        daymet_rows.append(
            {
                "dry_days": len(records) - wet,
                "occurrence_amount_eligible": len(records) >= 15 * 365 and wet >= 300 and len(records) - wet >= 300,
                "station_id": row["station_id"],
                "wet_days": wet,
                "years": len(records) / 365,
            }
        )
    write(
        "fit-applicability-v1.json",
        {
            "daymet": daymet_rows,
            "event_global_borrowing_eligible": global_borrow,
            "event_global_count": total_events,
            "event_global_site_count": len(event_rows),
            "events": event_rows,
            "fit_applicability": "pass" if global_borrow and all(row["occurrence_amount_eligible"] for row in daymet_rows) else "fail",
            "pooling_interpretation": "station first; frozen primary stratum second; the frozen all-strata global hyperdistribution supplies descriptors only for stations with at least 50 events when the global group has at least 1000 events across at least five sites",
            "schema_version": 1,
        },
    )

    predecessor_paths = [
        A9B / "package.md",
        A9B / "artifacts/a9c-handoff.md",
        A9B / "artifacts/predecessor-manifest-v1.json",
        A9B / "artifacts/source-manifest-v1.json",
        A9B / "artifacts/requirement-coverage.md",
        A9B / "artifacts/review.md",
        A9B / "artifacts/gate-results.md",
        *sorted((A9B / "artifacts/generated").glob("*.json")),
    ]
    write(
        "predecessor-manifest-v1.json",
        {
            "dispatch": {"branch": "main", "commit": "4e918ecd5d2b37eaa99ae365677f423080069480", "target": "main"},
            "files": [{"bytes": path.stat().st_size, "path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in predecessor_paths],
            "manifest_id": "a9c-predecessor-v1",
            "observed_confirmation_access": False,
            "predecessor_terminal": "HARNESS-READY-A9C",
            "schema_version": 1,
        },
    )
    print(f"prepared A9c roles; {total_events} fit events; global borrowing={global_borrow}")


if __name__ == "__main__":
    main()
