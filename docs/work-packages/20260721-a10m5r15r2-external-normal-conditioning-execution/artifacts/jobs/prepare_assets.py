#!/usr/bin/env python3
"""Prepare fresh A10M5R15R2 assets from authenticated R14R2R2 r3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
R1 = PACKAGE.parent / "20260721-a10m5r15r1-prism-eligible-cohort"
CONTRACT = PACKAGE / "artifacts/execution-contract.json"
CALIBRATION = PACKAGE / "artifacts/attribution-calibration.json"
REPLAY_SOURCE = PACKAGE / "artifacts/run_temporal_replay.py"
PARENT_MANIFEST_SHA256 = "7988efbb342045f0df5ce05ddb810cc36c8be46f145f4c0bc531d02c56291c05"
PARENT_PACKAGE = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
RUN_ID = "a10m5r15r2-external-normal-conditioning-execution-r0"
PORTFOLIO_ROLE = "external-normal-conditioning-portfolio"
RECORD_TYPE = "a10m5r15r2-submission-admission"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def published(source_commit: str) -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    if source_commit != head or head != upstream or branch != "main":
        raise RuntimeError("A10M5R15R2 assets require exact published main")
    for path in (
        Path(__file__).resolve(),
        CONTRACT,
        PACKAGE / "artifacts/portfolio-role-map.json",
        PACKAGE / "artifacts/corpus-layout-pin.json",
        PACKAGE / "artifacts/verify_corpus_layout.py",
        PACKAGE / "artifacts/rev2_selector.py",
        PACKAGE / "artifacts/run_runtime_benchmarks.py",
        CALIBRATION,
        REPLAY_SOURCE,
        PACKAGE / "artifacts/jobs/continuous_core.py",
        PACKAGE / "artifacts/jobs/continuous_candidate_experiment.py",
        PACKAGE / "artifacts/jobs/legacy_core.py",
        PACKAGE / "artifacts/jobs/build_control_records.py",
        PACKAGE / "artifacts/jobs/materialize_admission.py",
    ):
        if path.read_bytes() != git_bytes(source_commit, path):
            raise RuntimeError(f"published execution source drift: {path.name}")


def parent_manifest(root: Path) -> dict:
    path = root / "asset-manifest.json"
    if path.is_symlink() or not path.is_file() or digest(path) != PARENT_MANIFEST_SHA256:
        raise RuntimeError("R14R2R2 r3 parent asset identity drift")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("package_id") != PARENT_PACKAGE or manifest.get("protected_roles_opened") != []:
        raise RuntimeError("R14R2R2 r3 parent authority drift")
    for name, expected in manifest["assets"].items():
        member = root / name
        if member.is_symlink() or member.stat().st_nlink != 1 or identity(member) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"R14R2R2 parent member drift: {name}")
    return manifest


def rewrite_json(path: Path, transform) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    transform(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def transform_contracts(output: Path, contract: dict) -> None:
    arms = contract["arms"]
    candidates = [row["candidate"] for row in arms]
    roles = [row["role"] for row in arms]

    def portfolio(value):
        inherited_definition = value["architectures"]["centered_location_ou_smooth_climatology"]
        common = {
            "backbone_trainable": False,
            "centered_scale_ou": False,
            "decoder_head_indices": [0, 1, 3, 5],
            "decoder_head_semantics": inherited_definition["decoder_head_semantics"],
            "differentiable_selector_metric_count": 188,
            "location_ou_head_indices": [0, 1, 3, 5],
            "medium_time_scale_days": [14.0, 180.0],
            "observed_weather_inputs": [],
            "scale_ou_head_indices": [],
            "selector_aligned_annual_objective": True,
            "slow_state": True,
            "slow_time_scale_days": [180.0, 1460.0],
            "state_clock": "continuous_time_exact_ou_discretized_daily",
            "state_reset_boundaries": [],
        }
        value["architectures"] = {
            arms[0]["candidate"]: {
                **inherited_definition,
                "arm": "E0",
                "candidate_parameter_count": 1820,
                "parameter_ceiling": 340000,
                "parameter_count": 278747,
                "uses_normals": False,
                "uses_p2_backbone": True,
            },
            arms[1]["candidate"]: {
                **inherited_definition,
                "arm": "E1",
                "candidate_parameter_count": 2540,
                "deterministic_climatology_basis": "bias_free_5_by_40_outer_product_200_to_4",
                "deterministic_climatology_context": [
                    "sin_day_of_year", "cos_day_of_year", "latitude", "longitude",
                    "elevation", "36_candidate_fit_normalized_prism_monthly_normals",
                ],
                "deterministic_climatology_parameter_count": 800,
                "parameter_ceiling": 340000,
                "parameter_count": 279467,
                "uses_normals": True,
                "uses_p2_backbone": True,
            },
            arms[2]["candidate"]: {
                **common,
                "arm": "E2C",
                "base": "bias_free_descriptor_baseline_plus_centered_ou_residual",
                "baseline_mapping": "bias_free_20_to_15",
                "baseline_parameter_count": 300,
                "candidate_parameter_count": 2040,
                "context_inputs": ["sin_day_of_year", "cos_day_of_year", "latitude", "longitude", "elevation"],
                "parameter_ceiling": 330000,
                "parameter_count": 2040,
                "uses_normals": False,
                "uses_p2_backbone": False,
            },
            arms[3]["candidate"]: {
                **common,
                "arm": "E2",
                "base": "normal_anchored_mapping_plus_centered_ou_residual",
                "baseline_mapping": "bias_free_20_to_11_plus_bias_free_200_to_4",
                "baseline_parameter_count": 1020,
                "candidate_parameter_count": 2760,
                "context_inputs": [
                    "sin_day_of_year", "cos_day_of_year", "latitude", "longitude",
                    "elevation", "36_candidate_fit_normalized_prism_monthly_normals",
                ],
                "parameter_ceiling": 330000,
                "parameter_count": 2760,
                "uses_normals": True,
                "uses_p2_backbone": False,
            },
        }
        value["package_id"] = PACKAGE_ID
        value["roles"] = roles
        value["specification"] = "SPEC-A10-EXTERNAL-NORMAL-CONDITIONING-rev2"
        value["stochastic"]["evaluation_members"] = 8
        value["controls"]["capacities"]["K2"]["candidate_parameter_ceiling"] = 340000
        value["candidate_parameter_ceilings"] = {
            row["candidate"]: 340000 if row["uses_p2"] else 330000 for row in arms
        }
        value["status"] = "ratified"

    def temporal(value):
        value["contract_id"] = "a10m5r15r2-external-normal-conditioning-v1"
        value["predecessor_terminal"] = contract["corpus"]["terminal"]
        value["roles"] = [
            {
                "architecture": row["candidate"],
                "backbone_capacity": "P2" if row["uses_p2"] else "NONE",
                "capacity": row["capacity"],
                "configuration_id": row["configuration_id"],
                "role_id": row["role"],
                "seeds": [147031, 271828, 314159],
            }
            for row in arms
        ]
        value["resources"] = {
            "control_minutes": 30,
            "gpu_jobs": 2,
            "gpu_minute_ceiling": 515,
            "maximum_concurrent_candidates": 2,
            "portfolio_l40_count": 2,
            "portfolio_minutes": 240,
            "recovery_minutes": 5,
        }

    rewrite_json(output / "portfolio-contract.json", portfolio)
    rewrite_json(output / "temporal-contract.json", temporal)
    (output / "portfolio-role-map.json").write_bytes(
        (PACKAGE / "artifacts/portfolio-role-map.json").read_bytes()
    )
    role_map = json.loads((output / "portfolio-role-map.json").read_text())
    if [row["candidate"] for row in role_map["processes"]] != candidates:
        raise RuntimeError("role map and execution contract differ")


def transform_operational(output: Path, arms: list[dict]) -> None:
    old_roles = (
        "continuous-location-ou-k2",
        "continuous-location-ou-smooth-climatology-k2",
        "continuous-location-scale-ou-k2",
        "continuous-location-scale-ou-smooth-climatology-k2",
    )
    old_candidates = (
        "centered_location_ou",
        "centered_location_ou_smooth_climatology",
        "centered_location_and_scale_ou",
        "centered_location_and_scale_ou_smooth_climatology",
    )
    replacements = {
        PARENT_PACKAGE: PACKAGE_ID,
        "a10m5r14r2r2-two-l40-two-wave-portfolio-r3": RUN_ID,
        "a10m5r14r2r2-submission-admission": RECORD_TYPE,
        "continuous-distribution-head-factorial-portfolio": PORTFOLIO_ROLE,
        **{old: row["role"] for old, row in zip(old_roles, arms)},
        **{old: row["candidate"] for old, row in zip(old_candidates, arms)},
        "HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE": "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT",
        "A10M5R14-TEMPORAL-READY": "A10M5R15-TEMPORAL-READY",
    }
    protected = {
        "build_control_records.py",
        "continuous_candidate_experiment.py",
        "continuous_core.py",
        "inherited_r15_candidate_experiment.py",
        "inherited_r15_distribution_core.py",
        "inherited_r15_legacy_core.py",
        "legacy_core.py",
        "materialize_admission.py",
    }
    for path in output.iterdir():
        if not path.is_file() or path.name in protected or path.suffix not in (".py", ".sh"):
            continue
        text = path.read_text(encoding="utf-8")
        for old in sorted(replacements, key=len, reverse=True):
            text = text.replace(old, replacements[old])
        path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-assets", type=Path, required=True)
    parser.add_argument("--corpus-archive", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", options.source_commit) is None:
        raise RuntimeError("full source commit required")
    published(options.source_commit)
    parent = parent_manifest(options.parent_assets)
    if options.output.exists():
        raise RuntimeError("fresh execution asset output required")
    receipt_path = PACKAGE / "artifacts/corpus-archive-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("valid") or identity(options.corpus_archive) != {key: receipt[key] for key in ("bytes", "sha256")}:
        raise RuntimeError("successor corpus archive identity drift")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    if not (
        calibration.get("valid") is True
        and calibration.get("candidate_output_accessed") is False
        and calibration.get("protected_roles_opened") == []
        and calibration.get("package_id") == PACKAGE_ID
        and all(calibration.get("gates", {}).values())
        and digest(CALIBRATION) == contract["replay"].get("calibration_receipt_sha256")
    ):
        raise RuntimeError("candidate-blind attribution calibration is not frozen")
    shutil.copytree(options.parent_assets, options.output, symlinks=False)
    for name in ("controller-admissions", "__pycache__"):
        path = options.output / name
        if path.exists():
            shutil.rmtree(path)
    (options.output / "controller-admissions").mkdir(mode=0o700)
    renames = {
        "continuous_candidate_experiment.py": "inherited_r15_candidate_experiment.py",
        "continuous_core.py": "inherited_r15_distribution_core.py",
        "legacy_core.py": "inherited_r15_legacy_core.py",
    }
    for old, new in renames.items():
        os.replace(options.output / old, options.output / new)
    (options.output / "run_temporal_replay.py").unlink()
    os.replace(
        options.output / "job-continuous-distribution-head-factorial-portfolio.sh",
        options.output / f"job-{PORTFOLIO_ROLE}.sh",
    )
    overlays = {
        "build_control_records.py": PACKAGE / "artifacts/jobs/build_control_records.py",
        "continuous_candidate_experiment.py": PACKAGE / "artifacts/jobs/continuous_candidate_experiment.py",
        "continuous_core.py": PACKAGE / "artifacts/jobs/continuous_core.py",
        "legacy_core.py": PACKAGE / "artifacts/jobs/legacy_core.py",
        "materialize_admission.py": PACKAGE / "artifacts/jobs/materialize_admission.py",
        "execution-contract.json": PACKAGE / "artifacts/execution-contract.json",
        "corpus-layout-pin.json": PACKAGE / "artifacts/corpus-layout-pin.json",
        "verify_corpus_layout.py": PACKAGE / "artifacts/verify_corpus_layout.py",
        "rev2_selector.py": PACKAGE / "artifacts/rev2_selector.py",
        "run_runtime_benchmarks.py": PACKAGE / "artifacts/run_runtime_benchmarks.py",
    }
    for name, source in overlays.items():
        (options.output / name).write_bytes(git_bytes(options.source_commit, source))
    replay_payload = git_bytes(options.source_commit, REPLAY_SOURCE)
    (options.output / "post-collection-replay-entry.json").write_text(
        json.dumps(
            {
                "bytes": len(replay_payload),
                "execution_location": "published repository after authenticated collection",
                "path": REPLAY_SOURCE.relative_to(REPO).as_posix(),
                "sha256": hashlib.sha256(replay_payload).hexdigest(),
                "source_commit": options.source_commit,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (options.output / "attribution-calibration.json").write_bytes(
        git_bytes(options.source_commit, CALIBRATION)
    )
    shutil.copy2(options.corpus_archive, options.output / "corpus.tar")
    for name in (
        "normal-conditioning-index.json",
        "normal-conditioning-receipt.json",
        "normal-conditioning.f32le",
        "normalizer.f64le",
    ):
        source = R1 / "artifacts/normal-conditioning" / name
        (options.output / name).write_bytes(source.read_bytes())
    transform_contracts(options.output, contract)
    transform_operational(options.output, contract["arms"])
    for path in options.output.iterdir():
        if path.is_file() and path.suffix in (".py", ".sh"):
            path.chmod(0o700)
    source_paths = {
        name: path.relative_to(REPO).as_posix() for name, path in overlays.items()
    }
    assets = {}
    for path in sorted(options.output.iterdir()):
        if path.is_file() and path.name != "asset-manifest.json":
            assets[path.name] = {
                **identity(path),
                **({"source_path": source_paths[path.name]} if path.name in source_paths else {}),
            }
    manifest = {
        "assets": assets,
        "canonical_configuration_id": parent["canonical_configuration_id"],
        "canonical_configuration_semantic_sha256": parent["canonical_configuration_semantic_sha256"],
        "package_id": PACKAGE_ID,
        "parent_asset_manifest_sha256": PARENT_MANIFEST_SHA256,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": options.source_commit,
    }
    (options.output / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"A10M5R15R2-ASSETS-PREPARED {digest(options.output / 'asset-manifest.json')}")


if __name__ == "__main__":
    main()
