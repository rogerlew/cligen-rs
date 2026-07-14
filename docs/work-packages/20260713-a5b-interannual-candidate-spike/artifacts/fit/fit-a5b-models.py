#!/usr/bin/env python3
"""Fit the seven frozen A5b interannual candidates from archived Daymet.

This is an offline, deterministic fitter.  It reads only the A5a corpus
configuration, its content-addressed Daymet archives, and the operator-supplied
US-2015 station cache.  The 2010--2025 Daymet rows are structurally counted but
are never converted to floating point or placed in a fit array.

Usage:
  fit-a5b-models.py <release-cligen> <us-2015-cache> <output-directory>
  fit-a5b-models.py --self-test
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import functools
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable

from jsonschema import Draft202012Validator
import numpy as np
import scipy
from referencing import Registry, Resource


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = ROOT / "docs/work-packages/20260713-a5b-interannual-candidate-spike"
A5A_PACKAGE = ROOT / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
CORPUS_CONFIG = A5A_PACKAGE / "artifacts/corpus/corpus-config-v1.json"
A5A_SOURCE_MANIFEST = A5A_PACKAGE / "artifacts/corpus/source-manifest-v1.json"
A5A_SHA256SUMS = A5A_PACKAGE / "artifacts/corpus/SHA256SUMS"
BUNDLE_SCHEMA = ROOT / "docs/specifications/a5b-augmented-station-v1.schema.json"
BASE_STATION_SCHEMA = ROOT / "docs/specifications/station-document.schema.json"

IMPLEMENTATION_BASE_COMMIT = "10df134607fcf9c22d27aa38a0e27b457f7c176c"
SOURCE_SNAPSHOT_ID = "daymet_v4r1_a5a17_fit1980_2009_noleap_v1"
FIT_RECIPE_ID = "a5b_monthly_state_fit_v1"
COEFFICIENT_SCHEMA = "a5b_interannual_coefficients_v1"
CALENDAR_TRANSFORM = "noleap_365_v1"
FIT_YEARS = tuple(range(1980, 2010))
FULL_YEARS = tuple(range(1980, 2026))
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_NAMES = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)
DAYMET_VARIABLE_HEADER = "year,yday,prcp (mm/day),tmax (deg c),tmin (deg c)"
DAYMET_SELECTION = "All years; all variables"
DAYMET_SOFTWARE_VERSION = "4.0"
DAYMET_HEADER_LINE = (
    f"{DAYMET_SELECTION}; Daymet Software Version {DAYMET_SOFTWARE_VERSION}"
)
DAYMET_CITATION = (
    "Thornton; M.M.; R. Shrestha; Y. Wei; P.E. Thornton; S-C. Kao; and "
    "B.E. Wilson. 2022. Daymet: Daily Surface Weather Data on a 1-km Grid "
    "for North America; Version 4 R1. ORNL DAAC; Oak Ridge; Tennessee; USA. "
    "https://doi.org/10.3334/ORNLDAAC/2129"
)

FEATURE_ORDER = tuple(
    [f"prcp_log1p_total_mm_{month}" for month in MONTH_NAMES]
    + [f"tmax_mean_deg_c_{month}" for month in MONTH_NAMES]
    + [f"tmin_mean_deg_c_{month}" for month in MONTH_NAMES]
)

CANDIDATES = (
    (
        "rank_one_monthly_sd",
        "interannual_rank_one_monthly_sd_v1",
        "a5b_rank_one_monthly_sd_v1",
    ),
    (
        "full_monthly_covariance",
        "interannual_full_monthly_covariance_v1",
        "a5b_full_monthly_covariance_v1",
    ),
    ("fourier_eof", "interannual_fourier_eof_v1", "a5b_fourier_eof_v1"),
    ("vector_ar", "interannual_fourier_eof_var1_v1", "a5b_vector_ar_v1"),
    (
        "gaussian_hmm",
        "interannual_fourier_eof_hmm2_v1",
        "a5b_gaussian_hmm_v1",
    ),
    (
        "spectral_random_phase",
        "interannual_fourier_eof_spectral_v1",
        "a5b_spectral_random_phase_v1",
    ),
    (
        "precip_counterfactual",
        "interannual_fourier_eof_precip_counterfactual_v1",
        "a5b_fourier_eof_precip_counterfactual_v1",
    ),
)
CANDIDATE_IDS = tuple(row[0] for row in CANDIDATES)

TOP_LEVEL_KEYS = {
    "station_schema_version",
    "station_document_role",
    "station_id",
    "base_station",
    "source_lineage",
    "fit_contract",
    "extensions",
}
EXTENSION_KEYS = {
    "candidate_id",
    "station_model",
    "generation_profile",
    "coefficient_payload_schema_version",
    "fit_recipe_id",
    "fit_identity_sha256",
    "runtime_parameter_count",
    "payload",
    "diagnostics",
}
DIAGNOSTIC_REQUIRED_KEYS = {
    "fit_status",
    "warnings",
    "interventions",
    "serialized_numeric_count",
    "payload_sha256",
}
DIAGNOSTIC_ALLOWED_KEYS = DIAGNOSTIC_REQUIRED_KEYS | {
    "retained_rank",
    "explained_variance_fraction",
    "reconstruction_rmse",
    "minimum_eigenvalue",
    "maximum_eigenvalue",
    "em_iterations",
    "em_log_likelihood",
    "em_penalized_objective",
}

SELF_TEST_GOLDEN_SHA256 = (
    "35e5b359017cacf2a8ec9a9a97c988eb447a5db90346f671cafa77dc18552293"
)


class FitError(RuntimeError):
    """A fail-closed source, fit, or output-contract violation."""


@dataclass(frozen=True)
class Intake:
    annual_features: np.ndarray
    daily_precipitation: np.ndarray
    source_lineage: dict[str, Any]
    source_audit: dict[str, Any]


@dataclass(frozen=True)
class EofFit:
    rank: int
    reconstruction: np.ndarray
    scores: np.ndarray
    eigenvalues: np.ndarray
    explained_variance_fraction: float
    reconstruction_rmse: float
    zeroed_eigenvalues: int


def reject_constant(token: str) -> None:
    raise FitError(f"nonfinite JSON token is forbidden: {token}")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FitError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def load_json_strict_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FitError(f"cannot parse {label}: {error}") from error


def load_json_strict(path: Path) -> Any:
    return load_json_strict_bytes(path.read_bytes(), str(path))


def json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, (np.floating, float)):
        result = float(value)
        if not math.isfinite(result):
            raise FitError(f"nonfinite coefficient: {result}")
        return result
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, bool)):
        return value
    raise FitError(f"unsupported JSON value type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            json_ready(value),
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assert_static_identities(
    expected: dict[Path, tuple[str, int]], phase: str
) -> None:
    for path, (expected_sha256, expected_bytes) in expected.items():
        if not path.is_file():
            raise FitError(f"{phase}: frozen input disappeared: {path}")
        if path.stat().st_size != expected_bytes or sha256_path(path) != expected_sha256:
            raise FitError(f"{phase}: frozen input changed during fit: {path}")


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def aggregate_bundle_sha256(items: Iterable[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for station_id, raw in items:
        digest.update(station_id.encode("ascii"))
        digest.update(b"\0")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise FitError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def numeric_count(value: Any) -> int:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return 0
    if isinstance(value, (int, float, np.integer, np.floating)):
        return 1
    if isinstance(value, (list, tuple, np.ndarray)):
        return sum(numeric_count(item) for item in value)
    if isinstance(value, dict):
        return sum(numeric_count(item) for item in value.values())
    raise FitError(f"cannot inventory numeric type {type(value).__name__}")


def ensure_finite_array(value: np.ndarray, label: str) -> None:
    if not np.all(np.isfinite(value)):
        raise FitError(f"{label} contains a nonfinite value")


def parse_sha256sums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if not separator or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise FitError(f"malformed SHA256SUMS row: {line!r}")
        if relative in result:
            raise FitError(f"duplicate SHA256SUMS path: {relative}")
        result[relative] = digest
    return result


def parse_int_token(token: str, label: str) -> int:
    if not re.fullmatch(r"-?(0|[1-9][0-9]*)", token):
        raise FitError(f"{label} is not a canonical integer: {token!r}")
    return int(token)


def parse_finite_token(token: str, label: str) -> float:
    if token.strip() != token or not token:
        raise FitError(f"{label} is not a canonical number: {token!r}")
    try:
        value = float(token)
    except ValueError as error:
        raise FitError(f"{label} is not numeric: {token!r}") from error
    if not math.isfinite(value):
        raise FitError(f"{label} is nonfinite: {token!r}")
    return value


def month_for_ordinal(yday: int) -> int:
    if not 1 <= yday <= 365:
        raise FitError(f"Daymet ordinal day outside 1..365: {yday}")
    remaining = yday
    for month, days in enumerate(MONTH_DAYS):
        if remaining <= days:
            return month
        remaining -= days
    raise AssertionError("unreachable ordinal-day conversion")


def parse_daymet_header(lines: list[str], station: dict[str, Any]) -> dict[str, Any]:
    if len(lines) < 7:
        raise FitError(f"{station['station_id']}: truncated Daymet source")
    coordinate = re.fullmatch(
        r"Latitude: (-?[0-9]+(?:\.[0-9]+)?)  Longitude: (-?[0-9]+(?:\.[0-9]+)?)",
        lines[0],
    )
    lambert = re.fullmatch(
        r"X & Y on Lambert Conformal Conic: "
        r"(-?[0-9]+(?:\.[0-9]+)?) (-?[0-9]+(?:\.[0-9]+)?)",
        lines[1],
    )
    tile = re.fullmatch(r"Tile: ([1-9][0-9]*)", lines[2])
    elevation = re.fullmatch(r"Elevation: (-?(?:0|[1-9][0-9]*)) meters", lines[3])
    if coordinate is None or lambert is None or tile is None or elevation is None:
        raise FitError(f"{station['station_id']}: unexpected Daymet spatial header")
    if lines[4] != DAYMET_HEADER_LINE:
        raise FitError(f"{station['station_id']}: unexpected Daymet selection/version")
    if lines[5] != f"How to cite: {DAYMET_CITATION}":
        raise FitError(f"{station['station_id']}: unexpected Daymet citation")
    if lines[6] != DAYMET_VARIABLE_HEADER:
        raise FitError(f"{station['station_id']}: unexpected Daymet variable header")
    latitude = parse_finite_token(coordinate.group(1), "Daymet latitude")
    longitude = parse_finite_token(coordinate.group(2), "Daymet longitude")
    if latitude != float(station["latitude"]) or longitude != float(
        station["longitude"]
    ):
        raise FitError(
            f"{station['station_id']}: returned coordinates differ from requested"
        )
    return {
        "latitude_deg": latitude,
        "longitude_deg": longitude,
        "x_m": parse_finite_token(lambert.group(1), "Daymet Lambert x"),
        "y_m": parse_finite_token(lambert.group(2), "Daymet Lambert y"),
        "tile": int(tile.group(1)),
        "elevation_m": int(elevation.group(1)),
    }


def read_daymet(
    station: dict[str, Any],
    source: dict[str, Any],
    config: dict[str, Any],
    sums: dict[str, str],
) -> Intake:
    station_id = station["station_id"]
    expected_relative = f"references/observed/a5a-v1/daymet/{station_id}.csv.gz"
    if source["archive_path"] != expected_relative:
        raise FitError(f"{station_id}: unexpected Daymet archive path")
    archive = ROOT / expected_relative
    archive_raw = archive.read_bytes()
    archive_sha = sha256_bytes(archive_raw)
    expected_source_metadata = {
        "availability": "available",
        "calendar": "noleap_365",
        "dataset": "Daymet",
        "dataset_version": "V4 R1",
        "doi": "10.3334/ORNLDAAC/2129",
        "retrieval_date": config["retrieval_date"],
        "variables": {
            "prcp": "mm/day",
            "tmax": "degree_Celsius",
            "tmin": "degree_Celsius",
        },
        "requested_coordinates": {
            "latitude": station["latitude"],
            "longitude": station["longitude"],
        },
    }
    for key, expected in expected_source_metadata.items():
        if source.get(key) != expected:
            raise FitError(f"{station_id}: A5a Daymet {key} metadata differs")
    if archive_sha != source["archive_sha256"]:
        raise FitError(f"{station_id}: A5a Daymet archive hash mismatch")
    if len(archive_raw) != source["archive_bytes"]:
        raise FitError(f"{station_id}: A5a Daymet archive byte count mismatch")
    if sums.get(expected_relative) != archive_sha:
        raise FitError(f"{station_id}: SHA256SUMS Daymet archive hash mismatch")
    try:
        raw = gzip.decompress(archive_raw)
    except gzip.BadGzipFile as error:
        raise FitError(f"{station_id}: malformed Daymet gzip") from error
    raw_sha = sha256_bytes(raw)
    if len(raw) != source["source_bytes"]:
        raise FitError(f"{station_id}: A5a Daymet source byte count mismatch")
    expected_raw = station["daymet_source_sha256"]
    for label, value in (
        ("corpus config", expected_raw),
        ("A5a source_sha256", source["source_sha256"]),
        ("A5a q3_historical_source_sha256", source["q3_historical_source_sha256"]),
    ):
        if raw_sha != value:
            raise FitError(f"{station_id}: decompressed hash differs from {label}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FitError(f"{station_id}: Daymet source is not UTF-8") from error
    lines = text.splitlines()
    grid = parse_daymet_header(lines, station)
    if grid["elevation_m"] != source["grid_elevation_m"]:
        raise FitError(f"{station_id}: grid elevation differs from A5a manifest")

    fit = np.empty((len(FIT_YEARS), 365, 3), dtype=np.float64)
    fit.fill(np.nan)
    seen: dict[int, set[int]] = {year: set() for year in FULL_YEARS}
    post_fit_rows = 0
    reader = csv.reader(io.StringIO("\n".join(lines[7:])), strict=True)
    for row_number, row in enumerate(reader, 8):
        if len(row) != 5:
            raise FitError(f"{station_id}: malformed Daymet row {row_number}")
        year = parse_int_token(row[0], f"{station_id} row {row_number} year")
        yday = parse_int_token(row[1], f"{station_id} row {row_number} yday")
        if year not in seen or not 1 <= yday <= 365:
            raise FitError(
                f"{station_id}: date outside frozen full period at row {row_number}"
            )
        if yday in seen[year]:
            raise FitError(f"{station_id}: duplicate ordinal day {year}/{yday}")
        seen[year].add(yday)
        if year > FIT_YEARS[-1]:
            post_fit_rows += 1
            continue
        values = np.array(
            [
                parse_finite_token(row[2], f"{station_id} {year}/{yday} precipitation"),
                parse_finite_token(row[3], f"{station_id} {year}/{yday} Tmax"),
                parse_finite_token(row[4], f"{station_id} {year}/{yday} Tmin"),
            ],
            dtype=np.float64,
        )
        if values[0] < 0.0:
            raise FitError(f"{station_id}: negative precipitation at {year}/{yday}")
        if not (-100.0 <= values[1] <= 70.0 and -100.0 <= values[2] <= 70.0):
            raise FitError(
                f"{station_id}: temperature outside intake domain at {year}/{yday}"
            )
        if values[1] < values[2]:
            raise FitError(f"{station_id}: Tmax below Tmin at {year}/{yday}")
        fit[year - FIT_YEARS[0], yday - 1, :] = values

    incomplete = {year: len(days) for year, days in seen.items() if len(days) != 365}
    if incomplete:
        raise FitError(f"{station_id}: incomplete Daymet ordinal years: {incomplete}")
    if post_fit_rows != 16 * 365:
        raise FitError(
            f"{station_id}: held-out structural row count is {post_fit_rows}"
        )
    ensure_finite_array(fit, f"{station_id} fit array")

    annual = monthly_feature_matrix(fit)
    lineage = {
        "source_snapshot_id": SOURCE_SNAPSHOT_ID,
        "product": "Daymet V4 R1 daily",
        "product_version": "4.1",
        "doi": "10.3334/ORNLDAAC/2129",
        "retrieval_date": config["retrieval_date"],
        "archive_path": expected_relative,
        "archive_sha256": archive_sha,
        "decompressed_sha256": raw_sha,
        "requested_location": {
            "latitude_deg": station["latitude"],
            "longitude_deg": station["longitude"],
            "station_elevation_ft": station["catalog_elevation_ft"],
        },
        "returned_grid": grid,
        "header": {
            "software_version": DAYMET_SOFTWARE_VERSION,
            "selection": DAYMET_SELECTION,
            "citation": DAYMET_CITATION,
        },
        "variables": ["prcp_mm_day", "tmax_deg_c", "tmin_deg_c"],
        "fit_period": [FIT_YEARS[0], FIT_YEARS[-1]],
        "heldout_excluded_after": FIT_YEARS[-1],
        "calendar_transform": CALENDAR_TRANSFORM,
    }
    audit = {
        "station_id": station_id,
        "archive_path": expected_relative,
        "archive_bytes": len(archive_raw),
        "archive_sha256": archive_sha,
        "decompressed_bytes": len(raw),
        "decompressed_sha256": raw_sha,
        "configured_decompressed_sha256": expected_raw,
        "full_years": [FULL_YEARS[0], FULL_YEARS[-1]],
        "fit_years": len(FIT_YEARS),
        "fit_rows": len(FIT_YEARS) * 365,
        "post_fit_rows": post_fit_rows,
        "returned_grid": grid,
    }
    return Intake(annual, fit[:, :, 0].copy(), lineage, audit)


def monthly_feature_matrix(daily: np.ndarray) -> np.ndarray:
    if daily.shape != (30, 365, 3):
        raise FitError(f"daily fit array has wrong shape: {daily.shape}")
    result = np.empty((30, 36), dtype=np.float64)
    start = 0
    for month, days in enumerate(MONTH_DAYS):
        stop = start + days
        result[:, month] = np.log1p(np.sum(daily[:, start:stop, 0], axis=1))
        result[:, 12 + month] = np.mean(daily[:, start:stop, 1], axis=1)
        result[:, 24 + month] = np.mean(daily[:, start:stop, 2], axis=1)
        start = stop
    result -= np.mean(result, axis=0, keepdims=True)
    ensure_finite_array(result, "centered monthly features")
    return result


def sample_covariance(centered: np.ndarray) -> np.ndarray:
    if centered.ndim != 2 or centered.shape[0] < 2:
        raise FitError("sample covariance requires at least two rows")
    recentered = centered - np.mean(centered, axis=0, keepdims=True)
    result = recentered.T @ recentered / float(centered.shape[0] - 1)
    result = (result + result.T) / 2.0
    ensure_finite_array(result, "sample covariance")
    return result


def fourier_basis() -> np.ndarray:
    result = np.empty((12, 7), dtype=np.float64)
    result[:, 0] = 1.0 / math.sqrt(12.0)
    column = 1
    for harmonic in (1, 2, 3):
        for month in range(12):
            angle = 2.0 * math.pi * harmonic * month / 12.0
            result[month, column] = math.sqrt(2.0 / 12.0) * math.cos(angle)
            result[month, column + 1] = math.sqrt(2.0 / 12.0) * math.sin(angle)
        column += 2
    if not np.allclose(result.T @ result, np.eye(7), rtol=0.0, atol=2e-15):
        raise FitError("real Fourier basis is not orthonormal")
    return result


def ordered_eigenpairs(
    matrix: np.ndarray, zero_relative: float
) -> tuple[np.ndarray, np.ndarray, int]:
    values, vectors = np.linalg.eigh((matrix + matrix.T) / 2.0)
    ensure_finite_array(values, "eigenvalues")
    ensure_finite_array(vectors, "eigenvectors")
    largest = float(np.max(values))
    tolerance = 1e-12 * max(1.0, largest)

    def compare(left: int, right: int) -> int:
        difference = float(values[left] - values[right])
        if abs(difference) > tolerance:
            return -1 if difference > 0.0 else 1
        left_key = tuple(float(item) for item in np.abs(vectors[:, left]))
        right_key = tuple(float(item) for item in np.abs(vectors[:, right]))
        if left_key < right_key:
            return -1
        if left_key > right_key:
            return 1
        return -1 if left < right else (1 if left > right else 0)

    order = sorted(range(values.size), key=functools.cmp_to_key(compare))
    values = values[order]
    vectors = vectors[:, order]
    for column in range(vectors.shape[1]):
        pivot = int(np.argmax(np.abs(vectors[:, column])))
        if vectors[pivot, column] < 0.0:
            vectors[:, column] *= -1.0
    floor = zero_relative * max(1.0, float(values[0]))
    zero = values < floor
    values = values.copy()
    values[zero] = 0.0
    return values, vectors, int(np.count_nonzero(zero))


def fit_common_eof(features: np.ndarray) -> EofFit:
    basis = fourier_basis()
    compressed = np.concatenate(
        [features[:, offset : offset + 12] @ basis for offset in (0, 12, 24)],
        axis=1,
    )
    covariance = sample_covariance(compressed)
    covariance = 0.95 * covariance + 0.05 * np.diag(np.diag(covariance))
    covariance = (covariance + covariance.T) / 2.0
    eigenvalues, eigenvectors, zeroed = ordered_eigenpairs(covariance, 1e-12)
    positive = int(np.count_nonzero(eigenvalues > 0.0))
    if positive < 3:
        raise FitError("Fourier covariance retains fewer than three positive modes")
    total = float(np.sum(eigenvalues[:positive]))
    threshold_rank = int(
        np.searchsorted(np.cumsum(eigenvalues[:positive]), 0.90 * total) + 1
    )
    rank = min(10, max(3, threshold_rank))
    if rank > positive:
        raise FitError("bounded EOF rank exceeds positive mode count")
    retained_values = eigenvalues[:rank]
    retained_vectors = eigenvectors[:, :rank]
    inverse = np.zeros((36, 21), dtype=np.float64)
    for block in range(3):
        inverse[block * 12 : (block + 1) * 12, block * 7 : (block + 1) * 7] = basis
    reconstruction = inverse @ retained_vectors @ np.diag(np.sqrt(retained_values))
    scores = compressed @ retained_vectors @ np.diag(1.0 / np.sqrt(retained_values))
    scores -= np.mean(scores, axis=0, keepdims=True)
    reconstructed = scores @ reconstruction.T
    rmse = float(np.sqrt(np.mean(np.square(features - reconstructed))))
    ensure_finite_array(reconstruction, "EOF reconstruction")
    ensure_finite_array(scores, "standardized EOF scores")
    return EofFit(
        rank=rank,
        reconstruction=reconstruction,
        scores=scores,
        eigenvalues=retained_values,
        explained_variance_fraction=float(np.sum(retained_values) / total),
        reconstruction_rmse=rmse,
        zeroed_eigenvalues=zeroed,
    )


def repaired_cholesky(
    covariance: np.ndarray, shrinkage: float, label: str
) -> tuple[np.ndarray, np.ndarray]:
    repaired = (1.0 - shrinkage) * covariance + shrinkage * np.diag(np.diag(covariance))
    repaired = (repaired + repaired.T) / 2.0
    values, vectors = np.linalg.eigh(repaired)
    ensure_finite_array(values, f"{label} eigenvalues")
    largest = float(np.max(values))
    floor = 1e-10 * max(1.0, largest)
    values = np.maximum(values, floor)
    repaired = vectors @ np.diag(values) @ vectors.T
    repaired = (repaired + repaired.T) / 2.0
    try:
        lower = np.linalg.cholesky(repaired)
    except np.linalg.LinAlgError as error:
        raise FitError(
            f"{label} repaired covariance is not positive definite"
        ) from error
    ensure_finite_array(lower, f"{label} Cholesky factor")
    return lower, values


def lower_rows(lower: np.ndarray) -> list[list[float]]:
    if lower.ndim != 2 or lower.shape[0] != lower.shape[1]:
        raise FitError("lower-triangular factor is not square")
    return [
        [float(value) for value in lower[row, : row + 1]]
        for row in range(lower.shape[0])
    ]


def fit_var(scores: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, list[str]]:
    previous = scores[:-1].T
    following = scores[1:].T
    ridge = 0.01 * float(np.trace(previous @ previous.T)) / scores.shape[1]
    if not math.isfinite(ridge) or ridge <= 0.0:
        raise FitError("VAR ridge coefficient is not positive and finite")
    transition = (following @ previous.T) @ np.linalg.inv(
        previous @ previous.T + ridge * np.eye(scores.shape[1])
    )
    radius = float(np.max(np.abs(np.linalg.eigvals(transition))))
    interventions: list[str] = []
    if not math.isfinite(radius):
        raise FitError("VAR transition spectral radius is nonfinite")
    if radius > 0.98:
        transition *= 0.98 / radius
        interventions.append(f"transition_scaled_from_spectral_radius={radius:.17g}")
    residual = following.T - previous.T @ transition.T
    residual -= np.mean(residual, axis=0, keepdims=True)
    covariance = sample_covariance(residual)
    lower, _ = repaired_cholesky(covariance, 0.10, "VAR innovation")
    ensure_finite_array(transition, "VAR transition")
    return transition, lower, ridge, interventions


def stationary_distribution(transition: np.ndarray) -> np.ndarray:
    denominator = float(transition[1, 0] + transition[0, 1])
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise FitError("HMM transition has no unique stationary distribution")
    result = np.array(
        [transition[1, 0] / denominator, transition[0, 1] / denominator],
        dtype=np.float64,
    )
    result /= np.sum(result)
    ensure_finite_array(result, "HMM stationary distribution")
    return result


def hmm_expectation(
    scores: np.ndarray,
    transition: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
    initial: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    observations, rank = scores.shape
    log_emission = np.empty((observations, 2), dtype=np.float64)
    for state in range(2):
        difference = scores - means[state]
        log_emission[:, state] = -0.5 * (
            rank * math.log(2.0 * math.pi)
            + float(np.sum(np.log(variances[state])))
            + np.sum(np.square(difference) / variances[state], axis=1)
        )
    offsets = np.max(log_emission, axis=1)
    emission = np.exp(log_emission - offsets[:, None])
    alpha = np.empty((observations, 2), dtype=np.float64)
    scales = np.empty(observations, dtype=np.float64)
    alpha[0] = initial * emission[0]
    scales[0] = np.sum(alpha[0])
    if scales[0] <= 0.0:
        raise FitError("HMM forward scale is not positive")
    alpha[0] /= scales[0]
    for year in range(1, observations):
        alpha[year] = (alpha[year - 1] @ transition) * emission[year]
        scales[year] = np.sum(alpha[year])
        if not math.isfinite(float(scales[year])) or scales[year] <= 0.0:
            raise FitError("HMM forward scale is not positive and finite")
        alpha[year] /= scales[year]
    likelihood = float(np.sum(np.log(scales) + offsets))
    if not math.isfinite(likelihood):
        raise FitError("HMM likelihood is nonfinite")

    beta = np.ones((observations, 2), dtype=np.float64)
    for year in range(observations - 2, -1, -1):
        beta[year] = transition @ (emission[year + 1] * beta[year + 1])
        beta[year] /= scales[year + 1]
    gamma = alpha * beta
    gamma /= np.sum(gamma, axis=1, keepdims=True)
    xi = np.empty((observations - 1, 2, 2), dtype=np.float64)
    for year in range(observations - 1):
        cell = (
            alpha[year, :, None]
            * transition
            * (emission[year + 1] * beta[year + 1])[None, :]
        )
        xi[year] = cell / np.sum(cell)
    ensure_finite_array(gamma, "HMM posterior state probabilities")
    ensure_finite_array(xi, "HMM posterior transition probabilities")
    return likelihood, gamma, xi


def hmm_penalized_objective(raw_log_likelihood: float, transition: np.ndarray) -> float:
    if transition.shape != (2, 2) or np.any(transition <= 0.0):
        raise FitError("HMM transition is not a positive 2x2 matrix")
    objective = raw_log_likelihood + 0.5 * float(np.sum(np.log(transition)))
    if not math.isfinite(objective):
        raise FitError("HMM penalized objective is nonfinite")
    return objective


def hmm_objective_converged(
    improvement: float, iteration: int, interventions: list[str]
) -> bool:
    """Apply the frozen penalized-EM convergence rule and roundoff allowance."""
    if improvement < -1e-7:
        raise FitError(f"HMM penalized objective decreased by {improvement:.17g}")
    if improvement < 0.0:
        interventions.append(
            "em_penalized_objective_roundoff_"
            f"iteration={iteration},improvement={improvement:.17g}"
        )
        improvement = 0.0
    return improvement < 1e-8


def fit_hmm(
    scores: np.ndarray,
    annual_precipitation_anomaly: np.ndarray,
    reconstruction: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    int,
    float,
    float,
    list[str],
]:
    order = sorted(
        range(scores.shape[0]),
        key=lambda index: (float(annual_precipitation_anomaly[index]), index),
    )
    labels = np.ones(scores.shape[0], dtype=np.int64)
    labels[order[: scores.shape[0] // 2]] = 0
    if not np.any(labels == 0) or not np.any(labels == 1):
        raise FitError("HMM median split produced an empty state")
    counts = np.full((2, 2), 0.5, dtype=np.float64)
    for left, right in zip(labels[:-1], labels[1:]):
        counts[left, right] += 1.0
    transition = counts / np.sum(counts, axis=1, keepdims=True)
    initial = np.array(
        [float(np.mean(labels == state)) for state in range(2)], dtype=np.float64
    )
    means = np.vstack([np.mean(scores[labels == state], axis=0) for state in range(2)])
    variances = np.vstack(
        [
            np.mean(np.square(scores[labels == state] - means[state]), axis=0)
            for state in range(2)
        ]
    )
    initial_floors = int(np.count_nonzero(variances < 1e-6))
    variances = np.maximum(variances, 1e-6)
    interventions = []
    if initial_floors:
        interventions.append(f"initial_emission_variance_floor_count={initial_floors}")

    previous_objective: float | None = None
    converged = False
    likelihood = math.nan
    objective = math.nan
    for iteration in range(1, 201):
        likelihood, gamma, xi = hmm_expectation(
            scores, transition, means, variances, initial
        )
        objective = hmm_penalized_objective(likelihood, transition)
        if previous_objective is not None:
            improvement = objective - previous_objective
            if hmm_objective_converged(improvement, iteration, interventions):
                converged = True
                break
        transition_counts = np.sum(xi, axis=0) + 0.5
        transition = transition_counts / np.sum(
            transition_counts, axis=1, keepdims=True
        )
        weights = np.sum(gamma, axis=0)
        if np.any(weights <= 0.0):
            raise FitError("HMM EM produced an empty posterior state")
        means = (gamma.T @ scores) / weights[:, None]
        updated = np.empty_like(variances)
        for state in range(2):
            updated[state] = (
                np.sum(gamma[:, state, None] * np.square(scores - means[state]), axis=0)
                / weights[state]
            )
        floor_count = int(np.count_nonzero(updated < 1e-6))
        if floor_count:
            interventions.append(
                f"emission_variance_floor_iteration={iteration},count={floor_count}"
            )
        variances = np.maximum(updated, 1e-6)
        previous_objective = objective
    if not converged:
        raise FitError("HMM EM did not converge in 200 iterations")

    precipitation_means = means @ reconstruction[:12, :].T
    annual_state_means = np.sum(precipitation_means, axis=1)
    relabel = False
    if annual_state_means[0] > annual_state_means[1]:
        relabel = True
    elif annual_state_means[0] == annual_state_means[1]:
        relabel = tuple(means[0]) > tuple(means[1])
    if relabel:
        transition = transition[::-1, ::-1]
        means = means[::-1]
        variances = variances[::-1]
        interventions.append("states_relabelled_by_annual_precipitation_log_mean")
    stationary = stationary_distribution(transition)
    return (
        transition,
        stationary,
        means,
        np.sqrt(variances),
        iteration,
        likelihood,
        objective,
        interventions,
    )


def fit_spectral(scores: np.ndarray) -> np.ndarray:
    """Return pinned, unnormalized amplitudes for a 30-year real DFT.

    A generic FFT is deliberately not used here.  On the production arm64
    environment, repeated ``numpy.fft.rfft`` calls produced two amplitude
    outcomes that differed by one ULP.  The fit artifact is a byte-
    identity contract, so the small fixed transform is evaluated explicitly
    in chronological order with ``math.fsum``.  Bins 1--14 use the negative-
    sine DFT convention; bin 15 is the real Nyquist alternating sum and does
    not evaluate trigonometric functions.  There is no 1/N normalization.
    """
    if scores.ndim != 2 or scores.shape[0] != 30:
        raise FitError(f"spectral score matrix must have shape 30xr: {scores.shape}")
    ensure_finite_array(scores, "spectral training scores")
    rank = scores.shape[1]
    if rank < 1:
        raise FitError("spectral score matrix must contain at least one mode")
    amplitudes = np.empty((rank, 15), dtype=np.float64)
    for mode in range(rank):
        values = [float(scores[year, mode]) for year in range(30)]
        mean = math.fsum(values) / 30.0
        centered = [value - mean for value in values]
        sample_sd = math.sqrt(
            math.fsum(value * value for value in centered) / 29.0
        )
        if not math.isfinite(sample_sd) or sample_sd <= 0.0:
            raise FitError("spectral training score has zero or nonfinite sample SD")
        for frequency in range(1, 15):
            real = math.fsum(
                value
                * math.cos((2.0 * math.pi * frequency * year) / 30.0)
                for year, value in enumerate(centered)
            )
            imaginary = math.fsum(
                -value
                * math.sin((2.0 * math.pi * frequency * year) / 30.0)
                for year, value in enumerate(centered)
            )
            amplitudes[mode, frequency - 1] = math.hypot(real, imaginary)
        nyquist = math.fsum(
            value if year % 2 == 0 else -value
            for year, value in enumerate(centered)
        )
        amplitudes[mode, 14] = abs(nyquist)
    ensure_finite_array(amplitudes, "spectral amplitudes")
    return amplitudes


def fit_precipitation_counterfactual(
    daily_precipitation: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    probabilities = np.empty((12, 4), dtype=np.float64)
    correlations = np.empty(12, dtype=np.float64)
    interventions: list[str] = []
    start = 0
    for month, days in enumerate(MONTH_DAYS):
        stop = start + days
        wet_counts = np.zeros(4, dtype=np.float64)
        total_counts = np.zeros(4, dtype=np.float64)
        left_amounts: list[float] = []
        right_amounts: list[float] = []
        for year in range(daily_precipitation.shape[0]):
            month_values = daily_precipitation[year, start:stop]
            previous_two = 0
            previous_one = 0
            for amount in month_values:
                wet = int(amount > 0.0)
                context = 2 * previous_two + previous_one
                total_counts[context] += 1.0
                wet_counts[context] += wet
                previous_two, previous_one = previous_one, wet
            for left, right in zip(month_values[:-1], month_values[1:]):
                if left > 0.0 and right > 0.0:
                    left_amounts.append(math.log1p(float(left)))
                    right_amounts.append(math.log1p(float(right)))
        probabilities[month] = (wet_counts + 0.5) / (total_counts + 1.0)
        if len(left_amounts) < 3:
            correlations[month] = 0.0
        else:
            correlation = float(np.corrcoef(left_amounts, right_amounts)[0, 1])
            if not math.isfinite(correlation):
                raise FitError(f"month {month + 1} wet-amount correlation is nonfinite")
            clipped = min(0.95, max(-0.95, correlation))
            if clipped != correlation:
                interventions.append(
                    f"month={month + 1},amount_correlation_clamped_from={correlation:.17g}"
                )
            correlations[month] = clipped
        start = stop
    ensure_finite_array(probabilities, "second-order wet probabilities")
    ensure_finite_array(correlations, "wet-amount correlations")
    return probabilities, correlations, interventions


def fit_identity_sha256(
    station_id: str,
    candidate_id: str,
    source_sha256: str,
    par_sha256: str,
    payload_sha256: str,
    fitter_sha256: str,
) -> str:
    material = {
        "candidate_id": candidate_id,
        "coefficient_payload_schema": COEFFICIENT_SCHEMA,
        "fit_recipe_id": FIT_RECIPE_ID,
        "fitter_sha256": fitter_sha256,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "legacy_par_sha256": par_sha256,
        "payload_sha256": payload_sha256,
        "source_decompressed_sha256": source_sha256,
        "station_id": station_id,
    }
    return canonical_sha256(material)


def make_extension(
    candidate_index: int,
    station_id: str,
    source_sha256: str,
    par_sha256: str,
    fitter_sha256: str,
    runtime_parameter_count: int,
    payload: dict[str, Any],
    warnings: list[str] | None = None,
    interventions: list[str] | None = None,
    optional_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_id, station_model, generation_profile = CANDIDATES[candidate_index]
    payload = json_ready(payload)
    payload_sha = canonical_sha256(payload)
    diagnostics: dict[str, Any] = {
        "fit_status": "ok",
        "warnings": sorted(warnings or []),
        "interventions": sorted(interventions or []),
        "serialized_numeric_count": numeric_count(payload),
        "payload_sha256": payload_sha,
    }
    if optional_diagnostics:
        diagnostics.update(json_ready(optional_diagnostics))
    if not set(diagnostics).issubset(DIAGNOSTIC_ALLOWED_KEYS):
        raise FitError(
            f"{candidate_id}: diagnostics have unknown keys "
            f"{sorted(set(diagnostics) - DIAGNOSTIC_ALLOWED_KEYS)}"
        )
    extension = {
        "candidate_id": candidate_id,
        "station_model": station_model,
        "generation_profile": generation_profile,
        "coefficient_payload_schema_version": 1,
        "fit_recipe_id": FIT_RECIPE_ID,
        "fit_identity_sha256": fit_identity_sha256(
            station_id,
            candidate_id,
            source_sha256,
            par_sha256,
            payload_sha,
            fitter_sha256,
        ),
        "runtime_parameter_count": runtime_parameter_count,
        "payload": payload,
        "diagnostics": diagnostics,
    }
    require_exact_keys(extension, EXTENSION_KEYS, f"{candidate_id} extension")
    if not DIAGNOSTIC_REQUIRED_KEYS.issubset(diagnostics):
        raise FitError(f"{candidate_id}: diagnostics omit required keys")
    return extension


def fit_extensions(
    station_id: str,
    features: np.ndarray,
    daily_precipitation: np.ndarray,
    source_sha256: str,
    par_sha256: str,
    fitter_sha256: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if features.shape != (30, 36):
        raise FitError(f"{station_id}: centered feature shape is {features.shape}")
    if daily_precipitation.shape != (30, 365):
        raise FitError(
            f"{station_id}: daily precipitation shape is {daily_precipitation.shape}"
        )
    ensure_finite_array(features, f"{station_id} centered features")
    ensure_finite_array(daily_precipitation, f"{station_id} daily precipitation")

    covariance = sample_covariance(features)
    standard_deviations = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    ensure_finite_array(standard_deviations, "rank-one monthly standard deviations")
    rank_one = make_extension(
        0,
        station_id,
        source_sha256,
        par_sha256,
        fitter_sha256,
        36,
        {"standard_deviations": standard_deviations},
    )

    full_lower, full_values = repaired_cholesky(
        covariance, 0.10, "full monthly covariance"
    )
    full_covariance = make_extension(
        1,
        station_id,
        source_sha256,
        par_sha256,
        fitter_sha256,
        666,
        {"cholesky_lower": lower_rows(full_lower)},
        optional_diagnostics={
            "minimum_eigenvalue": float(np.min(full_values)),
            "maximum_eigenvalue": float(np.max(full_values)),
        },
    )

    eof = fit_common_eof(features)
    eof_optional = {
        "retained_rank": eof.rank,
        "explained_variance_fraction": eof.explained_variance_fraction,
        "reconstruction_rmse": eof.reconstruction_rmse,
        "minimum_eigenvalue": float(np.min(eof.eigenvalues)),
        "maximum_eigenvalue": float(np.max(eof.eigenvalues)),
    }
    eof_interventions = (
        [f"fourier_covariance_zeroed_eigenvalues={eof.zeroed_eigenvalues}"]
        if eof.zeroed_eigenvalues
        else []
    )
    eof_payload = {"rank": eof.rank, "reconstruction": eof.reconstruction}
    fourier_eof = make_extension(
        2,
        station_id,
        source_sha256,
        par_sha256,
        fitter_sha256,
        36 * eof.rank,
        eof_payload,
        interventions=eof_interventions,
        optional_diagnostics=eof_optional,
    )

    transition, innovation_lower, ridge, var_interventions = fit_var(eof.scores)
    vector_ar = make_extension(
        3,
        station_id,
        source_sha256,
        par_sha256,
        fitter_sha256,
        36 * eof.rank + eof.rank * eof.rank + eof.rank * (eof.rank + 1) // 2,
        {
            "rank": eof.rank,
            "reconstruction": eof.reconstruction,
            "transition": transition,
            "innovation_cholesky_lower": lower_rows(innovation_lower),
            "warmup_years": 256,
        },
        interventions=var_interventions,
        optional_diagnostics=eof_optional,
    )

    (
        hmm_transition,
        stationary,
        emission_means,
        emission_sds,
        em_iterations,
        em_likelihood,
        em_penalized_objective,
        hmm_interventions,
    ) = fit_hmm(eof.scores, np.sum(features[:, :12], axis=1), eof.reconstruction)
    gaussian_hmm = make_extension(
        4,
        station_id,
        source_sha256,
        par_sha256,
        fitter_sha256,
        36 * eof.rank + 2 + 4 * eof.rank,
        {
            "rank": eof.rank,
            "reconstruction": eof.reconstruction,
            "transition": hmm_transition,
            "stationary": stationary,
            "emission_means": emission_means,
            "emission_standard_deviations": emission_sds,
        },
        interventions=hmm_interventions,
        optional_diagnostics={
            **eof_optional,
            "em_iterations": em_iterations,
            "em_log_likelihood": em_likelihood,
            "em_penalized_objective": em_penalized_objective,
        },
    )

    amplitudes = fit_spectral(eof.scores)
    spectral = make_extension(
        5,
        station_id,
        source_sha256,
        par_sha256,
        fitter_sha256,
        36 * eof.rank + 15 * eof.rank,
        {
            "rank": eof.rank,
            "reconstruction": eof.reconstruction,
            "non_dc_amplitudes": amplitudes,
        },
        optional_diagnostics=eof_optional,
    )

    wet_probabilities, amount_rho, counterfactual_interventions = (
        fit_precipitation_counterfactual(daily_precipitation)
    )
    counterfactual = make_extension(
        6,
        station_id,
        source_sha256,
        par_sha256,
        fitter_sha256,
        36 * eof.rank + 60,
        {
            "rank": eof.rank,
            "reconstruction": eof.reconstruction,
            "second_order_wet_probabilities": wet_probabilities,
            "amount_rank_rho": amount_rho,
        },
        interventions=[*eof_interventions, *counterfactual_interventions],
        optional_diagnostics=eof_optional,
    )

    extensions = [
        rank_one,
        full_covariance,
        fourier_eof,
        vector_ar,
        gaussian_hmm,
        spectral,
        counterfactual,
    ]
    details = {
        "eof": {
            "rank": eof.rank,
            "retained_eigenvalues": json_ready(eof.eigenvalues),
            "explained_variance_fraction": eof.explained_variance_fraction,
            "reconstruction_rmse": eof.reconstruction_rmse,
            "zeroed_eigenvalues": eof.zeroed_eigenvalues,
        },
        "var": {
            "ridge_lambda": ridge,
            "transition_spectral_radius": float(
                np.max(np.abs(np.linalg.eigvals(transition)))
            ),
        },
        "hmm": {
            "em_iterations": em_iterations,
            "em_log_likelihood": em_likelihood,
            "em_penalized_objective": em_penalized_objective,
        },
        "candidates": [
            {
                "candidate_id": extension["candidate_id"],
                "runtime_parameter_count": extension["runtime_parameter_count"],
                "serialized_numeric_count": extension["diagnostics"][
                    "serialized_numeric_count"
                ],
                "payload_sha256": extension["diagnostics"]["payload_sha256"],
                "fit_identity_sha256": extension["fit_identity_sha256"],
                "warnings": extension["diagnostics"]["warnings"],
                "interventions": extension["diagnostics"]["interventions"],
            }
            for extension in extensions
        ],
    }
    return extensions, details


def fit_contract(fitter_sha256: str) -> dict[str, Any]:
    return {
        "coefficient_payload_schema": COEFFICIENT_SCHEMA,
        "fit_recipe_id": FIT_RECIPE_ID,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "fitter_sha256": fitter_sha256,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "feature_order": list(FEATURE_ORDER),
        "precipitation_transform": "monthly_log1p_total_mm_centered_v1",
        "temperature_transform": "monthly_mean_deg_c_centered_v1",
        "detrending": "center_only_raw_v1",
        "usable_years": 30,
        "fit_seed": "none_deterministic_v1",
    }


def build_bundle(
    station_id: str,
    base_station: dict[str, Any],
    intake: Intake,
    par_sha256: str,
    fitter_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    extensions, details = fit_extensions(
        station_id,
        intake.annual_features.copy(),
        intake.daily_precipitation.copy(),
        intake.source_lineage["decompressed_sha256"],
        par_sha256,
        fitter_sha256,
    )
    bundle = {
        "station_schema_version": 2,
        "station_document_role": "a5b_interannual_candidate_bundle_v1",
        "station_id": station_id,
        "base_station": base_station,
        "source_lineage": intake.source_lineage,
        "fit_contract": fit_contract(fitter_sha256),
        "extensions": extensions,
    }
    validate_bundle_semantics(bundle, par_sha256, fitter_sha256)
    return bundle, details


def expected_runtime_count(candidate_id: str, payload: dict[str, Any]) -> int:
    if candidate_id == "rank_one_monthly_sd":
        return 36
    if candidate_id == "full_monthly_covariance":
        return 666
    rank = payload["rank"]
    if candidate_id == "fourier_eof":
        return 36 * rank
    if candidate_id == "vector_ar":
        return 36 * rank + rank * rank + rank * (rank + 1) // 2
    if candidate_id == "gaussian_hmm":
        return 36 * rank + 2 + 4 * rank
    if candidate_id == "spectral_random_phase":
        return 36 * rank + 15 * rank
    if candidate_id == "precip_counterfactual":
        return 36 * rank + 60
    raise FitError(f"unknown candidate ID: {candidate_id}")


def require_matrix_shape(value: Any, rows: int, columns: int, label: str) -> None:
    if not isinstance(value, list) or len(value) != rows:
        raise FitError(f"{label} requires {rows} rows")
    if any(not isinstance(row, list) or len(row) != columns for row in value):
        raise FitError(f"{label} requires shape {rows}x{columns}")


def require_lower_shape(value: Any, dimension: int, label: str) -> None:
    if not isinstance(value, list) or len(value) != dimension:
        raise FitError(f"{label} requires {dimension} rows")
    if any(
        not isinstance(row, list) or len(row) != index + 1
        for index, row in enumerate(value)
    ):
        raise FitError(f"{label} requires packed lower rows of lengths 1..{dimension}")


def validate_payload_shape(candidate_id: str, payload: dict[str, Any]) -> None:
    expected_keys = {
        "rank_one_monthly_sd": {"standard_deviations"},
        "full_monthly_covariance": {"cholesky_lower"},
        "fourier_eof": {"rank", "reconstruction"},
        "vector_ar": {
            "rank",
            "reconstruction",
            "transition",
            "innovation_cholesky_lower",
            "warmup_years",
        },
        "gaussian_hmm": {
            "rank",
            "reconstruction",
            "transition",
            "stationary",
            "emission_means",
            "emission_standard_deviations",
        },
        "spectral_random_phase": {"rank", "reconstruction", "non_dc_amplitudes"},
        "precip_counterfactual": {
            "rank",
            "reconstruction",
            "second_order_wet_probabilities",
            "amount_rank_rho",
        },
    }[candidate_id]
    require_exact_keys(payload, expected_keys, f"{candidate_id} payload")
    if candidate_id == "rank_one_monthly_sd":
        if len(payload["standard_deviations"]) != 36:
            raise FitError("rank-one payload requires 36 standard deviations")
        return
    if candidate_id == "full_monthly_covariance":
        require_lower_shape(payload["cholesky_lower"], 36, "full covariance Cholesky")
        return
    rank = payload["rank"]
    if not isinstance(rank, int) or isinstance(rank, bool) or not 3 <= rank <= 10:
        raise FitError(f"{candidate_id}: rank outside 3..10")
    require_matrix_shape(payload["reconstruction"], 36, rank, "EOF reconstruction")
    if candidate_id == "vector_ar":
        require_matrix_shape(payload["transition"], rank, rank, "VAR transition")
        require_lower_shape(
            payload["innovation_cholesky_lower"], rank, "VAR innovation"
        )
        if payload["warmup_years"] != 256:
            raise FitError("VAR warmup must be 256 years")
    elif candidate_id == "gaussian_hmm":
        require_matrix_shape(payload["transition"], 2, 2, "HMM transition")
        if len(payload["stationary"]) != 2:
            raise FitError("HMM stationary vector requires two values")
        require_matrix_shape(payload["emission_means"], 2, rank, "HMM means")
        require_matrix_shape(
            payload["emission_standard_deviations"], 2, rank, "HMM SDs"
        )
    elif candidate_id == "spectral_random_phase":
        require_matrix_shape(
            payload["non_dc_amplitudes"], rank, 15, "spectral amplitudes"
        )
    elif candidate_id == "precip_counterfactual":
        require_matrix_shape(
            payload["second_order_wet_probabilities"], 12, 4, "wet probabilities"
        )
        if len(payload["amount_rank_rho"]) != 12:
            raise FitError("counterfactual requires 12 amount correlations")


def validate_bundle_semantics(
    bundle: dict[str, Any], par_sha256: str, fitter_sha256: str
) -> None:
    require_exact_keys(bundle, TOP_LEVEL_KEYS, "augmented station bundle")
    if [extension.get("candidate_id") for extension in bundle["extensions"]] != list(
        CANDIDATE_IDS
    ):
        raise FitError("augmented station extensions are not in the frozen order")
    for index, extension in enumerate(bundle["extensions"]):
        require_exact_keys(extension, EXTENSION_KEYS, f"extension {index}")
        candidate_id, station_model, generation_profile = CANDIDATES[index]
        if (
            extension["station_model"] != station_model
            or extension["generation_profile"] != generation_profile
        ):
            raise FitError(f"{candidate_id}: frozen model/profile identity differs")
        payload = extension["payload"]
        validate_payload_shape(candidate_id, payload)
        diagnostics = extension["diagnostics"]
        if not DIAGNOSTIC_REQUIRED_KEYS.issubset(diagnostics):
            raise FitError(f"{candidate_id}: diagnostics omit required keys")
        if not set(diagnostics).issubset(DIAGNOSTIC_ALLOWED_KEYS):
            raise FitError(f"{candidate_id}: diagnostics contain unknown keys")
        payload_sha = canonical_sha256(payload)
        if diagnostics["payload_sha256"] != payload_sha:
            raise FitError(f"{candidate_id}: payload hash differs")
        if diagnostics["serialized_numeric_count"] != numeric_count(payload):
            raise FitError(f"{candidate_id}: serialized numeric count differs")
        expected_count = expected_runtime_count(candidate_id, payload)
        if extension["runtime_parameter_count"] != expected_count:
            raise FitError(f"{candidate_id}: runtime parameter count differs")
        expected_identity = fit_identity_sha256(
            bundle["station_id"],
            candidate_id,
            bundle["source_lineage"]["decompressed_sha256"],
            par_sha256,
            payload_sha,
            fitter_sha256,
        )
        if extension["fit_identity_sha256"] != expected_identity:
            raise FitError(f"{candidate_id}: fit identity differs")
    canonical_json_bytes(bundle)


def bundle_validator() -> Draft202012Validator:
    schema = load_json_strict(BUNDLE_SCHEMA)
    base_schema = load_json_strict(BASE_STATION_SCHEMA)
    resolved_base_uri = (
        "https://raw.githubusercontent.com/rogerlew/cligen-rs/main/"
        "docs/specifications/station-document.schema.json"
    )
    registry = Registry().with_resources(
        [
            (schema["$id"], Resource.from_contents(schema)),
            (base_schema["$id"], Resource.from_contents(base_schema)),
            (resolved_base_uri, Resource.from_contents(base_schema)),
        ]
    )
    return Draft202012Validator(schema, registry=registry)


def validate_bundle_schema(
    bundle: dict[str, Any], validator: Draft202012Validator
) -> None:
    errors = sorted(
        validator.iter_errors(bundle), key=lambda error: list(error.absolute_path)
    )
    if errors:
        rendered = "; ".join(
            f"/{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
            for error in errors[:8]
        )
        raise FitError(f"augmented station schema validation failed: {rendered}")


def convert_base_station(
    binary: Path, par: Path, work: Path, station_id: str
) -> tuple[dict[str, Any], str]:
    destinations = [
        work / f"{station_id}-base-{repeat}.station.json" for repeat in (1, 2)
    ]
    converted: list[bytes] = []
    for destination in destinations:
        result = subprocess.run(
            [str(binary), "stations", "convert", str(par), str(destination)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise FitError(
                f"{station_id}: cligen stations convert failed: "
                f"{result.stderr.decode('utf-8', errors='replace').strip()}"
            )
        converted.append(destination.read_bytes())
    if converted[0] != converted[1]:
        raise FitError(f"{station_id}: repeated base-station conversion differs")
    document = load_json_strict_bytes(converted[0], f"{station_id} base station")
    return document, sha256_bytes(converted[0])


SOURCE_MANIFEST_KEYS = {
    "source_manifest_version",
    "source_snapshot_id",
    "calendar_transform",
    "fit_period",
    "heldout_period",
    "corpus_config",
    "a5a_source_manifest",
    "stations",
}
SOURCE_STATION_KEYS = {
    "station_id",
    "archive_path",
    "archive_bytes",
    "archive_sha256",
    "decompressed_bytes",
    "decompressed_sha256",
    "configured_decompressed_sha256",
    "full_years",
    "fit_years",
    "fit_rows",
    "post_fit_rows",
    "returned_grid",
}
FIT_MANIFEST_KEYS = {
    "fit_manifest_version",
    "coefficient_payload_schema",
    "fit_recipe_id",
    "implementation_base_commit",
    "fitter",
    "inputs",
    "output_contract",
    "repeatability",
    "diagnostics",
    "stations",
}
FIT_STATION_KEYS = {
    "station_id",
    "station_bundle",
    "station_bundle_sha256",
    "station_bundle_bytes",
    "base_par_sha256",
    "base_station_document_sha256",
    "source_decompressed_sha256",
    "retained_rank",
    "candidate_fits",
}
FIT_CANDIDATE_KEYS = {
    "candidate_id",
    "runtime_parameter_count",
    "serialized_numeric_count",
    "payload_sha256",
    "fit_identity_sha256",
    "fit_status",
}
GOLDEN_KEYS = {
    "fit_golden_version",
    "fit_recipe_id",
    "implementation_base_commit",
    "candidate_order",
    "station_count",
    "bundle_sha256",
    "bundle_aggregate_sha256",
    "source_manifest_sha256",
    "fit_manifest_sha256",
    "diagnostics_sha256",
}


def validate_source_manifest_shape(manifest: dict[str, Any]) -> None:
    require_exact_keys(manifest, SOURCE_MANIFEST_KEYS, "source manifest")
    require_exact_keys(
        manifest["corpus_config"], {"path", "sha256"}, "source manifest corpus config"
    )
    require_exact_keys(
        manifest["a5a_source_manifest"],
        {"path", "sha256"},
        "source manifest A5a source manifest",
    )
    if manifest["source_manifest_version"] != 1:
        raise FitError("source manifest version differs")
    if manifest["source_snapshot_id"] != SOURCE_SNAPSHOT_ID:
        raise FitError("source snapshot identity differs")
    if manifest["calendar_transform"] != CALENDAR_TRANSFORM:
        raise FitError("source calendar transform differs")
    if manifest["fit_period"] != [1980, 2009] or manifest["heldout_period"] != [
        2010,
        2025,
    ]:
        raise FitError("source periods differ")
    if len(manifest["stations"]) != 17:
        raise FitError("source manifest must contain 17 stations")
    for station in manifest["stations"]:
        require_exact_keys(station, SOURCE_STATION_KEYS, "source station record")
        if station["fit_rows"] != 10950 or station["post_fit_rows"] != 5840:
            raise FitError(f"{station['station_id']}: source row counts differ")


def validate_fit_manifest_shape(manifest: dict[str, Any]) -> None:
    require_exact_keys(manifest, FIT_MANIFEST_KEYS, "fit manifest")
    require_exact_keys(
        manifest["fitter"],
        {"path", "sha256", "python_version", "numpy_version", "scipy_version"},
        "fit manifest fitter",
    )
    require_exact_keys(
        manifest["inputs"],
        {
            "corpus_config_sha256",
            "a5a_source_manifest_sha256",
            "cligen_executable_sha256",
            "cligen_executable_bytes",
            "station_collection",
            "station_par_aggregate_sha256",
        },
        "fit manifest inputs",
    )
    require_exact_keys(
        manifest["output_contract"],
        {
            "station_schema_version",
            "station_document_role",
            "bundle_schema_path",
            "bundle_schema_sha256",
            "station_count",
            "candidate_order",
        },
        "fit manifest output contract",
    )
    require_exact_keys(
        manifest["repeatability"],
        {"passes", "byte_identical", "bundle_aggregate_sha256"},
        "fit manifest repeatability",
    )
    require_exact_keys(
        manifest["diagnostics"], {"path", "sha256", "bytes"}, "fit diagnostics"
    )
    if manifest["fit_manifest_version"] != 1:
        raise FitError("fit manifest version differs")
    if manifest["coefficient_payload_schema"] != COEFFICIENT_SCHEMA:
        raise FitError("fit manifest coefficient schema differs")
    if manifest["fit_recipe_id"] != FIT_RECIPE_ID:
        raise FitError("fit manifest recipe differs")
    if len(manifest["stations"]) != 17:
        raise FitError("fit manifest must contain 17 stations")
    for station in manifest["stations"]:
        require_exact_keys(station, FIT_STATION_KEYS, "fit station record")
        if len(station["candidate_fits"]) != 7:
            raise FitError(f"{station['station_id']}: candidate fit count differs")
        for candidate in station["candidate_fits"]:
            require_exact_keys(candidate, FIT_CANDIDATE_KEYS, "candidate fit record")


def validate_golden_shape(golden: dict[str, Any]) -> None:
    require_exact_keys(golden, GOLDEN_KEYS, "fit golden")
    if golden["fit_golden_version"] != 1 or golden["station_count"] != 17:
        raise FitError("fit golden version or station count differs")
    if golden["candidate_order"] != list(CANDIDATE_IDS):
        raise FitError("fit golden candidate order differs")
    if len(golden["bundle_sha256"]) != 17:
        raise FitError("fit golden bundle hash count differs")


def source_manifest(
    config_sha256: str,
    source_manifest_sha256: str,
    audits: list[dict[str, Any]],
) -> dict[str, Any]:
    result = {
        "source_manifest_version": 1,
        "source_snapshot_id": SOURCE_SNAPSHOT_ID,
        "calendar_transform": CALENDAR_TRANSFORM,
        "fit_period": [1980, 2009],
        "heldout_period": [2010, 2025],
        "corpus_config": {
            "path": CORPUS_CONFIG.relative_to(ROOT).as_posix(),
            "sha256": config_sha256,
        },
        "a5a_source_manifest": {
            "path": A5A_SOURCE_MANIFEST.relative_to(ROOT).as_posix(),
            "sha256": source_manifest_sha256,
        },
        "stations": audits,
    }
    validate_source_manifest_shape(result)
    return result


def candidate_fit_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": extension["candidate_id"],
            "runtime_parameter_count": extension["runtime_parameter_count"],
            "serialized_numeric_count": extension["diagnostics"][
                "serialized_numeric_count"
            ],
            "payload_sha256": extension["diagnostics"]["payload_sha256"],
            "fit_identity_sha256": extension["fit_identity_sha256"],
            "fit_status": extension["diagnostics"]["fit_status"],
        }
        for extension in bundle["extensions"]
    ]


def fit_manifest(
    fitter_sha256: str,
    binary: Path,
    config: dict[str, Any],
    config_sha256: str,
    a5a_source_sha256: str,
    par_aggregate_sha256: str,
    bundle_aggregate_sha256: str,
    diagnostics_sha256: str,
    diagnostics_bytes: int,
    station_records: list[dict[str, Any]],
) -> dict[str, Any]:
    result = {
        "fit_manifest_version": 1,
        "coefficient_payload_schema": COEFFICIENT_SCHEMA,
        "fit_recipe_id": FIT_RECIPE_ID,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "fitter": {
            "path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "sha256": fitter_sha256,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
        },
        "inputs": {
            "corpus_config_sha256": config_sha256,
            "a5a_source_manifest_sha256": a5a_source_sha256,
            "cligen_executable_sha256": sha256_path(binary),
            "cligen_executable_bytes": binary.stat().st_size,
            "station_collection": config["station_collection"],
            "station_par_aggregate_sha256": par_aggregate_sha256,
        },
        "output_contract": {
            "station_schema_version": 2,
            "station_document_role": "a5b_interannual_candidate_bundle_v1",
            "bundle_schema_path": BUNDLE_SCHEMA.relative_to(ROOT).as_posix(),
            "bundle_schema_sha256": sha256_path(BUNDLE_SCHEMA),
            "station_count": 17,
            "candidate_order": list(CANDIDATE_IDS),
        },
        "repeatability": {
            "passes": 2,
            "byte_identical": True,
            "bundle_aggregate_sha256": bundle_aggregate_sha256,
        },
        "diagnostics": {
            "path": "diagnostics/fit-diagnostics-v1.json",
            "sha256": diagnostics_sha256,
            "bytes": diagnostics_bytes,
        },
        "stations": station_records,
    }
    validate_fit_manifest_shape(result)
    return result


def verify_frozen_inputs(
    config: dict[str, Any], a5a_source: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    if config.get("config_version") != 1:
        raise FitError("A5a corpus config version differs")
    if config.get("periods") != {
        "evaluation": [2010, 2025],
        "fit": [1980, 2009],
        "full": [1980, 2025],
    }:
        raise FitError("A5a corpus periods differ from the frozen A5b periods")
    stations = config.get("stations")
    if not isinstance(stations, list) or len(stations) != 17:
        raise FitError("A5a corpus config does not contain exactly 17 stations")
    station_ids = [station.get("station_id") for station in stations]
    if len(set(station_ids)) != 17:
        raise FitError("A5a corpus station IDs are not unique")
    source_rows = a5a_source.get("stations")
    if not isinstance(source_rows, list) or len(source_rows) != 17:
        raise FitError("A5a source manifest does not contain exactly 17 stations")
    result: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        station_id = row.get("station_id")
        if station_id in result or station_id not in station_ids:
            raise FitError(f"unexpected or duplicate A5a source station: {station_id}")
        daymet = row.get("sources", {}).get("daymet")
        if not isinstance(daymet, dict) or daymet.get("availability") != "available":
            raise FitError(f"{station_id}: frozen Daymet source is unavailable")
        result[station_id] = daymet
    return result


def execute_fit(binary_arg: str, cache_arg: str, output_arg: str) -> None:
    expected_binary = (ROOT / "target/release/cligen").resolve()
    binary = Path(binary_arg).resolve(strict=True)
    if binary != expected_binary:
        raise FitError(f"release cligen must be {expected_binary}")
    if not binary.is_file() or not binary.stat().st_mode & 0o111:
        raise FitError("release cligen is not an executable file")
    cache = Path(cache_arg).resolve(strict=True)
    if not cache.is_dir():
        raise FitError("US-2015 cache argument is not a directory")
    output = Path(output_arg).resolve()
    if output.exists():
        raise FitError(f"output directory already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    config = load_json_strict(CORPUS_CONFIG)
    a5a_source = load_json_strict(A5A_SOURCE_MANIFEST)
    source_by_station = verify_frozen_inputs(config, a5a_source)
    sums = parse_sha256sums(A5A_SHA256SUMS)
    config_sha = sha256_path(CORPUS_CONFIG)
    a5a_source_sha = sha256_path(A5A_SOURCE_MANIFEST)
    if sums.get(CORPUS_CONFIG.relative_to(ROOT).as_posix()) != config_sha:
        raise FitError("A5a corpus config hash differs from SHA256SUMS")
    if sums.get(A5A_SOURCE_MANIFEST.relative_to(ROOT).as_posix()) != a5a_source_sha:
        raise FitError("A5a source manifest hash differs from SHA256SUMS")
    fitter_sha = sha256_path(Path(__file__).resolve())
    validator = bundle_validator()
    static_identities = {
        path: (sha256_path(path), path.stat().st_size)
        for path in (
            Path(__file__).resolve(),
            CORPUS_CONFIG,
            A5A_SOURCE_MANIFEST,
            A5A_SHA256SUMS,
            BUNDLE_SCHEMA,
            BASE_STATION_SCHEMA,
            binary,
        )
    }

    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        bundle_directory = temporary / "station-bundles"
        diagnostics_directory = temporary / "diagnostics"
        conversion_directory = temporary / ".base-conversion"
        bundle_directory.mkdir()
        diagnostics_directory.mkdir()
        conversion_directory.mkdir()
        audits: list[dict[str, Any]] = []
        station_records: list[dict[str, Any]] = []
        station_diagnostics: list[dict[str, Any]] = []
        bundle_items: list[tuple[str, bytes]] = []
        par_items: list[tuple[str, bytes]] = []

        for station in config["stations"]:
            station_id = station["station_id"]
            par = cache / f"{station_id}.par"
            if not par.is_file():
                raise FitError(f"{station_id}: station parameter file is missing")
            par_raw = par.read_bytes()
            par_sha = sha256_bytes(par_raw)
            if par_sha != station["par_sha256"]:
                raise FitError(f"{station_id}: station parameter hash mismatch")
            par_items.append((station_id, par_raw))
            base_station, base_document_sha = convert_base_station(
                binary, par, conversion_directory, station_id
            )

            first_intake = read_daymet(
                station, source_by_station[station_id], config, sums
            )
            second_intake = read_daymet(
                station, source_by_station[station_id], config, sums
            )
            if (
                first_intake.annual_features.tobytes()
                != second_intake.annual_features.tobytes()
                or first_intake.daily_precipitation.tobytes()
                != second_intake.daily_precipitation.tobytes()
                or first_intake.source_lineage != second_intake.source_lineage
                or first_intake.source_audit != second_intake.source_audit
            ):
                raise FitError(f"{station_id}: repeated source intake differs")

            first_bundle, details = build_bundle(
                station_id, base_station, first_intake, par_sha, fitter_sha
            )
            second_bundle, second_details = build_bundle(
                station_id, base_station, second_intake, par_sha, fitter_sha
            )
            first_bytes = canonical_json_bytes(first_bundle)
            second_bytes = canonical_json_bytes(second_bundle)
            if first_bytes != second_bytes or details != second_details:
                raise FitError(f"{station_id}: repeated fit bytes differ")
            validate_bundle_schema(first_bundle, validator)
            bundle_path = bundle_directory / f"{station_id}.a5b.station.json"
            bundle_path.write_bytes(first_bytes)
            if bundle_path.read_bytes() != first_bytes:
                raise FitError(
                    f"{station_id}: station bundle write verification failed"
                )
            bundle_sha = sha256_bytes(first_bytes)
            bundle_items.append((station_id, first_bytes))
            audits.append(first_intake.source_audit)
            station_records.append(
                {
                    "station_id": station_id,
                    "station_bundle": f"station-bundles/{bundle_path.name}",
                    "station_bundle_sha256": bundle_sha,
                    "station_bundle_bytes": len(first_bytes),
                    "base_par_sha256": par_sha,
                    "base_station_document_sha256": base_document_sha,
                    "source_decompressed_sha256": first_intake.source_lineage[
                        "decompressed_sha256"
                    ],
                    "retained_rank": first_bundle["extensions"][2]["payload"]["rank"],
                    "candidate_fits": candidate_fit_records(first_bundle),
                }
            )
            station_diagnostics.append(
                {
                    "station_id": station_id,
                    "annual_feature_shape": [30, 36],
                    "centered_feature_mean_max_abs": float(
                        np.max(np.abs(np.mean(first_intake.annual_features, axis=0)))
                    ),
                    "daily_precipitation_shape": [30, 365],
                    "source_boundary": {
                        "fit_rows_materialized": first_intake.source_audit["fit_rows"],
                        "post_fit_rows_counted_not_materialized": first_intake.source_audit[
                            "post_fit_rows"
                        ],
                    },
                    **details,
                }
            )
            assert_static_identities(static_identities, f"after {station_id}")

        source_value = source_manifest(config_sha, a5a_source_sha, audits)
        source_bytes = canonical_json_bytes(source_value)
        source_path = temporary / "source-manifest-v1.json"
        source_path.write_bytes(source_bytes)

        diagnostics_value = {
            "diagnostics_version": 1,
            "fit_recipe_id": FIT_RECIPE_ID,
            "stations": station_diagnostics,
        }
        diagnostics_bytes_value = canonical_json_bytes(diagnostics_value)
        diagnostics_path = diagnostics_directory / "fit-diagnostics-v1.json"
        diagnostics_path.write_bytes(diagnostics_bytes_value)

        bundle_aggregate = aggregate_bundle_sha256(bundle_items)
        par_aggregate = aggregate_bundle_sha256(par_items)
        fit_value = fit_manifest(
            fitter_sha,
            binary,
            config,
            config_sha,
            a5a_source_sha,
            par_aggregate,
            bundle_aggregate,
            sha256_bytes(diagnostics_bytes_value),
            len(diagnostics_bytes_value),
            station_records,
        )
        fit_bytes_value = canonical_json_bytes(fit_value)
        fit_path = temporary / "fit-manifest-v1.json"
        fit_path.write_bytes(fit_bytes_value)

        golden_value = {
            "fit_golden_version": 1,
            "fit_recipe_id": FIT_RECIPE_ID,
            "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
            "candidate_order": list(CANDIDATE_IDS),
            "station_count": 17,
            "bundle_sha256": {
                station_id: sha256_bytes(raw) for station_id, raw in bundle_items
            },
            "bundle_aggregate_sha256": bundle_aggregate,
            "source_manifest_sha256": sha256_bytes(source_bytes),
            "fit_manifest_sha256": sha256_bytes(fit_bytes_value),
            "diagnostics_sha256": sha256_bytes(diagnostics_bytes_value),
        }
        validate_golden_shape(golden_value)
        golden_path = temporary / "fit-golden-v1.json"
        golden_path.write_bytes(canonical_json_bytes(golden_value))

        assert_static_identities(static_identities, "before publication")
        shutil.rmtree(conversion_directory)
        for path in temporary.rglob("*.json"):
            load_json_strict(path)
        temporary.rename(output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    print(
        json.dumps(
            {
                "fit_recipe_id": FIT_RECIPE_ID,
                "output": str(output),
                "stations": 17,
                "candidates": 7,
                "bundle_aggregate_sha256": bundle_aggregate,
            },
            sort_keys=True,
        )
    )


def synthetic_daily() -> np.ndarray:
    result = np.empty((30, 365, 3), dtype=np.float64)
    for year in range(30):
        annual_a = math.sin(0.61 * year) + 0.35 * math.cos(0.17 * year)
        annual_b = math.cos(0.43 * year) - 0.20 * math.sin(0.29 * year)
        for day in range(365):
            seasonal = math.sin(2.0 * math.pi * day / 365.0)
            wet = ((day + 3 * year) % 9 in (0, 1)) or ((day + year) % 37 == 0)
            precipitation = (
                0.0
                if not wet
                else 1.2
                + 0.4 * (1.0 + math.cos(2.0 * math.pi * day / 31.0))
                + 0.12 * (year % 7)
                + 0.08 * annual_a
            )
            tmax = 18.0 + 11.0 * seasonal + 0.9 * annual_a + 0.2 * annual_b * seasonal
            tmin = tmax - 7.0 - 0.5 * annual_b
            result[year, day] = (precipitation, tmax, tmin)
    return result


def expect_fit_error(operation: Any, label: str) -> None:
    try:
        operation()
    except FitError:
        return
    raise FitError(f"self-test mutation was accepted: {label}")


def self_test() -> None:
    expect_fit_error(
        lambda: load_json_strict_bytes(b'{"x":1,"x":2}\n', "duplicate mutation"),
        "duplicate JSON key",
    )
    expect_fit_error(
        lambda: load_json_strict_bytes(b'{"x":NaN}\n', "nonfinite mutation"),
        "nonfinite JSON token",
    )
    expect_fit_error(
        lambda: require_exact_keys(
            {"expected": 1, "unknown": 2}, {"expected"}, "mutation"
        ),
        "unknown key",
    )
    roundoff_interventions: list[str] = []
    if not hmm_objective_converged(-5e-8, 17, roundoff_interventions):
        raise FitError("self-test HMM roundoff decrease did not converge")
    if len(roundoff_interventions) != 1 or not roundoff_interventions[0].startswith(
        "em_penalized_objective_roundoff_"
    ):
        raise FitError("self-test HMM roundoff intervention was not recorded")
    expect_fit_error(
        lambda: hmm_objective_converged(-1.0000001e-7, 17, []),
        "HMM penalized-objective decrease beyond roundoff allowance",
    )
    if hmm_objective_converged(1e-7, 17, []):
        raise FitError("self-test HMM material objective improvement converged early")
    test_transition = np.array([[0.75, 0.25], [0.4, 0.6]], dtype=np.float64)
    test_objective = hmm_penalized_objective(-10.0, test_transition)
    expected_objective = -10.0 + 0.5 * sum(
        math.log(float(value)) for value in test_transition.flat
    )
    if test_objective != expected_objective:
        raise FitError("self-test HMM penalized objective differs")
    basis = fourier_basis()
    if not np.array_equal(basis, fourier_basis()):
        raise FitError("self-test Fourier basis repeat differs")
    expect_fit_error(
        lambda: fit_spectral(np.ones((29, 1), dtype=np.float64)),
        "spectral training-year count",
    )
    expect_fit_error(
        lambda: fit_spectral(np.ones((30, 1), dtype=np.float64)),
        "spectral zero training SD",
    )
    nyquist_scores = np.array(
        [[1.0 if year % 2 == 0 else -1.0] for year in range(30)],
        dtype=np.float64,
    )
    nyquist_amplitudes = fit_spectral(nyquist_scores)
    if nyquist_amplitudes.shape != (1, 15) or nyquist_amplitudes[0, 14] != 30.0:
        raise FitError("self-test pinned spectral Nyquist amplitude differs")
    daily = synthetic_daily()
    features = monthly_feature_matrix(daily)
    spectral_scores = fit_common_eof(features).scores
    spectral_reference = fit_spectral(spectral_scores)
    spectral_reference_bytes = spectral_reference.tobytes(order="C")
    for _ in range(64):
        if (
            fit_spectral(spectral_scores).tobytes(order="C")
            != spectral_reference_bytes
        ):
            raise FitError("self-test repeated pinned spectral DFT differs")
    first, details = fit_extensions(
        "zz999999", features.copy(), daily[:, :, 0].copy(), "a" * 64, "b" * 64, "c" * 64
    )
    second, second_details = fit_extensions(
        "zz999999", features.copy(), daily[:, :, 0].copy(), "a" * 64, "b" * 64, "c" * 64
    )
    first_bytes = canonical_json_bytes(first)
    if first_bytes != canonical_json_bytes(second) or details != second_details:
        raise FitError("self-test repeated candidate fit differs")
    for extension in first:
        require_exact_keys(extension, EXTENSION_KEYS, "self-test extension")
        validate_payload_shape(extension["candidate_id"], extension["payload"])
    bad_payload = dict(first[0]["payload"])
    bad_payload["unknown"] = 0
    expect_fit_error(
        lambda: validate_payload_shape("rank_one_monthly_sd", bad_payload),
        "unknown payload key",
    )

    source_station = {
        "station_id": "zz999999",
        "archive_path": "source.csv.gz",
        "archive_bytes": 1,
        "archive_sha256": "0" * 64,
        "decompressed_bytes": 1,
        "decompressed_sha256": "1" * 64,
        "configured_decompressed_sha256": "1" * 64,
        "full_years": [1980, 2025],
        "fit_years": 30,
        "fit_rows": 10950,
        "post_fit_rows": 5840,
        "returned_grid": {},
    }
    source_example = {
        "source_manifest_version": 1,
        "source_snapshot_id": SOURCE_SNAPSHOT_ID,
        "calendar_transform": CALENDAR_TRANSFORM,
        "fit_period": [1980, 2009],
        "heldout_period": [2010, 2025],
        "corpus_config": {"path": "corpus.json", "sha256": "2" * 64},
        "a5a_source_manifest": {"path": "source.json", "sha256": "3" * 64},
        "stations": [dict(source_station) for _ in range(17)],
    }
    validate_source_manifest_shape(source_example)
    expect_fit_error(
        lambda: validate_source_manifest_shape({**source_example, "unknown": 0}),
        "unknown source-manifest key",
    )

    candidate_fit = {
        "candidate_id": "rank_one_monthly_sd",
        "runtime_parameter_count": 36,
        "serialized_numeric_count": 36,
        "payload_sha256": "4" * 64,
        "fit_identity_sha256": "5" * 64,
        "fit_status": "ok",
    }
    fit_station = {
        "station_id": "zz999999",
        "station_bundle": "bundle.json",
        "station_bundle_sha256": "6" * 64,
        "station_bundle_bytes": 1,
        "base_par_sha256": "7" * 64,
        "base_station_document_sha256": "8" * 64,
        "source_decompressed_sha256": "9" * 64,
        "retained_rank": 3,
        "candidate_fits": [dict(candidate_fit) for _ in range(7)],
    }
    fit_example = {
        "fit_manifest_version": 1,
        "coefficient_payload_schema": COEFFICIENT_SCHEMA,
        "fit_recipe_id": FIT_RECIPE_ID,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "fitter": {
            "path": "fit.py",
            "sha256": "a" * 64,
            "python_version": "test",
            "numpy_version": "test",
            "scipy_version": "test",
        },
        "inputs": {
            "corpus_config_sha256": "b" * 64,
            "a5a_source_manifest_sha256": "c" * 64,
            "cligen_executable_sha256": "d" * 64,
            "cligen_executable_bytes": 1,
            "station_collection": {},
            "station_par_aggregate_sha256": "e" * 64,
        },
        "output_contract": {
            "station_schema_version": 2,
            "station_document_role": "a5b_interannual_candidate_bundle_v1",
            "bundle_schema_path": "bundle.schema.json",
            "bundle_schema_sha256": "f" * 64,
            "station_count": 17,
            "candidate_order": list(CANDIDATE_IDS),
        },
        "repeatability": {
            "passes": 2,
            "byte_identical": True,
            "bundle_aggregate_sha256": "0" * 64,
        },
        "diagnostics": {"path": "diagnostics.json", "sha256": "1" * 64, "bytes": 1},
        "stations": [dict(fit_station) for _ in range(17)],
    }
    validate_fit_manifest_shape(fit_example)
    expect_fit_error(
        lambda: validate_fit_manifest_shape({**fit_example, "unknown": 0}),
        "unknown fit-manifest key",
    )

    golden_example = {
        "fit_golden_version": 1,
        "fit_recipe_id": FIT_RECIPE_ID,
        "implementation_base_commit": IMPLEMENTATION_BASE_COMMIT,
        "candidate_order": list(CANDIDATE_IDS),
        "station_count": 17,
        "bundle_sha256": {f"station-{index}": "2" * 64 for index in range(17)},
        "bundle_aggregate_sha256": "3" * 64,
        "source_manifest_sha256": "4" * 64,
        "fit_manifest_sha256": "5" * 64,
        "diagnostics_sha256": "6" * 64,
    }
    validate_golden_shape(golden_example)
    expect_fit_error(
        lambda: validate_golden_shape({**golden_example, "unknown": 0}),
        "unknown fit-golden key",
    )
    summary = {
        "basis_sha256": sha256_bytes(basis.tobytes(order="C")),
        "feature_sha256": sha256_bytes(features.tobytes(order="C")),
        "candidate_payload_sha256": [
            extension["diagnostics"]["payload_sha256"] for extension in first
        ],
        "candidate_runtime_parameter_count": [
            extension["runtime_parameter_count"] for extension in first
        ],
        "candidate_serialized_numeric_count": [
            extension["diagnostics"]["serialized_numeric_count"] for extension in first
        ],
        "spectral_dft_sha256": sha256_bytes(spectral_reference_bytes),
        "spectral_nyquist_amplitude": float(nyquist_amplitudes[0, 14]),
        "retained_rank": first[2]["payload"]["rank"],
        "em_iterations": first[4]["diagnostics"]["em_iterations"],
    }
    observed = canonical_sha256(summary)
    if SELF_TEST_GOLDEN_SHA256.startswith("__"):
        raise FitError(f"self-test golden is not frozen; observed {observed}")
    if observed != SELF_TEST_GOLDEN_SHA256:
        raise FitError(
            f"self-test golden differs: observed {observed}, expected {SELF_TEST_GOLDEN_SHA256}"
        )
    print(
        json.dumps(
            {
                "self_test": "ok",
                "golden_sha256": observed,
                "mutations_rejected": 10,
                "hmm_penalized_objective_policy": "ok",
                "spectral_dft_repetitions": 65,
                "candidate_count": len(first),
            },
            sort_keys=True,
        )
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", nargs="?")
    parser.add_argument("cache", nargs="?")
    parser.add_argument("output", nargs="?")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run deterministic algorithm goldens and rejection mutations without source data",
    )
    arguments = parser.parse_args(argv)
    if arguments.self_test:
        if any((arguments.binary, arguments.cache, arguments.output)):
            parser.error("--self-test does not accept positional arguments")
    elif not all((arguments.binary, arguments.cache, arguments.output)):
        parser.error(
            "binary, cache, and output are required unless --self-test is used"
        )
    return arguments


def main(argv: list[str]) -> int:
    arguments = parse_args(argv)
    try:
        with np.errstate(all="raise"):
            if arguments.self_test:
                self_test()
            else:
                execute_fit(arguments.binary, arguments.cache, arguments.output)
    except (FitError, OSError, subprocess.SubprocessError, FloatingPointError) as error:
        print(f"fit-a5b-models: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
