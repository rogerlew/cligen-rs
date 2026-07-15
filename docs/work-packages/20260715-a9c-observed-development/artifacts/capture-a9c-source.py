#!/usr/bin/env python3
"""Capture exact A9c research implementation and contract identities."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy
import scipy


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().with_name("implementation-manifest-v1.json")
FILES = [
    ".gitattributes",
    "research/a9c/__init__.py",
    "research/a9c/data.py",
    "research/a9c/models.py",
    "research/a9c/nulls.py",
    "research/a9c/run.py",
    "research/a9c/requirements.txt",
    "research/a9c/tests/__init__.py",
    "research/a9c/tests/test_data.py",
    "research/a9c/tests/test_models.py",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/analyze-a9c-availability.py",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/capture-a9c-source.py",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/prepare-a9c-roles.py",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/verify-a9c.py",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/data-role-freeze-v1.json",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/campaign-freeze-v1.json",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/stage-survival-freeze-v1.json",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/schemas/alternating-renewal-marked-v1.config.schema.json",
    "docs/work-packages/20260715-a9c-observed-development/artifacts/schemas/latent-regime-marked-v1.config.schema.json"
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    value = {
        "candidate_development_scores_accessed": False,
        "candidate_implementation_status": "research implementations completed through five immutable fits; ranking stopped at upstream availability hold",
        "dependencies": {"numpy": numpy.__version__, "scipy": scipy.__version__},
        "dispatch_commit": "4e918ecd5d2b37eaa99ae365677f423080069480",
        "files": [
            {"bytes": (ROOT / path).stat().st_size, "path": path, "sha256": sha(ROOT / path)}
            for path in FILES
        ],
        "manifest_id": "a9c-implementation-v1",
        "platform": {"machine": platform.machine(), "python": sys.version.split()[0], "system": platform.system()},
        "production_runtime_changed": False,
        "schema_version": 1,
    }
    OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"captured {len(FILES)} A9c implementation inputs")


if __name__ == "__main__":
    main()
