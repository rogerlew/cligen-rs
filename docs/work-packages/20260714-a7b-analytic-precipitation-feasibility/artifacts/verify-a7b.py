#!/usr/bin/env python3
"""Independent invariant and reproduction verifier for A7b."""

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
from scipy.special import ndtr

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
DEFAULT_REPO = PACKAGE.parents[2]


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
        raise AssertionError(f"expected object: {path}")
    return value


def close(left: float, right: float, tolerance: float = 2e-10) -> None:
    if not math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"numeric mismatch: {left!r} != {right!r}")


def mask_for(candidate_id: str) -> np.ndarray:
    if candidate_id.startswith("o2_"):
        return np.asarray([0.0, 1.0, 0.0, 1.0])
    if candidate_id.startswith("sm2_"):
        return np.asarray([0.0, 0.0, 1.0, 1.0])
    raise AssertionError(candidate_id)


def stationary(matrix: np.ndarray) -> np.ndarray:
    system = matrix.T - np.eye(len(matrix))
    system[-1, :] = 1.0
    target = np.zeros(len(matrix))
    target[-1] = 1.0
    return np.linalg.solve(system, target)


def occurrence(
    matrix: np.ndarray, pi: np.ndarray, mask: np.ndarray, days: int
) -> tuple[float, list[float]]:
    mu = float(pi @ mask)
    power = np.eye(len(matrix))
    restricted = matrix * mask[np.newaxis, :]
    all_vector = pi * mask
    variance = days * mu * (1.0 - mu)
    all_wet: list[float] = []
    for lag in range(1, days):
        power = power @ matrix
        endpoint = float((pi * mask) @ power @ mask)
        variance += 2.0 * (days - lag) * (endpoint - mu * mu)
        all_vector = all_vector @ restricted
        all_wet.append(float(np.sum(all_vector)))
    return float(variance), all_wet


def baseline_variance(pww: float, pwd: float, days: int) -> tuple[float, float]:
    matrix = np.asarray([[1.0 - pwd, pwd], [1.0 - pww, pww]])
    pi = stationary(matrix)
    variance, _ = occurrence(matrix, pi, np.asarray([0.0, 1.0]), days)
    return variance, float(pi[1])


class AmountCheck:
    def __init__(self, fit: dict[str, Any], contract: dict[str, Any]) -> None:
        self.probabilities = np.asarray(
            contract["amount_model"]["quantile_probabilities"], dtype=float
        )
        self.log_knots = np.log(np.asarray(fit["log_quantile_knots_mm"], dtype=float))
        nodes, weights = np.polynomial.legendre.leggauss(
            contract["numeric_rules"]["gauss_legendre_order"]
        )
        self.u = (nodes + 1.0) / 2.0
        self.weights = weights / 2.0
        nodes, weights = np.polynomial.hermite.hermgauss(
            contract["numeric_rules"]["gauss_hermite_order"]
        )
        normals = math.sqrt(2.0) * nodes
        self.z1 = normals[:, None]
        self.eps = normals[None, :]
        self.pair_weights = (weights[:, None] * weights[None, :]) / math.pi
        self.rho = float(fit["gaussian_copula_rho"])

    def q(self, u: np.ndarray | float, dispersion: float) -> np.ndarray:
        quadrature_z = np.interp(self.u, self.probabilities, self.log_knots)
        shift = float(np.max(dispersion * quadrature_z))
        normalizer = float(
            np.sum(self.weights * np.exp(dispersion * quadrature_z - shift))
        )
        z = np.interp(u, self.probabilities, self.log_knots)
        return np.exp(dispersion * z - shift) / normalizer

    def cv2(self, dispersion: float) -> float:
        values = self.q(self.u, dispersion)
        return max(0.0, float(np.sum(self.weights * values * values) - 1.0))

    def covariance(self, dispersion: float, correlation: float) -> float:
        if dispersion == 0.0 or correlation == 0.0:
            return 0.0
        z2 = correlation * self.z1 + math.sqrt(
            max(0.0, 1.0 - correlation * correlation)
        ) * self.eps
        return float(
            np.sum(
                self.pair_weights
                * self.q(ndtr(self.z1), dispersion)
                * self.q(ndtr(z2), dispersion)
            )
            - 1.0
        )

    def total(
        self,
        dispersion: float,
        wet_count_variance: float,
        mu: float,
        all_wet: list[float],
        days: int,
    ) -> float:
        value = wet_count_variance + days * mu * self.cv2(dispersion)
        for lag, probability in enumerate(all_wet, 1):
            value += (
                2.0
                * (days - lag)
                * probability
                * self.covariance(dispersion, self.rho**lag)
            )
        return float(value)


def median(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def compare_optional(left: float | None, right: float | None) -> None:
    if left is None or right is None:
        if left is not right:
            raise AssertionError("optional numeric mismatch")
    else:
        close(left, right)


def check_freeze(repo: Path, contract: dict[str, Any]) -> dict[str, Any]:
    freeze = load_json(ARTIFACTS / "pre-analysis-freeze-v1.json")
    if freeze["freeze_status"] != "FROZEN-BEFORE-A7B-OUTCOME":
        raise AssertionError("invalid freeze status")
    if freeze["source_commit"] != contract["source_commit"]:
        raise AssertionError("source commit mismatch")
    for relative, expected in freeze["frozen_files_sha256"].items():
        if sha256((repo / relative).read_bytes()) != expected:
            raise AssertionError(f"frozen source mismatch: {relative}")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", contract["source_commit"], "HEAD"],
        cwd=repo,
        check=True,
    )
    if (
        subprocess.run(
            ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
            cwd=repo,
            check=False,
        ).returncode
        != 0
    ):
        raise AssertionError("production crates changed after source freeze")
    for entry in contract["inputs"].values():
        if sha256((repo / entry["path"]).read_bytes()) != entry["sha256"]:
            raise AssertionError(f"parent input mismatch: {entry['path']}")
    return freeze


def verify(repo: Path) -> None:
    contract = load_json(ARTIFACTS / "feasibility-contract-v1.json")
    analysis = load_json(ARTIFACTS / "a7b-analysis-v1.json")
    decision = load_json(ARTIFACTS / "a7b-decision-v1.json")
    check_freeze(repo, contract)
    if decision["decision_contract_sha256"] != sha256(canonical_json_bytes(contract)):
        raise AssertionError("decision contract identity mismatch")
    expected_counts = {
        "amount_station_season_fits": 68,
        "candidate_station_month_cells": 408,
        "occurrence_candidate_station_season_fits": 136,
        "stations": 17,
    }
    if analysis["execution_counts"] != expected_counts:
        raise AssertionError(f"execution count mismatch: {analysis['execution_counts']}")
    if len(analysis["amount_fits"]) != 68 or len(analysis["occurrence_fits"]) != 136:
        raise AssertionError("fit cardinality mismatch")
    if len(analysis["cells"]) != 408 or len(analysis["occurrence_likelihoods"]) != 34:
        raise AssertionError("analysis cardinality mismatch")
    if analysis["rng_ownership_certification"] != {
        **contract["rng_ownership"],
        "status": "STATIC-CONTRACT-SATISFIED",
    }:
        raise AssertionError("RNG ownership contract mismatch")

    amount_fits = {
        (fit["station_id"], fit["season"]): fit for fit in analysis["amount_fits"]
    }
    tolerance = contract["numeric_rules"][
        "stationary_wet_fraction_absolute_tolerance"
    ]
    guard = contract["numeric_rules"]["minimum_probability"]
    for cell in analysis["cells"]:
        matrix = np.asarray(cell["kernel"]["transition_matrix"], dtype=float)
        pi = np.asarray(cell["kernel"]["stationary_distribution"], dtype=float)
        probabilities = np.asarray(cell["kernel"]["probabilities"], dtype=float)
        mask = mask_for(cell["candidate_id"])
        if np.max(np.abs(np.sum(matrix, axis=1) - 1.0)) > 2e-12:
            raise AssertionError("transition row does not sum to one")
        if np.max(np.abs(pi @ matrix - pi)) > 2e-10:
            raise AssertionError("stored distribution is not stationary")
        target_mu = cell["legacy"]["stationary_wet_fraction"]
        close(float(pi @ mask), target_mu, tolerance)
        close(cell["kernel"]["stationary_wet_fraction"], target_mu, tolerance)
        probability_violation = bool(
            np.min(probabilities) < guard or np.max(probabilities) > 1.0 - guard
        )
        if probability_violation != ("probability_guard" in cell["infeasibility_reasons"]):
            raise AssertionError("probability guard disposition mismatch")
        if not cell["feasible"]:
            if not cell["infeasibility_reasons"]:
                raise AssertionError("infeasible cell lacks reason")
            continue
        if cell["infeasibility_reasons"]:
            raise AssertionError("feasible cell has reasons")
        days = cell["days"]
        wet_count_variance, all_wet = occurrence(matrix, pi, mask, days)
        close(
            wet_count_variance,
            cell["occurrence_moments"]["candidate_wet_count_variance"],
        )
        legacy_wet_count, baseline_mu = baseline_variance(
            cell["legacy"]["pww"], cell["legacy"]["pwd"], days
        )
        close(baseline_mu, target_mu)
        close(
            legacy_wet_count,
            cell["occurrence_moments"]["legacy_wet_count_variance"],
        )
        shape = AmountCheck(amount_fits[(cell["station_id"], cell["season"])], contract)
        budget = cell["budget"]
        cv2_legacy = (cell["legacy"]["wet_sd_mm"] / cell["legacy"]["wet_mean_mm"]) ** 2
        close(shape.cv2(budget["legacy_dispersion"]), cv2_legacy)
        target = legacy_wet_count + days * baseline_mu * cv2_legacy
        close(target, budget["legacy_target_dimensionless_variance"])
        achieved = shape.total(
            budget["budget_dispersion"],
            wet_count_variance,
            target_mu,
            all_wet,
            days,
        )
        close(achieved, budget["achieved_dimensionless_variance"], 2e-9)
        relative_error = abs(achieved - target) / max(1.0, abs(target))
        close(relative_error, budget["monthly_variance_relative_error"], 2e-9)
        if relative_error > contract["numeric_rules"]["budget_relative_tolerance"]:
            raise AssertionError("feasible cell exceeds variance-budget tolerance")
        retention = shape.cv2(budget["budget_dispersion"]) / cv2_legacy
        close(retention, budget["wet_amount_variance_retention"], 2e-9)
        if retention < contract["numeric_rules"]["minimum_wet_amount_variance_retention"]:
            raise AssertionError("feasible cell violates variance-retention gate")
        if budget["budget_dispersion"] > budget["legacy_dispersion"] + 1e-12:
            raise AssertionError("feasible cell increases amount dispersion")
        errors = []
        for probability, key in ((0.95, "p95"), (0.99, "p99")):
            error = abs(
                math.log(
                    float(shape.q(probability, budget["budget_dispersion"]))
                    / float(shape.q(probability, 1.0))
                )
            )
            close(error, budget["tail_log_errors"][key], 2e-9)
            errors.append(error)
        close(max(errors), budget["tail_log_error_max"], 2e-9)

    summaries: list[dict[str, Any]] = []
    development = set(contract["comparison"]["development_stations"])
    for candidate in contract["candidates"]:
        candidate_id = candidate["candidate_id"]
        cells = [cell for cell in analysis["cells"] if cell["candidate_id"] == candidate_id]
        feasible = [cell for cell in cells if cell["feasible"]]
        reasons: dict[str, int] = {}
        for cell in cells:
            for reason in cell["infeasibility_reasons"]:
                reasons[reason] = reasons.get(reason, 0) + 1
        likelihoods = [
            entry["improvement"]
            for entry in analysis["occurrence_likelihoods"]
            if entry["candidate_id"] == candidate_id
        ]
        summary = {
            "candidate_id": candidate_id,
            "corpus_feasible_cells": len(feasible),
            "development_feasible_cells": sum(
                cell["feasible"] and cell["station_id"] in development for cell in cells
            ),
            "infeasibility_reason_counts": reasons,
            "median_station_occurrence_log_loss_improvement": median(likelihoods),
            "median_tail_log_error": median(
                [cell["budget"]["tail_log_error_max"] for cell in feasible]
            ),
            "median_wet_amount_variance_retention": median(
                [cell["budget"]["wet_amount_variance_retention"] for cell in feasible]
            ),
            "total_cells": len(cells),
        }
        summary["qualifies"] = bool(
            summary["development_feasible_cells"]
            == contract["decision"]["development_feasible_cells_required"]
            and summary["corpus_feasible_cells"]
            >= contract["decision"]["corpus_feasible_cells_min"]
        )
        summaries.append(summary)
    for recomputed, stored in zip(summaries, decision["candidate_summaries"]):
        for key in (
            "candidate_id",
            "corpus_feasible_cells",
            "development_feasible_cells",
            "infeasibility_reason_counts",
            "qualifies",
            "total_cells",
        ):
            if recomputed[key] != stored[key]:
                raise AssertionError(f"summary mismatch: {key}")
        for key in (
            "median_station_occurrence_log_loss_improvement",
            "median_tail_log_error",
            "median_wet_amount_variance_retention",
        ):
            compare_optional(recomputed[key], stored[key])
    if summaries != analysis["candidate_summaries"]:
        raise AssertionError("analysis/decision summaries differ")

    def rank_key(summary: dict[str, Any]) -> tuple[Any, ...]:
        improvement = summary["median_station_occurrence_log_loss_improvement"]
        retention = summary["median_wet_amount_variance_retention"]
        return (
            -summary["development_feasible_cells"],
            -summary["corpus_feasible_cells"],
            -(improvement if improvement is not None else -math.inf),
            -(retention if retention is not None else -math.inf),
            summary["median_tail_log_error"]
            if summary["median_tail_log_error"] is not None
            else math.inf,
            summary["candidate_id"],
        )

    ranked = sorted(summaries, key=rank_key)
    if decision["ranking"] != [summary["candidate_id"] for summary in ranked]:
        raise AssertionError("ranking mismatch")
    qualifying = [summary for summary in ranked if summary["qualifies"]]
    selected = qualifying[0]["candidate_id"] if qualifying else None
    terminal = contract["decision"]["no_candidate_terminal"]
    if selected is not None:
        terminal = next(
            candidate["terminal"]
            for candidate in contract["candidates"]
            if candidate["candidate_id"] == selected
        )
    if decision["selected_candidate"] != selected or decision["terminal"] != terminal:
        raise AssertionError("terminal selection mismatch")
    if analysis["terminal"] != terminal:
        raise AssertionError("analysis terminal mismatch")


def reproduce(repo: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="a7b-reproduce-") as temporary:
        root = Path(temporary)
        output = root / "analysis.json"
        decision = root / "decision.json"
        findings = root / "findings.md"
        subprocess.run(
            [
                sys.executable,
                str(ARTIFACTS / "analyze-a7b.py"),
                "--repo",
                str(repo),
                "--output",
                str(output),
                "--decision",
                str(decision),
                "--findings",
                str(findings),
            ],
            cwd=repo,
            check=True,
        )
        for generated, canonical in (
            (output, ARTIFACTS / "a7b-analysis-v1.json"),
            (decision, ARTIFACTS / "a7b-decision-v1.json"),
            (findings, ARTIFACTS / "findings.md"),
        ):
            if generated.read_bytes() != canonical.read_bytes():
                raise AssertionError(f"non-reproducible artifact: {canonical.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    verify(repo)
    if args.reproduce:
        reproduce(repo)
    print("A7b independent verification: PASS")


if __name__ == "__main__":
    main()
