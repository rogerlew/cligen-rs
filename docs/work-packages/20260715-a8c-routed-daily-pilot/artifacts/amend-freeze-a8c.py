#!/usr/bin/env python3
"""Rebind A8c after amendment 001 and before any outcome is written."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
V1 = ARTIFACTS / "pre-execution-freeze-v1.json"
EXECUTION = ARTIFACTS / "execution-evidence-v1.json"
AMENDMENT = ARTIFACTS / "post-generation-pre-outcome-amendment-001.md"
OUTPUT = ARTIFACTS / "pre-analysis-freeze-v2.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    forbidden = [
        ARTIFACTS / "a8c-analysis-v1.json",
        ARTIFACTS / "a8c-decision-v1.json",
        ARTIFACTS / "findings.md",
    ]
    if any(path.exists() for path in forbidden):
        raise RuntimeError("scientific outcome artifacts already exist")
    prior = json.loads(V1.read_text(encoding="utf-8"))
    files = set(prior["frozen_files_sha256"])
    files.update(
        {
            str(AMENDMENT.relative_to(ROOT)),
            str(EXECUTION.relative_to(ROOT)),
            str(Path(__file__).resolve().relative_to(ROOT)),
        }
    )
    value = {
        "amendment_sha256": sha256(AMENDMENT),
        "candidate_output_generated": True,
        "execution_evidence_sha256": sha256(EXECUTION),
        "frozen_files_sha256": {
            relative: sha256(ROOT / relative) for relative in sorted(files)
        },
        "schema_version": 2,
        "scientific_outcome_accessed": False,
        "source_commit": prior["source_commit"],
        "status": "FROZEN-POST-GENERATION-BEFORE-OUTCOME",
        "supersedes_freeze_sha256": sha256(V1),
    }
    OUTPUT.write_text(
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(sha256(OUTPUT))


if __name__ == "__main__":
    main()
