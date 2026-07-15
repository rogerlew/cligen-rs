#!/usr/bin/env python3
"""Post-result deterministic semantic replay of the frozen A5d1b count matrix."""

from __future__ import annotations

import importlib.util
import math
import sys
import time
from pathlib import Path

from a5d1b_common import (
    A5D1_CONTRACT,
    ARTIFACTS,
    CONTRACT,
    COUNT_RESULTS,
    ROOT,
    freeze_identity,
    load_json,
    station_ids,
    write_json,
)


SOLVER_PATH = ARTIFACTS / "solve-count-feasibility.py"
AUDIT = ARTIFACTS / "count-semantic-replay-audit-v1.json"
REPEAT_DIR = ROOT / "target/a5d1b-count-semantic-replay/counts"
IGNORED_KEYS = {"wall_seconds", "mip_gap", "mip_node_count"}


def load_solver():
    spec = importlib.util.spec_from_file_location("a5d1b_repeat_solver", SOLVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import frozen count solver")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compare(left, right, path: str, state: dict) -> None:
    if isinstance(left, dict) and isinstance(right, dict):
        left_keys = set(left) - IGNORED_KEYS
        right_keys = set(right) - IGNORED_KEYS
        if left_keys != right_keys:
            state["mismatches"].append(f"{path}: key mismatch")
            return
        for key in sorted(left_keys):
            compare(left[key], right[key], f"{path}.{key}", state)
        return
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            state["mismatches"].append(f"{path}: length mismatch")
            return
        for index, (a, b) in enumerate(zip(left, right)):
            compare(a, b, f"{path}[{index}]", state)
        return
    if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
        state["numeric_comparisons"] += 1
        difference = abs(float(left) - float(right))
        scale = max(abs(float(left)), abs(float(right)), 1.0)
        state["maximum_absolute_difference"] = max(state["maximum_absolute_difference"], difference)
        state["maximum_relative_difference"] = max(state["maximum_relative_difference"], difference / scale)
        if not math.isclose(float(left), float(right), rel_tol=2.0e-10, abs_tol=2.0e-10):
            state["mismatches"].append(f"{path}: {left!r} != {right!r}")
        return
    if left != right:
        state["mismatches"].append(f"{path}: {left!r} != {right!r}")


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: verify-count-semantic-replay.py")
    if AUDIT.exists():
        raise ValueError("semantic replay audit already exists")
    REPEAT_DIR.mkdir(parents=True, exist_ok=True)
    if any(REPEAT_DIR.iterdir()):
        raise ValueError("semantic replay target is not empty")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    a5d1_contract = load_json(A5D1_CONTRACT)
    published = load_json(COUNT_RESULTS)
    solver = load_solver()
    solver.COUNT_DIR = REPEAT_DIR
    published_index = {row["station_id"]: load_json(ROOT / row["certificate"]["path"]) for row in published["records"]}
    state = {
        "numeric_comparisons": 0,
        "maximum_absolute_difference": 0.0,
        "maximum_relative_difference": 0.0,
        "mismatches": [],
    }
    started = time.monotonic()
    station_summaries = []
    for station_id in station_ids():
        row = solver.solve_station(station_id, contract, a5d1_contract, freeze_sha256)
        repeat = load_json(ROOT / row["certificate"]["path"])
        before = len(state["mismatches"])
        compare(published_index[station_id], repeat, station_id, state)
        station_summaries.append(
            {
                "station_id": station_id,
                "published_count_pass": published_index[station_id]["count_pass"],
                "repeat_count_pass": repeat["count_pass"],
                "semantic_match": len(state["mismatches"]) == before,
            }
        )
    value = {
        "count_semantic_replay_audit_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "station_count": len(station_summaries),
        "semantic_match_count": sum(row["semantic_match"] for row in station_summaries),
        "numeric_comparisons": state["numeric_comparisons"],
        "maximum_absolute_difference": state["maximum_absolute_difference"],
        "maximum_relative_difference": state["maximum_relative_difference"],
        "mismatch_count": len(state["mismatches"]),
        "mismatches": state["mismatches"][:100],
        "stations": station_summaries,
        "wall_seconds": round(time.monotonic() - started, 6),
        "pass": len(state["mismatches"]) == 0,
    }
    write_json(AUDIT, value)
    if not value["pass"]:
        raise ValueError(f"count semantic replay mismatch: {value['mismatch_count']}")
    print(f"A5d1b count semantic replay: PASS ({value['semantic_match_count']}/17; {value['numeric_comparisons']} numeric comparisons)")


if __name__ == "__main__":
    main()

