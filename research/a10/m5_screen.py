"""Frozen A10M5 screen ordering and disposition helpers.

The compute trainer is package-local because it is evidence-producing research
code.  This module keeps the promotion arithmetic small, dependency-free, and
independently testable on the rmm controller.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any


POOLING_CLASSES = ("N0_complete", "N1_partial")
CONFIGURATIONS = (
    ("N0-l32-w128-d2-lognormal", "N0_complete", 32, 128, 2, "lognormal"),
    ("N0-l32-w128-d2-gpd", "N0_complete", 32, 128, 2, "gpd"),
    ("N0-l64-w128-d2-lognormal", "N0_complete", 64, 128, 2, "lognormal"),
    ("N0-l64-w128-d2-gpd", "N0_complete", 64, 128, 2, "gpd"),
    ("N0-l64-w128-d3-lognormal", "N0_complete", 64, 128, 3, "lognormal"),
    ("N0-l64-w128-d3-gpd", "N0_complete", 64, 128, 3, "gpd"),
    ("N1-l32-w128-d2-lognormal", "N1_partial", 32, 128, 2, "lognormal"),
    ("N1-l32-w128-d2-gpd", "N1_partial", 32, 128, 2, "gpd"),
    ("N1-l64-w128-d2-lognormal", "N1_partial", 64, 128, 2, "lognormal"),
    ("N1-l64-w128-d2-gpd", "N1_partial", 64, 128, 2, "gpd"),
    ("N1-l64-w128-d3-lognormal", "N1_partial", 64, 128, 3, "lognormal"),
    ("N1-l64-w128-d3-gpd", "N1_partial", 64, 128, 3, "gpd"),
)
CONFIGURATION_IDS = tuple(row[0] for row in CONFIGURATIONS)
CONFIGURATION_BY_ID = {
    row[0]: {
        "configuration_id": row[0],
        "pooling_class": row[1],
        "latent_dim": row[2],
        "width": row[3],
        "depth": row[4],
        "tail_head": row[5],
    }
    for row in CONFIGURATIONS
}


class ScreenError(ValueError):
    """The screen is incomplete, malformed, or outside the frozen design."""


def _finite(record: Mapping[str, Any], key: str) -> float:
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScreenError(f"{key} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ScreenError(f"{key} must be finite")
    return result


def validate_result(record: Mapping[str, Any]) -> None:
    """Validate the fields consumed by the frozen M5 promotion ordering."""
    configuration_id = record.get("configuration_id")
    if configuration_id not in CONFIGURATION_BY_ID:
        raise ScreenError("configuration is outside the frozen 12-row grid")
    expected = CONFIGURATION_BY_ID[str(configuration_id)]
    if record.get("pooling_class") != expected["pooling_class"]:
        raise ScreenError("pooling class differs from the frozen grid")
    if not isinstance(record.get("valid"), bool):
        raise ScreenError("valid must be boolean")
    if not record["valid"]:
        return
    for key in (
        "validation_primary_nll",
        "validation_tail_score",
        "validation_stability",
        "runtime_ratio_max",
    ):
        if _finite(record, key) < 0:
            raise ScreenError(f"{key} must be nonnegative")
    parameter_count = record.get("parameter_count")
    if (
        isinstance(parameter_count, bool)
        or not isinstance(parameter_count, int)
        or not 1 <= parameter_count <= 50_000_000
    ):
        raise ScreenError("parameter_count is outside the frozen ceiling")


def runtime_class(ratio: float) -> str:
    """Apply the exact M3 unrounded warm-generation boundaries."""
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
        raise ScreenError("runtime ratio must be numeric")
    value = float(ratio)
    if not math.isfinite(value) or value < 0:
        raise ScreenError("runtime ratio must be finite and nonnegative")
    if value < 5.0:
        return "PASS"
    if value < 10.0:
        return "WARN"
    return "FAIL"


def promotion_order(record: Mapping[str, Any]) -> tuple[float, float, float, int, str]:
    """Return the exact frozen screen ordering key."""
    validate_result(record)
    if not record["valid"]:
        raise ScreenError("invalid fits cannot enter promotion ordering")
    return (
        _finite(record, "validation_primary_nll"),
        _finite(record, "validation_tail_score"),
        _finite(record, "validation_stability"),
        int(record["parameter_count"]),
        str(record["configuration_id"]),
    )


def select_promotions(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Select at most two valid configurations per pooling class.

    Runtime is a hard eligibility gate after the frozen validation ordering;
    it is not allowed to reorder configurations within the screen.
    """
    values = list(records)
    identities = [record.get("configuration_id") for record in values]
    if len(values) != 12 or set(identities) != set(CONFIGURATION_IDS):
        raise ScreenError("all 12 frozen configurations are required exactly once")
    if len(set(identities)) != 12:
        raise ScreenError("duplicate screen configuration")
    for record in values:
        validate_result(record)

    promotions: dict[str, list[str]] = {}
    ordering: dict[str, list[str]] = {}
    for pooling in POOLING_CLASSES:
        valid = [
            record
            for record in values
            if record["pooling_class"] == pooling and record["valid"]
        ]
        ranked = sorted(valid, key=promotion_order)
        ordering[pooling] = [str(record["configuration_id"]) for record in ranked]
        eligible = [record for record in ranked if runtime_class(record["runtime_ratio_max"]) != "FAIL"]
        promotions[pooling] = [
            str(record["configuration_id"]) for record in eligible[:2]
        ]

    promoted = [item for pooling in POOLING_CLASSES for item in promotions[pooling]]
    if not promoted:
        terminal = "HOLD-A10-GENERATION-RUNTIME" if any(record["valid"] for record in values) else "HOLD-A10-NO-VALID-NEURAL-FIT"
    else:
        terminal = "A10M5-PROMOTIONS-READY"
    return {
        "schema_version": 1,
        "screen_seed": 147031,
        "ordering": ordering,
        "promotions": promotions,
        "promoted_count": len(promoted),
        "terminal": terminal,
    }
