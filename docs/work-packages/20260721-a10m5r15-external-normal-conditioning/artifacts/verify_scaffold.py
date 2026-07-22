#!/usr/bin/env python3
"""Fail closed on every material A10M5R15 scaffold contract."""

from __future__ import annotations

import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
PACKAGE_ID = "20260721-a10m5r15-external-normal-conditioning"
PREDECESSOR = ROOT / "docs/work-packages/20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


science = read(PACKAGE / "artifacts/science-contract.json")
data = read(PACKAGE / "artifacts/data-preflight-contract.json")
resources = read(PACKAGE / "artifacts/resource-contract.json")
pin = read(PACKAGE / "artifacts/predecessor-pin.json")
for contract in (science, data, resources):
    if contract["package_id"] != PACKAGE_ID:
        raise RuntimeError("package identity drift")

arms = science["arms"]
expected_arms = [
    ("E0", "centered_location_ou_smooth_climatology-k2", "adapter", False, 340000, 278747, True),
    ("E1", "normal_conditioned_smooth_climatology-k2", "adapter", True, 340000, 279467, True),
    ("E2C", "descriptor_anchored_residual-v1", "replacement", False, 330000, 2040, False),
    ("E2", "normal_anchored_residual-v1", "replacement", True, 330000, 2760, False),
]
actual_arms = [
    (
        row["arm"], row["configuration_id"], row["matched_pair"],
        row["normals_conditioned"], row["parameter_ceiling"],
        row["parameter_count"], row["uses_p2_backbone"],
    )
    for row in arms
]
if actual_arms != expected_arms:
    raise RuntimeError("arm identity/capacity/count drift")
if science["candidate_seeds"] != [147031, 271828, 314159]:
    raise RuntimeError("candidate seed drift")
if science["candidate_member_count"] != 8 or science["objective_component_count"] != 188:
    raise RuntimeError("member/objective count drift")
if science["calendar_boundary_resets"] or science["location_head_indices"] != [0, 1, 3, 5]:
    raise RuntimeError("continuous-process/head drift")
if science["normal_field_count"] != 36 or science["normal_layer_order"] != [
    "ppt_jan_to_dec", "tmax_jan_to_dec", "tmin_jan_to_dec"
]:
    raise RuntimeError("normal field/layer drift")
if science["protected_roles_opened"] != []:
    raise RuntimeError("protected role opened")

replacement = science["replacement_architecture"]
if replacement != {
    "common_initialization": "same_seed_default_pytorch_linear_initialization; copy shared descriptor columns; zero initialize E2 normal-only columns",
    "descriptor_basis": "outer_product(5_term_day_of_year_harmonic,[1,lat,lon,elev])",
    "descriptor_basis_width": 20,
    "e2_location_basis": "outer_product(5_term_day_of_year_harmonic,[1,lat,lon,elev,36_normalized_normals])",
    "e2_location_basis_width": 200,
    "e2c_baseline": "bias_free_linear_20_to_15",
    "e2c_baseline_parameter_count": 300,
    "e2_baseline": "bias_free_linear_20_to_11_nonlocation_plus_bias_free_linear_200_to_4_location",
    "e2_baseline_parameter_count": 1020,
    "medium_state_dimension": 8,
    "medium_time_scale_days": [14.0, 180.0],
    "ou_adapter_parameter_count": 1740,
    "ou_discretization": "byte_inherited_r14_exact_stationary_continuous_time",
    "residual_centering": "subtract exact eight_member mean at every site_day_head cell",
    "residual_head_indices": [0, 1, 3, 5],
    "slow_state_dimension": 4,
    "slow_time_scale_days": [180.0, 1460.0],
}:
    raise RuntimeError("replacement architecture drift")
if replacement["ou_adapter_parameter_count"] + replacement["e2c_baseline_parameter_count"] != arms[2]["parameter_count"]:
    raise RuntimeError("E2C parameter arithmetic drift")
if replacement["ou_adapter_parameter_count"] + replacement["e2_baseline_parameter_count"] != arms[3]["parameter_count"]:
    raise RuntimeError("E2 parameter arithmetic drift")
r14_science = read(ROOT / "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/science-contract.json")
r14_b = next(row for row in r14_science["candidates"] if row["arm"] == "B")
inherited_ou_count = r14_b["parameter_count"] - 276927 - r14_science["smooth_climatology"]["parameter_count"]
if inherited_ou_count != replacement["ou_adapter_parameter_count"]:
    raise RuntimeError("R14 OU adapter parameter identity drift")
if arms[1]["parameter_count"] - arms[0]["parameter_count"] != 5 * 36 * 4:
    raise RuntimeError("E1 normal-column parameter delta drift")

training = science["training"]
if training != {
    "batches_per_epoch": 6,
    "checkpoint_points_per_regime": 4,
    "checkpoint_scalar": "unweighted_mean_of_same_188_absolute_scaled_components",
    "daily_proper_nll_weight": 0.0,
    "early_stop_patience": 16,
    "fit_validation_gradient": False,
    "gradient_clip_norm": 1.0,
    "learning_rate": 0.001,
    "maximum_epochs": 96,
    "minimum_epochs": 24,
    "optimizer": "AdamW",
    "records_per_batch": 6,
    "regularization": {"latent_stability_weight": 0.005, "residual_size_and_centering_weight": 0.01},
    "tie_tolerance": 1e-06,
    "training_members": 8,
    "weight_decay": 0.01,
    "wet_semantics": "exact_hard_forward_relaxed_soft_backward_temperature_0.5",
}:
    raise RuntimeError("replacement training/checkpoint drift")

attribution = science["attribution"]
if attribution["comparisons"] != [["E1", "E0"], ["E2", "E2C"]]:
    raise RuntimeError("matched attribution pair drift")
if attribution["calibration"] != {
    "bootstrap_operator": "byte_inherited_r14_temporal_bootstrap",
    "bootstrap_replicates_per_sequence": 1000,
    "calibration_source": "accepted_r14_e0_streams_only",
    "floor": 1e-06,
    "margin_equation": "max(floor, nearest_rank_q90(abs(A_i-B_i)/max(A_i,B_i)))",
    "nearest_rank_index_zero_based": 899,
    "receipt_required_before_candidate_output": True,
    "sequence_seeds": [410542, 410543],
}:
    raise RuntimeError("attribution calibration drift")
if (
    attribution["gate_equation"] != "1-treatment_u90/control_u90"
    or attribution["gate_boundary"] != "relative_improvement_greater_than_or_equal_to_margin"
    or attribution["paired_bootstrap_seed"] != 410542
    or not attribution["shared_strictly_positive_margin"]
):
    raise RuntimeError("attribution gate drift")

if science["temporal"] != {
    "bootstrap_replicates": 1000,
    "horizons_years": [30, 100],
    "maximum_regime_ratio": 1.5,
    "median_regime_ratio_upper_90_percent": 1.25,
    "nested_prefix": True,
    "site_count": 6,
}:
    raise RuntimeError("temporal protocol drift")
if science["runtime"] != {"fail_at_or_above": 30.0, "pass_below": 5.0, "warn_at_or_above": 5.0}:
    raise RuntimeError("ADR-0006 runtime drift")
if science["diagnostics"] != {
    "replacement_dispersion": "report E2/E2C combined monthly_and_annual_interannual_dispersion ratio; non-gating",
    "replacement_runtime": "report E2/E1 warm runtime ratio; non-gating beyond ADR-0006",
}:
    raise RuntimeError("non-gating diagnostic semantics drift")
expected_terminals = [
    "FAIL-A10M5R15-INVALID-EVIDENCE",
    "HOLD-A10M5R15-ENGINEERING-INCOMPLETE",
    "HOLD-A10M5R15-RUNTIME-INELIGIBLE",
    "HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED",
    "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT",
    "A10M5R15-TEMPORAL-READY",
]
if science["selection"] != {
    "matched_controls": {"E1": "E0", "E2": "E2C"},
    "full_treatment_predicate_after_engineering": "runtime_valid(T)&&temporal(T)&&attribution(T,C)",
    "portfolio_evidence_may_not_mix_treatments": True,
    "runtime_valid_predicate": "runtime(T)!=FAIL&&runtime(C)!=FAIL",
    "terminal_conditions_after_evidence_and_engineering": {
        "A10M5R15-TEMPORAL-READY": "any_T(full(T))",
        "HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED": "any_T(runtime_valid(T)&&temporal(T))&&!any_T(full(T))",
        "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT": "any_T(runtime_valid(T))&&!any_T(runtime_valid(T)&&temporal(T))",
        "HOLD-A10M5R15-RUNTIME-INELIGIBLE": "!any_T(runtime_valid(T))",
    },
    "terminal_precedence": expected_terminals,
}:
    raise RuntimeError("per-treatment selection/terminal precedence drift")


def classify(states: tuple[tuple[bool, bool, bool], tuple[bool, bool, bool]]) -> str:
    """Evaluate post-evidence/engineering branches for (runtime, temporal, attribution)."""
    full = [runtime and temporal and attribution for runtime, temporal, attribution in states]
    if not any(runtime for runtime, _, _ in states):
        return "HOLD-A10M5R15-RUNTIME-INELIGIBLE"
    if any(runtime and temporal for runtime, temporal, _ in states) and not any(full):
        return "HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED"
    if not any(runtime and temporal for runtime, temporal, _ in states):
        return "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT"
    if any(full):
        return "A10M5R15-TEMPORAL-READY"
    raise RuntimeError("non-exhaustive post-engineering terminal branches")


for bits in range(64):
    state = tuple(
        tuple(bool(bits & (1 << (3 * arm + field))) for field in range(3))
        for arm in range(2)
    )
    terminal = classify(state)  # type: ignore[arg-type]
    full_exists = any(runtime and temporal and attribution for runtime, temporal, attribution in state)
    if (terminal == "A10M5R15-TEMPORAL-READY") != full_exists:
        raise RuntimeError("cross-treatment evidence can reach READY")

if data["calendar"] != {
    "adjacent_annual_pairs_per_window": 15,
    "axis_rows_per_window": 5844,
    "eligible_origins_per_window": 13,
    "leap_day_policy": "february_29_observed_december_31_structural_null",
    "minimum_eligible_days_per_month": 28,
    "normalized_axis": "proleptic_gregorian_daily",
    "observed_core_rows_per_window": 5840,
    "source_calendar": "daymet_official_365_v1",
    "transform": "daymet_official_365_v1_to_proleptic_gregorian_daily",
    "window_end": "exclusive",
    "window_years": 16,
}:
    raise RuntimeError("calendar/missingness drift")
if data["corpus"] != {
    "candidate_fit": 1200,
    "fit_validation": 240,
    "required_mask": ["source_observed", "finite_precipitation", "finite_tmax", "finite_tmin"],
    "total_objects": 1440,
}:
    raise RuntimeError("corpus role/count drift")
normals = data["normals"]
required_normal_fields = {
    "candidate_fit_normalizer_count": 1200,
    "canonical_point_order": "ascending_utf8_point_id_bytes",
    "field_count": 36,
    "fit_validation_may_update_normalizer": False,
    "input_dtype": "source_ieee754_f32_promoted_exactly_to_f64",
    "input_units": ["ppt_monthly_mm", "tmax_degrees_c", "tmin_degrees_c"],
    "layer_order": ["ppt_jan_to_dec", "tmax_jan_to_dec", "tmin_jan_to_dec"],
    "model_conversion": "(f64_input-f64_mean)/f64_population_scale_then_single_round_to_ieee754_f32_nearest_ties_even",
    "normalizer_role": "candidate_fit_only",
    "normalizer_statistics": "per_field_welford_f64_population_mean_and_population_standard_deviation_ddof_0",
    "required_corpus_query_count": 1440,
    "required_temporal_query_count": 6,
    "zero_or_nonfinite_scale": "fail_before_resource_reservation",
}
if any(normals[key] != value for key, value in required_normal_fields.items()):
    raise RuntimeError("normals preprocessing drift")
if normals["canonical_receipt"] != {
    "binary_payload": "72_little_endian_ieee754_f64_values_means_then_population_scales",
    "manifest_fields": ["schema_version", "bundle_id", "candidate_fit_count", "point_order_sha256", "payload_bytes", "payload_sha256"],
    "schema_version": "a10m5r15-normalizer-receipt-1",
}:
    raise RuntimeError("normalizer receipt drift")

distribution = read(ROOT / "crates/cligen/src/prism/distribution.json")
bundle = read(ROOT / "docs/work-packages/20260718-a10m5r4r1-stochastic-prism-comparator/artifacts/prism-bundle-manifest.json")
prism = pin["prism"]
if (
    normals["bundle_id"] != distribution["bundle_id"]
    or normals["runtime_archive_sha256"] != distribution["runtime_archive"]["sha256"]
    or normals["source_archive_sha256"] != distribution["source_archive"]["sha256"]
    or prism["runtime_archive_sha256"] != bundle["runtime"]["sha256"]
    or prism["source_archive_sha256"] != bundle["source"]["sha256"]
    or prism["grid_manifest_sha256"] != bundle["runtime"]["grid_manifest_sha256"]
    or prism["normals_sha256"] != bundle["runtime"]["normals_sha256"]
    or prism["validity_mask_sha256"] != bundle["runtime"]["validity_mask_sha256"]
    or prism["source_manifest_sha256"] != bundle["source"]["source_manifest_sha256"]
    or prism["build_receipt_sha256"] != bundle["build_receipt_sha256"]
    or prism["attribution_sha256"] != bundle["attribution_sha256"]
):
    raise RuntimeError("PRISM identity drift")

portfolio = resources["candidate_portfolio"]
if (
    portfolio != {
        "allocated_l40_count": 2,
        "maximum_minutes": 240,
        "one_scientific_attempt_per_arm": True,
        "waves": [["E0", "E1"], ["E2C", "E2"]],
    }
    or resources["control"] != {"allocated_l40_count": 1, "maximum_minutes": 30}
    or resources["recovery"] != {"maximum_l40_minutes": 5, "scope": "cleanup-only"}
):
    raise RuntimeError("resource topology drift")
computed_minutes = 1 * 30 + 2 * 240 + 5
if resources["maximum_l40_minute_equivalents"] != computed_minutes:
    raise RuntimeError("resource ceiling arithmetic drift")

result = read(PREDECESSOR / "artifacts/temporal-result-r3.json")
replay = read(PREDECESSOR / "artifacts/replay-identity-r3.json")
accepted = pin["accepted_predecessor"]
if (
    accepted["package_id"] != replay["package_id"]
    or accepted["source_commit"] != replay["source_commit"]
    or accepted["replay_asset_manifest_sha256"] != replay["asset_manifest_sha256"]
    or accepted["terminal"] != replay["terminal"]
    or result["terminal"] != accepted["terminal"]
    or not replay["byte_identical_passes"]
):
    raise RuntimeError("accepted predecessor identity drift")
incumbent = result["candidate_decisions"][pin["prior_incumbent"]["configuration_id"]]
if (
    incumbent["bootstrap_median_regime_ratio_upper_90_percent"] != pin["prior_incumbent"]["median_regime_ratio_upper_90_percent"]
    or incumbent["maximum_regime_ratio"] != pin["prior_incumbent"]["maximum_regime_ratio"]
):
    raise RuntimeError("prior incumbent result drift")

spec = (ROOT / "docs/specifications/SPEC-A10-EXTERNAL-NORMAL-CONDITIONING.md").read_text(encoding="utf-8")
package_text = (PACKAGE / "package.md").read_text(encoding="utf-8")
for token in (
    "**RATIFIED** (rev 1", "### E2C", "Exact totals are", "### Attribution calibration",
    "E1 is compared only to E0", "E2 only to E2C", "340,000", "330,000",
):
    if token not in spec:
        raise RuntimeError(f"ratified specification text drift: {token}")
exit_text = package_text.split("## Exit criteria", 1)[1]
for terminal in expected_terminals:
    if terminal not in exit_text:
        raise RuntimeError(f"terminal precedence drift: {terminal}")
positions = [exit_text.index(terminal) for terminal in expected_terminals]
if positions != sorted(positions):
    raise RuntimeError("terminal precedence order drift")
for token in (
    "runtime_valid(T)", "runtime(T) != FAIL", "runtime(C) != FAIL",
    "any_T(full(T))", "!any_T(full(T))", "Evidence from different treatments",
):
    if token not in package_text:
        raise RuntimeError(f"per-treatment predicate prose drift: {token}")

print("A10M5R15-SCAFFOLD-VERIFY-PASS")
