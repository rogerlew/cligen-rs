#!/usr/bin/env python3
"""Exercise corrected acceptance of independently valid time-limit incumbents."""

from __future__ import annotations

import importlib.util
import sys
from types import SimpleNamespace

import numpy as np
from scipy.optimize import Bounds, LinearConstraint

from a5d1b_common import ARTIFACTS, write_json


RESULTS = ARTIFACTS / "incumbent-acceptance-fixture-results-v1.json"
SOLVER_PATH = ARTIFACTS / "solve-count-feasibility.py"


def load_solver():
    spec = importlib.util.spec_from_file_location("a5d1b_fixture_solver", SOLVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import corrected count solver")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def result(values):
    return SimpleNamespace(
        success=False,
        status=1,
        message="synthetic time limit",
        fun=1.0 if values is not None else None,
        mip_gap=0.25 if values is not None else None,
        mip_node_count=3 if values is not None else None,
        x=None if values is None else np.asarray(values, dtype=np.float64),
    )


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: run-incumbent-acceptance-fixtures.py")
    solver = load_solver()
    model = {
        "objective": np.zeros(2),
        "integrality": np.asarray([1, 0], dtype=np.uint8),
        "bounds": Bounds([0.0, 0.0], [2.0, 1.0]),
        "constraints": LinearConstraint([[1.0, 1.0]], [1.0], [2.0]),
    }
    cases = []

    def add(fixture_id: str, candidate, expected: bool) -> None:
        accepted, replay = solver.validated_incumbent(result(candidate), model)
        passed = (accepted is not None) == expected
        cases.append(
            {
                "fixture_id": fixture_id,
                "expected_acceptance": expected,
                "observed_acceptance": accepted is not None,
                "replay": replay,
                "pass": passed,
            }
        )

    add("status1_valid_integral_incumbent", [1.0, 0.25], True)
    add("status1_fractional_integer_variable", [1.5, 0.25], False)
    add("status1_primal_constraint_violation", [0.0, 0.25], False)
    add("status1_no_incumbent", None, False)
    value = {
        "incumbent_acceptance_fixture_results_schema_version": 1,
        "development_only": True,
        "expected_count": 4,
        "actual_count": len(cases),
        "pass_count": sum(row["pass"] for row in cases),
        "records": cases,
    }
    if value["pass_count"] != value["expected_count"]:
        raise ValueError("incumbent acceptance fixture failed")
    write_json(RESULTS, value)
    print("A5d1b incumbent acceptance fixtures: 4/4 pass")


if __name__ == "__main__":
    main()
