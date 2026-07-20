#!/usr/bin/env python3
"""Repair the R14 adapter/total parameter-count interface without model changes."""

from __future__ import annotations

CONTROL_PARAMETER_COUNT = 276927
EXPECTED_TOTALS = {
    "centered_location_ou": 278667,
    "centered_location_ou_smooth_climatology": 278747,
    "centered_location_and_scale_ou": 279819,
    "centered_location_and_scale_ou_smooth_climatology": 279899,
}


def repair(training: dict, candidate: str, adapter_count: int) -> dict:
    expected_total = EXPECTED_TOTALS[candidate]
    inherited_total = training.get("parameter_count")
    if adapter_count <= 0 or CONTROL_PARAMETER_COUNT + adapter_count != expected_total:
        raise RuntimeError("R14R2 adapter parameter-count identity drift")
    if training.get("candidate_adapter_parameter_count") != adapter_count:
        raise RuntimeError("R14 candidate adapter parameter-count drift")
    if inherited_total != expected_total:
        raise RuntimeError("R14 inherited total parameter-count drift")
    result = dict(training)
    result["parameter_count"] = adapter_count
    result["candidate_adapter_parameter_count"] = adapter_count
    result["total_parameter_count"] = expected_total
    result["parameter_accounting_interface"] = "adapter-only-parameter_count-plus-explicit-total"
    return result
