#!/usr/bin/env python3
"""Acquire, normalize, audit, and verify the frozen A10M1 corpus.

Large third-party bytes are confined to the package's ignored raw/ tree.
Only immutable identities and compact evidence are written to artifacts/.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import statistics
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, time as civil_time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[5]
PACKAGE = REPO / "docs/work-packages/20260717-a10m1-corpus-role-freeze"
ARTIFACTS = PACKAGE / "artifacts"
RAW = PACKAGE / "raw"
FREEZE_PATH = ARTIFACTS / "a10m1-freeze-v1.json"
PARTITION_PATH = ARTIFACTS / "partition-role-freeze-v1.json"
SOURCE_MANIFEST_PATH = ARTIFACTS / "source-manifest-v1.json"
NORMALIZED_MANIFEST_PATH = ARTIFACTS / "normalized-manifest-v1.json"
TRANSFER_MANIFEST_PATH = ARTIFACTS / "offline-transfer-manifest-v1.json"
CONFIRMATION = REPO / (
    "docs/work-packages/20260715-a9a-successor-family-foundation/"
    "artifacts/confirmation-metadata-selection-v1.json"
)
A9_FREEZE = REPO / (
    "docs/work-packages/20260715-a9c-observed-development/"
    "artifacts/data-role-freeze-v1.json"
)
A8A_MANIFEST = REPO / (
    "docs/work-packages/20260715-a8a-dry-regime-applicability/"
    "artifacts/source-manifest-v1.json"
)
DAYMET_LEDGER = ARTIFACTS / "daymet-access-v1.ndjson"
USCRN_LEDGER = ARTIFACTS / "uscrn-access-v1.ndjson"
USER_AGENT = "cligen-rs-a10m1-corpus-v1"
DAYMET_FIELDS = {
    "prcp": "prcp (mm/day)",
    "tmax": "tmax (deg c)",
    "tmin": "tmin (deg c)",
    "srad": "srad (W/m^2)",
    "vp": "vp (Pa)",
    "swe": "swe (kg/m^2)",
    "dayl": "dayl (s/day)",
}
DAYMET_UNITS = {
    "prcp": "mm/day",
    "tmax": "degC",
    "tmin": "degC",
    "srad": "W/m^2",
    "vp": "Pa",
    "swe": "kg/m^2",
    "dayl": "s/day",
}
DAILY_HEADERS = [
    "WBANNO", "LST_DATE", "CRX_VN", "LONGITUDE", "LATITUDE",
    "T_DAILY_MAX", "T_DAILY_MIN", "T_DAILY_MEAN", "T_DAILY_AVG",
    "P_DAILY_CALC", "SOLARAD_DAILY", "SUR_TEMP_DAILY_TYPE",
    "SUR_TEMP_DAILY_MAX", "SUR_TEMP_DAILY_MIN", "SUR_TEMP_DAILY_AVG",
    "RH_DAILY_MAX", "RH_DAILY_MIN", "RH_DAILY_AVG",
    "SOIL_MOISTURE_5_DAILY", "SOIL_MOISTURE_10_DAILY",
    "SOIL_MOISTURE_20_DAILY", "SOIL_MOISTURE_50_DAILY",
    "SOIL_MOISTURE_100_DAILY", "SOIL_TEMP_5_DAILY",
    "SOIL_TEMP_10_DAILY", "SOIL_TEMP_20_DAILY", "SOIL_TEMP_50_DAILY",
    "SOIL_TEMP_100_DAILY",
]
DAILY_UNITS = {
    "T_DAILY_MAX": "degC", "T_DAILY_MIN": "degC",
    "T_DAILY_MEAN": "degC", "T_DAILY_AVG": "degC",
    "P_DAILY_CALC": "mm/day", "SOLARAD_DAILY": "MJ/m^2/day",
    "SUR_TEMP_DAILY_MAX": "degC", "SUR_TEMP_DAILY_MIN": "degC",
    "SUR_TEMP_DAILY_AVG": "degC", "RH_DAILY_MAX": "percent",
    "RH_DAILY_MIN": "percent", "RH_DAILY_AVG": "percent",
    "SOIL_MOISTURE_5_DAILY": "m^3/m^3",
    "SOIL_MOISTURE_10_DAILY": "m^3/m^3",
    "SOIL_MOISTURE_20_DAILY": "m^3/m^3",
    "SOIL_MOISTURE_50_DAILY": "m^3/m^3",
    "SOIL_MOISTURE_100_DAILY": "m^3/m^3",
    "SOIL_TEMP_5_DAILY": "degC", "SOIL_TEMP_10_DAILY": "degC",
    "SOIL_TEMP_20_DAILY": "degC", "SOIL_TEMP_50_DAILY": "degC",
    "SOIL_TEMP_100_DAILY": "degC",
}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any, *, replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value))
    temporary.replace(path)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_key(*values: object) -> str:
    return sha256_bytes("|".join(map(str, values)).encode())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def source_name(state: str, location: str, vector: str) -> str:
    return "_".join((state, location, vector)).replace(" ", "_")


def station_token(state: str, location: str, vector: str) -> str:
    return source_name(state, location, vector).lower().replace(".", "")


def haversine_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp = math.radians(b_lat - a_lat)
    dl = math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.asin(math.sqrt(h))


def regime_for(freeze: dict[str, Any], latitude: float, longitude: float) -> str | None:
    for regime, frames in freeze["regime_frames"].items():
        for south, north, west, east in frames:
            if south <= latitude <= north and west <= longitude <= east:
                return regime
    return None


def fetch(url: str, *, timeout: int = 180, attempts: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as error:
            last = error
            if isinstance(error, urllib.error.HTTPError) and error.code == 404:
                raise
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    assert last is not None
    raise last


def append_ledger(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab", buffering=0) as stream:
        for record in records:
            stream.write(canonical_bytes(record))
        os.fsync(stream.fileno())


def load_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def development_coordinates() -> list[tuple[float, float]]:
    coordinates: list[tuple[float, float]] = []
    manifest = read_json(A8A_MANIFEST)
    selected = {row["station_id"] for row in read_json(A9_FREEZE)["daymet"]["stations"]}
    for station in manifest["stations"]:
        if station["station_id"] not in selected:
            continue
        query = urllib.parse.parse_qs(urllib.parse.urlparse(station["sources"]["daymet"]["upstream_url"]).query)
        coordinates.append((float(query["lat"][0]), float(query["lon"][0])))
    return coordinates


def locked_metadata() -> tuple[set[str], list[tuple[float, float]]]:
    confirmation = read_json(CONFIRMATION)
    tokens = set()
    coordinates = []
    for station in confirmation["stations"]:
        words = station["station_name"].split()
        tokens.add("_".join(words).lower().replace(".", ""))
        coordinates.append((station["latitude"], station["longitude"]))
    return tokens, coordinates


def build_daymet_candidates(freeze: dict[str, Any]) -> list[dict[str, Any]]:
    _, confirmation_coordinates = locked_metadata()
    prohibited = confirmation_coordinates + development_coordinates()
    step = freeze["daymet"]["grid_step_degrees"]
    minimum = freeze["daymet"]["minimum_distance_locked_km"]
    candidates: list[dict[str, Any]] = []
    seen = set()
    for regime, frames in freeze["regime_frames"].items():
        for south, north, west, east in frames:
            lat = south
            while lat <= north + 1e-8:
                lon = west
                while lon <= east + 1e-8:
                    coordinate = (round(lat, 4), round(lon, 4))
                    lon += step
                    if coordinate in seen:
                        continue
                    seen.add(coordinate)
                    if any(
                        abs(coordinate[0] - other[0]) <= 1.0
                        and abs(coordinate[1] - other[1]) <= 1.5
                        and haversine_km(*coordinate, *other) < minimum
                        for other in prohibited
                    ):
                        continue
                    tile = f"{math.floor(coordinate[0]):+03d}_{math.floor(coordinate[1]):+04d}"
                    tile_hash = stable_key(freeze["freeze_id"], regime, tile)
                    role = "fit_validation" if int(tile_hash[:8], 16) % 6 == 0 else "candidate_fit"
                    point_id = f"p{round(coordinate[0] * 100):+05d}_{round(coordinate[1] * 100):+06d}"
                    candidates.append({
                        "latitude": coordinate[0], "longitude": coordinate[1],
                        "point_id": point_id, "regime": regime, "role": role,
                        "tile_id": tile,
                        "order": stable_key(freeze["freeze_id"], regime, role, point_id),
                    })
                lat += step
    candidates.sort(key=lambda row: (row["regime"], row["role"], row["order"]))
    return candidates


def download_documents(freeze: dict[str, Any]) -> list[dict[str, Any]]:
    documents = {
        "stations.tsv": freeze["uscrn"]["station_table"],
        "daily01-headers.txt": freeze["uscrn"]["daily_root"] + "/headers.txt",
        "daily01-readme.txt": freeze["uscrn"]["daily_root"] + "/readme.txt",
        "subhourly01-headers.txt": freeze["uscrn"]["subhourly_root"] + "/headers.txt",
        "subhourly01-readme.txt": freeze["uscrn"]["subhourly_root"] + "/readme.txt",
    }
    output = []
    for name, url in documents.items():
        path = ARTIFACTS / "source-documents" / name
        raw = fetch(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        output.append({"accessed_at_utc": utc_now(), "bytes": len(raw), "path": str(path.relative_to(REPO)), "sha256": sha256_bytes(raw), "url": url})
    return output


def parse_station_table(freeze: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    locked_tokens, _ = locked_metadata()
    a9 = read_json(A9_FREEZE)
    development = {row["source_name"].lower().replace(".", "") for row in a9["uscrn"]["stations"]}
    inventory = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            token = station_token(row["STATE"], row["LOCATION"], row["VECTOR"])
            reasons = []
            if row["COUNTRY"] != "US": reasons.append("outside_us")
            if row["NETWORK"] != "USCRN": reasons.append("not_uscrn")
            if row["OPERATION"] != "Operational": reasons.append("not_operational")
            if row["CLOSING"] and row["CLOSING"][:4].isdigit() and int(row["CLOSING"][:4]) < 2010:
                reasons.append("closed_before_fit_period")
            if token in development: reasons.append("a9_development_station")
            if token in locked_tokens: reasons.append("confirmation_locked_metadata")
            latitude, longitude = float(row["LATITUDE"]), float(row["LONGITUDE"])
            regime = regime_for(freeze, latitude, longitude)
            if regime is None: reasons.append("outside_primary_frames")
            inventory.append({
                "commissioning": row["COMMISSIONING"],
                "elevation_ft": None if row["ELEVATION"] == "UN" else float(row["ELEVATION"]),
                "exclusion_reasons": reasons, "latitude": latitude, "longitude": longitude,
                "network": row["NETWORK"], "regime": regime,
                "source_name": source_name(row["STATE"], row["LOCATION"], row["VECTOR"]),
                "station_id": token, "wban": row["WBAN"],
            })
    eligible = [row for row in inventory if not row["exclusion_reasons"]]
    by_regime: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        by_regime[row["regime"]].append(row)
    validation_count = freeze["uscrn"]["validation_stations_per_regime"]
    event_count = freeze["uscrn"]["event_stations_per_regime"]
    for regime, rows in by_regime.items():
        rows.sort(key=lambda row: stable_key(freeze["freeze_id"], "uscrn-role", row["station_id"]))
        regime_validation_count = min(validation_count, len(rows) // 5)
        for index, row in enumerate(rows):
            row["role"] = "fit_validation" if index < regime_validation_count else "candidate_fit"
        fit_rows = [row for row in rows if row["role"] == "candidate_fit"]
        fit_rows.sort(key=lambda row: stable_key(freeze["freeze_id"], "uscrn-event", row["station_id"]))
        event_ids = {row["station_id"] for row in fit_rows[:event_count]}
        for row in rows:
            row["subhourly_selected"] = row["station_id"] in event_ids
    return inventory


def inventory() -> None:
    if PARTITION_PATH.exists():
        raise FileExistsError(PARTITION_PATH)
    freeze = read_json(FREEZE_PATH)
    documents = download_documents(freeze)
    stations_path = REPO / next(row["path"] for row in documents if row["path"].endswith("stations.tsv"))
    stations = parse_station_table(freeze, stations_path)
    daymet = build_daymet_candidates(freeze)
    role_counts = Counter((row["regime"], row["role"]) for row in daymet)
    for regime in freeze["regime_frames"]:
        if role_counts[(regime, "candidate_fit")] < freeze["daymet"]["per_regime_candidate_fit"]:
            raise ValueError(f"insufficient candidate-fit lattice: {regime}")
        if role_counts[(regime, "fit_validation")] < freeze["daymet"]["per_regime_fit_validation"]:
            raise ValueError(f"insufficient validation lattice: {regime}")
    write_json(PARTITION_PATH, {
        "confirmation_target_series_accessed": False,
        "daymet_candidate_locations": daymet,
        "documents": documents,
        "freeze_sha256": sha256_path(FREEZE_PATH),
        "partition_id": "a10m1-partition-role-freeze-v1",
        "schema_version": 1,
        "uscrn_station_inventory": stations,
    })
    eligible = [row for row in stations if not row["exclusion_reasons"]]
    print(f"PASS inventory: {len(daymet)} Daymet candidates; {len(stations)} USCRN rows; {len(eligible)} eligible")


def daymet_url(freeze: dict[str, Any], point: dict[str, Any]) -> str:
    years = ",".join(
        str(year)
        for year in range(
            freeze["daymet"]["fit_start_year"],
            freeze["daymet"]["fit_end_year"] + 1,
        )
    )
    query = urllib.parse.urlencode({
        "lat": point["latitude"], "lon": point["longitude"],
        "vars": ",".join(freeze["daymet"]["variables"]),
        "years": years,
    }, safe=",")
    return freeze["daymet"]["service"] + "?" + query


def parse_daymet(raw: bytes, point: dict[str, Any], freeze: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    text = raw.decode("utf-8")
    lines = text.splitlines()
    header_index = next(index for index, line in enumerate(lines) if line.startswith("year,yday,"))
    rows = list(csv.DictReader(lines[header_index:]))
    expected_source = 365 * (freeze["daymet"]["fit_end_year"] - freeze["daymet"]["fit_start_year"] + 1)
    if len(rows) != expected_source:
        raise ValueError(f"Daymet row count {point['point_id']}: {len(rows)}")
    dates: list[str] = []
    observed: list[bool] = []
    fields: dict[str, list[float | None]] = {name: [] for name in DAYMET_FIELDS}
    availability = {name: Counter() for name in DAYMET_FIELDS}
    stats = {name: {"count": 0, "sum": 0.0, "sum_squares": 0.0, "minimum": None, "maximum": None} for name in DAYMET_FIELDS}
    for row in rows:
        year, yday = int(row["year"]), int(row["yday"])
        civil = date(year, 1, 1) + timedelta(days=yday - 1)
        dates.append(civil.isoformat())
        observed.append(True)
        for name, source_field in DAYMET_FIELDS.items():
            value = float(row[source_field])
            fields[name].append(value)
            availability[name][(year, civil.month, "available")] += 1
            summary = stats[name]
            summary["count"] += 1; summary["sum"] += value; summary["sum_squares"] += value * value
            summary["minimum"] = value if summary["minimum"] is None else min(summary["minimum"], value)
            summary["maximum"] = value if summary["maximum"] is None else max(summary["maximum"], value)
        if civil.month == 12 and civil.day == 30 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            dates.append(date(year, 12, 31).isoformat())
            observed.append(False)
            for name in fields:
                fields[name].append(None)
                availability[name][(year, 12, "source_calendar_absence")] += 1
    if len(dates) != (date(freeze["daymet"]["fit_end_year"], 12, 31) - date(freeze["daymet"]["fit_start_year"], 1, 1)).days + 1:
        raise ValueError("Daymet Gregorian axis incomplete")
    elevation_match = re.search(r"Elevation:\s*([-0-9.]+)\s*meters", text)
    payload = {
        "calendar_transform_id": "daymet_official_365_v1", "dates": dates,
        "elevation_m": float(elevation_match.group(1)) if elevation_match else None,
        "fields": fields, "latitude": point["latitude"], "longitude": point["longitude"],
        "missing_reason": {"leap_december_31": "source_calendar_absence"},
        "point_id": point["point_id"], "regime": point["regime"], "role": point["role"],
        "schema_version": 1, "source_id": "daymet_v4r1_single_pixel",
        "source_observed": observed, "tile_id": point["tile_id"], "units": DAYMET_UNITS,
    }
    coverage = {"availability": {
        name: [{"count": count, "month": month, "state": state, "year": year}
               for (year, month, state), count in sorted(counter.items())]
        for name, counter in availability.items()
    }, "statistics": stats}
    return payload, coverage


def request_one_daymet(freeze: dict[str, Any], point: dict[str, Any]) -> dict[str, Any]:
    url = daymet_url(freeze, point)
    try:
        raw = fetch(url)
        parse_daymet(raw, point, freeze)
        path = RAW / "daymet/source" / f"{point['point_id']}.csv.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as target:
            with gzip.GzipFile(filename="", fileobj=target, mode="wb", mtime=0, compresslevel=6) as stream:
                stream.write(raw)
        return {"accessed_at_utc": utc_now(), "bytes": len(raw), "point_id": point["point_id"], "raw_gzip_bytes": path.stat().st_size, "raw_gzip_sha256": sha256_path(path), "source_sha256": sha256_bytes(raw), "status": "accepted", "url": url}
    except Exception as error:  # recorded outcome; quotas decide whether fatal
        return {"accessed_at_utc": utc_now(), "error": f"{type(error).__name__}: {error}", "point_id": point["point_id"], "status": "rejected", "url": url}


def deterministic_tar_gz(path: Path, objects: list[tuple[str, bytes]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        with temp_path.open("wb") as raw:
            with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=9) as zipped:
                with tarfile.open(fileobj=zipped, mode="w|") as archive:
                    for name, logical in objects:
                        info = tarfile.TarInfo(name)
                        info.size = len(logical); info.mtime = 0; info.uid = 0; info.gid = 0
                        info.uname = ""; info.gname = ""; info.mode = 0o644
                        archive.addfile(info, io.BytesIO(logical))
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {"bytes": path.stat().st_size, "path": str(path.relative_to(REPO)), "sha256": sha256_path(path)}


def acquire_daymet() -> None:
    freeze = read_json(FREEZE_PATH)
    partition = read_json(PARTITION_PATH)
    previous = {row["point_id"]: row for row in load_ledger(DAYMET_LEDGER)}
    accepted_counts = Counter()
    for point in partition["daymet_candidate_locations"]:
        if previous.get(point["point_id"], {}).get("status") == "accepted":
            accepted_counts[(point["regime"], point["role"])] += 1
    targets = {"candidate_fit": freeze["daymet"]["per_regime_candidate_fit"], "fit_validation": freeze["daymet"]["per_regime_fit_validation"]}
    candidates = [
        row
        for row in partition["daymet_candidate_locations"]
        if previous.get(row["point_id"], {}).get("status") != "accepted"
    ]
    attempted = len(previous)
    while any(accepted_counts[(regime, role)] < target for regime in freeze["regime_frames"] for role, target in targets.items()):
        batch = []
        for point in candidates:
            key = (point["regime"], point["role"])
            if accepted_counts[key] >= targets[point["role"]]:
                continue
            batch.append(point)
            if len(batch) >= 72:
                break
        if not batch or attempted + len(batch) > freeze["daymet"]["max_requests"]:
            raise RuntimeError(f"Daymet target unavailable within request ceiling: {dict(accepted_counts)}")
        batch_ids = {row["point_id"] for row in batch}
        candidates = [row for row in candidates if row["point_id"] not in batch_ids]
        records = []
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = {executor.submit(request_one_daymet, freeze, point): point for point in batch}
            for future in as_completed(futures):
                record = future.result(); records.append(record)
                if record["status"] == "accepted":
                    point = futures[future]
                    accepted_counts[(point["regime"], point["role"])] += 1
        append_ledger(DAYMET_LEDGER, sorted(records, key=lambda row: row["point_id"]))
        previous.update({row["point_id"]: row for row in records})
        attempted += len(batch)
        print(f"Daymet requests={attempted} accepted={sum(accepted_counts.values())}", flush=True)
    selected = []
    for regime in freeze["regime_frames"]:
        for role, target in targets.items():
            points = [row for row in partition["daymet_candidate_locations"] if row["regime"] == regime and row["role"] == role and previous.get(row["point_id"], {}).get("status") == "accepted"]
            selected.extend(points[:target])
    selected.sort(key=lambda row: (row["regime"], row["role"], row["order"]))
    shard_manifest = []
    aggregate_availability: Counter[tuple[str, str, str, int, int, str]] = Counter()
    aggregate_stats: dict[tuple[str, str, str], dict[str, Any]] = {}
    for shard_index in range(0, len(selected), 24):
        points = selected[shard_index:shard_index + 24]
        objects = []
        for point in points:
            raw_path = RAW / "daymet/source" / f"{point['point_id']}.csv.gz"
            with gzip.open(raw_path, "rb") as stream:
                payload, coverage = parse_daymet(stream.read(), point, freeze)
            logical = canonical_bytes(payload)
            objects.append((f"{point['point_id']}.json", logical))
            for field_name, rows in coverage["availability"].items():
                for row in rows:
                    aggregate_availability[(point["regime"], point["role"], field_name, row["year"], row["month"], row["state"])] += row["count"]
            for field_name, summary in coverage["statistics"].items():
                key = (point["regime"], point["role"], field_name)
                target = aggregate_stats.setdefault(key, {"count": 0, "sum": 0.0, "sum_squares": 0.0, "minimum": None, "maximum": None})
                target["count"] += summary["count"]; target["sum"] += summary["sum"]; target["sum_squares"] += summary["sum_squares"]
                target["minimum"] = summary["minimum"] if target["minimum"] is None else min(target["minimum"], summary["minimum"])
                target["maximum"] = summary["maximum"] if target["maximum"] is None else max(target["maximum"], summary["maximum"])
        path = RAW / "training/daymet" / f"daymet-{shard_index // 24:03d}.tar.gz"
        identity = deterministic_tar_gz(path, objects)
        identity.update({"object_count": len(points), "point_ids": [row["point_id"] for row in points], "schema_version": 1, "source_id": "daymet_v4r1_single_pixel"})
        shard_manifest.append(identity)
    write_json(ARTIFACTS / "daymet-selected-v1.json", {"locations": selected, "schema_version": 1}, replace=True)
    write_json(ARTIFACTS / "daymet-shard-manifest-v1.json", {"schema_version": 1, "shards": shard_manifest}, replace=True)
    write_json(RAW / "daymet/coverage-v1.json", {
        "availability": [{"count": count, "field": field_name, "month": month, "regime": regime, "role": role, "state": state, "year": year} for (regime, role, field_name, year, month, state), count in sorted(aggregate_availability.items())],
        "schema_version": 1,
        "statistics": [{**summary, "field": field_name, "regime": regime, "role": role} for (regime, role, field_name), summary in sorted(aggregate_stats.items())],
    }, replace=True)
    print(f"PASS Daymet: {len(selected)} locations in {len(shard_manifest)} shards")


def uscrn_url(root: str, product: str, year: int, station: str) -> str:
    prefix = "CRND0103" if product == "daily01" else "CRNS0101-05"
    return f"{root}/{year}/{prefix}-{year}-{station}.txt"


def request_uscrn(item: tuple[str, str, int, dict[str, Any]]) -> dict[str, Any]:
    product, root, year, station = item
    url = uscrn_url(root, product, year, station["source_name"])
    path = RAW / "uscrn/source" / product / str(year) / f"{station['station_id']}.txt.gz"
    if path.exists():
        return {"bytes": None, "path": str(path.relative_to(REPO)), "product": product, "station_id": station["station_id"], "status": "existing", "url": url, "year": year}
    try:
        raw = fetch(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as target:
            with gzip.GzipFile(filename="", fileobj=target, mode="wb", mtime=0, compresslevel=6) as stream:
                stream.write(raw)
        return {"accessed_at_utc": utc_now(), "bytes": len(raw), "path": str(path.relative_to(REPO)), "product": product, "source_sha256": sha256_bytes(raw), "station_id": station["station_id"], "status": "accepted", "stored_bytes": path.stat().st_size, "stored_sha256": sha256_path(path), "url": url, "year": year}
    except urllib.error.HTTPError as error:
        if error.code != 404: raise
        return {"accessed_at_utc": utc_now(), "product": product, "station_id": station["station_id"], "status": "unavailable", "url": url, "year": year}


def parse_daily_station(station: dict[str, Any], freeze: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    records = []
    availability = {name: Counter() for name in DAILY_UNITS}
    stats = {name: {"count": 0, "sum": 0.0, "sum_squares": 0.0, "minimum": None, "maximum": None} for name in DAILY_UNITS}
    for year in range(freeze["uscrn"]["daily_start_year"], freeze["uscrn"]["daily_end_year"] + 1):
        path = RAW / "uscrn/source/daily01" / str(year) / f"{station['station_id']}.txt.gz"
        if not path.exists():
            continue
        with gzip.open(path, "rt", encoding="ascii") as stream:
            for line in stream:
                fields = line.split()
                if len(fields) != len(DAILY_HEADERS):
                    raise ValueError(f"Daily01 field count {station['station_id']}/{year}: {len(fields)}")
                row = dict(zip(DAILY_HEADERS, fields))
                civil = datetime.strptime(row["LST_DATE"], "%Y%m%d").date()
                normalized: dict[str, Any] = {"date": civil.isoformat()}
                for name in DAILY_UNITS:
                    value = float(row[name])
                    normalized[name.lower()] = None if value <= -99.0 else value
                    availability[name][(civil.year, civil.month, "missing" if value <= -99.0 else "available")] += 1
                    if value > -99.0:
                        summary = stats[name]
                        summary["count"] += 1; summary["sum"] += value; summary["sum_squares"] += value * value
                        summary["minimum"] = value if summary["minimum"] is None else min(summary["minimum"], value)
                        summary["maximum"] = value if summary["maximum"] is None else max(summary["maximum"], value)
                normalized["surface_temperature_type"] = row["SUR_TEMP_DAILY_TYPE"]
                records.append(normalized)
    payload = {"calendar_transform_id": "uscrn_daily01_lst_v1", "elevation_ft": station["elevation_ft"], "latitude": station["latitude"], "longitude": station["longitude"], "records": records, "regime": station["regime"], "role": station["role"], "schema_version": 1, "source_id": "uscrn_daily01", "station_id": station["station_id"], "units": {key.lower(): value for key, value in DAILY_UNITS.items()}}
    coverage = {"availability": {name.lower(): [{"count": count, "month": month, "state": state, "year": year} for (year, month, state), count in sorted(values.items())] for name, values in availability.items()}, "statistics": {name.lower(): summary for name, summary in stats.items()}}
    return payload, coverage


@dataclass
class EventState:
    zero_run: int = 72
    active: bool = False
    invalid: bool = False
    first_end: datetime | None = None
    last_positive_end: datetime | None = None
    positive: list[tuple[datetime, float, float | None, float | None, float | None, float | None]] = field(default_factory=list)


def valid_value(raw: str) -> float | None:
    value = float(raw)
    return None if value <= -99.0 else value


def event_record(state: EventState) -> dict[str, Any] | None:
    if state.invalid or not state.positive or state.first_end is None or state.last_positive_end is None:
        return None
    lower = state.first_end - timedelta(minutes=5)
    duration = (state.last_positive_end - lower).total_seconds() / 60
    total = sum(row[1] for row in state.positive)
    peak = max(row[1] for row in state.positive)
    peak_end = next(row[0] for row in state.positive if row[1] == peak)
    def complete_mean(index: int) -> float | None:
        values = [row[index] for row in state.positive]
        return None if any(value is None for value in values) else statistics.fmean(float(value) for value in values if value is not None)
    return {"air_temperature_c": complete_mean(2), "depth_mm": total, "duration_min": duration, "peak_ratio": peak * (duration / 5) / total, "relative_humidity_pct": complete_mean(4), "solar_radiation_w_m2": complete_mean(3), "start_lst": lower.isoformat(timespec="minutes"), "time_to_peak_fraction": ((peak_end - timedelta(minutes=2.5)) - lower).total_seconds() / 60 / duration, "wind_speed_1_5m_m_s": complete_mean(5)}


def advance_event(state: EventState, end: datetime, precip: float | None, context: tuple[float | None, float | None, float | None, float | None]) -> dict[str, Any] | None:
    if precip is None:
        state.zero_run = 0
        if state.active: state.invalid = True
        return None
    if precip == 0:
        state.zero_run += 1
        if state.active and state.zero_run == 72:
            result = event_record(state)
            state.active = False; state.invalid = False; state.first_end = None; state.last_positive_end = None; state.positive.clear()
            return result
        return None
    if not state.active:
        if state.zero_run < 72:
            state.zero_run = 0
            return None
        state.active = True; state.invalid = False; state.first_end = end; state.positive.clear()
    state.zero_run = 0; state.last_positive_end = end; state.positive.append((end, precip, *context))
    return None


def parse_subhourly_station(station: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    state = EventState(); events = []; previous: datetime | None = None; years = []
    for year in range(freeze["uscrn"]["daily_start_year"], freeze["uscrn"]["daily_end_year"] + 1):
        path = RAW / "uscrn/source/subhourly01" / str(year) / f"{station['station_id']}.txt.gz"
        if not path.exists(): continue
        years.append(year)
        with gzip.open(path, "rt", encoding="ascii") as stream:
            for line in stream:
                fields = line.split()
                if len(fields) != 23: raise ValueError(f"Subhourly01 field count {station['station_id']}/{year}")
                day = datetime.strptime(fields[3], "%Y%m%d").date(); hhmm = int(fields[4])
                end = datetime.combine(day, civil_time(hhmm // 100, hhmm % 100))
                if previous is not None and end != previous + timedelta(minutes=5):
                    advance_event(state, end, None, (None, None, None, None))
                previous = end
                precip = valid_value(fields[9]); temp = valid_value(fields[8])
                solar = valid_value(fields[10]) if fields[11] == "0" else None
                rh = valid_value(fields[15]) if fields[16] == "0" else None
                wind = valid_value(fields[21]) if fields[22] == "0" else None
                event = advance_event(state, end, precip, (temp, solar, rh, wind))
                if event is not None: events.append(event)
    return {"calendar_transform_id": "uscrn_subhourly01_lst_v1", "event_definition": freeze["event_definition"], "events": events, "regime": station["regime"], "role": station["role"], "schema_version": 1, "source_id": "uscrn_subhourly01", "station_id": station["station_id"], "years_present": years}


def deterministic_json_gzip(path: Path, value: Any) -> dict[str, Any]:
    logical = canonical_bytes(value); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=9) as stream: stream.write(logical)
    return {"bytes": path.stat().st_size, "logical_sha256": sha256_bytes(logical), "path": str(path.relative_to(REPO)), "sha256": sha256_path(path)}


def acquire_uscrn() -> None:
    freeze = read_json(FREEZE_PATH); partition = read_json(PARTITION_PATH)
    stations = [row for row in partition["uscrn_station_inventory"] if not row["exclusion_reasons"]]
    items = []
    for station in stations:
        start = max(freeze["uscrn"]["daily_start_year"], int(station["commissioning"][:4]))
        for year in range(start, freeze["uscrn"]["daily_end_year"] + 1):
            items.append(("daily01", freeze["uscrn"]["daily_root"], year, station))
            if station["subhourly_selected"]:
                items.append(("subhourly01", freeze["uscrn"]["subhourly_root"], year, station))
    if sum(item[0] == "daily01" for item in items) > freeze["uscrn"]["daily_max_station_year_requests"]: raise RuntimeError("Daily01 request ceiling")
    if sum(item[0] == "subhourly01" for item in items) > freeze["uscrn"]["subhourly_max_station_year_requests"]: raise RuntimeError("Subhourly01 request ceiling")
    records = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(request_uscrn, item) for item in items]
        for index, future in enumerate(as_completed(futures), 1):
            record = future.result()
            if record["status"] != "existing": records.append(record)
            if index % 100 == 0: print(f"USCRN requests {index}/{len(items)}", flush=True)
    append_ledger(USCRN_LEDGER, sorted(records, key=lambda row: (row["product"], row["station_id"], row["year"])))
    identities = []
    aggregate_availability: Counter[tuple[str, str, str, int, int, str]] = Counter()
    aggregate_stats: dict[tuple[str, str, str], dict[str, Any]] = {}
    for station in stations:
        daily, daily_coverage = parse_daily_station(station, freeze)
        path = RAW / "training/uscrn/daily" / f"{station['station_id']}.json.gz"
        identity = deterministic_json_gzip(path, daily); identity.update({"event_count": None, "record_count": len(daily["records"]), "regime": station["regime"], "role": station["role"], "source_id": "uscrn_daily01", "station_id": station["station_id"]}); identities.append(identity)
        for field_name, rows in daily_coverage["availability"].items():
            for row in rows:
                aggregate_availability[(station["regime"], station["role"], field_name, row["year"], row["month"], row["state"])] += row["count"]
        for field_name, summary in daily_coverage["statistics"].items():
            key = (station["regime"], station["role"], field_name)
            target = aggregate_stats.setdefault(key, {"count": 0, "sum": 0.0, "sum_squares": 0.0, "minimum": None, "maximum": None})
            target["count"] += summary["count"]; target["sum"] += summary["sum"]; target["sum_squares"] += summary["sum_squares"]
            if summary["minimum"] is not None:
                target["minimum"] = summary["minimum"] if target["minimum"] is None else min(target["minimum"], summary["minimum"])
                target["maximum"] = summary["maximum"] if target["maximum"] is None else max(target["maximum"], summary["maximum"])
        if station["subhourly_selected"]:
            events = parse_subhourly_station(station, freeze)
            event_path = RAW / "training/uscrn/events" / f"{station['station_id']}.json.gz"
            identity = deterministic_json_gzip(event_path, events); identity.update({"event_count": len(events["events"]), "record_count": None, "regime": station["regime"], "role": station["role"], "source_id": "uscrn_subhourly01", "station_id": station["station_id"], "years_present": events["years_present"]}); identities.append(identity)
    write_json(ARTIFACTS / "uscrn-normalized-manifest-v1.json", {"objects": identities, "schema_version": 1}, replace=True)
    write_json(RAW / "uscrn/coverage-v1.json", {
        "availability": [{"count": count, "field": field_name, "month": month, "regime": regime, "role": role, "state": state, "year": year} for (regime, role, field_name, year, month, state), count in sorted(aggregate_availability.items())],
        "schema_version": 1,
        "statistics": [{**summary, "field": field_name, "regime": regime, "role": role} for (regime, role, field_name), summary in sorted(aggregate_stats.items())],
    }, replace=True)
    print(f"PASS USCRN: {len(stations)} daily stations; {sum(row['source_id']=='uscrn_subhourly01' for row in identities)} event stations")


def inherited_objects() -> list[dict[str, Any]]:
    manifest_path = REPO / "docs/work-packages/20260715-a9c-observed-development/artifacts/observed-source-manifest-v1.json"
    manifest = read_json(manifest_path)
    output = []
    for group in ("daymet_normalized_objects", "uscrn_normalized_objects"):
        for row in manifest[group]:
            if row["role"] != "development": continue
            path = REPO / row["path"]
            if sha256_path(path) != row["object_sha256"]: raise ValueError(f"inherited object hash mismatch: {path}")
            output.append({"bytes": path.stat().st_size, "path": row["path"], "role": "development", "sha256": row["object_sha256"], "source_id": row["source_id"], "station_id": row["station_id"]})
    return output


def finalize() -> None:
    freeze = read_json(FREEZE_PATH); partition = read_json(PARTITION_PATH)
    daymet_shards = read_json(ARTIFACTS / "daymet-shard-manifest-v1.json")["shards"]
    uscrn_objects = read_json(ARTIFACTS / "uscrn-normalized-manifest-v1.json")["objects"]
    inherited = inherited_objects()
    selected = read_json(ARTIFACTS / "daymet-selected-v1.json")["locations"]
    daymet_counts = Counter((row["regime"], row["role"]) for row in selected)
    daymet_tiles = defaultdict(set)
    for row in selected: daymet_tiles[(row["regime"], row["role"])].add(row["tile_id"])
    uscrn_counts = Counter((row["regime"], row["role"], row["source_id"]) for row in uscrn_objects)
    event_counts = Counter()
    zero_event = []
    for row in uscrn_objects:
        if row["source_id"] == "uscrn_subhourly01":
            event_counts[(row["regime"], row["role"])] += row["event_count"]
            if row["event_count"] == 0: zero_event.append(row["station_id"])
    tile_roles = defaultdict(set)
    for row in selected: tile_roles[row["tile_id"]].add(row["role"])
    station_roles = defaultdict(set)
    for row in uscrn_objects: station_roles[row["station_id"]].add(row["role"])
    locked_tokens, _ = locked_metadata()
    used_stations = {row["station_id"] for row in uscrn_objects}
    leakage = {
        "confirmation_overlap": sorted(locked_tokens & used_stations),
        "station_role_splits": sorted(key for key, roles in station_roles.items() if len(roles) != 1),
        "tile_role_splits": sorted(key for key, roles in tile_roles.items() if len(roles) != 1),
    }
    if any(leakage.values()): raise ValueError(f"leakage: {leakage}")
    daymet_coverage = read_json(RAW / "daymet/coverage-v1.json")
    uscrn_coverage = read_json(RAW / "uscrn/coverage-v1.json")
    availability_cube = {"rows": [{**row, "source_id": "daymet_v4r1_single_pixel"} for row in daymet_coverage["availability"]] + [{**row, "source_id": "uscrn_daily01"} for row in uscrn_coverage["availability"]], "schema_version": 1}
    normalization_statistics = []
    for source_id, rows in (("daymet_v4r1_single_pixel", daymet_coverage["statistics"]), ("uscrn_daily01", uscrn_coverage["statistics"])):
        for row in rows:
            if row["role"] != "candidate_fit" or row["count"] == 0: continue
            variance = max(0.0, row["sum_squares"] / row["count"] - (row["sum"] / row["count"]) ** 2)
            normalization_statistics.append({"count": row["count"], "field": row["field"], "maximum": row["maximum"], "mean": row["sum"] / row["count"], "minimum": row["minimum"], "regime": row["regime"], "source_id": source_id, "standard_deviation": math.sqrt(variance)})
    coverage_summary = {
        "daymet": [{"locations": daymet_counts[(regime, role)], "regime": regime, "role": role, "tiles": len(daymet_tiles[(regime, role)])} for regime in freeze["regime_frames"] for role in ("candidate_fit", "fit_validation")],
        "uscrn": [{"event_count": event_counts[(regime, role)], "objects": uscrn_counts[(regime, role, source)], "regime": regime, "role": role, "source_id": source} for regime in freeze["regime_frames"] for role in ("candidate_fit", "fit_validation") for source in ("uscrn_daily01", "uscrn_subhourly01")],
        "zero_event_stations": zero_event,
    }
    source_manifest = {
        "confirmation_target_series_accessed": False, "daymet_access": load_ledger(DAYMET_LEDGER),
        "documents": partition["documents"], "freeze_sha256": sha256_path(FREEZE_PATH),
        "manifest_id": "a10m1-source-manifest-v1", "schema_version": 1,
        "uscrn_access": load_ledger(USCRN_LEDGER),
    }
    normalized_manifest = {"coverage_summary": coverage_summary, "daymet_shards": daymet_shards, "freeze_sha256": sha256_path(FREEZE_PATH), "inherited_development_objects": inherited, "leakage_audit": leakage, "manifest_id": "a10m1-normalized-manifest-v1", "schema_version": 1, "uscrn_objects": uscrn_objects}
    transfer_objects = []
    for row in daymet_shards + uscrn_objects:
        transfer_objects.append({"bytes": row["bytes"], "destination_class": "job_local_stage", "path": row["path"], "sha256": row["sha256"]})
    transfer = {"aggregate_bytes": sum(row["bytes"] for row in transfer_objects), "hash_required_before_use": True, "manifest_id": "a10m1-offline-transfer-v1", "objects": transfer_objects, "schema_version": 1, "source_manifest_sha256": sha256_bytes(canonical_bytes(source_manifest)), "small_file_policy": "Daymet locations bundled 24 per archive; USCRN station objects may be tar-bundled at transfer time without changing logical identities"}
    write_json(SOURCE_MANIFEST_PATH, source_manifest, replace=True)
    write_json(NORMALIZED_MANIFEST_PATH, normalized_manifest, replace=True)
    write_json(TRANSFER_MANIFEST_PATH, transfer, replace=True)
    write_json(ARTIFACTS / "coverage-availability-v1.json", coverage_summary, replace=True)
    write_json(ARTIFACTS / "availability-cube-v1.json", availability_cube, replace=True)
    write_json(ARTIFACTS / "normalization-statistics-v1.json", {"fit_role_only": "candidate_fit", "rows": normalization_statistics, "schema_version": 1}, replace=True)
    write_json(ARTIFACTS / "leakage-audit-v1.json", leakage, replace=True)
    print(f"PASS finalize: {len(transfer_objects)} transfer objects, {transfer['aggregate_bytes']} bytes")


def self_test() -> None:
    assert date(2000, 1, 1) + timedelta(days=59) == date(2000, 2, 29)
    assert date(2000, 1, 1) + timedelta(days=364) == date(2000, 12, 30)
    assert date(2001, 1, 1) + timedelta(days=364) == date(2001, 12, 31)
    end = datetime.combine(date(2019, 1, 2), civil_time(0, 0))
    assert (end - timedelta(microseconds=1)).date() == date(2019, 1, 1)
    state = EventState(); start = datetime(2020, 1, 1, 0, 5)
    assert advance_event(state, start, 1.0, (1.0, 2.0, 3.0, 4.0)) is None
    for index in range(71): assert advance_event(state, start + timedelta(minutes=5 * (index + 1)), 0.0, (None, None, None, None)) is None
    assert state.active
    assert advance_event(state, start + timedelta(minutes=360), 0.0, (None, None, None, None)) is not None
    assert not state.active
    print("PASS self-test: calendar, 0000 boundary, and 72-zero event separator")


def verify() -> None:
    self_test()
    freeze = read_json(FREEZE_PATH); partition = read_json(PARTITION_PATH)
    if partition["freeze_sha256"] != sha256_path(FREEZE_PATH): raise ValueError("partition freeze hash")
    normalized = read_json(NORMALIZED_MANIFEST_PATH); transfer = read_json(TRANSFER_MANIFEST_PATH)
    if normalized["freeze_sha256"] != sha256_path(FREEZE_PATH): raise ValueError("normalized freeze hash")
    for group in (normalized["daymet_shards"], normalized["uscrn_objects"], normalized["inherited_development_objects"]):
        for row in group:
            if sha256_path(REPO / row["path"]) != row["sha256"]: raise ValueError(f"hash mismatch: {row['path']}")
    for row in normalized["coverage_summary"]["daymet"]:
        target = freeze["daymet"]["per_regime_candidate_fit" if row["role"] == "candidate_fit" else "per_regime_fit_validation"]
        if row["locations"] != target or row["tiles"] < 2: raise ValueError(f"Daymet coverage: {row}")
    if any(normalized["leakage_audit"].values()): raise ValueError("leakage audit")
    if read_json(SOURCE_MANIFEST_PATH)["confirmation_target_series_accessed"] is not False: raise ValueError("confirmation flag")
    for row in transfer["objects"]:
        if sha256_path(REPO / row["path"]) != row["sha256"]: raise ValueError(f"transfer hash: {row['path']}")
    print(f"PASS verify: six regimes, {len(transfer['objects'])} transfer objects, zero confirmation access")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("self-test", "inventory", "acquire-daymet", "acquire-uscrn", "finalize", "verify"))
    args = parser.parse_args(argv)
    globals()[args.mode.replace("-", "_")]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
