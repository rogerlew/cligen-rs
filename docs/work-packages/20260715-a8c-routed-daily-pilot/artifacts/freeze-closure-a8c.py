#!/usr/bin/env python3
"""Bind the non-scientific A8c closure and retained evidence transport."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
OUTPUT = ARTIFACTS / "closure-manifest-v1.json"
FILES = [
    ".gitattributes",
    "crates/cligen/schemas/provenance-v1.schema.json",
    "crates/cligen/schemas/quality-report-s2-m3.schema.json",
    "crates/cligen/src/quality/mod.rs",
    "crates/cligen/src/quality/report.rs",
    "crates/cligen/src/runspec.rs",
    "crates/cligen/tests/a8c_routed_daily.rs",
    "docs/ROADMAP.md",
    "docs/specifications/README.md",
    "docs/specifications/SPEC-A8C-ROUTED-DAILY.md",
    "docs/specifications/SPEC-QUALITY-REPORT.md",
    "docs/specifications/quality-report-s2-m3.schema.json",
    "docs/work-packages/README.md",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/package.md",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/a8c-retained-streams-v1.tar.gz",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/analyze-a8c.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/archive-a8c-evidence.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/retained-streams-manifest-v1.json",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/verify-a8c.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    decision = json.loads((ARTIFACTS / "a8c-decision-v1.json").read_text(encoding="utf-8"))
    if decision["terminal_decision"] != "STOP-A8-ROUTED-DAILY":
        raise RuntimeError("closure terminal mismatch")
    value = {
        "closed_files_sha256": {
            relative: sha256(ROOT / relative) for relative in sorted(FILES)
        },
        "decision_sha256": sha256(ARTIFACTS / "a8c-decision-v1.json"),
        "pre_analysis_freeze_sha256": sha256(ARTIFACTS / "pre-analysis-freeze-v2.json"),
        "schema_version": 1,
        "status": "CLOSED-AFTER-STOP-A8-ROUTED-DAILY",
    }
    OUTPUT.write_text(
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(sha256(OUTPUT))


if __name__ == "__main__":
    main()
