#!/usr/bin/env python3
"""Verify the closed A10M4O2 acceptance evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from research.a10.lemhi_toolkit.core import read_record


ARTIFACTS = Path(__file__).resolve().parent
LIVE = ARTIFACTS / "live"


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {label}")


def load(name: str) -> dict:
    return json.loads((LIVE / name).read_text(encoding="utf-8"))


for name in (
    "abort.json",
    "job-success.0.json",
    "job-failure.0.json",
    "recovery.json",
    "collection.json",
    "cleanup.json",
    "terminal.json",
):
    read_record(LIVE / name)

abort = load("abort.json")
success = load("job-success.0.json")
failure = load("job-failure.0.json")
recovery = load("recovery.json")
collection = load("collection.json")
cleanup = load("cleanup.json")
terminal = load("terminal.json")
scheduler = load("scheduler-accounting.json")
ledger = load("resource-ledger-summary.json")

require(abort["terminal"] == "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION", "abort terminal")
require(abort["remote_absent"] is True and abort["job_local_cleanup"] == "not_started", "abort cleanup")
require(success["passed"] is True and success["result"]["gates"] == {"job_local_cleanup": True, "l40_visible": True, "registered_success": True}, "success gates")
require(success["result"]["elapsed_seconds"] == 5, "success elapsed")
require(success["result"]["actual_gpu_seconds"] == 5, "success GPU seconds")
require(success["result"]["actual_gpu_minutes"] == 1, "success rounded GPU minutes")
require(failure["passed"] is False and failure["result"]["exit_code"] == 7, "controlled failure")
require(failure["result"]["gates"] == {"job_local_cleanup": False, "registered_failure": True}, "failure receipt")
target = failure["result"]["recovery_target"]
target_hash = hashlib.sha256(target["target"].encode()).hexdigest()
proof = recovery["result"]["recovery_result"]
require(recovery["passed"] is True and all(recovery["result"]["gates"].values()), "recovery gates")
require(recovery["result"]["node"] == target["node"] == proof["node"] == "node03", "exact node")
require(proof["original_job_id"] == failure["job_id"] and proof["target_sha256"] == target_hash, "recovery identity")

published = {item["logical_name"]: item for item in collection["sanitized_files"]}
for logical, local_name in (
    ("success.json", "evidence-success.json"),
    ("failure.json", "evidence-failure.json"),
    ("recovery.json", "evidence-recovery.json"),
):
    content = (LIVE / local_name).read_bytes()
    require(published[logical]["bytes"] == len(content), f"{logical} bytes")
    require(published[logical]["sha256"] == hashlib.sha256(content).hexdigest(), f"{logical} hash")

require(collection["download_promoted"] is True, "collection promoted")
require(cleanup["remote_absent"] is True and cleanup["job_local_cleanup"] == "verified_absent", "cleanup")
require(terminal["terminal"] == "LEMHI-TOOLKIT-RUN-CLOSED" and terminal["attempt_count"] == 2, "terminal")
require(scheduler["squeue_absent"] is True and scheduler["remote_roots_absent"] is True, "external absence")
require([item["job_id"] for item in scheduler["jobs"]] == ["1013867", "1013868", "1013869"], "scheduler identities")
require({item["job_id"] for item in ledger["jobs"]} == {item["job_id"] for item in scheduler["jobs"]}, "ledger reconciliation")
require(ledger["requested_gpu_minutes"] == 6 <= ledger["ceiling_gpu_minutes"] == 10, "resource ceiling")
require(ledger["actual_gpu_seconds"] == 8 and ledger["actual_gpu_minutes"] == 3, "actual accounting")
require(ledger["jobs"][-1]["absence_proof"] == "JOB_LOCAL_ABSENT", "ledger absence proof")

print("A10M4O2-ACCEPTANCE-EVIDENCE-PASS")
