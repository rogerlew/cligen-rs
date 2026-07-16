#!/usr/bin/env python3
"""Build or verify the A9c2 metadata-only hot-arid roster census."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
FREEZE_PATH = ARTIFACTS / "metadata-roster-freeze-v1.json"
OUTPUT_PATH = ARTIFACTS / "hot-arid-roster-inventory-v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def strict_json(path: Path) -> Any:
    def reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"duplicate JSON key {key!r}: {path}")
            value[key] = item
        return value

    return json.loads(
        path.read_text(),
        object_pairs_hook=reject_duplicate,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"nonfinite JSON value {value}: {path}")
        ),
    )


def station_id(row: dict[str, str]) -> str:
    raw = f"{row['STATE']} {row['LOCATION']} {row['VECTOR']}".lower()
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_")


def parse_commissioning(value: str) -> datetime:
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.0")
    return parsed.replace(tzinfo=timezone.utc)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    return radius_km * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def input_path(record: dict[str, Any]) -> Path:
    path = ROOT / record["path"]
    require(path.is_file(), f"missing frozen input: {path}")
    require(sha256(path) == record["sha256"], f"frozen input hash mismatch: {path}")
    return path


def build() -> dict[str, Any]:
    freeze = strict_json(FREEZE_PATH)
    require(freeze["freeze_id"] == "a9c2-metadata-roster-freeze-v1", "freeze ID")
    require(freeze["frozen_before_inventory_evaluation"] is True, "prospective freeze")
    paths = {record["role"]: input_path(record) for record in freeze["inputs"]}

    selection = strict_json(paths["hot_arid_semantics_authority"])
    expected_bounds = selection["selected_strata"]["hot_arid"]["bounds"]
    bounds = freeze["crosswalk"]["hot_arid_bounds"]
    require(
        expected_bounds
        == {
            "annual_expected_precip_mm_max": bounds[
                "annual_expected_precip_mm_max_inclusive"
            ],
            "annual_tmean_c_min": bounds["annual_tmean_c_min_inclusive"],
            "longitude_max": bounds["longitude_max_inclusive"],
        },
        "hot-arid semantics diverged from A8a",
    )

    inventory = strict_json(paths["legacy_parameter_catalog_descriptor_inventory"])
    require(inventory["station_count"] == len(inventory["stations"]), "descriptor count")
    require(
        inventory["descriptor_boundary"]
        == "legacy parameter and catalog metadata only; no daily observation was read",
        "descriptor boundary",
    )
    descriptors = inventory["stations"]

    confirmation = strict_json(paths["locked_confirmation_metadata_roster"])
    confirmations = confirmation["stations"]
    require(len(confirmations) == 18, "locked confirmation count")
    confirmation_ids = {item["station_id"] for item in confirmations}

    with paths["official_uscrn_station_listing_snapshot"].open(newline="") as handle:
        listing = list(csv.DictReader(handle, delimiter="\t"))
    base_rule = freeze["network_base_rule"]
    deadline = datetime.fromisoformat(
        base_rule["commissioning_on_or_before"].replace("Z", "+00:00")
    )
    base_rows = [
        row
        for row in listing
        if row["COUNTRY"] == base_rule["country"]
        and row["NETWORK"] == base_rule["network"]
        and row["STATUS"] == base_rule["status"]
        and row["OPERATION"] == base_rule["operation"]
        and bool(row["COMMISSIONING"])
        and parse_commissioning(row["COMMISSIONING"]) <= deadline
    ]

    crosswalk_limit = freeze["crosswalk"][
        "maximum_nearest_descriptor_distance_km_inclusive"
    ]
    partition_limit = freeze["partition_rule"][
        "minimum_distance_from_every_locked_confirmation_station_km_inclusive"
    ]
    rows: list[dict[str, Any]] = []
    accepted: list[str] = []
    for row in sorted(base_rows, key=station_id):
        sid = station_id(row)
        latitude = float(row["LATITUDE"])
        longitude = float(row["LONGITUDE"])
        nearest_descriptor = min(
            descriptors,
            key=lambda item: (
                haversine_km(
                    latitude,
                    longitude,
                    float(item["latitude"]),
                    float(item["longitude"]),
                ),
                item["station_id"],
            ),
        )
        descriptor_distance = haversine_km(
            latitude,
            longitude,
            float(nearest_descriptor["latitude"]),
            float(nearest_descriptor["longitude"]),
        )
        nearest_confirmation = min(
            confirmations,
            key=lambda item: (
                haversine_km(
                    latitude,
                    longitude,
                    float(item["latitude"]),
                    float(item["longitude"]),
                ),
                item["station_id"],
            ),
        )
        confirmation_distance = haversine_km(
            latitude,
            longitude,
            float(nearest_confirmation["latitude"]),
            float(nearest_confirmation["longitude"]),
        )
        descriptor_in_range = descriptor_distance <= crosswalk_limit
        hot_arid = (
            descriptor_in_range
            and longitude <= bounds["longitude_max_inclusive"]
            and nearest_descriptor["annual_expected_precip_mm"]
            <= bounds["annual_expected_precip_mm_max_inclusive"]
            and nearest_descriptor["annual_tmean_c"]
            >= bounds["annual_tmean_c_min_inclusive"]
        )
        if sid in confirmation_ids:
            disposition = "excluded"
            reason = "locked_confirmation_station_id"
        elif confirmation_distance < partition_limit:
            disposition = "excluded"
            reason = "confirmation_partition_distance"
        elif not descriptor_in_range:
            disposition = "excluded"
            reason = "descriptor_crosswalk_out_of_range"
        elif not hot_arid:
            disposition = "excluded"
            reason = "not_hot_arid_descriptor_stratum"
        else:
            disposition = "accepted"
            reason = "passes_all_frozen_metadata_rules"
            accepted.append(sid)
        rows.append(
            {
                "commissioning": row["COMMISSIONING"],
                "disposition": disposition,
                "elevation_ft": float(row["ELEVATION"]),
                "hot_arid_descriptor_match": hot_arid,
                "latitude": latitude,
                "longitude": longitude,
                "nearest_confirmation_distance_km": round(confirmation_distance, 3),
                "nearest_confirmation_station_id": nearest_confirmation["station_id"],
                "nearest_descriptor_annual_expected_precip_mm": round(
                    nearest_descriptor["annual_expected_precip_mm"], 6
                ),
                "nearest_descriptor_annual_tmean_c": round(
                    nearest_descriptor["annual_tmean_c"], 6
                ),
                "nearest_descriptor_distance_km": round(descriptor_distance, 3),
                "nearest_descriptor_station_id": nearest_descriptor["station_id"],
                "reason": reason,
                "station_id": sid,
                "station_name": f"{row['STATE']} {row['LOCATION']} {row['VECTOR']}",
                "wban": row["WBAN"],
            }
        )

    required = freeze["retention_rule"]["required_retained_station_ids"]
    minimum = freeze["retention_rule"]["minimum_accepted_locations"]
    missing_required = sorted(set(required) - set(accepted))
    terminal = (
        freeze["terminal_rule"]["otherwise"]
        if len(accepted) >= minimum and not missing_required
        else freeze["terminal_rule"][
            "fewer_than_five_or_missing_required_retained_site"
        ]
    )
    reason_counts: dict[str, int] = {}
    for row in rows:
        reason_counts[row["reason"]] = reason_counts.get(row["reason"], 0) + 1
    return {
        "accepted_station_count": len(accepted),
        "accepted_station_ids": accepted,
        "candidate_development_outputs_accessed": False,
        "confirmation_series_accessed": False,
        "daily_or_subdaily_station_series_accessed": False,
        "freeze_sha256": sha256(FREEZE_PATH),
        "inventory_id": "a9c2-hot-arid-roster-inventory-v1",
        "locked_confirmation_station_count": len(confirmations),
        "metadata_base_station_count": len(rows),
        "minimum_accepted_station_count": minimum,
        "missing_required_retained_station_ids": missing_required,
        "reason_counts": dict(sorted(reason_counts.items())),
        "rows": rows,
        "schema_version": 1,
        "station_listing_row_count": len(listing),
        "terminal": terminal,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = build()
    encoded = canonical_bytes(result)
    if args.write:
        require(not OUTPUT_PATH.exists(), f"refusing to replace frozen output: {OUTPUT_PATH}")
        OUTPUT_PATH.write_bytes(encoded)
    else:
        require(OUTPUT_PATH.is_file(), f"missing output: {OUTPUT_PATH}; run with --write")
        require(OUTPUT_PATH.read_bytes() == encoded, "roster inventory does not reproduce")
    print(
        f"{result['terminal']}: {result['accepted_station_count']} accepted / "
        f"{result['minimum_accepted_station_count']} required; "
        f"{result['metadata_base_station_count']} metadata-base sites"
    )


if __name__ == "__main__":
    main()
