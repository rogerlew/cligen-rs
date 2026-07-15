#!/usr/bin/env python3
"""Inventory us-2015 station parameters without reading daily observations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import struct
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

EXPECTED_CATALOG_SHA256 = (
    "650b59d17adfdeeab00c5346b812d1d5db791978897c2851ce95c24c133a7211"
)
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32_widen(value: float) -> float:
    return float(struct.unpack("<f", struct.pack("<f", value))[0])


def parameter_row(line: str) -> list[float]:
    fields = [line[8 + 6 * index : 14 + 6 * index] for index in range(12)]
    if len(line) < 80 or any(not field.strip() for field in fields):
        raise ValueError(f"expected 12 monthly values: {line!r}")
    return [f32_widen(float(field)) for field in fields]


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


def parse_parameter(path: Path, catalog: sqlite3.Row) -> dict[str, Any]:
    raw = path.read_bytes()
    lines = raw.decode("ascii").splitlines()
    if len(lines) < 10:
        raise ValueError(f"short parameter file: {path}")
    wet_mean_in = parameter_row(lines[3])
    pww = parameter_row(lines[6])
    pwd = parameter_row(lines[7])
    tmax_f = parameter_row(lines[8])
    tmin_f = parameter_row(lines[9])
    wet_fraction = [
        pwd_value / (1.0 - pww_value + pwd_value)
        for pww_value, pwd_value in zip(pww, pwd)
    ]
    monthly_precip_mm = [
        days * fraction * mean_in * 25.4
        for days, fraction, mean_in in zip(MONTH_DAYS, wet_fraction, wet_mean_in)
    ]
    monthly_tmean_c = [
        (((maximum + minimum) / 2.0) - 32.0) * (5.0 / 9.0)
        for maximum, minimum in zip(tmax_f, tmin_f)
    ]
    annual_precip_mm = sum(monthly_precip_mm)
    annual_wet_days = sum(
        days * fraction for days, fraction in zip(MONTH_DAYS, wet_fraction)
    )
    annual_tmean_c = sum(
        days * temperature
        for days, temperature in zip(MONTH_DAYS, monthly_tmean_c)
    ) / 365.0
    july_september = sum(monthly_precip_mm[6:9]) / annual_precip_mm
    april_june = sum(monthly_precip_mm[3:6]) / annual_precip_mm
    october_march = (
        sum(monthly_precip_mm[9:12]) + sum(monthly_precip_mm[0:3])
    ) / annual_precip_mm
    station_id = path.stem
    return {
        "annual_expected_precip_mm": annual_precip_mm,
        "annual_expected_wet_days": annual_wet_days,
        "annual_tmean_c": annual_tmean_c,
        "april_june_precip_fraction": april_june,
        "catalog_description": str(catalog["desc"]).strip(),
        "catalog_elevation_ft": float(catalog["elevation"]),
        "catalog_years": float(catalog["years"]),
        "july_september_precip_fraction": july_september,
        "latitude": float(catalog["latitude"]),
        "longitude": float(catalog["longitude"]),
        "october_march_precip_fraction": october_march,
        "parameter_sha256": sha256(raw),
        "state_code": station_id[:2],
        "station_id": station_id,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--station-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.station_root.resolve()
    catalog_path = root / "2015_stations.db"
    actual_catalog_sha = sha256(catalog_path.read_bytes())
    if actual_catalog_sha != EXPECTED_CATALOG_SHA256:
        raise ValueError(f"catalog identity mismatch: {actual_catalog_sha}")
    connection = sqlite3.connect(catalog_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute("SELECT * FROM stations ORDER BY par").fetchall()
    entries = []
    seen: set[str] = set()
    for row in rows:
        relative = str(row["par"])
        path = root / relative
        if "/" in relative or not path.is_file():
            raise ValueError(f"unexpected catalog path: {relative}")
        entry = parse_parameter(path, row)
        if entry["station_id"] in seen:
            raise ValueError(f"duplicate station: {entry['station_id']}")
        seen.add(entry["station_id"])
        if not all(
            math.isfinite(float(entry[key]))
            for key in (
                "annual_expected_precip_mm",
                "annual_expected_wet_days",
                "annual_tmean_c",
                "latitude",
                "longitude",
            )
        ):
            raise ValueError(f"nonfinite descriptor: {entry['station_id']}")
        entries.append(entry)
    result = {
        "catalog_sha256": actual_catalog_sha,
        "collection": "us-2015",
        "collection_version": "2026.07",
        "descriptor_boundary": (
            "legacy parameter and catalog metadata only; no daily observation was read"
        ),
        "schema_version": 1,
        "station_count": len(entries),
        "stations": entries,
    }
    args.output.write_bytes(canonical_json_bytes(result))
    print(f"inventoried {len(entries)} stations")


if __name__ == "__main__":
    main()
