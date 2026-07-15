#!/usr/bin/env python3
"""Capture exact A9b research-tool and generated-evidence identities."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    sources = [
        path
        for path in (ROOT / "research/a9_harness").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    sources.append(ROOT / "research/__init__.py")
    sources.extend(
        [
            Path(__file__).resolve(),
            ARTIFACTS / "exercise-a9b-commands.py",
            ARTIFACTS / "verify-a9b.py",
            ARTIFACTS / "verify-a9b-replay.py",
        ]
    )
    generated = sorted((ARTIFACTS / "generated").glob("*.json"))
    record = {
        "schema_version": 1,
        "manifest_id": "a9b-source-v1",
        "dispatch_commit": "795f76775135044f7643e44f1f08cca1136e7236",
        "research_only": True,
        "observed_target_access": False,
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "math_backend": "CPython math module / host libm; research f64 only",
        },
        "schema_dependencies": {
            package: importlib.metadata.version(package)
            for package in (
                "attrs",
                "jsonschema",
                "jsonschema-specifications",
                "referencing",
                "rpds-py",
            )
        },
        "source_files": [identity(path) for path in sorted(sources)],
        "generated_evidence": [identity(path) for path in generated],
    }
    data = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8")
    destination = ARTIFACTS / "source-manifest-v1.json"
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    temporary.write_bytes(data)
    os.replace(temporary, destination)
    print(f"captured {len(sources)} source files and {len(generated)} evidence files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
