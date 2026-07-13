#!/usr/bin/env python3
"""Acquire once, then verify the immutable A5a-v1 observed source archive."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True

from corpus_common import (
    archive_records,
    deterministic_gzip,
    expected_dates,
    logical_records_bytes,
    sha256,
    write_canonical_json,
)

DAYMET_DOI = "10.3334/ORNLDAAC/2129"
GHCN_DOI = "10.7289/V5D21VHZ"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "cligen-rs-a5a-observed-corpus-v1"}
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def store_immutable(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"immutable archive differs: {path}")
        return
    path.write_bytes(data)


def source_entry(
    repo: Path,
    archive_path: Path,
    kind: str,
    station: dict[str, object],
    period: list[int],
) -> dict[str, object]:
    records, metadata = archive_records(archive_path, kind, station)
    logical = logical_records_bytes(records, period[0], period[1])
    variables = {
        variable: sum(
            1
            for date, values in records.items()
            if period[0] <= date[0] <= period[1] and variable in values
        )
        for variable in ("prcp", "tmax", "tmin")
    }
    if kind == "daymet":
        station_id = str(station["station_id"])
        url = (
            "https://daymet.ornl.gov/single-pixel/api/data"
            f"?lat={station['latitude']}&lon={station['longitude']}"
            "&vars=prcp,tmax,tmin"
        )
        identity = {
            "dataset": "Daymet",
            "dataset_version": "V4 R1",
            "doi": DAYMET_DOI,
            "requested_coordinates": {
                "latitude": station["latitude"],
                "longitude": station["longitude"],
            },
            "source_id": f"daymet-v4r1-{station_id}",
            "upstream_url": url,
        }
        compression = "gzip-9-mtime-0-empty-name"
        media_type = "text/csv"
        source_sha = str(metadata["source_sha256"])
        if source_sha != station["daymet_source_sha256"]:
            raise ValueError(f"{station_id}: Daymet Q3 source hash mismatch")
        expected = expected_dates(str(metadata["calendar"]), period[0], period[1])
        for variable, count in variables.items():
            if count != len(expected) or any(
                variable not in records.get(date, {}) for date in expected
            ):
                raise ValueError(
                    f"{station_id}: incomplete Daymet {variable} fixed window"
                )
        q3_hash = station["daymet_source_sha256"]
        intake_rules = {
            "missing_value_rule": "all 365 no-leap days and all three variables are required; no sentinel or imputation is accepted",
            "quality_flag_rule": "Daymet single-pixel CSV has no per-observation quality-flag field",
        }
    else:
        ghcn_id = str(station["ghcn_station_id"])
        identity = {
            "dataset": "GHCN-Daily",
            "dataset_version": "snapshot-2026-07-12",
            "doi": GHCN_DOI,
            "source_id": f"ghcn-daily-{ghcn_id}-20260712",
            "station_identifier": ghcn_id,
            "upstream_url": (
                "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/"
                f"{ghcn_id}.csv.gz"
            ),
        }
        compression = "upstream-gzip-byte-for-byte"
        media_type = "application/gzip"
        q3_hash = station["q3_ghcn_source_sha256"]
        intake_rules = {
            "missing_value_rule": "absent date/element rows remain missing; no sentinel or imputation is accepted",
            "quality_flag_rule": "rows with a nonblank GHCN Q_FLAG field are excluded; M_FLAG and S_FLAG do not exclude a row",
        }
    return {
        **identity,
        "availability": "available",
        "archive_bytes": metadata["archive_bytes"],
        "archive_path": archive_path.relative_to(repo).as_posix(),
        "archive_sha256": metadata["archive_sha256"],
        "calendar": metadata["calendar"],
        "compression": compression,
        "fixed_window_logical_records_sha256": sha256(logical),
        "fixed_window_record_counts": variables,
        "media_type": media_type,
        "intake_rules": intake_rules,
        "q3_historical_source_sha256": q3_hash,
        "retrieval_date": "2026-07-12",
        "source_bytes": metadata["source_bytes"],
        "source_sha256": metadata["source_sha256"],
        "variables": {
            "prcp": "mm/day",
            "tmax": "degree_Celsius",
            "tmin": "degree_Celsius",
        },
        **(
            {"grid_elevation_m": metadata["grid_elevation_m"]}
            if kind == "daymet"
            else {}
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--network",
        action="store_true",
        help="fetch upstream bytes; otherwise verify the local archive only",
    )
    parser.add_argument("--config", type=Path)
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    script = Path(__file__).resolve()
    repo = script.parents[5]
    config_path = args.config or script.with_name("corpus-config-v1.json")
    archive_root = args.archive_root or repo / "references/observed/a5a-v1"
    manifest_path = args.manifest or script.with_name("source-manifest-v1.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("config_version") != 1:
        raise ValueError("unsupported corpus config version")
    full_period = config["periods"]["full"]
    entries = []
    for station in config["stations"]:
        station_id = station["station_id"]
        daymet_url = (
            "https://daymet.ornl.gov/single-pixel/api/data"
            f"?lat={station['latitude']}&lon={station['longitude']}"
            "&vars=prcp,tmax,tmin"
        )
        daymet_path = archive_root / "daymet" / f"{station_id}.csv.gz"
        if args.network:
            source = fetch(daymet_url)
            if sha256(source) != station["daymet_source_sha256"]:
                raise ValueError(f"{station_id}: mutable Daymet source changed")
            store_immutable(daymet_path, deterministic_gzip(source))
        if not daymet_path.is_file():
            raise FileNotFoundError(daymet_path)
        sources = {
            "daymet": source_entry(repo, daymet_path, "daymet", station, full_period)
        }
        ghcn_id = station["ghcn_station_id"]
        if ghcn_id is not None:
            ghcn_url = (
                "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/"
                f"{ghcn_id}.csv.gz"
            )
            ghcn_path = archive_root / "ghcn" / f"{ghcn_id}.csv.gz"
            if args.network:
                store_immutable(ghcn_path, fetch(ghcn_url))
            if not ghcn_path.is_file():
                raise FileNotFoundError(ghcn_path)
            sources["ghcn"] = source_entry(
                repo, ghcn_path, "ghcn", station, full_period
            )
        else:
            sources["ghcn"] = {
                "availability": "unavailable",
                "reason": "Q3 station mapping absent or failed the completeness screen",
            }
        entries.append(
            {
                "sources": sources,
                "station_id": station_id,
            }
        )
        print(f"verified {station_id}", file=sys.stderr, flush=True)

    manifest = {
        "config_sha256": sha256(config_path.read_bytes()),
        "fixed_periods": config["periods"],
        "source_manifest_schema_version": 1,
        "station_collection": config["station_collection"],
        "stations": entries,
    }
    write_canonical_json(manifest_path, manifest)
    print(manifest_path)


if __name__ == "__main__":
    main()
