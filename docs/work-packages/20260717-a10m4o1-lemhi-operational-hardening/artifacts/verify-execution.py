#!/usr/bin/env python3
"""Fail-closed verification for completed A10M4O1 hardening."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
sys.path.insert(0, str(ROOT))

from research.a10.lemhi_toolkit.core import canonical_bytes, loads_strict, read_json, sha256_bytes, sha256_file


V1_RAW_SHA256 = "99a7df3d4192ccf9a585944f62501087126c855a4fe59964aa6106afe42ae312"
CANDIDATE_SHA256 = "5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d"


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"A10M4O1 execution: FAIL: {detail}")


def main() -> None:
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    require("Status: `EXECUTED-COMPLETE`" in package, "package status")
    require("A10M4O1-TOOLKIT-HARDENED" in package, "terminal")
    require("No VPN, SSH, Slurm, GPU" in package, "side-effect boundary")

    spec = (ROOT / "docs/specifications/SPEC-LEMHI-AGENT-TOOLKIT.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs/c3-lemhi-gpu-computing-for-agents.md").read_text(encoding="utf-8")
    for token in ("authoritative revision 2", "RAW_COLLECTED", "--export=NONE", "toolkit_recoverable", "wholesale restoration", "5x/10x"):
        require(token in spec, f"spec token {token}")
    for token in ("A10M4 operational hardening", "toolkit supervisor", "format-aware parser", "cross-run caching remains deferred"):
        require(token in guide, f"guide token {token}")

    v1 = ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v1.json"
    require(hashlib.sha256(v1.read_bytes()).hexdigest() == V1_RAW_SHA256, "canonical v1 changed")
    candidate_path = ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json"
    candidate = read_json(candidate_path)
    recorded = candidate.pop("configuration_semantic_sha256")
    require(recorded == CANDIDATE_SHA256 == sha256_bytes(canonical_bytes(candidate)), "candidate identity")
    require("configuration_status" not in candidate and "evidence" not in candidate, "candidate mutable state")
    for item in [candidate["toolkit_profile"], *candidate["provider_stack"]]:
        require(sha256_file(ROOT / item["path"]) == item["sha256"], f"pinned file {item['path']}")
    require(len(candidate["provider_stack"]) == 7, "v2 provider count")
    require(not list((candidate_path.parent).glob("*designation*")), "designation exists before smoke")

    test_tree = ast.parse((ROOT / "research/a10/lemhi_toolkit/tests/test_hardening.py").read_text(encoding="utf-8"))
    hardening_tests = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_") for node in ast.walk(test_tree))
    require(hardening_tests == 21, "hardening test count")
    for script in (ROOT / "research/a10/lemhi_toolkit/remote").glob("*.sh"):
        text = script.read_text(encoding="utf-8")
        require("eval " not in text, f"eval in {script.name}")
    submit_v2 = (ROOT / "research/a10/lemhi_toolkit/remote/submit_v2.sh").read_text(encoding="utf-8")
    require("--export=NONE" in submit_v2 and "--comment" in submit_v2, "v2 Slurm closure")

    smoke = ROOT / "docs/work-packages/20260717-a10-lemhi-canonical-v2-smoke/package.md"
    require("Status: `SCAFFOLDED`" in smoke.read_text(encoding="utf-8"), "smoke handoff")
    roadmap = (ROOT / "docs/ROADMAP.md").read_text(encoding="utf-8")
    catalog = (ROOT / "docs/work-packages/README.md").read_text(encoding="utf-8")
    require("A10M4O1-TOOLKIT-HARDENED" in roadmap and "canonical-v2 smoke package" in roadmap, "roadmap")
    require("20260717-a10m4o1-lemhi-operational-hardening" in catalog and "EXECUTED-COMPLETE" in catalog, "catalog")

    json_count = 0
    roots = [ROOT / "research/a10/lemhi_toolkit", PACKAGE, smoke.parent]
    for root in roots:
        for path in root.rglob("*.json"):
            value = loads_strict(path.read_text(encoding="utf-8"))
            require(isinstance(value, (dict, list)), f"JSON shape {path}")
            json_count += 1
    require(json_count >= 20, "JSON coverage")
    print("A10M4O1 execution: PASS")
    print(json.dumps({"candidate_sha256": recorded, "hardening_tests": hardening_tests, "json_files": json_count, "remote_allocations": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
