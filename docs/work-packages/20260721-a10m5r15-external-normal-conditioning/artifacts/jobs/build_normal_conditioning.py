#!/usr/bin/env python3
"""Build the pre-reservation A10M5R15 PRISM/calendar conditioning receipt."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import struct
import tarfile
from pathlib import Path

PACKAGE_ID = "20260721-a10m5r15-external-normal-conditioning"
BUNDLE_ID = "prism_norm91m_9120_4km_m4_m5_v1"
GRID_MANIFEST_SHA256 = "f0eb4b9d4fbe422477c70aebf6eb11e43d329947d6731010edaf315d87de4c9d"
NORMALS_SHA256 = "9af8031291825757a2ce639079479593f53501c7a8ce147d32503fdc481694c2"
RUNTIME_ARCHIVE_SHA256 = "49fe87c83511678094e1033ecc2143d5d833811135934858aab854af78c28292"
SOURCE_ARCHIVE_SHA256 = "c3b832d43de54face39486673843d6c5bc511793804f5678dcb1af809ac0475c"
FIELD_COUNT = 36


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic_bytes(path: Path, value: bytes) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_bytes(value)
    os.replace(partial, path)


def atomic_json(path: Path, value: object) -> None:
    atomic_bytes(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def validate_calendar(record: dict) -> None:
    dates = record.get("dates")
    observed = record.get("source_observed")
    fields = record.get("fields")
    if (
        record.get("calendar_transform_id") != "daymet_official_365_v1"
        or not isinstance(dates, list)
        or len(dates) != 10958
        or not isinstance(observed, list)
        or len(observed) != len(dates)
        or sum(value is True for value in observed) != 10950
        or not isinstance(fields, dict)
    ):
        raise RuntimeError(f"Daymet calendar surface drift: {record.get('point_id')}")
    for name in ("prcp", "tmax", "tmin"):
        values = fields.get(name)
        if not isinstance(values, list) or len(values) != len(dates):
            raise RuntimeError(f"Daymet core field shape drift: {record.get('point_id')}/{name}")
        for index, source_observed in enumerate(observed):
            value = values[index]
            if source_observed and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise RuntimeError(f"Daymet observed core value is invalid: {record.get('point_id')}/{name}")
    for index, text in enumerate(dates):
        date = dt.date.fromisoformat(text)
        if date.month == 2 and date.day == 29 and observed[index] is not True:
            raise RuntimeError("Daymet February 29 must be observed")
        if date.month == 12 and date.day == 31 and date.year % 4 == 0 and observed[index] is not False:
            raise RuntimeError("Daymet leap-year December 31 must be structural null")


def corpus_points(corpus: Path) -> list[dict]:
    manifest = json.loads((corpus / "artifacts/normalized-manifest-v1.json").read_text())
    points = []
    for shard in manifest.get("daymet_shards", []):
        path = corpus / shard["path"]
        if digest(path) != shard["sha256"]:
            raise RuntimeError(f"Daymet shard identity drift: {path.name}")
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                stream = archive.extractfile(member)
                if stream is None:
                    raise RuntimeError(f"Daymet member is not readable: {member.name}")
                record = json.load(stream)
                validate_calendar(record)
                points.append(
                    {
                        "latitude": float(record["latitude"]),
                        "longitude": float(record["longitude"]),
                        "point_id": str(record["point_id"]),
                        "role": str(record["role"]),
                    }
                )
    counts = {role: sum(row["role"] == role for row in points) for role in ("candidate_fit", "fit_validation")}
    if counts != {"candidate_fit": 1200, "fit_validation": 240} or len({row["point_id"] for row in points}) != 1440:
        raise RuntimeError(f"Daymet point-role roster drift: {counts}")
    return points


def validate_grid(root: Path) -> dict:
    manifest_path = root / "grid-manifest.json"
    if digest(manifest_path) != GRID_MANIFEST_SHA256:
        raise RuntimeError("PRISM grid-manifest identity drift")
    manifest = json.loads(manifest_path.read_text())
    expected_transform = [0.041666666667, 0.0, -125.0208333333335, 0.0, -0.041666666667, 49.9375000000005, 0.0, 0.0, 1.0]
    if (
        manifest.get("bundle_id") != BUNDLE_ID
        or manifest.get("width") != 1405
        or manifest.get("height") != 621
        or manifest.get("transform") != expected_transform
        or manifest.get("layout") != "cell-major"
        or manifest.get("byte_order") != "little-endian"
        or manifest.get("scalar_type") != "float32"
        or manifest.get("normals", {}).get("sha256") != NORMALS_SHA256
        or digest(root / "normals.f32le") != NORMALS_SHA256
        or digest(root / "validity-mask.bin") != manifest.get("validity_mask", {}).get("sha256")
    ):
        raise RuntimeError("PRISM runtime grid contract drift")
    layers = manifest.get("layers", [])
    actual = [(row.get("index"), row.get("variable"), row.get("month"), row.get("units")) for row in layers]
    expected = [(block * 12 + month - 1, variable, month, units) for block, (variable, units) in enumerate((("ppt", "millimetres/month"), ("tmax", "degrees Celsius"), ("tmin", "degrees Celsius"))) for month in range(1, 13)]
    if actual != expected:
        raise RuntimeError("PRISM layer order or units drift")
    return manifest


def query(root: Path, manifest: dict, longitude: float, latitude: float) -> tuple[int, int, tuple[float, ...]]:
    transform = manifest["transform"]
    column = math.floor((longitude - transform[2]) / transform[0])
    row = math.floor((latitude - transform[5]) / transform[4])
    width, height = int(manifest["width"]), int(manifest["height"])
    if not (0 <= column < width and 0 <= row < height):
        raise RuntimeError("coordinate is outside the registered PRISM grid")
    cell = row * width + column
    with (root / "validity-mask.bin").open("rb") as stream:
        stream.seek(cell // 8)
        value = stream.read(1)
    if len(value) != 1 or value[0] & (1 << (cell % 8)) == 0:
        raise RuntimeError(
            f"coordinate resolves to a masked PRISM cell: {latitude},{longitude} ({row},{column})"
        )
    with (root / "normals.f32le").open("rb") as stream:
        stream.seek(cell * FIELD_COUNT * 4)
        raw = stream.read(FIELD_COUNT * 4)
    if len(raw) != FIELD_COUNT * 4:
        raise RuntimeError("short PRISM normals cell")
    values = struct.unpack("<36f", raw)
    if any(not math.isfinite(value) or value == -9999.0 for value in values):
        raise RuntimeError("PRISM normals cell contains invalid values")
    if any(values[index] < 0.0 for index in range(12)) or any(values[12 + index] < values[24 + index] for index in range(12)):
        raise RuntimeError("PRISM normals cell violates physical support")
    return row, column, values


def welford(rows: list[dict]) -> tuple[list[float], list[float]]:
    ordered = sorted(rows, key=lambda row: row["point_id"].encode("utf-8"))
    if len(ordered) != 1200:
        raise RuntimeError("candidate-fit normalizer requires exactly 1200 rows")
    mean = [0.0] * FIELD_COUNT
    m2 = [0.0] * FIELD_COUNT
    for count, row in enumerate(ordered, start=1):
        for field, value in enumerate(row["normals"]):
            delta = value - mean[field]
            mean[field] += delta / count
            m2[field] += delta * (value - mean[field])
    scales = [math.sqrt(value / len(ordered)) for value in m2]
    if any(not math.isfinite(value) for value in mean + scales) or any(value == 0.0 for value in scales):
        raise RuntimeError("normalizer contains a zero or non-finite value")
    return mean, scales


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--prism-root", type=Path, required=True)
    parser.add_argument("--sites", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    manifest = validate_grid(options.prism_root)
    points = corpus_points(options.corpus)
    fit_validation_cells = set()
    query_failures = []
    for point in points:
        try:
            row, column, normals = query(
                options.prism_root, manifest, point["longitude"], point["latitude"]
            )
        except RuntimeError as error:
            query_failures.append({**point, "error": str(error)})
            continue
        point.update({"cell": [row, column], "normals": normals})
        if point["role"] == "fit_validation":
            fit_validation_cells.add((row, column))
    sites = json.loads(options.sites.read_text())["sites"]
    if len(sites) != 6:
        raise RuntimeError("temporal-site roster drift")
    site_rows = []
    for site in sites:
        try:
            row, column, normals = query(
                options.prism_root,
                manifest,
                float(site["longitude"]),
                float(site["latitude"]),
            )
        except RuntimeError as error:
            query_failures.append(
                {
                    "error": str(error),
                    "latitude": float(site["latitude"]),
                    "longitude": float(site["longitude"]),
                    "point_id": f"temporal/{site['point_id']}",
                    "role": "temporal_site",
                }
            )
            continue
        site_rows.append(
            {
                "cell": [row, column],
                "normals": normals,
                "point_id": f"temporal/{site['point_id']}",
                "role": "temporal_site",
            }
        )
    if query_failures:
        failures = sorted(
            query_failures,
            key=lambda row: (row["role"].encode("utf-8"), row["point_id"].encode("utf-8")),
        )
        by_role = {
            role: sum(row["role"] == role for row in failures)
            for role in ("candidate_fit", "fit_validation", "temporal_site")
        }
        failure = {
            "bundle_id": BUNDLE_ID,
            "calendar_points_validated": len(points),
            "corpus_query_count": len(points),
            "failure_count": len(failures),
            "failures": failures,
            "failed_by_role": by_role,
            "gates": {
                "all_calendar_surfaces_valid": len(points) == 1440,
                "all_corpus_queries_valid": False,
                "all_temporal_queries_valid": by_role["temporal_site"] == 0,
                "containing_cell_only": True,
                "fallback_or_interpolation_used": False,
                "pre_reservation": True,
            },
            "grid_manifest_sha256": GRID_MANIFEST_SHA256,
            "normals_grid_sha256": NORMALS_SHA256,
            "package_id": PACKAGE_ID,
            "resource_reserved": False,
            "runtime_archive_sha256": RUNTIME_ARCHIVE_SHA256,
            "schema_version": "a10m5r15-normal-conditioning-preflight-failure-1",
            "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
            "terminal": "HOLD-A10M5R15-ENGINEERING-INCOMPLETE",
            "valid": False,
        }
        atomic_json(options.output / "normal-conditioning-preflight-failure.json", failure)
        print(
            "HOLD-A10M5R15-NORMAL-CONDITIONING-PREFLIGHT "
            f"{len(failures)}-MASKED-OR-OUT-OF-COVERAGE"
        )
        raise SystemExit(2)
    means, scales = welford([row for row in points if row["role"] == "candidate_fit"])
    payload = struct.pack("<72d", *(means + scales))
    payload_path = options.output / "normalizer.f64le"
    atomic_bytes(payload_path, payload)
    ordered = sorted(points + site_rows, key=lambda row: row["point_id"].encode("utf-8"))
    point_order = b"".join(row["point_id"].encode("utf-8") + b"\0" for row in ordered)
    normalized = bytearray()
    for row in ordered:
        for field, value in enumerate(row["normals"]):
            normalized.extend(struct.pack("<f", (value - means[field]) / scales[field]))
    archive_path = options.output / "normal-conditioning.f32le"
    atomic_bytes(archive_path, bytes(normalized))
    index_path = options.output / "normal-conditioning-index.json"
    atomic_json(
        index_path,
        {
            "point_ids": [row["point_id"] for row in ordered],
            "roles": [row["role"] for row in ordered],
            "schema_version": "a10m5r15-normal-conditioning-index-1",
        },
    )
    gates = {
        "all_calendar_surfaces_valid": len(points) == 1440,
        "all_corpus_queries_valid": len(points) == 1440,
        "all_temporal_queries_valid": len(site_rows) == 6,
        "candidate_fit_only_normalizer": len([row for row in points if row["role"] == "candidate_fit"]) == 1200,
        "canonical_layer_order_and_units": True,
        "finite_nonzero_population_scales": all(math.isfinite(value) and value > 0.0 for value in scales),
        "source_f32_single_round_normalization": len(normalized) == 1446 * FIELD_COUNT * 4,
        "temporal_sites_match_fit_validation_cells": all(tuple(row["cell"]) in fit_validation_cells for row in site_rows),
    }
    receipt = {
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": digest(archive_path),
        "bundle_id": BUNDLE_ID,
        "candidate_fit_count": 1200,
        "field_count": FIELD_COUNT,
        "fit_validation_count": 240,
        "gates": gates,
        "grid_manifest_sha256": GRID_MANIFEST_SHA256,
        "index_sha256": digest(index_path),
        "normalizer_payload_bytes": len(payload),
        "normalizer_payload_sha256": digest(payload_path),
        "normals_grid_sha256": NORMALS_SHA256,
        "package_id": PACKAGE_ID,
        "point_order_sha256": hashlib.sha256(point_order).hexdigest(),
        "runtime_archive_sha256": RUNTIME_ARCHIVE_SHA256,
        "schema_version": "a10m5r15-normal-conditioning-1",
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "temporal_site_count": 6,
        "valid": bool(gates) and all(gates.values()),
    }
    atomic_json(options.output / "normal-conditioning-receipt.json", receipt)
    if not receipt["valid"]:
        raise RuntimeError("A10M5R15 normal-conditioning preflight failed")
    print(f"A10M5R15-NORMAL-CONDITIONING-PREFLIGHT-PASS {receipt['archive_sha256']}")


if __name__ == "__main__":
    main()
