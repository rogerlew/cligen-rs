#!/usr/bin/env python3
"""Compare first and replayed A5d1 paths excluding recorded runtimes."""

from __future__ import annotations

import hashlib
import json
import math
import tarfile

from a5d1_common import PACKAGE, freeze_identity, load_json, sha256, write_json


FIRST_ARCHIVE = PACKAGE / "detailed-evidence-v1.tar.gz"
REPLAY_ARCHIVE = PACKAGE / "replay-evidence-v1.tar.gz"
REPLAY_MANIFEST = PACKAGE / "replay-evidence-manifest-v1.json"
OUTPUT = PACKAGE / "semantic-replay-audit-v1.json"
TOLERANCE = 2.0e-10


def archive_payloads(path) -> dict[str, bytes]:
    with tarfile.open(path, "r:gz") as archive:
        result = {}
        for member in archive.getmembers():
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError(f"unreadable archive member: {member.name}")
            result[member.name] = handle.read()
        return result


def semantic_hash(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def strip_runtime(value):
    if isinstance(value, dict):
        return {
            key: strip_runtime(item)
            for key, item in value.items()
            if key not in ("wall_seconds", "total_wall_seconds")
        }
    if isinstance(value, list):
        return [strip_runtime(item) for item in value]
    return value


def compare(left, right, stats: dict, label: str) -> None:
    if isinstance(left, bool) or isinstance(right, bool):
        if left is not right:
            stats["structural_mismatches"].append(label)
    elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
        stats["numeric_comparisons"] += 1
        absolute = abs(float(left) - float(right))
        relative = absolute / max(abs(float(left)), abs(float(right)), 1.0e-300)
        stats["maximum_absolute_difference"] = max(stats["maximum_absolute_difference"], absolute)
        stats["maximum_relative_difference"] = max(stats["maximum_relative_difference"], relative)
        if not math.isclose(float(left), float(right), rel_tol=TOLERANCE, abs_tol=TOLERANCE):
            stats["numeric_mismatches"].append(label)
    elif isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            stats["structural_mismatches"].append(label + ".keys")
            return
        for key in sorted(left):
            compare(left[key], right[key], stats, f"{label}.{key}")
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            stats["structural_mismatches"].append(label + ".length")
            return
        for index, (a, b) in enumerate(zip(left, right)):
            compare(a, b, stats, f"{label}[{index}]")
    elif left != right:
        stats["structural_mismatches"].append(label)


def main() -> None:
    freeze_sha256 = freeze_identity()
    replay_manifest = load_json(REPLAY_MANIFEST)
    if replay_manifest["freeze_sha256"] != freeze_sha256:
        raise ValueError("replay freeze mismatch")
    if replay_manifest["archive"]["sha256"] != sha256(REPLAY_ARCHIVE):
        raise ValueError("replay archive hash mismatch")
    first = archive_payloads(FIRST_ARCHIVE)
    replay = archive_payloads(REPLAY_ARCHIVE)
    first_paths = {name: payload for name, payload in first.items() if name.startswith("paths/")}
    replay_paths = {name: payload for name, payload in replay.items() if name.startswith("paths/")}
    if set(first_paths) != set(replay_paths) or len(first_paths) != 306:
        raise ValueError("replay path member set mismatch")
    stats = {
        "numeric_comparisons": 0,
        "maximum_absolute_difference": 0.0,
        "maximum_relative_difference": 0.0,
        "numeric_mismatches": [],
        "structural_mismatches": [],
    }
    exact_member_matches = 0
    first_hashes = []
    replay_hashes = []
    for name in sorted(first_paths):
        left = strip_runtime(json.loads(first_paths[name]))
        right = strip_runtime(json.loads(replay_paths[name]))
        exact_member_matches += int(left == right)
        first_hashes.append((name, semantic_hash(left)))
        replay_hashes.append((name, semantic_hash(right)))
        compare(left, right, stats, name)
    first_aggregate = load_json(PACKAGE / "path-results-v1.json")
    replay_aggregate = json.loads(replay["path-results-v1.json"])
    first_aggregate = strip_runtime(first_aggregate)
    replay_aggregate = strip_runtime(replay_aggregate)
    for row in first_aggregate["records"]:
        row["path_record"].pop("sha256", None)
    for row in replay_aggregate["records"]:
        row["path_record"].pop("sha256", None)
    compare(first_aggregate, replay_aggregate, stats, "path-results")
    equivalent = not stats["numeric_mismatches"] and not stats["structural_mismatches"]
    value = {
        "semantic_replay_audit_schema_version": 1,
        "post_result_closure_evidence": True,
        "freeze_sha256": freeze_sha256,
        "excluded_fields": ["wall_seconds", "total_wall_seconds", "path_record.sha256"],
        "numeric_tolerance_relative_and_absolute": TOLERANCE,
        "path_count": len(first_paths),
        "exact_member_matches_after_runtime_exclusion": exact_member_matches,
        "first_semantic_sha256": semantic_hash(first_hashes),
        "replay_semantic_sha256": semantic_hash(replay_hashes),
        "exact_semantic_match": first_hashes == replay_hashes,
        "numeric_comparisons": stats["numeric_comparisons"],
        "maximum_absolute_difference": stats["maximum_absolute_difference"],
        "maximum_relative_difference": stats["maximum_relative_difference"],
        "numeric_mismatch_count": len(stats["numeric_mismatches"]),
        "structural_mismatch_count": len(stats["structural_mismatches"]),
        "numeric_mismatch_examples": stats["numeric_mismatches"][:10],
        "structural_mismatch_examples": stats["structural_mismatches"][:10],
        "semantic_equivalent": equivalent,
        "first_archive_sha256": sha256(FIRST_ARCHIVE),
        "replay_archive_sha256": sha256(REPLAY_ARCHIVE),
    }
    write_json(OUTPUT, value)
    if not equivalent:
        raise SystemExit("A5d1 semantic replay: FAIL")
    print(
        "A5d1 semantic replay: PASS "
        f"({len(first_paths)} paths; exact={value['exact_semantic_match']}; "
        f"max_abs={value['maximum_absolute_difference']:.3e})"
    )


if __name__ == "__main__":
    main()
