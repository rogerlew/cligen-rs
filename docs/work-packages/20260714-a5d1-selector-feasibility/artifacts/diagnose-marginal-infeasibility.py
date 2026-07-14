#!/usr/bin/env python3
"""Post-result phase-I diagnosis for frozen A5d1 infeasible marginal LPs.

This tool does not alter, refit, or reclassify the frozen solve. It minimizes
normalized constraint slacks solely to name the preservation conflicts behind
an already-recorded HiGHS infeasible status.
"""

from __future__ import annotations

import importlib.util
import sys

import numpy as np
from scipy.optimize import linprog

from a5d1_common import (
    CONTRACT,
    FEATURE_DIR,
    MARGINAL_RESULTS,
    MONTH_NAMES,
    PACKAGE,
    freeze_identity,
    load_json,
    write_json,
)
OUTPUT = PACKAGE / "marginal-infeasibility-diagnostics-v1.json"
SOLVER = PACKAGE / "solve-selector-feasibility.py"
SPEC = importlib.util.spec_from_file_location("a5d1_solver", SOLVER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load frozen marginal solver")
SOLVER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOLVER_MODULE)
build_problem = SOLVER_MODULE.build_problem


def labels() -> list[str]:
    result = []
    for month in MONTH_NAMES:
        for name in (
            "fitted.wet_fraction",
            "fitted.wet_mean",
            "fitted.wet_raw_second",
            "fitted.wet_given_dry",
            "fitted.wet_given_wet",
            "fitted.tmax_mean",
            "fitted.tmax_raw_second",
            "fitted.tmin_mean",
            "fitted.tmin_raw_second",
        ):
            result.extend((f"{month}.{name}.upper", f"{month}.{name}.lower"))
        for name in ("bin_0_1", "bin_1_5", "bin_5_20", "bin_20_inf"):
            result.extend((f"{month}.uniform.{name}.upper", f"{month}.uniform.{name}.lower"))
        for name in ("p_tmax", "p_tmin", "tmax_tmin"):
            result.extend((f"{month}.uniform.{name}.upper", f"{month}.uniform.{name}.lower"))
        for descriptor in ("duration", "time_to_peak", "peak_ratio"):
            for moment in ("first", "second"):
                result.extend(
                    (
                        f"{month}.uniform.{descriptor}.{moment}.upper",
                        f"{month}.uniform.{descriptor}.{moment}.lower",
                    )
                )
    for name in ("precip_mean", "tmax_mean", "tmin_mean"):
        result.extend((f"annual.uniform.{name}.upper", f"annual.uniform.{name}.lower"))
    for name in (
        "precip_second", "tmax_second", "tmin_second",
        "precip_tmax_cross", "precip_tmin_cross", "tmax_tmin_cross",
    ):
        result.extend(
            (
                f"annual.daymet.{name}.absolute_positive",
                f"annual.daymet.{name}.absolute_negative",
                f"annual.daymet.{name}.noninferior_positive",
                f"annual.daymet.{name}.noninferior_negative",
            )
        )
    return result


def diagnose(station_id: str, pool_size: int, contract: dict) -> dict:
    feature = load_json(FEATURE_DIR / f"{station_id}-year-features-v1.json")
    problem = build_problem(feature["blocks"][:pool_size], feature["targets"], contract)
    names = labels()
    if len(names) != problem["a_ub"].shape[0]:
        raise ValueError(f"constraint label mismatch: {len(names)} != {problem['a_ub'].shape[0]}")
    row_scale = np.maximum(
        1.0,
        np.maximum(np.abs(problem["b_ub"]), np.max(np.abs(problem["a_ub"]), axis=1)),
    )
    count = len(names)
    a_phase = np.hstack((problem["a_ub"], -np.diag(row_scale)))
    a_eq = np.hstack((problem["a_eq"], np.zeros((problem["a_eq"].shape[0], count))))
    objective = np.concatenate((np.zeros(problem["a_ub"].shape[1]), np.ones(count)))
    bounds = problem["bounds"] + [(0.0, None)] * count
    result = linprog(
        objective,
        A_ub=a_phase,
        b_ub=problem["b_ub"],
        A_eq=a_eq,
        b_eq=problem["b_eq"],
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"phase-I diagnosis failed: {station_id}/{pool_size}: {result.message}")
    normalized = result.x[-count:]
    ranked = sorted(
        (
            {
                "constraint": names[index],
                "normalized_slack": float(value),
                "native_slack": float(value * row_scale[index]),
            }
            for index, value in enumerate(normalized)
            if value > 1.0e-9
        ),
        key=lambda row: (-row["normalized_slack"], row["constraint"]),
    )
    group_tests = {}
    selectors = {
        "preservation_without_daymet_annual": lambda name: not name.startswith("annual.daymet."),
        "fitted_monthly_only": lambda name: ".fitted." in name,
        "uniform_preservation_only": lambda name: ".uniform." in name or name.startswith("annual.uniform."),
        "fitted_monthly_plus_daymet_annual": lambda name: ".uniform." not in name and not name.startswith("annual.uniform."),
        "uniform_preservation_plus_daymet_annual": lambda name: ".fitted." not in name,
        "daymet_annual_only": lambda name: name.startswith("annual.daymet."),
    }
    for group, selector in selectors.items():
        selected = [index for index, name in enumerate(names) if selector(name)]
        group_result = linprog(
            problem["objective"],
            A_ub=problem["a_ub"][selected],
            b_ub=problem["b_ub"][selected],
            A_eq=problem["a_eq"],
            b_eq=problem["b_eq"],
            bounds=problem["bounds"],
            method="highs",
        )
        group_tests[group] = {
            "constraint_count": len(selected),
            "feasible": bool(group_result.success),
            "status": int(group_result.status),
        }
    return {
        "station_id": station_id,
        "pool_size": pool_size,
        "phase_one_status": "optimal",
        "minimum_normalized_total_slack": float(result.fun),
        "violated_constraint_count": len(ranked),
        "first_failed_constraint": ranked[0]["constraint"] if ranked else None,
        "largest_conflicts": ranked[:10],
        "constraint_group_ablation": group_tests,
        "interpretation": "Diagnostic only; no frozen tolerance, outcome, or decision was changed.",
    }


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: diagnose-marginal-infeasibility.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    marginal = load_json(MARGINAL_RESULTS)
    records = [
        diagnose(row["station_id"], row["pool_size"], contract)
        for row in marginal["records"]
        if row["first_failed_criterion"] == "solver_status"
    ]
    value = {
        "marginal_infeasibility_diagnostics_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "frozen_results_unchanged": True,
        "record_count": len(records),
        "records": records,
    }
    write_json(OUTPUT, value)
    print(f"A5d1 marginal phase-I diagnostics: PASS ({len(records)} infeasible cells)")


if __name__ == "__main__":
    main()
