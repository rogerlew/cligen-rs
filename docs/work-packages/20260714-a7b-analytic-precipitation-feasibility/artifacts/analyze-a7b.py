#!/usr/bin/env python3
"""Deterministic analytic feasibility analysis for A7b.

This program fits no generator output.  It fits two bounded daily
precipitation mechanisms to the frozen Daymet corpus, recenters each monthly
kernel to the legacy CLIGEN wet fraction, and certifies whether wet-amount
variance can be reallocated to retain the legacy monthly-total variance.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import re
import struct
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit, ndtr
from scipy.stats import rankdata

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
DEFAULT_REPO = PACKAGE.parents[2]
CONTRACT_NAME = "feasibility-contract-v1.json"
FREEZE_NAME = "pre-analysis-freeze-v1.json"
ANALYSIS_NAME = "a7b-analysis-v1.json"
DECISION_NAME = "a7b-decision-v1.json"
FINDINGS_NAME = "findings.md"
SEASONS = ("DJF", "MAM", "JJA", "SON")
STATE_LABELS = {
    "o2_logqspline_gaussian_copula_v1": ("DD", "DW", "WD", "WW"),
    "sm2_logqspline_gaussian_copula_v1": ("D1", "D2+", "W1", "W2+"),
}
FLOAT_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?")


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
        raise ValueError(f"expected JSON object: {path}")
    return value


def checked_input(repo: Path, entry: dict[str, str]) -> Path:
    path = repo / entry["path"]
    actual = sha256(path.read_bytes())
    if actual != entry["sha256"]:
        raise ValueError(f"input identity mismatch for {entry['path']}: {actual}")
    return path


def check_source_boundary(repo: Path, source_commit: str) -> None:
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
        cwd=repo,
        check=True,
    )
    changed = subprocess.run(
        ["git", "diff", "--quiet", source_commit, "--", "crates"],
        cwd=repo,
        check=False,
    ).returncode
    if changed != 0:
        raise ValueError("production crates changed after the frozen source commit")


def check_freeze(repo: Path, contract: dict[str, Any]) -> dict[str, Any]:
    freeze_path = ARTIFACTS / FREEZE_NAME
    freeze = load_json(freeze_path)
    if freeze.get("freeze_status") != "FROZEN-BEFORE-A7B-OUTCOME":
        raise ValueError("A7b pre-analysis freeze is not active")
    for relative, expected in freeze["frozen_files_sha256"].items():
        actual = sha256((repo / relative).read_bytes())
        if actual != expected:
            raise ValueError(f"frozen file changed: {relative}")
    if freeze["source_commit"] != contract["source_commit"]:
        raise ValueError("freeze/contract source commit mismatch")
    return freeze


def f32_widen(value: float) -> float:
    return float(struct.unpack("<f", struct.pack("<f", value))[0])


def parse_parameter_row(line: str) -> list[float]:
    values = [f32_widen(float(value)) for value in FLOAT_RE.findall(line[8:])]
    if len(values) != 12:
        raise ValueError(f"expected 12 monthly values in parameter row: {line!r}")
    return values


def load_legacy_parameters(
    archive_path: Path,
    stations: list[dict[str, Any]],
) -> dict[str, dict[str, list[float]]]:
    result: dict[str, dict[str, list[float]]] = {}
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for station in stations:
            station_id = station["station_id"]
            member = archive.getmember(f"station-parameters/{station_id}.par")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"missing parameter member for {station_id}")
            raw = stream.read()
            if sha256(raw) != station["par_sha256"]:
                raise ValueError(f"parameter identity mismatch for {station_id}")
            lines = raw.decode("ascii").splitlines()
            mean_mm = [value * 25.4 for value in parse_parameter_row(lines[3])]
            sd_mm = [value * 25.4 for value in parse_parameter_row(lines[4])]
            pww = parse_parameter_row(lines[6])
            pwd = parse_parameter_row(lines[7])
            for month in range(12):
                if mean_mm[month] <= 0.0 or sd_mm[month] < 0.0:
                    raise ValueError(f"invalid wet-amount target for {station_id}")
                if not 0.0 < pww[month] < 1.0 or not 0.0 < pwd[month] < 1.0:
                    raise ValueError(f"invalid occurrence target for {station_id}")
            result[station_id] = {
                "wet_mean_mm": mean_mm,
                "wet_sd_mm": sd_mm,
                "pww": pww,
                "pwd": pwd,
            }
    return result


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("a7b_corpus_common", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class DailySeries:
    dates: tuple[tuple[int, int, int], ...]
    amounts: np.ndarray
    wet: np.ndarray


def load_daymet_series(
    repo: Path,
    common: Any,
    config: dict[str, Any],
    manifest: dict[str, Any],
    threshold: float,
) -> dict[str, DailySeries]:
    start_year, end_year = config["periods"]["full"]
    manifest_stations = {
        entry["station_id"]: entry for entry in manifest["stations"]
    }
    result: dict[str, DailySeries] = {}
    for station in config["stations"]:
        station_id = station["station_id"]
        source = manifest_stations[station_id]["sources"]["daymet"]
        if source["availability"] != "available" or source["calendar"] != "noleap_365":
            raise ValueError(f"frozen Daymet source unavailable for {station_id}")
        path = repo / source["archive_path"]
        records, metadata = common.archive_records(path, "daymet", station)
        if metadata["archive_sha256"] != source["archive_sha256"]:
            raise ValueError(f"Daymet archive mismatch for {station_id}")
        if metadata["source_sha256"] != source["source_sha256"]:
            raise ValueError(f"Daymet source mismatch for {station_id}")
        logical = common.logical_records_bytes(records, start_year, end_year)
        if sha256(logical) != source["fixed_window_logical_records_sha256"]:
            raise ValueError(f"Daymet logical-record mismatch for {station_id}")
        dates = tuple(
            date for date in sorted(records) if start_year <= date[0] <= end_year
        )
        expected = tuple(common.expected_dates("noleap_365", start_year, end_year))
        if dates != expected:
            raise ValueError(f"incomplete no-leap series for {station_id}")
        amounts = np.asarray([records[date]["prcp"] for date in dates], dtype=float)
        result[station_id] = DailySeries(dates, amounts, amounts >= threshold)
    return result


def season_for_month(contract: dict[str, Any], month: int) -> str:
    for season, months in contract["comparison"]["seasons"].items():
        if month in months:
            return season
    raise ValueError(month)


def seasonal_amount_fit(
    series: DailySeries,
    season: str,
    contract: dict[str, Any],
) -> dict[str, Any]:
    months = set(contract["comparison"]["seasons"][season])
    indices = [index for index, date in enumerate(series.dates) if date[1] in months]
    wet_values = series.amounts[indices][series.wet[indices]]
    distinct = len(np.unique(wet_values))
    pairs: list[tuple[float, float]] = []
    for index in indices:
        if index > 0 and series.dates[index][1] in months:
            if series.wet[index - 1] and series.wet[index]:
                pairs.append((series.amounts[index - 1], series.amounts[index]))
    if len(pairs) >= 2:
        left = rankdata([pair[0] for pair in pairs], method="average")
        right = rankdata([pair[1] for pair in pairs], method="average")
        spearman = float(np.corrcoef(left, right)[0, 1])
    else:
        spearman = 0.0
    probabilities = np.asarray(contract["amount_model"]["quantile_probabilities"])
    if len(wet_values):
        knots = np.quantile(wet_values, probabilities, method="inverted_cdf")
    else:
        knots = np.full(len(probabilities), np.nan)
    rules = contract["fit_rules"]
    reasons: list[str] = []
    if len(wet_values) < rules["minimum_wet_amounts_per_station_season"]:
        reasons.append("insufficient_wet_amounts")
    if distinct < rules["minimum_distinct_wet_amounts_per_station_season"]:
        reasons.append("insufficient_distinct_wet_amounts")
    if len(pairs) < rules["minimum_adjacent_wet_pairs_per_station_season"]:
        reasons.append("insufficient_adjacent_wet_pairs")
    if not math.isfinite(spearman) or abs(spearman) > rules["maximum_absolute_spearman"]:
        reasons.append("invalid_spearman")
    if len(wet_values) and (not np.all(np.isfinite(knots)) or np.any(knots <= 0.0)):
        reasons.append("invalid_positive_amount_support")
    rho = 2.0 * math.sin(math.pi * spearman / 6.0) if math.isfinite(spearman) else None
    return {
        "adjacent_wet_pairs": len(pairs),
        "distinct_wet_amounts": distinct,
        "gaussian_copula_rho": rho,
        "identifiable": not reasons,
        "infeasibility_reasons": reasons,
        "log_quantile_knots_mm": [float(value) for value in knots],
        "season": season,
        "spearman_adjacent_wet_amount": spearman if math.isfinite(spearman) else None,
        "wet_amount_count": len(wet_values),
    }


def seasonal_occurrence_fit(
    series: DailySeries,
    season: str,
    candidate_id: str,
    contract: dict[str, Any],
) -> dict[str, Any]:
    months = set(contract["comparison"]["seasons"][season])
    exposures = np.zeros(4, dtype=int)
    successes = np.zeros(4, dtype=int)
    wet = series.wet
    if candidate_id.startswith("o2_"):
        for index in range(2, len(wet)):
            if series.dates[index][1] not in months:
                continue
            state = 2 * int(wet[index - 2]) + int(wet[index - 1])
            exposures[state] += 1
            successes[state] += int(wet[index])
    elif candidate_id.startswith("sm2_"):
        run_age = 1
        for index in range(1, len(wet)):
            previous_wet = bool(wet[index - 1])
            if series.dates[index][1] in months:
                state = (2 if previous_wet else 0) + (1 if run_age >= 2 else 0)
                exposures[state] += 1
                successes[state] += int(bool(wet[index]) == previous_wet)
            run_age = run_age + 1 if wet[index] == wet[index - 1] else 1
    else:
        raise ValueError(candidate_id)
    pseudo = contract["fit_rules"]["jeffreys_pseudocount"]
    probabilities = (successes + pseudo) / (exposures + 2.0 * pseudo)
    minimum = contract["fit_rules"][
        "minimum_occurrence_exposure_per_state_and_station_season"
    ]
    reasons = [
        f"insufficient_occurrence_exposure_{STATE_LABELS[candidate_id][index]}"
        for index, exposure in enumerate(exposures)
        if exposure < minimum
    ]
    return {
        "candidate_id": candidate_id,
        "effective_fisher_information": [
            float(exposure * probability * (1.0 - probability))
            for exposure, probability in zip(exposures, probabilities)
        ],
        "exposures": [int(value) for value in exposures],
        "identifiable": not reasons,
        "infeasibility_reasons": reasons,
        "probabilities": [float(value) for value in probabilities],
        "season": season,
        "state_labels": list(STATE_LABELS[candidate_id]),
        "successes": [int(value) for value in successes],
    }


def transition_matrix(candidate_id: str, probabilities: np.ndarray) -> np.ndarray:
    matrix = np.zeros((4, 4), dtype=float)
    if candidate_id.startswith("o2_"):
        for state, probability in enumerate(probabilities):
            last = state & 1
            matrix[state, 2 * last] = 1.0 - probability
            matrix[state, 2 * last + 1] = probability
    elif candidate_id.startswith("sm2_"):
        dry1, dry2, wet1, wet2 = probabilities
        matrix[0, 1], matrix[0, 2] = dry1, 1.0 - dry1
        matrix[1, 1], matrix[1, 2] = dry2, 1.0 - dry2
        matrix[2, 3], matrix[2, 0] = wet1, 1.0 - wet1
        matrix[3, 3], matrix[3, 0] = wet2, 1.0 - wet2
    else:
        raise ValueError(candidate_id)
    return matrix


def stationary(matrix: np.ndarray) -> np.ndarray:
    system = matrix.T - np.eye(len(matrix))
    system[-1, :] = 1.0
    target = np.zeros(len(matrix))
    target[-1] = 1.0
    values = np.linalg.solve(system, target)
    if np.min(values) < -1e-12 or abs(float(np.sum(values)) - 1.0) > 1e-10:
        raise ValueError("invalid stationary distribution")
    return np.maximum(values, 0.0) / np.sum(np.maximum(values, 0.0))


def wet_mask(candidate_id: str) -> np.ndarray:
    if candidate_id.startswith("o2_"):
        return np.asarray([0.0, 1.0, 0.0, 1.0])
    return np.asarray([0.0, 0.0, 1.0, 1.0])


def shifted_probabilities(
    candidate_id: str, base: np.ndarray, shift: float
) -> np.ndarray:
    logits = np.log(base / (1.0 - base))
    if candidate_id.startswith("o2_"):
        return expit(logits + shift)
    return expit(logits + np.asarray([-shift, -shift, shift, shift]))


def recenter_kernel(
    candidate_id: str,
    base: np.ndarray,
    target_wet_fraction: float,
    contract: dict[str, Any],
) -> dict[str, Any]:
    mask = wet_mask(candidate_id)

    def error(shift: float) -> float:
        probabilities = shifted_probabilities(candidate_id, base, shift)
        pi = stationary(transition_matrix(candidate_id, probabilities))
        return float(pi @ mask - target_wet_fraction)

    shift = brentq(
        error,
        -40.0,
        40.0,
        xtol=contract["numeric_rules"]["root_absolute_tolerance"],
        rtol=4.0 * np.finfo(float).eps,
    )
    probabilities = shifted_probabilities(candidate_id, base, shift)
    matrix = transition_matrix(candidate_id, probabilities)
    pi = stationary(matrix)
    wet_fraction = float(pi @ mask)
    guard = contract["numeric_rules"]["minimum_probability"]
    reasons: list[str] = []
    if np.min(probabilities) < guard or np.max(probabilities) > 1.0 - guard:
        reasons.append("probability_guard")
    if (
        abs(wet_fraction - target_wet_fraction)
        > contract["numeric_rules"]["stationary_wet_fraction_absolute_tolerance"]
    ):
        reasons.append("stationary_wet_fraction_error")
    return {
        "infeasibility_reasons": reasons,
        "probabilities": probabilities,
        "stationary": pi,
        "stationary_wet_fraction": wet_fraction,
        "transition": matrix,
        "logit_shift": float(shift),
    }


def occurrence_moments(
    matrix: np.ndarray, pi: np.ndarray, mask: np.ndarray, days: int
) -> dict[str, Any]:
    wet_fraction = float(pi @ mask)
    endpoint: list[float] = []
    all_wet: list[float] = []
    power = np.eye(len(matrix))
    restricted = matrix * mask[np.newaxis, :]
    all_vector = pi * mask
    for _lag in range(1, days):
        power = power @ matrix
        endpoint.append(float((pi * mask) @ power @ mask))
        all_vector = all_vector @ restricted
        all_wet.append(float(np.sum(all_vector)))
    variance = days * wet_fraction * (1.0 - wet_fraction)
    variance += 2.0 * sum(
        (days - lag) * (value - wet_fraction * wet_fraction)
        for lag, value in enumerate(endpoint, 1)
    )
    return {
        "all_wet_probabilities": all_wet,
        "endpoint_wet_probabilities": endpoint,
        "wet_count_variance": float(variance),
        "wet_fraction": wet_fraction,
    }


def baseline_occurrence(pww: float, pwd: float, days: int) -> dict[str, Any]:
    matrix = np.asarray([[1.0 - pwd, pwd], [1.0 - pww, pww]])
    pi = stationary(matrix)
    return occurrence_moments(matrix, pi, np.asarray([0.0, 1.0]), days)


class AmountShape:
    def __init__(self, fit: dict[str, Any], contract: dict[str, Any]) -> None:
        self.probabilities = np.asarray(
            contract["amount_model"]["quantile_probabilities"], dtype=float
        )
        self.log_knots = np.log(np.asarray(fit["log_quantile_knots_mm"], dtype=float))
        order = contract["numeric_rules"]["gauss_legendre_order"]
        nodes, weights = np.polynomial.legendre.leggauss(order)
        self.gl_u = (nodes + 1.0) / 2.0
        self.gl_w = weights / 2.0
        gh_order = contract["numeric_rules"]["gauss_hermite_order"]
        gh_nodes, gh_weights = np.polynomial.hermite.hermgauss(gh_order)
        normals = math.sqrt(2.0) * gh_nodes
        self.gh_z1 = normals[:, np.newaxis]
        self.gh_eps = normals[np.newaxis, :]
        self.gh_weights = (gh_weights[:, np.newaxis] * gh_weights[np.newaxis, :]) / math.pi
        self.rho = float(fit["gaussian_copula_rho"])

    def normalization(self, dispersion: float) -> tuple[float, float]:
        z = np.interp(self.gl_u, self.probabilities, self.log_knots)
        shift = float(np.max(dispersion * z))
        normalizer = float(np.sum(self.gl_w * np.exp(dispersion * z - shift)))
        return shift, normalizer

    def quantile(self, u: np.ndarray | float, dispersion: float) -> np.ndarray:
        shift, normalizer = self.normalization(dispersion)
        z = np.interp(u, self.probabilities, self.log_knots)
        return np.exp(dispersion * z - shift) / normalizer

    def cv_squared(self, dispersion: float) -> float:
        values = self.quantile(self.gl_u, dispersion)
        return max(0.0, float(np.sum(self.gl_w * values * values) - 1.0))

    def covariance(self, dispersion: float, correlation: float) -> float:
        if dispersion == 0.0 or correlation == 0.0:
            return 0.0
        z2 = correlation * self.gh_z1 + math.sqrt(
            max(0.0, 1.0 - correlation * correlation)
        ) * self.gh_eps
        left = self.quantile(ndtr(self.gh_z1), dispersion)
        right = self.quantile(ndtr(z2), dispersion)
        return float(np.sum(self.gh_weights * left * right) - 1.0)

    def total_dimensionless_variance(
        self,
        dispersion: float,
        occurrence: dict[str, Any],
        days: int,
    ) -> float:
        total = occurrence["wet_count_variance"]
        total += days * occurrence["wet_fraction"] * self.cv_squared(dispersion)
        for lag, all_wet in enumerate(occurrence["all_wet_probabilities"], 1):
            total += (
                2.0
                * (days - lag)
                * all_wet
                * self.covariance(dispersion, self.rho**lag)
            )
        return float(total)


def solve_dispersion(
    function: Callable[[float], float],
    target: float,
    maximum: float,
    tolerance: float,
) -> float:
    at_zero = function(0.0) - target
    if abs(at_zero) <= tolerance:
        return 0.0
    high = min(1.0, maximum)
    while high < maximum and function(high) < target:
        high = min(maximum, high * 2.0)
    if function(high) < target:
        raise ValueError("dispersion root exceeds frozen maximum")
    return float(brentq(lambda value: function(value) - target, 0.0, high, xtol=tolerance))


def certify_amount_budget(
    shape: AmountShape,
    occurrence: dict[str, Any],
    baseline: dict[str, Any],
    days: int,
    mean_mm: float,
    sd_mm: float,
    contract: dict[str, Any],
) -> dict[str, Any]:
    numeric = contract["numeric_rules"]
    cv_legacy_squared = (sd_mm / mean_mm) ** 2
    reasons: list[str] = []
    try:
        legacy_dispersion = solve_dispersion(
            shape.cv_squared,
            cv_legacy_squared,
            numeric["root_maximum_lambda"],
            numeric["root_absolute_tolerance"],
        )
    except ValueError:
        return {
            "feasible": False,
            "infeasibility_reasons": ["legacy_amount_variance_not_representable"],
        }
    target_dimensionless = (
        baseline["wet_count_variance"]
        + days * baseline["wet_fraction"] * cv_legacy_squared
    )
    occurrence_only = shape.total_dimensionless_variance(0.0, occurrence, days)
    at_legacy = shape.total_dimensionless_variance(
        legacy_dispersion, occurrence, days
    )
    scale = max(1.0, abs(target_dimensionless))
    allowed = numeric["budget_relative_tolerance"] * scale
    if occurrence_only > target_dimensionless + allowed:
        reasons.append("occurrence_variance_exceeds_legacy_budget")
    if at_legacy < target_dimensionless - allowed:
        reasons.append("requires_wet_amount_variance_increase")
    grid = np.linspace(0.0, legacy_dispersion, 17)
    grid_values = [shape.total_dimensionless_variance(x, occurrence, days) for x in grid]
    if any(right + allowed < left for left, right in zip(grid_values, grid_values[1:])):
        reasons.append("nonmonotone_budget_mapping")
    if reasons:
        return {
            "candidate_at_legacy_dimensionless_variance": at_legacy,
            "feasible": False,
            "infeasibility_reasons": reasons,
            "legacy_dispersion": legacy_dispersion,
            "legacy_target_dimensionless_variance": target_dimensionless,
            "occurrence_only_dimensionless_variance": occurrence_only,
        }
    if abs(target_dimensionless - occurrence_only) <= allowed:
        budget_dispersion = 0.0
    elif abs(target_dimensionless - at_legacy) <= allowed:
        budget_dispersion = legacy_dispersion
    else:
        budget_dispersion = float(
            brentq(
                lambda value: shape.total_dimensionless_variance(
                    value, occurrence, days
                )
                - target_dimensionless,
                0.0,
                legacy_dispersion,
                xtol=numeric["root_absolute_tolerance"],
            )
        )
    achieved = shape.total_dimensionless_variance(budget_dispersion, occurrence, days)
    relative_error = abs(achieved - target_dimensionless) / scale
    retained = (
        shape.cv_squared(budget_dispersion) / cv_legacy_squared
        if cv_legacy_squared > 0.0
        else 1.0
    )
    tail_errors = []
    for probability in (0.95, 0.99):
        observed = float(shape.quantile(probability, 1.0))
        candidate = float(shape.quantile(probability, budget_dispersion))
        tail_errors.append(abs(math.log(candidate / observed)))
    tail_error = max(tail_errors)
    if relative_error > numeric["budget_relative_tolerance"]:
        reasons.append("monthly_variance_budget_error")
    if retained < numeric["minimum_wet_amount_variance_retention"]:
        reasons.append("wet_amount_variance_retention")
    if tail_error > numeric["maximum_tail_log_error"]:
        reasons.append("tail_log_error")
    return {
        "achieved_dimensionless_variance": achieved,
        "budget_dispersion": budget_dispersion,
        "candidate_at_legacy_dimensionless_variance": at_legacy,
        "feasible": not reasons,
        "infeasibility_reasons": reasons,
        "legacy_amount_cv_squared": cv_legacy_squared,
        "legacy_dispersion": legacy_dispersion,
        "legacy_target_dimensionless_variance": target_dimensionless,
        "monthly_variance_relative_error": relative_error,
        "occurrence_only_dimensionless_variance": occurrence_only,
        "tail_log_errors": {"p95": tail_errors[0], "p99": tail_errors[1]},
        "tail_log_error_max": tail_error,
        "wet_amount_variance_retention": retained,
    }


def station_log_loss_improvement(
    series: DailySeries,
    candidate_id: str,
    monthly_probabilities: list[list[float]],
    legacy: dict[str, list[float]],
) -> dict[str, float | int]:
    wet = series.wet
    candidate_nll = 0.0
    baseline_nll = 0.0
    count = 0
    run_age = 1
    start = 2 if candidate_id.startswith("o2_") else 1
    for index in range(1, len(wet)):
        if index < start:
            run_age = run_age + 1 if wet[index] == wet[index - 1] else 1
            continue
        month = series.dates[index][1] - 1
        previous_wet = bool(wet[index - 1])
        if candidate_id.startswith("o2_"):
            state = 2 * int(wet[index - 2]) + int(wet[index - 1])
            candidate_probability = monthly_probabilities[month][state]
        else:
            state = (2 if previous_wet else 0) + (1 if run_age >= 2 else 0)
            continuation = monthly_probabilities[month][state]
            candidate_probability = continuation if previous_wet else 1.0 - continuation
        baseline_probability = (
            legacy["pww"][month] if previous_wet else legacy["pwd"][month]
        )
        outcome = bool(wet[index])
        candidate_nll -= math.log(
            candidate_probability if outcome else 1.0 - candidate_probability
        )
        baseline_nll -= math.log(
            baseline_probability if outcome else 1.0 - baseline_probability
        )
        count += 1
        run_age = run_age + 1 if wet[index] == wet[index - 1] else 1
    return {
        "baseline_negative_log_likelihood": baseline_nll,
        "candidate_negative_log_likelihood": candidate_nll,
        "evaluated_days": count,
        "improvement": baseline_nll - candidate_nll,
    }


def median(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def candidate_summary(
    candidate_id: str,
    cells: list[dict[str, Any]],
    likelihoods: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    candidate_cells = [cell for cell in cells if cell["candidate_id"] == candidate_id]
    feasible = [cell for cell in candidate_cells if cell["feasible"]]
    development = set(contract["comparison"]["development_stations"])
    development_feasible = sum(
        cell["feasible"] and cell["station_id"] in development
        for cell in candidate_cells
    )
    reasons: dict[str, int] = {}
    for cell in candidate_cells:
        for reason in cell["infeasibility_reasons"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    summary = {
        "candidate_id": candidate_id,
        "corpus_feasible_cells": len(feasible),
        "development_feasible_cells": development_feasible,
        "infeasibility_reason_counts": reasons,
        "median_station_occurrence_log_loss_improvement": median(
            [entry["improvement"] for entry in likelihoods if entry["candidate_id"] == candidate_id]
        ),
        "median_tail_log_error": median(
            [cell["budget"]["tail_log_error_max"] for cell in feasible]
        ),
        "median_wet_amount_variance_retention": median(
            [cell["budget"]["wet_amount_variance_retention"] for cell in feasible]
        ),
        "total_cells": len(candidate_cells),
    }
    summary["qualifies"] = bool(
        development_feasible
        == contract["decision"]["development_feasible_cells_required"]
        and len(feasible) >= contract["decision"]["corpus_feasible_cells_min"]
    )
    return summary


def ranking_key(summary: dict[str, Any]) -> tuple[Any, ...]:
    improvement = summary["median_station_occurrence_log_loss_improvement"]
    retention = summary["median_wet_amount_variance_retention"]
    tail = summary["median_tail_log_error"]
    return (
        -summary["development_feasible_cells"],
        -summary["corpus_feasible_cells"],
        -(improvement if improvement is not None else -math.inf),
        -(retention if retention is not None else -math.inf),
        tail if tail is not None else math.inf,
        summary["candidate_id"],
    )


def run_analysis(repo: Path, contract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    checked = {
        name: checked_input(repo, entry)
        for name, entry in contract["inputs"].items()
    }
    a7a = load_json(checked["a7a_decision"])
    if a7a.get("terminal_decision") != "DAILY-PRECIPITATION-GAP-MEASURED":
        raise ValueError("A7a did not authorize A7b")
    config = load_json(checked["corpus_config"])
    manifest = load_json(checked["source_manifest"])
    if sha256(canonical_json_bytes(config)) != manifest["config_sha256"]:
        raise ValueError("corpus config/manifest mismatch")
    stations = config["stations"]
    if len(stations) != 17:
        raise ValueError("A7b requires exactly 17 frozen stations")
    common = load_module(checked["corpus_common"])
    series = load_daymet_series(
        repo,
        common,
        config,
        manifest,
        contract["amount_model"]["wet_day_threshold_mm"],
    )
    legacy = load_legacy_parameters(checked["baseline_archive"], stations)

    amount_fits: list[dict[str, Any]] = []
    occurrence_fits: list[dict[str, Any]] = []
    amount_index: dict[tuple[str, str], dict[str, Any]] = {}
    occurrence_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for station in stations:
        station_id = station["station_id"]
        for season in SEASONS:
            amount = seasonal_amount_fit(series[station_id], season, contract)
            amount["station_id"] = station_id
            amount_fits.append(amount)
            amount_index[(station_id, season)] = amount
            for candidate in contract["candidates"]:
                fit = seasonal_occurrence_fit(
                    series[station_id], season, candidate["candidate_id"], contract
                )
                fit["station_id"] = station_id
                occurrence_fits.append(fit)
                occurrence_index[(candidate["candidate_id"], station_id, season)] = fit

    cells: list[dict[str, Any]] = []
    likelihoods: list[dict[str, Any]] = []
    month_lengths = contract["comparison"]["month_lengths"]
    for candidate in contract["candidates"]:
        candidate_id = candidate["candidate_id"]
        for station in stations:
            station_id = station["station_id"]
            monthly_probabilities: list[list[float]] = []
            station_cells: list[dict[str, Any]] = []
            for month_number, days in enumerate(month_lengths, 1):
                season = season_for_month(contract, month_number)
                amount_fit = amount_index[(station_id, season)]
                occurrence_fit = occurrence_index[(candidate_id, station_id, season)]
                target = legacy[station_id]
                pww = target["pww"][month_number - 1]
                pwd = target["pwd"][month_number - 1]
                target_wet_fraction = pwd / (1.0 - pww + pwd)
                reasons = list(amount_fit["infeasibility_reasons"])
                reasons.extend(occurrence_fit["infeasibility_reasons"])
                cell: dict[str, Any] = {
                    "candidate_id": candidate_id,
                    "days": days,
                    "infeasibility_reasons": reasons,
                    "legacy": {
                        "pwd": pwd,
                        "pww": pww,
                        "stationary_wet_fraction": target_wet_fraction,
                        "wet_mean_mm": target["wet_mean_mm"][month_number - 1],
                        "wet_sd_mm": target["wet_sd_mm"][month_number - 1],
                    },
                    "month": month_number,
                    "season": season,
                    "station_id": station_id,
                }
                recentered = recenter_kernel(
                    candidate_id,
                    np.asarray(occurrence_fit["probabilities"]),
                    target_wet_fraction,
                    contract,
                )
                monthly_probabilities.append(
                    [float(value) for value in recentered["probabilities"]]
                )
                reasons.extend(recentered["infeasibility_reasons"])
                cell["kernel"] = {
                    "logit_shift": recentered["logit_shift"],
                    "probabilities": [float(value) for value in recentered["probabilities"]],
                    "stationary_distribution": [float(value) for value in recentered["stationary"]],
                    "stationary_wet_fraction": recentered["stationary_wet_fraction"],
                    "transition_matrix": [
                        [float(value) for value in row] for row in recentered["transition"]
                    ],
                }
                if amount_fit["identifiable"] and occurrence_fit["identifiable"] and not recentered["infeasibility_reasons"]:
                    occurrence = occurrence_moments(
                        recentered["transition"],
                        recentered["stationary"],
                        wet_mask(candidate_id),
                        days,
                    )
                    baseline = baseline_occurrence(pww, pwd, days)
                    shape = AmountShape(amount_fit, contract)
                    budget = certify_amount_budget(
                        shape,
                        occurrence,
                        baseline,
                        days,
                        target["wet_mean_mm"][month_number - 1],
                        target["wet_sd_mm"][month_number - 1],
                        contract,
                    )
                    reasons.extend(budget["infeasibility_reasons"])
                    cell["occurrence_moments"] = {
                        "legacy_wet_count_variance": baseline["wet_count_variance"],
                        "candidate_wet_count_variance": occurrence["wet_count_variance"],
                    }
                    cell["budget"] = budget
                else:
                    cell["budget"] = {
                        "feasible": False,
                        "infeasibility_reasons": list(reasons),
                    }
                cell["infeasibility_reasons"] = sorted(set(reasons))
                cell["feasible"] = not cell["infeasibility_reasons"]
                station_cells.append(cell)
                cells.append(cell)
            likelihood = station_log_loss_improvement(
                series[station_id], candidate_id, monthly_probabilities, legacy[station_id]
            )
            likelihood.update({"candidate_id": candidate_id, "station_id": station_id})
            likelihoods.append(likelihood)

    summaries = [
        candidate_summary(candidate["candidate_id"], cells, likelihoods, contract)
        for candidate in contract["candidates"]
    ]
    ranking = sorted(summaries, key=ranking_key)
    qualifying = [summary for summary in ranking if summary["qualifies"]]
    if qualifying:
        selected = qualifying[0]["candidate_id"]
        terminal = next(
            item["terminal"] for item in contract["candidates"] if item["candidate_id"] == selected
        )
    else:
        selected = None
        terminal = contract["decision"]["no_candidate_terminal"]
    decision = {
        "analysis_id": contract["analysis_id"],
        "candidate_summaries": summaries,
        "decision_contract_sha256": sha256(canonical_json_bytes(contract)),
        "interpretation": (
            "Analytic feasibility authorizes only a separately frozen A7c development pilot; "
            "it is not evidence of generated-climate improvement."
        ),
        "ranking": [summary["candidate_id"] for summary in ranking],
        "schema_version": 1,
        "selected_candidate": selected,
        "terminal": terminal,
    }
    analysis = {
        "analysis_id": contract["analysis_id"],
        "amount_fits": amount_fits,
        "candidate_summaries": summaries,
        "cells": cells,
        "execution_counts": {
            "amount_station_season_fits": len(amount_fits),
            "candidate_station_month_cells": len(cells),
            "occurrence_candidate_station_season_fits": len(occurrence_fits),
            "stations": len(stations),
        },
        "input_identities": {
            name: entry["sha256"] for name, entry in contract["inputs"].items()
        },
        "occurrence_fits": occurrence_fits,
        "occurrence_likelihoods": likelihoods,
        "rng_ownership_certification": {
            **contract["rng_ownership"],
            "status": "STATIC-CONTRACT-SATISFIED",
        },
        "schema_version": 1,
        "source_commit": contract["source_commit"],
        "terminal": terminal,
    }
    return analysis, decision


def findings_markdown(decision: dict[str, Any]) -> str:
    def rendered(value: float | None) -> str:
        return "n/a" if value is None else format(value, ".6g")

    lines = [
        "# A7b Findings",
        "",
        f"Terminal: `{decision['terminal']}`",
        "",
        "A7b performed analytic fitting and moment certification only. It generated no",
        "candidate climate and made no claim of climate improvement.",
        "",
        "| Candidate | Development feasible | Corpus feasible | Median log-loss improvement | Median retention | Median tail error | Qualifies |",
        "|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for summary in decision["candidate_summaries"]:
        lines.append(
            f"| {summary['candidate_id']} | {summary['development_feasible_cells']}/36 | "
            f"{summary['corpus_feasible_cells']}/204 | "
            f"{rendered(summary['median_station_occurrence_log_loss_improvement'])} | "
            f"{rendered(summary['median_wet_amount_variance_retention'])} | "
            f"{rendered(summary['median_tail_log_error'])} | {summary['qualifies']} |"
        )
    lines.extend(
        [
            "",
            "## Disposition",
            "",
            (
                f"Selected `{decision['selected_candidate']}` for a separately frozen A7c "
                "three-station development pilot."
                if decision["selected_candidate"]
                else "Neither bounded mechanism met the frozen A7b feasibility surface; the precipitation line stops."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def synthetic_check() -> None:
    for candidate_id in STATE_LABELS:
        base = np.asarray([0.7, 0.6, 0.55, 0.5])
        target = 0.3
        contract = load_json(ARTIFACTS / CONTRACT_NAME)
        result = recenter_kernel(candidate_id, base, target, contract)
        assert abs(result["stationary_wet_fraction"] - target) < 1e-10
        moments = occurrence_moments(
            result["transition"], result["stationary"], wet_mask(candidate_id), 31
        )
        assert moments["wet_count_variance"] >= 0.0
    print("A7b synthetic kernel checks: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--synthetic-check", action="store_true")
    parser.add_argument("--output", type=Path, default=ARTIFACTS / ANALYSIS_NAME)
    parser.add_argument("--decision", type=Path, default=ARTIFACTS / DECISION_NAME)
    parser.add_argument("--findings", type=Path, default=ARTIFACTS / FINDINGS_NAME)
    args = parser.parse_args()
    if args.synthetic_check:
        synthetic_check()
        return
    repo = args.repo.resolve()
    contract = load_json(ARTIFACTS / CONTRACT_NAME)
    check_source_boundary(repo, contract["source_commit"])
    check_freeze(repo, contract)
    analysis, decision = run_analysis(repo, contract)
    args.output.write_bytes(canonical_json_bytes(analysis))
    args.decision.write_bytes(canonical_json_bytes(decision))
    args.findings.write_text(findings_markdown(decision), encoding="utf-8")
    print(decision["terminal"])


if __name__ == "__main__":
    main()
