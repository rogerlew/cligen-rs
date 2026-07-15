#!/usr/bin/env python3
"""Acquire once, then verify the immutable A8a observed-source archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
ARCHIVE_ROOT = REPO / "references/observed/a8a-v1"
STATION_LIST_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
GHCN_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{station_id}.csv.gz"


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


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("a8a_corpus_common", path)
    if spec is None or spec.loader is None:
        raise ValueError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_freeze() -> None:
    path = ARTIFACTS / "pre-analysis-freeze-v2.json"
    freeze = load_json(path)
    if freeze["status"] != "FROZEN-BEFORE-NEW-DAILY-DATA":
        raise ValueError("A8a pre-analysis freeze is not active")
    for relative, expected in freeze["frozen_files_sha256"].items():
        actual = sha256((REPO / relative).read_bytes())
        if actual != expected:
            raise ValueError(f"frozen file changed: {relative}")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "cligen-rs-a8a-observed-corpus-v1"}
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


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = phi2 - phi1
    delta_lon = math.radians(lon2 - lon1)
    term = math.sin(delta_phi / 2.0) ** 2
    term += math.cos(phi1) * math.cos(phi2) * math.sin(delta_lon / 2.0) ** 2
    return 2.0 * 6371.0088 * math.asin(math.sqrt(term))


def parse_station_list(raw: bytes) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for line in raw.decode("utf-8").splitlines():
        if len(line) < 71:
            continue
        station_id = line[0:11]
        result[station_id] = {
            "elevation_m": float(line[31:37]),
            "latitude": float(line[12:20]),
            "longitude": float(line[21:30]),
            "name": line[41:71].strip(),
            "state": line[38:40].strip(),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true")
    parser.add_argument(
        "--manifest", type=Path, default=ARTIFACTS / "source-manifest-v1.json"
    )
    args = parser.parse_args()
    check_freeze()
    contract = load_json(ARTIFACTS / "analysis-contract-v1.json")
    panel_path = REPO / contract["inputs"]["panel"]["path"]
    if sha256(panel_path.read_bytes()) != contract["inputs"]["panel"]["sha256"]:
        raise ValueError("panel identity mismatch")
    panel = load_json(panel_path)
    common_path = REPO / contract["inputs"]["corpus_common"]["path"]
    if sha256(common_path.read_bytes()) != contract["inputs"]["corpus_common"]["sha256"]:
        raise ValueError("corpus helper identity mismatch")
    common = load_module(common_path)
    metadata_path = ARCHIVE_ROOT / "metadata/ghcnd-stations.txt.gz"
    if args.network:
        station_list_raw = fetch(STATION_LIST_URL)
        store_immutable(metadata_path, common.deterministic_gzip(station_list_raw))
    if not metadata_path.is_file():
        raise FileNotFoundError(metadata_path)
    station_list_archive = metadata_path.read_bytes()
    station_list_raw = gzip.decompress(station_list_archive)
    station_list = parse_station_list(station_list_raw)
    entries = []
    start_year, end_year = contract["sources"]["period"]
    expected_daymet = common.expected_dates("noleap_365", start_year, end_year)
    for station in panel["stations"]:
        station_id = station["station_id"]
        daymet_path = ARCHIVE_ROOT / "daymet" / f"{station_id}.csv.gz"
        if args.network:
            raw = fetch(station["daymet_url"])
            store_immutable(daymet_path, common.deterministic_gzip(raw))
        records, metadata = common.archive_records(daymet_path, "daymet", station)
        dates = [date for date in sorted(records) if start_year <= date[0] <= end_year]
        if dates != expected_daymet:
            raise ValueError(f"incomplete Daymet fixed window: {station_id}")
        logical = common.logical_records_bytes(records, start_year, end_year)
        daymet = {
            "archive_bytes": metadata["archive_bytes"],
            "archive_path": daymet_path.relative_to(REPO).as_posix(),
            "archive_sha256": metadata["archive_sha256"],
            "availability": "available",
            "calendar": metadata["calendar"],
            "dataset": "Daymet",
            "dataset_version": "V4 R1 / 4.1",
            "doi": "10.3334/ORNLDAAC/2129",
            "fixed_window_logical_records_sha256": sha256(logical),
            "fixed_window_record_count": len(dates),
            "grid_elevation_m": metadata["grid_elevation_m"],
            "retrieval_date": "2026-07-15",
            "source_bytes": metadata["source_bytes"],
            "source_sha256": metadata["source_sha256"],
            "upstream_url": station["daymet_url"],
        }
        ghcn_id = station["candidate_ghcn_station_id"]
        ghcn_metadata = station_list.get(ghcn_id)
        if ghcn_metadata is None:
            ghcn: dict[str, Any] = {
                "availability": "unavailable",
                "reason": "candidate U.S. Cooperative identifier absent from official station list",
                "station_identifier": ghcn_id,
            }
        else:
            separation = distance_km(
                station["latitude"],
                station["longitude"],
                ghcn_metadata["latitude"],
                ghcn_metadata["longitude"],
            )
            if separation > contract["sources"]["ghcn_coordinate_tolerance_km"]:
                ghcn = {
                    "availability": "unavailable",
                    "coordinate_separation_km": separation,
                    "reason": "official GHCN coordinate exceeds frozen tolerance",
                    "station_identifier": ghcn_id,
                    "station_metadata": ghcn_metadata,
                }
            else:
                ghcn_path = ARCHIVE_ROOT / "ghcn" / f"{ghcn_id}.csv.gz"
                url = GHCN_URL.format(station_id=ghcn_id)
                if args.network:
                    try:
                        store_immutable(ghcn_path, fetch(url))
                    except urllib.error.HTTPError as error:
                        if error.code != 404:
                            raise
                if not ghcn_path.is_file():
                    ghcn = {
                        "availability": "unavailable",
                        "coordinate_separation_km": separation,
                        "reason": "GHCN by-station object unavailable",
                        "station_identifier": ghcn_id,
                        "station_metadata": ghcn_metadata,
                    }
                else:
                    ghcn_records, ghcn_archive = common.archive_records(
                        ghcn_path, "ghcn", {"ghcn_station_id": ghcn_id}
                    )
                    logical = common.logical_records_bytes(
                        ghcn_records, start_year, end_year
                    )
                    expected_count = len(
                        common.expected_dates(
                            "proleptic_gregorian", start_year, end_year
                        )
                    )
                    prcp_count = sum(
                        "prcp" in values
                        for date, values in ghcn_records.items()
                        if start_year <= date[0] <= end_year
                    )
                    ghcn = {
                        "archive_bytes": ghcn_archive["archive_bytes"],
                        "archive_path": ghcn_path.relative_to(REPO).as_posix(),
                        "archive_sha256": ghcn_archive["archive_sha256"],
                        "availability": "available",
                        "calendar": "proleptic_gregorian",
                        "coordinate_separation_km": separation,
                        "dataset": "GHCN-Daily",
                        "dataset_version": "snapshot-2026-07-15",
                        "doi": "10.7289/V5D21VHZ",
                        "fixed_window_logical_records_sha256": sha256(logical),
                        "fixed_window_prcp_count": prcp_count,
                        "fixed_window_prcp_coverage": prcp_count / expected_count,
                        "retrieval_date": "2026-07-15",
                        "source_bytes": ghcn_archive["source_bytes"],
                        "source_sha256": ghcn_archive["source_sha256"],
                        "station_identifier": ghcn_id,
                        "station_metadata": ghcn_metadata,
                        "sensitivity_eligible": (
                            prcp_count / expected_count
                            >= contract["sources"]["ghcn_minimum_prcp_coverage"]
                        ),
                        "upstream_url": url,
                    }
        entries.append(
            {
                "sources": {"daymet": daymet, "ghcn": ghcn},
                "station_id": station_id,
                "stratum": station["stratum"],
            }
        )
        print(f"verified {station_id}", file=sys.stderr, flush=True)
    manifest = {
        "access_date": "2026-07-15",
        "analysis_contract_sha256": sha256(
            (ARTIFACTS / "analysis-contract-v1.json").read_bytes()
        ),
        "pre_analysis_freeze_sha256": sha256(
            (ARTIFACTS / "pre-analysis-freeze-v2.json").read_bytes()
        ),
        "ghcn_station_list": {
            "archive_path": metadata_path.relative_to(REPO).as_posix(),
            "archive_sha256": sha256(station_list_archive),
            "source_bytes": len(station_list_raw),
            "source_sha256": sha256(station_list_raw),
            "upstream_url": STATION_LIST_URL,
        },
        "panel_sha256": contract["inputs"]["panel"]["sha256"],
        "schema_version": 1,
        "stations": entries,
    }
    args.manifest.write_bytes(canonical_json_bytes(manifest))
    print(args.manifest)


if __name__ == "__main__":
    main()
