#!/usr/bin/env python3
"""Fail closed on the A10M5R15R1 cohort contract and frozen queue."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
A10M1 = REPO / "docs/work-packages/20260717-a10m1-corpus-role-freeze"
R15 = REPO / "docs/work-packages/20260721-a10m5r15-external-normal-conditioning"
PACKAGE_ID = "20260721-a10m5r15r1-prism-eligible-cohort"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


contract = read(PACKAGE / "artifacts/cohort-contract.json")
plan = read(PACKAGE / "artifacts/cohort-plan.json")

if contract != {
    "candidate_fit_per_regime": 200,
    "fit_validation_per_regime": 40,
    "frozen_new_request_deficit": {
        "cold/candidate_fit": 8,
        "hot_arid/candidate_fit": 28,
    },
    "maximum_new_daymet_requests": 72,
    "package_id": PACKAGE_ID,
    "predecessors": contract["predecessors"],
    "prism": {
        "bundle_id": "prism_norm91m_9120_4km_m4_m5_v1",
        "grid_manifest_sha256": "f0eb4b9d4fbe422477c70aebf6eb11e43d329947d6731010edaf315d87de4c9d",
        "query": "one_valid_containing_cell_no_fallback_no_interpolation",
    },
    "regimes": [
        "hot_arid",
        "arid_boundary",
        "monsoonal_transition",
        "non_monsoonal_semi_arid",
        "humid",
        "cold",
    ],
    "schema_version": "a10m5r15r1-cohort-contract-1",
    "selection": "retain_valid_v2_then_original_candidate_blind_order_existing_accepted_first_then_published_request_queue",
    "target_total": 1440,
}:
    raise RuntimeError("cohort contract drift")

predecessors = {
    "a10m1_freeze_sha256": A10M1 / "artifacts/a10m1-freeze-v1.json",
    "a10m1_job_source_sha256": A10M1 / "artifacts/jobs/a10m1_corpus.py",
    "a10m1_original_access_ledger_sha256": A10M1 / "artifacts/daymet-access-v1.ndjson",
    "a10m1_partition_sha256": A10M1 / "artifacts/partition-role-freeze-v1.json",
    "a10m1_selected_v2_sha256": A10M1 / "artifacts/daymet-selected-v2.json",
    "a10m1_tile_repair_sha256": A10M1 / "artifacts/daymet-tile-repair-freeze-v2.json",
    "a10m5r15_failure_sha256": R15 / "artifacts/preflight/normal-conditioning-preflight-failure.json",
    "a10m5r15_preflight_source_sha256": R15 / "artifacts/jobs/build_normal_conditioning.py",
}
if contract["predecessors"] != {name: digest(path) for name, path in predecessors.items()}:
    raise RuntimeError("predecessor identity drift")

if (
    plan["package_id"] != PACKAGE_ID
    or plan["schema_version"] != "a10m5r15r1-cohort-plan-1"
    or plan["candidate_order_used_climate_values"] is not False
    or plan["confirmation_roles_opened"] != []
    or plan["deficits_after_existing"] != contract["frozen_new_request_deficit"]
    or plan["maximum_new_requests"] != 72
):
    raise RuntimeError("frozen plan contract drift")

groups = {
    "retained": plan["retained_locations"],
    "existing": plan["existing_replacements"],
    "queue": plan["request_queue"],
}
if {name: len(rows) for name, rows in groups.items()} != {
    "retained": 1366,
    "existing": 38,
    "queue": 72,
} or len(plan["invalid_predecessor_points"]) != 74:
    raise RuntimeError("cohort plan count drift")

point_sets = {name: {row["point_id"] for row in rows} for name, rows in groups.items()}
if any(len(point_sets[name]) != len(groups[name]) for name in groups):
    raise RuntimeError("duplicate point in a cohort-plan group")
if point_sets["retained"] & point_sets["existing"] or point_sets["retained"] & point_sets["queue"] or point_sets["existing"] & point_sets["queue"]:
    raise RuntimeError("cohort-plan groups overlap")
if set(plan["invalid_predecessor_points"]) & point_sets["retained"]:
    raise RuntimeError("invalid predecessor point was retained")

queue_counts = Counter((row["regime"], row["role"]) for row in groups["queue"])
if queue_counts != Counter({("cold", "candidate_fit"): 16, ("hot_arid", "candidate_fit"): 56}):
    raise RuntimeError("bounded queue allocation drift")
if any(row["role"] not in {"candidate_fit", "fit_validation"} for rows in groups.values() for row in rows):
    raise RuntimeError("protected role opened")

selected = read(A10M1 / "artifacts/daymet-selected-v2.json")["locations"]
selected_ids = {row["point_id"] for row in selected}
invalid = set(plan["invalid_predecessor_points"])
if point_sets["retained"] != selected_ids - invalid:
    raise RuntimeError("retained cohort differs from valid predecessor subset")

package_text = (PACKAGE / "package.md").read_text(encoding="utf-8")
if "Status: `A10M5R15R1-COHORT-READY`" not in package_text or "72 new requests" not in package_text:
    raise RuntimeError("package state or resource bound drift")
if PACKAGE_ID not in (REPO / "docs/work-packages/README.md").read_text(encoding="utf-8"):
    raise RuntimeError("work-package catalog missing cohort remedy")
if "A10M5R15R1" not in (REPO / "docs/ROADMAP.md").read_text(encoding="utf-8"):
    raise RuntimeError("roadmap missing cohort remedy")
if "A10M5R15R1" not in (REPO / "docs/exec-plans/20260721-a10-external-normal-conditioning.md").read_text(encoding="utf-8"):
    raise RuntimeError("living ExecPlan missing cohort remedy")

print("A10M5R15R1-SCAFFOLD-VERIFIED")
