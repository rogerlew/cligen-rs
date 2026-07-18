#!/usr/bin/env python3
"""Fail-closed checks for the canonical-v2 live-smoke handoff."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json"
sys.path.insert(0, str(ROOT))

from research.a10.lemhi_toolkit.core import canonical_bytes, read_json, sha256_bytes, sha256_file


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"canonical-v2 smoke scaffold: FAIL: {detail}")


def main() -> None:
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    require(
        "Status: `SCAFFOLDED`" in package or "Status: `EXECUTED-HOLD`" in package,
        "status",
    )
    require("20 L40-GPU-minutes" in package, "resource ceiling")
    require("No remote" not in package, "invalid dispatch wording")
    candidate = read_json(CANDIDATE)
    recorded = candidate.pop("configuration_semantic_sha256")
    require(recorded == sha256_bytes(canonical_bytes(candidate)), "candidate semantic hash")
    require(candidate["schema_version"] == "lemhi-canonical-configuration-semantics-2", "candidate schema")
    require("configuration_status" not in candidate and "evidence" not in candidate, "candidate contains mutable state")
    pinned = [candidate["toolkit_profile"], *candidate["provider_stack"]]
    for item in pinned:
        require(sha256_file(ROOT / item["path"]) == item["sha256"], f"pinned input {item['path']}")
    require(len(candidate["provider_stack"]) == 7, "provider count")
    require(not list(ROOT.glob("research/a10/lemhi_toolkit/configurations/*designation*")), "designation created before smoke")
    print("canonical-v2 smoke scaffold: PASS")
    print(f"candidate={recorded} requested_gpu_minutes=20 remote_allocations=0")


if __name__ == "__main__":
    main()
