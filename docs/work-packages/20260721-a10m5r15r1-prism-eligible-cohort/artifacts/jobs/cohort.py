#!/usr/bin/env python3
"""Freeze, acquire, and finalize the A10M5R15R1 balanced cohort."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
A10M1 = REPO / "docs/work-packages/20260717-a10m1-corpus-role-freeze"
R15 = REPO / "docs/work-packages/20260721-a10m5r15-external-normal-conditioning"
CONTRACT = PACKAGE / "artifacts/cohort-contract.json"
PLAN = PACKAGE / "artifacts/cohort-plan.json"
LEDGER = PACKAGE / "artifacts/daymet-access.ndjson"
ACQUISITION = PACKAGE / "artifacts/acquisition-result.json"
SELECTION = PACKAGE / "artifacts/cohort-selection.json"
SHARD_MANIFEST = PACKAGE / "artifacts/daymet-shard-manifest-v1.json"
NORMALIZED_MANIFEST = PACKAGE / "artifacts/normalized-manifest-v1.json"
NORMALIZATION = PACKAGE / "artifacts/normalization-statistics-v1.json"
TRANSFER_MANIFEST = PACKAGE / "artifacts/offline-transfer-manifest-v1.json"
SOURCE_MANIFEST = PACKAGE / "artifacts/source-manifest-v1.json"
BUILD_RECEIPT = PACKAGE / "artifacts/cohort-build-receipt.json"
RAW = PACKAGE / "raw"
PARENT_SOURCE = A10M1 / "artifacts/jobs/a10m1_corpus.py"
PREFLIGHT_SOURCE = R15 / "artifacts/jobs/build_normal_conditioning.py"
TARGETS = {"candidate_fit": 200, "fit_validation": 40}
MAX_REQUESTS = 72


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> bytes:
    return (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_bytes(canonical(value))
    os.replace(partial, path)


def append(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab", buffering=0) as stream:
        stream.write(canonical(value))
        os.fsync(stream.fileno())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def authenticate() -> tuple[dict, object, object]:
    contract = read(CONTRACT)
    pins = contract["predecessors"]
    paths = {
        "a10m1_freeze_sha256": A10M1 / "artifacts/a10m1-freeze-v1.json",
        "a10m1_job_source_sha256": PARENT_SOURCE,
        "a10m1_original_access_ledger_sha256": A10M1 / "artifacts/daymet-access-v1.ndjson",
        "a10m1_partition_sha256": A10M1 / "artifacts/partition-role-freeze-v1.json",
        "a10m1_selected_v2_sha256": A10M1 / "artifacts/daymet-selected-v2.json",
        "a10m1_tile_repair_sha256": A10M1 / "artifacts/daymet-tile-repair-freeze-v2.json",
        "a10m5r15_failure_sha256": R15 / "artifacts/preflight/normal-conditioning-preflight-failure.json",
        "a10m5r15_preflight_source_sha256": PREFLIGHT_SOURCE,
    }
    if any(digest(path) != pins[name] for name, path in paths.items()):
        raise RuntimeError("cohort predecessor identity drift")
    parent = load_module("a10m5r15r1_parent", PARENT_SOURCE)
    preflight = load_module("a10m5r15r1_preflight", PREFLIGHT_SOURCE)
    return contract, parent, preflight


def original_statuses() -> dict[str, dict]:
    rows = {}
    for line in (A10M1 / "artifacts/daymet-access-v1.ndjson").read_text().splitlines():
        if line:
            row = json.loads(line)
            rows[row["point_id"]] = row
    return rows


def successor_statuses() -> dict[str, dict]:
    rows = {}
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            if line:
                row = json.loads(line)
                rows[row["point_id"]] = row
    return rows


def source_path(point_id: str) -> Path | None:
    successor = RAW / "daymet/source" / f"{point_id}.csv.gz"
    parent = A10M1 / "raw/daymet/source" / f"{point_id}.csv.gz"
    if successor.is_file():
        return successor
    if parent.is_file():
        return parent
    return None


def valid_candidates(preflight) -> tuple[list[dict], dict, set[str], set[str]]:
    partition = read(A10M1 / "artifacts/partition-role-freeze-v1.json")
    selected = read(A10M1 / "artifacts/daymet-selected-v2.json")["locations"]
    failures = read(R15 / "artifacts/preflight/normal-conditioning-preflight-failure.json")
    invalid = {row["point_id"] for row in failures["failures"]}
    conflicts = set(read(A10M1 / "artifacts/daymet-tile-repair-freeze-v2.json")["conflicted_tiles_excluded"])
    root = Path(os.environ["A10M5R15R1_PRISM_ROOT"])
    manifest = preflight.validate_grid(root)
    candidates = []
    for row in partition["daymet_candidate_locations"]:
        if row["tile_id"] in conflicts:
            continue
        try:
            preflight.query(root, manifest, float(row["longitude"]), float(row["latitude"]))
        except RuntimeError:
            continue
        candidates.append(row)
    return candidates, {row["point_id"]: row for row in selected}, invalid, conflicts


def freeze() -> None:
    contract, _, preflight = authenticate()
    candidates, selected, invalid, _ = valid_candidates(preflight)
    retained = [row for point_id, row in selected.items() if point_id not in invalid]
    counts = Counter((row["regime"], row["role"]) for row in retained)
    deficits = {
        (regime, role): TARGETS[role] - counts[(regime, role)]
        for regime in contract["regimes"]
        for role in TARGETS
    }
    selected_ids = set(selected)
    original = original_statuses()
    existing, existing_ids = [], set()
    remaining = dict(deficits)
    for row in candidates:
        key = (row["regime"], row["role"])
        if (
            remaining[key] > 0
            and row["point_id"] not in selected_ids
            and original.get(row["point_id"], {}).get("status") == "accepted"
            and source_path(row["point_id"]) is not None
        ):
            existing.append(row)
            existing_ids.add(row["point_id"])
            remaining[key] -= 1
    expected_remaining = {("cold", "candidate_fit"): 8, ("hot_arid", "candidate_fit"): 28}
    if {key: value for key, value in remaining.items() if value} != expected_remaining:
        raise RuntimeError(f"frozen existing-surplus arithmetic drift: {remaining}")
    queue = []
    queue_limits = {key: max(value + 8, value * 2) for key, value in expected_remaining.items()}
    queue_counts = Counter()
    for row in candidates:
        key = (row["regime"], row["role"])
        if key not in expected_remaining or queue_counts[key] >= queue_limits[key]:
            continue
        if row["point_id"] in selected_ids or row["point_id"] in existing_ids:
            continue
        if row["point_id"] in original:
            continue
        queue.append(row)
        queue_counts[key] += 1
    if len(queue) != MAX_REQUESTS or queue_counts != Counter({("cold", "candidate_fit"): 16, ("hot_arid", "candidate_fit"): 56}):
        raise RuntimeError(f"bounded request queue drift: {queue_counts}")
    plan = {
        "candidate_order_used_climate_values": False,
        "confirmation_roles_opened": [],
        "deficits_after_existing": {f"{a}/{b}": value for (a, b), value in sorted(expected_remaining.items())},
        "existing_replacements": existing,
        "invalid_predecessor_points": sorted(invalid),
        "maximum_new_requests": MAX_REQUESTS,
        "package_id": contract["package_id"],
        "request_queue": queue,
        "retained_locations": sorted(retained, key=lambda row: (row["regime"], row["role"], row["order"])),
        "schema_version": "a10m5r15r1-cohort-plan-1",
    }
    if len(plan["retained_locations"]) != 1366 or len(existing) != 38:
        raise RuntimeError("cohort plan count drift")
    write(PLAN, plan)
    print("A10M5R15R1-COHORT-PLAN-FROZEN")


def verify_published(source_commit: str) -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    published_paths = (Path(__file__).resolve(), CONTRACT, PLAN)
    exact = True
    for path in published_paths:
        relative = path.relative_to(REPO).as_posix()
        published = subprocess.run(
            ("git", "show", f"{source_commit}:{relative}"),
            cwd=REPO,
            check=True,
            capture_output=True,
        ).stdout
        exact = exact and published == path.read_bytes()
    if source_commit != head or head != upstream or branch != "main" or not exact:
        raise RuntimeError("cohort acquisition source is not exact published main")


def acquire(source_commit: str) -> None:
    _, parent, _ = authenticate()
    verify_published(source_commit)
    plan = read(PLAN)
    statuses = successor_statuses()
    needed = {("cold", "candidate_fit"): 8, ("hot_arid", "candidate_fit"): 28}
    accepted = Counter()
    accepted_rows = []
    parent.RAW = RAW
    parent.USER_AGENT = "cligen-rs-a10m5r15r1-cohort-v1"
    freeze_contract = read(A10M1 / "artifacts/a10m1-freeze-v1.json")
    for row in plan["request_queue"]:
        key = (row["regime"], row["role"])
        if accepted[key] >= needed[key]:
            continue
        receipt = statuses.get(row["point_id"])
        if receipt is None:
            receipt = parent.request_one_daymet(freeze_contract, row)
            receipt.update({"package_id": plan["package_id"], "source_commit": source_commit})
            append(LEDGER, receipt)
            statuses[row["point_id"]] = receipt
        if receipt.get("status") == "accepted":
            path = source_path(row["point_id"])
            if path is None or digest(path) != receipt["raw_gzip_sha256"]:
                raise RuntimeError("new Daymet source identity drift")
            accepted[key] += 1
            accepted_rows.append(row)
    if accepted != Counter(needed):
        write(
            ACQUISITION,
            {
                "accepted": {f"{a}/{b}": count for (a, b), count in sorted(accepted.items())},
                "package_id": plan["package_id"],
                "request_count": len(statuses),
                "schema_version": "a10m5r15r1-acquisition-1",
                "source_commit": source_commit,
                "terminal": "HOLD-A10M5R15R1-PRISM-ELIGIBLE-COHORT-UNAVAILABLE",
                "valid": False,
            },
        )
        raise RuntimeError(f"bounded request queue did not fill cohort: {accepted}")
    write(
        ACQUISITION,
        {
            "accepted_new_locations": accepted_rows,
            "ledger_sha256": digest(LEDGER),
            "package_id": plan["package_id"],
            "request_count": len(statuses),
            "schema_version": "a10m5r15r1-acquisition-1",
            "source_commit": source_commit,
            "valid": True,
        },
    )
    print("A10M5R15R1-DAYMET-ACQUISITION-COMPLETE")


def finalize() -> None:
    contract, parent, _ = authenticate()
    plan = read(PLAN)
    acquisition = read(ACQUISITION)
    if acquisition.get("valid") is not True:
        raise RuntimeError("cohort acquisition is not complete")
    selected = plan["retained_locations"] + plan["existing_replacements"] + acquisition["accepted_new_locations"]
    selected.sort(key=lambda row: (row["regime"], row["role"], row["order"]))
    counts = Counter((row["regime"], row["role"]) for row in selected)
    expected = Counter({(regime, role): TARGETS[role] for regime in contract["regimes"] for role in TARGETS})
    if len(selected) != 1440 or len({row["point_id"] for row in selected}) != 1440 or counts != expected:
        raise RuntimeError("final cohort point/count identity drift")
    tiles = {}
    freeze_contract = read(A10M1 / "artifacts/a10m1-freeze-v1.json")
    for row in selected:
        tiles.setdefault(row["tile_id"], set()).add(row["role"])
        path = source_path(row["point_id"])
        if path is None:
            raise RuntimeError(f"selected Daymet source missing: {row['point_id']}")
        import gzip
        with gzip.open(path, "rb") as stream:
            parent.parse_daymet(stream.read(), row, freeze_contract)
    if any(len(roles) != 1 for roles in tiles.values()):
        raise RuntimeError("final cohort tile role collision")
    write(
        SELECTION,
        {
            "counts": {f"{a}/{b}": count for (a, b), count in sorted(counts.items())},
            "locations": selected,
            "package_id": contract["package_id"],
            "schema_version": "a10m5r15r1-cohort-selection-1",
            "selection_used_climate_values": False,
            "source_identity_roots": [
                str((A10M1 / "raw/daymet/source").relative_to(REPO)),
                str((RAW / "daymet/source").relative_to(REPO)),
            ],
        },
    )
    print("A10M5R15R1-COHORT-SELECTION-FINALIZED")


def build() -> None:
    contract, parent, _ = authenticate()
    selection = read(SELECTION)
    selected = selection["locations"]
    if len(selected) != 1440 or digest(SELECTION) == "":
        raise RuntimeError("final cohort selection is unavailable")
    freeze_contract = read(A10M1 / "artifacts/a10m1-freeze-v1.json")
    shards = []
    availability = Counter()
    statistics: dict[tuple[str, str, str], dict] = {}
    for shard_index in range(0, len(selected), 24):
        points = selected[shard_index : shard_index + 24]
        objects = []
        for point in points:
            path = source_path(point["point_id"])
            if path is None:
                raise RuntimeError(f"selected Daymet source missing: {point['point_id']}")
            with gzip.open(path, "rb") as stream:
                payload, coverage = parent.parse_daymet(stream.read(), point, freeze_contract)
            objects.append((f"{point['point_id']}.json", parent.canonical_bytes(payload)))
            for field, rows in coverage["availability"].items():
                for row in rows:
                    availability[(point["regime"], point["role"], field, row["year"], row["month"], row["state"])] += row["count"]
            for field, summary in coverage["statistics"].items():
                key = (point["regime"], point["role"], field)
                target = statistics.setdefault(
                    key,
                    {
                        "count": 0,
                        "maximum": None,
                        "minimum": None,
                        "sum": 0.0,
                        "sum_squares": 0.0,
                    },
                )
                target["count"] += summary["count"]
                target["sum"] += summary["sum"]
                target["sum_squares"] += summary["sum_squares"]
                target["minimum"] = summary["minimum"] if target["minimum"] is None else min(target["minimum"], summary["minimum"])
                target["maximum"] = summary["maximum"] if target["maximum"] is None else max(target["maximum"], summary["maximum"])
        path = RAW / "training/daymet-v1" / f"daymet-{shard_index // 24:03d}.tar.gz"
        identity = parent.deterministic_tar_gz(path, objects)
        identity.update(
            {
                "object_count": len(points),
                "point_ids": [row["point_id"] for row in points],
                "schema_version": 1,
                "source_id": "daymet_v4r1_single_pixel",
            }
        )
        shards.append(identity)

    coverage = {
        "availability": [
            {
                "count": count,
                "field": field,
                "month": month,
                "regime": regime,
                "role": role,
                "state": state,
                "year": year,
            }
            for (regime, role, field, year, month, state), count in sorted(availability.items())
        ],
        "schema_version": 1,
        "statistics": [
            {**summary, "field": field, "regime": regime, "role": role}
            for (regime, role, field), summary in sorted(statistics.items())
        ],
    }
    write(RAW / "daymet/coverage-v1.json", coverage)
    write(SHARD_MANIFEST, {"schema_version": 1, "shards": shards})

    parent_normalized = read(A10M1 / "artifacts/normalized-manifest-v1.json")
    parent_normalization = read(A10M1 / "artifacts/normalization-statistics-v1.json")
    daymet_counts = Counter((row["regime"], row["role"]) for row in selected)
    daymet_tiles = defaultdict(set)
    tile_roles = defaultdict(set)
    for row in selected:
        daymet_tiles[(row["regime"], row["role"])].add(row["tile_id"])
        tile_roles[row["tile_id"]].add(row["role"])
    leakage = dict(parent_normalized["leakage_audit"])
    leakage["tile_role_splits"] = sorted(tile for tile, roles in tile_roles.items() if len(roles) != 1)
    if any(leakage.values()):
        raise RuntimeError(f"successor leakage audit failed: {leakage}")
    coverage_summary = dict(parent_normalized["coverage_summary"])
    coverage_summary["daymet"] = [
        {
            "locations": daymet_counts[(regime, role)],
            "regime": regime,
            "role": role,
            "tiles": len(daymet_tiles[(regime, role)]),
        }
        for regime in freeze_contract["regime_frames"]
        for role in ("candidate_fit", "fit_validation")
    ]
    normalization_rows = []
    for (regime, role, field), row in sorted(statistics.items()):
        if role != "candidate_fit" or row["count"] == 0:
            continue
        mean = row["sum"] / row["count"]
        variance = max(0.0, row["sum_squares"] / row["count"] - mean**2)
        normalization_rows.append(
            {
                "count": row["count"],
                "field": field,
                "maximum": row["maximum"],
                "mean": mean,
                "minimum": row["minimum"],
                "regime": regime,
                "source_id": "daymet_v4r1_single_pixel",
                "standard_deviation": math.sqrt(variance),
            }
        )
    normalization_rows.extend(
        row for row in parent_normalization["rows"] if row["source_id"] != "daymet_v4r1_single_pixel"
    )
    normalized = {
        "cohort_contract_sha256": digest(CONTRACT),
        "cohort_selection_sha256": digest(SELECTION),
        "coverage_summary": coverage_summary,
        "daymet_shards": shards,
        "freeze_sha256": digest(A10M1 / "artifacts/a10m1-freeze-v1.json"),
        "inherited_development_objects": parent_normalized["inherited_development_objects"],
        "leakage_audit": leakage,
        "manifest_id": "a10m5r15r1-normalized-manifest-v1",
        "schema_version": 1,
        "uscrn_objects": parent_normalized["uscrn_objects"],
    }
    source_manifest = {
        "confirmation_target_series_accessed": False,
        "cohort_contract_sha256": digest(CONTRACT),
        "cohort_selection_sha256": digest(SELECTION),
        "original_daymet_access_ledger_sha256": contract["predecessors"]["a10m1_original_access_ledger_sha256"],
        "package_id": contract["package_id"],
        "schema_version": "a10m5r15r1-source-manifest-1",
        "successor_daymet_access_ledger_sha256": digest(LEDGER),
    }
    parent_transfer = read(A10M1 / "artifacts/offline-transfer-manifest-v1.json")
    inherited_objects = [row for row in parent_transfer["objects"] if "/daymet-v2/" not in row["path"]]
    transfer_objects = [
        {
            "bytes": row["bytes"],
            "destination_class": "job_local_stage",
            "path": row["path"],
            "sha256": row["sha256"],
        }
        for row in shards
    ] + inherited_objects
    transfer = {
        "aggregate_bytes": sum(row["bytes"] for row in transfer_objects),
        "hash_required_before_use": True,
        "manifest_id": "a10m5r15r1-offline-transfer-v1",
        "objects": transfer_objects,
        "schema_version": 1,
        "source_manifest_sha256": hashlib.sha256(canonical(source_manifest)).hexdigest(),
        "small_file_policy": parent_transfer["small_file_policy"],
    }
    write(SOURCE_MANIFEST, source_manifest)
    write(NORMALIZED_MANIFEST, normalized)
    write(NORMALIZATION, {"fit_role_only": "candidate_fit", "rows": normalization_rows, "schema_version": 1})
    write(TRANSFER_MANIFEST, transfer)
    write(
        BUILD_RECEIPT,
        {
            "aggregate_bytes": transfer["aggregate_bytes"],
            "cohort_selection_sha256": digest(SELECTION),
            "daymet_location_count": len(selected),
            "daymet_shard_count": len(shards),
            "normalized_manifest_sha256": digest(NORMALIZED_MANIFEST),
            "normalization_statistics_sha256": digest(NORMALIZATION),
            "package_id": contract["package_id"],
            "schema_version": "a10m5r15r1-cohort-build-1",
            "transfer_manifest_sha256": digest(TRANSFER_MANIFEST),
            "transfer_object_count": len(transfer_objects),
            "valid": True,
        },
    )
    print("A10M5R15R1-CORPUS-BUILT")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "acquire", "finalize", "build"))
    parser.add_argument("--source-commit")
    options = parser.parse_args()
    if options.mode == "freeze":
        freeze()
    elif options.mode == "acquire":
        if options.source_commit is None:
            raise RuntimeError("--source-commit is required for acquisition")
        acquire(options.source_commit)
    elif options.mode == "finalize":
        finalize()
    else:
        build()


if __name__ == "__main__":
    main()
