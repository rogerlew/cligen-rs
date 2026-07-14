#!/usr/bin/env python3
"""Fail-closed verifier for the executed A5d0 hold package."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
LOCK_PATH = ARTIFACTS / "evidence-lock-inputs-v1.json"
FIXTURE_PATH = ARTIFACTS / "feasibility-fixtures-v1.json"
FIXTURE_SCRIPT = ARTIFACTS / "run-feasibility-fixtures.py"
DECISION_PATH = ARTIFACTS / "a5d0-decision-v1.json"
INVENTORY_PATH = ARTIFACTS / "data-role-inventory-v1.json"
CLOSURE_PATH = ARTIFACTS / "closure-evidence-v1.json"
PACKAGE_PATH = ARTIFACTS.parent / "package.md"


class VerificationError(RuntimeError):
    """An A5d0 closure invariant failed."""


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


def require_finite(value: Any) -> None:
    if isinstance(value, float):
        require(math.isfinite(value), "non-finite numeric value")
    elif isinstance(value, dict):
        for nested in value.values():
            require_finite(nested)
    elif isinstance(value, list):
        for nested in value:
            require_finite(nested)


def validate_lock(lock: dict[str, Any]) -> None:
    require(lock.get("evidence_lock_version") == 1, "wrong input lock version")
    require(
        lock.get("package_id") == "20260714-a5d0-successor-feasibility-calibration",
        "input lock package id mismatch",
    )
    commit = lock.get("source_commit")
    require(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
        "invalid source commit",
    )
    entries = lock.get("entries")
    require(isinstance(entries, list) and len(entries) == 19, "expected 19 input lock entries")
    paths: set[str] = set()
    roles: set[str] = set()
    for entry in entries:
        require(set(entry) == {"role", "path", "sha256"}, "invalid input lock keys")
        role = entry["role"]
        relative = entry["path"]
        expected = entry["sha256"]
        require(isinstance(role, str) and role not in roles, f"duplicate input role: {role}")
        require(isinstance(relative, str) and relative not in paths, f"duplicate path: {relative}")
        require(
            isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
            f"invalid hash: {relative}",
        )
        path = ROOT / relative
        require(path.is_file(), f"missing locked input: {relative}")
        require(sha256(path) == expected, f"locked input hash mismatch: {relative}")
        roles.add(role)
        paths.add(relative)


def validate_closure_manifest(closure: dict[str, Any]) -> None:
    require(closure.get("closure_evidence_version") == 1, "wrong closure evidence version")
    require(
        closure.get("package_id") == "20260714-a5d0-successor-feasibility-calibration",
        "closure evidence package id mismatch",
    )
    require(
        closure.get("status") == "executed_hold_contract_incomplete",
        "closure evidence status mismatch",
    )
    entries = closure.get("entries")
    require(isinstance(entries, list) and len(entries) == 15, "expected 15 closure entries")
    paths: set[str] = set()
    for entry in entries:
        require(set(entry) == {"path", "sha256"}, "invalid closure entry keys")
        relative = entry["path"]
        expected = entry["sha256"]
        require(isinstance(relative, str) and relative not in paths, f"duplicate closure path: {relative}")
        require(
            isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
            f"invalid closure hash: {relative}",
        )
        path = ROOT / relative
        require(path.is_file(), f"missing closure artifact: {relative}")
        require(sha256(path) == expected, f"closure artifact hash mismatch: {relative}")
        paths.add(relative)


def validate_public_surfaces() -> None:
    a5c_lock = strict_load(
        ROOT
        / "docs/work-packages/20260714-a5c-interannual-profile-adjudication/artifacts/evidence-lock-v1.json"
    )
    protected = [
        entry
        for entry in a5c_lock["entries"]
        if entry["role"].startswith("public-") or entry["role"] == "embedded-provenance-schema"
    ]
    require(len(protected) == 10, "unexpected A5c public-surface lock count")
    for entry in protected:
        require(
            sha256(ROOT / entry["path"]) == entry["sha256"],
            f"accepted public surface changed: {entry['path']}",
        )
    runspec = strict_load(ROOT / "docs/specifications/runspec.schema.json")
    profile = runspec["$defs"]["generationProfile"]
    require(
        profile["enum"] == ["faithful_5_32_3", "fast_batch_v0"]
        and profile["default"] == "faithful_5_32_3",
        "accepted public profile enum/default changed",
    )
    for entry in protected:
        text = (ROOT / entry["path"]).read_text(encoding="utf-8")
        require("a5d_" not in text and "a5d0_" not in text, f"A5d id leaked: {entry['path']}")
    require(
        not (ROOT / "docs/specifications/SPEC-A5D-EVALUATION.md").exists(),
        "held package created a normative A5d evaluation spec",
    )


def reproduce_fixture() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(FIXTURE_SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    reproduced = strict_loads(completed.stdout)
    stored = strict_load(FIXTURE_PATH)
    require(reproduced == stored, "stored feasibility fixture is not reproducible")
    self_test = subprocess.run(
        [sys.executable, str(FIXTURE_SCRIPT), "--self-test"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    require(
        self_test.stdout.strip() == "A5d0 feasibility fixture self-test: PASS",
        "fixture self-test output changed",
    )
    return stored


def validate_fixture(fixture: dict[str, Any]) -> None:
    require(fixture.get("status") == "complete", "fixture is incomplete")
    variance = fixture["variance_reallocation_fixture"]
    baseline = variance["baseline"]
    candidate = variance["candidate"]
    require(abs(baseline["mean"] - candidate["mean"]) <= 1.0e-12, "fixture mean changed")
    require(
        abs(baseline["daily_second_moment"] - candidate["daily_second_moment"]) <= 1.0e-12,
        "fixture second moment changed",
    )
    require(
        abs(variance["between_year_variance_ratio"] - 1.4) <= 1.0e-12,
        "fixture variance ratio changed",
    )
    require(variance["physical_daily_values_modified"] == 0, "fixture mutates daily values")
    kernel = fixture["stationary_kernel_fixture"]
    require(kernel["row_sum_max_abs_error"] <= 1.0e-12, "kernel row sum failed")
    require(kernel["stationary_max_abs_error"] <= 1.0e-12, "kernel stationarity failed")
    require(kernel["same_block_repeat_probability"] > 0.67, "repeat blocker disappeared")
    require(
        abs(kernel["zero_frequency_power_ratio_vs_independent"] - 4.0) <= 1.0e-12,
        "zero-frequency power identity changed",
    )
    require(
        fixture["structural_counterexample"]["result"]
        == "preserving mean and daily second moment fixes between-year variance",
        "counterexample changed",
    )
    power = fixture["calibration_power"]
    require(power["minimum_independent_null_trials_if_zero_failures"] == 59, "null trial count changed")
    require(power["upper_bound_after_eight_trials"] > 0.31, "eight-trial upper bound changed")
    balanced = power["balanced_four_regime_sign_design"]
    require(
        balanced["stations"] == 28
        and balanced["required_improved"] == 19
        and balanced["null_one_sided_probability"] <= 0.05
        and balanced["power_if_true_improvement_probability_is_0_75"] >= 0.80,
        "balanced sign design changed",
    )
    require(fixture["conclusion"]["production_contract_freeze_ready"] is False, "fixture asserts readiness")


def validate_inventory(inventory: dict[str, Any]) -> None:
    require(inventory.get("status") == "complete", "data inventory incomplete")
    existing = inventory["existing_exposed_development"]
    daymet = sorted(path.stem.removesuffix(".csv") for path in (ROOT / "references/observed/a5a-v1/daymet").glob("*.csv.gz"))
    ghcn = sorted(path.stem.removesuffix(".csv") for path in (ROOT / "references/observed/a5a-v1/ghcn").glob("*.csv.gz"))
    require(existing["daymet_station_ids"] == daymet, "Daymet inventory mismatch")
    require(existing["ghcn_station_ids"] == ghcn, "GHCN inventory mismatch")
    require(existing["daymet_station_count"] == len(daymet) == 17, "Daymet count mismatch")
    require(existing["ghcn_station_count"] == len(ghcn) == 8, "GHCN count mismatch")
    confirmation = inventory["untouched_confirmation"]
    require(confirmation["station_count"] == 0, "confirmation stations were asserted")
    require(confirmation["raw_objects_present"] == 0, "confirmation raw objects were asserted")
    require(inventory["raw_value_rows_opened_during_a5d0"] is False, "raw access asserted")


def validate_decision(decision: dict[str, Any]) -> None:
    require(decision.get("a5d0_decision_version") == 1, "wrong decision version")
    require(decision.get("status") == "hold_contract_incomplete", "wrong terminal decision")
    require(decision["primary_blocker"]["code"] == "contract_incomplete", "wrong primary blocker")
    require(
        [item["code"] for item in decision["secondary_blockers"]]
        == ["evaluation_uncalibrated", "confirmation_corpus"],
        "secondary blockers changed",
    )
    require(decision["feasibility"]["candidate_contract_freeze_ready"] is False, "candidate marked ready")
    require(decision["exposure"]["status"] == "clean", "exposure status changed")
    require(decision["exposure"]["a5d_confirmation_candidate_outputs_accessed"] == 0, "candidate access asserted")
    require(decision["exposure"]["a5d_confirmation_target_values_accessed"] == 0, "target access asserted")
    require(decision["candidate_identifiers_frozen"] == [], "candidate identifier frozen")
    require(decision["confirmation_campaign_authorized"] is False, "confirmation was authorized")
    changes = decision["public_surface_changes"]
    require(len(changes) == 8 and all(value is False for value in changes.values()), "public change asserted")


def validate_documents() -> None:
    package = PACKAGE_PATH.read_text(encoding="utf-8")
    require("Status: `EXECUTED-HOLD-CONTRACT-INCOMPLETE`" in package, "package status mismatch")
    required = {
        "feasibility-analysis.md": "Status: `EXECUTED-HOLD-CONTRACT-INCOMPLETE`",
        "evaluation-revision-4-plan.md": "Status: `EXECUTED-HOLD-EVALUATION-UNCALIBRATED`",
        "validation-corpus-plan.md": "Status: `EXECUTED-HOLD-CONFIRMATION-CORPUS`",
        "candidate-contract-outline.md": "Status: `EXECUTED-HOLD-CONTRACT-INCOMPLETE`",
        "exposure-ledger.md": "Status: `CLEAN`",
        "go-hold-decision.md": "Status: `HOLD-CONTRACT-INCOMPLETE`",
    }
    for name, marker in required.items():
        text = (ARTIFACTS / name).read_text(encoding="utf-8")
        require(marker in text, f"artifact status mismatch: {name}")
    roadmap = (ROOT / "docs/ROADMAP.md").read_text(encoding="utf-8")
    require("**A5d0 held**" in roadmap, "roadmap does not record A5d0 hold")
    require("ready for operator dispatch" not in roadmap, "roadmap still marks A5d0 ready")
    catalog = (ROOT / "docs/work-packages/README.md").read_text(encoding="utf-8")
    require(
        "[20260714-a5d0-successor-feasibility-calibration]" in catalog
        and "EXECUTED-HOLD-CONTRACT-INCOMPLETE" in catalog,
        "work-package catalog status mismatch",
    )


def validate_no_candidate_outputs() -> None:
    forbidden_suffixes = (".cli", ".cli.parquet", ".quality.json")
    forbidden = [
        path
        for path in ARTIFACTS.rglob("*")
        if path.is_file() and path.name.endswith(forbidden_suffixes)
    ]
    require(not forbidden, f"candidate-like output in held package: {forbidden}")
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    changed_paths = [line[3:] for line in status if len(line) >= 4]
    require(not any(path.startswith("crates/") for path in changed_paths), "production source changed")


def expect_failure(label: str, action: Callable[[], None]) -> None:
    try:
        action()
    except (VerificationError, KeyError, TypeError, ValueError):
        return
    raise VerificationError(f"mutation self-test unexpectedly passed: {label}")


def run_mutation_tests(decision: dict[str, Any], lock: dict[str, Any]) -> None:
    expect_failure("duplicate-key", lambda: strict_loads('{"x": 1, "x": 2}'))
    expect_failure("non-finite", lambda: strict_loads('{"x": NaN}'))
    bad_lock = copy.deepcopy(lock)
    bad_lock["entries"][0]["sha256"] = "0" * 64
    expect_failure("input-hash", lambda: validate_lock(bad_lock))

    for label, mutate in (
        ("authorize-confirmation", lambda value: value.__setitem__("confirmation_campaign_authorized", True)),
        ("freeze-candidate-id", lambda value: value.__setitem__("candidate_identifiers_frozen", ["a5d_bad_v1"])),
        ("candidate-access", lambda value: value["exposure"].__setitem__("a5d_confirmation_candidate_outputs_accessed", 1)),
        ("public-change", lambda value: value["public_surface_changes"].__setitem__("runspec", True)),
    ):
        mutated = copy.deepcopy(decision)
        mutate(mutated)
        expect_failure(label, lambda mutated=mutated: validate_decision(mutated))


def main() -> None:
    lock = strict_load(LOCK_PATH)
    closure = strict_load(CLOSURE_PATH)
    decision = strict_load(DECISION_PATH)
    inventory = strict_load(INVENTORY_PATH)
    for value in (lock, closure, decision, inventory):
        require_finite(value)
    validate_lock(lock)
    validate_closure_manifest(closure)
    validate_public_surfaces()
    fixture = reproduce_fixture()
    require_finite(fixture)
    validate_fixture(fixture)
    validate_inventory(inventory)
    validate_decision(decision)
    validate_documents()
    validate_no_candidate_outputs()
    run_mutation_tests(decision, lock)
    print("A5d0 package verification: PASS")
    print("locked inputs: 19; public surfaces changed: 0")
    print("synthetic feasibility: reproducible; candidate contract ready: no")
    print("confirmation stations: 0; candidate/target exposures: 0/0")
    print("terminal status: EXECUTED-HOLD-CONTRACT-INCOMPLETE")
    print("mutation self-tests: 7/7 rejected")


if __name__ == "__main__":
    main()
