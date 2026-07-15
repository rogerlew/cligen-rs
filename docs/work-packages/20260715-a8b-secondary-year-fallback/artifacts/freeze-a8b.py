#!/usr/bin/env python3
"""Freeze A8b methods before annual aggregation or candidate fitting."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
FROZEN_PATHS = (
    "docs/work-packages/20260715-a8b-secondary-year-fallback/artifacts/design.md",
    "docs/work-packages/20260715-a8b-secondary-year-fallback/artifacts/feasibility-contract-v1.json",
    "docs/work-packages/20260715-a8b-secondary-year-fallback/artifacts/analyze-a8b.py",
    "docs/work-packages/20260715-a8b-secondary-year-fallback/artifacts/verify-a8b.py",
    "docs/work-packages/20260715-a8b-secondary-year-fallback/artifacts/freeze-a8b.py",
)
OUTCOMES = (
    "a8b-coefficients-v1.json",
    "a8b-analysis-v1.json",
    "a8b-decision-v1.json",
    "findings.md",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def main() -> None:
    output = ARTIFACTS / "pre-analysis-freeze-v1.json"
    if output.exists() or any((ARTIFACTS / name).exists() for name in OUTCOMES):
        raise SystemExit("refusing to freeze after A8b candidate output access")
    contract = load_json(ARTIFACTS / "feasibility-contract-v1.json")
    for entry in contract["inputs"].values():
        if sha256((REPO / entry["path"]).read_bytes()) != entry["sha256"]:
            raise SystemExit(f"input mismatch: {entry['path']}")
    parent_contract = load_json(REPO / contract["inputs"]["a8a_analysis_contract"]["path"])
    for entry in parent_contract["inputs"].values():
        if sha256((REPO / entry["path"]).read_bytes()) != entry["sha256"]:
            raise SystemExit(f"nested A8a input mismatch: {entry['path']}")
    parent_freeze = load_json(REPO / contract["inputs"]["a8a_freeze"]["path"])
    for relative, expected in parent_freeze["frozen_files_sha256"].items():
        if sha256((REPO / relative).read_bytes()) != expected:
            raise SystemExit(f"A8a frozen file mismatch: {relative}")
    parent_analysis = load_json(REPO / contract["inputs"]["a8a_analysis"]["path"])
    parent_decision = load_json(REPO / contract["inputs"]["a8a_decision"]["path"])
    development = sorted(
        entry["station_id"]
        for entry in parent_analysis["station_results"]
        if not entry["confirmation"] and entry["classification"] == "legacy_daily_fallback"
    )
    heldout = sorted(
        entry["station_id"]
        for entry in parent_analysis["station_results"]
        if entry["confirmation"] and entry["classification"] == "legacy_daily_fallback"
    )
    if parent_decision["terminal"] != contract["parent_required_terminal"]:
        raise SystemExit("A8a terminal does not authorize A8b")
    if not all(parent_decision["guards"].values()):
        raise SystemExit("A8a guard failure")
    if development != contract["corpus"]["expected_development_station_ids"]:
        raise SystemExit("A8a development fallback identity mismatch")
    if heldout != contract["corpus"]["expected_heldout_station_ids"]:
        raise SystemExit("A8a heldout fallback identity mismatch")
    a5f0 = load_json(REPO / contract["inputs"]["a5f0_decision"]["path"])
    if a5f0["decision"] != "RETIRE-SCALAR-IID-MECHANISM":
        raise SystemExit("A5f0 retirement boundary mismatch")
    alternatives = [entry["candidate_id"] for entry in contract["alternatives"]]
    if alternatives != [
        "legacy_daily_only_v1",
        "bounded_eof2_copula_ar1_reallocation_v1",
    ]:
        raise SystemExit("alternative set mismatch")
    if (
        subprocess.run(
            ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
            cwd=REPO,
            check=False,
        ).returncode
        != 0
    ):
        raise SystemExit("production crates changed after source boundary")
    value = {
        "a8a_parent_terminal": parent_decision["terminal"],
        "a8b_candidate_outputs_present_at_freeze": False,
        "frozen_files_sha256": {
            relative: sha256((REPO / relative).read_bytes()) for relative in FROZEN_PATHS
        },
        "input_files_sha256": {
            entry["path"]: entry["sha256"] for entry in contract["inputs"].values()
        },
        "method_boundary": (
            "Exact parent classes, corpus, alternatives, fit, pooled EOF rank, variance "
            "budget, held-out metrics, thresholds, RNG ownership, and terminal priority "
            "frozen before any A8b annual aggregate or candidate coefficient was computed"
        ),
        "schema_version": 1,
        "source_commit": contract["source_commit"],
        "status": "FROZEN-BEFORE-A8B-CANDIDATE-FIT",
    }
    output.write_bytes(canonical_json_bytes(value))
    print(sha256(output.read_bytes()))


if __name__ == "__main__":
    main()
