#!/usr/bin/env python3
"""Fail-closed checks for the environment-closure successor scaffold."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.a10.lemhi_toolkit.core import canonical_bytes, read_json, sha256_bytes, sha256_file


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"canonical-v2 environment successor: FAIL: {detail}")


def main() -> None:
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    require("Status: `SCAFFOLDED`" in package, "status")
    require("20 L40-GPU-minutes" in package, "resource ceiling")
    candidate_path = ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json"
    candidate = read_json(candidate_path)
    recorded = candidate.pop("configuration_semantic_sha256")
    require(recorded == sha256_bytes(canonical_bytes(candidate)), "candidate semantic hash")
    for item in [candidate["toolkit_profile"], *candidate["provider_stack"]]:
        require(sha256_file(ROOT / item["path"]) == item["sha256"], f"pinned input {item['path']}")
    jobs = PACKAGE / "artifacts/jobs"
    for name in ("smoke-v2.sh", "smoke-app.sh"):
        require(os.access(jobs / name, os.X_OK), f"{name} executable mode")
    smoke = (jobs / "smoke-v2.sh").read_text(encoding="utf-8")
    require("environment_entry_presence" in smoke, "typed entry evidence")
    require("unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH" in smoke, "ambient clearing")
    require("trap fail_receipt EXIT" in smoke, "failure receipt")
    print("canonical-v2 environment successor scaffold: PASS")
    print(f"candidate={recorded} requested_gpu_minutes=20 remote_allocations=0")


if __name__ == "__main__":
    main()
