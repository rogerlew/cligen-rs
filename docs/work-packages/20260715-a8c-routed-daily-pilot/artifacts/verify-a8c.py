#!/usr/bin/env python3
"""Independent reproducibility and identity checks for A8c artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
CLOSURE = ARTIFACTS / "closure-manifest-v1.json"
CLOSURE_OWNED = {
    "crates/cligen/src/runspec.rs",
    "crates/cligen/tests/a8c_routed_daily.rs",
    "docs/specifications/SPEC-A8C-ROUTED-DAILY.md",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/package.md",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/analyze-a8c.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/verify-a8c.py",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    execution_freeze = load_json(ARTIFACTS / "pre-execution-freeze-v1.json")
    freeze = load_json(ARTIFACTS / "pre-analysis-freeze-v2.json")
    contract = load_json(ARTIFACTS / "pilot-contract-v1.json")
    execution = load_json(ARTIFACTS / "execution-evidence-v1.json")
    analysis = load_json(ARTIFACTS / "a8c-analysis-v1.json")
    decision = load_json(ARTIFACTS / "a8c-decision-v1.json")
    closure = load_json(CLOSURE)
    checks = 0

    if freeze["status"] != "FROZEN-POST-GENERATION-BEFORE-OUTCOME":
        raise ValueError("freeze is inactive")
    for relative, expected in freeze["frozen_files_sha256"].items():
        if relative in CLOSURE_OWNED:
            continue
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"frozen identity mismatch: {relative}")
        checks += 1
    if closure["status"] != "CLOSED-AFTER-STOP-A8-ROUTED-DAILY":
        raise ValueError("closure manifest is inactive")
    for relative, expected in closure["closed_files_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"closure identity mismatch: {relative}")
        checks += 1
    if execution["contract_sha256"] != sha256(ARTIFACTS / "pilot-contract-v1.json"):
        raise ValueError("execution contract mismatch")
    if execution_freeze["status"] != "FROZEN-BEFORE-CANDIDATE-GENERATION":
        raise ValueError("execution freeze is inactive")
    if execution["freeze_sha256"] != sha256(ARTIFACTS / "pre-execution-freeze-v1.json"):
        raise ValueError("execution freeze mismatch")
    if analysis["pre_analysis_freeze_sha256"] != sha256(
        ARTIFACTS / "pre-analysis-freeze-v2.json"
    ):
        raise ValueError("analysis freeze mismatch")
    if analysis["execution_evidence_sha256"] != sha256(
        ARTIFACTS / "execution-evidence-v1.json"
    ):
        raise ValueError("analysis execution mismatch")
    if decision["analysis_sha256"] != sha256(ARTIFACTS / "a8c-analysis-v1.json"):
        raise ValueError("decision analysis mismatch")
    checks += 5

    expected_stations = {row["station_id"]: row for row in contract["stations"]}
    if len(execution["cells"]) != 24:
        raise ValueError("unexpected execution cell count")
    missing = [
        ROOT / cell[variant][path_key]
        for cell in execution["cells"]
        for variant in ("candidate", "faithful")
        for path_key in ("cli_path", "provenance_path")
        if not (ROOT / cell[variant][path_key]).exists()
    ]
    if missing:
        result = subprocess.run(
            [
                sys.executable,
                str(ARTIFACTS / "archive-a8c-evidence.py"),
                "--restore",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
    for cell in execution["cells"]:
        station = expected_stations[cell["station_id"]]
        if cell["route"] != station["route"]:
            raise ValueError(f"route mismatch: {cell['station_id']}")
        for variant in ("candidate", "faithful"):
            entry = cell[variant]
            if sha256(ROOT / entry["cli_path"]) != entry["cli_sha256"]:
                raise ValueError(f"stream mismatch: {entry['cli_path']}")
            if sha256(ROOT / entry["provenance_path"]) != entry["provenance_sha256"]:
                raise ValueError(f"provenance mismatch: {entry['provenance_path']}")
            checks += 2

    with tempfile.TemporaryDirectory(prefix="a8c-verify-") as directory:
        result = subprocess.run(
            [
                sys.executable,
                str(ARTIFACTS / "analyze-a8c.py"),
                "--output-dir",
                directory,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        for name in ("a8c-analysis-v1.json", "a8c-decision-v1.json", "findings.md"):
            if (Path(directory) / name).read_bytes() != (ARTIFACTS / name).read_bytes():
                raise ValueError(f"analysis replay mismatch: {name}")
            checks += 1

    print(
        json.dumps(
            {
                "checks": checks,
                "decision": decision["terminal_decision"],
                "status": "PASS",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
