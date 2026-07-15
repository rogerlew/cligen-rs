"""Objective availability, null calibration, Pareto, and frozen selection."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from .canonical import read_json, validate_schema
from .errors import require


def load_objective_registry(path: str, schema_path: str) -> dict[str, Any]:
    registry = read_json(path)
    validate_schema(registry, read_json(schema_path))
    ids = [objective["id"] for objective in registry["objectives"]]
    require(len(ids) == len(set(ids)), "OBJECTIVE_ID_DUPLICATE", "registry")
    return registry


def normalized_distance(candidate: float, baseline: float, floor: float) -> float:
    require(all(math.isfinite(value) for value in (candidate, baseline, floor)), "OBJECTIVE_NONFINITE", "distance")
    require(candidate >= 0.0 and baseline >= 0.0 and floor > 0.0, "OBJECTIVE_DISTANCE_SUPPORT", f"{candidate},{baseline},{floor}")
    return candidate / max(baseline, floor)


def two_part_zero_distance(
    candidate_zero_mass: float,
    baseline_zero_mass: float,
    candidate_positive_scale: float,
    baseline_positive_scale: float,
    zero_mass_floor: float,
    scale_floor: float,
) -> float:
    require(0.0 <= candidate_zero_mass <= 1.0 and 0.0 <= baseline_zero_mass <= 1.0, "ZERO_MASS_SUPPORT", "probability")
    zero_part = abs(candidate_zero_mass - baseline_zero_mass) / zero_mass_floor
    scale_part = abs(candidate_positive_scale - baseline_positive_scale) / max(abs(baseline_positive_scale), scale_floor)
    result = 0.5 * (zero_part + scale_part)
    require(math.isfinite(result), "OBJECTIVE_NONFINITE", "two-part")
    return result


def availability_by_stratum(
    cells: Iterable[dict[str, Any]],
    minimum: int = 2,
    required_strata: Iterable[str] = (),
) -> dict[str, bool]:
    available: dict[str, set[str]] = defaultdict(set)
    all_strata: set[str] = set(required_strata)
    for cell in cells:
        all_strata.add(cell["stratum"])
        if cell["status"] == "available":
            available[cell["stratum"]].add(cell["station_id"])
    return {stratum: len(available[stratum]) >= minimum for stratum in sorted(all_strata)}


def nearest_rank_quantile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(values)
    require(bool(ordered), "QUANTILE_EMPTY", "values")
    require(0.0 < probability <= 1.0, "QUANTILE_PROBABILITY", str(probability))
    rank = max(1, math.ceil(probability * len(ordered)))
    return ordered[rank - 1]


def calibrate_max_statistic(
    replicate_cells: list[dict[tuple[str, int], list[float]]],
    floors: dict[tuple[str, int], float],
    alpha: float = 0.05,
) -> dict[str, float]:
    """Candidate-blind family/horizon thresholds from paired null replicates."""

    require(len(replicate_cells) >= 100, "NULL_REPLICATES_INSUFFICIENT", str(len(replicate_cells)))
    expected_keys = set(replicate_cells[0])
    require(bool(expected_keys) and set(floors) == expected_keys, "NULL_CELL_SET", "floors")
    maxima: dict[tuple[str, int], list[float]] = defaultdict(list)
    for replicate in replicate_cells:
        require(set(replicate) == expected_keys, "NULL_CELL_SET", "replicate")
        for key, values in replicate.items():
            require(bool(values) and all(math.isfinite(value) for value in values), "NULL_CELL_INVALID", repr(key))
            maxima[key].append(max(values))
    result: dict[str, float] = {}
    for key, values in sorted(maxima.items()):
        threshold = max(floors[key], nearest_rank_quantile(values, 1.0 - alpha))
        result[f"{key[0]}:{key[1]}"] = threshold
    return result


def pareto_frontier(items: list[dict[str, Any]], metric_ids: list[str]) -> list[str]:
    """Return non-dominated IDs for finite minimize-distance vectors."""

    vectors: dict[str, tuple[float, ...]] = {}
    for item in items:
        require(set(metric_ids) <= set(item["objectives"]), "PARETO_METRIC_MISSING", item["id"])
        vector = tuple(float(item["objectives"][metric]) for metric in metric_ids)
        require(all(math.isfinite(value) for value in vector), "PARETO_NONFINITE", item["id"])
        vectors[item["id"]] = vector
    frontier = []
    for identifier, vector in vectors.items():
        dominated = any(
            other != identifier
            and all(left <= right for left, right in zip(other_vector, vector))
            and any(left < right for left, right in zip(other_vector, vector))
            for other, other_vector in vectors.items()
        )
        if not dominated:
            frontier.append(identifier)
    return sorted(frontier)


@dataclass(frozen=True)
class SelectionSummary:
    candidate_class: str
    feasible: bool
    complete: bool
    degradation_count: int
    worst_standardized_improvement: float
    improved_families: int
    median_normalized_distance: float
    effective_parameter_count: int


def select_candidate(summaries: Iterable[SelectionSummary]) -> str:
    items = list(summaries)
    for item in items:
        require(
            item.degradation_count >= 0
            and item.improved_families >= 0
            and item.effective_parameter_count >= 0
            and math.isfinite(item.worst_standardized_improvement)
            and math.isfinite(item.median_normalized_distance),
            "SELECTION_SUMMARY_INVALID",
            item.candidate_class,
        )
    survivors = [item for item in items if item.feasible and item.complete and item.degradation_count == 0]
    require(bool(survivors), "NO_SELECTABLE_CANDIDATE", "lexicographic filter")
    survivors.sort(
        key=lambda item: (
            -item.worst_standardized_improvement,
            -item.improved_families,
            item.median_normalized_distance,
            item.effective_parameter_count,
            item.candidate_class,
        )
    )
    return survivors[0].candidate_class
