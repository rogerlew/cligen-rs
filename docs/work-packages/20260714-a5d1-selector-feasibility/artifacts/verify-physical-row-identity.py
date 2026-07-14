#!/usr/bin/env python3
"""Independently render and byte-audit every A5d1 destination path."""

from __future__ import annotations

import hashlib
import re

from a5d1_common import (
    LIBRARY_MANIFEST,
    PACKAGE,
    PATH_RESULTS,
    ROOT,
    freeze_identity,
    load_json,
    sha256,
    write_json,
)


OUTPUT = PACKAGE / "physical-row-identity-audit-v1.json"
ROW = re.compile(rb"^\s*(\d+)\s+(\d+)\s+(\d+)(.*)$")


def source_rows(path) -> dict[int, list[tuple[int, int, bytes]]]:
    result: dict[int, list[tuple[int, int, bytes]]] = {}
    started = False
    skip_units = False
    for line in path.read_bytes().splitlines():
        if line.startswith(b" da mo year"):
            started, skip_units = True, True
            continue
        if skip_units:
            skip_units = False
            continue
        if not started or not line.strip():
            continue
        match = ROW.match(line)
        if match is None:
            raise ValueError(f"unparseable physical row: {path}: {line!r}")
        day, month, year = map(int, match.group(1, 2, 3))
        result.setdefault(year, []).append((day, month, match.group(4)))
    return result


def independent_render(
    rows: dict[int, list[tuple[int, int, bytes]]], indices: list[int], horizon: int
) -> bytes:
    rendered = bytearray()
    for destination_year in range(1, horizon + 1):
        source_year = indices[destination_year - 1] + 1
        for day, month, physical_suffix in rows[source_year]:
            rendered.extend(f"{day:3d}{month:3d}{destination_year:6d}".encode())
            rendered.extend(physical_suffix)
            rendered.extend(b"\n")
    return bytes(rendered)


def compare_rows(
    rendered: bytes,
    rows: dict[int, list[tuple[int, int, bytes]]],
    indices: list[int],
    horizon: int,
) -> bool:
    expected = [row for index in indices[:horizon] for row in rows[index + 1]]
    candidate = rendered.splitlines()
    if len(candidate) != len(expected):
        return False
    for destination, (source_day, source_month, source_suffix) in zip(candidate, expected):
        match = ROW.match(destination)
        if match is None:
            return False
        if int(match.group(1)) != source_day or int(match.group(2)) != source_month:
            return False
        if match.group(4) != source_suffix:
            return False
    return True


def main() -> None:
    freeze_sha256 = freeze_identity()
    libraries = load_json(LIBRARY_MANIFEST)
    paths = load_json(PATH_RESULTS)
    library_index = {row["station_id"]: row for row in libraries["records"]}
    source_cache = {}
    records = []
    for cell in paths["records"]:
        path_record_path = ROOT / cell["path_record"]["path"]
        path_record = load_json(path_record_path)
        station_id = cell["station_id"]
        if station_id not in source_cache:
            cli = ROOT / library_index[station_id]["cli"]["path"]
            source_cache[station_id] = source_rows(cli)
        rows = source_cache[station_id]
        indices = path_record["source_year_indices_zero_based"]
        rendered_100 = independent_render(rows, indices, 100)
        rendered_30 = independent_render(rows, list(path_record["thirty_year_prefix"]), 30)
        hash_100 = hashlib.sha256(rendered_100).hexdigest()
        hash_30 = hashlib.sha256(rendered_30).hexdigest()
        inv = path_record["invariants"]
        passed = (
            indices[:30] == path_record["thirty_year_prefix"]
            and rendered_100.startswith(rendered_30)
            and compare_rows(rendered_100, rows, indices, 100)
            and compare_rows(rendered_30, rows, indices, 30)
            and hash_100 == inv["rendered_daily_100_sha256"]
            and hash_30 == inv["rendered_daily_30_sha256"]
            and inv["physical_value_interventions"] == 0
        )
        records.append(
            {
                "cell_id": cell["cell_id"],
                "path_record_sha256": sha256(path_record_path),
                "independent_rendered_daily_100_sha256": hash_100,
                "independent_rendered_daily_30_sha256": hash_30,
                "destination_date_and_source_suffix_rows_match": passed,
                "pass": passed,
            }
        )
    value = {
        "physical_row_identity_audit_schema_version": 2,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "definition": "Independent destination-year rendering with exact source physical suffix comparison and exact 30/100 daily-segment prefix",
        "path_results_sha256": sha256(PATH_RESULTS),
        "expected_cells": 306,
        "actual_cells": len(records),
        "unique_cells": len({row["cell_id"] for row in records}),
        "pass_count": sum(row["pass"] for row in records),
        "physical_value_interventions": 0,
        "records": records,
    }
    write_json(OUTPUT, value)
    if not value["actual_cells"] == value["unique_cells"] == value["pass_count"] == 306:
        raise SystemExit("A5d1 independent physical-row audit: FAIL")
    print("A5d1 independent physical-row audit: PASS (306/306)")


if __name__ == "__main__":
    main()
