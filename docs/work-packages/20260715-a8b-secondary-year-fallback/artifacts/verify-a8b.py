#!/usr/bin/env python3
"""Independent identity, algebra, decision, and reproduction checks for A8b."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
CANDIDATE_ID = "bounded_eof2_copula_ar1_reallocation_v1"
NULL_ID = "legacy_daily_only_v1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(path)
    return value


def close(left: float, right: float, tolerance: float = 2e-10) -> None:
    if not math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"numeric mismatch: {left} != {right}")


def check_freeze(contract: dict[str, Any]) -> None:
    freeze = load_json(ARTIFACTS / "pre-analysis-freeze-v2.json")
    if freeze["status"] != "FROZEN-BEFORE-A8B-CANDIDATE-FIT":
        raise AssertionError("freeze status mismatch")
    for relative, expected in freeze["frozen_files_sha256"].items():
        if sha256((REPO / relative).read_bytes()) != expected:
            raise AssertionError(f"frozen file mismatch: {relative}")
    for entry in contract["inputs"].values():
        if sha256((REPO / entry["path"]).read_bytes()) != entry["sha256"]:
            raise AssertionError(f"input mismatch: {entry['path']}")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", contract["source_commit"], "HEAD"],
        cwd=REPO,
        check=True,
    )
    if (
        subprocess.run(
            ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
            cwd=REPO,
            check=False,
        ).returncode
        != 0
    ):
        raise AssertionError("production crates changed after source boundary")


def verify() -> None:
    contract = load_json(ARTIFACTS / "feasibility-contract-v1.json")
    coefficients = load_json(ARTIFACTS / "a8b-coefficients-v1.json")
    analysis = load_json(ARTIFACTS / "a8b-analysis-v1.json")
    decision = load_json(ARTIFACTS / "a8b-decision-v1.json")
    check_freeze(contract)
    if [entry["candidate_id"] for entry in contract["alternatives"]] != [
        NULL_ID,
        CANDIDATE_ID,
    ]:
        raise AssertionError("alternative set mismatch")
    expected_development = contract["corpus"]["expected_development_station_ids"]
    expected_heldout = contract["corpus"]["expected_heldout_station_ids"]
    if analysis["parent"]["development_fallback_station_ids"] != expected_development:
        raise AssertionError("development class mismatch")
    if analysis["parent"]["heldout_fallback_station_ids"] != expected_heldout:
        raise AssertionError("heldout class mismatch")
    if not analysis["parent"]["valid"] or not decision["parent_valid"]:
        raise AssertionError("parent authorization mismatch")
    if analysis["pre_analysis_freeze_sha256"] != sha256(
        (ARTIFACTS / "pre-analysis-freeze-v2.json").read_bytes()
    ):
        raise AssertionError("analysis freeze mismatch")
    if analysis["fit_failure"] is not None:
        expected_counts = {
            "alternatives": 2,
            "fallback_stations": 10,
            "monthly_budget_cells": 0,
            "training_station_years": 300,
            "validation_station_years": 160,
        }
        if analysis["execution_counts"] != expected_counts:
            raise AssertionError("infeasible execution cardinality mismatch")
        failure = analysis["fit_failure"]
        if failure["code"] != "zero_training_monthly_scale":
            raise AssertionError("unexpected fit failure")
        if not failure["context"]["months"] or not failure["context"]["station_id"]:
            raise AssertionError("incomplete fit failure context")
        if coefficients["fit_failure"] != failure or decision["fit_failure"] != failure:
            raise AssertionError("fit failure identity mismatch")
        if coefficients["fit_status"] != "INFEASIBLE-BEFORE-COEFFICIENTS":
            raise AssertionError("fit status mismatch")
        if coefficients["shared_model"] is not None or coefficients["stations"]:
            raise AssertionError("infeasible candidate published coefficients")
        if analysis["shared_fit"] is not None or analysis["station_results"]:
            raise AssertionError("infeasible candidate published fit metrics")
        if any(decision["candidate_guards"].values()):
            raise AssertionError("infeasible candidate passed a guard")
        if decision["candidate_eligible"] or coefficients["candidate_eligible"]:
            raise AssertionError("infeasible candidate marked eligible")
        if not decision["null_certified"]:
            raise AssertionError("legacy-only null was not certified")
        if decision["selected_alternative"] != NULL_ID:
            raise AssertionError("legacy-only null not selected")
        if decision["terminal"] != contract["decision"]["null_terminal"]:
            raise AssertionError("infeasible terminal mismatch")
        if analysis["terminal"] != decision["terminal"]:
            raise AssertionError("analysis terminal mismatch")
        if list(PACKAGE.rglob("*.cli")):
            raise AssertionError("A8b generated climate unexpectedly")
        return
    if analysis["execution_counts"] != {
        "alternatives": 2,
        "fallback_stations": 10,
        "monthly_budget_cells": 120,
        "training_station_years": 300,
        "validation_station_years": 160,
    }:
        raise AssertionError("execution cardinality mismatch")
    shared = coefficients["shared_model"]
    vectors = np.asarray(shared["eof_vectors"], dtype=float)
    if vectors.shape != (12, 2):
        raise AssertionError("EOF shape mismatch")
    if np.max(np.abs(vectors.T @ vectors - np.eye(2))) > 2e-12:
        raise AssertionError("EOF vectors not orthonormal")
    if any(abs(value) > contract["mechanism"]["gaussian_copula_rho_absolute_max"] + 1e-12 for value in shared["latent_gaussian_rho"]):
        raise AssertionError("latent AR bound mismatch")
    station_index = {entry["station_id"]: entry for entry in coefficients["stations"]}
    expected_ids = sorted(expected_development + expected_heldout)
    if sorted(station_index) != expected_ids:
        raise AssertionError("coefficient station set mismatch")
    for station_id in expected_ids:
        station = station_index[station_id]
        if len(station["months"]) != 12:
            raise AssertionError("month cardinality mismatch")
        loadings = np.asarray(
            [month["state_loadings_total_mm"] for month in station["months"]],
            dtype=float,
        )
        covariance = loadings @ loadings.T
        if np.max(np.abs(covariance - np.asarray(station["secondary_state_covariance_mm2"]))) > 2e-9:
            raise AssertionError("secondary covariance mismatch")
        allocated = 0
        month_feasible = True
        for month in station["months"]:
            n = month["wet_count_mean"]
            count_variance = month["wet_count_variance"]
            mean = month["legacy_wet_amount_mean_mm"]
            residual_variance = month["residual_wet_amount_sd_mm"] ** 2
            state_variance = month["state_variance_mm2"]
            if month["active"] and state_variance > contract["numeric"]["absolute_zero_tolerance"]:
                allocated += 1
                reconstructed = (
                    n * residual_variance
                    + count_variance * (mean**2 + state_variance / n**2)
                    + state_variance
                )
                close(reconstructed, month["legacy_monthly_variance_mm2"], 2e-9)
                if month["residual_variance_retention"] < contract["mechanism"]["residual_variance_retention_min"] - 1e-12:
                    month_feasible = False
                if month["minimum_wet_amount_mean_fraction"] < contract["mechanism"]["minimum_wet_amount_mean_fraction"] - 1e-12:
                    month_feasible = False
            else:
                if abs(state_variance) > contract["numeric"]["absolute_zero_tolerance"]:
                    raise AssertionError("inactive month has state variance")
            close(month["candidate_monthly_mean_mm"], month["legacy_monthly_mean_mm"])
            close(month["wet_fraction_error"], 0.0)
            if bool(month["feasible"]) != (not month["infeasibility_reasons"]):
                raise AssertionError("month disposition mismatch")
            month_feasible &= bool(month["feasible"])
        if allocated != station["allocated_month_count"]:
            raise AssertionError("allocated month count mismatch")
        reasons = []
        if station["gamma"] < contract["mechanism"]["minimum_station_scale"]:
            reasons.append("station_scale_below_minimum")
        if allocated < contract["mechanism"]["minimum_allocated_months_per_station"]:
            reasons.append("insufficient_allocated_months")
        if not month_feasible:
            reasons.append("monthly_budget_failure")
        if reasons != station["infeasibility_reasons"]:
            raise AssertionError("station disposition reasons mismatch")
        if station["feasible"] != (not reasons):
            raise AssertionError("station feasibility mismatch")
    results = analysis["station_results"]
    if sorted(entry["station_id"] for entry in results) != expected_ids:
        raise AssertionError("analysis station set mismatch")
    covariance_ratio = analysis["candidate_skill"]["candidate_to_null_offdiagonal_rmse_ratio"]
    annual_ratio = analysis["candidate_skill"]["candidate_to_null_annual_covariance_error_ratio"]
    guards = {
        "all_station_budgets_feasible": all(entry["feasible"] for entry in coefficients["stations"]),
        "annual_covariance_improvement": annual_ratio is not None
        and annual_ratio <= contract["decision"]["pooled_improvement_ratio_max"],
        "cross_month_covariance_improvement": covariance_ratio is not None
        and covariance_ratio <= contract["decision"]["pooled_improvement_ratio_max"],
        "eof_representation": shared["explained_fraction"]
        >= contract["mechanism"]["minimum_eof_explained_fraction"],
        "joint_station_breadth": analysis["candidate_skill"]["joint_station_improvement_count"]
        >= contract["decision"]["minimum_joint_station_improvements"],
        "minimum_allocated_months": all(
            entry["allocated_month_count"]
            >= contract["mechanism"]["minimum_allocated_months_per_station"]
            for entry in coefficients["stations"]
        ),
        "persistence_not_degraded": analysis["candidate_skill"]["candidate_lag_error"]
        <= analysis["candidate_skill"]["null_lag_error"],
        "station_scale_bounds": all(
            entry["gamma"] >= contract["mechanism"]["minimum_station_scale"]
            for entry in coefficients["stations"]
        ),
    }
    if guards != decision["candidate_guards"]:
        raise AssertionError("candidate guard mismatch")
    eligible = bool(decision["null_certified"] and all(guards.values()))
    if eligible != decision["candidate_eligible"] or eligible != coefficients["candidate_eligible"]:
        raise AssertionError("candidate eligibility mismatch")
    if not decision["null_certified"]:
        terminal = contract["decision"]["stop_terminal"]
        selected = None
    elif eligible:
        terminal = contract["decision"]["candidate_terminal"]
        selected = CANDIDATE_ID
    else:
        terminal = contract["decision"]["null_terminal"]
        selected = NULL_ID
    if decision["terminal"] != terminal or analysis["terminal"] != terminal:
        raise AssertionError("terminal mismatch")
    if decision["selected_alternative"] != selected:
        raise AssertionError("selected alternative mismatch")
    if list(PACKAGE.rglob("*.cli")):
        raise AssertionError("A8b generated climate unexpectedly")


def reproduce() -> None:
    with tempfile.TemporaryDirectory(prefix="a8b-reproduce-") as temporary:
        root = Path(temporary)
        generated = {
            "coefficients": root / "coefficients.json",
            "analysis": root / "analysis.json",
            "decision": root / "decision.json",
            "findings": root / "findings.md",
        }
        subprocess.run(
            [
                sys.executable,
                str(ARTIFACTS / "analyze-a8b.py"),
                "--coefficients",
                str(generated["coefficients"]),
                "--analysis",
                str(generated["analysis"]),
                "--decision",
                str(generated["decision"]),
                "--findings",
                str(generated["findings"]),
            ],
            cwd=REPO,
            check=True,
        )
        canonical = {
            "coefficients": ARTIFACTS / "a8b-coefficients-v1.json",
            "analysis": ARTIFACTS / "a8b-analysis-v1.json",
            "decision": ARTIFACTS / "a8b-decision-v1.json",
            "findings": ARTIFACTS / "findings.md",
        }
        for name in generated:
            if generated[name].read_bytes() != canonical[name].read_bytes():
                raise AssertionError(f"non-reproducible {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    verify()
    if args.reproduce:
        reproduce()
    print("A8b independent verification: PASS")


if __name__ == "__main__":
    main()
