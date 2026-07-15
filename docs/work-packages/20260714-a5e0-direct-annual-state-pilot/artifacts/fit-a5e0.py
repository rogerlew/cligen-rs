#!/usr/bin/env python3
"""Fit the frozen A5e0 direct annual-state coefficients.

This is a package-local research producer.  The normative algorithm is
SPEC-A5E0-PILOT revision 1; changes here require a new prospective package.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.optimize import root


SOURCE_COMMIT = "27e5e7754bdfafcca649a71d0f5576910433d0d3"
STATIONS = (
    ("ca042319", "dry"),
    ("co051660", "cold"),
    ("ms227840", "wet"),
)
MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
FIT_YEARS = tuple(range(1980, 2010))
WET_THRESHOLD_MM = 0.254
QUADRATURE_NODES = 32
ROOT_XTOL = 1.0e-12
ROOT_MAXFEV = 20_000
COUNT_TOLERANCE = 1.0e-10
MOMENT_TOLERANCE = 1.0e-10
NEGATIVE_TOLERANCE = 1.0e-12


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, root_path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root_path).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(
            stream,
            object_pairs_hook=strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"nonfinite JSON token: {token}")
            ),
        )
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )
    path.write_text(text + "\n", encoding="utf-8")


def read_daymet(path: Path, expected_decompressed_sha256: str) -> dict[int, np.ndarray]:
    raw = gzip.open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != expected_decompressed_sha256:
        raise ValueError(f"decompressed Daymet hash mismatch: {path}")
    lines = raw.decode("utf-8").splitlines()
    if len(lines) < 8:
        raise ValueError(f"truncated Daymet file: {path}")
    if lines[6] != "year,yday,prcp (mm/day),tmax (deg c),tmin (deg c)":
        raise ValueError(f"unexpected Daymet columns: {path}")
    rows: dict[int, list[tuple[int, float, float, float]]] = {}
    for record in csv.reader(lines[7:]):
        if len(record) != 5:
            raise ValueError(f"malformed Daymet row: {path}")
        year, yday = int(record[0]), int(record[1])
        if year not in FIT_YEARS:
            continue
        values = tuple(float(item) for item in record[2:])
        if not all(math.isfinite(item) for item in values):
            raise ValueError(f"nonfinite Daymet value: {path}")
        prcp, tmax, tmin = values
        if prcp < 0.0 or tmax < tmin:
            raise ValueError(f"invalid Daymet physical value: {path}")
        rows.setdefault(year, []).append((yday, prcp, tmax, tmin))
    if tuple(sorted(rows)) != FIT_YEARS:
        raise ValueError(f"Daymet fit years are incomplete: {path}")
    result: dict[int, np.ndarray] = {}
    for year in FIT_YEARS:
        records = rows[year]
        if [item[0] for item in records] != list(range(1, 366)):
            raise ValueError(f"Daymet ordinal calendar is incomplete: {path}, {year}")
        result[year] = np.asarray([item[1:] for item in records], dtype=np.float64)
    return result


def month_slices() -> tuple[slice, ...]:
    slices = []
    start = 0
    for count in MONTH_LENGTHS:
        slices.append(slice(start, start + count))
        start += count
    return tuple(slices)


def affine_calendar(
    pww: np.ndarray, pwd: np.ndarray, start_probability: float
) -> tuple[float, np.ndarray]:
    probability = start_probability
    counts = np.zeros(12, dtype=np.float64)
    for month, days in enumerate(MONTH_LENGTHS):
        rho = pww[month] - pwd[month]
        for _ in range(days):
            probability = pwd[month] + rho * probability
            counts[month] += probability
    return probability, counts


def annual_affine(pww: np.ndarray, pwd: np.ndarray) -> tuple[float, float]:
    end_zero, _ = affine_calendar(pww, pwd, 0.0)
    end_one, _ = affine_calendar(pww, pwd, 1.0)
    return end_one - end_zero, end_zero


def stationary_base_counts(pww: np.ndarray, pwd: np.ndarray) -> np.ndarray:
    a_value, b_value = annual_affine(pww, pwd)
    if not 0.0 <= a_value < 1.0:
        raise ValueError("base occurrence calendar lacks a stationary solution")
    start = b_value / (1.0 - a_value)
    _, counts = affine_calendar(pww, pwd, start)
    return counts


def logistic(value: np.ndarray) -> np.ndarray:
    result = np.empty_like(value)
    positive = value >= 0.0
    result[positive] = 1.0 / (1.0 + np.exp(-value[positive]))
    exponential = np.exp(value[~positive])
    result[~positive] = exponential / (1.0 + exponential)
    return result


def conditional_occurrence(
    intercepts: np.ndarray,
    loadings: np.ndarray,
    rho: np.ndarray,
    nodes: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    pww_rows = []
    pwd_rows = []
    a_rows = []
    b_rows = []
    minimum = 1.0
    maximum = 0.0
    for node in nodes:
        q_value = logistic(intercepts + loadings * node)
        pwd_value = (1.0 - rho) * q_value
        pww_value = rho + (1.0 - rho) * q_value
        minimum = min(minimum, float(np.min(pwd_value)), float(np.min(pww_value)))
        maximum = max(maximum, float(np.max(pwd_value)), float(np.max(pww_value)))
        pww_rows.append(pww_value)
        pwd_rows.append(pwd_value)
        a_value, b_value = annual_affine(pww_value, pwd_value)
        a_rows.append(a_value)
        b_rows.append(b_value)
    expected_a = math.fsum(float(w * value) for w, value in zip(weights, a_rows))
    expected_b = math.fsum(float(w * value) for w, value in zip(weights, b_rows))
    if not 0.0 <= expected_a < 1.0:
        raise ValueError("annual occurrence mixture lacks a stationary solution")
    start = expected_b / (1.0 - expected_a)
    count_rows = []
    for pww_value, pwd_value in zip(pww_rows, pwd_rows):
        _, counts = affine_calendar(pww_value, pwd_value, start)
        count_rows.append(counts)
    return np.asarray(count_rows), np.asarray(pwd_rows), minimum, maximum


def solve_occurrence(
    pww: np.ndarray,
    pwd: np.ndarray,
    loadings: np.ndarray,
    nodes: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float, float, float]:
    target = stationary_base_counts(pww, pwd)
    rho = pww - pwd
    q_value = pwd / (1.0 - pww + pwd)
    initial = np.log(q_value / (1.0 - q_value))

    def residual(intercepts: np.ndarray) -> np.ndarray:
        counts, _, _, _ = conditional_occurrence(
            intercepts, loadings, rho, nodes, weights
        )
        expected = np.asarray(
            [
                math.fsum(float(w * counts[row, month]) for row, w in enumerate(weights))
                for month in range(12)
            ]
        )
        return expected - target

    solved = root(
        residual,
        initial,
        method="hybr",
        options={"xtol": ROOT_XTOL, "maxfev": ROOT_MAXFEV},
    )
    errors = residual(solved.x)
    max_error = float(np.max(np.abs(errors)))
    if not solved.success or max_error > COUNT_TOLERANCE:
        raise ValueError(
            f"occurrence solve failed: success={solved.success}, error={max_error:.17g}, "
            f"message={solved.message}"
        )
    counts, _, minimum, maximum = conditional_occurrence(
        solved.x, loadings, rho, nodes, weights
    )
    if not 0.0 < minimum <= maximum < 1.0:
        raise ValueError(
            f"invalid occurrence probability range [{minimum:.17g}, {maximum:.17g}]"
        )
    return solved.x, counts, minimum, maximum, max_error


def leading_component_signs(features: np.ndarray) -> np.ndarray:
    means = np.mean(features, axis=0, dtype=np.float64)
    standard_deviations = np.std(features, axis=0, ddof=1, dtype=np.float64)
    standardized = np.zeros_like(features)
    nonzero = standard_deviations > 0.0
    standardized[:, nonzero] = (
        features[:, nonzero] - means[nonzero]
    ) / standard_deviations[nonzero]
    correlation = np.cov(standardized, rowvar=False, ddof=1)
    correlation = (correlation + correlation.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(correlation)
    largest = float(eigenvalues[-1])
    tolerance = 1.0e-12 * max(1.0, abs(largest))
    candidates = np.flatnonzero(np.abs(eigenvalues - largest) <= tolerance)
    vectors = [eigenvectors[:, index] for index in candidates]
    vector = min(vectors, key=lambda item: tuple(abs(float(value)) for value in item))
    anchor = math.fsum(float(value) for value in vector[:24])
    if anchor < 0.0:
        vector = -vector
    elif anchor == 0.0:
        first = next((float(value) for value in vector if value != 0.0), 1.0)
        if first < 0.0:
            vector = -vector
    return np.where(vector < 0.0, -1, 1).astype(np.int64)


def finite_month_occurrence_variance(q_value: float, rho: float, days: int) -> float:
    serial = math.fsum((days - lag) * rho**lag for lag in range(1, days))
    return q_value * (1.0 - q_value) * (days + 2.0 * serial) / days**2


def fit_station(
    station_id: str,
    regime: str,
    base_path: Path,
    daymet_path: Path,
    root_path: Path,
    nodes: np.ndarray,
    weights: np.ndarray,
) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = load_json(base_path)
    if bundle.get("station_id") != station_id:
        raise ValueError(f"station identity mismatch in {base_path}")
    lineage = bundle["source_lineage"]
    if sha256(daymet_path) != lineage["archive_sha256"]:
        raise ValueError(f"compressed Daymet hash mismatch: {daymet_path}")
    rows = read_daymet(daymet_path, lineage["decompressed_sha256"])
    parameters = bundle["base_station"]["parameters"]
    precipitation = parameters["precipitation"]
    temperature = parameters["temperature"]
    # The consumed station surface is source REAL*4.  Reconstruct those bits
    # before widening so the fit and runtime use the same base values.
    def faithful(values: Any) -> np.ndarray:
        return np.asarray(values, dtype=np.float32).astype(np.float64)

    pww = faithful(precipitation["probability_wet_given_wet"])
    pwd = faithful(precipitation["probability_wet_given_dry"])
    mean_amount_in = faithful(precipitation["mean_daily"])
    sd_amount_in = faithful(precipitation["standard_deviation_daily"])
    tmax_sd_f = faithful(temperature["maximum_standard_deviation"])
    tmin_sd_f = faithful(temperature["minimum_standard_deviation"])
    if not (
        np.all((pww > 0.0) & (pww < 1.0))
        and np.all((pwd > 0.0) & (pwd < 1.0))
        and np.all(pww - pwd >= 0.0)
        and np.all(mean_amount_in > 0.0)
        and np.all(sd_amount_in >= 0.0)
    ):
        raise ValueError("base station violates A5e0 analytic domain")

    feature_rows = []
    slices = month_slices()
    for year in FIT_YEARS:
        data = rows[year]
        occurrence = []
        amount = []
        tmax = []
        tmin = []
        for month, selected in enumerate(slices):
            month_data = data[selected]
            wet = month_data[:, 0] >= WET_THRESHOLD_MM
            wet_count = int(np.sum(wet))
            occurrence.append(wet_count / MONTH_LENGTHS[month])
            wet_sum = math.fsum(float(value) for value in month_data[wet, 0])
            base_mean_mm = mean_amount_in[month] * 25.4
            amount.append(math.log((wet_sum + base_mean_mm) / (wet_count + 1)))
            tmax.append(math.fsum(float(value) for value in month_data[:, 1]) / MONTH_LENGTHS[month])
            tmin.append(math.fsum(float(value) for value in month_data[:, 2]) / MONTH_LENGTHS[month])
        feature_rows.append(occurrence + amount + tmax + tmin)
    features = np.asarray(feature_rows, dtype=np.float64)
    sample_sd = np.std(features, axis=0, ddof=1, dtype=np.float64)
    signs = leading_component_signs(features)

    q_value = pwd / (1.0 - pww + pwd)
    rho = pww - pwd
    occurrence_base_sd = np.asarray(
        [
            math.sqrt(finite_month_occurrence_variance(q_value[m], rho[m], days))
            for m, days in enumerate(MONTH_LENGTHS)
        ]
    )
    occurrence_magnitude = np.sqrt(
        np.maximum(sample_sd[:12] ** 2 - occurrence_base_sd**2, 0.0)
    ) / np.maximum(q_value * (1.0 - q_value), 1.0e-12)

    expected_wet = q_value * np.asarray(MONTH_LENGTHS, dtype=np.float64)
    amount_base_sd = (sd_amount_in / mean_amount_in) / np.sqrt(expected_wet + 1.0)
    amount_magnitude = np.sqrt(
        np.maximum(sample_sd[12:24] ** 2 - amount_base_sd**2, 0.0)
    )

    tmax_base_sd = (tmax_sd_f / 1.8) / np.sqrt(np.asarray(MONTH_LENGTHS))
    tmin_base_sd = (tmin_sd_f / 1.8) / np.sqrt(np.asarray(MONTH_LENGTHS))
    tmax_magnitude = np.sqrt(
        np.maximum(sample_sd[24:36] ** 2 - tmax_base_sd**2, 0.0)
    )
    tmin_magnitude = np.sqrt(
        np.maximum(sample_sd[36:48] ** 2 - tmin_base_sd**2, 0.0)
    )

    occurrence_loading = occurrence_magnitude * signs[:12]
    amount_loading = amount_magnitude * signs[12:24]
    tmax_loading = tmax_magnitude * signs[24:36]
    tmin_loading = tmin_magnitude * signs[36:48]

    intercepts, conditional_counts, minimum_probability, maximum_probability, occurrence_error = solve_occurrence(
        pww, pwd, occurrence_loading, nodes, weights
    )

    amount_center = np.zeros(12, dtype=np.float64)
    amount_residual_sd = np.zeros(12, dtype=np.float64)
    max_mean_error = 0.0
    max_second_error = 0.0
    minimum_amount_variance = math.inf
    for month in range(12):
        conditional_weight = conditional_counts[:, month]
        expected_weight = math.fsum(
            float(weight * count)
            for weight, count in zip(weights, conditional_weight)
        )
        exponential = np.exp(amount_loading[month] * nodes)
        weighted_exponential = math.fsum(
            float(weight * count * value)
            for weight, count, value in zip(weights, conditional_weight, exponential)
        )
        center = math.log(expected_weight / weighted_exponential)
        amount_center[month] = center
        effective_mean = mean_amount_in[month] * np.exp(
            center + amount_loading[month] * nodes
        )
        reconstructed_mean = math.fsum(
            float(weight * count * value)
            for weight, count, value in zip(weights, conditional_weight, effective_mean)
        ) / expected_weight
        weighted_mean_square = math.fsum(
            float(weight * count * value * value)
            for weight, count, value in zip(weights, conditional_weight, effective_mean)
        ) / expected_weight
        target_second = mean_amount_in[month] ** 2 + sd_amount_in[month] ** 2
        residual_variance = target_second - weighted_mean_square
        if residual_variance < -NEGATIVE_TOLERANCE:
            raise ValueError(
                f"month {month + 1}: amount residual variance {residual_variance:.17g}"
            )
        residual_variance = max(0.0, residual_variance)
        amount_residual_sd[month] = math.sqrt(residual_variance)
        reconstructed_second = weighted_mean_square + residual_variance
        mean_error = abs(reconstructed_mean - mean_amount_in[month]) / max(
            1.0, abs(mean_amount_in[month])
        )
        second_error = abs(reconstructed_second - target_second) / max(
            1.0, abs(target_second)
        )
        max_mean_error = max(max_mean_error, mean_error)
        max_second_error = max(max_second_error, second_error)
        minimum_amount_variance = min(minimum_amount_variance, residual_variance)
    if max_mean_error > MOMENT_TOLERANCE or max_second_error > MOMENT_TOLERANCE:
        raise ValueError(
            f"amount reconstruction errors exceed tolerance: {max_mean_error}, {max_second_error}"
        )

    tmax_radicand = tmax_sd_f**2 - (1.8 * tmax_loading) ** 2
    tmin_radicand = tmin_sd_f**2 - (1.8 * tmin_loading) ** 2
    minimum_temperature_variance = float(min(np.min(tmax_radicand), np.min(tmin_radicand)))
    if minimum_temperature_variance < -NEGATIVE_TOLERANCE:
        raise ValueError(
            f"temperature residual variance {minimum_temperature_variance:.17g}"
        )
    tmax_residual_sd = np.sqrt(np.maximum(tmax_radicand, 0.0))
    tmin_residual_sd = np.sqrt(np.maximum(tmin_radicand, 0.0))

    def groups(values: np.ndarray) -> dict[str, list[float]]:
        return {
            "occurrence": [float(value) for value in values[:12]],
            "amount": [float(value) for value in values[12:24]],
            "tmax": [float(value) for value in values[24:36]],
            "tmin": [float(value) for value in values[36:48]],
        }

    station = {
        "station_id": station_id,
        "regime": regime,
        "base_station": artifact(base_path, root_path),
        "base_par_sha256": bundle["base_station"]["lineage"]["source_sha256"],
        "daymet": artifact(daymet_path, root_path),
        "loadings": {
            "occurrence": [float(value) for value in occurrence_loading],
            "amount": [float(value) for value in amount_loading],
            "tmax": [float(value) for value in tmax_loading],
            "tmin": [float(value) for value in tmin_loading],
        },
        "derived": {
            "occurrence_intercepts": [float(value) for value in intercepts],
            "amount_center": [float(value) for value in amount_center],
            "amount_residual_sd_in": [float(value) for value in amount_residual_sd],
            "tmax_residual_sd_f": [float(value) for value in tmax_residual_sd],
            "tmin_residual_sd_f": [float(value) for value in tmin_residual_sd],
        },
        "diagnostics": {
            "feature_sample_sd": groups(sample_sd),
            "base_sampling_sd": {
                "occurrence": [float(value) for value in occurrence_base_sd],
                "amount": [float(value) for value in amount_base_sd],
                "tmax": [float(value) for value in tmax_base_sd],
                "tmin": [float(value) for value in tmin_base_sd],
            },
            "component_sign": {
                "occurrence": [int(value) for value in signs[:12]],
                "amount": [int(value) for value in signs[12:24]],
                "tmax": [int(value) for value in signs[24:36]],
                "tmin": [int(value) for value in signs[36:48]],
            },
            "occurrence_max_abs_count_error": occurrence_error,
            "amount_max_relative_mean_error": max_mean_error,
            "amount_max_relative_second_moment_error": max_second_error,
            "minimum_amount_residual_variance": minimum_amount_variance,
            "minimum_temperature_residual_variance": max(0.0, minimum_temperature_variance),
            "minimum_occurrence_probability": minimum_probability,
            "maximum_occurrence_probability": maximum_probability,
        },
    }
    feasibility = {
        "station_id": station_id,
        "status": "PASS",
        "checks": {
            "finite_loadings": True,
            "occurrence_solver": True,
            "occurrence_probabilities": True,
            "amount_variance_budget": True,
            "temperature_variance_budget": True,
            "moment_reconstruction": True,
        },
        "detail": "all frozen analytic feasibility checks passed",
    }
    return station, feasibility


def main() -> int:
    root_path = repo_root()
    package = root_path / "docs/work-packages/20260714-a5e0-direct-annual-state-pilot"
    artifacts = package / "artifacts"
    fitter_path = Path(__file__).resolve()
    nodes_raw, weights_raw = np.polynomial.hermite.hermgauss(QUADRATURE_NODES)
    nodes = np.sqrt(2.0) * nodes_raw
    weights = weights_raw / math.sqrt(math.pi)
    fitted = []
    feasibility_rows = []
    for station_id, regime in STATIONS:
        base_path = (
            root_path
            / "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/fit/evidence-v1/station-bundles"
            / f"{station_id}.a5b.station.json"
        )
        daymet_path = root_path / f"references/observed/a5a-v1/daymet/{station_id}.csv.gz"
        try:
            station, result = fit_station(
                station_id,
                regime,
                base_path,
                daymet_path,
                root_path,
                nodes,
                weights,
            )
            fitted.append(station)
            feasibility_rows.append(result)
        except Exception as error:  # complete negative feasibility evidence
            feasibility_rows.append(
                {
                    "station_id": station_id,
                    "status": "FAIL",
                    "checks": {},
                    "detail": f"{type(error).__name__}: {error}",
                }
            )
    status = "PASS" if len(fitted) == len(STATIONS) else "FAIL"
    feasibility = {
        "feasibility_schema": "a5e0_analytic_feasibility_v1",
        "status": status,
        "identity": {
            "research_profile": "a5e0_direct_annual_state_v1",
            "fit_recipe": "a5e0_direct_monthly_loading_fit_v1",
            "source_commit": SOURCE_COMMIT,
            "fitter_sha256": sha256(fitter_path),
        },
        "stations": feasibility_rows,
    }
    feasibility_path = artifacts / "a5e0-feasibility-v1.json"
    write_json(feasibility_path, feasibility)
    coefficient_path = artifacts / "a5e0-coefficients-v1.json"
    if status == "PASS":
        coefficients = {
            "coefficient_schema": "a5e0_direct_annual_state_coefficients_v1",
            "identity": {
                "research_profile": "a5e0_direct_annual_state_v1",
                "fit_recipe": "a5e0_direct_monthly_loading_fit_v1",
                "source_commit": SOURCE_COMMIT,
                "fitter_sha256": sha256(fitter_path),
            },
            "source": {
                "observed_snapshot": "daymet_v4r1_a5a17_fit1980_2009_noleap_v1",
                "fit_years": [1980, 2009],
                "calendar": "noleap_365_v1",
                "wet_threshold_mm": WET_THRESHOLD_MM,
                "station_order": [station_id for station_id, _ in STATIONS],
            },
            "numerics": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "quadrature_nodes": QUADRATURE_NODES,
                "root_method": "hybr",
                "root_xtol": ROOT_XTOL,
                "root_maxfev": ROOT_MAXFEV,
            },
            "stations": fitted,
        }
        write_json(coefficient_path, coefficients)
    elif coefficient_path.exists():
        coefficient_path.unlink()
    print(json.dumps({"status": status, "feasibility": str(feasibility_path), "coefficients": str(coefficient_path) if status == "PASS" else None}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
