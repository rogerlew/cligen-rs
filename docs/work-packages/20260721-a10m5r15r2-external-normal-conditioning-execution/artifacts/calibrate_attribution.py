#!/usr/bin/env python3
"""Freeze the candidate-blind rev-2 attribution margin from accepted R14 E0."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from rev2_selector import digest, extract_observations, run_selector


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
SOURCE_COMMIT = "719d83451ddff698b280219708f7648ff73c8f9d"
ASSET_MANIFEST_SHA256 = "7988efbb342045f0df5ce05ddb810cc36c8be46f145f4c0bc531d02c56291c05"
E0_CONFIGURATION = "centered_location_ou_smooth_climatology-k2"
E0_STREAM_SHA256 = "2bb8379f639712dc864308510bd2a8c10ac9c39ea3cae609abdc2a2bf51384ff"


def sequence_sha256(values: list[float]) -> str:
    return hashlib.sha256(
        json.dumps(values, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    published = subprocess.run(
        ("git", "show", f"{head}:{relative}"), cwd=REPO, check=True, capture_output=True
    ).stdout
    if head != upstream or published != Path(__file__).read_bytes():
        raise RuntimeError("calibration requires exact published main")
    if options.work_root.exists() or options.output.exists():
        raise RuntimeError("fresh calibration destinations required")
    manifest = json.loads((options.asset_root / "asset-manifest.json").read_text(encoding="utf-8"))
    stream = options.evidence_root / "results/continuous-location-ou-smooth-climatology-k2/streams.npz"
    if not (
        digest(options.asset_root / "asset-manifest.json") == ASSET_MANIFEST_SHA256
        and manifest.get("source_commit") == SOURCE_COMMIT
        and digest(stream) == E0_STREAM_SHA256
    ):
        raise RuntimeError("accepted R14 E0 calibration source drift")
    sites = json.loads((options.asset_root / "sites.json").read_text(encoding="utf-8"))["sites"]
    observations = options.work_root / "observations"
    extract_observations(options.corpus, observations, sites)
    outputs = []
    try:
        for seed in (410542, 410543):
            result, sequences = run_selector(
                asset_root=options.asset_root,
                binary=options.binary,
                data_root=options.data_root,
                evidence_root=options.evidence_root,
                observations=observations,
                output_root=options.work_root / f"sequence-{seed}",
                bootstrap_seed=seed,
            )
            if E0_CONFIGURATION not in sequences or result.get("protected_roles_opened") != []:
                raise RuntimeError("accepted E0 calibration replay incomplete")
            outputs.append(sequences[E0_CONFIGURATION])
        differences = [
            abs(left - right) / max(left, right)
            for left, right in zip(outputs[0], outputs[1])
        ]
        if len(differences) != 1000 or any(value < 0 for value in differences):
            raise RuntimeError("calibration replicate drift")
        nearest_rank_q90 = sorted(differences)[899]
        receipt = {
            "asset_manifest_sha256": ASSET_MANIFEST_SHA256,
            "candidate_output_accessed": False,
            "calibration_configuration": E0_CONFIGURATION,
            "calibration_source_commit": SOURCE_COMMIT,
            "calibration_stream_sha256": E0_STREAM_SHA256,
            "difference_sequence_sha256": sequence_sha256(differences),
            "gates": {
                "candidate_blind": True,
                "replicate_count": len(differences) == 1000,
                "sequence_seeds_exact": True,
                "strictly_positive_margin": max(1e-6, nearest_rank_q90) > 0,
            },
            "margin": max(1e-6, nearest_rank_q90),
            "nearest_rank_q90": nearest_rank_q90,
            "nearest_rank_zero_based_index": 899,
            "package_id": PACKAGE_ID,
            "protected_roles_opened": [],
            "replicates": 1000,
            "schema_version": 1,
            "sequence_seeds": [410542, 410543],
            "sequence_sha256": [sequence_sha256(value) for value in outputs],
            "source_commit": head,
            "valid": True,
        }
        semantic = json.dumps(receipt, separators=(",", ":"), sort_keys=True).encode("utf-8")
        receipt["record_sha256"] = hashlib.sha256(semantic).hexdigest()
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"A10M5R15R2-ATTRIBUTION-MARGIN {receipt['margin']:.17g}")
    except BaseException:
        if options.output.exists():
            options.output.unlink()
        raise
    finally:
        shutil.rmtree(options.work_root, ignore_errors=True)


if __name__ == "__main__":
    main()
