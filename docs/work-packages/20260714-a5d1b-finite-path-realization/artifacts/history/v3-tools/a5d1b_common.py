#!/usr/bin/env python3
"""Shared fail-closed utilities for the A5d1b development experiment."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = Path(__file__).resolve().parent
TARGET = ROOT / "target/a5d1b-finite-path-realization"
COUNT_DIR = TARGET / "counts"
PATH_DIR = TARGET / "paths"

A5D1_ROOT = ROOT / "docs/work-packages/20260714-a5d1-selector-feasibility"
A5D1 = A5D1_ROOT / "artifacts"
A5D1_TARGET = ROOT / "target/a5d1-selector-feasibility"
A5D1_FEATURE_DIR = A5D1_TARGET / "features"
A5D1_CERTIFICATE_DIR = A5D1_TARGET / "certificates"
A5D1_PATH_DIR = A5D1_TARGET / "paths"
A5D1_CONTRACT = A5D1 / "selector-feasibility-contract-v4.json"
A5D1_FREEZE = A5D1 / "pre-solver-freeze-v6.json"
A5D1_FEATURE_MANIFEST = A5D1 / "year-feature-manifest-v1.json"
A5D1_LIBRARY_MANIFEST = A5D1 / "development-library-manifest-v1.json"
A5D1_MARGINAL = A5D1 / "marginal-results-v1.json"
A5D1_PATH_RESULTS = A5D1 / "path-results-v1.json"
A5D1_DECISION = A5D1 / "a5d1-decision-v1.json"
A5D1_DETAILED_ARCHIVE = A5D1 / "detailed-evidence-v1.tar.gz"
A5D1_DETAILED_MANIFEST = A5D1 / "detailed-evidence-manifest-v1.json"

CONTRACT = ARTIFACTS / "finite-path-realization-contract-v1.json"
CONTRACT_SCHEMA = ARTIFACTS / "finite-path-realization-contract-v1.schema.json"
FREEZE = ARTIFACTS / "pre-outcome-freeze-v3.json"
LOCK = ARTIFACTS / "evidence-lock-inputs-v1.json"
DIAGNOSTIC_RESULTS = ARTIFACTS / "inherited-path-diagnostics-v1.json"
COUNT_RESULTS = ARTIFACTS / "count-feasibility-results-v1.json"
PATH_RESULTS = ARTIFACTS / "ordered-path-results-v1.json"

MONTH_NAMES = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]
ANNUAL_COMPONENTS = [
    "precip_total_mm.variance",
    "tmax_mean_c.variance",
    "tmin_mean_c.variance",
    "precip_total_mm_x_tmax_mean_c.covariance",
    "precip_total_mm_x_tmin_mean_c.covariance",
    "tmax_mean_c_x_tmin_mean_c.covariance",
]


def reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON token: {token}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"JSON number overflows binary64: {token}")
    return value


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(
            handle,
            parse_constant=reject_nonfinite,
            parse_float=parse_finite_float,
            object_pairs_hook=reject_duplicate_keys,
        )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def identity(path: Path) -> dict:
    return {"path": relative(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def load_a5d1_module(name: str, filename: str):
    package_text = str(A5D1)
    if package_text not in sys.path:
        sys.path.insert(0, package_text)
    spec = importlib.util.spec_from_file_location(name, A5D1 / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import A5d1 tool: {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def a5d1_modules():
    solver = load_a5d1_module("a5d1b_inherited_solver", "solve-selector-feasibility.py")
    path_tool = load_a5d1_module("a5d1b_inherited_path", "run-path-feasibility.py")
    return solver, path_tool


def station_ids() -> list[str]:
    manifest = load_json(A5D1_FEATURE_MANIFEST)
    if not isinstance(manifest, dict):
        raise ValueError("A5d1 feature manifest is not an object")
    ids = sorted(row["station_id"] for row in manifest["records"])
    if len(ids) != 17 or len(set(ids)) != 17:
        raise ValueError("A5d1b requires exactly 17 development stations")
    return ids


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def feature_path(station_id: str) -> Path:
    return A5D1_FEATURE_DIR / f"{station_id}-year-features-v1.json"


def certificate_path(station_id: str) -> Path:
    return A5D1_CERTIFICATE_DIR / f"{station_id}-pool-256-marginal-certificate-v1.json"


def freeze_identity() -> str:
    freeze = load_json(FREEZE)
    if not isinstance(freeze, dict):
        raise ValueError("A5d1b freeze is not an object")
    claimed = freeze.get("freeze_sha256")
    body = dict(freeze)
    body.pop("freeze_sha256", None)
    actual = canonical_sha256(body)
    if claimed != actual:
        raise ValueError("A5d1b freeze identity mismatch")
    return actual


def expanded_indices(counts: list[int]) -> list[int]:
    result: list[int] = []
    for index, count in enumerate(counts):
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("counts must be nonnegative integers")
        result.extend([index] * count)
    return result


def annual_means(blocks: list[dict], counts: list[int], horizon: int) -> tuple[float, float, float]:
    if sum(counts) != horizon:
        raise ValueError("count total does not equal horizon")
    result = []
    for name in ("precip_total_mm", "tmax_mean_c", "tmin_mean_c"):
        result.append(
            math.fsum(count * float(block["annual"][name]) for count, block in zip(counts, blocks))
            / horizon
        )
    return tuple(result)  # type: ignore[return-value]


def count_only_replay(problem: dict, blocks: list[dict], counts: list[int], horizon: int, a5d1_contract: dict) -> dict:
    """Replay the frozen finite marginal contract excluding order-dependent January."""
    if len(counts) != len(blocks) or sum(counts) != horizon:
        raise ValueError("count replay shape/total mismatch")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ValueError("invalid count vector")
    solver, _ = a5d1_modules()
    weights = np.asarray(counts, dtype=np.float64) / float(horizon)
    variables = np.concatenate((weights, np.zeros(len(ANNUAL_COMPONENTS))))
    row_count = problem["preservation_ub_count"]
    residuals = problem["a_ub"][:row_count] @ variables - problem["b_ub"][:row_count]
    centered = solver.centered_values(blocks, weights)
    components = {
        name: abs(centered[name] - problem["centered_target_values"][name])
        / problem["scales"][name]
        for name in ANNUAL_COMPONENTS
    }
    baseline = {
        name: abs(
            problem["centered_baseline_values"][name]
            - problem["centered_target_values"][name]
        )
        / problem["scales"][name]
        for name in ANNUAL_COMPONENTS
    }
    aggregate = math.fsum(components.values())
    baseline_aggregate = math.fsum(baseline.values())
    guard = 2.0e-12
    noninferiority = all(
        components[name] <= baseline[name] + 1.0e-7 + guard
        for name in ANNUAL_COMPONENTS
    )
    strict = aggregate <= 0.95 * baseline_aggregate + guard
    ordering_violations = sum(
        counts[index] * int(blocks[index]["monthly"][month]["temperature_ordering_violations"])
        for index in range(len(blocks))
        for month in MONTH_NAMES
    )
    maximum_residual = float(np.max(residuals))
    preservation_pass = maximum_residual <= a5d1_contract["marginal_solver"]["independent_replay_tolerance"]
    row_scales = np.maximum(
        1.0,
        np.maximum(
            np.abs(problem["b_ub"][:row_count]),
            np.max(np.abs(problem["a_ub"][:row_count]), axis=1),
        ),
    )
    violation = float(np.sum(np.maximum(residuals / row_scales, 0.0)))
    violation += math.fsum(
        max(0.0, components[name] - baseline[name] - 1.0e-7 - guard)
        for name in ANNUAL_COMPONENTS
    )
    violation += max(0.0, aggregate - 0.95 * baseline_aggregate - guard)
    violation += float(ordering_violations)
    return {
        "horizon": horizon,
        "preservation_maximum_residual": maximum_residual,
        "preservation_pass": preservation_pass,
        "centered_target_values": problem["centered_target_values"],
        "centered_actual_values": centered,
        "baseline_components": baseline,
        "actual_components": components,
        "baseline_aggregate": baseline_aggregate,
        "actual_aggregate": aggregate,
        "noninferiority": noninferiority,
        "strict_improvement": strict,
        "temperature_ordering_violations": ordering_violations,
        "pass": preservation_pass
        and noninferiority
        and strict
        and ordering_violations == a5d1_contract["preservation"]["temperature_ordering_violations"],
        "violation_objective": violation,
    }


def validate_counts(blocks: list[dict], weights: list[float], counts30: list[int], counts100: list[int], threshold: float) -> dict:
    if len(blocks) != 256 or len(weights) != 256 or len(counts30) != 256 or len(counts100) != 256:
        raise ValueError("count validation requires 256 entries")
    integer = all(isinstance(value, int) and not isinstance(value, bool) for value in counts30 + counts100)
    nested = integer and all(0 <= left <= right <= 2 for left, right in zip(counts30, counts100))
    positive = integer and all(count == 0 or weights[index] > threshold for index, count in enumerate(counts100))
    calendar = {}
    for horizon, counts, expected in ((30, counts30, (23, 7)), (100, counts100, (76, 24))):
        common = sum(count for count, block in zip(counts, blocks) if block["calendar_class"] == "common")
        leap = sum(count for count, block in zip(counts, blocks) if block["calendar_class"] == "leap")
        calendar[str(horizon)] = {
            "common": common,
            "leap": leap,
            "pass": (common, leap) == expected and sum(counts) == horizon,
        }
    return {
        "integer": integer,
        "nested_and_reuse": nested,
        "positive_support": positive,
        "calendar": calendar,
        "pass": integer and nested and positive and all(value["pass"] for value in calendar.values()),
    }
