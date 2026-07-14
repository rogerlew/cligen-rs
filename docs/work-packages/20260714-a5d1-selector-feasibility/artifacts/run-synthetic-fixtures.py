#!/usr/bin/env python3
"""Execute the prospectively authored A5d1 synthetic failure fixtures."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from a5d1_common import PACKAGE, canonical_sha256, load_json, write_json


FIXTURES = PACKAGE / "synthetic-feasibility-fixtures-v1.json"
RESULTS = PACKAGE / "synthetic-feasibility-fixture-results-v1.json"


def outcome(row: dict) -> str:
    kind = row["kind"]
    if kind == "weights":
        valid = (
            abs(math.fsum(row["weights"]) - 1.0) <= 1e-12
            and min(row["weights"]) >= 0.0
            and max(row["weights"]) <= row["max_weight"]
        )
        return "pass" if valid else "infeasible"
    if kind == "tolerance":
        return "pass" if row["residual"] <= row["tolerance"] else "reject"
    if kind == "calendar":
        return "exhausted" if row["target_has_leap_year"] and row["available_leap_blocks"] == 0 else "pass"
    if kind == "reuse":
        capacity = row["pool_size"] * row["max_reuse"]
        return "exhausted" if capacity < row["target_years"] else "pass"
    if kind == "iteration":
        return "bounded_failure" if row["iterations_allowed"] == 0 else "pass"
    if kind == "certificate":
        actual = hashlib.sha256(
            json.dumps(row["payload"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return "pass" if actual == row["certificate_sha256"] else "reject"
    if kind == "centered":
        variance = row["raw_second"] - row["fixed_mean"] ** 2
        return "pass" if abs(variance - row["target_variance"]) <= 1e-12 else "reject"
    if kind == "zero_weight":
        return (
            "reject"
            if any(row["weights"][index] <= 1e-12 for index in row["selected"])
            else "pass"
        )
    if kind == "boundary":
        directional = {tuple(pair) for pair in row["states"]}
        return "pass" if len(directional) == 4 else "reject"
    if kind == "render":
        return "pass" if row["hundred"].startswith(row["thirty"]) else "reject"
    if kind == "january_transition":
        denominator = row["within_denominator"] + row["boundary_denominator"]
        numerator = row["within_numerator"] + row["boundary_numerator"]
        if denominator == 0:
            return "reject"
        actual = numerator / denominator
        lower = max(0.0, row["target"] - row["tolerance"])
        upper = min(1.0, row["target"] + row["tolerance"])
        return "pass" if lower <= actual <= upper else "reject"
    raise ValueError(f"unknown fixture kind: {kind}")


def main() -> None:
    fixtures = load_json(FIXTURES)
    rows = []
    for fixture in fixtures["fixtures"]:
        actual = outcome(fixture)
        rows.append(
            {
                "id": fixture["id"],
                "expected": fixture["expected"],
                "actual": actual,
                "pass": actual == fixture["expected"],
            }
        )
    value = {
        "fixture_results_schema_version": 1,
        "fixture_identity_sha256": canonical_sha256(fixtures),
        "count": len(rows),
        "pass_count": sum(row["pass"] for row in rows),
        "records": rows,
    }
    write_json(RESULTS, value)
    if value["pass_count"] != value["count"]:
        raise SystemExit("A5d1 synthetic fixtures: FAIL")
    print(f"A5d1 synthetic fixtures: PASS ({value['count']}/{value['count']})")


if __name__ == "__main__":
    main()
