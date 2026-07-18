#!/usr/bin/env python3
"""Verify the exact-asset smoke and immutable attestation."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.a10.lemhi_toolkit.core import canonical_bytes, read_json, sha256_bytes


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"exact-asset smoke execution: FAIL: {detail}")


def main() -> None:
    candidate = read_json(ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json")
    gate = read_json(PACKAGE / "artifacts/evidence/smoke-gate.json")
    assets = read_json(PACKAGE / "artifacts/evidence/asset-identity.json")
    scheduler = read_json(PACKAGE / "artifacts/evidence/scheduler-accounting.json")
    closeout = read_json(PACKAGE / "artifacts/evidence/toolkit-closeout.json")
    attestation = read_json(PACKAGE / "artifacts/lemhi-canonical-smoke-attestation.json")
    recorded = attestation.pop("attestation_sha256")
    require(recorded == sha256_bytes(canonical_bytes(attestation)), "attestation hash")
    require(attestation["configuration_semantic_sha256"] == candidate["configuration_semantic_sha256"], "candidate binding")
    require(gate["verdict"] == "PASS" and all(gate["gates"].values()), "smoke gates")
    require(assets["verdict"] == "PASS" and assets["firewall_before_staging"] == assets["firewall_before_attestation"] == "PASS", "asset firewall")
    require(assets["frozen_assets"]["cargo-vendor.tar.gz"]["sha256"] == candidate["toolchain"]["vendor_archive_sha256"], "vendor identity")
    require(scheduler["settled"] is True and scheduler["squeue_absent"] is True and scheduler["slurm"]["state"] == "COMPLETED", "scheduler settlement")
    require(closeout["cleanup"] == {"job_local_cleanup": "verified_absent", "record_sha256": attestation["cleanup_receipt_sha256"], "remote_absent": True}, "cleanup")
    require(closeout["terminal"]["record_sha256"] == attestation["terminal_receipt_sha256"], "terminal binding")
    print(f"exact-asset smoke execution: PASS attestation={recorded}")


if __name__ == "__main__":
    main()
