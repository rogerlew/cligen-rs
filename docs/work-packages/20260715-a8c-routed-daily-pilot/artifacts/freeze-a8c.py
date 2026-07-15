#!/usr/bin/env python3
"""Freeze A8c prospective inputs before any candidate climate generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
OUTPUT = ARTIFACTS / "pre-execution-freeze-v1.json"
SOURCE_COMMIT = "046eba3c8d4508c84522c6dbd7cec4d39f094563"
FILES = [
    "Cargo.lock",
    "Cargo.toml",
    "crates/cligen/Cargo.toml",
    "crates/cligen/src/daily.rs",
    "crates/cligen/src/fast_batch.rs",
    "crates/cligen/src/lib.rs",
    "crates/cligen/src/modes.rs",
    "crates/cligen/src/parquet_output.rs",
    "crates/cligen/src/profile.rs",
    "crates/cligen/src/provenance.rs",
    "crates/cligen/src/routed_precip.rs",
    "crates/cligen/src/runspec.rs",
    "crates/cligen/src/station/document_v2.rs",
    "crates/cligen/src/station/mod.rs",
    "crates/cligen/src/typed_output.rs",
    "crates/cligen/tests/a8c_routed_daily.rs",
    "docs/specifications/SPEC-A8C-ROUTED-DAILY.md",
    "docs/specifications/SPEC-GENERATION-PROFILES.md",
    "docs/specifications/SPEC-PROVENANCE.md",
    "docs/specifications/SPEC-RUNSPEC.md",
    "docs/specifications/SPEC-STATION-DOCUMENT.md",
    "docs/specifications/station-document.schema.json",
    "docs/specifications/station-document-v2.schema.json",
    "docs/specifications/provenance-v1.schema.json",
    "docs/specifications/runspec.schema.json",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/pilot-contract-v1.json",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/build-stations.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/execute-a8c.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/analyze-a8c.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/verify-a8c.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/freeze-a8c.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/runspecs/runspec-template-v1.yaml",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/runspecs/runspec-matrix-v1.json",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/package.md",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    forbidden = [
        ARTIFACTS / "execution-evidence-v1.json",
        ARTIFACTS / "a8c-analysis-v1.json",
        ARTIFACTS / "a8c-decision-v1.json",
    ]
    present = [str(path) for path in forbidden if path.exists()]
    if present:
        raise RuntimeError(f"candidate evidence already exists: {present}")
    station_files = sorted(
        str(path.relative_to(ROOT))
        for path in (ARTIFACTS / "stations").glob("*.station.json")
    )
    if len(station_files) != 6:
        raise RuntimeError("exactly six station documents are required")
    frozen = FILES + station_files
    value = {
        "candidate_output_accessed": False,
        "frozen_files_sha256": {
            relative: sha256(ROOT / relative) for relative in sorted(frozen)
        },
        "schema_version": 1,
        "source_commit": SOURCE_COMMIT,
        "status": "FROZEN-BEFORE-CANDIDATE-GENERATION",
    }
    OUTPUT.write_text(
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(sha256(OUTPUT))


if __name__ == "__main__":
    main()
