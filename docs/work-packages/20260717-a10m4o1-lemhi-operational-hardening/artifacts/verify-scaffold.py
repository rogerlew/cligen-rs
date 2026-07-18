#!/usr/bin/env python3
"""Fail-closed checks for the prospective A10M4O1 scaffold."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
ARTIFACTS = PACKAGE / "artifacts"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"A10M4O1 scaffold: FAIL: {message}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    package_words = " ".join(package.split())
    lessons = (ARTIFACTS / "lessons-register.md").read_text(encoding="utf-8")
    design = (ARTIFACTS / "design-freeze.md").read_text(encoding="utf-8")
    disposition = (ARTIFACTS / "review-disposition.md").read_text(encoding="utf-8")
    gates = (ARTIFACTS / "scaffold-gates.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/ROADMAP.md").read_text(encoding="utf-8")
    catalog = (ROOT / "docs/work-packages/README.md").read_text(encoding="utf-8")

    require(
        "Status: `SCAFFOLDED`" in package or "Status: `EXECUTED-COMPLETE`" in package,
        "package status",
    )
    require("A10M4O1-TOOLKIT-HARDENED" in package, "terminal")
    require("No remote write or allocation is authorized" in package_words, "dispatch boundary")
    require("5x/10x" in package and "separate prospective" in package, "runtime defer")

    observed = re.findall(r"^\| (L\d{2}) \|", lessons, flags=re.MULTILINE)
    expected = [f"L{number:02d}" for number in range(1, 16)]
    require(observed == expected, "lesson IDs/order")

    for token in (
        "derive-run",
        "lemhi-toolkit-provider-2",
        "lemhi-toolkit-record-2",
        "toolkit_recoverable",
        "CUBLAS_WORKSPACE_CONFIG=:4096:8",
        "RAW_COLLECTED",
        "recovery contingency",
        "ledger anchor",
        "initialize-authority",
        "scheduler reconciliation",
        "process supervisor",
        "Transfer telemetry and bounded reuse",
        "Canonical configuration transition",
        "lemhi-canonical-smoke-attestation-1",
        "lemhi-canonical-designation-index-1",
    ):
        require(token in design, f"missing design token: {token}")

    require("Cross-run/cross-authority caching is deferred" in design, "cross-run reuse defer")
    require("does **not** claim" in design, "ledger rollback trust-boundary disclosure")
    require("L08 and L15 are explicitly deferred" in lessons, "lesson deferrals")
    for finding in [f"AR-{number:02d}" for number in range(1, 9)]:
        require(f"| {finding} | ACCEPT |" in disposition, f"architecture disposition {finding}")
    for finding in [f"HS-{number:02d}" for number in range(1, 11)]:
        require(f"| {finding} | ACCEPT |" in disposition, f"HPC disposition {finding}")
    disposition_words = " ".join(disposition.lower().split())
    require("there are no waivers" in disposition_words, "review waiver policy")
    require("R2-AR-01" in disposition and "`ACCEPT`" in disposition, "round-2 disposition")
    require(disposition.count("`CONVERGED`") == 2, "dual-review convergence")
    require("Result: `PASS`" in gates and "0 remote allocations" in gates, "scaffold gates")

    configuration_path = ROOT / (
        "research/a10/lemhi_toolkit/configurations/"
        "lemhi-a10-py311-l40-v1.json"
    )
    configuration = json.loads(configuration_path.read_text(encoding="utf-8"))
    require(configuration["configuration_id"] == "lemhi-a10-py311-l40-v1", "v1 identity")
    require(configuration["configuration_status"] == "current-canonical", "v1 current status")
    require(
        sha256(configuration_path)
        == "99a7df3d4192ccf9a585944f62501087126c855a4fe59964aa6106afe42ae312",
        "canonical v1 changed during scaffold",
    )

    require(
        "A10M4O1 operational-hardening package" in roadmap
        or "A10M4O1 operational hardening" in roadmap,
        "roadmap transition",
    )
    require("20260717-a10m4o1-lemhi-operational-hardening" in catalog, "catalog entry")
    require("confirmation target access" in package, "confirmation firewall")

    print("A10M4O1 prospective scaffold: PASS")
    print(json.dumps({"lessons": len(observed), "remote_allocations": 0, "v1_sha256": sha256(configuration_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
