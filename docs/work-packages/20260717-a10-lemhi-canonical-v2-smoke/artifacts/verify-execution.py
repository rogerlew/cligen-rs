#!/usr/bin/env python3
"""Verify the canonical-v2 hold disposition without remote access."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json"


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"canonical-v2 execution: FAIL: {detail}")


def main() -> None:
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    terminal = (PACKAGE / "artifacts/terminal.md").read_text(encoding="utf-8")
    gate = json.loads((PACKAGE / "artifacts/evidence/smoke-gate.json").read_text())
    scheduler = json.loads((PACKAGE / "artifacts/evidence/scheduler-accounting.json").read_text())
    ledger = json.loads((PACKAGE / "artifacts/evidence/resource-ledger-summary.json").read_text())
    candidate = json.loads(CANDIDATE.read_text())
    require("Status: `EXECUTED-HOLD`" in package, "package status")
    require("HOLD-A10-CANONICAL-V2-SMOKE-ENVIRONMENT-CLOSURE" in terminal, "terminal")
    require(gate["verdict"] == "FAIL" and gate["exit_code"] == 1, "smoke failure")
    require(gate["configuration_semantic_sha256"] == candidate["configuration_semantic_sha256"], "candidate identity")
    require(scheduler["squeue_absent"] is True and [job["state"] for job in scheduler["jobs"]] == ["FAILED", "COMPLETED"], "scheduler settlement")
    require(ledger["requested_gpu_minutes"] == ledger["ceiling_gpu_minutes"] == 20, "resource ceiling")
    require(ledger["jobs"][1]["absence_proof"] == "JOB_LOCAL_ABSENT", "recovery proof")
    require(not list(ROOT.glob("research/a10/lemhi_toolkit/configurations/*designation*")), "designation exists")
    require(not list(PACKAGE.rglob("*attestation*.json")), "attestation exists")
    print("canonical-v2 execution: PASS (hold verified)")


if __name__ == "__main__":
    main()
