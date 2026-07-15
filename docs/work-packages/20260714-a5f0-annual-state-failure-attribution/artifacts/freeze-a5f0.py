#!/usr/bin/env python3
"""Freeze A5f0's derived-analysis sources and retained A5e0 inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE_COMMIT = "1ca40bbe006ed5d823d2dd8e373f720f20d60ba0"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, root: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"missing freeze input: {path}")
    return {
        "bytes": path.stat().st_size,
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path),
    }


def main() -> int:
    root = repo_root()
    package = root / "docs/work-packages/20260714-a5f0-annual-state-failure-attribution"
    artifacts = package / "artifacts"
    frozen_sources = [
        artifacts / "design.md",
        artifacts / "attribution-contract-v1.json",
        artifacts / "analyze-a5f0.py",
        artifacts / "verify-a5f0.py",
        artifacts / "freeze-a5f0.py",
    ]
    retained_inputs = [
        root
        / "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-analysis-v1.json",
        root
        / "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-campaign-evidence-v1.json",
        root
        / "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/a5e0-coefficients-v1.json",
        root / "target/a5e0/matrix-index-v1.json",
    ]
    value = {
        "freeze_schema": "a5f0_pre_analysis_freeze_v1",
        "frozen_sources": [artifact(path, root) for path in frozen_sources],
        "identity": {
            "freeze_scope": "derived attribution algorithm after A5e0 outcome exposure",
            "source_commit": SOURCE_COMMIT,
            "work_package": "20260714-a5f0-annual-state-failure-attribution",
        },
        "retained_inputs": [artifact(path, root) for path in retained_inputs],
        "status": "FROZEN-BEFORE-DERIVED-ATTRIBUTION",
    }
    output = artifacts / "pre-analysis-freeze-v1.json"
    output.write_text(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    print(output.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
