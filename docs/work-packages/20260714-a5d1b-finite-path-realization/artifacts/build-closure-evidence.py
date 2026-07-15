#!/usr/bin/env python3
"""Build the hash-bound terminal closure record for A5d1b."""

from __future__ import annotations

import sys

from a5d1b_common import ARTIFACTS, ROOT, identity, sha256, write_json


CLOSURE = ARTIFACTS / "closure-evidence-v1.json"
REPORT = ROOT / "docs/reports/a5d1b-finite-path-realization-report.md"
REPORT_MANIFEST = REPORT.with_suffix(".manifest.json")
PACKAGE = ARTIFACTS.parent / "package.md"
FILES = [
    ROOT / ".gitattributes",
    PACKAGE,
    ARTIFACTS / "build-closure-evidence.py",
    ARTIFACTS / "finite-path-realization-contract-v1.json",
    ARTIFACTS / "finite-path-realization-contract-v1.schema.json",
    ARTIFACTS / "evidence-lock-inputs-v1.json",
    ARTIFACTS / "pre-outcome-freeze-v1.json",
    ARTIFACTS / "pre-outcome-freeze-amendment-001.json",
    ARTIFACTS / "pre-outcome-freeze-v2.json",
    ARTIFACTS / "pre-outcome-freeze-amendment-002.json",
    ARTIFACTS / "pre-outcome-freeze-v3.json",
    ARTIFACTS / "post-outcome-correction-amendment-003.json",
    ARTIFACTS / "corrected-execution-freeze-v4.json",
    ARTIFACTS / "post-outcome-correction-amendment-004.json",
    ARTIFACTS / "corrected-execution-freeze-v5.json",
    ARTIFACTS / "inherited-path-diagnostics-v1.json",
    ARTIFACTS / "count-feasibility-results-v1.json",
    ARTIFACTS / "count-witness-replay-audit-v1.json",
    ARTIFACTS / "ordered-path-results-v1.json",
    ARTIFACTS / "detailed-evidence-manifest-v1.json",
    ARTIFACTS / "detailed-evidence-v1.tar.gz",
    ARTIFACTS / "a5d1b-results-v1.json",
    ARTIFACTS / "a5d1b-decision-v1.json",
    ARTIFACTS / "resource-audit-v1.json",
    ARTIFACTS / "next-action-disposition-v1.json",
    ARTIFACTS / "review.md",
    ARTIFACTS / "gate-results.md",
    REPORT,
    REPORT_MANIFEST,
    ROOT / "docs/ROADMAP.md",
    ROOT / "docs/work-packages/README.md",
    ROOT / "docs/reports/README.md",
]


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: build-closure-evidence.py")
    missing = [str(path) for path in FILES if not path.is_file()]
    if missing:
        raise ValueError(f"closure input missing: {missing}")
    value = {
        "closure_evidence_schema_version": 1,
        "status": "EXECUTED-HOLD-COUNT-SEARCH-BOUNDED",
        "development_only": True,
        "source_commit": "08db78cb5365b2f961599421826a600dae1c765a",
        "branch": "main",
        "report_sha256": sha256(REPORT),
        "report_manifest_sha256": sha256(REPORT_MANIFEST),
        "review_sha256": sha256(ARTIFACTS / "review.md"),
        "gate_results_sha256": sha256(ARTIFACTS / "gate-results.md"),
        "results_sha256": sha256(ARTIFACTS / "a5d1b-results-v1.json"),
        "decision_sha256": sha256(ARTIFACTS / "a5d1b-decision-v1.json"),
        "files": [identity(path) for path in FILES],
        "lfs_archives": [
            identity(ARTIFACTS / "detailed-evidence-v1.tar.gz"),
            identity(ARTIFACTS / "invalidated-v3-detailed-evidence-v1.tar.gz"),
            identity(ARTIFACTS / "invalidated-v4-count-certificates-v1.tar.gz"),
        ],
        "confirmation_objects_accessed": 0,
        "production_source_changes": 0,
        "public_surface_changes": 0,
        "coverage_crap_applicable": False,
    }
    write_json(CLOSURE, value)
    print(f"A5d1b closure evidence: PASS ({len(FILES)} bound files)")


if __name__ == "__main__":
    main()
