#!/usr/bin/env python3
"""Verify that the A9c4 pre-output contract is intact."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "docs/work-packages/20260715-a9c4-context-support-completeness"
ARTIFACTS = PACKAGE / "artifacts"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(name: str) -> dict:
    return json.loads((ARTIFACTS / name).read_text())


def main() -> None:
    dispatch = load("execution-dispatch-v1.json")
    predecessor = load("predecessor-manifest-v1.json")
    design = load("design-freeze-v1.json")
    assert dispatch["branch"] == dispatch["target_branch"] == "main"
    assert dispatch["source_commit"] == design["source_commit"]
    assert dispatch["execution_authorized"] is True
    assert dispatch["commit_or_push_authorized"] is False
    assert design["confirmation_series_access_allowed"] is False
    assert design["context_correction"]["realized_output_clipping_or_repair"] is False
    completeness = design["evidence_completeness"]
    assert completeness["candidate_blind_mask_inputs"] == ["observed", "faithful"]
    assert completeness["mask_freeze_precedes_corrected_candidate_output"] is True
    assert completeness["favorable_missing_value"] is False
    for row in predecessor["files"]:
        path = ROOT / row["path"]
        assert path.is_file(), row["path"]
        assert sha256(path) == row["sha256"], row["path"]
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", dispatch["source_commit"], "--", "crates"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert not changed, changed
    print(
        f"A9c4 scaffold verified: {len(predecessor['files'])} predecessors; "
        "candidate-blind mask and structural-support correction frozen"
    )


if __name__ == "__main__":
    main()
