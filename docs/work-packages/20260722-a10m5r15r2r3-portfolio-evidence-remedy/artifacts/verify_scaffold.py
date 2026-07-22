#!/usr/bin/env python3
"""Fail closed on the A10M5R15R2 execution scaffold."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
accounting_path = PACKAGE / "artifacts/campaign-accounting.json"
accounting = json.loads(accounting_path.read_text(encoding="utf-8"))
actual = sum(row.get("actual_l40_minutes", -1) for row in accounting.get("components", []))
if not (
    accounting.get("valid") is True
    and accounting.get("package_id") == PACKAGE.name
    and actual == accounting.get("realized_l40_minutes") == 60
    and accounting.get("outstanding_study_ceiling_l40_minutes") == 515
    and accounting.get("bounded_maximum_l40_minutes") == actual + 515 == 575
    and accounting.get("authorized_outer_ceiling_l40_minutes") == 597
    and len(accounting.get("released_recovery_reserves", [])) == 3
):
    raise RuntimeError("campaign accounting identity or arithmetic drift")
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
corpus_verifier_spec = importlib.util.spec_from_file_location(
    "r2r2_verify_corpus_layout",
    PACKAGE / "artifacts/verify_corpus_layout.py",
)
if corpus_verifier_spec is None or corpus_verifier_spec.loader is None:
    raise RuntimeError("cannot load successor corpus verifier")
corpus_verifier = importlib.util.module_from_spec(corpus_verifier_spec)
corpus_verifier_spec.loader.exec_module(corpus_verifier)
if corpus_verifier.load_pin() != pin:
    raise RuntimeError("successor corpus verifier pin self-identity drift")
if contract["replay"] != {
    "attribution_bootstrap_seed": 410542,
    "calibration_receipt_sha256": "d54013c376f19a3d969f312a9e660dd5879e142bf64c3a16b622d21b30c2d9a2",
    "calibration_replicates": 1000,
    "calibration_sequence_seeds": [410542, 410543],
    "materiality_floor": 0.000001,
    "nearest_rank_q90_zero_based_index": 899,
    "replay_count": 2,
    "selection": "per-treatment",
}:
    raise RuntimeError("rev-2 replay contract drift")

calibration_path = PACKAGE / "artifacts/attribution-calibration.json"
calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
semantic_calibration = dict(calibration)
record_sha256 = semantic_calibration.pop("record_sha256", None)
semantic_bytes = json.dumps(
    semantic_calibration, separators=(",", ":"), sort_keys=True
).encode("utf-8")
calibration_commit = calibration.get("source_commit", "")
ancestor = subprocess.run(
    ("git", "merge-base", "--is-ancestor", calibration_commit, "HEAD"),
    cwd=REPO,
    check=False,
).returncode == 0
if not (
    digest(calibration_path) == contract["replay"]["calibration_receipt_sha256"]
    and record_sha256 == hashlib.sha256(semantic_bytes).hexdigest()
    and ancestor
    and calibration.get("package_id")
    == "20260721-a10m5r15r2-external-normal-conditioning-execution"
    and calibration.get("calibration_configuration")
    == "centered_location_ou_smooth_climatology-k2"
    and calibration.get("asset_manifest_sha256")
    == contract["parent_asset_manifest_sha256"]
    and calibration.get("calibration_source_commit")
    == contract["parent_asset_source_commit"]
    and calibration.get("calibration_stream_sha256")
    == "2bb8379f639712dc864308510bd2a8c10ac9c39ea3cae609abdc2a2bf51384ff"
    and calibration.get("candidate_output_accessed") is False
    and calibration.get("protected_roles_opened") == []
    and calibration.get("sequence_seeds") == [410542, 410543]
    and calibration.get("replicates") == 1000
    and calibration.get("nearest_rank_zero_based_index") == 899
    and calibration.get("margin", 0) > 0
    and calibration.get("valid") is True
    and calibration.get("gates")
    == {
        "candidate_blind": True,
        "replicate_count": True,
        "sequence_seeds_exact": True,
        "strictly_positive_margin": True,
    }
):
    raise RuntimeError("candidate-blind attribution calibration drift")

successor_path = PACKAGE / "artifacts/successor-reconstruction-contract.json"
successor = json.loads(successor_path.read_text(encoding="utf-8"))
control_package = PACKAGE.parent / "20260722-a10m5r15r2r1-successor-control-identity-calibration"
control_identity_path = control_package / "artifacts/successor-control-identity.json"
control_identity = json.loads(control_identity_path.read_text(encoding="utf-8"))
calibrated = successor.get("successor_control_calibration", {})
expected = []
for row in successor.get("models", []):
    item = dict(row)
    item.pop("non_gating_accepted_export_sha256", None)
    expected.append(item)
if not (
    successor.get("contract_id") == "a10m5r15r2r2-successor-semantic-reconstruction-v1"
    and len(expected) == 6
    and len({row["row_id"] for row in expected}) == 6
    and control_identity.get("all_static_identities_exact") is True
    and control_identity.get("candidate_output_accessed") is False
    and control_identity.get("protected_roles_opened") == []
    and [row.get("actual") for row in control_identity.get("models", [])] == expected
    and digest(control_identity_path) == calibrated.get("identity_artifact_sha256")
    and calibrated.get("collection_record_sha256")
    == "c9521e4422e629d5faf0079370fdd59f097c7f4b2b101138605e1a0360c362af"
    and calibrated.get("terminal_record_sha256")
    == "847a891e4c38c7c9e668091bcbb60445dfda52e7f7c02456951ae6ab91f20981"
):
    raise RuntimeError("successor control reconstruction contract drift")

# Exercise the real asset transformation against the authenticated parent
# contracts and prove the staged producer consumes the six successor pins.
prepare_path = PACKAGE / "artifacts/jobs/prepare_assets.py"
sys.path.insert(0, str(prepare_path.parent))
import campaign_accounting as campaign_accounting_validator

campaign_accounting_validator.validate()
if "campaign accounting validator differs from published source" not in prepare_path.with_name(
    "campaign_accounting.py"
).read_text(encoding="utf-8"):
    raise RuntimeError("campaign accounting validator publication gate absent")
prepare_spec = importlib.util.spec_from_file_location("r2r2_prepare_assets", prepare_path)
if prepare_spec is None or prepare_spec.loader is None:
    raise RuntimeError("cannot load R2R2 asset preparer")
prepare_module = importlib.util.module_from_spec(prepare_spec)
prepare_spec.loader.exec_module(prepare_module)
with tempfile.TemporaryDirectory() as temporary:
    fixture_root = Path(temporary)
    for name in (
        "portfolio-contract.json",
        "temporal-contract.json",
        "job-local-capacity-contract.json",
    ):
        shutil.copy2(parent_assets / name, fixture_root / name)
    prepare_module.transform_contracts(fixture_root, contract)
    staged_portfolio = json.loads(
        (fixture_root / "portfolio-contract.json").read_text(encoding="utf-8")
    )
    if staged_portfolio.get("controls", {}).get("models") != expected:
        raise RuntimeError("staged control producer does not consume successor pins")

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
    "PortableCandidateExport",
    "portable_stationary_ou_states",
    "if uses_normals:",
):
    if token not in core:
        raise RuntimeError(f"continuous-core invariant absent: {token}")
builder = (PACKAGE / "artifacts/jobs/build_control_records.py").read_text(encoding="utf-8")
for token in (
    "def rebind_evidence_roles(paths: list[str]) -> list[str]:",
    'path.replace(f"/{old_role}/", f"/{new_role}/")',
    'f"admissions/{old_role}.json", f"admissions/{new_role}.json"',
    'value["evidence_allowlist"] = rebind_evidence_roles(value["evidence_allowlist"])',
):
    if token not in builder:
        raise RuntimeError(f"portfolio evidence-role remedy absent: {token}")
builder_spec = importlib.util.spec_from_file_location(
    "r2r3_build_control_records", PACKAGE / "artifacts/jobs/build_control_records.py"
)
if builder_spec is None or builder_spec.loader is None:
    raise RuntimeError("cannot load R2R3 authority builder")
builder_module = importlib.util.module_from_spec(builder_spec)
sys.modules[builder_spec.name] = builder_module
builder_spec.loader.exec_module(builder_module)
role_suffixes = (
    "calendar-preflight.json",
    "candidate-summary.json",
    "control-identity.json",
    "streams.json",
    "streams.npz",
    "seeds/147031.json",
    "seeds/271828.json",
    "seeds/314159.json",
    "seed-work/147031/checkpoint.pt",
    "seed-work/271828/checkpoint.pt",
    "seed-work/314159/checkpoint.pt",
    "training.json",
    "candidate.stderr",
    "process.json",
    "evidence.json",
)
inherited_role_paths = [
    path
    for old_role in builder_module.OLD_ROLES
    for path in (
        f"admissions/{old_role}.json",
        *(f"results/{old_role}/{suffix}" for suffix in role_suffixes),
    )
]
expected_role_paths = [
    path
    for new_role, _, _ in builder_module.ROLES
    for path in (
        f"admissions/{new_role}.json",
        *(f"results/{new_role}/{suffix}" for suffix in role_suffixes),
    )
]
rebound_role_paths = builder_module.rebind_evidence_roles(inherited_role_paths)
if not (
    rebound_role_paths == expected_role_paths
    and len(rebound_role_paths) == len(inherited_role_paths) == 64
    and not any(
        old_role in path
        for old_role in builder_module.OLD_ROLES
        for path in rebound_role_paths
    )
):
    raise RuntimeError("portfolio evidence-role behavioral fixture failed")
for path in (PACKAGE / "artifacts/jobs").glob("*.py"):
    subprocess.run(("python3", "-m", "py_compile", str(path)), check=True)
for path in (
    PACKAGE / "artifacts/rev2_selector.py",
    PACKAGE / "artifacts/run_runtime_benchmarks.py",
    PACKAGE / "artifacts/run_temporal_replay.py",
    PACKAGE / "artifacts/verify_corpus_layout.py",
):
    subprocess.run(("python3", "-m", "py_compile", str(path)), check=True)
if 'with_name("corpus-layout-pin.json")' not in (
    PACKAGE / "artifacts/verify_corpus_layout.py"
).read_text(encoding="utf-8"):
    raise RuntimeError("corpus verifier is not relocatable with staged pin")
texts = {
    name: (PACKAGE / "artifacts" / name).read_text(encoding="utf-8")
    for name in ("run_runtime_benchmarks.py", "run_temporal_replay.py")
}
for token in (
    "PAIRINGS",
    "selector_replays_byte_identical",
    "runtime_receipt",
    "verify_replay_asset_bundle",
    'ATTRIBUTION_PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"',
    'calibration_identity["sha256"] == ATTRIBUTION_RECEIPT_SHA256',
    "staged asset manifest differs from authenticated plan",
    "replay-consumed asset identity drift",
    "verify_runtime_semantics",
    "runtime Cartesian roster drift",
    "timed candidate artifact identity drift",
    "runtime environment provenance drift",
    "expected_retained, expected_discarded = runtime_discard_contaminated_pairs",
    'runtime.get("gates") != computed_gates',
    "runtime safeguard gate recomputation drift",
    '"engineering_eligible"',
    '"faithful_output_deterministic"',
    "successor calendar preflight/corpus binding drift",
):
    if token not in texts["run_temporal_replay.py"]:
        raise RuntimeError(f"replay invariant absent: {token}")
for token in (
    "discard_contaminated_pairs",
    "raw_timed_sample_count",
    "timed_sample_count",
    "candidate_exports",
    "artifact_identities",
    "torch.set_num_interop_threads(1)",
    "CUDA_VISIBLE_DEVICES",
    "host_environment",
    "warn_below\": 30.0",
    '"daily_field_count": 8',
    '"clean_export_prefix_exact"',
    '"clean_export_cold_start"',
    '"clean_export_peak_rss"',
    '"candidate_complete"',
    '"faithful_complete"',
    '"deterministic_output"',
):
    if token not in texts["run_runtime_benchmarks.py"]:
        raise RuntimeError(f"runtime invariant absent: {token}")
builder = (PACKAGE / "artifacts/jobs/build_control_records.py").read_text(encoding="utf-8")
if (
    "inherited.PACKAGE = PACKAGE" not in builder
    or "inherited.ROLES = ROLES" not in builder
    or "control-export.pt" not in builder
    or "candidate-export-{years}.pt" not in builder
    or "runtime-benchmark.json" not in builder
):
    raise RuntimeError("successor authority/portable export override absent")
wrapper = (PACKAGE / "artifacts/jobs/continuous_candidate_experiment.py").read_text(encoding="utf-8")
if "if uses_normals:\n    continuous.load_conditioning" not in wrapper:
    raise RuntimeError("descriptor-only process still loads conditioning")
if 'value["configuration_id"] = arm["configuration_id"]' not in wrapper:
    raise RuntimeError("per-seed replacement configuration identity override absent")
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
coverage = json.loads((parent_assets / "objective-selector-coverage.json").read_text())
metric_keys = tuple(row["metric_key"] for row in coverage["metrics"])
dispersion_keys = selector_module.dispersion_metric_keys(metric_keys)
if len(dispersion_keys) != 39 or not all(
    name.endswith("_standard_deviation") for name in dispersion_keys
):
    raise RuntimeError("interannual-dispersion diagnostic registry drift")
if (
    selector_module.failure_terminal(selector_module.InvalidEvidenceError("fixture"))
    != "FAIL-A10M5R15-INVALID-EVIDENCE"
    or selector_module.failure_terminal(
        selector_module.EngineeringIncompleteError("fixture")
    )
    != "HOLD-A10M5R15-ENGINEERING-INCOMPLETE"
    or selector_module.failure_terminal(FileNotFoundError("fixture"))
    != "HOLD-A10M5R15-ENGINEERING-INCOMPLETE"
):
    raise RuntimeError("failure-terminal precedence fixture drift")
prepare = (PACKAGE / "artifacts/jobs/prepare_assets.py").read_text(encoding="utf-8")
for token in (
    "candidate-blind attribution calibration is not frozen",
    "validate_successor_control(options.source_commit)",
    "validate_campaign_accounting(options.source_commit)",
    '"reconstruction-contract.json": SUCCESSOR_RECONSTRUCTION',
    '"recover-job-local-v2.sh": REPO',
    '"campaign-accounting.json": CAMPAIGN_ACCOUNTING',
    'post-collection-replay-entry.json',
    '(options.output / "run_temporal_replay.py").unlink()',
    "install_runtime_execution",
    "runtime-parameters.tar",
    "cargo-vendor.tar.gz",
    "runtime-walltime-preflight.json",
    '"$benchmark_remaining" -ge 1800',
    '"maximum_expanded_bytes": 19327352832',
    '"minimum_free_bytes_before_mutation": 21474836480',
    '"minimum_free_inodes_before_mutation": 262144',
    '.replace("16000", "262144")',
    'rm -rf -- "$benchmark_root/rust-1.92.0-x86_64-unknown-linux-gnu"',
    'rm -rf -- "$benchmark_root/source/target"',
    "rebuild_calendar_preflight(options.corpus_archive, options.output)",
    'value["admission"]["waves"] = [[PORTFOLIO_ROLE]]',
    '"none": "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT"',
):
    if token not in prepare:
        raise RuntimeError(f"calibration/replay preparation gate absent: {token}")
if "inherited.prospective_calendar_preflight = prospective_calendar_preflight" not in builder:
    raise RuntimeError("successor calendar preflight authority override absent")
if builder.count("inherited.write(options.output, value)") != 2:
    raise RuntimeError("successor authority/plan record writer override absent")
if (
    'json.dumps(value).replace(\n            "continuous-distribution-head-factorial-portfolio", PORTFOLIO_ROLE'
    not in builder
    or "parent.PORTFOLIO_ROLE = PORTFOLIO_ROLE" in builder
):
    raise RuntimeError("successor semantic-plan portfolio role rebinding drift")
if not (PACKAGE / "plan.md").is_file():
    raise RuntimeError("bounded execution plan absent")
if not any(
    status in (PACKAGE / "package.md").read_text(encoding="utf-8")
    for status in ("Status: `SCAFFOLDED`", "Status: `EXECUTION-READY`")
):
    raise RuntimeError("execution package state drift")
if PACKAGE.name not in (REPO / "docs/work-packages/README.md").read_text(encoding="utf-8"):
    raise RuntimeError("execution package missing from catalog")

print("A10M5R15R2-EXECUTION-READY-VERIFIED")
