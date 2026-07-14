#!/usr/bin/env python3
"""Execute the frozen A5d1 finite-path matrix without physical mutation."""

from __future__ import annotations

import hashlib
import importlib.util
import math
import random
import re
import sys
import time

import numpy as np

from a5d1_common import (
    CONTRACT,
    FEATURE_DIR,
    LIBRARY_MANIFEST,
    MARGINAL_RESULTS,
    PACKAGE,
    PATH_DIR,
    PATH_RESULTS,
    ROOT,
    dependence_metrics,
    freeze_identity,
    is_leap,
    load_json,
    relative,
    sha256,
    station_records,
    write_json,
)


SOLVER_SPEC = importlib.util.spec_from_file_location(
    "a5d1_solver", PACKAGE / "solve-selector-feasibility.py"
)
if SOLVER_SPEC is None or SOLVER_SPEC.loader is None:
    raise RuntimeError("cannot load frozen marginal solver")
SOLVER = importlib.util.module_from_spec(SOLVER_SPEC)
SOLVER_SPEC.loader.exec_module(SOLVER)
ROW = re.compile(rb"^\s*(\d+)\s+(\d+)\s+(\d+)(.*)$")


def detrend(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    x = np.arange(len(array), dtype=np.float64)
    design = np.column_stack((np.ones(len(array)), x))
    return [
        float(value)
        for value in array - design @ np.linalg.lstsq(design, array, rcond=None)[0]
    ]


def target_dependence(feature: dict) -> dict[str, float]:
    series = {
        name: detrend(feature["targets"]["annual_daymet_fit_series"][name])
        for name in ("precip_total_mm", "tmax_mean_c", "tmin_mean_c")
    }
    metrics = dependence_metrics(series, 30)
    # One stationary statistic estimated from the exposed 30-year fit period is
    # intentionally reused at both generated horizons; it is not 100-year data.
    return {f"30.{name}": value for name, value in metrics.items()} | {
        f"100.{name}": value for name, value in metrics.items()
    }


def path_series(
    blocks: list[dict], indices: list[int], horizon: int
) -> dict[str, list[float]]:
    selected = [blocks[index]["annual"] for index in indices[:horizon]]
    return {
        name: detrend([float(row[name]) for row in selected])
        for name in ("precip_total_mm", "tmax_mean_c", "tmin_mean_c")
    }


def path_metrics(blocks: list[dict], indices: list[int]) -> dict[str, float]:
    metrics = {}
    for horizon in (30, 100):
        values = dependence_metrics(path_series(blocks, indices, horizon), horizon)
        metrics.update({f"{horizon}.{name}": value for name, value in values.items()})
    return metrics


def distances(
    actual: dict[str, float], target: dict[str, float], baseline: dict[str, float]
) -> tuple[float, dict[str, float], dict[str, float], dict[str, float]]:
    scales = {
        name: max(abs(target[name] - baseline[name]), 0.10) for name in sorted(target)
    }
    candidate = {
        name: abs(actual[name] - target[name]) / scales[name] for name in sorted(target)
    }
    baseline_components = {
        name: abs(baseline[name] - target[name]) / scales[name] for name in sorted(target)
    }
    return math.fsum(candidate.values()), candidate, baseline_components, scales


def eligible_indices(
    blocks: list[dict], weights: list[float], target_year: int, threshold: float
) -> list[int]:
    expected = "leap" if is_leap(target_year) else "common"
    return [
        index
        for index, block in enumerate(blocks)
        if block["calendar_class"] == expected and weights[index] > threshold
    ]


def guarded_replacement(
    blocks: list[dict],
    weights: list[float],
    seed: int,
    cooldown: int,
    max_reuse: int,
    threshold: float,
) -> list[int]:
    rng = random.Random(seed)
    path: list[int] = []
    counts: dict[int, int] = {}
    for target_year in range(1, 101):
        candidates = [
            index
            for index in eligible_indices(blocks, weights, target_year, threshold)
            if counts.get(index, 0) < max_reuse and index not in path[-cooldown:]
        ]
        if not candidates:
            raise RuntimeError("guarded replacement exhausted positive-weight blocks")
        chosen = rng.choices(candidates, weights=[weights[index] for index in candidates], k=1)[0]
        path.append(chosen)
        counts[chosen] = counts.get(chosen, 0) + 1
    return path


def weighted_permutation(
    blocks: list[dict], weights: list[float], seed: int, threshold: float
) -> list[int]:
    rng = random.Random(seed)
    ordered_by_class: dict[str, list[int]] = {}
    for calendar_class in ("common", "leap"):
        candidates = [
            index
            for index, block in enumerate(blocks)
            if block["calendar_class"] == calendar_class and weights[index] > threshold
        ]
        candidates.sort(
            key=lambda index: -math.log(max(rng.random(), 1.0e-15)) / weights[index]
        )
        ordered_by_class[calendar_class] = candidates
    offsets = {"common": 0, "leap": 0}
    path = []
    for target_year in range(1, 101):
        calendar_class = "leap" if is_leap(target_year) else "common"
        offset = offsets[calendar_class]
        if offset >= len(ordered_by_class[calendar_class]):
            raise RuntimeError("weighted permutation exhausted positive-weight blocks")
        path.append(ordered_by_class[calendar_class][offset])
        offsets[calendar_class] += 1
    return path


def state_persistent(
    blocks: list[dict],
    weights: list[float],
    seed: int,
    cooldown: int,
    max_reuse: int,
    threshold: float,
) -> list[int]:
    rng = random.Random(seed)
    annual = np.asarray(
        [
            [
                block["annual"]["precip_total_mm"],
                block["annual"]["tmax_mean_c"],
                block["annual"]["tmin_mean_c"],
            ]
            for block in blocks
        ],
        dtype=np.float64,
    )
    scale = np.std(annual, axis=0, ddof=1)
    scale[scale == 0.0] = 1.0
    standardized = (annual - np.mean(annual, axis=0)) / scale
    path: list[int] = []
    counts: dict[int, int] = {}
    for target_year in range(1, 101):
        candidates = [
            index
            for index in eligible_indices(blocks, weights, target_year, threshold)
            if counts.get(index, 0) < max_reuse and index not in path[-cooldown:]
        ]
        if not candidates:
            raise RuntimeError("state-persistent selector exhausted positive-weight blocks")
        if path:
            previous = standardized[path[-1]]
            candidate_weights = [
                weights[index]
                * math.exp(-0.20 * float(np.sum((standardized[index] - previous) ** 2)))
                for index in candidates
            ]
        else:
            candidate_weights = [weights[index] for index in candidates]
        chosen = rng.choices(candidates, weights=candidate_weights, k=1)[0]
        path.append(chosen)
        counts[chosen] = counts.get(chosen, 0) + 1
    return path


def valid_reuse(indices: list[int], cooldown: int, max_reuse: int) -> bool:
    counts: dict[int, int] = {}
    for position, index in enumerate(indices):
        counts[index] = counts.get(index, 0) + 1
        if counts[index] > max_reuse or index in indices[max(0, position - cooldown) : position]:
            return False
    return True


def boundary_metrics(blocks: list[dict], indices: list[int], horizon: int) -> dict[str, float]:
    selected = indices[:horizon]
    count = len(selected) - 1
    values = {name: 0.0 for name in ("dry_to_dry_fraction", "dry_to_wet_fraction", "wet_to_dry_fraction", "wet_to_wet_fraction")}
    wet_continuation = 0.0
    dry_continuation = 0.0
    for left, right in zip(selected[:-1], selected[1:]):
        left_wet = blocks[left]["last_day_wet"]
        right_wet = blocks[right]["first_day_wet"]
        key = (
            "wet_to_wet_fraction" if left_wet and right_wet
            else "wet_to_dry_fraction" if left_wet
            else "dry_to_wet_fraction" if right_wet
            else "dry_to_dry_fraction"
        )
        values[key] += 1.0 / count
        continuation = (
            blocks[left]["trailing_same_state_spell_days"]
            + blocks[right]["leading_same_state_spell_days"]
        )
        if left_wet and right_wet:
            wet_continuation += continuation / count
        elif not left_wet and not right_wet:
            dry_continuation += continuation / count
    values["wet_spell_continuation_days_per_boundary"] = wet_continuation
    values["dry_spell_continuation_days_per_boundary"] = dry_continuation
    return values


def boundary_replay(
    blocks: list[dict], indices: list[int], baseline_indices: list[int], contract: dict
) -> dict:
    horizons = {}
    total_violation = 0.0
    passed = True
    for horizon in (30, 100):
        actual = boundary_metrics(blocks, indices, horizon)
        baseline = boundary_metrics(blocks, baseline_indices, horizon)
        components = {}
        for name in actual:
            if name.endswith("_fraction"):
                tolerance = contract["preservation"]["boundary_transition_absolute"]
            else:
                tolerance = contract["preservation"]["boundary_spell_mean_relative"] * max(
                    abs(baseline[name]), 1.0e-12
                )
            residual = abs(actual[name] - baseline[name]) - tolerance
            components[name] = {
                "actual": actual[name],
                "reference": baseline[name],
                "tolerance": tolerance,
                "pass": residual <= 1.0e-12,
            }
            total_violation += max(0.0, residual / max(tolerance, 1.0e-12))
            passed = passed and components[name]["pass"]
        horizons[str(horizon)] = components
    return {"horizons": horizons, "pass": passed, "violation_objective": total_violation}


def objective_tuple(
    blocks: list[dict],
    indices: list[int],
    problem: dict,
    target: dict[str, float],
    baseline_metrics: dict[str, float],
    baseline_indices: list[int],
    contract: dict,
) -> tuple[float, float, float]:
    finite = math.fsum(
        SOLVER.finite_prefix_replay(problem, blocks, indices, horizon, contract)[
            "violation_objective"
        ]
        for horizon in (30, 100)
    )
    boundary = boundary_replay(blocks, indices, baseline_indices, contract)[
        "violation_objective"
    ]
    dependence = distances(path_metrics(blocks, indices), target, baseline_metrics)[0]
    return finite, boundary, dependence


def optimize_path(
    blocks: list[dict],
    indices: list[int],
    problem: dict,
    target: dict[str, float],
    baseline_metrics: dict[str, float],
    baseline_indices: list[int],
    seed: int,
    contract: dict,
) -> tuple[list[int], int, tuple[float, float, float]]:
    rng = random.Random(seed ^ 0xA5D1)
    current = list(indices)
    current_objective = objective_tuple(
        blocks, current, problem, target, baseline_metrics, baseline_indices, contract
    )
    accepted = 0
    for _ in range(contract["path"]["iterations_per_path"]):
        left, right = rng.sample(range(100), 2)
        if is_leap(left + 1) != is_leap(right + 1):
            continue
        current[left], current[right] = current[right], current[left]
        if not valid_reuse(
            current,
            contract["path"]["cooldown_years"],
            contract["path"]["exact_block_max_reuse"],
        ):
            current[left], current[right] = current[right], current[left]
            continue
        candidate = objective_tuple(
            blocks, current, problem, target, baseline_metrics, baseline_indices, contract
        )
        if candidate < current_objective:
            current_objective = candidate
            accepted += 1
        else:
            current[left], current[right] = current[right], current[left]
    return current, accepted, current_objective


def raw_cli_rows(path) -> dict[int, list[tuple[int, int, bytes]]]:
    result: dict[int, list[tuple[int, int, bytes]]] = {}
    started = False
    skip_units = False
    for line in path.read_bytes().splitlines():
        if line.startswith(b" da mo year"):
            started, skip_units = True, True
            continue
        if skip_units:
            skip_units = False
            continue
        if not started or not line.strip():
            continue
        match = ROW.match(line)
        if match is None:
            raise ValueError(f"unparseable source row: {path}: {line!r}")
        day, month, year = map(int, match.group(1, 2, 3))
        result.setdefault(year, []).append((day, month, match.group(4)))
    return result


def render_hundred(rows: dict[int, list[tuple[int, int, bytes]]], indices: list[int]) -> bytes:
    output = bytearray()
    for destination_year, index in enumerate(indices, 1):
        for day, month, suffix in rows[index + 1]:
            output.extend(f"{day:3d}{month:3d}{destination_year:6d}".encode())
            output.extend(suffix)
            output.extend(b"\n")
    return bytes(output)


def render_thirty(rows: dict[int, list[tuple[int, int, bytes]]], indices: list[int]) -> bytes:
    output = bytearray()
    for destination_year in range(1, 31):
        source_year = indices[destination_year - 1] + 1
        for source_row in rows[source_year]:
            day = source_row[0]
            month = source_row[1]
            physical_suffix = source_row[2]
            output.extend(f"{day:3d}{month:3d}{destination_year:6d}".encode())
            output.extend(physical_suffix)
            output.extend(b"\n")
    return bytes(output)


def verify_rendered_suffixes(
    rendered: bytes,
    rows: dict[int, list[tuple[int, int, bytes]]],
    indices: list[int],
    horizon: int,
) -> bool:
    expected = [row for index in indices[:horizon] for row in rows[index + 1]]
    actual_lines = rendered.splitlines()
    if len(expected) != len(actual_lines):
        return False
    for (expected_day, expected_month, expected_suffix), line in zip(expected, actual_lines):
        match = ROW.match(line)
        if match is None:
            return False
        if int(match.group(1)) != expected_day or int(match.group(2)) != expected_month:
            return False
        if match.group(4) != expected_suffix:
            return False
    return True


def execute_cell(
    station_id: str,
    pool_size: int,
    algorithm: str,
    seed: int,
    blocks: list[dict],
    weights: list[float],
    marginal_pass: bool,
    problem: dict,
    target: dict[str, float],
    baseline_indices: list[int],
    contract: dict,
    raw_rows: dict[int, list[tuple[int, int, bytes]]],
    freeze_sha256: str,
) -> dict:
    started = time.monotonic()
    cooldown = contract["path"]["cooldown_years"]
    max_reuse = contract["path"]["exact_block_max_reuse"]
    threshold = contract["marginal_solver"]["positive_weight_threshold"]
    selector = {
        "guarded_replacement": lambda: guarded_replacement(
            blocks, weights, seed, cooldown, max_reuse, threshold
        ),
        "weighted_permutation": lambda: weighted_permutation(
            blocks, weights, seed, threshold
        ),
        "state_persistent_different_block": lambda: state_persistent(
            blocks, weights, seed, cooldown, max_reuse, threshold
        ),
    }[algorithm]
    baseline_metrics = path_metrics(blocks, baseline_indices)
    failure = None
    try:
        initial = selector()
        optimized, accepted_swaps, objective = optimize_path(
            blocks,
            initial,
            problem,
            target,
            baseline_metrics,
            baseline_indices,
            seed,
            contract,
        )
    except RuntimeError as error:
        failure = str(error)
        optimized = baseline_indices
        accepted_swaps = 0
        objective = (math.inf, math.inf, math.inf)
    actual_metrics = path_metrics(blocks, optimized)
    aggregate, components, baseline_components, scales = distances(
        actual_metrics, target, baseline_metrics
    )
    baseline_aggregate = math.fsum(baseline_components.values())
    noninferiority = all(
        components[name] <= baseline_components[name] + 0.10 + 1.0e-9
        for name in components
    )
    strict_improvement = aggregate <= 0.95 * baseline_aggregate + 1.0e-9
    finite = {
        str(horizon): SOLVER.finite_prefix_replay(
            problem, blocks, optimized, horizon, contract
        )
        for horizon in (30, 100)
    }
    finite_pass = all(value["pass"] for value in finite.values())
    calendar_pass = all(
        blocks[index]["calendar_class"] == ("leap" if is_leap(year) else "common")
        for year, index in enumerate(optimized, 1)
    )
    reuse_pass = valid_reuse(optimized, cooldown, max_reuse)
    zero_weight_selections = sum(weights[index] <= threshold for index in optimized)
    boundary = boundary_replay(blocks, optimized, baseline_indices, contract)
    rendered_100 = render_hundred(raw_rows, optimized)
    rendered_30 = render_thirty(raw_rows, optimized)
    render_100_identity = verify_rendered_suffixes(rendered_100, raw_rows, optimized, 100)
    render_30_identity = verify_rendered_suffixes(rendered_30, raw_rows, optimized, 30)
    prefix_pass = rendered_100.startswith(rendered_30)
    render_pass = render_100_identity and render_30_identity and prefix_pass
    path_pass = bool(
        marginal_pass
        and failure is None
        and finite_pass
        and noninferiority
        and strict_improvement
        and calendar_pass
        and reuse_pass
        and zero_weight_selections == 0
        and boundary["pass"]
        and render_pass
    )
    cell_id = f"{station_id}|{pool_size}|canonical-burn-0|{algorithm}|{seed}"
    value = {
        "path_cell_schema_version": 2,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "cell_id": cell_id,
        "station_id": station_id,
        "pool_size": pool_size,
        "library_realization": "canonical-burn-0",
        "algorithm": algorithm,
        "path_seed": seed,
        "source_year_indices_zero_based": optimized,
        "source_years_one_based": [index + 1 for index in optimized],
        "thirty_year_prefix": optimized[:30],
        "marginal_pass": marginal_pass,
        "finite_prefix_marginal": finite,
        "path_pass": path_pass,
        "failure": failure,
        "iterations": contract["path"]["iterations_per_path"],
        "accepted_swaps": accepted_swaps,
        "objective_tuple": list(objective),
        "dependence": {
            "detrending": "OLS linear detrend applied identically to target, baseline, and candidate",
            "target": target,
            "baseline": baseline_metrics,
            "actual": actual_metrics,
            "scales": scales,
            "baseline_components": baseline_components,
            "actual_components": components,
            "baseline_aggregate": baseline_aggregate,
            "actual_aggregate": aggregate,
            "noninferiority": noninferiority,
            "strict_improvement": strict_improvement,
        },
        "boundary": boundary,
        "invariants": {
            "calendar_pass": calendar_pass,
            "reuse_cooldown_pass": reuse_pass,
            "zero_weight_selections": zero_weight_selections,
            "rendered_daily_100_sha256": hashlib.sha256(rendered_100).hexdigest(),
            "rendered_daily_30_sha256": hashlib.sha256(rendered_30).hexdigest(),
            "rendered_100_physical_identity_pass": render_100_identity,
            "rendered_30_physical_identity_pass": render_30_identity,
            "common_prefix_pass": prefix_pass,
            "physical_value_interventions": 0,
            "payload_identity_pass": render_100_identity and render_30_identity,
        },
        "wall_seconds": round(time.monotonic() - started, 6),
    }
    output = PATH_DIR / f"{station_id}-pool-{pool_size}-{algorithm}-seed-{seed}-path-v1.json"
    write_json(output, value)
    criteria = (
        ("stationary_marginal_feasibility", marginal_pass),
        ("bounded_positive_weight_selector", failure is None),
        ("finite_prefix_marginal", finite_pass),
        ("dependence_noninferiority", noninferiority),
        ("dependence_strict_improvement", strict_improvement),
        ("boundary_vector", boundary["pass"]),
        ("calendar", calendar_pass),
        ("reuse_cooldown", reuse_pass),
        ("zero_weight_selection", zero_weight_selections == 0),
        ("render_and_physical_identity", render_pass),
    )
    return {
        "cell_id": cell_id,
        "station_id": station_id,
        "pool_size": pool_size,
        "algorithm": algorithm,
        "path_seed": seed,
        "marginal_pass": marginal_pass,
        "finite_prefix_pass": finite_pass,
        "path_pass": path_pass,
        "first_failed_criterion": next((name for name, passed in criteria if not passed), None),
        "path_record": {"path": relative(output), "sha256": sha256(output)},
        "wall_seconds": value["wall_seconds"],
    }


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: run-path-feasibility.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    marginal = load_json(MARGINAL_RESULTS)
    libraries = load_json(LIBRARY_MANIFEST)
    if not all(isinstance(value, dict) for value in (contract, marginal, libraries)):
        raise ValueError("invalid path inputs")
    if marginal["freeze_sha256"] != freeze_sha256 or libraries["freeze_sha256"] != freeze_sha256:
        raise ValueError("path input freeze mismatch")
    marginal_index = {
        (row["station_id"], row["pool_size"]): row for row in marginal["records"]
    }
    library_index = {row["station_id"]: row for row in libraries["records"]}
    PATH_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    started = time.monotonic()
    for station in station_records():
        station_id = station["station_id"]
        feature = load_json(FEATURE_DIR / f"{station_id}-year-features-v1.json")
        cli = ROOT / library_index[station_id]["cli"]["path"]
        raw_rows = raw_cli_rows(cli)
        target = target_dependence(feature)
        for pool_size in contract["pool_sizes"]:
            blocks = feature["blocks"][:pool_size]
            problem = SOLVER.build_problem(blocks, feature["targets"], contract)
            marginal_row = marginal_index[(station_id, pool_size)]
            certificate = load_json(ROOT / marginal_row["certificate"]["path"])
            weights = certificate["weights"]
            baseline_indices = list(range(100))
            for algorithm in contract["algorithms"]:
                for seed in contract["path"]["path_seeds"]:
                    records.append(
                        execute_cell(
                            station_id,
                            pool_size,
                            algorithm,
                            seed,
                            blocks,
                            weights,
                            marginal_row["marginal_pass"],
                            problem,
                            target,
                            baseline_indices,
                            contract,
                            raw_rows,
                            freeze_sha256,
                        )
                    )
    expected = 17 * 2 * 1 * 3 * 3
    cell_ids = [row["cell_id"] for row in records]
    if len(records) != expected or len(set(cell_ids)) != expected:
        raise ValueError("path matrix closure failure")
    value = {
        "path_results_schema_version": 2,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "contract_sha256": sha256(CONTRACT),
        "marginal_results_sha256": sha256(MARGINAL_RESULTS),
        "expected_cell_count": expected,
        "actual_cell_count": len(records),
        "unique_cell_count": len(set(cell_ids)),
        "pass_count": sum(row["path_pass"] for row in records),
        "records": records,
        "total_wall_seconds": round(time.monotonic() - started, 6),
    }
    write_json(PATH_RESULTS, value)
    print(f"A5d1 path matrix: {value['pass_count']}/{expected} pass")


if __name__ == "__main__":
    main()
