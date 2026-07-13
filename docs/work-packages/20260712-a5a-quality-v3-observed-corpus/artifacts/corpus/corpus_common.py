#!/usr/bin/env python3
"""Shared deterministic intake helpers for the A5a observed corpus.

Only Python's standard library is used.  Dates are integer tuples so Daymet's
native no-leap calendar is never accidentally coerced to Gregorian.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import platform
import subprocess
import sys
import sysconfig
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

MONTH_DAYS_NOLEAP = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
VARIABLES = ("prcp", "tmax", "tmin")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_environment() -> dict[str, object]:
    """Informational build-host identity; not part of estimator semantics."""
    command_version = lambda command: subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()
    return {
        "machine": platform.machine(),
        "operating_system": platform.system(),
        "operating_system_release": platform.release(),
        "platform_tag": sysconfig.get_platform(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "cargo_version": command_version(["cargo", "--version"]),
        "rustc_version": command_version(["rustc", "--version", "--verbose"]),
    }


def metric_estimator_identity(repo: Path) -> dict[str, object]:
    """Portable source identity for the metrics-v3 Rust/libm DFT helper."""
    paths = [
        repo / "Cargo.lock",
        repo / "Cargo.toml",
        repo / "rust-toolchain.toml",
        repo / "crates/cligen/Cargo.toml",
        repo / "crates/cligen/src/lib.rs",
        repo / "crates/cligen/src/bin/cligen-quality-estimator.rs",
        repo / "crates/cligen/src/quality/estimators.rs",
        repo / "crates/cligen/src/quality/mod.rs",
    ]
    files = {
        path.relative_to(repo).as_posix(): sha256(path.read_bytes()) for path in paths
    }
    lock = tomllib.loads((repo / "Cargo.lock").read_text(encoding="utf-8"))
    libm = next(package for package in lock["package"] if package["name"] == "libm")
    return {
        "algorithm": "quality_metrics_v3_low_frequency_power_fraction",
        "build_command": "cargo build --locked --offline --bin cligen-quality-estimator",
        "compiler": {
            "cargo": subprocess.run(
                ["cargo", "--version", "--verbose"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.strip(),
            "rustc": subprocess.run(
                ["rustc", "--version", "--verbose"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.strip(),
        },
        "files": files,
        "files_sha256": sha256(canonical_json_bytes(files)),
        "libm": {
            "checksum": libm["checksum"],
            "version": libm["version"],
        },
    }


def canonical_json_bytes(value: object) -> bytes:
    text = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return (text + "\n").encode("utf-8")


def write_canonical_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


def deterministic_gzip(data: bytes) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="", mode="wb", compresslevel=9, fileobj=output, mtime=0
    ) as stream:
        stream.write(data)
    result = output.getvalue()
    if result[0:10] != b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff":
        raise ValueError("unexpected non-canonical gzip header")
    return result


def noleap_date(year: int, yday: int) -> tuple[int, int, int]:
    if not 1 <= yday <= 365:
        raise ValueError(f"Daymet yday outside 1..365: {year}/{yday}")
    remaining = yday
    for month, days in enumerate(MONTH_DAYS_NOLEAP, 1):
        if remaining <= days:
            return year, month, remaining
        remaining -= days
    raise AssertionError("unreachable no-leap conversion")


def expected_dates(
    calendar: str, start_year: int, end_year: int
) -> list[tuple[int, int, int]]:
    dates: list[tuple[int, int, int]] = []
    for year in range(start_year, end_year + 1):
        if calendar == "noleap_365":
            dates.extend(noleap_date(year, day) for day in range(1, 366))
        elif calendar == "proleptic_gregorian":
            current = dt.date(year, 1, 1)
            stop = dt.date(year + 1, 1, 1)
            while current < stop:
                dates.append((current.year, current.month, current.day))
                current += dt.timedelta(days=1)
        else:
            raise ValueError(f"unsupported calendar: {calendar}")
    return dates


def next_date(calendar: str, date: tuple[int, int, int]) -> tuple[int, int, int]:
    year, month, day = date
    if calendar == "proleptic_gregorian":
        value = dt.date(year, month, day) + dt.timedelta(days=1)
        return value.year, value.month, value.day
    if calendar != "noleap_365":
        raise ValueError(f"unsupported calendar: {calendar}")
    days = MONTH_DAYS_NOLEAP[month - 1]
    if day < days:
        return year, month, day + 1
    if month < 12:
        return year, month + 1, 1
    return year + 1, 1, 1


def parse_daymet(
    raw: bytes, expected_latitude: float, expected_longitude: float
) -> tuple[dict[tuple[int, int, int], dict[str, float]], dict[str, object]]:
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("Latitude:"):
        raise ValueError("unrecognized Daymet header")
    fields = lines[0].replace("Latitude:", "").replace("Longitude:", "").split()
    latitude, longitude = float(fields[0]), float(fields[1])
    if latitude != expected_latitude or longitude != expected_longitude:
        raise ValueError(
            f"Daymet coordinate mismatch: {(latitude, longitude)} != "
            f"{(expected_latitude, expected_longitude)}"
        )
    elevation_line = next(
        (line for line in lines if line.startswith("Elevation:")), None
    )
    if elevation_line is None:
        raise ValueError("Daymet elevation metadata missing")
    elevation_m = int(elevation_line.split()[1])
    try:
        header = lines.index("year,yday,prcp (mm/day),tmax (deg c),tmin (deg c)")
    except ValueError as error:
        raise ValueError("unexpected Daymet variable header") from error
    records: dict[tuple[int, int, int], dict[str, float]] = {}
    for row in csv.reader(lines[header + 1 :]):
        if len(row) != 5:
            raise ValueError(f"malformed Daymet row: {row!r}")
        date = noleap_date(int(row[0]), int(row[1]))
        if date in records:
            raise ValueError(f"duplicate Daymet date: {date}")
        values = {name: float(value) for name, value in zip(VARIABLES, row[2:])}
        validate_values(date, values)
        records[date] = values
    return records, {
        "calendar": "noleap_365",
        "grid_elevation_m": elevation_m,
        "latitude": latitude,
        "longitude": longitude,
    }


def parse_ghcn(
    raw_gzip: bytes, station_id: str
) -> dict[tuple[int, int, int], dict[str, float]]:
    records: dict[tuple[int, int, int], dict[str, float]] = {}
    with gzip.GzipFile(fileobj=io.BytesIO(raw_gzip), mode="rb") as compressed:
        text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
        for row in csv.reader(text):
            if len(row) < 6 or row[0] != station_id:
                if len(row) < 1 or row[0] != station_id:
                    raise ValueError(f"unexpected GHCN station/row: {row!r}")
                raise ValueError(f"malformed GHCN row: {row!r}")
            element = row[2]
            if element not in ("PRCP", "TMAX", "TMIN") or row[5].strip():
                continue
            date_text = row[1]
            date = (int(date_text[:4]), int(date_text[4:6]), int(date_text[6:8]))
            dt.date(*date)
            variable = {"PRCP": "prcp", "TMAX": "tmax", "TMIN": "tmin"}[element]
            value = int(row[3]) / 10.0
            cell = records.setdefault(date, {})
            if variable in cell:
                raise ValueError(
                    f"duplicate GHCN station/date/element: {date}/{element}"
                )
            cell[variable] = value
    for date, values in records.items():
        validate_values(date, values)
    return records


def validate_values(date: tuple[int, int, int], values: dict[str, float]) -> None:
    for variable, value in values.items():
        if variable not in VARIABLES or not math.isfinite(value):
            raise ValueError(f"invalid {variable} at {date}: {value}")
        if variable == "prcp" and value < 0.0:
            raise ValueError(f"negative precipitation at {date}: {value}")
        if variable in ("tmax", "tmin") and not -100.0 <= value <= 70.0:
            raise ValueError(f"temperature outside intake domain at {date}: {value}")
    if "tmax" in values and "tmin" in values and values["tmax"] < values["tmin"]:
        raise ValueError(f"Tmax below Tmin at {date}")


def logical_records_bytes(
    records: dict[tuple[int, int, int], dict[str, float]],
    start_year: int,
    end_year: int,
) -> bytes:
    lines = ["date,prcp_mm,tmax_c,tmin_c\n"]
    for date in sorted(records):
        if not start_year <= date[0] <= end_year:
            continue
        values = records[date]
        fields = [f"{date[0]:04d}-{date[1]:02d}-{date[2]:02d}"]
        fields.extend(
            "" if name not in values else format(values[name], ".17g")
            for name in VARIABLES
        )
        lines.append(",".join(fields) + "\n")
    return "".join(lines).encode("ascii")


def archive_records(
    archive_path: Path,
    source_kind: str,
    station: dict[str, object],
) -> tuple[dict[tuple[int, int, int], dict[str, float]], dict[str, object]]:
    archived = archive_path.read_bytes()
    if source_kind == "daymet":
        raw = gzip.decompress(archived)
        records, metadata = parse_daymet(
            raw, float(station["latitude"]), float(station["longitude"])
        )
        metadata["source_sha256"] = sha256(raw)
        metadata["source_bytes"] = len(raw)
    elif source_kind == "ghcn":
        records = parse_ghcn(archived, str(station["ghcn_station_id"]))
        metadata = {
            "calendar": "proleptic_gregorian",
            "source_sha256": sha256(archived),
            "source_bytes": len(archived),
        }
    else:
        raise ValueError(source_kind)
    metadata["archive_sha256"] = sha256(archived)
    metadata["archive_bytes"] = len(archived)
    return records, metadata
