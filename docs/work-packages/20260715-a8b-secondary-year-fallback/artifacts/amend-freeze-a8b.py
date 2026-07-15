#!/usr/bin/env python3
"""Bind A8b's bounded fail-closed reporting amendment."""

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
PRIOR_FREEZE_SHA256 = "b66f0c8d3788e0230db5958c301a7a4a68d2448d1bd871eb83676daf5bc9fdfc"
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
    output = ARTIFACTS / "pre-analysis-freeze-v2.json"
    if output.exists() or any((ARTIFACTS / name).exists() for name in OUTCOMES):
        raise SystemExit("refusing amendment after successor freeze or outcome artifact")
    prior_path = ARTIFACTS / "pre-analysis-freeze-v1.json"
    if sha256(prior_path.read_bytes()) != PRIOR_FREEZE_SHA256:
        raise SystemExit("prior freeze identity mismatch")
    prior = load_json(prior_path)
    amendment_path = ARTIFACTS / "pre-analysis-amendment-001.json"
    amendment = load_json(amendment_path)
    for relative, identities in amendment["amended_files"].items():
        if prior["frozen_files_sha256"][relative] != identities["original_sha256"]:
            raise SystemExit(f"original identity mismatch: {relative}")
        if sha256((REPO / relative).read_bytes()) != identities["amended_sha256"]:
            raise SystemExit(f"amended identity mismatch: {relative}")
    contract = load_json(ARTIFACTS / "feasibility-contract-v1.json")
    for entry in contract["inputs"].values():
        if sha256((REPO / entry["path"]).read_bytes()) != entry["sha256"]:
            raise SystemExit(f"input mismatch: {entry['path']}")
    if (
        subprocess.run(
            ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
            cwd=REPO,
            check=False,
        ).returncode
        != 0
    ):
        raise SystemExit("production crates changed after source boundary")
    frozen_paths = set(prior["frozen_files_sha256"])
    frozen_paths.update(
        {
            prior_path.relative_to(REPO).as_posix(),
            amendment_path.relative_to(REPO).as_posix(),
            Path(__file__).resolve().relative_to(REPO).as_posix(),
        }
    )
    value = {
        "a8a_parent_terminal": prior["a8a_parent_terminal"],
        "a8b_candidate_outputs_present_at_freeze": False,
        "amendments": [amendment["amendment_id"]],
        "fit_input_access_before_amendment": amendment["access_boundary"],
        "freeze_id": "a8b_pre_analysis_freeze_v2",
        "frozen_files_sha256": {
            relative: sha256((REPO / relative).read_bytes())
            for relative in sorted(frozen_paths)
        },
        "method_boundary": (
            "The v1 corpus, alternatives, fit, zero-scale failure, budgets, metrics, "
            "thresholds, RNG, and terminal priority remain unchanged; v2 only binds "
            "structured reporting of candidate infeasibility and the registered null."
        ),
        "prior_freeze": {
            "path": prior_path.relative_to(REPO).as_posix(),
            "sha256": PRIOR_FREEZE_SHA256,
        },
        "schema_version": 2,
        "source_commit": contract["source_commit"],
        "status": "FROZEN-BEFORE-A8B-CANDIDATE-FIT",
    }
    output.write_bytes(canonical_json_bytes(value))
    print(sha256(output.read_bytes()))


if __name__ == "__main__":
    main()
