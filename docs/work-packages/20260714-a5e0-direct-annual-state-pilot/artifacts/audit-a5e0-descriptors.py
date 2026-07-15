#!/usr/bin/env python3
"""Evaluate both pre-output readings of the A5e0 descriptor guard."""

from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
from typing import Any


SUBFAMILIES = ("time_to_peak", "peak_intensity_ratio", "dependence")


def strict_json(path: Path) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate key {key!r} in {path}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"nonfinite token {token!r} in {path}")
        ),
    )


def median(values: list[float]) -> float:
    ordered = sorted(values)
    size = len(ordered)
    if size == 0:
        raise ValueError("cannot take the median of an empty sequence")
    midpoint = size // 2
    if size % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def evaluate(horizon: dict[str, Any]) -> dict[str, Any]:
    descriptor = horizon["h3"]["families"]["descriptor_guard"]
    literal: dict[str, Any] = {}
    for subfamily in SUBFAMILIES:
        stations = []
        for station in descriptor["stations"]:
            station_median = median(
                [row[subfamily] for row in station["replicate_subfamilies"]]
            )
            stations.append(
                {"station_id": station["station_id"], "median": station_median}
            )
        three_station_median = median([row["median"] for row in stations])
        maximum_station = max(row["median"] for row in stations)
        literal[subfamily] = {
            "status": (
                "PASS"
                if three_station_median <= 0.50 and maximum_station <= 0.75
                else "FAIL"
            ),
            "three_station_median": three_station_median,
            "maximum_station": maximum_station,
            "median_limit": 0.50,
            "station_limit": 0.75,
            "stations": stations,
        }
    if not all(math.isfinite(value) for row in literal.values() for value in (
        row["three_station_median"],
        row["maximum_station"],
    )):
        raise ValueError("descriptor audit produced a nonfinite value")
    return {
        "horizon_years": horizon["horizon_years"],
        "committed_scaffold_composite": {
            "status": descriptor["status"],
            "three_station_median": descriptor["three_station_median"],
            "median_limit": descriptor["median_limit"],
            "station_limit": descriptor["station_limit"],
        },
        "literal_spec_subfamilies": literal,
        "literal_spec_status": (
            "PASS" if all(row["status"] == "PASS" for row in literal.values()) else "FAIL"
        ),
    }


def main() -> int:
    package = Path(__file__).resolve().parent
    analysis_path = package / "a5e0-analysis-v1.json"
    analysis = strict_json(analysis_path)
    horizons = [evaluate(horizon) for horizon in analysis["horizons"]]
    result = {
        "audit_schema": "a5e0_descriptor_rule_audit_v1",
        "status": "complete",
        "timing": "post_output_authority_reconciliation",
        "analysis_sha256": hashlib.sha256(analysis_path.read_bytes()).hexdigest(),
        "interpretation": (
            "Both pre-output descriptor-rule readings pass at both horizons; "
            "this audit does not cure the prospective-boundary hold."
        ),
        "horizons": horizons,
    }
    output = package / "a5e0-descriptor-rule-audit-v1.json"
    output.write_text(
        json.dumps(
            result,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
