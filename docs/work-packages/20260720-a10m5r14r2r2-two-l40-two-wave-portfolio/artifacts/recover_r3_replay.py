#!/usr/bin/env python3
"""Recover the r3 pre-cleanup replay without weakening its source audit.

R3's preparer rewrote the inherited replay's execution identity, but did not
retain a source-path entry for that generated asset.  This recovery verifies
that exact deterministic rewrite from the published R14R2R1 source before it
executes the unchanged inherited selector logic.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

PARENT_COMMIT = "6463ab2bebcf016c371afc56e31ffc7156a2fb95"
PARENT_PACKAGE_ID = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
PARENT_RUN_ID = "a10m5r14r2r1-inherited-admission-checker-identity-remedy-r0"
PACKAGE_ID = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
RUN_ID = "a10m5r14r2r2-two-l40-two-wave-portfolio-r3"
PARENT_RECORD = "a10m5r14r2r1-submission-admission"
RECORD = "a10m5r14r2r2-submission-admission"
PARENT_REPLAY = (
    "docs/work-packages/"
    f"{PARENT_PACKAGE_ID}/artifacts/run_temporal_replay.py"
)
BASE_REPLAY = (
    "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/"
    "artifacts/run_temporal_replay.py"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def published_bytes(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout


def expected_r3_replay(repo: Path) -> bytes:
    """Reproduce the exact identity rewrite in prepare_assets.py."""
    text = published_bytes(repo, PARENT_COMMIT, PARENT_REPLAY).decode()
    return (
        text.replace(PARENT_PACKAGE_ID, PACKAGE_ID)
        .replace(PARENT_RUN_ID, RUN_ID)
        .replace(PARENT_RECORD, RECORD)
        .replace("a10m5r14r2r1-precleanup-replay", "a10m5r14r2r2-precleanup-replay")
        .replace(
            "a10m5r14r2r1-immediate-pre-submit-occupancy",
            "a10m5r14r2r2-immediate-pre-submit-occupancy",
        )
        .encode()
    )


def load_r3_validator(cache_replay: Path, base_replay: Path) -> types.ModuleType:
    """Load only the frozen r3 portfolio validator with a published parent."""
    source = cache_replay.read_text()
    old_parent = '''PARENT = (
    PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial"
    / "artifacts/run_temporal_replay.py"
)
'''
    if source.count(old_parent) != 1:
        raise RuntimeError("r3 replay parent anchor drift")
    source = source.replace(old_parent, f"PARENT = Path({str(base_replay)!r})\n")
    substitutions = {
        "len(allocation_tokens) == 4": "len(allocation_tokens) == 2",
        "len(set(allocation_tokens)) == 4": "len(set(allocation_tokens)) == 2",
        "len(launcher_devices) == 4": "len(launcher_devices) == 2",
        "[device.get(\"index\") for device in launcher_devices] == [0, 1, 2, 3]": "[device.get(\"index\") for device in launcher_devices] == [0, 1]",
        "allocation_tokens[row[\"slot\"]]": "allocation_tokens[row[\"allocation_token_index\"]]",
    }
    for old, new in substitutions.items():
        if source.count(old) != 1:
            raise RuntimeError(f"r3 two-wave replay anchor drift: {old}")
        source = source.replace(old, new)
    module = types.ModuleType("a10m5r14r2r2_r3_replay")
    module.__file__ = str(cache_replay)
    exec(compile(source, str(cache_replay), "exec"), module.__dict__)
    return module


def recovery_asset_root(asset_root: Path, output_parent: Path) -> Path:
    """Materialize only the selector surface needed for four-way diagnostics."""
    root = output_parent / "recovery-assets"
    if root.exists():
        raise RuntimeError("fresh recovery asset root required")
    root.mkdir(mode=0o700)
    manifest = json.loads((asset_root / "asset-manifest.json").read_text())
    for name in (
        "calendar-control-expectation.json",
        "portfolio-contract.json",
        "sites.json",
        "temporal-contract.json",
        "temporal_metrics.py",
    ):
        (root / name).symlink_to(asset_root / name)
    selector = (asset_root / "temporal_select.py").read_text()
    old = '''        left, right = configurations
        left_values = np.asarray(values[left])
        right_values = np.asarray(values[right])
        annual_diagnostics[family] = {
            "configurations": summaries,
            "probability_medium_lower_error": float(np.mean(left_values < right_values)),
            "selection_gating": False,
        }
'''
    new = '''        pairwise_probability_lower_error = {}
        for left_index, left in enumerate(configurations):
            for right in configurations[left_index + 1:]:
                pairwise_probability_lower_error[f"{left}__vs__{right}"] = float(
                    np.mean(np.asarray(values[left]) < np.asarray(values[right]))
                )
        annual_diagnostics[family] = {
            "configurations": summaries,
            "pairwise_probability_lower_error": pairwise_probability_lower_error,
            "selection_gating": False,
        }
'''
    if selector.count(old) != 1:
        raise RuntimeError("four-way annual diagnostic anchor drift")
    selector_path = root / "temporal_select.py"
    selector_path.write_text(selector.replace(old, new))
    manifest["assets"]["temporal_select.py"].update(
        {"bytes": selector_path.stat().st_size, "sha256": digest(selector_path)}
    )
    (root / "asset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-replay", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--semantic-plan", type=Path, required=True)
    parser.add_argument("--plan-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()

    repo = Path(__file__).resolve().parents[4]
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != "719d83451ddff698b280219708f7648ff73c8f9d":
        raise RuntimeError("recovery requires the exact r3 published source")
    expected = expected_r3_replay(repo)
    if options.cache_replay.read_bytes() != expected:
        raise RuntimeError("cached r3 replay is not the deterministic published rebind")
    base_replay = repo / BASE_REPLAY
    validator = load_r3_validator(options.cache_replay, base_replay)
    raw = validator.parent.read_toolkit_object(options.semantic_plan)
    receipt = validator.parent.read_toolkit_object(options.plan_receipt)
    collection = validator.parent.read_toolkit_object(options.collection)
    plan = validator.parent.authenticate_plan(raw, receipt, head)
    if not (
        validator.parent.authenticated(collection)
        and collection.get("package_id") == PACKAGE_ID
        and collection.get("run_id") == RUN_ID
        and collection.get("source_commit") == head
        and collection.get("plan_id") == receipt.get("plan_id")
        and collection.get("remote_cleanup_performed") is not True
    ):
        raise RuntimeError("r3 collection authentication failed before recovery replay")
    identities = validator.verify_portfolio_records(options.evidence_root, plan, collection)
    selector_root = recovery_asset_root(options.asset_root, options.output_root.parent)

    replay_args = [
        "run_temporal_replay.py",
        "--python", str(options.python), "--binary", str(options.binary),
        "--data-root", str(options.data_root), "--corpus", str(options.corpus),
        "--asset-root", str(selector_root), "--evidence-root", str(options.evidence_root),
        "--collection", str(options.collection), "--semantic-plan", str(options.semantic_plan),
        "--plan-receipt", str(options.plan_receipt), "--output-root", str(options.output_root),
    ]
    previous_argv = sys.argv
    try:
        sys.argv = replay_args
        validator.parent.main()
    finally:
        sys.argv = previous_argv
    replay_path = options.output_root / "replay-identity.json"
    replay = json.loads(replay_path.read_text())
    if replay.get("package_id") != PACKAGE_ID or replay.get("run_id") != RUN_ID:
        raise RuntimeError("inherited replay identity was not rebound to r3")
    replay["record_type"] = "a10m5r14r2r2-precleanup-replay"
    replay["portfolio_evidence"] = identities
    replay["recovery_selector_asset_manifest_sha256"] = digest(
        selector_root / "asset-manifest.json"
    )
    replay.pop("record_sha256", None)
    replay["record_sha256"] = hashlib.sha256(validator.parent.canonical(replay)).hexdigest()
    replay_path.write_text(json.dumps(replay, indent=2, sort_keys=True) + "\n")
    attestation = {
        "base_replay_source": BASE_REPLAY,
        "cache_replay": {"bytes": options.cache_replay.stat().st_size, "sha256": digest(options.cache_replay)},
        "deterministic_parent_source": {"commit": PARENT_COMMIT, "path": PARENT_REPLAY},
        "package_id": PACKAGE_ID,
        "recovery_selector": {
            "bytes": (selector_root / "temporal_select.py").stat().st_size,
            "sha256": digest(selector_root / "temporal_select.py"),
        },
        "replay_record_sha256": replay["record_sha256"],
        "run_id": RUN_ID,
        "source_commit": head,
    }
    attestation["record_sha256"] = hashlib.sha256(
        validator.parent.canonical(attestation)
    ).hexdigest()
    (options.output_root / "replay-recovery-attestation.json").write_text(
        json.dumps(attestation, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
