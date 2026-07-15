#!/usr/bin/env python3
"""Bind the reviewed A7a arithmetic corrections and corrected outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
OUTPUT = PACKAGE / "post-analysis-freeze-v2.json"
PRIOR_POST_FREEZE = PACKAGE / "post-analysis-freeze-v1.json"
AMENDMENT = PACKAGE / "post-analysis-amendment-005.md"
EXPECTED = {
    "a7a-analysis-v1.json": "45342c8763c3d079c81f8a9b3910882bdd82f2557dfb420a80d5a4bfefa2b1ad",
    "a7a-decision-v1.json": "c5aab286d5fffb8a61bb3bb50ac228f636d6da97f6e0880973f478073e0b1c0f",
    "findings.md": "4fb3cc87f70c690f26e20a14b4ef839e24c2d52c0bc4019a09be3ca3b2296f57",
}
SOURCES = (
    "analyze-a7a.py",
    "verify-a7a.py",
    "freeze-post-analysis-a7a-v2.py",
    "post-analysis-amendment-005.md",
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
            raise ValueError(f"review-corrected output changed: {name}: {actual}")
    prior = json.loads(PRIOR_POST_FREEZE.read_text(encoding="utf-8"))
    value = {
        "amendment": {
            "path": AMENDMENT.name,
            "sha256": sha256(AMENDMENT),
        },
        "current_sources": {name: sha256(PACKAGE / name) for name in SOURCES},
        "outputs": {name: sha256(PACKAGE / name) for name in EXPECTED},
        "post_analysis_freeze_schema_version": 2,
        "prior_outputs": prior["outputs"],
        "prior_post_freeze": {
            "path": PRIOR_POST_FREEZE.name,
            "sha256": sha256(PRIOR_POST_FREEZE),
        },
        "review_corrections": [
            "pooled Daymet-off station-horizon severity aggregation",
            "explicit extended-real zero-null severity policy",
            "observation-supported null component parity",
        ],
        "superseded_source_hashes": {
            name: prior["current_sources"][name]
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
