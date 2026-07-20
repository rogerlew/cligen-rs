#!/usr/bin/env python3
"""Fail-closed prospective freeze verifier for A10M5R12."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
PREDECESSOR = REPO / "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/artifacts"
INHERITED_TEMPORAL = PREDECESSOR / "evaluation-contract.json"
INHERITED_PREFLIGHT = (
    REPO
    / "docs/work-packages/20260719-a10m5r11r1-admission-role-matrix-remedy"
    / "artifacts/toolkit-recovered/evidence/results/control-materialization/calendar-preflight.json"
)
PORTFOLIO_PARENT = (
    REPO
    / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio"
    / "artifacts/portfolio-contract.json"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    predecessor = json.loads((PREDECESSOR / "temporal-result.json").read_text())
    if digest(PREDECESSOR / "temporal-result.json") != "656f23ce7b8ec64a96aa7eff98a162f12c57c8d51497fd4285d5eb7594d68a41":
        raise SystemExit("predecessor result identity drift")
    if predecessor["terminal"] != "HOLD-A10M5R11-NO-TEMPORALLY-ELIGIBLE-CANDIDATE":
        raise SystemExit("predecessor terminal drift")
    science = json.loads((PACKAGE / "artifacts/portfolio-contract.json").read_text())
    parent_science = json.loads(PORTFOLIO_PARENT.read_text())
    temporal = json.loads((PACKAGE / "artifacts/temporal-contract.json").read_text())
    inherited = json.loads(INHERITED_TEMPORAL.read_text())
    for field in ("generation", "observation", "metrics", "scoring", "solar"):
        if temporal[field] != inherited[field]:
            raise SystemExit(f"inherited temporal field drift: {field}")
    roles = science["roles"]
    if len(roles) != 2 or {row["capacity"] for row in roles} != {"K2"}:
        raise SystemExit("candidate matrix drift")
    for definition in science["architectures"].values():
        if definition["state_reset_boundaries"] or definition["observed_weather_inputs"]:
            raise SystemExit("continuous-state or input firewall drift")
        if definition["state_clock"] != "continuous_time_exact_ou_discretized_daily":
            raise SystemExit("continuous state clock drift")
    if temporal["metrics"]["paired_daily_pattern_weight"] != 0.0:
        raise SystemExit("paired daily objective drift")
    for field in (
        "schema_version",
        "controls",
        "calendar",
        "data_roles",
        "stochastic",
        "eligibility",
        "pareto",
    ):
        if science[field] != parent_science[field]:
            raise SystemExit(f"inherited portfolio field drift: {field}")
    evidence_layout = json.loads(json.dumps(science["evidence_layout"]))
    for name in ("streams.json", "streams.npz"):
        evidence_layout["candidate_files"].remove(name)
    evidence_layout.pop("candidate_checkpoint_files_required", None)
    if evidence_layout != parent_science["evidence_layout"]:
        raise SystemExit("evidence layout drift outside temporal retention")
    objective = dict(science["objective"])
    objective["daily_proper_nll_weight"] = parent_science["objective"][
        "daily_proper_nll_weight"
    ]
    if objective != parent_science["objective"]:
        raise SystemExit("portfolio objective drift outside daily-NLL disposition")
    training = dict(science["training"])
    training.pop("continuous_learning_rate", None)
    if training != parent_science["training"]:
        raise SystemExit("inherited training field drift")
    checkpoint = json.loads(json.dumps(science["checkpoint"]))
    checkpoint["selection_scalar"]["daily_proper_nll_weight"] = parent_science[
        "checkpoint"
    ]["selection_scalar"]["daily_proper_nll_weight"]
    if checkpoint != parent_science["checkpoint"]:
        raise SystemExit("checkpoint drift outside daily-NLL disposition")
    capacity_shapes = json.loads(json.dumps(science["capacity_shapes"]))
    for name in (
        "continuous_medium_state_dim",
        "continuous_slow_state_dim",
        "continuous_context_width",
    ):
        capacity_shapes["K2"].pop(name, None)
    if capacity_shapes != parent_science["capacity_shapes"]:
        raise SystemExit("capacity drift outside continuous extension")
    if (
        science["objective"]["daily_proper_nll_weight"] != 0.0
        or science["checkpoint"]["selection_scalar"]["daily_proper_nll_weight"]
        != 0.0
    ):
        raise SystemExit("conditional-member daily NLL weight drift")
    if temporal["protected_roles_opened"] or temporal["solar"]["opened"]:
        raise SystemExit("protected role drift")
    if science["execution"]["total_gpu_minute_ceiling"] != 395:
        raise SystemExit("resource ceiling drift")
    sites = PACKAGE / "artifacts/sites.json"
    if digest(sites) != "f8415f74143f37e07b9936b4c3ecdc0a08908fc32b285e523c63ccfe12ad71dd":
        raise SystemExit("site roster identity drift")
    control_expectation = PACKAGE / "artifacts/calendar-control-expectation.json"
    if (
        digest(INHERITED_PREFLIGHT)
        != "bc2ec73330ea678ff8248766ff696b96b2d8de4fa94ed9b7266c10592500911a"
        or control_expectation.read_bytes() != INHERITED_PREFLIGHT.read_bytes()
    ):
        raise SystemExit("control calendar expectation identity drift")
    preflight = PACKAGE / "artifacts/calendar-preflight.json"
    if digest(preflight) != "58a927b6facc255fb8feb803b05c23be3cb727790fb4dd7ac77f627cffa48c75":
        raise SystemExit("revision-2 calendar preflight identity drift")
    calendar = json.loads(preflight.read_text())
    if not (
        calendar["valid"]
        and calendar["profile_id"] == science["calendar"]["profile_id"]
        and calendar["source_bounds"]
        == {"start_inclusive": "1980-01-01", "end_inclusive": "2009-12-31"}
        and calendar["window"]["end_semantics"] == "exclusive"
        and calendar["month_year_eligibility"]["eligible"] is True
        and calendar["month_year_eligibility"]["required_minimum_observed_rows"] == 28
        and calendar["fixture"]["spans_observed_february_29"] is True
        and calendar["fixture"]["spans_absent_leap_december_31"] is True
        and calendar["fixture"]["spans_window_end_exclusive"]
        == ["1987-12-31", "1988-01-01"]
    ):
        raise SystemExit("prospective calendar preflight failed")
    source = (PACKAGE / "artifacts/jobs/continuous_core.py").read_text()
    if "del regimes, months, years" not in source:
        raise SystemExit("calendar-bin state-input firewall drift")
    if "rho = torch.exp(-1.0 / time_scales)" not in source:
        raise SystemExit("exact OU transition drift")
    print("A10M5R12-FREEZE-READY")


if __name__ == "__main__":
    main()
