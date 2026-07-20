#!/usr/bin/env python3
"""Pin the R14 factorial, resources, selector inheritance, and firewalls."""

from __future__ import annotations

import json
from pathlib import Path

package = Path(__file__).resolve().parents[1]
read = lambda name: json.loads((package / "artifacts" / name).read_text(encoding="utf-8"))
science = read("science-contract.json")
portfolio = read("portfolio-contract.json")
temporal = read("temporal-contract.json")
capacity = read("job-local-capacity-contract.json")
plan = read("execution-plan-template.json")
coverage = read("objective-selector-coverage.json")

factorial = [
    (row["smooth_uncentered_climatology"], row["centered_scale_ou"])
    for row in science["candidates"]
]
if factorial != [(False, False), (True, False), (False, True), (True, True)]:
    raise RuntimeError("2x2 factorial identity drift")
process = science["continuous_process"]
if (
    process["medium_state_dimension"], process["slow_state_dimension"],
    process["calendar_boundary_resets"], process["scale_head_indices"],
) != (8, 4, False, [2, 4, 6]):
    raise RuntimeError("continuous OU/state-head freeze drift")
window = science["training_window"]
if (window["axis_rows"], window["observed_rows"], window["eligible_origins_per_point"]) != (5844, 5840, 13):
    raise RuntimeError("calendar-window freeze drift")
if science["smooth_climatology"]["month_id_input"] or science["smooth_climatology"]["member_centered"]:
    raise RuntimeError("smooth uncentered continuous climatology drift")
if science["solar_opened"] or science["daily_proper_nll_weight"] or science["paired_daily_pattern_weight"]:
    raise RuntimeError("science firewall/zero-weight diagnostic drift")
if coverage["counts"]["total"] != 188 or not science["objective"]["same_components_for_training_and_checkpoint"]:
    raise RuntimeError("188-metric objective/checkpoint alignment drift")
if (
    [row["parameter_count"] for row in science["candidates"]]
    != [278667, 278747, 279819, 279899]
    or science["smooth_climatology"]["parameter_count"] != 80
    or science["smooth_climatology"]["bias"] is not False
    or science["smooth_climatology"]["basis_width"] != 20
    or science["smooth_climatology"]["output_activation"] != "identity"
    or "sin(2theta)" not in science["smooth_climatology"]["basis"]
):
    raise RuntimeError("factorial parameter-count/outer-product basis drift")
if science["candidate_parameter_ceiling"] != 340000 or max(
    row["parameter_count"] for row in science["candidates"]
) >= science["candidate_parameter_ceiling"]:
    raise RuntimeError("K2 parameter ceiling drift")
if "absolute" not in science["objective"]["reduction"] or "1mm" not in science["objective"]["wet_semantics"]:
    raise RuntimeError("absolute loss or realized-wet semantics drift")
if set(portfolio["objective"]["climate_blocks"]) != {
    row["metric_key"] for row in coverage["metrics"]
} or any(value != 1.0 for value in portfolio["objective"]["climate_blocks"].values()):
    raise RuntimeError("checkpoint weighted-score registry differs from 188-metric objective")
if len(portfolio["roles"]) != 4 or len(temporal["roles"]) != 4:
    raise RuntimeError("candidate role count drift")
resources = temporal["resources"]
if (resources["control_minutes"], resources["candidate_minutes_each"], resources["recovery_minutes"], resources["gpu_minute_ceiling"], resources["maximum_concurrent_candidates"]) != (30, 240, 5, 995, 4):
    raise RuntimeError("resource matrix drift")
if capacity["admission"]["maximum_live_candidate_jobs"] != 4 or plan["candidate_concurrency"] != 4:
    raise RuntimeError("concurrency/admission matrix drift")
if len(plan["submission_waves"]) != 2 or len(plan["submission_waves"][1]) != 4:
    raise RuntimeError("candidate submission wave drift")
if temporal["protected_roles_opened"] != [] or temporal["solar"]["opened"]:
    raise RuntimeError("protected/solar role firewall drift")
print("A10M5R14-CONTRACT-TEST-PASS")
