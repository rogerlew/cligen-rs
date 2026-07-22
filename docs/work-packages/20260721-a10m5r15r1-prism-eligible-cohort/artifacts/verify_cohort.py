#!/usr/bin/env python3
"""Verify the built A10M5R15R1 cohort without opening protected roles."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
JOB = PACKAGE / "artifacts/jobs/cohort.py"


def load_job():
    spec = importlib.util.spec_from_file_location("a10m5r15r1_cohort_verify", JOB)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load cohort job")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


job = load_job()
contract, _, preflight = job.authenticate()
plan = job.read(job.PLAN)
acquisition = job.read(job.ACQUISITION)
selection = job.read(job.SELECTION)
normalized = job.read(job.NORMALIZED_MANIFEST)
normalization = job.read(job.NORMALIZATION)
transfer = job.read(job.TRANSFER_MANIFEST)
source = job.read(job.SOURCE_MANIFEST)
receipt = job.read(job.BUILD_RECEIPT)

if acquisition.get("valid") is not True or acquisition["request_count"] != 36:
    raise RuntimeError("bounded acquisition result drift")
if job.digest(job.LEDGER) != acquisition["ledger_sha256"]:
    raise RuntimeError("successor access ledger identity drift")
accepted = acquisition["accepted_new_locations"]
if Counter((row["regime"], row["role"]) for row in accepted) != Counter(
    {("cold", "candidate_fit"): 8, ("hot_arid", "candidate_fit"): 28}
):
    raise RuntimeError("new accepted cohort allocation drift")
published = subprocess.run(
    ("git", "cat-file", "-t", acquisition["source_commit"]),
    cwd=REPO,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
if published != "commit":
    raise RuntimeError("acquisition source commit is unavailable")

locations = selection["locations"]
counts = Counter((row["regime"], row["role"]) for row in locations)
expected = Counter(
    {
        (regime, role): contract[f"{role}_per_regime"]
        for regime in contract["regimes"]
        for role in ("candidate_fit", "fit_validation")
    }
)
if len(locations) != 1440 or len({row["point_id"] for row in locations}) != 1440 or counts != expected:
    raise RuntimeError("final cohort balance drift")
tile_roles = defaultdict(set)
for row in locations:
    tile_roles[row["tile_id"]].add(row["role"])
if any(len(roles) != 1 for roles in tile_roles.values()):
    raise RuntimeError("final cohort tile role collision")

prism_root = Path(os.environ["A10M5R15R1_PRISM_ROOT"])
grid = preflight.validate_grid(prism_root)
for row in locations:
    preflight.query(prism_root, grid, float(row["longitude"]), float(row["latitude"]))

if (
    normalized["cohort_contract_sha256"] != job.digest(job.CONTRACT)
    or normalized["cohort_selection_sha256"] != job.digest(job.SELECTION)
    or len(normalized["daymet_shards"]) != 60
    or len(normalized["uscrn_objects"]) != 38
    or any(normalized["leakage_audit"].values())
):
    raise RuntimeError("normalized manifest drift")
manifest_ids = []
for shard in normalized["daymet_shards"]:
    path = REPO / shard["path"]
    if path.stat().st_size != shard["bytes"] or job.digest(path) != shard["sha256"]:
        raise RuntimeError(f"Daymet shard identity drift: {path.name}")
    with tarfile.open(path, "r:gz") as archive:
        names = [member.name for member in archive.getmembers()]
    expected_names = [f"{point_id}.json" for point_id in shard["point_ids"]]
    if names != expected_names or len(names) != shard["object_count"]:
        raise RuntimeError(f"Daymet shard roster drift: {path.name}")
    manifest_ids.extend(shard["point_ids"])
if manifest_ids != [row["point_id"] for row in locations]:
    raise RuntimeError("Daymet shard order differs from final cohort")

observed_bytes = 0
for row in transfer["objects"]:
    path = REPO / row["path"]
    if path.stat().st_size != row["bytes"] or job.digest(path) != row["sha256"]:
        raise RuntimeError(f"transfer object identity drift: {row['path']}")
    observed_bytes += row["bytes"]
if len(transfer["objects"]) != 98 or observed_bytes != transfer["aggregate_bytes"]:
    raise RuntimeError("transfer aggregate drift")

daymet_rows = [row for row in normalization["rows"] if row["source_id"] == "daymet_v4r1_single_pixel"]
if (
    normalization["fit_role_only"] != "candidate_fit"
    or len(daymet_rows) != 42
    or any(row["count"] != 2_190_000 or row["standard_deviation"] <= 0 for row in daymet_rows)
):
    raise RuntimeError("candidate-fit-only normalization drift")
if source["confirmation_target_series_accessed"] is not False or source["successor_daymet_access_ledger_sha256"] != job.digest(job.LEDGER):
    raise RuntimeError("source manifest or protected-role state drift")
if receipt != {
    "aggregate_bytes": transfer["aggregate_bytes"],
    "cohort_selection_sha256": job.digest(job.SELECTION),
    "daymet_location_count": 1440,
    "daymet_shard_count": 60,
    "normalized_manifest_sha256": job.digest(job.NORMALIZED_MANIFEST),
    "normalization_statistics_sha256": job.digest(job.NORMALIZATION),
    "package_id": contract["package_id"],
    "schema_version": "a10m5r15r1-cohort-build-1",
    "transfer_manifest_sha256": job.digest(job.TRANSFER_MANIFEST),
    "transfer_object_count": 98,
    "valid": True,
}:
    raise RuntimeError("cohort build receipt drift")

print("A10M5R15R1-COHORT-VERIFIED")
