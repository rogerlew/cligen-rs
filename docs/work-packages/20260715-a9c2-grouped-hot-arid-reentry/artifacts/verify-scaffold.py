#!/usr/bin/env python3
"""Verify the preserved A9c2 scaffold authorities and pre-access boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
ARTIFACTS = PACKAGE / "artifacts"

sys.dont_write_bytecode = True


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    manifest = json.loads((ARTIFACTS / "predecessor-manifest-v1.json").read_text())
    require(manifest["manifest_id"] == "a9c2-predecessor-v1", "manifest ID")
    require(manifest["a9c_historical_terminal"] == "HOLD-A9C-GATE-CALIBRATION", "A9c terminal")
    require(manifest["a9c_report_revision"] == 2, "report revision")
    require(manifest["a9c2_execution_authorized"] is False, "execution authorization")
    for record in manifest["files"]:
        path = ROOT / record["path"]
        require(path.is_file(), f"missing predecessor: {path}")
        require(path.stat().st_size == record["bytes"], f"predecessor bytes: {path}")
        require(sha256(path) == record["sha256"], f"predecessor hash: {path}")

    package = (PACKAGE / "package.md").read_text()
    context = (ARTIFACTS / "context-and-design-contract.md").read_text()
    require(
        "Status: `SCAFFOLDED`" in package
        or "Status: `EXECUTED-HOLD-HOT-ARID-ROSTER`" in package,
        "package status",
    )
    require("first outcome-bearing gate" in package, "preserved dispatch boundary")
    require("at least five" in package and "at least five" in context, "roster floor")
    require("station-balanced" in package and "Station-balanced" in context, "group estimator")
    require("a9c2-objective-registry-v1.json" in context, "versioned registry")
    require("0.80 power" in package and "0.80 power" in context, "power target")
    require("A9a's registry or SPEC-A9 revision 1" in context, "immutable registry/spec")
    require("confirmation" in context and "metadata-only" in context, "confirmation firewall")
    require(not (ARTIFACTS / "large").exists(), "unexpected acquired A9c2 evidence")

    attribute = subprocess.check_output(
        ["git", "check-attr", "filter", "--", str((PACKAGE / "artifacts/large/probe.bin").relative_to(ROOT))],
        cwd=ROOT,
        text=True,
    )
    require(attribute.rstrip().endswith(": lfs"), "package-local LFS rule")
    subprocess.run(
        [
            sys.executable,
            "docs/reports/verify-report.py",
            "docs/reports/a9c-observed-development-availability-report.manifest.json",
        ],
        cwd=ROOT,
        check=True,
    )
    require(
        not subprocess.run(
            ["git", "diff", "--quiet", "--", "crates", "reference/cligen532"],
            cwd=ROOT,
        ).returncode,
        "production/reference diff",
    )
    print(
        f"PASS: {len(manifest['files'])} predecessors; A9c revision 2; "
        "A9c2 scaffold authorities; local LFS"
    )


if __name__ == "__main__":
    main()
