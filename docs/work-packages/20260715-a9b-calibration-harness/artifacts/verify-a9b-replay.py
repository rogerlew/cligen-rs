#!/usr/bin/env python3
"""Replay all A9b fixtures and freeze exact evidence-byte identity."""

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from research.a9_harness.canonical import write_canonical
from research.a9_harness.fixtures import FixtureRunner


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    generated = ARTIFACTS / "generated"
    with tempfile.TemporaryDirectory() as temporary:
        replay = Path(temporary)
        FixtureRunner(ROOT).write_evidence(replay)
        comparisons = []
        for replay_path in sorted(replay.glob("*.json")):
            original = generated / replay_path.name
            original_hash = digest(original)
            replay_hash = digest(replay_path)
            comparisons.append(
                {
                    "path": replay_path.name,
                    "original_sha256": original_hash,
                    "replay_sha256": replay_hash,
                    "byte_identical": original.read_bytes() == replay_path.read_bytes(),
                }
            )
    if len(comparisons) != 5 or not all(item["byte_identical"] for item in comparisons):
        raise SystemExit("fixture replay differs")
    record = {
        "schema_version": 1,
        "replay_id": "a9b-full-fixture-replay-v1",
        "files_replayed": len(comparisons),
        "byte_identical": True,
        "comparisons": comparisons,
        "observed_target_access": False,
    }
    write_canonical(generated / "determinism-replay-v1.json", record)
    print(f"replayed {len(comparisons)} evidence files byte-identically")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

