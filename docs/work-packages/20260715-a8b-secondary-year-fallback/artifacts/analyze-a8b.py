#!/usr/bin/env python3
"""Deterministic analytic and held-out feasibility analysis for A8b."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import rankdata

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
CANDIDATE_ID = "bounded_eof2_copula_ar1_reallocation_v1"
NULL_ID = "legacy_daily_only_v1"


class CandidateInfeasible(ValueError):
    def __init__(self, code: str, context: dict[str, Any]) -> None:
        super().__init__(code)
        self.code = code
        self.context = context


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def checked_input(contract: dict[str, Any], name: str) -> Path:
    entry = contract["inputs"][name]
    path = REPO / entry["path"]
    actual = sha256(path.read_bytes())
    if actual != entry["sha256"]:
        raise ValueError(f"input mismatch for {name}: {actual}")
    return path


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(item) for item in value]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    return value


def check_freeze(contract: dict[str, Any]) -> dict[str, Any]:
    freeze = load_json(ARTIFACTS / "pre-analysis-freeze-v2.json")
    if freeze["status"] != "FROZEN-BEFORE-A8B-CANDIDATE-FIT":
        raise ValueError("A8b pre-analysis freeze is not active")
    for relative, expected in freeze["frozen_files_sha256"].items():
        if sha256((REPO / relative).read_bytes()) != expected:
            raise ValueError(f"frozen file changed: {relative}")
    if freeze["source_commit"] != contract["source_commit"]:
        raise ValueError("source commit mismatch")
    return freeze


def annual_monthly_totals(series: Any, start: int, end: int) -> np.ndarray:
    years = list(range(start, end + 1))
    index = {year: row for row, year in enumerate(years)}
    totals = np.zeros((len(years), 12), dtype=float)
    counts = np.zeros((len(years), 12), dtype=int)
    for date, amount in zip(series.dates, series.amounts):
        year, month, _day = date
        if start <= year <= end:
            totals[index[year], month - 1] += float(amount)
            counts[index[year], month - 1] += 1
    expected = np.tile(np.asarray(MONTH_DAYS, dtype=int), (len(years), 1))
    if not np.array_equal(counts, expected):
        raise ValueError(f"incomplete annual/monthly matrix for {start}-{end}")
    return totals


def deterministic_eigh(matrix: np.ndarray, rank: int, tolerance: float) -> tuple[np.ndarray, np.ndarray]:
    values, vectors = np.linalg.eigh(matrix)
    order = sorted(range(len(values)), key=lambda index: (-float(values[index]), index))
    values = values[order]
    vectors = vectors[:, order]
    if values[rank - 1] <= tolerance:
        raise ValueError("nonpositive retained EOF eigenvalue")
    if rank < len(values) and abs(float(values[rank - 1] - values[rank])) <= tolerance:
        raise ValueError("EOF rank boundary is tied")
    for column in range(rank):
        vector = vectors[:, column]
        maximum = float(np.max(np.abs(vector)))
        pivot = int(np.flatnonzero(np.abs(vector) >= maximum - tolerance)[0])
        if vector[pivot] < 0.0:
            vectors[:, column] *= -1.0
    return values, vectors


def spearman(left: list[float], right: list[float]) -> float:
    if len(left) < 3:
        raise ValueError("insufficient lag pairs")
    left_rank = rankdata(left, method="average")
    right_rank = rankdata(right, method="average")
    value = float(np.corrcoef(left_rank, right_rank)[0, 1])
    if not math.isfinite(value):
        raise ValueError("nonfinite lag correlation")
    return value


def fit_shared_model(
    training: dict[str, np.ndarray], contract: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[str, np.ndarray]]]:
    standardized: dict[str, dict[str, np.ndarray]] = {}
    pooled = []
    for station_id in sorted(training):
        matrix = training[station_id]
        center = np.mean(matrix, axis=0)
        scale = np.std(matrix, axis=0, ddof=1)
        zero_months = [
            index + 1
            for index, value in enumerate(scale)
            if value <= contract["numeric"]["absolute_zero_tolerance"]
        ]
        if zero_months:
            raise CandidateInfeasible(
                "zero_training_monthly_scale",
                {"months": zero_months, "station_id": station_id},
            )
        values = (matrix - center) / scale
        standardized[station_id] = {"center": center, "scale": scale, "values": values}
        pooled.append(values)
    pooled_values = np.vstack(pooled)
    sample = np.cov(pooled_values, rowvar=False, ddof=1)
    shrinkage = contract["mechanism"]["shrinkage_to_diagonal"]
    shrunk = (1.0 - shrinkage) * sample + shrinkage * np.eye(12)
    eigenvalues, eigenvectors = deterministic_eigh(
        shrunk,
        contract["mechanism"]["eof_rank"],
        contract["mechanism"]["eigenvalue_tie_tolerance"],
    )
    rank = contract["mechanism"]["eof_rank"]
    retained_vectors = eigenvectors[:, :rank]
    retained_values = eigenvalues[:rank]
    basis = retained_vectors @ np.diag(np.sqrt(retained_values))
    lag_spearman = []
    latent_rho = []
    implied_state_correlation = []
    for mode in range(rank):
        left: list[float] = []
        right: list[float] = []
        for station_id in sorted(standardized):
            scores = standardized[station_id]["values"] @ retained_vectors
            left.extend(float(value) for value in scores[:-1, mode])
            right.extend(float(value) for value in scores[1:, mode])
        observed = spearman(left, right)
        rho = 2.0 * math.sin(math.pi * observed / 6.0)
        cap = contract["mechanism"]["gaussian_copula_rho_absolute_max"]
        rho = min(cap, max(-cap, rho))
        implied = 6.0 / math.pi * math.asin(rho / 2.0)
        lag_spearman.append(observed)
        latent_rho.append(rho)
        implied_state_correlation.append(implied)
    explained = float(np.sum(retained_values) / np.sum(eigenvalues))
    model = {
        "basis": basis,
        "eigenvalues": eigenvalues,
        "eigenvectors": retained_vectors,
        "explained_fraction": explained,
        "implied_state_lag_correlation": implied_state_correlation,
        "latent_gaussian_rho": latent_rho,
        "pooled_row_count": len(pooled_values),
        "training_score_lag_spearman": lag_spearman,
    }
    return model, standardized


def fit_station_budget(
    station_id: str,
    legacy: dict[str, Any],
    basis: np.ndarray,
    contract: dict[str, Any],
    a7b_contract: dict[str, Any],
    a7b: Any,
) -> dict[str, Any]:
    mechanism = contract["mechanism"]
    tolerance = contract["numeric"]["absolute_zero_tolerance"]
    months: list[dict[str, Any]] = []
    raw_loadings = np.zeros((12, mechanism["eof_rank"]), dtype=float)
    gamma_bounds = [1.0]
    base_rows = []
    for month, days in enumerate(a7b_contract["comparison"]["month_lengths"], 1):
        mean = float(legacy["wet_mean_mm"][month - 1])
        sd = float(legacy["wet_sd_mm"][month - 1])
        pww = float(legacy["pww"][month - 1])
        pwd = float(legacy["pwd"][month - 1])
        occurrence = a7b.baseline_occurrence(pww, pwd, days)
        wet_count_mean = days * float(occurrence["wet_fraction"])
        wet_count_variance = float(occurrence["wet_count_variance"])
        wet_count_second = wet_count_variance + wet_count_mean**2
        legacy_variance = wet_count_mean * sd**2 + wet_count_variance * mean**2
        active = bool(
            wet_count_mean > tolerance
            and mean > tolerance
            and sd > tolerance
            and legacy_variance > tolerance
        )
        if active:
            raw_loadings[month - 1, :] = (
                math.sqrt(mechanism["allocation_fraction"] * legacy_variance)
                * basis[month - 1, :]
            )
        raw_variance = float(raw_loadings[month - 1] @ raw_loadings[month - 1])
        if active and raw_variance > tolerance:
            retention_numerator = (
                (1.0 - mechanism["residual_variance_retention_min"])
                * sd**2
                * wet_count_mean**3
            )
            retention_denominator = raw_variance * wet_count_second
            gamma_bounds.append(math.sqrt(retention_numerator / retention_denominator))
            absolute_loading = float(np.sum(np.abs(raw_loadings[month - 1])))
            if absolute_loading > tolerance:
                gamma_bounds.append(
                    (1.0 - mechanism["minimum_wet_amount_mean_fraction"])
                    * mean
                    * wet_count_mean
                    / (math.sqrt(3.0) * absolute_loading)
                )
        base_rows.append(
            {
                "active": active,
                "days": days,
                "legacy_monthly_mean_mm": wet_count_mean * mean,
                "legacy_monthly_variance_mm2": legacy_variance,
                "legacy_wet_amount_mean_mm": mean,
                "legacy_wet_amount_sd_mm": sd,
                "month": month,
                "pwd": pwd,
                "pww": pww,
                "wet_count_mean": wet_count_mean,
                "wet_count_second_moment": wet_count_second,
                "wet_count_variance": wet_count_variance,
                "wet_fraction": occurrence["wet_fraction"],
            }
        )
    gamma_limit = min(gamma_bounds)
    gamma = mechanism["scale_safety_factor"] * min(1.0, gamma_limit)
    loadings = gamma * raw_loadings
    covariance = loadings @ loadings.T
    allocated = 0
    station_reasons: list[str] = []
    for row in base_rows:
        index = row["month"] - 1
        reasons: list[str] = []
        state_variance = float(covariance[index, index])
        if row["active"] and state_variance > tolerance:
            allocated += 1
            n = row["wet_count_mean"]
            e2 = row["wet_count_second_moment"]
            mean = row["legacy_wet_amount_mean_mm"]
            variance = row["legacy_wet_amount_sd_mm"] ** 2
            residual_variance = variance - state_variance * e2 / n**3
            retention = residual_variance / variance
            minimum_mean = mean - math.sqrt(3.0) * float(np.sum(np.abs(loadings[index]))) / n
            minimum_mean_fraction = minimum_mean / mean
            reconstructed = (
                n * residual_variance
                + row["wet_count_variance"] * (mean**2 + state_variance / n**2)
                + state_variance
            )
            relative_error = abs(reconstructed - row["legacy_monthly_variance_mm2"]) / max(
                row["legacy_monthly_variance_mm2"], 1.0
            )
            if retention < mechanism["residual_variance_retention_min"] - tolerance:
                reasons.append("residual_variance_retention")
            if minimum_mean_fraction < mechanism["minimum_wet_amount_mean_fraction"] - tolerance:
                reasons.append("minimum_wet_amount_mean")
            if relative_error > contract["numeric"]["monthly_budget_relative_tolerance"]:
                reasons.append("monthly_variance_budget")
        else:
            residual_variance = row["legacy_wet_amount_sd_mm"] ** 2
            retention = 1.0
            minimum_mean = row["legacy_wet_amount_mean_mm"]
            minimum_mean_fraction = 1.0 if minimum_mean > 0.0 else None
            reconstructed = row["legacy_monthly_variance_mm2"]
            relative_error = 0.0
            if state_variance > tolerance:
                reasons.append("inactive_month_nonzero_loading")
        months.append(
            {
                **row,
                "candidate_monthly_mean_mm": row["legacy_monthly_mean_mm"],
                "candidate_monthly_variance_mm2": reconstructed,
                "feasible": not reasons,
                "infeasibility_reasons": reasons,
                "minimum_wet_amount_mean_fraction": minimum_mean_fraction,
                "minimum_wet_amount_mean_mm": minimum_mean,
                "residual_variance_retention": retention,
                "residual_wet_amount_sd_mm": math.sqrt(max(0.0, residual_variance)),
                "state_loadings_total_mm": loadings[index].tolist(),
                "state_variance_mm2": state_variance,
                "variance_budget_relative_error": relative_error,
                "wet_fraction_error": 0.0,
            }
        )
    if gamma < mechanism["minimum_station_scale"]:
        station_reasons.append("station_scale_below_minimum")
    if allocated < mechanism["minimum_allocated_months_per_station"]:
        station_reasons.append("insufficient_allocated_months")
    if any(not month["feasible"] for month in months):
        station_reasons.append("monthly_budget_failure")
    return {
        "allocated_month_count": allocated,
        "candidate_id": CANDIDATE_ID,
        "feasible": not station_reasons,
        "gamma": gamma,
        "gamma_limit": gamma_limit,
        "infeasibility_reasons": station_reasons,
        "legacy_parameter_sha256": legacy["parameter_sha256"],
        "months": months,
        "secondary_state_covariance_mm2": covariance,
        "station_id": station_id,
    }


def validation_metrics(
    validation: np.ndarray,
    coefficient: dict[str, Any],
    shrinkage: float,
) -> dict[str, Any]:
    sample = np.cov(validation, rowvar=False, ddof=1)
    target = (1.0 - shrinkage) * sample + shrinkage * np.diag(np.diag(sample))
    scale = np.sqrt(np.maximum(np.diag(target), np.finfo(float).tiny))
    denominator = np.outer(scale, scale)
    target_correlation = target / denominator
    candidate_covariance = np.asarray(coefficient["secondary_state_covariance_mm2"])
    candidate_correlation = candidate_covariance / denominator
    indices = np.triu_indices(12, 1)
    target_cells = target_correlation[indices]
    candidate_cells = candidate_correlation[indices]
    null_rmse = float(np.sqrt(np.mean(target_cells**2)))
    candidate_rmse = float(np.sqrt(np.mean((candidate_cells - target_cells) ** 2)))
    target_cross = float(np.sum(target) - np.trace(target))
    candidate_cross = float(np.sum(candidate_covariance) - np.trace(candidate_covariance))
    normalizer = max(float(np.trace(target)), np.finfo(float).tiny)
    null_annual_error = abs(target_cross) / normalizer
    candidate_annual_error = abs(candidate_cross - target_cross) / normalizer
    return {
        "candidate_annual_cross_covariance_error": candidate_annual_error,
        "candidate_cross_month_contribution_mm2": candidate_cross,
        "candidate_offdiagonal_correlation_rmse": candidate_rmse,
        "joint_improvement": bool(
            candidate_rmse < null_rmse and candidate_annual_error < null_annual_error
        ),
        "null_annual_cross_covariance_error": null_annual_error,
        "null_cross_month_contribution_mm2": 0.0,
        "null_offdiagonal_correlation_rmse": null_rmse,
        "target_cross_month_contribution_mm2": target_cross,
        "validation_year_count": len(validation),
    }


def ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0:
        return 0.0 if numerator <= 0.0 else None
    return numerator / denominator


def infeasible_candidate_outputs(
    contract: dict[str, Any],
    parent_valid: bool,
    alternatives_valid: bool,
    actual_development: set[str],
    actual_heldout: set[str],
    training: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    failure: CandidateInfeasible,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    guards = {
        "all_station_budgets_feasible": False,
        "annual_covariance_improvement": False,
        "cross_month_covariance_improvement": False,
        "eof_representation": False,
        "joint_station_breadth": False,
        "minimum_allocated_months": False,
        "persistence_not_degraded": False,
        "station_scale_bounds": False,
    }
    null_certified = bool(parent_valid and alternatives_valid)
    terminal = (
        contract["decision"]["null_terminal"]
        if null_certified
        else contract["decision"]["stop_terminal"]
    )
    selected = NULL_ID if null_certified else None
    fit_failure = {"code": failure.code, "context": failure.context}
    contract_sha = sha256((ARTIFACTS / "feasibility-contract-v1.json").read_bytes())
    freeze_sha = sha256((ARTIFACTS / "pre-analysis-freeze-v2.json").read_bytes())
    coefficients = {
        "analysis_contract_sha256": contract_sha,
        "candidate_id": CANDIDATE_ID,
        "candidate_eligible": False,
        "coefficient_schema": "a8b_bounded_eof2_reallocation_coefficients_v1",
        "fit_failure": fit_failure,
        "fit_status": "INFEASIBLE-BEFORE-COEFFICIENTS",
        "rng": contract["rng"],
        "schema_version": 1,
        "shared_model": None,
        "stations": [],
        "use_authorization": "none; candidate infeasible",
    }
    analysis = {
        "analysis_id": contract["analysis_id"],
        "analysis_contract_sha256": contract_sha,
        "candidate_skill": {
            "candidate_lag_error": None,
            "candidate_to_null_annual_covariance_error_ratio": None,
            "candidate_to_null_offdiagonal_rmse_ratio": None,
            "joint_station_improvement_count": 0,
            "null_lag_error": None,
            "validation_score_lag_spearman": None,
        },
        "execution_counts": {
            "alternatives": 2,
            "fallback_stations": len(training),
            "monthly_budget_cells": 0,
            "training_station_years": sum(len(value) for value in training.values()),
            "validation_station_years": sum(len(value) for value in validation.values()),
        },
        "fit_failure": fit_failure,
        "parent": {
            "development_fallback_station_ids": sorted(actual_development),
            "heldout_fallback_station_ids": sorted(actual_heldout),
            "terminal": contract["parent_required_terminal"],
            "valid": parent_valid,
        },
        "pre_analysis_freeze_sha256": freeze_sha,
        "schema_version": 1,
        "shared_fit": None,
        "station_results": [],
        "terminal": terminal,
    }
    decision = {
        "analysis_id": contract["analysis_id"],
        "candidate_eligible": False,
        "candidate_guards": guards,
        "fit_failure": fit_failure,
        "null_certified": null_certified,
        "parent_valid": parent_valid,
        "schema_version": 1,
        "selected_alternative": selected,
        "terminal": terminal,
    }
    return coefficients, analysis, decision


def analyze(contract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    for name in contract["inputs"]:
        checked_input(contract, name)
    parent_analysis = load_json(checked_input(contract, "a8a_analysis"))
    parent_decision = load_json(checked_input(contract, "a8a_decision"))
    expected_development = set(contract["corpus"]["expected_development_station_ids"])
    expected_heldout = set(contract["corpus"]["expected_heldout_station_ids"])
    actual_development = {
        entry["station_id"]
        for entry in parent_analysis["station_results"]
        if not entry["confirmation"] and entry["classification"] == "legacy_daily_fallback"
    }
    actual_heldout = {
        entry["station_id"]
        for entry in parent_analysis["station_results"]
        if entry["confirmation"] and entry["classification"] == "legacy_daily_fallback"
    }
    parent_valid = bool(
        parent_decision["terminal"] == contract["parent_required_terminal"]
        and all(parent_decision["guards"].values())
        and actual_development == expected_development
        and actual_heldout == expected_heldout
    )
    alternatives_valid = bool(
        [entry["candidate_id"] for entry in contract["alternatives"]]
        == [NULL_ID, CANDIDATE_ID]
    )
    a8a_contract = load_json(checked_input(contract, "a8a_analysis_contract"))
    a8a = load_module(checked_input(contract, "a8a_analyzer"), "a8b_a8a_analyzer")
    a8a.check_freeze(a8a_contract)
    a7b = a8a.load_module(
        a8a.checked_input(a8a_contract, "a7b_analyzer"), "a8b_a7b_analyzer"
    )
    a7b_contract = load_json(a8a.checked_input(a8a_contract, "a7b_contract"))
    common = a8a.load_module(
        a8a.checked_input(a8a_contract, "corpus_common"), "a8b_corpus_common"
    )
    panel = load_json(a8a.checked_input(a8a_contract, "panel"))
    series, parameters, strata, _ghcn = a8a.load_sources(
        a8a_contract, panel, common, a7b
    )
    station_ids = sorted(expected_development | expected_heldout)
    training_period = contract["corpus"]["training_period"]
    validation_period = contract["corpus"]["validation_period"]
    training = {
        station_id: annual_monthly_totals(series[station_id], *training_period)
        for station_id in station_ids
    }
    validation = {
        station_id: annual_monthly_totals(series[station_id], *validation_period)
        for station_id in station_ids
    }
    try:
        shared, standardized = fit_shared_model(training, contract)
    except CandidateInfeasible as failure:
        return infeasible_candidate_outputs(
            contract,
            parent_valid,
            alternatives_valid,
            actual_development,
            actual_heldout,
            training,
            validation,
            failure,
        )
    coefficients = [
        fit_station_budget(
            station_id,
            parameters[station_id],
            shared["basis"],
            contract,
            a7b_contract,
            a7b,
        )
        for station_id in station_ids
    ]
    coefficient_index = {entry["station_id"]: entry for entry in coefficients}
    station_results = []
    for station_id in station_ids:
        metrics = validation_metrics(
            validation[station_id],
            coefficient_index[station_id],
            contract["mechanism"]["shrinkage_to_diagonal"],
        )
        station_results.append(
            {
                "coefficient_feasible": coefficient_index[station_id]["feasible"],
                "role": "development" if station_id in expected_development else "heldout",
                "station_id": station_id,
                "stratum": strata[station_id],
                "validation_metrics": metrics,
            }
        )
    validation_lag = []
    for mode in range(contract["mechanism"]["eof_rank"]):
        left: list[float] = []
        right: list[float] = []
        vector = np.asarray(shared["eigenvectors"])[:, mode]
        for station_id in station_ids:
            normalized = (
                validation[station_id] - standardized[station_id]["center"]
            ) / standardized[station_id]["scale"]
            scores = normalized @ vector
            left.extend(float(value) for value in scores[:-1])
            right.extend(float(value) for value in scores[1:])
        validation_lag.append(spearman(left, right))
    implied_lag = [float(value) for value in shared["implied_state_lag_correlation"]]
    candidate_lag_error = float(np.mean(np.abs(np.asarray(implied_lag) - validation_lag)))
    null_lag_error = float(np.mean(np.abs(validation_lag)))
    null_covariance = [
        entry["validation_metrics"]["null_offdiagonal_correlation_rmse"]
        for entry in station_results
    ]
    candidate_covariance = [
        entry["validation_metrics"]["candidate_offdiagonal_correlation_rmse"]
        for entry in station_results
    ]
    null_annual = [
        entry["validation_metrics"]["null_annual_cross_covariance_error"]
        for entry in station_results
    ]
    candidate_annual = [
        entry["validation_metrics"]["candidate_annual_cross_covariance_error"]
        for entry in station_results
    ]
    covariance_ratio = ratio(float(np.median(candidate_covariance)), float(np.median(null_covariance)))
    annual_ratio = ratio(float(np.median(candidate_annual)), float(np.median(null_annual)))
    null_certified = bool(parent_valid and alternatives_valid)
    candidate_guards = {
        "all_station_budgets_feasible": all(entry["feasible"] for entry in coefficients),
        "annual_covariance_improvement": annual_ratio is not None
        and annual_ratio <= contract["decision"]["pooled_improvement_ratio_max"],
        "cross_month_covariance_improvement": covariance_ratio is not None
        and covariance_ratio <= contract["decision"]["pooled_improvement_ratio_max"],
        "eof_representation": shared["explained_fraction"]
        >= contract["mechanism"]["minimum_eof_explained_fraction"],
        "joint_station_breadth": sum(
            entry["validation_metrics"]["joint_improvement"] for entry in station_results
        )
        >= contract["decision"]["minimum_joint_station_improvements"],
        "minimum_allocated_months": all(
            entry["allocated_month_count"]
            >= contract["mechanism"]["minimum_allocated_months_per_station"]
            for entry in coefficients
        ),
        "persistence_not_degraded": candidate_lag_error <= null_lag_error,
        "station_scale_bounds": all(
            entry["gamma"] >= contract["mechanism"]["minimum_station_scale"]
            for entry in coefficients
        ),
    }
    candidate_eligible = bool(null_certified and all(candidate_guards.values()))
    if not null_certified:
        terminal = contract["decision"]["stop_terminal"]
        selected = None
    elif candidate_eligible:
        terminal = contract["decision"]["candidate_terminal"]
        selected = CANDIDATE_ID
    else:
        terminal = contract["decision"]["null_terminal"]
        selected = NULL_ID
    decision = {
        "analysis_id": contract["analysis_id"],
        "candidate_eligible": candidate_eligible,
        "candidate_guards": candidate_guards,
        "fit_failure": None,
        "null_certified": null_certified,
        "parent_valid": parent_valid,
        "schema_version": 1,
        "selected_alternative": selected,
        "terminal": terminal,
    }
    coefficient_bundle = {
        "analysis_contract_sha256": sha256(
            (ARTIFACTS / "feasibility-contract-v1.json").read_bytes()
        ),
        "candidate_id": CANDIDATE_ID,
        "candidate_eligible": candidate_eligible,
        "coefficient_schema": "a8b_bounded_eof2_reallocation_coefficients_v1",
        "fit_failure": None,
        "fit_status": "FIT-COMPLETE",
        "rng": contract["rng"],
        "schema_version": 1,
        "shared_model": {
            "eigenvalues": shared["eigenvalues"],
            "eof_vectors": shared["eigenvectors"],
            "explained_fraction": shared["explained_fraction"],
            "implied_state_lag_correlation": shared["implied_state_lag_correlation"],
            "latent_gaussian_rho": shared["latent_gaussian_rho"],
        },
        "stations": coefficients,
        "use_authorization": "A8c pilot only if candidate_eligible is true",
    }
    analysis = {
        "analysis_id": contract["analysis_id"],
        "analysis_contract_sha256": sha256(
            (ARTIFACTS / "feasibility-contract-v1.json").read_bytes()
        ),
        "candidate_skill": {
            "candidate_lag_error": candidate_lag_error,
            "candidate_to_null_annual_covariance_error_ratio": annual_ratio,
            "candidate_to_null_offdiagonal_rmse_ratio": covariance_ratio,
            "joint_station_improvement_count": sum(
                entry["validation_metrics"]["joint_improvement"] for entry in station_results
            ),
            "null_lag_error": null_lag_error,
            "validation_score_lag_spearman": validation_lag,
        },
        "execution_counts": {
            "alternatives": 2,
            "fallback_stations": len(station_ids),
            "monthly_budget_cells": 12 * len(station_ids),
            "training_station_years": sum(len(value) for value in training.values()),
            "validation_station_years": sum(len(value) for value in validation.values()),
        },
        "fit_failure": None,
        "parent": {
            "development_fallback_station_ids": sorted(actual_development),
            "heldout_fallback_station_ids": sorted(actual_heldout),
            "terminal": parent_decision["terminal"],
            "valid": parent_valid,
        },
        "pre_analysis_freeze_sha256": sha256(
            (ARTIFACTS / "pre-analysis-freeze-v2.json").read_bytes()
        ),
        "schema_version": 1,
        "shared_fit": {
            "eigenvalues": shared["eigenvalues"],
            "eof_vectors": shared["eigenvectors"],
            "explained_fraction": shared["explained_fraction"],
            "implied_state_lag_correlation": shared["implied_state_lag_correlation"],
            "latent_gaussian_rho": shared["latent_gaussian_rho"],
            "pooled_row_count": shared["pooled_row_count"],
            "training_score_lag_spearman": shared["training_score_lag_spearman"],
        },
        "station_results": station_results,
        "terminal": terminal,
    }
    return clean_json(coefficient_bundle), clean_json(analysis), clean_json(decision)


def render_findings(decision: dict[str, Any], analysis: dict[str, Any]) -> str:
    skill = analysis["candidate_skill"]
    failed = [name for name, passed in decision["candidate_guards"].items() if not passed]
    return "\n".join(
        [
            "# A8b findings",
            "",
            f"Terminal: `{decision['terminal']}`",
            f"Selected alternative: `{decision['selected_alternative']}`",
            "",
            f"Candidate/null off-diagonal RMSE ratio: {skill['candidate_to_null_offdiagonal_rmse_ratio']}",
            f"Candidate/null annual covariance-error ratio: {skill['candidate_to_null_annual_covariance_error_ratio']}",
            f"Joint station improvements: {skill['joint_station_improvement_count']}/10",
            f"Failed candidate guards: {', '.join(failed) if failed else 'none'}",
            "",
            "No climate was generated. Candidate failure selects the registered legacy-only null; it does not authorize repair or another candidate.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--coefficients", type=Path, default=ARTIFACTS / "a8b-coefficients-v1.json"
    )
    parser.add_argument("--analysis", type=Path, default=ARTIFACTS / "a8b-analysis-v1.json")
    parser.add_argument("--decision", type=Path, default=ARTIFACTS / "a8b-decision-v1.json")
    parser.add_argument("--findings", type=Path, default=ARTIFACTS / "findings.md")
    args = parser.parse_args()
    contract = load_json(ARTIFACTS / "feasibility-contract-v1.json")
    check_freeze(contract)
    subprocess.run(
        ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
        cwd=REPO,
        check=True,
    )
    coefficients, analysis, decision = analyze(contract)
    args.coefficients.write_bytes(canonical_json_bytes(coefficients))
    args.analysis.write_bytes(canonical_json_bytes(analysis))
    args.decision.write_bytes(canonical_json_bytes(decision))
    args.findings.write_text(render_findings(decision, analysis), encoding="utf-8")
    print(decision["terminal"])


if __name__ == "__main__":
    main()
