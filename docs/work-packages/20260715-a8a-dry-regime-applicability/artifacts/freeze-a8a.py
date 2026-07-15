#!/usr/bin/env python3
"""Freeze A8a selection and analysis methods before new daily-data access."""

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
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/acquire-a8a.py",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/analysis-contract-v1.json",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/analyze-a8a.py",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/freeze-a8a.py",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/inventory-stations.py",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/select-panel.py",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/selected-parameters-v1.tar.gz",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/selection-contract-v1.json",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/station-inventory-v1.json",
    "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/verify-a8a.py",
    "references/observed/a8a-v1/README.md",
    "references/observed/a8a-v1/THIRD_PARTY_DATA_NOTICE.md",
)
OUTCOMES = (
    "source-manifest-v1.json",
    "a8a-analysis-v1.json",
    "a8a-decision-v1.json",
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
        raise SystemExit("refusing to freeze after daily-source or outcome access")
    archive_root = REPO / "references/observed/a8a-v1"
    if any(archive_root.rglob("*.gz")):
        raise SystemExit("refusing to freeze after a daily/metadata source archive exists")
    contract = load_json(ARTIFACTS / "analysis-contract-v1.json")
    panel = load_json(ARTIFACTS / "panel-v1.json")
    if panel["daily_data_accessed"] is not False:
        raise SystemExit("panel does not preserve the metadata-only boundary")
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
    value = {
        "daily_source_files_present_at_freeze": False,
        "frozen_files_sha256": {
            relative: sha256((REPO / relative).read_bytes()) for relative in FROZEN_PATHS
        },
        "method_boundary": (
            "Exact panel, sources, classifier, bootstrap, analytic mechanism, stability, "
            "and terminal rules frozen before any new Daymet/GHCN record access"
        ),
        "schema_version": 1,
        "source_commit": contract["source_commit"],
        "status": "FROZEN-BEFORE-NEW-DAILY-DATA",
    }
    output.write_bytes(canonical_json_bytes(value))
    print(sha256(output.read_bytes()))


if __name__ == "__main__":
    main()
