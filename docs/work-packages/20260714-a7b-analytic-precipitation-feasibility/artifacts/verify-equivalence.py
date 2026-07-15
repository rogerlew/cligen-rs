#!/usr/bin/env python3
"""Reproduce the post-analysis A7b occurrence-parameterization review."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

ARTIFACTS = Path(__file__).resolve().parent
O2 = "o2_logqspline_gaussian_copula_v1"
SM2 = "sm2_logqspline_gaussian_copula_v1"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(path)
    return value


def main() -> None:
    analysis = load_json(ARTIFACTS / "a7b-analysis-v1.json")
    decision = load_json(ARTIFACTS / "a7b-decision-v1.json")
    cells = {
        (cell["candidate_id"], cell["station_id"], cell["month"]): cell
        for cell in analysis["cells"]
    }
    stations = sorted({cell["station_id"] for cell in analysis["cells"]})
    # SM2 order D1,D2+,W1,W2+ equals O2 order WD,DD,DW,WW.
    permutation = [2, 0, 1, 3]
    maximum_transition = 0.0
    maximum_stationary = 0.0
    maximum_probability = 0.0
    maximum_wet_count_variance = 0.0
    maximum_achieved_budget = 0.0
    for station_id in stations:
        for month in range(1, 13):
            o2 = cells[(O2, station_id, month)]
            sm2 = cells[(SM2, station_id, month)]
            if o2["feasible"] != sm2["feasible"]:
                raise AssertionError("paired feasibility differs")
            if o2["infeasibility_reasons"] != sm2["infeasibility_reasons"]:
                mapped_o2 = [reason.replace("WW", "W2+") for reason in o2["infeasibility_reasons"]]
                if mapped_o2 != sm2["infeasibility_reasons"]:
                    raise AssertionError("paired infeasibility reason differs")
            o2_transition = np.asarray(o2["kernel"]["transition_matrix"])
            sm2_transition = np.asarray(sm2["kernel"]["transition_matrix"])
            maximum_transition = max(
                maximum_transition,
                float(
                    np.max(
                        np.abs(
                            o2_transition[np.ix_(permutation, permutation)]
                            - sm2_transition
                        )
                    )
                ),
            )
            o2_stationary = np.asarray(o2["kernel"]["stationary_distribution"])
            sm2_stationary = np.asarray(sm2["kernel"]["stationary_distribution"])
            maximum_stationary = max(
                maximum_stationary,
                float(np.max(np.abs(o2_stationary[permutation] - sm2_stationary))),
            )
            q = np.asarray(o2["kernel"]["probabilities"])
            continuation = np.asarray(sm2["kernel"]["probabilities"])
            expected = np.asarray([1.0 - q[2], 1.0 - q[0], q[1], q[3]])
            maximum_probability = max(
                maximum_probability, float(np.max(np.abs(expected - continuation)))
            )
            if "occurrence_moments" in o2 and "occurrence_moments" in sm2:
                maximum_wet_count_variance = max(
                    maximum_wet_count_variance,
                    abs(
                        o2["occurrence_moments"]["candidate_wet_count_variance"]
                        - sm2["occurrence_moments"]["candidate_wet_count_variance"]
                    ),
                )
            if o2["feasible"]:
                maximum_achieved_budget = max(
                    maximum_achieved_budget,
                    abs(
                        o2["budget"]["achieved_dimensionless_variance"]
                        - sm2["budget"]["achieved_dimensionless_variance"]
                    ),
                )
    expected_values = {
        "transition": 0.0012456961202288452,
        "stationary": 0.0000978425282837786,
        "probability": 0.0012456961202288452,
        "wet_count": 0.00679471490979644,
        "budget": 6.394884621840902e-14,
    }
    actual_values = {
        "transition": maximum_transition,
        "stationary": maximum_stationary,
        "probability": maximum_probability,
        "wet_count": maximum_wet_count_variance,
        "budget": maximum_achieved_budget,
    }
    for key, expected in expected_values.items():
        if not math.isclose(actual_values[key], expected, rel_tol=1e-12, abs_tol=1e-15):
            raise AssertionError(f"{key}: {actual_values[key]} != {expected}")
    summaries = {entry["candidate_id"]: entry for entry in decision["candidate_summaries"]}
    for candidate_id in (O2, SM2):
        if summaries[candidate_id]["corpus_feasible_cells"] != 192:
            raise AssertionError("unexpected corpus feasibility")
        if summaries[candidate_id]["development_feasible_cells"] != 31:
            raise AssertionError("unexpected development feasibility")
    likelihoods = {
        (entry["candidate_id"], entry["station_id"]): entry
        for entry in analysis["occurrence_likelihoods"]
    }
    for station_id in stations:
        if (
            likelihoods[(SM2, station_id)]["evaluated_days"]
            - likelihoods[(O2, station_id)]["evaluated_days"]
            != 1
        ):
            raise AssertionError("likelihood support difference is not one day")
    if decision["selected_candidate"] is not None:
        raise AssertionError("equivalence review expected no selected candidate")
    print("A7b occurrence-parameterization equivalence review: PASS")


if __name__ == "__main__":
    main()
