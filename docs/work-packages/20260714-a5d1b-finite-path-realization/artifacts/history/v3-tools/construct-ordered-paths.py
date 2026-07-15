#!/usr/bin/env python3
"""Construct fixed-count ordered paths after complete A5d1b count feasibility."""

from __future__ import annotations

import hashlib
import math
import random
import sys
import time

from a5d1b_common import (
    A5D1_CONTRACT,
    A5D1_LIBRARY_MANIFEST,
    CONTRACT,
    COUNT_RESULTS,
    PATH_DIR,
    PATH_RESULTS,
    ROOT,
    a5d1_modules,
    certificate_path,
    feature_path,
    freeze_identity,
    identity,
    is_leap,
    load_json,
    station_ids,
    validate_counts,
    write_json,
)


def place_segment(multiset: list[int], blocks: list[dict], start: int, seed: int, prior: list[int], cooldown: int) -> list[int]:
    remaining = {}
    for index in multiset:
        remaining[index] = remaining.get(index, 0) + 1
    rng = random.Random(seed)
    ranks = {
        (position, index): rng.random()
        for position in range(start, start + len(multiset))
        for index in remaining
    }
    result = list(prior)
    nodes = 0

    def search(position: int) -> bool:
        nonlocal nodes
        nodes += 1
        if nodes > 1_000_000:
            return False
        if position == start + len(multiset):
            return True
        calendar_class = "leap" if is_leap(position + 1) else "common"
        candidates = [
            index
            for index, count in remaining.items()
            if count > 0
            and blocks[index]["calendar_class"] == calendar_class
            and index not in result[max(0, len(result) - cooldown) :]
        ]
        candidates.sort(key=lambda index: (ranks[(position, index)], index))
        for index in candidates:
            remaining[index] -= 1
            result.append(index)
            if search(position + 1):
                return True
            result.pop()
            remaining[index] += 1
        return False

    if not search(start):
        raise RuntimeError("bounded calendar/cooldown placement exhausted")
    return result[len(prior) :]


def initial_path(counts30: list[int], counts100: list[int], blocks: list[dict], seed: int, cooldown: int) -> list[int]:
    prefix = [index for index, count in enumerate(counts30) for _ in range(count)]
    suffix = [index for index, (left, right) in enumerate(zip(counts30, counts100)) for _ in range(right - left)]
    first = place_segment(prefix, blocks, 0, seed ^ 0x30A5D1B, [], cooldown)
    second = place_segment(suffix, blocks, 30, seed ^ 0x64A5D1B, first, cooldown)
    return first + second


def january_replay(blocks: list[dict], indices: list[int], horizon: int, problem: dict, contract: dict) -> dict:
    selected = indices[:horizon]
    counts = {
        name: sum(blocks[index]["monthly"]["jan"][name] for index in selected)
        for name in ("dry_predecessors", "wet_after_dry", "wet_predecessors", "wet_after_wet")
    }
    boundary = {name: 0 for name in counts}
    for left, right in zip(selected[:-1], selected[1:]):
        previous = bool(blocks[left]["last_day_wet"])
        destination = bool(blocks[right]["first_day_wet"])
        if previous:
            boundary["wet_predecessors"] += 1
            boundary["wet_after_wet"] += int(destination)
        else:
            boundary["dry_predecessors"] += 1
            boundary["wet_after_dry"] += int(destination)
    tolerance = contract["monthly_tolerances"]["precipitation_transition_probability_absolute"]
    probabilities = {}
    violation = 0.0
    for name, numerator_name, denominator_name in (
        ("wet_given_dry", "wet_after_dry", "dry_predecessors"),
        ("wet_given_wet", "wet_after_wet", "wet_predecessors"),
    ):
        numerator = counts[numerator_name] + boundary[numerator_name]
        denominator = counts[denominator_name] + boundary[denominator_name]
        actual = numerator / denominator if denominator else None
        target = problem["january_transition_target"][name]
        lower = max(0.0, target - tolerance)
        upper = min(1.0, target + tolerance)
        passed = actual is not None and lower <= actual <= upper
        excess = 1.0 if actual is None else max(lower - actual, actual - upper, 0.0)
        violation += excess
        probabilities[name] = {
            "actual": actual,
            "numerator": numerator,
            "denominator": denominator,
            "lower": lower,
            "upper": upper,
            "pass": passed,
        }
    return {"pass": all(value["pass"] for value in probabilities.values()), "violation": violation, "probabilities": probabilities}


def dependence_replay(path_tool, blocks: list[dict], indices: list[int], target: dict, baseline_metrics: dict) -> dict:
    actual_metrics = path_tool.path_metrics(blocks, indices)
    aggregate, components, baseline_components, scales = path_tool.distances(actual_metrics, target, baseline_metrics)
    baseline_aggregate = math.fsum(baseline_components.values())
    noninferiority = all(components[name] <= baseline_components[name] + 0.10 + 1.0e-9 for name in components)
    strict = aggregate <= 0.95 * baseline_aggregate + 1.0e-9
    violation = math.fsum(max(0.0, components[name] - baseline_components[name] - 0.10 - 1.0e-9) / 0.10 for name in components)
    violation += max(0.0, aggregate - 0.95 * baseline_aggregate - 1.0e-9) / max(0.05 * baseline_aggregate, 1.0e-12)
    return {
        "target": target,
        "baseline": baseline_metrics,
        "actual": actual_metrics,
        "scales": scales,
        "baseline_components": baseline_components,
        "actual_components": components,
        "baseline_aggregate": baseline_aggregate,
        "actual_aggregate": aggregate,
        "noninferiority": noninferiority,
        "strict_improvement": strict,
        "violation": violation,
    }


def order_evaluation(path_tool, blocks: list[dict], indices: list[int], problem: dict, target: dict, baseline_metrics: dict, baseline_indices: list[int], a5d1_contract: dict) -> dict:
    january = {str(h): january_replay(blocks, indices, h, problem, a5d1_contract) for h in (30, 100)}
    boundary = path_tool.boundary_replay(blocks, indices, baseline_indices, a5d1_contract)
    dependence = dependence_replay(path_tool, blocks, indices, target, baseline_metrics)
    failure_count = sum(not value["pass"] for value in january.values())
    failure_count += int(not boundary["pass"])
    failure_count += int(not dependence["noninferiority"])
    failure_count += int(not dependence["strict_improvement"])
    violation = math.fsum(value["violation"] for value in january.values())
    violation += boundary["violation_objective"] + dependence["violation"]
    return {
        "january": january,
        "boundary": boundary,
        "dependence": dependence,
        "failure_count": failure_count,
        "violation": violation,
        "pass": failure_count == 0,
    }


def optimize_order(path_tool, blocks: list[dict], initial: list[int], problem: dict, target: dict, baseline_metrics: dict, baseline_indices: list[int], seed: int, contract: dict, a5d1_contract: dict) -> tuple[list[int], dict, int, float, bool]:
    rng = random.Random(seed ^ 0xA5D1B)
    current = list(initial)
    current_eval = order_evaluation(path_tool, blocks, current, problem, target, baseline_metrics, baseline_indices, a5d1_contract)
    best = list(current)
    best_eval = current_eval
    accepted = 0
    started = time.monotonic()
    iterations = contract["algorithm"]["ordering_iterations"]
    start_temperature = contract["algorithm"]["ordering_temperature_start"]
    end_temperature = contract["algorithm"]["ordering_temperature_end"]
    groups = []
    for segment in (range(0, 30), range(30, 100)):
        for calendar_class in ("common", "leap"):
            values = [position for position in segment if blocks[current[position]]["calendar_class"] == calendar_class]
            if len(values) >= 2:
                groups.append(values)
    exhausted = False
    for iteration in range(iterations):
        if best_eval["pass"]:
            break
        if time.monotonic() - started > contract["resource_ceilings"]["ordering_seconds_per_path"]:
            exhausted = True
            break
        positions = rng.choice(groups)
        left, right = rng.sample(positions, 2)
        if current[left] == current[right]:
            continue
        current[left], current[right] = current[right], current[left]
        if not path_tool.valid_reuse(current, a5d1_contract["path"]["cooldown_years"], a5d1_contract["path"]["exact_block_max_reuse"]):
            current[left], current[right] = current[right], current[left]
            continue
        candidate = order_evaluation(path_tool, blocks, current, problem, target, baseline_metrics, baseline_indices, a5d1_contract)
        candidate_path = list(current)
        fraction = iteration / max(iterations - 1, 1)
        temperature = start_temperature * ((end_temperature / start_temperature) ** fraction)
        delta = candidate["violation"] - current_eval["violation"]
        if delta <= 0.0 or rng.random() < math.exp(-delta / max(temperature, 1.0e-12)):
            current_eval = candidate
            accepted += 1
        else:
            current[left], current[right] = current[right], current[left]
        candidate_key = (candidate["failure_count"], candidate["violation"], candidate["dependence"]["actual_aggregate"], tuple(candidate_path))
        best_key = (best_eval["failure_count"], best_eval["violation"], best_eval["dependence"]["actual_aggregate"], tuple(best))
        if candidate_key < best_key:
            best = candidate_path
            best_eval = candidate
    return best, best_eval, accepted, time.monotonic() - started, exhausted


def execute_cell(station_id: str, seed: int, contract: dict, a5d1_contract: dict, count_certificate: dict, library_record: dict, freeze_sha256: str) -> dict:
    solver, path_tool = a5d1_modules()
    feature = load_json(feature_path(station_id))
    stationary = load_json(certificate_path(station_id))
    witness = count_certificate["count_witness"]
    counts30 = witness["counts_30"]
    counts100 = witness["counts_100"]
    blocks = feature["blocks"][:256]
    validation = validate_counts(blocks, stationary["weights"], counts30, counts100, contract["nested_count_constraints"]["positive_weight_threshold"])
    if not validation["pass"]:
        raise ValueError(f"count certificate invariant mismatch: {station_id}")
    problem = solver.build_problem(blocks, feature["targets"], a5d1_contract)
    baseline_indices = list(range(100))
    target = path_tool.target_dependence(feature)
    baseline_metrics = path_tool.path_metrics(blocks, baseline_indices)
    initial = initial_path(counts30, counts100, blocks, seed, a5d1_contract["path"]["cooldown_years"])
    optimized, order_eval, accepted, wall, exhausted = optimize_order(
        path_tool, blocks, initial, problem, target, baseline_metrics, baseline_indices, seed, contract, a5d1_contract
    )
    exact_finite = {
        str(h): solver.finite_prefix_replay(problem, blocks, optimized, h, a5d1_contract)
        for h in (30, 100)
    }
    exact_dependence = dependence_replay(path_tool, blocks, optimized, target, baseline_metrics)
    exact_boundary = path_tool.boundary_replay(blocks, optimized, baseline_indices, a5d1_contract)
    rows = path_tool.raw_cli_rows(ROOT / library_record["cli"]["path"])
    rendered100 = path_tool.render_hundred(rows, optimized)
    rendered30 = path_tool.render_thirty(rows, optimized)
    render100 = path_tool.verify_rendered_suffixes(rendered100, rows, optimized, 100)
    render30 = path_tool.verify_rendered_suffixes(rendered30, rows, optimized, 30)
    invariants = {
        "calendar": all(blocks[index]["calendar_class"] == ("leap" if is_leap(year) else "common") for year, index in enumerate(optimized, 1)),
        "reuse_cooldown": path_tool.valid_reuse(optimized, a5d1_contract["path"]["cooldown_years"], a5d1_contract["path"]["exact_block_max_reuse"]),
        "zero_weight_selections": sum(stationary["weights"][index] <= contract["nested_count_constraints"]["positive_weight_threshold"] for index in optimized),
        "count_30_identity": [optimized[:30].count(index) for index in range(256)] == counts30,
        "count_100_identity": [optimized.count(index) for index in range(256)] == counts100,
        "rendered_100_physical_identity": render100,
        "rendered_30_physical_identity": render30,
        "common_prefix": rendered100.startswith(rendered30),
        "physical_value_interventions": 0,
        "rendered_100_sha256": hashlib.sha256(rendered100).hexdigest(),
        "rendered_30_sha256": hashlib.sha256(rendered30).hexdigest(),
    }
    invariant_pass = all(value for key, value in invariants.items() if key not in ("zero_weight_selections", "physical_value_interventions", "rendered_100_sha256", "rendered_30_sha256"))
    invariant_pass = invariant_pass and invariants["zero_weight_selections"] == 0 and invariants["physical_value_interventions"] == 0
    path_pass = (
        all(value["pass"] for value in exact_finite.values())
        and exact_dependence["noninferiority"]
        and exact_dependence["strict_improvement"]
        and exact_boundary["pass"]
        and invariant_pass
        and not exhausted
    )
    record = {
        "ordered_path_cell_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "cell_id": f"{station_id}|256|nested_count_annealed_order_v1|{seed}",
        "station_id": station_id,
        "path_seed": seed,
        "algorithm": contract["algorithm"]["ordering_id"],
        "source_year_indices_zero_based": optimized,
        "thirty_year_prefix": optimized[:30],
        "finite_prefix": exact_finite,
        "dependence": exact_dependence,
        "boundary": exact_boundary,
        "invariants": invariants | {"pass": invariant_pass},
        "search": {"accepted_moves": accepted, "wall_seconds": round(wall, 6), "resource_exhausted": exhausted, "final_order_evaluation": order_eval},
        "path_pass": path_pass,
    }
    output = PATH_DIR / f"{station_id}-seed-{seed}-ordered-path-v1.json"
    write_json(output, record)
    return {"cell_id": record["cell_id"], "station_id": station_id, "path_seed": seed, "path_pass": path_pass, "resource_exhausted": exhausted, "path_record": identity(output), "wall_seconds": record["search"]["wall_seconds"]}


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: construct-ordered-paths.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    a5d1_contract = load_json(A5D1_CONTRACT)
    counts = load_json(COUNT_RESULTS)
    libraries = load_json(A5D1_LIBRARY_MANIFEST)
    if not all(isinstance(value, dict) for value in (contract, a5d1_contract, counts, libraries)):
        raise ValueError("invalid ordered-path inputs")
    if counts["count_pass_count"] != 17:
        value = {
            "ordered_path_results_schema_version": 1,
            "development_only": True,
            "freeze_sha256": freeze_sha256,
            "executed": False,
            "reason": "count_gate_not_complete",
            "expected_cells_if_executed": 51,
            "actual_cells": 0,
            "pass_count": 0,
            "records": [],
        }
        write_json(PATH_RESULTS, value)
        print("A5d1b ordered paths: SKIPPED (count gate not complete)")
        return
    PATH_DIR.mkdir(parents=True, exist_ok=True)
    count_index = {}
    for row in counts["records"]:
        certificate = load_json(ROOT / row["certificate"]["path"])
        count_index[row["station_id"]] = certificate
    library_index = {row["station_id"]: row for row in libraries["records"]}
    started = time.monotonic()
    records = []
    for station_id in station_ids():
        for seed in contract["matrix"]["path_seeds"]:
            records.append(execute_cell(station_id, seed, contract, a5d1_contract, count_index[station_id], library_index[station_id], freeze_sha256))
    value = {
        "ordered_path_results_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "executed": True,
        "expected_cells_if_executed": 51,
        "actual_cells": len(records),
        "unique_cells": len({row["cell_id"] for row in records}),
        "pass_count": sum(row["path_pass"] for row in records),
        "resource_exhausted_count": sum(row["resource_exhausted"] for row in records),
        "records": records,
        "total_wall_seconds": round(time.monotonic() - started, 6),
    }
    write_json(PATH_RESULTS, value)
    print(f"A5d1b ordered paths: {value['pass_count']}/51 pass")


if __name__ == "__main__":
    main()
