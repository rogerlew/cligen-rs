#!/usr/bin/env python3
"""Fail-closed verification for the A5c no-promotion adjudication."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
DECISION_PATH = ARTIFACTS / "a5c-decision-v1.json"
LOCK_PATH = ARTIFACTS / "evidence-lock-v1.json"
RESULTS_PATH = ROOT / (
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/"
    "artifacts/results.md"
)
REPORT_MANIFEST_PATH = (
    ROOT / "docs/reports/interannual-candidate-exp-001-report.manifest.json"
)

EXPECTED_CANDIDATES = {
    "rank_one_monthly_sd": (
        "Rank-one monthly SD",
        "a5b_rank_one_monthly_sd_v1",
        "interannual_rank_one_monthly_sd_v1",
    ),
    "full_monthly_covariance": (
        "Full monthly covariance",
        "a5b_full_monthly_covariance_v1",
        "interannual_full_monthly_covariance_v1",
    ),
    "fourier_eof": (
        "Fourier/EOF",
        "a5b_fourier_eof_v1",
        "interannual_fourier_eof_v1",
    ),
    "vector_ar": (
        "Vector AR",
        "a5b_vector_ar_v1",
        "interannual_fourier_eof_var1_v1",
    ),
    "gaussian_hmm": (
        "Gaussian HMM",
        "a5b_gaussian_hmm_v1",
        "interannual_fourier_eof_hmm2_v1",
    ),
    "spectral_random_phase": (
        "Spectral random phase",
        "a5b_spectral_random_phase_v1",
        "interannual_fourier_eof_spectral_v1",
    ),
    "precip_counterfactual": (
        "Precipitation counterfactual",
        "a5b_fourier_eof_precip_counterfactual_v1",
        "interannual_fourier_eof_precip_counterfactual_v1",
    ),
}
PUBLIC_SURFACES = (
    "docs/specifications/SPEC-GENERATION-PROFILES.md",
    "docs/specifications/SPEC-RUNSPEC.md",
    "docs/specifications/runspec.schema.json",
    "docs/specifications/SPEC-PROVENANCE.md",
    "docs/specifications/provenance-v1.schema.json",
    "crates/cligen/schemas/provenance-v1.schema.json",
    "docs/specifications/SPEC-STATION-DOCUMENT.md",
    "docs/specifications/station-document.schema.json",
    "docs/specifications/SPEC-CLI-PARQUET.md",
    "docs/specifications/cli-parquet-v1.fields.json",
)


class VerificationError(RuntimeError):
    """Raised when an A5c invariant is not satisfied."""


def reject_constant(value: str) -> None:
    raise VerificationError(f"non-finite JSON constant: {value}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_loads(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_constant,
    )


def strict_load(path: Path) -> Any:
    return strict_loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def validate_lock(lock: dict[str, Any]) -> None:
    require(lock.get("evidence_lock_version") == 1, "wrong evidence lock version")
    require(
        lock.get("decision_id") == "a5c-interannual-profile-adjudication-v1",
        "evidence lock decision id mismatch",
    )
    commit = lock.get("frozen_at_commit")
    require(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
        "invalid frozen commit",
    )
    entries = lock.get("entries")
    require(isinstance(entries, list) and len(entries) == 24, "expected 24 lock entries")
    paths: set[str] = set()
    roles: set[str] = set()
    for entry in entries:
        require(set(entry) == {"role", "path", "sha256"}, "invalid lock entry keys")
        role = entry["role"]
        relative = entry["path"]
        expected = entry["sha256"]
        require(isinstance(role, str) and role not in roles, f"duplicate lock role: {role}")
        require(
            isinstance(relative, str) and relative not in paths,
            f"duplicate or invalid lock path: {relative}",
        )
        require(
            isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
            f"invalid digest for {relative}",
        )
        path = ROOT / relative
        require(path.is_file(), f"missing locked evidence: {relative}")
        require(sha256(path) == expected, f"evidence hash mismatch: {relative}")
        roles.add(role)
        paths.add(relative)
    require(set(PUBLIC_SURFACES).issubset(paths), "public surfaces are not fully locked")


def parse_gate_table() -> dict[tuple[str, int], tuple[str, ...]]:
    by_label = {values[0]: key for key, values in EXPECTED_CANDIDATES.items()}
    rows: dict[tuple[str, int], tuple[str, ...]] = {}
    for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if len(cells) != 10 or cells[0] not in by_label or cells[1] not in {"30", "100"}:
            continue
        if not all(value in {"P", "F"} for value in cells[2:9]) or cells[9] != "No":
            continue
        key = (by_label[cells[0]], int(cells[1]))
        require(key not in rows, f"duplicate result row: {key}")
        require(not all(value == "P" for value in cells[2:8]), f"climate gates pass: {key}")
        require(cells[4:7] == ("F", "F", "F"), f"G3-G5 preservation claim changed: {key}")
        require(cells[8] == "P", f"G7 incomplete: {key}")
        rows[key] = cells[2:]
    expected = {(candidate, years) for candidate in EXPECTED_CANDIDATES for years in (30, 100)}
    require(set(rows) == expected, "gate table does not contain exactly 14 expected rows")
    return rows


def validate_report_manifest(manifest: dict[str, Any]) -> None:
    require(manifest.get("status") == "ACCEPTED", "report is not accepted")
    require(manifest.get("report_revision") == 2, "unexpected report revision")
    facts = manifest.get("study_facts", {})
    expected = {
        "stations": 17,
        "candidates": 7,
        "horizons_years": [30, 100],
        "candidate_horizon_rows": 14,
        "candidate_climates": 1904,
        "observed_bootstrap_replicates": 2000,
        "wepp_response_records": 2176,
        "wepp_execution_records": 2176,
        "eligible_candidate_horizon_rows": 0,
        "promoted_candidates": 0,
        "evidence_classification": "exploratory for model selection",
    }
    for key, value in expected.items():
        require(facts.get(key) == value, f"report study fact changed: {key}")


def validate_public_surfaces(decision: dict[str, Any]) -> None:
    runspec = strict_load(ROOT / "docs/specifications/runspec.schema.json")
    profile = runspec["$defs"]["generationProfile"]
    require(
        profile.get("enum") == ["faithful_5_32_3", "fast_batch_v0"],
        "public generation-profile enum changed",
    )
    require(profile.get("default") == "faithful_5_32_3", "public profile default changed")
    experimental_ids = {
        values[1] for values in EXPECTED_CANDIDATES.values()
    }
    for relative in PUBLIC_SURFACES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        leaked = sorted(profile_id for profile_id in experimental_ids if profile_id in text)
        require(not leaked, f"A5b profile id entered public surface {relative}: {leaked}")
    require(
        decision["public_default"]
        == {"generation_profile": "faithful_5_32_3", "qc_filter": "faithful"},
        "decision public defaults changed",
    )


def validate_decision(
    decision: dict[str, Any],
    lock: dict[str, Any],
    rows: dict[tuple[str, int], tuple[str, ...]],
) -> None:
    require(decision.get("a5c_decision_version") == 1, "wrong decision version")
    require(
        decision.get("decision_id") == lock.get("decision_id"),
        "decision id does not match lock",
    )
    require(decision.get("status") == "no_promotion", "decision is not no-promotion")
    evidence = decision.get("evidence", {})
    require(
        evidence.get("lock_path")
        == "docs/work-packages/20260714-a5c-interannual-profile-adjudication/artifacts/evidence-lock-v1.json",
        "decision lock path changed",
    )
    require(evidence.get("lock_sha256") == sha256(LOCK_PATH), "decision lock digest mismatch")
    require(
        evidence.get("classification") == "exploratory_model_selection",
        "evidence boundary classification changed",
    )
    candidates = decision.get("evaluated_candidates")
    require(isinstance(candidates, list) and len(candidates) == 7, "expected seven candidates")
    seen: set[str] = set()
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        require(candidate_id in EXPECTED_CANDIDATES, f"unknown candidate: {candidate_id}")
        require(candidate_id not in seen, f"duplicate candidate: {candidate_id}")
        _, profile_id, station_model_id = EXPECTED_CANDIDATES[candidate_id]
        require(candidate.get("generation_profile_id") == profile_id, f"profile mismatch: {candidate_id}")
        require(candidate.get("station_model_id") == station_model_id, f"model mismatch: {candidate_id}")
        horizons = candidate.get("horizons")
        require(isinstance(horizons, list) and len(horizons) == 2, f"bad horizons: {candidate_id}")
        require([row.get("years") for row in horizons] == [30, 100], f"horizon order changed: {candidate_id}")
        for horizon in horizons:
            years = horizon["years"]
            require((candidate_id, years) in rows, f"missing source gate row: {candidate_id}/{years}")
            require(horizon.get("passes_all_climate_gates") is False, f"climate pass asserted: {candidate_id}/{years}")
            require(horizon.get("eligible") is False, f"eligibility asserted: {candidate_id}/{years}")
        seen.add(candidate_id)
    require(seen == set(EXPECTED_CANDIDATES), "candidate set mismatch")
    require(decision.get("eligible_candidate_ids") == [], "eligible candidate list is not empty")
    require(decision.get("promoted_profile_ids") == [], "promoted profile list is not empty")
    changes = decision.get("public_surface_changes")
    require(isinstance(changes, dict) and len(changes) == 7, "public surface map changed")
    require(all(value is False for value in changes.values()), "a public surface change was asserted")
    require(
        isinstance(decision.get("renewal_condition"), str)
        and "prospectively registered study" in decision["renewal_condition"],
        "prospective renewal condition missing",
    )
    requirements = decision.get("prospective_successor_requirements")
    require(isinstance(requirements, list) and len(requirements) == 6, "successor requirements changed")
    validate_public_surfaces(decision)


def validate_closure_records() -> None:
    adr = (ROOT / "docs/decisions/0004-a5b-interannual-no-promotion.md").read_text(encoding="utf-8")
    require("Status: Accepted" in adr and "No A5b" in adr, "ADR-0004 is not accepted")
    roadmap = (ROOT / "docs/ROADMAP.md").read_text(encoding="utf-8")
    require("| 1 | **A5c" not in roadmap, "A5c remains in the active roadmap table")
    require("20260714-a5c-interannual-profile-adjudication" in roadmap, "roadmap lacks A5c closure")
    catalog = (ROOT / "docs/work-packages/README.md").read_text(encoding="utf-8")
    require(
        "[20260714-a5c-interannual-profile-adjudication]" in catalog
        and "EXECUTED-COMPLETE" in catalog,
        "work-package catalog lacks A5c closure",
    )
    decisions = (ROOT / "docs/decisions/README.md").read_text(encoding="utf-8")
    require("[0004](0004-a5b-interannual-no-promotion.md)" in decisions, "ADR registry lacks 0004")


def expect_failure(label: str, action: Callable[[], None]) -> None:
    try:
        action()
    except (VerificationError, KeyError, TypeError, ValueError):
        return
    raise VerificationError(f"mutation self-test unexpectedly passed: {label}")


def run_mutation_tests(
    decision: dict[str, Any],
    lock: dict[str, Any],
    rows: dict[tuple[str, int], tuple[str, ...]],
) -> None:
    expect_failure("duplicate-key", lambda: strict_loads('{"x": 1, "x": 2}'))
    expect_failure("non-finite", lambda: strict_loads('{"x": NaN}'))

    bad_lock = copy.deepcopy(lock)
    bad_lock["entries"][0]["sha256"] = "0" * 64
    expect_failure("evidence-hash", lambda: validate_lock(bad_lock))

    def mutate_and_check(path: tuple[str, ...], value: Any) -> None:
        mutated = copy.deepcopy(decision)
        target: Any = mutated
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        validate_decision(mutated, lock, rows)

    expect_failure(
        "candidate-eligibility",
        lambda: mutate_and_check(("evaluated_candidates",), [
            {
                **decision["evaluated_candidates"][0],
                "horizons": [
                    {"years": 30, "passes_all_climate_gates": True, "eligible": True},
                    decision["evaluated_candidates"][0]["horizons"][1],
                ],
            },
            *decision["evaluated_candidates"][1:],
        ]),
    )
    expect_failure("promotion", lambda: mutate_and_check(("promoted_profile_ids",), ["a5b_fourier_eof_v1"]))
    changed_surfaces = dict(decision["public_surface_changes"])
    changed_surfaces["runspec"] = True
    expect_failure("public-surface", lambda: mutate_and_check(("public_surface_changes",), changed_surfaces))
    expect_failure(
        "public-default",
        lambda: mutate_and_check(
            ("public_default",),
            {"generation_profile": "a5b_fourier_eof_v1", "qc_filter": "faithful"},
        ),
    )


def main() -> None:
    decision = strict_load(DECISION_PATH)
    lock = strict_load(LOCK_PATH)
    require_finite(decision)
    require_finite(lock)
    validate_lock(lock)
    rows = parse_gate_table()
    validate_report_manifest(strict_load(REPORT_MANIFEST_PATH))
    validate_decision(decision, lock, rows)
    validate_closure_records()
    run_mutation_tests(decision, lock, rows)
    print("A5c verification: PASS")
    print("locked evidence: 24 files")
    print("candidate/horizon rows: 14, eligible: 0")
    print("promoted profiles: 0; public surfaces changed: 0")
    print("mutation self-tests: 6/6 rejected (plus non-finite JSON)")


def require_finite(value: Any) -> None:
    if isinstance(value, float):
        require(math.isfinite(value), "non-finite numeric value")
    elif isinstance(value, dict):
        for nested in value.values():
            require_finite(nested)
    elif isinstance(value, list):
        for nested in value:
            require_finite(nested)


if __name__ == "__main__":
    main()
