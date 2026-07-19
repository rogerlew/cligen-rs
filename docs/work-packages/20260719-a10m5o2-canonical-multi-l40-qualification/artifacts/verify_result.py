#!/usr/bin/env python3
"""Verify the committed A10M5O2 qualification disposition."""

import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
summary = json.loads((PACKAGE / "artifacts/live/operational-summary.json").read_text())
scaling = json.loads((PACKAGE / "artifacts/scaling-summary.json").read_text())

assert summary["operational_terminal"] == "A10M5O2-MULTI-L40-OPS-READY"
assert summary["performance_classification"] == "SINGLE-GPU-PREFERRED"
assert [job["gpus"] for job in summary["jobs"]] == [1, 2, 4, 2]
assert [job["expected_exit_code"] for job in summary["jobs"]] == [0, 0, 0, 1]
assert all(job["node"] == "node03" for job in summary["jobs"])
assert summary["ledger"]["primary_requested_gpu_minutes"] == 82
assert summary["ledger"]["actual_gpu_seconds"] == 650
assert summary["ledger"]["recovery_status"] == "released"
assert summary["cleanup"] == {
    "job_local_cleanup": "verified_absent",
    "remote_absent": True,
    "terminal": "LEMHI-TOOLKIT-RUN-CLOSED",
}
assert summary["projection"]["projector_version"] == "lemhi-evidence-projection-4"
assert summary["projection"]["escaped_reserved_token_counts"] == {
    "NO_OTHER_FAILURES": 1
}
assert scaling["fixed_global_work"]["two_gpu_over_one"] < 1.6
assert scaling["fixed_global_work"]["four_gpu_incremental_over_two"] < 1.4
for role in ("single-baseline", "dual-qualification", "quad-qualification", "dual-rank-failure"):
    admission = (PACKAGE / f"artifacts/admission/{role}.txt").read_text()
    assert "Admission: PASS" in admission
print("A10M5O2_RESULT_PASS")
