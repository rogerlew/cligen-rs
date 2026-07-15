#!/usr/bin/env python3
"""Run outcome-independent synthetic A5d1b conformance fixtures."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from a5d1b_common import (
    ARTIFACTS,
    ANNUAL_COMPONENTS,
    MONTH_NAMES,
    count_only_replay,
    is_leap,
    load_json,
    reject_duplicate_keys,
    reject_nonfinite,
    validate_counts,
    write_json,
)
FIXTURES = ARTIFACTS / "synthetic-fixtures-v1.json"
RESULTS = ARTIFACTS / "synthetic-fixture-results-v1.json"


ORDER_SPEC = importlib.util.spec_from_file_location(
    "a5d1b_synthetic_order", ARTIFACTS / "construct-ordered-paths.py"
)
if ORDER_SPEC is None or ORDER_SPEC.loader is None:
    raise RuntimeError("cannot import frozen ordering tool")
ORDER_TOOL = importlib.util.module_from_spec(ORDER_SPEC)
ORDER_SPEC.loader.exec_module(ORDER_TOOL)


def rejected_json(text: str) -> bool:
    try:
        json.loads(text, parse_constant=reject_nonfinite, object_pairs_hook=reject_duplicate_keys, parse_float=lambda token: (_ for _ in ()).throw(ValueError("overflow")) if not np.isfinite(float(token)) else float(token))
    except ValueError:
        return True
    return False


def synthetic_blocks() -> list[dict]:
    annual = {
        "precip_total_mm": 1.0,
        "tmax_mean_c": 2.0,
        "tmin_mean_c": 1.0,
        "precip_total_mm.raw_second_moment": 1.0,
        "tmax_mean_c.raw_second_moment": 4.0,
        "tmin_mean_c.raw_second_moment": 1.0,
        "precip_total_mm_x_tmax_mean_c.raw_cross_moment": 2.0,
        "precip_total_mm_x_tmin_mean_c.raw_cross_moment": 1.0,
        "tmax_mean_c_x_tmin_mean_c.raw_cross_moment": 2.0,
    }
    monthly = {month: {"temperature_ordering_violations": 0} for month in MONTH_NAMES}
    return [
        {
            "calendar_class": "leap" if is_leap(index + 1) else "common",
            "annual": dict(annual),
            "monthly": copy.deepcopy(monthly),
        }
        for index in range(256)
    ]


def toy_problem() -> dict:
    return {
        "preservation_ub_count": 1,
        "a_ub": np.zeros((1, 256 + len(ANNUAL_COMPONENTS))),
        "b_ub": np.zeros(1),
        "centered_target_values": {name: 0.0 for name in ANNUAL_COMPONENTS},
        "centered_baseline_values": {name: 0.0 for name in ANNUAL_COMPONENTS},
        "scales": {name: 1.0 for name in ANNUAL_COMPONENTS},
    }


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: run-synthetic-fixtures.py")
    definition = load_json(FIXTURES)
    blocks = synthetic_blocks()
    weights = [1.0 / 100.0 if index < 100 else 0.0 for index in range(256)]
    counts30 = [1 if index < 30 else 0 for index in range(256)]
    counts100 = [1 if index < 100 else 0 for index in range(256)]
    threshold = 1.0e-12
    records = []

    def add(fixture_id: str, passed: bool, observation: str) -> None:
        records.append({"fixture_id": fixture_id, "pass": bool(passed), "observation": observation})

    valid = validate_counts(blocks, weights, counts30, counts100, threshold)
    add("valid_nested_counts", valid["pass"], str(valid))
    mutation = list(counts30)
    mutation[100] = 1
    add("nonnested_counts", not validate_counts(blocks, weights, mutation, counts100, threshold)["pass"], "c30 not <= c100")
    mutation = list(counts30)
    mutation[0] = 0
    mutation[31] = 1
    add("calendar_count_mutation", not validate_counts(blocks, weights, mutation, counts100, threshold)["pass"], "30-year leap/common total changed")
    mutation100 = list(counts100)
    mutation100[0] = 3
    mutation100[1] = 0
    mutation30 = [min(left, right) for left, right in zip(counts30, mutation100)]
    add("maximum_reuse_mutation", not validate_counts(blocks, weights, mutation30, mutation100, threshold)["pass"], "count exceeds two")
    zero = list(counts100)
    zero[0] = 0
    zero[100] = 1
    add("zero_weight_support_mutation", not validate_counts(blocks, weights, counts30, zero, threshold)["pass"], "selected zero stationary weight")
    first = ORDER_TOOL.initial_path(counts30, counts100, blocks, 104729, 5)
    second = ORDER_TOOL.initial_path(counts30, counts100, blocks, 104729, 5)
    placement_pass = first == second and len(first) == 100 and all(index not in first[max(0, position - 5) : position] for position, index in enumerate(first))
    add("deterministic_calendar_cooldown_placement", placement_pass, "deterministic exact placement")
    infeasible = milp(np.zeros(1), integrality=np.ones(1), bounds=Bounds([0.0], [1.0]), constraints=LinearConstraint([[1.0]], [0.5], [0.5]))
    add("synthetic_integer_infeasible", not infeasible.success and int(infeasible.status) == 2, str(infeasible.message))
    a5d1_contract = {"marginal_solver": {"independent_replay_tolerance": 2.0e-7}, "preservation": {"temperature_ordering_violations": 0}}
    replay = count_only_replay(toy_problem(), blocks, counts30, 30, a5d1_contract)
    add("count_only_exact_replay", replay["pass"], str(replay["violation_objective"]))
    mutated_blocks = copy.deepcopy(blocks)
    mutated_blocks[0]["annual"]["precip_total_mm"] = 10.0
    mutated = count_only_replay(toy_problem(), mutated_blocks, counts30, 30, a5d1_contract)
    add("count_only_centered_mutation", not mutated["pass"], str(mutated["actual_components"]["precip_total_mm.variance"]))
    add("duplicate_json_key", rejected_json('{"a":1,"a":2}'), "duplicate rejected")
    add("nonfinite_json_number", rejected_json('{"a":NaN}'), "NaN rejected")
    add("overflow_json_number", rejected_json('{"a":1e9999}'), "overflow rejected")
    expected = {row["id"] for row in definition["fixtures"]}
    if {row["fixture_id"] for row in records} != expected or not all(row["pass"] for row in records):
        failures = [row for row in records if not row["pass"]]
        raise ValueError(f"synthetic fixture matrix failed: {failures}")
    value = {
        "synthetic_fixture_results_schema_version": 1,
        "development_only": True,
        "expected_count": len(expected),
        "actual_count": len(records),
        "pass_count": sum(row["pass"] for row in records),
        "records": records,
    }
    write_json(RESULTS, value)
    print(f"A5d1b synthetic fixtures: {value['pass_count']}/{value['expected_count']} pass")


if __name__ == "__main__":
    main()
