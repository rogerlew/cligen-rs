#!/usr/bin/env python3
"""Verify the zero-allocation A10M5R3R1 evidence reconciliation."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
R3 = PACKAGE.parent / "20260718-a10m5r3-candidate-family-capacity-knee"
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


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object: {path}")
    return value


def main() -> None:
    require("HOLD-A10-RESOURCE-BOUND" in (R3 / "package.md").read_text(), "parent hold absent")

    results = load(R3 / "artifacts/screen-results.json")
    family_rows = results["family_rows"]
    capacity_rows = results["capacity_rows"]
    frontier_rows = results["frontier_rows"]
    require(isinstance(family_rows, list) and len(family_rows) == len(FAMILIES) * len(SEEDS), "family rows")
    require(isinstance(capacity_rows, list) and len(capacity_rows) == len(CAPACITY_LADDER), "capacity rows")
    require(isinstance(frontier_rows, list) and len(frontier_rows) == 4, "frontier rows")

    family = select_family(family_rows)
    capacity = select_capacity(capacity_rows, str(family["winner"]))
    pair = [str(value) for value in capacity["pair"]]
    pair_rows = [
        row
        for row in capacity_rows + frontier_rows
        if row.get("capacity_id") in pair and row.get("training_seed") in SEEDS
    ]
    validation = validate_pair(pair_rows, str(family["winner"]), pair)
    require(validation["ready"] is True, "pair stability")
    require(all(float(row["runtime_ratio_max"]) < 10.0 for row in pair_rows), "pair runtime")
    require(load(R3 / "artifacts/family-selection.json") == family, "family replay")
    require(load(R3 / "artifacts/capacity-selection.json") == capacity, "capacity replay")

    receipts = [load(path) for path in sorted((R3 / "artifacts/toolkit-recovered").glob("job-*.json"))]
    expected_roles = {
        *(f"family-{short}-s{seed}" for short in ("lognormal", "gamma", "splice") for seed in SEEDS),
        *(f"capacity-p{slot}-s147031" for slot in range(5)),
        *(f"frontier-k{slot}-s{seed}" for slot in range(2) for seed in SEEDS[1:]),
    }
    require(len(receipts) == 18, "accepted receipt count")
    require({receipt["job_role"] for receipt in receipts} == expected_roles, "accepted role identity")
    require(all(receipt["attempt_index"] == 0 for receipt in receipts), "accepted attempt identity")
    require(all(receipt["passed"] is True for receipt in receipts), "accepted job failure")
    require(all(receipt["source_commit"] == "47963a9" for receipt in receipts), "accepted source drift")

    failed = [load(path) for path in sorted((R3 / "artifacts/failed-lineages").glob("r[23]/job-*.json"))]
    require(len(failed) == 11, "failed-lineage receipt count")
    require(sum(1 for receipt in failed if receipt["passed"] is False) == 2, "failed-lineage failures")
    require(all(receipt["run_id"] != "a10m5r3-screen-r4" for receipt in failed), "lineage overlap")
    require(load(R3 / "artifacts/failed-lineages/r1/abort.json")["terminal"] == "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION", "r1 abort")
    all_receipts = receipts + failed
    require(sum(receipt["result"]["actual_gpu_seconds"] for receipt in all_receipts) == 10_418, "elapsed accounting")
    require(sum(receipt["result"]["actual_gpu_minutes"] for receipt in all_receipts) == 188, "rounded accounting")

    collection = load(R3 / "artifacts/toolkit-recovered/collection-recovery.json")
    cleanup = load(R3 / "artifacts/toolkit-recovered/cleanup-recovery.json")
    raw = load(R3 / "artifacts/toolkit-recovered/raw-collected.json")
    projections = json.loads((R3 / "artifacts/toolkit-recovered/projection-receipts.json").read_text())
    require(isinstance(projections, list) and len(projections) == 239, "projection receipt count")
    raw_hashes = {row["logical_name"]: row["sha256"] for row in raw["files"]}
    require({row["logical_name"] for row in projections} == set(raw_hashes), "projection identity")
    require(all(row["raw_parent_sha256"] == raw_hashes[row["logical_name"]] for row in projections), "projection parent hash")
    recovered = R3 / "artifacts/toolkit-recovered/evidence"
    published = {row["logical_name"]: row for row in collection["files"]}
    require(set(published) == set(raw_hashes), "published identity")
    forbidden = (b"rogerlew.ui", b"/Users/roger", b"/ceph/home/")
    for logical, row in published.items():
        data = (recovered / logical).read_bytes()
        require(len(data) == row["bytes"], f"published bytes: {logical}")
        require(hashlib.sha256(data).hexdigest() == row["sha256"], f"published hash: {logical}")
        require(not any(value in data for value in forbidden), f"forbidden value: {logical}")
    require(collection["parent_terminal"] == "SANITIZATION_FAILED", "parent terminal")
    require(collection["sanitizer_version"] == "lemhi-evidence-projection-3", "sanitizer drift")
    require(cleanup["remote_absent"] is True, "accepted durable cleanup")
    require(cleanup["toolkit_close"] is False, "parent close was relabeled")
    print("A10M5R3R1-CAPACITY-PAIR-READY")


if __name__ == "__main__":
    main()
