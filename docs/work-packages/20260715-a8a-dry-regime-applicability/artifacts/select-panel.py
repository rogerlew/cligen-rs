#!/usr/bin/env python3
"""Validate and archive the metadata-only A8a confirmation panel."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import sys
import tarfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def distance_km(left: dict[str, Any], right: dict[str, Any]) -> float:
    lat1 = math.radians(left["latitude"])
    lat2 = math.radians(right["latitude"])
    delta_lat = lat2 - lat1
    delta_lon = math.radians(right["longitude"] - left["longitude"])
    term = math.sin(delta_lat / 2.0) ** 2
    term += math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2.0) ** 2
    return 2.0 * 6371.0088 * math.asin(math.sqrt(term))


def validate_bounds(
    station: dict[str, Any], stratum: str, definition: dict[str, Any]
) -> None:
    bounds = definition["bounds"]
    if stratum == "negative_control":
        subgroup = next(
            name
            for name, members in definition["subgroups"].items()
            if station["station_id"] in members
        )
        bounds = bounds[subgroup]
    for key, expected in bounds.items():
        if key.endswith("_min"):
            value = station[key.removesuffix("_min")]
            if value < expected:
                raise ValueError(f"{station['station_id']} violates {key}")
        elif key.endswith("_max"):
            value = station[key.removesuffix("_max")]
            if value > expected:
                raise ValueError(f"{station['station_id']} violates {key}")
        elif isinstance(expected, list) and len(expected) == 2:
            if not expected[0] <= station[key] <= expected[1]:
                raise ValueError(f"{station['station_id']} violates {key}")
        else:
            raise ValueError(f"unsupported bound: {key}")


def deterministic_tar_gzip(entries: list[tuple[str, bytes]]) -> bytes:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, data in sorted(entries):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=output, mtime=0) as stream:
        stream.write(tar_buffer.getvalue())
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--station-root", type=Path, required=True)
    parser.add_argument("--panel", type=Path, default=ARTIFACTS / "panel-v1.json")
    parser.add_argument(
        "--parameter-archive",
        type=Path,
        default=ARTIFACTS / "selected-parameters-v1.tar.gz",
    )
    args = parser.parse_args()
    contract_path = ARTIFACTS / "selection-contract-v1.json"
    contract = load_json(contract_path)
    inventory_path = Path.cwd() / contract["inventory"]["path"]
    if sha256(inventory_path.read_bytes()) != contract["inventory"]["sha256"]:
        raise ValueError("station inventory identity mismatch")
    inventory = load_json(inventory_path)
    if inventory["catalog_sha256"] != contract["catalog"]["sha256"]:
        raise ValueError("catalog identity mismatch")
    stations = {entry["station_id"]: entry for entry in inventory["stations"]}
    exposed = set(contract["exposed_station_ids"])
    selected: list[dict[str, Any]] = []
    archive_entries: list[tuple[str, bytes]] = []
    for stratum, definition in sorted(contract["selected_strata"].items()):
        members = [stations[station_id] for station_id in definition["station_ids"]]
        if len(members) < 4:
            raise ValueError(f"insufficient {stratum} breadth")
        minimum_distance = min(
            distance_km(left, right)
            for index, left in enumerate(members)
            for right in members[index + 1 :]
        )
        if minimum_distance < contract["geographic_rules"][
            "minimum_within_stratum_pair_distance_km"
        ]:
            raise ValueError(f"{stratum} geographic separation failed")
        for station in members:
            station_id = station["station_id"]
            if station_id in exposed:
                raise ValueError(f"exposed station selected: {station_id}")
            if station["catalog_years"] < contract["minimum_catalog_years"]:
                raise ValueError(f"short catalog record: {station_id}")
            validate_bounds(station, stratum, definition)
            par_path = args.station_root / f"{station_id}.par"
            raw = par_path.read_bytes()
            if sha256(raw) != station["parameter_sha256"]:
                raise ValueError(f"parameter identity mismatch: {station_id}")
            selected.append(
                {
                    **station,
                    "candidate_ghcn_station_id": f"USC00{station_id[2:]}",
                    "daymet_url": (
                        "https://daymet.ornl.gov/single-pixel/api/data"
                        f"?lat={station['latitude']}&lon={station['longitude']}"
                        "&vars=prcp,tmax,tmin"
                    ),
                    "stratum": stratum,
                }
            )
            archive_entries.append((f"station-parameters/{station_id}.par", raw))
    if len({entry["station_id"] for entry in selected}) != len(selected):
        raise ValueError("selected station appears in more than one stratum")
    archive = deterministic_tar_gzip(archive_entries)
    args.parameter_archive.write_bytes(archive)
    result = {
        "daily_data_accessed": False,
        "metadata_boundary": inventory["descriptor_boundary"],
        "parameter_archive": {
            "path": args.parameter_archive.relative_to(Path.cwd()).as_posix(),
            "sha256": sha256(archive),
        },
        "schema_version": 1,
        "selected_station_count": len(selected),
        "selection_contract_sha256": sha256(contract_path.read_bytes()),
        "stations": sorted(selected, key=lambda entry: entry["station_id"]),
        "stratum_counts": {
            name: len(definition["station_ids"])
            for name, definition in sorted(contract["selected_strata"].items())
        },
    }
    args.panel.write_bytes(canonical_json_bytes(result))
    print(f"selected {len(selected)} stations without daily-data access")


if __name__ == "__main__":
    main()
