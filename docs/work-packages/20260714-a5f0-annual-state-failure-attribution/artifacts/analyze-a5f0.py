#!/usr/bin/env python3
"""Derive the frozen A5f0 attribution from retained A5e0 evidence."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


STATIONS = ("ca042319", "co051660", "ms227840")
ARMS = ("research_baseline", "candidate")
SEAMS = ("occurrence", "amount", "tmax", "tmin")
HORIZONS = (30, 100)
WET_THRESHOLD_MM = 0.254
MONTHS = tuple(range(1, 13))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


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
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, root: Path) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size,
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path),
    }


def fmedian(values: list[float]) -> float:
    if not values:
        raise ValueError("median of empty sequence")
    return float(np.median(np.asarray(values, dtype=np.float64)))


def ols_slope(x_values: np.ndarray, y_values: np.ndarray) -> float:
    x_centered = x_values - np.mean(x_values, dtype=np.float64)
    denominator = float(np.dot(x_centered, x_centered))
    if denominator <= 0.0:
        raise ValueError("OLS predictor has zero variance")
    y_centered = y_values - np.mean(y_values, dtype=np.float64)
    return float(np.dot(x_centered, y_centered) / denominator)


def logistic(values: np.ndarray) -> np.ndarray:
    result = np.empty_like(values)
    positive = values >= 0.0
    result[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exponential = np.exp(values[~positive])
    result[~positive] = exponential / (1.0 + exponential)
    return result


def faithful_base_mean_mm(root: Path, station: dict[str, Any]) -> np.ndarray:
    path = root / station["base_station"]["path"]
    if sha256(path) != station["base_station"]["sha256"]:
        raise ValueError(f"base-station hash mismatch: {path}")
    bundle = load_json(path)
    values = bundle["base_station"]["parameters"]["precipitation"]["mean_daily"]
    result = np.asarray(values, dtype=np.float32).astype(np.float64) * 25.4
    if result.shape != (12,) or np.any(result <= 0.0):
        raise ValueError(f"invalid base precipitation means: {path}")
    return result


def annual_features_from_months(
    years: dict[int, dict[int, list[tuple[float, float, float]]]],
    base_mean_mm: np.ndarray,
) -> np.ndarray:
    rows: list[list[float]] = []
    expected_years = list(range(min(years), max(years) + 1))
    if sorted(years) != expected_years:
        raise ValueError("annual feature input has a noncontiguous calendar")
    for year in expected_years:
        occurrence: list[float] = []
        amount: list[float] = []
        tmax: list[float] = []
        tmin: list[float] = []
        if tuple(sorted(years[year])) != MONTHS:
            raise ValueError(f"year {year} lacks all 12 months")
        for month in MONTHS:
            records = years[year][month]
            if not records:
                raise ValueError(f"empty month {year}-{month:02d}")
            wet = [row for row in records if row[0] >= WET_THRESHOLD_MM]
            occurrence.append(len(wet) / len(records))
            wet_sum = math.fsum(row[0] for row in wet)
            amount.append(
                math.log((wet_sum + base_mean_mm[month - 1]) / (len(wet) + 1))
            )
            tmax.append(math.fsum(row[1] for row in records) / len(records))
            tmin.append(math.fsum(row[2] for row in records) / len(records))
        rows.append(occurrence + amount + tmax + tmin)
    result = np.asarray(rows, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise ValueError("annual feature matrix contains nonfinite values")
    return result


def read_cli(path: Path, base_mean_mm: np.ndarray) -> tuple[np.ndarray, int]:
    years: dict[int, dict[int, list[tuple[float, float, float]]]] = {}
    rows = 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) != 13:
                continue
            try:
                day, month, year = (int(fields[index]) for index in range(3))
                precipitation = float(fields[3])
                tmax = float(fields[7])
                tmin = float(fields[8])
            except ValueError:
                continue
            if not (1 <= day <= 31 and 1 <= month <= 12 and year >= 1):
                continue
            if precipitation < 0.0 or tmax < tmin:
                raise ValueError(f"invalid physical value in {path}")
            years.setdefault(year, {}).setdefault(month, []).append(
                (precipitation, tmax, tmin)
            )
            rows += 1
    if not years:
        raise ValueError(f"no daily records parsed from {path}")
    return annual_features_from_months(years, base_mean_mm), rows


def read_daymet(
    root: Path,
    station: dict[str, Any],
    base_mean_mm: np.ndarray,
    selected_years: tuple[int, ...],
) -> np.ndarray:
    path = root / station["daymet"]["path"]
    if sha256(path) != station["daymet"]["sha256"]:
        raise ValueError(f"Daymet archive hash mismatch: {path}")
    raw = gzip.open(path, "rb").read()
    lines = raw.decode("utf-8").splitlines()
    if len(lines) < 8 or lines[6] != (
        "year,yday,prcp (mm/day),tmax (deg c),tmin (deg c)"
    ):
        raise ValueError(f"unexpected Daymet structure: {path}")
    years: dict[int, dict[int, list[tuple[float, float, float]]]] = {}
    ordinals: dict[int, list[int]] = {}
    selected = set(selected_years)
    for record in csv.reader(lines[7:]):
        if len(record) != 5:
            raise ValueError(f"malformed Daymet row: {path}")
        year, ordinal = int(record[0]), int(record[1])
        if year not in selected:
            continue
        precipitation, tmax, tmin = (float(value) for value in record[2:])
        month_lengths = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        cursor = ordinal
        month = 1
        for length in month_lengths:
            if cursor <= length:
                break
            cursor -= length
            month += 1
        if month > 12 or cursor < 1:
            raise ValueError(f"invalid Daymet ordinal: {path}, {year}, {ordinal}")
        years.setdefault(year, {}).setdefault(month, []).append(
            (precipitation, tmax, tmin)
        )
        ordinals.setdefault(year, []).append(ordinal)
    if tuple(sorted(years)) != selected_years:
        raise ValueError(f"Daymet selected years incomplete: {path}")
    for year in selected_years:
        if ordinals[year] != list(range(1, 366)):
            raise ValueError(f"Daymet ordinal calendar incomplete: {path}, {year}")
    return annual_features_from_months(years, base_mean_mm)


def verify_matrix(root: Path, matrix: dict[str, Any]) -> tuple[int, int]:
    runs = matrix.get("runs")
    if not isinstance(runs, list) or len(runs) != 48:
        raise ValueError("A5e0 matrix must contain exactly 48 runs")
    identities = set()
    product_count = 0
    for run in runs:
        identity = (run["station_id"], run["arm"], int(run["replicate"]))
        if identity in identities:
            raise ValueError(f"duplicate A5e0 run: {identity}")
        identities.add(identity)
        for horizon in ("30", "100"):
            products = run["products"][horizon]
            for record in products.values():
                path = root / record["path"]
                if not path.is_file():
                    raise ValueError(f"missing A5e0 product: {path}")
                if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
                    raise ValueError(f"A5e0 product identity mismatch: {path}")
                product_count += 1
    expected = {
        (station, arm, replicate)
        for station in STATIONS
        for arm in ARMS
        for replicate in range(1, 9)
    }
    if identities != expected:
        raise ValueError("A5e0 matrix membership differs from the frozen design")
    return len(runs), product_count


def h1_family_attribution(a5e0: dict[str, Any]) -> dict[str, Any]:
    horizons = []
    all_ratios_worse = True
    for horizon in a5e0["horizons"]:
        families = {
            name: {"positive_degradation": 0.0, "station_deltas": []}
            for name in (
                "annual_dispersion",
                "monthly_dispersion",
                "cross_month_dependence",
                "cross_variable_dependence",
            )
        }
        ratios = []
        for station in horizon["h1"]["stations"]:
            ratios.append(float(station["ratio"]))
            all_ratios_worse = all_ratios_worse and station["ratio"] > 1.0
            for name, result in families.items():
                delta = float(
                    station["families"]["candidate"][name]["median"]
                    - station["families"]["research_baseline"][name]["median"]
                )
                result["station_deltas"].append(
                    {"delta": delta, "station_id": station["station_id"]}
                )
                result["positive_degradation"] += max(delta, 0.0)
        total = math.fsum(item["positive_degradation"] for item in families.values())
        for result in families.values():
            result["positive_degradation_share"] = (
                result["positive_degradation"] / total if total > 0.0 else 0.0
            )
        dominant = max(
            families,
            key=lambda name: (families[name]["positive_degradation_share"], name),
        )
        horizons.append(
            {
                "dominant_family": dominant,
                "dominant_positive_degradation_share": families[dominant][
                    "positive_degradation_share"
                ],
                "families": families,
                "horizon_years": int(horizon["horizon_years"]),
                "station_ratios": ratios,
                "three_station_median_ratio": fmedian(ratios),
            }
        )
    return {"all_six_station_horizon_ratios_above_one": all_ratios_worse, "horizons": horizons}


def fit_geometry(features: np.ndarray, station: dict[str, Any]) -> dict[str, Any]:
    means = np.mean(features, axis=0, dtype=np.float64)
    deviations = np.std(features, axis=0, ddof=1, dtype=np.float64)
    if np.any(deviations <= 0.0):
        raise ValueError(f"zero fit-period feature SD: {station['station_id']}")
    standardized = (features - means) / deviations
    correlation = np.cov(standardized, rowvar=False, ddof=1)
    correlation = (correlation + correlation.T) / 2.0
    eigenvalues = np.linalg.eigvalsh(correlation)
    nonnegative = np.maximum(eigenvalues, 0.0)
    variance_share = float(nonnegative[-1] / math.fsum(float(x) for x in nonnegative))
    squared_total = float(np.dot(eigenvalues, eigenvalues))
    residual = math.sqrt(float(np.dot(eigenvalues[:-1], eigenvalues[:-1])) / squared_total)

    loadings = np.concatenate(
        [np.asarray(station["loadings"][seam], dtype=np.float64) for seam in SEAMS]
    )
    eligible = 0
    matches = 0
    for left in range(48):
        if loadings[left] == 0.0:
            continue
        for right in range(left + 1, 48):
            if loadings[right] == 0.0 or abs(correlation[left, right]) < 0.2:
                continue
            eligible += 1
            matches += int(
                math.copysign(1.0, loadings[left] * loadings[right])
                == math.copysign(1.0, correlation[left, right])
            )
    return {
        "active_loading_count": int(np.count_nonzero(loadings)),
        "leading_component_variance_share": variance_share,
        "rank_one_frobenius_residual_fraction": residual,
        "strong_pair_sign_agreement": matches / eligible if eligible else None,
        "strong_pair_threshold_abs_correlation": 0.2,
        "strong_pairs_evaluated": eligible,
    }


def distance_by_seam(generated: np.ndarray, observed: np.ndarray) -> dict[str, float]:
    generated_sd = np.std(generated, axis=0, ddof=1, dtype=np.float64)
    observed_sd = np.std(observed, axis=0, ddof=1, dtype=np.float64)
    relative = np.abs(generated_sd - observed_sd) / np.maximum(observed_sd, 1.0e-12)
    return {
        seam: float(np.mean(relative[index * 12 : (index + 1) * 12], dtype=np.float64))
        for index, seam in enumerate(SEAMS)
    }


def runtime_response(
    station_records: dict[str, dict[tuple[str, int], dict[str, Any]]],
    coefficients: dict[str, dict[str, Any]],
    cli_features: dict[tuple[str, str, int, int], np.ndarray],
    root: Path,
) -> dict[str, Any]:
    station_results = []
    global_cells: list[dict[str, Any]] = []
    by_seam_cells: dict[str, list[dict[str, Any]]] = {seam: [] for seam in SEAMS}
    for station_id in STATIONS:
        station = coefficients[station_id]
        seam_results: dict[str, Any] = {}
        for seam_index, seam in enumerate(SEAMS):
            cells = []
            for month_index, loading_value in enumerate(station["loadings"][seam]):
                loading = float(loading_value)
                if abs(loading) == 0.0:
                    continue
                replicate_rows = []
                for replicate in range(1, 9):
                    run = station_records[station_id][("candidate", replicate)]
                    diagnostics_path = root / run["products"]["100"]["diagnostics"]["path"]
                    diagnostics = load_json(diagnostics_path)
                    states = np.asarray(diagnostics["annual_states"], dtype=np.float64)
                    actual = cli_features[(station_id, "candidate", replicate, 100)][
                        :, seam_index * 12 + month_index
                    ]
                    if states.shape != actual.shape:
                        raise ValueError("annual-state and generated-feature lengths differ")
                    actual_slope = ols_slope(states, actual)
                    if seam == "occurrence":
                        intercept = float(station["derived"]["occurrence_intercepts"][month_index])
                        expected_series = logistic(intercept + loading * states)
                        expected_slope = ols_slope(states, expected_series)
                    else:
                        expected_slope = loading
                    replicate_rows.append(
                        {
                            "actual_slope": actual_slope,
                            "expected_slope": expected_slope,
                            "replicate": replicate,
                            "response_ratio": actual_slope / expected_slope,
                        }
                    )
                ratio = fmedian([row["response_ratio"] for row in replicate_rows])
                actual_median = fmedian([row["actual_slope"] for row in replicate_rows])
                expected_median = fmedian([row["expected_slope"] for row in replicate_rows])
                cell = {
                    "median_actual_slope": actual_median,
                    "median_expected_slope": expected_median,
                    "median_response_ratio": ratio,
                    "month": month_index + 1,
                    "replicates": replicate_rows,
                    "sign_match": actual_median * expected_median > 0.0,
                }
                cells.append(cell)
                tagged = {**cell, "seam": seam, "station_id": station_id}
                global_cells.append(tagged)
                by_seam_cells[seam].append(tagged)
            seam_results[seam] = {
                "active_cells": len(cells),
                "cells": cells,
                "median_response_ratio": fmedian(
                    [cell["median_response_ratio"] for cell in cells]
                )
                if cells
                else None,
                "sign_match_fraction": sum(cell["sign_match"] for cell in cells) / len(cells)
                if cells
                else None,
            }
        station_results.append({"seams": seam_results, "station_id": station_id})

    def aggregate(cells: list[dict[str, Any]]) -> dict[str, Any]:
        if not cells:
            return {
                "active_cells": 0,
                "median_response_ratio": None,
                "sign_match_fraction": None,
            }
        return {
            "active_cells": len(cells),
            "median_response_ratio": fmedian(
                [cell["median_response_ratio"] for cell in cells]
            ),
            "sign_match_fraction": sum(cell["sign_match"] for cell in cells) / len(cells),
        }

    return {
        "by_seam": {seam: aggregate(by_seam_cells[seam]) for seam in SEAMS},
        "global": aggregate(global_cells),
        "stations": station_results,
    }


def seam_attribution(
    observed: dict[str, np.ndarray],
    cli_features: dict[tuple[str, str, int, int], np.ndarray],
    contract: dict[str, Any],
) -> dict[str, Any]:
    cells = []
    counts = {seam: 0 for seam in SEAMS}
    minimum_delta = float(contract["thresholds"]["unique_worst_minimum_delta"])
    minimum_margin = float(contract["thresholds"]["unique_worst_minimum_margin"])
    for station_id in STATIONS:
        for horizon in HORIZONS:
            seams: dict[str, Any] = {}
            for seam in SEAMS:
                arm_distances: dict[str, list[float]] = {arm: [] for arm in ARMS}
                for arm in ARMS:
                    for replicate in range(1, 9):
                        values = distance_by_seam(
                            cli_features[(station_id, arm, replicate, horizon)],
                            observed[station_id],
                        )
                        arm_distances[arm].append(values[seam])
                baseline = fmedian(arm_distances["research_baseline"])
                candidate = fmedian(arm_distances["candidate"])
                seams[seam] = {
                    "candidate_median_distance": candidate,
                    "delta": candidate - baseline,
                    "replicate_distances": arm_distances,
                    "research_baseline_median_distance": baseline,
                }
            ranked = sorted(SEAMS, key=lambda name: (-seams[name]["delta"], name))
            top, second = ranked[:2]
            margin = seams[top]["delta"] - seams[second]["delta"]
            unique = seams[top]["delta"] >= minimum_delta and margin >= minimum_margin
            if unique:
                counts[top] += 1
            cells.append(
                {
                    "horizon_years": horizon,
                    "seams": seams,
                    "station_id": station_id,
                    "top_delta_margin": margin,
                    "unique_worst": unique,
                    "unique_worst_seam": top if unique else None,
                }
            )
    winner = max(SEAMS, key=lambda name: (counts[name], name))
    minimum_cells = int(
        contract["thresholds"]["bounded_ablation"][
            "minimum_cells_with_same_unique_worst_seam"
        ]
    )
    return {
        "cells": cells,
        "localization": {
            "candidate_seam": winner if counts[winner] >= minimum_cells else None,
            "same_unique_worst_counts": counts,
            "threshold_cells": minimum_cells,
        },
    }


def make_decision(
    contract: dict[str, Any],
    h1: dict[str, Any],
    geometry: list[dict[str, Any]],
    response: dict[str, Any],
    seam_result: dict[str, Any],
) -> dict[str, Any]:
    structural_thresholds = contract["thresholds"]["structural_overcoupling"]
    h1_condition = all(
        horizon["dominant_family"] == structural_thresholds["dominant_h1_family"]
        and horizon["dominant_positive_degradation_share"]
        >= structural_thresholds[
            "minimum_dominant_positive_degradation_share_each_horizon"
        ]
        for horizon in h1["horizons"]
    )
    geometry_condition = all(
        station["geometry"]["leading_component_variance_share"]
        < structural_thresholds["maximum_rank_one_variance_share_each_station"]
        for station in geometry
    )
    global_response = response["global"]
    response_condition = (
        global_response["sign_match_fraction"]
        >= structural_thresholds["minimum_global_response_sign_match_fraction"]
        and structural_thresholds["response_ratio_minimum"]
        <= global_response["median_response_ratio"]
        <= structural_thresholds["response_ratio_maximum"]
    )
    structural = h1_condition and geometry_condition and response_condition

    seam = seam_result["localization"]["candidate_seam"]
    ablation_thresholds = contract["thresholds"]["bounded_ablation"]
    seam_response = response["by_seam"].get(seam) if seam is not None else None
    seam_response_condition = bool(
        seam_response
        and seam_response["active_cells"] > 0
        and seam_response["sign_match_fraction"]
        >= ablation_thresholds["minimum_response_sign_match_fraction"]
        and ablation_thresholds["response_ratio_minimum"]
        <= seam_response["median_response_ratio"]
        <= ablation_thresholds["response_ratio_maximum"]
    )
    ablation = not structural and seam is not None and seam_response_condition

    if structural:
        value = "RETIRE-SCALAR-IID-MECHANISM"
        rule = "RETIRE_STRUCTURAL_OVERCOUPLING"
        basis = (
            "cross-month dependence dominates positive H1 degradation at both "
            "horizons, one component captures less than half of fit-period annual-"
            "feature variance at every station, and generated features respond to "
            "the encoded state in the expected aggregate direction and scale"
        )
    elif ablation:
        value = "JUSTIFY-ONE-BOUNDED-ABLATION"
        rule = "JUSTIFY_ONE_BOUNDED_ABLATION"
        basis = (
            f"the {seam} seam is the same uniquely worst annual-feature SD-distance "
            "seam in at least five of six station-horizon cells and its runtime "
            "response passes the frozen direction-and-scale screen"
        )
    else:
        value = "RETIRE-SCALAR-IID-MECHANISM"
        rule = "RETIRE_NO_ISOLATED_REPAIR_TARGET"
        basis = (
            "the already unfavorable A5e0 result does not satisfy the frozen "
            "requirements for one isolated, runtime-responsive seam repair target"
        )
    return {
        "basis": basis,
        "bounded_ablation_seam": seam if ablation else None,
        "criteria": {
            "bounded_ablation": ablation,
            "geometry_condition": geometry_condition,
            "h1_condition": h1_condition,
            "runtime_response_condition": response_condition,
            "seam_response_condition": seam_response_condition,
            "structural_overcoupling": structural,
        },
        "rule": rule,
        "value": value,
    }


def render_findings(analysis: dict[str, Any], decision: dict[str, Any]) -> str:
    h1_rows = analysis["h1_family_attribution"]["horizons"]
    geometry = analysis["annual_feature_geometry"]
    response = analysis["runtime_response"]["global"]
    localization = analysis["seam_variance_distance"]["localization"]
    lines = [
        "# A5f0 Annual-State Failure Attribution",
        "",
        "## Abstract",
        "",
        "A5f0 reanalyzed the retained, hash-verified A5e0 products without new ",
        "climate generation or coefficient fitting. The result is descriptive evidence ",
        "for the already exposed three-station development surface, not a prospective ",
        "climate test or a population claim.",
        "",
        "## Findings",
        "",
    ]
    for horizon in h1_rows:
        lines.append(
            f"- At {horizon['horizon_years']} years, "
            f"`{horizon['dominant_family']}` supplied "
            f"{100.0 * horizon['dominant_positive_degradation_share']:.1f}% of summed "
            "positive H1 family degradation."
        )
    for station in geometry:
        item = station["geometry"]
        lines.append(
            f"- `{station['station_id']}`: the leading component represented "
            f"{100.0 * item['leading_component_variance_share']:.1f}% of standardized "
            "1980–2009 annual-feature variance; the rank-one correlation residual was "
            f"{item['rank_one_frobenius_residual_fraction']:.3f}."
        )
    lines.extend(
        [
            f"- Across {response['active_cells']} active station-month loadings, the "
            f"realized/expected median response ratio was "
            f"{response['median_response_ratio']:.3f}, with "
            f"{100.0 * response['sign_match_fraction']:.1f}% sign agreement.",
            "- Same uniquely worst seam counts across the six station-horizon cells: "
            + ", ".join(
                f"{seam}={count}"
                for seam, count in localization["same_unique_worst_counts"].items()
            )
            + ".",
            "",
            "## Decision",
            "",
            f"`{decision['decision']}` under rule `{decision['rule']}`.",
            "",
            decision["basis"] + ".",
            "",
            "This disposition applies only to `a5e0_direct_annual_state_v1` with "
            "`a5e0_direct_monthly_loading_fit_v1`. It neither rejects annual-state "
            "models generally nor authorizes an implementation follow-on.",
            "",
            "## Interpretation limits",
            "",
            "The stations and A5e0 outcome were exposed before A5f0 was designed. "
            "Generated `.cli` values are formatted outputs, so response slopes include "
            "output quantization. The seam-distance diagnostic is a derived aid and does "
            "not replace the frozen A5e0 quality vector. No significance test, causal "
            "claim, confirmation claim, or promotion claim is made.",
            "",
        ]
    )
    return "\n".join(lines)


def build(root: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    package = root / "docs/work-packages/20260714-a5f0-annual-state-failure-attribution"
    artifacts = package / "artifacts"
    contract = load_json(artifacts / "attribution-contract-v1.json")
    freeze_path = artifacts / "pre-analysis-freeze-v1.json"
    freeze = load_json(freeze_path)
    coefficient_path = root / contract["inputs"]["a5e0_coefficients"]
    analysis_path = root / contract["inputs"]["a5e0_analysis"]
    campaign_path = root / contract["inputs"]["a5e0_campaign"]
    matrix_path = root / contract["inputs"]["a5e0_matrix"]
    coefficients_raw = load_json(coefficient_path)
    a5e0_analysis = load_json(analysis_path)
    matrix = load_json(matrix_path)
    load_json(campaign_path)
    run_count, product_count = verify_matrix(root, matrix)
    coefficients = {item["station_id"]: item for item in coefficients_raw["stations"]}
    if tuple(sorted(coefficients)) != STATIONS:
        raise ValueError("coefficient station membership differs from A5f0 contract")
    station_records: dict[str, dict[tuple[str, int], dict[str, Any]]] = {
        station: {} for station in STATIONS
    }
    for run in matrix["runs"]:
        station_records[run["station_id"]][(run["arm"], int(run["replicate"]))] = run

    base_means: dict[str, np.ndarray] = {}
    fit_features: dict[str, np.ndarray] = {}
    observed_features: dict[str, np.ndarray] = {}
    geometry = []
    fit_years = tuple(int(value) for value in contract["inputs"]["fit_years"])
    evaluation_years = tuple(
        int(value) for value in contract["inputs"]["evaluation_years"]
    )
    for station_id in STATIONS:
        station = coefficients[station_id]
        base_means[station_id] = faithful_base_mean_mm(root, station)
        fit_features[station_id] = read_daymet(
            root, station, base_means[station_id], fit_years
        )
        observed_features[station_id] = read_daymet(
            root, station, base_means[station_id], evaluation_years
        )
        geometry.append(
            {
                "geometry": fit_geometry(fit_features[station_id], station),
                "station_id": station_id,
            }
        )

    cli_features: dict[tuple[str, str, int, int], np.ndarray] = {}
    cli_rows = 0
    for station_id in STATIONS:
        for arm in ARMS:
            for replicate in range(1, 9):
                run = station_records[station_id][(arm, replicate)]
                hundred, rows = read_cli(
                    root / run["products"]["100"]["cli"]["path"],
                    base_means[station_id],
                )
                thirty, prefix_rows = read_cli(
                    root / run["products"]["30"]["cli"]["path"],
                    base_means[station_id],
                )
                if hundred.shape != (100, 48) or thirty.shape != (30, 48):
                    raise ValueError("A5e0 CLI feature matrix has unexpected dimensions")
                if not np.array_equal(thirty, hundred[:30]):
                    raise ValueError("A5e0 30-year CLI is not the 100-year prefix")
                if rows != run["full_rows"] or prefix_rows != run["prefix_rows"]:
                    raise ValueError("A5e0 CLI row count differs from matrix index")
                cli_features[(station_id, arm, replicate, 100)] = hundred
                cli_features[(station_id, arm, replicate, 30)] = thirty
                cli_rows += rows + prefix_rows

    h1 = h1_family_attribution(a5e0_analysis)
    response = runtime_response(station_records, coefficients, cli_features, root)
    seam_result = seam_attribution(observed_features, cli_features, contract)
    disposition = make_decision(contract, h1, geometry, response, seam_result)

    identity = {
        "a5e0_analysis": artifact(analysis_path, root),
        "a5e0_campaign": artifact(campaign_path, root),
        "a5e0_coefficients": artifact(coefficient_path, root),
        "a5e0_matrix": artifact(matrix_path, root),
        "attribution_contract": artifact(artifacts / "attribution-contract-v1.json", root),
        "pre_analysis_freeze": artifact(freeze_path, root),
        "source_commit": freeze["identity"]["source_commit"],
        "work_package": "20260714-a5f0-annual-state-failure-attribution",
    }
    result = {
        "analysis_schema": "a5f0_attribution_v1",
        "annual_feature_geometry": geometry,
        "decision": disposition,
        "h1_family_attribution": h1,
        "identity": identity,
        "integrity": {
            "cli_daily_rows_parsed": cli_rows,
            "matrix_products_verified": product_count,
            "matrix_runs_verified": run_count,
            "status": "PASS",
        },
        "runtime_response": response,
        "seam_variance_distance": seam_result,
    }
    decision = {
        "basis": disposition["basis"],
        "bounded_ablation_seam": disposition["bounded_ablation_seam"],
        "decision": disposition["value"],
        "decision_schema": "a5f0_decision_v1",
        "identity": identity,
        "next_step": (
            "none; a new operator dispatch is required for any different model structure"
            if disposition["value"] == "RETIRE-SCALAR-IID-MECHANISM"
            else "one new prospectively frozen package may zero only the named seam"
        ),
        "rule": disposition["rule"],
        "scope": contract["scope"]["retirement_target"],
    }
    return result, decision, render_findings(result, decision)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    artifacts = root / (
        "docs/work-packages/20260714-a5f0-annual-state-failure-attribution/artifacts"
    )
    analysis, decision, findings = build(root)
    outputs = {
        artifacts / "a5f0-attribution-v1.json": canonical_json(analysis),
        artifacts / "a5f0-decision-v1.json": canonical_json(decision),
        artifacts / "a5f0-findings.md": findings.encode("utf-8"),
    }
    if args.check:
        for path, expected in outputs.items():
            if not path.is_file() or path.read_bytes() != expected:
                raise SystemExit(f"derived artifact mismatch: {path}")
        print("A5f0 derived artifacts reproduce byte-for-byte: PASS")
        return 0
    for path, value in outputs.items():
        path.write_bytes(value)
    print(decision["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
