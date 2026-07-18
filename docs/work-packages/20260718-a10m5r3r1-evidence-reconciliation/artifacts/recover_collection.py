#!/usr/bin/env python3
"""Recover A10M5R3 publication from its authenticated raw collection."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
R3 = PACKAGE.parent / "20260718-a10m5r3-candidate-family-capacity-knee"
REPO = PACKAGE.parents[2]
PRIVATE = Path("/Users/roger/.cache/cligen-rs/a10m5r3-screen-r4")
RUN_STATE = PRIVATE / "private-state/runs/a10m5r3-screen-r4/private/state.json"
RAW_ROOT = PRIVATE / "private-state/runs/a10m5r3-screen-r4/private/quarantine/extracted"
PLAN = PRIVATE / "private/plan.json"
PROFILE = REPO / "research/a10/lemhi_toolkit/profiles/lemhi-v2.json"
DESTINATION = R3 / "artifacts/toolkit-recovered/evidence"
sys.path.insert(0, str(REPO))

from research.a10.lemhi_toolkit.hardening import project_evidence  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def main() -> None:
    state = json.loads(RUN_STATE.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    raw_receipt = state["raw_collected"]
    require(raw_receipt["record_type"] == "RAW_COLLECTED", "raw receipt type")
    require(state["run_state"] == "MATRIX_SETTLED", "parent terminal drift")

    expected = {row["logical_name"]: row for row in raw_receipt["files"]}
    actual_paths = {
        str(path.relative_to(RAW_ROOT)): path
        for path in RAW_ROOT.rglob("*")
        if path.is_file()
    }
    require(set(actual_paths) == set(expected), "raw evidence identity mismatch")

    original = plan["evidence_replacements"]
    require(
        original
        == [
            {
                "kind": "path",
                "token": "[REMOTE_RUN_ROOT]",
                "value": "/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/a10m5r3-screen-r4",
            }
        ],
        "unexpected parent projection defect",
    )
    replacements = [
        {
            "kind": "path",
            "token": "<REMOTE_RUN_ROOT>",
            "value": original[0]["value"],
        }
    ]
    forbidden = tuple(profile["forbidden_publication_substrings"])

    require(not DESTINATION.exists(), "recovered destination already exists")
    receipts = []
    published = []
    for logical, path in sorted(actual_paths.items()):
        raw = path.read_bytes()
        row = expected[logical]
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], f"raw hash: {logical}")
        projected, receipt = project_evidence(
            raw,
            media_type="application/json" if path.suffix == ".json" else "text/plain",
            replacements=replacements,
            forbidden=forbidden,
            raw_parent_sha256=row["sha256"],
        )
        target = DESTINATION / logical
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(projected)
        require(not any(value and value.encode("utf-8") in projected for value in forbidden), f"forbidden: {logical}")
        receipts.append({"logical_name": logical, **receipt})
        published.append({"logical_name": logical, "bytes": len(projected), "sha256": digest(projected)})

    atomic_json(R3 / "artifacts/toolkit-recovered/raw-collected.json", raw_receipt)
    atomic_json(R3 / "artifacts/toolkit-recovered/projection-receipts.json", receipts)
    atomic_json(
        R3 / "artifacts/toolkit-recovered/collection-recovery.json",
        {
            "schema_version": 1,
            "terminal": "A10M5R3R1-LOCAL-PROJECTION-RECOVERED",
            "parent_terminal": "SANITIZATION_FAILED",
            "parent_plan_id": raw_receipt["plan_id"],
            "raw_record_sha256": raw_receipt["record_sha256"],
            "sanitizer_version": "lemhi-evidence-projection-3",
            "defect": "invalid replacement token",
            "original_token": "[REMOTE_RUN_ROOT]",
            "corrected_token": "<REMOTE_RUN_ROOT>",
            "files": published,
        },
    )
    print(f"projected {len(published)} authenticated files")


if __name__ == "__main__":
    main()
