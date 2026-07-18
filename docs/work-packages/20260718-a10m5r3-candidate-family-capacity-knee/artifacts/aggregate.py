#!/usr/bin/env python3
"""Aggregate the collected A10M5R3 matrix and replay frozen selectors."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(REPO))

from research.a10.m5r3_contract import (  # noqa: E402
    SEEDS,
    select_capacity,
    select_family,
    validate_pair,
)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def atomic_json(path: Path, value: object) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def main() -> None:
    evidence = PACKAGE / "artifacts/toolkit-recovered/evidence"
    rows = [load_json(path) for path in sorted((evidence / "results").glob("*/row.json"))]
    family_rows = [row for row in rows if row.get("phase") == "family"]
    capacity_rows = [row for row in rows if row.get("phase") == "capacity"]
    frontier_rows = [row for row in rows if row.get("phase") == "frontier"]

    family = select_family(family_rows)
    capacity = select_capacity(capacity_rows, str(family["winner"]))
    pair = [str(value) for value in capacity["pair"]]
    pair_rows = [
        row
        for row in capacity_rows + frontier_rows
        if row.get("capacity_id") in pair and row.get("training_seed") in SEEDS
    ]
    validation = validate_pair(pair_rows, str(family["winner"]), pair)
    validation["retained_runtime_boundary_pass"] = all(
        float(row["runtime_ratio_max"]) < 10.0 for row in pair_rows
    )
    if not validation["retained_runtime_boundary_pass"]:
        validation["ready"] = False
        validation["disposition"] = "HOLD-A10-GENERATION-RUNTIME"

    atomic_json(
        PACKAGE / "artifacts/screen-results.json",
        {
            "schema_version": 1,
            "family_rows": family_rows,
            "capacity_rows": capacity_rows,
            "frontier_rows": frontier_rows,
        },
    )
    atomic_json(PACKAGE / "artifacts/family-selection.json", family)
    atomic_json(PACKAGE / "artifacts/capacity-selection.json", capacity)
    atomic_json(PACKAGE / "artifacts/pair-validation.json", validation)
    print(validation["disposition"])


if __name__ == "__main__":
    main()
