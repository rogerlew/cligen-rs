#!/usr/bin/env python3
"""Verify A5f0 freeze identity, scope, decision, and reproducibility."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(
            stream,
            object_pairs_hook=strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"nonfinite JSON token: {token}")
            ),
        )
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_artifact(root: Path, record: dict[str, Any]) -> None:
    path = root / record["path"]
    if not path.is_file():
        raise ValueError(f"missing frozen artifact: {path}")
    if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
        raise ValueError(f"frozen artifact identity mismatch: {path}")


def main() -> int:
    root = repo_root()
    artifacts = root / (
        "docs/work-packages/20260714-a5f0-annual-state-failure-attribution/artifacts"
    )
    freeze = load_json(artifacts / "pre-analysis-freeze-v1.json")
    if freeze.get("status") != "FROZEN-BEFORE-DERIVED-ATTRIBUTION":
        raise ValueError("A5f0 freeze status is invalid")
    for record in freeze["frozen_sources"] + freeze["retained_inputs"]:
        verify_artifact(root, record)

    completed = subprocess.run(
        [sys.executable, str(artifacts / "analyze-a5f0.py"), "--check"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError(
            "A5f0 deterministic reproduction failed:\n"
            + completed.stdout
            + completed.stderr
        )

    analysis = load_json(artifacts / "a5f0-attribution-v1.json")
    decision = load_json(artifacts / "a5f0-decision-v1.json")
    contract = load_json(artifacts / "attribution-contract-v1.json")
    if analysis.get("integrity", {}).get("status") != "PASS":
        raise ValueError("A5f0 retained-input integrity did not pass")
    if analysis["integrity"]["matrix_runs_verified"] != 48:
        raise ValueError("A5f0 matrix run count is not 48")
    if analysis["integrity"]["matrix_products_verified"] != 288:
        raise ValueError("A5f0 matrix product count is not 288")
    if decision["decision"] not in contract["scope"]["allowed_decisions"]:
        raise ValueError("A5f0 decision is outside the frozen vocabulary")
    if decision["decision"] != analysis["decision"]["value"]:
        raise ValueError("A5f0 decision artifacts disagree")
    if decision["rule"] != analysis["decision"]["rule"]:
        raise ValueError("A5f0 decision rules disagree")

    changed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            freeze["identity"]["source_commit"],
            "--",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    forbidden = [
        path
        for path in changed
        if path.startswith("crates/")
        or path.endswith(".cli")
        or "coefficients" in Path(path).name
    ]
    if forbidden:
        raise ValueError(f"A5f0 scope violation: {forbidden}")
    print(completed.stdout.strip())
    print(
        "A5f0 freeze, retained matrix, decision, scope, and reproduction gates: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
