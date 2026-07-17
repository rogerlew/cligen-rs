#!/usr/bin/env python3
"""Verify A10M3 authority, schemas, finite bounds, and executable vectors."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: top level must be object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    authority = load(HERE / "authority-manifest-v1.json")
    for item in authority["authorities"]:
        path = REPO / item["path"]
        assert path.is_file(), path
        assert sha256(path) == item["sha256"], path
    assert authority["candidate_fit_count"] == 0
    assert authority["candidate_output_count"] == 0
    assert authority["confirmation_target_access"] is False

    model = load(HERE / "model-training-generation-v1.json")
    selector = load(HERE / "selector-benchmark-v1.json")
    calibration = load(HERE / "candidate-blind-calibration-v1.json")
    schemas = [
        load(REPO / "docs/specifications/a10-model-v1.schema.json"),
        load(REPO / "docs/specifications/a10-fit-checkpoint-v1.schema.json"),
        load(REPO / "docs/specifications/a10-generated-stream-v1.schema.json"),
        load(REPO / "docs/specifications/a10-selector-evidence-v1.schema.json"),
    ]
    assert all(schema.get("additionalProperties") is False for schema in schemas)

    canonical = model["canonical_configuration"]
    assert canonical["configuration_id"] == "lemhi-a10-py311-l40-v1"
    assert canonical["semantic_sha256"] == (
        "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179"
    )
    assert canonical["legacy_automatic_fallback"] is False

    screen = model["screen"]
    assert screen["maximum_configurations"] == len(screen["configurations"]) == 12
    assert len({value["id"] for value in screen["configurations"]}) == 12
    assert {value["pooling"] for value in screen["configurations"]} == {
        "N0_complete", "N1_partial"
    }
    assert screen["maximum_full_promotions_per_pooling_class"] == 2
    assert screen["maximum_finalists_per_pooling_class"] == 1
    assert len(screen["finalist_training_seeds"]) == 3
    generation = model["generation"]
    assert generation["horizons_years"] == [30, 100]
    assert len(generation["burn_ids"]) == 3
    assert generation["members_per_burn"] == 20
    losses = model["training"]["loss_terms"]
    assert losses[0]["id"] == "proper_mixed_output_nll"
    assert losses[0]["weight"] == 1.0
    assert sum(value["weight"] for value in losses[1:]) <= model["training"]["auxiliary_loss_weight_ceiling"]

    resources = model["resources"]
    components = [
        resources["m4_qualification_gpu_hours"],
        resources["m5_screen_gpu_hours"],
        resources["m5_finalist_development_gpu_hours"],
        resources["conditional_confirmation_gpu_hours"],
        resources["contingency_gpu_hours"],
    ]
    assert all(isinstance(value, int) and value > 0 for value in components)
    assert sum(components) == resources["total_a10_l40_gpu_hours"] == 560
    for job_name in ("single_job", "finalist_job"):
        job = resources[job_name]
        assert job["partition"] == "gpu-icrews"
        assert job["gres"] == "gpu:l40:1"
        assert all(job[key] > 0 for key in ("cpus", "memory_mb", "wall_minutes"))

    applicability = selector["applicability"]
    assert applicability["material_improvement_delta_b0"] > 0
    assert applicability["material_improvement_delta_b1"] > 0
    assert applicability["horizons_years"] == [30, 100]
    assert 0 < applicability["minimum_regimes"] <= 6
    benchmark = selector["benchmark"]
    assert benchmark["normative_host"].startswith("lemhi_gpu_icrews")
    assert benchmark["controller"] == "rmm_macos_arm64_apple_m1_16gb_not_timed"
    assert benchmark["warm_ratio_pass_below"] == 5.0
    assert benchmark["warm_ratio_warn_at_or_above"] == 5.0
    assert benchmark["warm_ratio_fail_at_or_above"] == 10.0
    assert benchmark["alternating_timed_samples"] == 9
    assert len(selector["representative_workload"]) == 6
    assert len({row["regime"] for row in selector["representative_workload"]}) == 6
    assert calibration["candidate_fit_count_at_freeze"] == 0
    assert calibration["candidate_output_count_at_freeze"] == 0
    assert calibration["confirmation_target_access"] is False

    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "research.a10.test_m3_contract", "-v"],
        cwd=REPO,
        check=False,
    )
    assert completed.returncode == 0
    print("A10M3 verification: PASS")
    print("authorities=8 schemas=4 vectors=15 gpu_hour_ceiling=560")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
