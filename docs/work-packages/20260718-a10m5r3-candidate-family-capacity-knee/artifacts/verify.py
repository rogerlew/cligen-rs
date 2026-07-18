#!/usr/bin/env python3
"""Fail-closed terminal verifier for A10M5R3."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(REPO))

from research.a10.m5r3_contract import (  # noqa: E402
    CAPACITY_LADDER,
    FAMILIES,
    SEEDS,
    select_capacity,
    select_family,
    validate_pair,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object: {path}")
    return value


def main() -> None:
    for path in (PACKAGE / "artifacts/jobs").glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ast.parse((PACKAGE / "artifacts/aggregate.py").read_text(encoding="utf-8"))

    results_path = PACKAGE / "artifacts/screen-results.json"
    if not results_path.exists():
        print("A10M5R3 verifier: prospective PASS")
        return

    results = load_json(results_path)
    family_rows = results["family_rows"]
    capacity_rows = results["capacity_rows"]
    frontier_rows = results["frontier_rows"]
    require(isinstance(family_rows, list) and len(family_rows) == len(FAMILIES) * len(SEEDS), "family row count")
    require(isinstance(capacity_rows, list) and len(capacity_rows) == len(CAPACITY_LADDER), "capacity row count")
    require(isinstance(frontier_rows, list) and len(frontier_rows) == 4, "frontier row count")

    family = select_family(family_rows)
    capacity = select_capacity(capacity_rows, str(family["winner"]))
    pair = [str(value) for value in capacity["pair"]]
    pair_rows = [
        row
        for row in capacity_rows + frontier_rows
        if row.get("capacity_id") in pair and row.get("training_seed") in SEEDS
    ]
    validation = validate_pair(pair_rows, str(family["winner"]), pair)

    require(load_json(PACKAGE / "artifacts/family-selection.json") == family, "family selection drift")
    require(load_json(PACKAGE / "artifacts/capacity-selection.json") == capacity, "capacity selection drift")
    recorded = load_json(PACKAGE / "artifacts/pair-validation.json")
    require(recorded["summaries"] == validation["summaries"], "pair validation drift")
    require(validation["ready"] is True, "retained pair is not seed-stable")
    require(all(float(row["runtime_ratio_max"]) < 10.0 for row in pair_rows), "retained runtime boundary")
    require(all(row.get("valid") is True and all(row["gates"].values()) for row in pair_rows), "retained row gate failure")

    toolkit = PACKAGE / "artifacts/toolkit-recovered"
    require(load_json(toolkit / "cleanup-recovery.json")["remote_absent"] is True, "durable cleanup")
    require(
        load_json(toolkit / "collection-recovery.json")["parent_terminal"]
        == "SANITIZATION_FAILED",
        "parent collection terminal",
    )
    print("A10M5R3 verifier: evidence PASS; package HOLD-A10-RESOURCE-BOUND")


if __name__ == "__main__":
    main()
