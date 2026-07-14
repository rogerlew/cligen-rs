#!/usr/bin/env python3
"""Shared, fail-closed utilities for the A5d1 feasibility experiment."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
TARGET = ROOT / "target" / "a5d1-selector-feasibility"
LIBRARY_DIR = TARGET / "libraries"
FEATURE_DIR = TARGET / "features"
CERTIFICATE_DIR = TARGET / "certificates"
PATH_DIR = TARGET / "paths"

CORPUS_CONFIG = (
    ROOT
    / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
    / "artifacts/corpus/corpus-config-v1.json"
)
OBSERVED_TARGETS = CORPUS_CONFIG.with_name("observed-target-corpus-v1.json")
DAYMET_DIR = ROOT / "references/observed/a5a-v1/daymet"
A5A_ARCHIVE = (
    ROOT
    / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
    / "artifacts/baseline-evidence-v1.tar.gz"
)
A5B_BUNDLES = (
    ROOT
    / "docs/work-packages/20260713-a5b-interannual-candidate-spike"
    / "artifacts/fit/evidence-v1/station-bundles"
)
CONTRACT = PACKAGE / "selector-feasibility-contract-v4.json"
FREEZE = PACKAGE / "pre-solver-freeze-v6.json"
LIBRARY_MANIFEST = PACKAGE / "development-library-manifest-v1.json"
FEATURE_MANIFEST = PACKAGE / "year-feature-manifest-v1.json"
MARGINAL_RESULTS = TARGET / "marginal-results-v1.json"
PATH_RESULTS = TARGET / "path-results-v1.json"

MONTH_NAMES = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]
PHYSICAL_FIELD_NAMES = [
    "precipitation_mm", "duration_h", "time_to_peak_fraction",
    "peak_intensity_ratio", "tmax_c", "tmin_c", "radiation_ly",
    "wind_speed_ms", "wind_direction_degrees", "dewpoint_c",
]


def reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON token: {token}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"JSON number overflows binary64: {token}")
    return value


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(
            handle,
            parse_constant=reject_nonfinite,
            parse_float=parse_finite_float,
            object_pairs_hook=reject_duplicate_keys,
        )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def station_records() -> list[dict]:
    config = load_json(CORPUS_CONFIG)
    if not isinstance(config, dict) or not isinstance(config.get("stations"), list):
        raise ValueError("invalid A5a corpus configuration")
    records = sorted(config["stations"], key=lambda row: row["station_id"])
    if len(records) != 17 or len({row["station_id"] for row in records}) != 17:
        raise ValueError("A5d1 requires exactly 17 unique development stations")
    return records


def freeze_identity() -> str:
    freeze = load_json(FREEZE)
    if not isinstance(freeze, dict):
        raise ValueError("pre-solver freeze is not an object")
    claimed = freeze.get("freeze_sha256")
    body = dict(freeze)
    body.pop("freeze_sha256", None)
    actual = canonical_sha256(body)
    if claimed != actual:
        raise ValueError("pre-solver freeze identity mismatch")
    return actual


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_year(year: int) -> int:
    return 366 if is_leap(year) else 365


def parse_cli(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith(" da mo year")),
        None,
    )
    if header_index is None or header_index + 2 >= len(lines):
        raise ValueError(f"daily header missing: {path}")
    rows: list[dict] = []
    for line in lines[header_index + 2 :]:
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) != 13:
            raise ValueError(f"daily row has {len(tokens)} fields: {path}: {line!r}")
        numeric = [float(token) for token in tokens[3:]]
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError(f"non-finite physical value: {path}")
        day, month, year = map(int, tokens[:3])
        rows.append(
            {
                "day": day,
                "month": month,
                "year": year,
                "values": numeric,
                "payload": " ".join(tokens[3:]),
            }
        )
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["year"], []).append(row)
    if sorted(grouped) != list(range(1, len(grouped) + 1)):
        raise ValueError(f"non-contiguous generated years: {path}")
    for year, year_rows in grouped.items():
        if len(year_rows) != days_in_year(year):
            raise ValueError(f"year {year} has wrong day count: {path}")
    return rows


def sample_mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        raise ValueError("mean of empty sequence")
    return math.fsum(items) / len(items)


def sample_variance(values: Iterable[float]) -> float:
    items = list(values)
    if len(items) < 2:
        raise ValueError("sample variance requires two values")
    mean = sample_mean(items)
    return math.fsum((value - mean) ** 2 for value in items) / (len(items) - 1)


def sample_covariance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("sample covariance shape mismatch")
    left_mean = sample_mean(left)
    right_mean = sample_mean(right)
    return math.fsum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right)
    ) / (len(left) - 1)


def pearson(values: list[float]) -> float:
    if len(values) < 3:
        return 0.0
    left, right = values[:-1], values[1:]
    left_mean, right_mean = sample_mean(left), sample_mean(right)
    numerator = math.fsum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right)
    )
    denominator = math.sqrt(
        math.fsum((x - left_mean) ** 2 for x in left)
        * math.fsum((y - right_mean) ** 2 for y in right)
    )
    return numerator / denominator if denominator else 0.0


def low_frequency_fraction(values: list[float]) -> float:
    """Periodogram fraction at periods >= 4 years, excluding the DC bin."""
    import numpy as np

    array = np.asarray(values, dtype=np.float64)
    centered = array - np.mean(array)
    power = np.abs(np.fft.rfft(centered)) ** 2
    frequencies = np.fft.rfftfreq(len(array), d=1.0)
    valid = frequencies > 0.0
    denominator = float(np.sum(power[valid]))
    if denominator == 0.0:
        return 0.0
    selected = valid & (frequencies <= 0.25)
    return float(np.sum(power[selected]) / denominator)


def daymet_annual_series(station_id: str) -> dict[str, list[float]]:
    path = DAYMET_DIR / f"{station_id}.csv.gz"
    annual: dict[int, dict[str, list[float]]] = {}
    with gzip.open(path, mode="rt", encoding="utf-8", newline="") as handle:
        for _ in range(6):
            next(handle)
        reader = csv.DictReader(handle)
        for row in reader:
            year = int(row["year"])
            if not 1980 <= year <= 2009:
                continue
            bucket = annual.setdefault(year, {"p": [], "x": [], "n": []})
            bucket["p"].append(float(row["prcp (mm/day)"]))
            bucket["x"].append(float(row["tmax (deg c)"]))
            bucket["n"].append(float(row["tmin (deg c)"]))
    if sorted(annual) != list(range(1980, 2010)):
        raise ValueError(f"incomplete Daymet fit period: {station_id}")
    return {
        "precip_total_mm": [math.fsum(annual[y]["p"]) for y in sorted(annual)],
        "tmax_mean_c": [sample_mean(annual[y]["x"]) for y in sorted(annual)],
        "tmin_mean_c": [sample_mean(annual[y]["n"]) for y in sorted(annual)],
    }


def dependence_metrics(series: dict[str, list[float]], horizon: int) -> dict[str, float]:
    result: dict[str, float] = {}
    for name in ("precip_total_mm", "tmax_mean_c", "tmin_mean_c"):
        values = series[name][:horizon]
        result[f"{name}.lag1"] = pearson(values)
        result[f"{name}.low_frequency_fraction"] = low_frequency_fraction(values)
    return result


def normalized_distance(
    values: dict[str, float], targets: dict[str, float], scales: dict[str, float]
) -> tuple[float, dict[str, float]]:
    components = {
        name: abs(values[name] - targets[name]) / scales[name]
        for name in sorted(targets)
    }
    return math.fsum(components.values()), components


def synthetic_self_test() -> dict[str, bool]:
    duplicate_rejected = False
    nonfinite_rejected = False
    try:
        json.loads('{"x":1,"x":2}', object_pairs_hook=reject_duplicate_keys)
    except ValueError:
        duplicate_rejected = True
    try:
        json.loads('{"x":NaN}', parse_constant=reject_nonfinite)
    except ValueError:
        nonfinite_rejected = True
    return {
        "duplicate_key_rejected": duplicate_rejected,
        "nonfinite_rejected": nonfinite_rejected,
        "leap_calendar": days_in_year(4) == 366 and days_in_year(100) == 365,
        "dependence_finite": all(
            math.isfinite(value)
            for value in dependence_metrics(
                {
                    "precip_total_mm": [float(i % 7) for i in range(100)],
                    "tmax_mean_c": [float(i % 11) for i in range(100)],
                    "tmin_mean_c": [float(i % 13) for i in range(100)],
                },
                100,
            ).values()
        ),
    }
