#!/usr/bin/env python3
"""Independently replay all joint and separate-horizon A5d1b witnesses."""

from __future__ import annotations

import copy
import math
import sys

from a5d1b_common import (
    A5D1_CONTRACT,
    ARTIFACTS,
    CONTRACT,
    COUNT_RESULTS,
    ROOT,
    a5d1_modules,
    certificate_path,
    count_only_replay,
    feature_path,
    load_json,
    station_ids,
    validate_counts,
    write_json,
)


AUDIT = ARTIFACTS / "count-witness-replay-audit-v1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=2.0e-8, abs_tol=2.0e-8)


def replay_single(
    station_id: str,
    horizon: int,
    witness: dict,
    blocks: list[dict],
    weights: list[float],
    problem: dict,
    contract: dict,
    a5d1_contract: dict,
) -> bool:
    counts = witness["counts"]
    expected = contract["nested_count_constraints"]["calendar_counts"][str(horizon)]
    observed = {
        calendar: sum(
            count
            for count, block in zip(counts, blocks)
            if block["calendar_class"] == calendar
        )
        for calendar in ("common", "leap")
    }
    invariants = {
        "total": sum(counts) == horizon,
        "maximum_reuse": max(counts) <= 2,
        "positive_support": all(
            count == 0
            or weights[index]
            > contract["nested_count_constraints"]["positive_weight_threshold"]
            for index, count in enumerate(counts)
        ),
        "calendar": observed == expected,
    }
    require(invariants == witness["invariants"], f"single invariants changed: {station_id}:{horizon}")
    replay = count_only_replay(problem, blocks, counts, horizon, a5d1_contract)
    stored = witness["replay"]
    require(replay["pass"] == stored["pass"], f"single replay pass changed: {station_id}:{horizon}")
    require(close(replay["violation_objective"], stored["violation_objective"]), f"single replay objective changed: {station_id}:{horizon}")
    exact = all(invariants.values()) and replay["pass"]
    require(exact == witness["exact_pass"], f"single exact status changed: {station_id}:{horizon}")
    return exact


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: verify-count-witnesses.py")
    contract = load_json(CONTRACT)
    a5d1_contract = load_json(A5D1_CONTRACT)
    results = load_json(COUNT_RESULTS)
    solver, _ = a5d1_modules()
    rows = {row["station_id"]: row for row in results["records"]}
    require(sorted(rows) == station_ids(), "count result station matrix does not close")
    joint_exact = 0
    separate = {
        "30": {"attempted": 0, "optimal": 0, "incumbent": 0, "linear": 0, "exact": 0, "witness_records": 0},
        "100": {"attempted": 0, "optimal": 0, "incumbent": 0, "linear": 0, "exact": 0, "witness_records": 0},
    }
    mutation_source = None
    for station_id in station_ids():
        certificate = load_json(ROOT / rows[station_id]["certificate"]["path"])
        feature = load_json(feature_path(station_id))
        stationary = load_json(certificate_path(station_id))
        blocks = feature["blocks"][:256]
        weights = [float(value) for value in stationary["weights"]]
        problem = solver.build_problem(blocks, feature["targets"], a5d1_contract)
        witness = certificate["count_witness"]
        if witness is not None:
            validation = validate_counts(
                blocks,
                weights,
                witness["counts_30"],
                witness["counts_100"],
                contract["nested_count_constraints"]["positive_weight_threshold"],
            )
            replay30 = count_only_replay(problem, blocks, witness["counts_30"], 30, a5d1_contract)
            replay100 = count_only_replay(problem, blocks, witness["counts_100"], 100, a5d1_contract)
            exact = validation["pass"] and replay30["pass"] and replay100["pass"]
            require(exact == witness["exact_pass"] == certificate["count_pass"], f"joint replay changed: {station_id}")
            joint_exact += exact
        diagnostics = certificate["separate_horizon_diagnostics"]
        if diagnostics is None:
            continue
        for horizon in (30, 100):
            record = diagnostics[str(horizon)]
            aggregate = separate[str(horizon)]
            aggregate["attempted"] += 1
            aggregate["optimal"] += bool(record["initial_solver_success"] and record["initial_solver_status"] == 0)
            aggregate["incumbent"] += bool(record["initial_incumbent_present"])
            aggregate["linear"] += bool(record["linear_necessary_system_witness"])
            exact_witness = record["exact_witness"]
            if exact_witness is not None:
                aggregate["witness_records"] += 1
                exact = replay_single(
                    station_id,
                    horizon,
                    exact_witness,
                    blocks,
                    weights,
                    problem,
                    contract,
                    a5d1_contract,
                )
                aggregate["exact"] += exact
                if mutation_source is None:
                    mutation_source = (
                        station_id,
                        horizon,
                        exact_witness,
                        blocks,
                        weights,
                        problem,
                    )
            require(bool(record["exact_pass"]) == bool(exact_witness is not None and exact_witness["exact_pass"]), f"single stored exact aggregate changed: {station_id}:{horizon}")
    require(joint_exact == results["count_pass_count"], "joint exact aggregate changed")
    for horizon in ("30", "100"):
        published = results["separate_horizon_summary"][horizon]
        observed = separate[horizon]
        require(observed["attempted"] == published["attempted_station_count"], f"separate attempted aggregate changed: {horizon}")
        require(observed["optimal"] == published["optimal_status_count"], f"separate optimal aggregate changed: {horizon}")
        require(observed["incumbent"] == published["incumbent_present_count"], f"separate incumbent aggregate changed: {horizon}")
        require(observed["linear"] == published["linear_necessary_system_witness_count"], f"separate linear aggregate changed: {horizon}")
        require(observed["exact"] == published["exact_pass_count"], f"separate exact aggregate changed: {horizon}")
    require(mutation_source is not None, "no witness available for mutation self-test")
    station_id, horizon, witness, blocks, weights, problem = mutation_source
    mutated = copy.deepcopy(witness)
    mutated["counts"][0] += 1
    mutation_rejected = False
    try:
        replay_single(
            station_id,
            horizon,
            mutated,
            blocks,
            weights,
            problem,
            contract,
            a5d1_contract,
        )
    except (ValueError, IndexError):
        mutation_rejected = True
    require(mutation_rejected, "single-witness mutation was not rejected")
    value = {
        "count_witness_replay_audit_schema_version": 1,
        "development_only": True,
        "station_count": 17,
        "joint_exact_pass_count": joint_exact,
        "separate_horizon_replay": separate,
        "mutation_self_test_rejected": mutation_rejected,
        "pass": True,
    }
    write_json(AUDIT, value)
    print(
        "A5d1b count witness replay: PASS "
        f"(joint={joint_exact}/17; separate100={separate['100']['exact']}/17)"
    )


if __name__ == "__main__":
    main()
