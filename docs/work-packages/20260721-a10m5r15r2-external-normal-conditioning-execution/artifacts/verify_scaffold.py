#!/usr/bin/env python3
"""Fail closed on the A10M5R15R2 execution scaffold."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
R1 = PACKAGE.parent / "20260721-a10m5r15r1-prism-eligible-cohort"
PARENT = PACKAGE.parent / "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


contract = json.loads((PACKAGE / "artifacts/execution-contract.json").read_text())
arms = contract["arms"]
if contract["package_id"] != PACKAGE.name or contract["protected_roles_opened"] != []:
    raise RuntimeError("execution package/protected-role identity drift")
if [
    (row["arm"], row["candidate"], row["configuration_id"], row["parameter_count"], row["uses_normals"], row["uses_p2"], row["wave"])
    for row in arms
] != [
    ("E0", "centered_location_ou_smooth_climatology", "centered_location_ou_smooth_climatology-k2", 278747, False, True, 0),
    ("E1", "normal_conditioned_smooth_climatology", "normal_conditioned_smooth_climatology-k2", 279467, True, True, 0),
    ("E2C", "descriptor_anchored_residual", "descriptor_anchored_residual-v1", 2040, False, False, 1),
    ("E2", "normal_anchored_residual", "normal_anchored_residual-v1", 2760, True, False, 1),
]:
    raise RuntimeError("four-arm identity drift")
resource = contract["resource"]
if resource != {
    "control_l40_minutes": 30,
    "portfolio_l40_count": 2,
    "portfolio_minutes": 240,
    "recovery_l40_minutes": 5,
    "total_l40_minute_equivalent": 515,
} or 30 + 2 * 240 + 5 != 515:
    raise RuntimeError("resource arithmetic drift")
parent_assets = Path(os.environ["A10M5R15R2_PARENT_ASSETS"])
if digest(parent_assets / "asset-manifest.json") != contract["parent_asset_manifest_sha256"]:
    raise RuntimeError("local R14R2R2 parent asset identity drift")

corpus_paths = {
    "build_receipt_sha256": R1 / "artifacts/cohort-build-receipt.json",
    "normalized_manifest_sha256": R1 / "artifacts/normalized-manifest-v1.json",
    "normalization_statistics_sha256": R1 / "artifacts/normalization-statistics-v1.json",
    "selection_sha256": R1 / "artifacts/cohort-selection.json",
    "transfer_manifest_sha256": R1 / "artifacts/offline-transfer-manifest-v1.json",
}
if any(digest(path) != contract["corpus"][name] for name, path in corpus_paths.items()):
    raise RuntimeError("A10M5R15R1 corpus pin drift")
conditioning_paths = {
    "archive_sha256": R1 / "artifacts/normal-conditioning/normal-conditioning.f32le",
    "index_sha256": R1 / "artifacts/normal-conditioning/normal-conditioning-index.json",
    "normalizer_sha256": R1 / "artifacts/normal-conditioning/normalizer.f64le",
    "receipt_sha256": R1 / "artifacts/normal-conditioning/normal-conditioning-receipt.json",
}
if any(digest(path) != contract["conditioning"][name] for name, path in conditioning_paths.items()):
    raise RuntimeError("A10M5R15R1 conditioning pin drift")
pin = json.loads((PACKAGE / "artifacts/corpus-layout-pin.json").read_text())
receipt = json.loads((PACKAGE / "artifacts/corpus-archive-receipt.json").read_text())
if (
    pin["package_id"] != PACKAGE.name
    or pin["archive"] != {key: receipt[key] for key in ("bytes", "sha256")}
    or pin["layout"]["accepted_object_count"] != 98
    or pin["layout"]["sole_top_level_prefix"] != "corpus"
):
    raise RuntimeError("successor corpus layout pin drift")
if contract["replay"] != {
    "attribution_bootstrap_seed": 410542,
    "calibration_replicates": 1000,
    "calibration_sequence_seeds": [410542, 410543],
    "materiality_floor": 0.000001,
    "nearest_rank_q90_zero_based_index": 899,
    "replay_count": 2,
    "selection": "per-treatment",
}:
    raise RuntimeError("rev-2 replay contract drift")

role_map = json.loads((PACKAGE / "artifacts/portfolio-role-map.json").read_text())
if (
    role_map["waves"] != [[0, 1], [2, 3]]
    or role_map["expected_allocated_devices"] != 2
    or [(row["role"], row["candidate"], row["wave"], row["allocation_token_index"]) for row in role_map["processes"]]
    != [
        (row["role"], row["candidate"], row["wave"], token)
        for row, token in zip(arms, (0, 1, 0, 1))
    ]
):
    raise RuntimeError("two-wave role map drift")

core = (PACKAGE / "artifacts/jobs/continuous_core.py").read_text(encoding="utf-8")
for token in (
    "EXPECTED_COUNTS",
    "normal_only_basis",
    "descriptor_basis",
    "nn.init.zeros_(self.climatology_heads.weight)",
    "self.location_baseline.weight[:, list(DESCRIPTOR_COLUMNS)].copy_",
    "torch.count_nonzero(e2.location_baseline.weight[:, normal_columns])",
    "portfolio.forward_control = lambda control, features, station, hidden_size: None",
    "descriptor-only control accepted conditioned tensors",
    "if uses_normals:",
):
    if token not in core:
        raise RuntimeError(f"continuous-core invariant absent: {token}")
for path in (PACKAGE / "artifacts/jobs").glob("*.py"):
    subprocess.run(("python3", "-m", "py_compile", str(path)), check=True)
for path in (
    PACKAGE / "artifacts/calibrate_attribution.py",
    PACKAGE / "artifacts/rev2_selector.py",
    PACKAGE / "artifacts/run_runtime_benchmarks.py",
    PACKAGE / "artifacts/run_temporal_replay.py",
    PACKAGE / "artifacts/verify_corpus_layout.py",
):
    subprocess.run(("python3", "-m", "py_compile", str(path)), check=True)
texts = {
    name: (PACKAGE / "artifacts" / name).read_text(encoding="utf-8")
    for name in (
        "calibrate_attribution.py", "run_runtime_benchmarks.py", "run_temporal_replay.py"
    )
}
for token in ("410542", "410543", "899", "candidate_output_accessed"):
    if token not in texts["calibrate_attribution.py"]:
        raise RuntimeError(f"calibration invariant absent: {token}")
for token in ("PAIRINGS", "selector_replays_byte_identical", "runtime_receipt"):
    if token not in texts["run_temporal_replay.py"]:
        raise RuntimeError(f"replay invariant absent: {token}")
for token in ("timed_sample_count", "single_core", "warn_below\": 30.0"):
    if token not in texts["run_runtime_benchmarks.py"]:
        raise RuntimeError(f"runtime invariant absent: {token}")
builder = (PACKAGE / "artifacts/jobs/build_control_records.py").read_text(encoding="utf-8")
if (
    "inherited.PACKAGE = PACKAGE" not in builder
    or "inherited.ROLES = ROLES" not in builder
    or "control-export.pt" not in builder
):
    raise RuntimeError("successor authority/portable export override absent")
wrapper = (PACKAGE / "artifacts/jobs/continuous_candidate_experiment.py").read_text(encoding="utf-8")
if "if uses_normals:\n    continuous.load_conditioning" not in wrapper:
    raise RuntimeError("descriptor-only process still loads conditioning")
if "180 normals-only input columns (720 weights)" not in (PACKAGE / "package.md").read_text(encoding="utf-8"):
    raise RuntimeError("normal-only parameter explanation drift")
materializer_path = PACKAGE / "artifacts/jobs/materialize_admission.py"
spec = __import__("importlib.util").util.spec_from_file_location(
    "r15r2_materializer_fixture", materializer_path
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load R2 admission fixture")
materializer = __import__("importlib.util").util.module_from_spec(spec)
spec.loader.exec_module(materializer)
expected_top_roles = {"control-materialization", "external-normal-conditioning-portfolio"}
if (
    materializer.delegated.ROLES != expected_top_roles
    or materializer.checker.ROLES != expected_top_roles
    or materializer.delegated.fetch_and_verify is not materializer.fetch_and_verify
):
    raise RuntimeError("R2 materialized-admission role/freshness wiring drift")
builder_spec = __import__("importlib.util").util.spec_from_file_location(
    "r15r2_builder_fixture", PACKAGE / "artifacts/jobs/build_control_records.py"
)
if builder_spec is None or builder_spec.loader is None:
    raise RuntimeError("cannot load R2 authority fixture")
builder_module = __import__("importlib.util").util.module_from_spec(builder_spec)
builder_spec.loader.exec_module(builder_module)
expected_child_roles = {
    (row["role"], row["candidate"], row["capacity"]) for row in arms
}
if set(builder_module.inherited.ROLES) != expected_child_roles:
    raise RuntimeError("R2 authority role matrix wiring drift")
selector_spec = __import__("importlib.util").util.spec_from_file_location(
    "r15r2_selector_fixture", PACKAGE / "artifacts/rev2_selector.py"
)
if selector_spec is None or selector_spec.loader is None:
    raise RuntimeError("cannot load four-arm selector fixture")
selector_module = __import__("importlib.util").util.module_from_spec(selector_spec)
selector_spec.loader.exec_module(selector_module)
transformed = selector_module.four_arm_source(
    (parent_assets / "temporal_select.py").read_text(encoding="utf-8")
)
if "left, right = configurations" in transformed or "pairwise_probabilities" not in transformed:
    raise RuntimeError("four-arm selector diagnostic transform drift")
prepare = (PACKAGE / "artifacts/jobs/prepare_assets.py").read_text(encoding="utf-8")
for token in (
    "candidate-blind attribution calibration is not frozen",
    'post-collection-replay-entry.json',
    '(options.output / "run_temporal_replay.py").unlink()',
):
    if token not in prepare:
        raise RuntimeError(f"calibration/replay preparation gate absent: {token}")
if not (PACKAGE / "plan.md").is_file():
    raise RuntimeError("bounded execution plan absent")
if "Status: `SCAFFOLDED`" not in (PACKAGE / "package.md").read_text(encoding="utf-8"):
    raise RuntimeError("execution package state drift")
if PACKAGE.name not in (REPO / "docs/work-packages/README.md").read_text(encoding="utf-8"):
    raise RuntimeError("execution package missing from catalog")

print("A10M5R15R2-SCAFFOLD-VERIFIED")
