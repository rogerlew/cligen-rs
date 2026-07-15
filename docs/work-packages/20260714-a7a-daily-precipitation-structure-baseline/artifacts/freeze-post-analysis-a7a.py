#!/usr/bin/env python3
"""Bind the bounded A7a post-analysis renderer correction and outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
OUTPUT = PACKAGE / "post-analysis-freeze-v1.json"
PRE_FREEZE = PACKAGE / "pre-analysis-freeze-v4.json"
AMENDMENT = PACKAGE / "post-analysis-amendment-004.md"
EXPECTED = {
    "a7a-analysis-v1.json": "425ce817f0167d3c65df57b8fa6f77d333c94a7fa59bfa7eef771322f99366a0",
    "a7a-decision-v1.json": "4f82ab9b61942bced8ef546018a02e561e443df515cf8a1ba4eeeaab3ab38b15",
}
SOURCES = (
    "analyze-a7a.py",
    "verify-a7a.py",
    "freeze-post-analysis-a7a.py",
    "post-analysis-amendment-004.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    for name, expected in EXPECTED.items():
        actual = sha256(PACKAGE / name)
        if actual != expected:
            raise ValueError(f"post-correction output changed: {name}: {actual}")
    findings = PACKAGE / "findings.md"
    if not findings.is_file():
        raise ValueError("corrected findings are missing")
    value = {
        "amendment": {
            "path": AMENDMENT.name,
            "sha256": sha256(AMENDMENT),
        },
        "current_sources": {name: sha256(PACKAGE / name) for name in SOURCES},
        "outputs": {
            name: sha256(PACKAGE / name)
            for name in (*EXPECTED, "findings.md")
        },
        "post_analysis_freeze_schema_version": 1,
        "prior_freeze": {
            "path": PRE_FREEZE.name,
            "sha256": sha256(PRE_FREEZE),
        },
        "superseded_source_hashes": {
            name: json.loads(PRE_FREEZE.read_text())["frozen_sources"][name]
            for name in ("analyze-a7a.py", "verify-a7a.py")
        },
    }
    OUTPUT.write_text(
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

