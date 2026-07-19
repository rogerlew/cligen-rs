#!/usr/bin/env python3
"""Verify the frozen A10M5O1 multi-L40 toolkit surface."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(detail)


core = (ROOT / "research/a10/lemhi_toolkit/core.py").read_text(encoding="utf-8")
tests = (ROOT / "research/a10/lemhi_toolkit/tests/test_hardening.py").read_text(
    encoding="utf-8"
)
provider_path = (
    ROOT
    / "research/a10/lemhi_toolkit/providers/accelerator-l40-multigpu-v1.json"
)
provider = json.loads(provider_path.read_text(encoding="utf-8"))
spec = (
    ROOT / "docs/specifications/SPEC-LEMHI-MULTI-GPU-CAPABILITY.md"
).read_text(encoding="utf-8")

for fragment in (
    "def parse_typed_gres",
    "job gpus and gres count mismatch",
    "recovery gpus and gres count mismatch",
    "job gpu count exceeds provider maximum",
):
    require(fragment in core, f"missing core invariant: {fragment}")

require(provider["provider_api_version"] == 2, "provider API drift")
require(
    provider["provides"]["accelerator_request"] == "gpu:l40",
    "provider request drift",
)
require(
    provider["provides"]["accelerator_maximum_devices"] == 4,
    "provider maximum drift",
)
require(
    provider["capability_contract"]["allowed_counts"] == [1, 2, 4],
    "provider allowed counts drift",
)
for test_name in (
    "test_typed_gres_parser_and_plan_counts_fail_closed",
    "test_multigpu_provider_accepts_two_and_four_and_rejects_five",
    "test_recovery_gres_count_must_match_ledger_multiplier",
    "test_live_elapsed_accounting_uses_four_validated_gpus",
):
    require(test_name in tests, f"missing test: {test_name}")
require("does not change the default" in spec, "additive capability boundary absent")
print("A10M5O1_VERIFY_PASS")
