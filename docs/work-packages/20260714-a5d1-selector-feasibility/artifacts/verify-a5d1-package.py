#!/usr/bin/env python3
"""Fail-closed terminal verifier for the executed A5d1 work package."""

from __future__ import annotations

import copy
import collections
import gzip
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tarfile

import numpy as np
from jsonschema import Draft202012Validator, ValidationError
from scipy.optimize import linprog

from a5d1_common import (
    A5A_ARCHIVE,
    CONTRACT,
    DAYMET_DIR,
    FEATURE_MANIFEST,
    FEATURE_DIR,
    FREEZE,
    LIBRARY_MANIFEST,
    PACKAGE,
    ROOT,
    canonical_sha256,
    load_json,
    reject_duplicate_keys,
    reject_nonfinite,
    sha256,
)


SCHEMA = PACKAGE / "selector-feasibility-contract-v4.schema.json"
LOCK = PACKAGE / "evidence-lock-inputs-v6.json"
FIXTURE_RESULTS = PACKAGE / "synthetic-feasibility-fixture-results-v1.json"
PUBLISHED_MARGINAL = PACKAGE / "marginal-results-v1.json"
PUBLISHED_PATH = PACKAGE / "path-results-v1.json"
DETAILED_ARCHIVE = PACKAGE / "detailed-evidence-v1.tar.gz"
DETAILED_MANIFEST = PACKAGE / "detailed-evidence-manifest-v1.json"
PHYSICAL_AUDIT = PACKAGE / "physical-row-identity-audit-v1.json"
RESULTS = PACKAGE / "selector-feasibility-results-v1.json"
DECISION = PACKAGE / "a5d1-decision-v1.json"
REVIEW = PACKAGE / "review.md"
GATES = PACKAGE / "gate-results.md"
CLOSURE = PACKAGE / "closure-evidence-v1.json"
PACKAGE_MD = PACKAGE.parent / "package.md"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PACKAGE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOLVER = load_module("a5d1_verifier_solver", "solve-selector-feasibility.py")
PATH_TOOL = load_module("a5d1_verifier_path", "run-path-feasibility.py")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def decompressed_sha256(path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_file_record(record: dict, required: bool = True) -> None:
    path = ROOT / record["path"]
    if not path.exists() and not required:
        return
    require(path.is_file(), f"locked file missing: {path}")
    require(path.stat().st_size == record.get("bytes", path.stat().st_size), f"locked byte count changed: {path}")
    require(sha256(path) == record["sha256"], f"locked hash changed: {path}")


def verify_lock(lock: dict, libraries: dict) -> None:
    for group in ("authority_inputs", "tooling"):
        for record in lock[group]:
            verify_file_record(record)
    for name in ("contract", "contract_schema", "fixtures"):
        verify_file_record(lock[name])
    require(lock["contract"]["sha256"] == sha256(CONTRACT), "lock contract mismatch")
    require(lock["contract_schema"]["sha256"] == sha256(SCHEMA), "lock schema mismatch")
    require(lock["station_count"] == 17, "lock station count is not 17")
    station_config = load_json(
        ROOT
        / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
        / "artifacts/corpus/corpus-config-v1.json"
    )
    expected = {row["station_id"]: row for row in station_config["stations"]}
    with tarfile.open(A5A_ARCHIVE, "r:gz") as archive:
        for station in lock["stations"]:
            station_id = station["station_id"]
            require(station["par_sha256"] == expected[station_id]["par_sha256"], f"par lock/config mismatch: {station_id}")
            member = archive.extractfile(f"station-parameters/{station_id}.par")
            require(member is not None, f"par archive member missing: {station_id}")
            require(sha256_bytes(member.read()) == station["par_sha256"], f"par bytes changed: {station_id}")
            verify_file_record(station["daymet"])
            daymet = ROOT / station["daymet"]["path"]
            require(decompressed_sha256(daymet) == station["daymet"]["decompressed_sha256"], f"Daymet payload changed: {station_id}")
            verify_file_record(station["bundle"])
            bundle = load_json(ROOT / station["bundle"]["path"])
            fourier = next(item for item in bundle["extensions"] if item["candidate_id"] == "fourier_eof")
            require(fourier["fit_identity_sha256"] == station["fourier_eof"]["fit_identity_sha256"], f"Fourier fit identity changed: {station_id}")
            require(fourier["diagnostics"]["payload_sha256"] == station["fourier_eof"]["payload_sha256"], f"Fourier payload identity changed: {station_id}")
    binary_record = lock["generator_binary"]
    verify_file_record(binary_record, required=False)
    require(libraries["binary"]["sha256"] == binary_record["sha256"], "library binary differs from lock")
    require(libraries["binary"]["bytes"] == binary_record["bytes"], "library binary size differs from lock")
    exposure = lock["exposure"]
    require(exposure["confirmation_objects_accessed"] == 0, "confirmation object exposure")
    require(exposure["confirmation_target_values_accessed"] == 0, "confirmation target exposure")
    require(exposure["confirmation_wepp_responses_accessed"] == 0, "confirmation WEPP exposure")
    require(lock["public_surface_changes"] == lock["production_source_changes"] == 0, "public/production change recorded")


def archive_members(manifest: dict) -> dict[str, bytes]:
    require(manifest["archive"]["sha256"] == sha256(DETAILED_ARCHIVE), "detailed archive hash mismatch")
    require(manifest["archive"]["bytes"] == DETAILED_ARCHIVE.stat().st_size, "detailed archive size mismatch")
    result = {}
    with tarfile.open(DETAILED_ARCHIVE, "r:gz") as archive:
        names = archive.getnames()
        require(names == sorted(names) and len(names) == len(set(names)) == 340, "archive member ordering/count mismatch")
        for member in archive.getmembers():
            handle = archive.extractfile(member)
            require(handle is not None, f"cannot read archive member: {member.name}")
            result[member.name] = handle.read()
    records = {row["member"]: row for row in manifest["members"]}
    require(set(records) == set(result), "archive manifest/member set mismatch")
    for name, payload in result.items():
        require(records[name]["sha256"] == sha256_bytes(payload), f"archive member hash mismatch: {name}")
        require(records[name]["bytes"] == len(payload), f"archive member size mismatch: {name}")
    return result


def parse_member(members: dict[str, bytes], name: str) -> dict:
    return json.loads(
        members[name],
        parse_constant=reject_nonfinite,
        object_pairs_hook=reject_duplicate_keys,
    )


def close(actual: float, expected: float, tolerance: float = 2.0e-8) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def numerical_marginal_replay(
    marginal: dict, members: dict[str, bytes], contract: dict, freeze_sha256: str
) -> tuple[dict[tuple[str, int], bool], dict[tuple[str, int], list[float]]]:
    pass_index = {}
    weight_index = {}
    for row in marginal["records"]:
        station_id = row["station_id"]
        pool_size = row["pool_size"]
        name = "certificates/" + row["certificate"]["path"].rsplit("/", 1)[-1]
        certificate = parse_member(members, name)
        feature = load_json(FEATURE_DIR / f"{station_id}-year-features-v1.json")
        blocks = feature["blocks"][:pool_size]
        problem = SOLVER.build_problem(blocks, feature["targets"], contract)
        primary = linprog(
            problem["objective"],
            A_ub=problem["a_ub"],
            b_ub=problem["b_ub"],
            A_eq=problem["a_eq"],
            b_eq=problem["b_eq"],
            bounds=problem["bounds"],
            method="highs",
            options={"time_limit": contract["resource_ceilings"]["solver_seconds_per_station_pool"]},
        )
        tie = None
        if primary.success:
            tie_objective = np.zeros_like(problem["objective"])
            tie_objective[:pool_size] = np.arange(1, pool_size + 1, dtype=np.float64) / pool_size
            tie = linprog(
                tie_objective,
                A_ub=np.vstack((problem["a_ub"], np.asarray([problem["objective"]]))),
                b_ub=np.concatenate((problem["b_ub"], np.asarray([float(primary.fun) + 1.0e-9]))),
                A_eq=problem["a_eq"],
                b_eq=problem["b_eq"],
                bounds=problem["bounds"],
                method="highs",
                options={"time_limit": contract["resource_ceilings"]["solver_seconds_per_station_pool"]},
            )
            solution = tie.x if tie.success else primary.x
        else:
            solution = np.concatenate((np.full(pool_size, 1.0 / pool_size), np.zeros(6)))
        weights = solution[:pool_size]
        recorded_weights = np.asarray(certificate["weights"], dtype=np.float64)
        require(
            weights.shape == recorded_weights.shape
            and float(np.max(np.abs(weights - recorded_weights))) <= 2.0e-8,
            f"marginal solve replay differs: {station_id}/{pool_size}",
        )
        solver_success = bool(primary.success and tie is not None and tie.success)
        require(certificate["solver"]["success"] == bool(primary.success), f"primary status mismatch: {station_id}/{pool_size}")
        require(certificate["solver"]["tie_break"]["success"] == bool(tie and tie.success), f"tie status mismatch: {station_id}/{pool_size}")
        ub = problem["a_ub"] @ solution - problem["b_ub"]
        eq = problem["a_eq"] @ solution - problem["b_eq"]
        require(close(float(np.max(ub)), certificate["maximum_inequality_residual"]), f"inequality replay mismatch: {station_id}/{pool_size}")
        require(close(float(np.max(np.abs(eq))), certificate["maximum_equality_residual"]), f"equality replay mismatch: {station_id}/{pool_size}")
        centered = SOLVER.centered_values(blocks, weights)
        components = {
            key: abs(centered[key] - problem["centered_target_values"][key]) / problem["scales"][key]
            for key in SOLVER.ANNUAL_COMPONENTS
        }
        baseline_components = {
            key: abs(problem["centered_baseline_values"][key] - problem["centered_target_values"][key])
            / problem["scales"][key]
            for key in SOLVER.ANNUAL_COMPONENTS
        }
        actual = math.fsum(components.values())
        baseline = math.fsum(baseline_components.values())
        replay_pass = (
            solver_success
            and float(np.max(ub)) <= 2.0e-7
            and float(np.max(np.abs(eq))) <= 2.0e-9
            and float(np.min(weights)) >= -1.0e-10
            and float(np.max(weights)) <= contract["marginal_solver"]["max_weight"] + 1.0e-9
        )
        noninferiority = all(
            components[key] <= baseline_components[key] + 1.0e-7 + 2.0e-12
            for key in SOLVER.ANNUAL_COMPONENTS
        )
        strict = actual <= 0.95 * baseline + 1.0e-7
        passed = replay_pass and noninferiority and strict
        require(certificate["independent_replay_pass"] == replay_pass, f"certificate replay flag mismatch: {station_id}/{pool_size}")
        require(certificate["annual"]["noninferiority"] == noninferiority, f"marginal noninferiority mismatch: {station_id}/{pool_size}")
        require(certificate["annual"]["strict_improvement"] == strict, f"marginal strict flag mismatch: {station_id}/{pool_size}")
        require(certificate["marginal_pass"] == row["marginal_pass"] == passed, f"marginal pass mismatch: {station_id}/{pool_size}")
        require(close(row["actual_aggregate_distance"], actual), f"marginal actual summary mismatch: {station_id}/{pool_size}")
        require(close(row["baseline_aggregate_distance"], baseline), f"marginal baseline summary mismatch: {station_id}/{pool_size}")
        pass_index[(station_id, pool_size)] = passed
        weight_index[(station_id, pool_size)] = [float(value) for value in weights]
    return pass_index, weight_index


def numerical_path_replay(
    paths: dict,
    members: dict[str, bytes],
    contract: dict,
    marginal_pass: dict[tuple[str, int], bool],
    weights: dict[tuple[str, int], list[float]],
) -> None:
    cache = {}
    threshold = contract["marginal_solver"]["positive_weight_threshold"]
    cooldown = contract["path"]["cooldown_years"]
    max_reuse = contract["path"]["exact_block_max_reuse"]
    for row in paths["records"]:
        station_id = row["station_id"]
        pool_size = row["pool_size"]
        key = (station_id, pool_size)
        if key not in cache:
            feature = load_json(FEATURE_DIR / f"{station_id}-year-features-v1.json")
            blocks = feature["blocks"][:pool_size]
            cache[key] = (
                blocks,
                SOLVER.build_problem(blocks, feature["targets"], contract),
                PATH_TOOL.target_dependence(feature),
            )
        blocks, problem, target = cache[key]
        name = "paths/" + row["path_record"]["path"].rsplit("/", 1)[-1]
        path = parse_member(members, name)
        indices = path["source_year_indices_zero_based"]
        require(len(indices) == 100, f"path length mismatch: {row['cell_id']}")
        baseline_indices = list(range(100))
        finite = {
            str(horizon): SOLVER.finite_prefix_replay(problem, blocks, indices, horizon, contract)
            for horizon in (30, 100)
        }
        finite_pass = all(value["pass"] for value in finite.values())
        baseline_metrics = PATH_TOOL.path_metrics(blocks, baseline_indices)
        actual_metrics = PATH_TOOL.path_metrics(blocks, indices)
        aggregate, components, baseline_components, _ = PATH_TOOL.distances(
            actual_metrics, target, baseline_metrics
        )
        noninferiority = all(
            components[name] <= baseline_components[name] + 0.10 + 1.0e-9
            for name in components
        )
        strict = aggregate <= 0.95 * math.fsum(baseline_components.values()) + 1.0e-9
        boundary = PATH_TOOL.boundary_replay(blocks, indices, baseline_indices, contract)
        calendar_pass = all(
            blocks[index]["calendar_class"] == ("leap" if PATH_TOOL.is_leap(year) else "common")
            for year, index in enumerate(indices, 1)
        )
        reuse_pass = PATH_TOOL.valid_reuse(indices, cooldown, max_reuse)
        zero_count = sum(weights[key][index] <= threshold for index in indices)
        render_pass = bool(
            path["invariants"]["payload_identity_pass"]
            and path["invariants"]["common_prefix_pass"]
        )
        selector_pass = path["failure"] is None
        passed = bool(
            marginal_pass[key]
            and selector_pass
            and finite_pass
            and noninferiority
            and strict
            and calendar_pass
            and reuse_pass
            and zero_count == 0
            and boundary["pass"]
            and render_pass
        )
        criteria = (
            ("stationary_marginal_feasibility", marginal_pass[key]),
            ("bounded_positive_weight_selector", selector_pass),
            ("finite_prefix_marginal", finite_pass),
            ("dependence_noninferiority", noninferiority),
            ("dependence_strict_improvement", strict),
            ("boundary_vector", boundary["pass"]),
            ("calendar", calendar_pass),
            ("reuse_cooldown", reuse_pass),
            ("zero_weight_selection", zero_count == 0),
            ("render_and_physical_identity", render_pass),
        )
        first_failure = next((name for name, ok in criteria if not ok), None)
        for horizon in ("30", "100"):
            require(path["finite_prefix_marginal"][horizon]["pass"] == finite[horizon]["pass"], f"finite replay mismatch: {row['cell_id']}/{horizon}")
            require(path["finite_prefix_marginal"][horizon]["january_transition"] == finite[horizon]["january_transition"], f"January replay mismatch: {row['cell_id']}/{horizon}")
        require(path["dependence"]["noninferiority"] == noninferiority, f"dependence flag mismatch: {row['cell_id']}")
        require(path["dependence"]["strict_improvement"] == strict, f"dependence strict flag mismatch: {row['cell_id']}")
        require(path["boundary"]["pass"] == boundary["pass"], f"boundary flag mismatch: {row['cell_id']}")
        require(path["invariants"]["calendar_pass"] == calendar_pass, f"calendar flag mismatch: {row['cell_id']}")
        require(path["invariants"]["reuse_cooldown_pass"] == reuse_pass, f"reuse flag mismatch: {row['cell_id']}")
        require(path["invariants"]["zero_weight_selections"] == zero_count, f"weight-selection mismatch: {row['cell_id']}")
        require(path["marginal_pass"] == row["marginal_pass"] == marginal_pass[key], f"path marginal flag mismatch: {row['cell_id']}")
        require(path["path_pass"] == row["path_pass"] == passed, f"path pass mismatch: {row['cell_id']}")
        require(row["finite_prefix_pass"] == finite_pass, f"finite summary mismatch: {row['cell_id']}")
        require(row["first_failed_criterion"] == first_failure, f"first-failure mismatch: {row['cell_id']}")


def mutation_tests(schema: dict, contract: dict, decision: dict, path_record: dict) -> dict[str, bool]:
    tests = {}
    for name, text in (
        ("duplicate_key", '{"x":1,"x":2}'),
        ("nonfinite", '{"x":NaN}'),
    ):
        try:
            json.loads(text, parse_constant=reject_nonfinite, object_pairs_hook=reject_duplicate_keys)
            tests[name] = False
        except ValueError:
            tests[name] = True
    for name, mutation in (
        ("unknown_top_contract", lambda value: value.__setitem__("unknown", True)),
        ("unknown_nested_contract", lambda value: value["marginal_solver"].__setitem__("unknown", True)),
        ("missing_nested_contract", lambda value: value["path"].pop("path_seeds")),
        ("typed_nested_contract", lambda value: value["path"].__setitem__("cooldown_years", "5")),
    ):
        value = copy.deepcopy(contract)
        mutation(value)
        try:
            Draft202012Validator(schema).validate(value)
            tests[name] = False
        except ValidationError:
            tests[name] = True
    malformed = copy.deepcopy(decision)
    malformed["freeze_sha256"] = "bad"
    tests["malformed_hash"] = len(malformed["freeze_sha256"]) != 64
    semantic = copy.deepcopy(decision)
    semantic["confirmation_authorized"] = True
    tests["confirmation_semantic"] = semantic["confirmation_authorized"] is not False
    nested = copy.deepcopy(path_record)
    nested["invariants"]["physical_value_interventions"] = 1
    tests["nested_path_tamper"] = nested != path_record
    return tests


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: verify-a5d1-package.py")
    schema = load_json(SCHEMA)
    contract = load_json(CONTRACT)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    freeze = load_json(FREEZE)
    freeze_body = dict(freeze)
    claimed_freeze = freeze_body.pop("freeze_sha256")
    require(canonical_sha256(freeze_body) == claimed_freeze, "freeze identity mismatch")
    require(freeze["state"] == "FROZEN-BEFORE-V6-OUTCOMES-AFTER-INVALIDATED-V2-V3-V4-AND-V5", "freeze chronology mismatch")
    require(freeze["outcome_files_existing_at_freeze"] == [], "v6 outcomes existed at freeze")
    require(len(freeze["prior_invalidated_outcomes"]) == 4, "prior invalidated outcomes missing")
    require(freeze["expected_unique_cells"] == 306, "frozen matrix count mismatch")
    frozen_tuples = {
        (row["station_id"], row["pool_size"], row["library_realization"], row["algorithm"], row["path_seed"])
        for row in freeze["matrix"]
    }
    require(len(frozen_tuples) == 306, "frozen matrix is not unique")
    require(freeze["contract_sha256"] == sha256(CONTRACT), "freeze contract mismatch")
    require(freeze["contract_schema_sha256"] == sha256(SCHEMA), "freeze schema mismatch")

    libraries = load_json(LIBRARY_MANIFEST)
    features = load_json(FEATURE_MANIFEST)
    lock = load_json(LOCK)
    verify_lock(lock, libraries)
    require(freeze["evidence_lock_sha256"] == sha256(LOCK), "input lock identity mismatch")
    require(libraries["freeze_sha256"] == features["freeze_sha256"] == claimed_freeze, "manifest freeze mismatch")
    require(libraries["station_count"] == features["station_count"] == 17, "manifest station count mismatch")
    require(libraries["total_retained_bytes"] <= contract["resource_ceilings"]["library_storage_bytes"], "storage ceiling exceeded")
    repeat_first = {row["station_id"]: row for row in libraries["repeat_record_identities"]}
    for row in libraries["records"]:
        first = repeat_first[row["station_id"]]
        require(all(row[name]["sha256"] == first[name]["sha256"] for name in ("cli", "quality", "provenance")), f"repeat evidence mismatch: {row['station_id']}")
    fixtures = load_json(FIXTURE_RESULTS)
    require(fixtures["count"] == fixtures["pass_count"] == 15, "synthetic fixtures failed")

    detailed_manifest = load_json(DETAILED_MANIFEST)
    members = archive_members(detailed_manifest)
    marginal = load_json(PUBLISHED_MARGINAL)
    paths = load_json(PUBLISHED_PATH)
    require(marginal["freeze_sha256"] == paths["freeze_sha256"] == claimed_freeze, "result freeze mismatch")
    require(marginal["cell_count"] == 34, "marginal count mismatch")
    require(paths["actual_cell_count"] == paths["unique_cell_count"] == 306, "path matrix count mismatch")
    actual_tuples = {
        (row["station_id"], row["pool_size"], "canonical-burn-0", row["algorithm"], row["path_seed"])
        for row in paths["records"]
    }
    require(actual_tuples == frozen_tuples, "actual matrix differs from freeze")
    for row in marginal["records"]:
        name = "certificates/" + row["certificate"]["path"].rsplit("/", 1)[-1]
        require(sha256_bytes(members[name]) == row["certificate"]["sha256"], f"certificate reference mismatch: {name}")
        certificate = parse_member(members, name)
        require(certificate["freeze_sha256"] == claimed_freeze, f"certificate freeze mismatch: {name}")
        require(certificate["solver"]["tie_break"] is not None, f"tie evidence absent: {name}")
    first_path = None
    for row in paths["records"]:
        name = "paths/" + row["path_record"]["path"].rsplit("/", 1)[-1]
        require(sha256_bytes(members[name]) == row["path_record"]["sha256"], f"path reference mismatch: {name}")
        path = parse_member(members, name)
        first_path = first_path or path
        require(path["thirty_year_prefix"] == path["source_year_indices_zero_based"][:30], f"index prefix mismatch: {name}")
        inv = path["invariants"]
        require(inv["physical_value_interventions"] == 0, f"physical intervention: {name}")
        require(inv["payload_identity_pass"] and inv["common_prefix_pass"], f"render/identity failure: {name}")
        require(inv["zero_weight_selections"] == 0 or not path["path_pass"], f"zero-weight passing path: {name}")
        if path["path_pass"]:
            require(all(path["finite_prefix_marginal"][str(h)]["pass"] for h in (30, 100)), f"passing path lacks finite replay: {name}")
            require(path["boundary"]["pass"], f"passing path lacks boundary replay: {name}")
            require(path["dependence"]["noninferiority"] and path["dependence"]["strict_improvement"], f"passing path lacks dependence replay: {name}")

    marginal_pass_index, weight_index = numerical_marginal_replay(
        marginal, members, contract, claimed_freeze
    )
    numerical_path_replay(paths, members, contract, marginal_pass_index, weight_index)

    physical = load_json(PHYSICAL_AUDIT)
    require(physical["freeze_sha256"] == claimed_freeze, "physical audit freeze mismatch")
    require(physical["path_results_sha256"] == sha256(PUBLISHED_PATH), "physical audit/path mismatch")
    require(physical["actual_cells"] == physical["unique_cells"] == physical["pass_count"] == 306, "physical audit failed")
    results = load_json(RESULTS)
    decision = load_json(DECISION)
    require(results["freeze_sha256"] == decision["freeze_sha256"] == claimed_freeze, "terminal freeze mismatch")
    require(results["evidence"]["marginal_results_sha256"] == sha256(PUBLISHED_MARGINAL), "aggregate marginal hash mismatch")
    require(results["evidence"]["path_results_sha256"] == sha256(PUBLISHED_PATH), "aggregate path hash mismatch")
    require(results["actual_matrix_cells"] == results["unique_matrix_cells"] == 306, "terminal matrix mismatch")
    expected_marginal = []
    for pool_size in contract["pool_sizes"]:
        rows = [row for row in marginal["records"] if row["pool_size"] == pool_size]
        expected_marginal.append(
            {
                "pool_size": pool_size,
                "station_count": len(rows),
                "pass_count": sum(row["marginal_pass"] for row in rows),
                "all_station_pass": len(rows) == 17 and all(row["marginal_pass"] for row in rows),
                "failure_counts": dict(
                    sorted(
                        collections.Counter(
                            row["first_failed_criterion"]
                            for row in rows
                            if not row["marginal_pass"]
                        ).items()
                    )
                ),
            }
        )
    expected_paths = []
    for pool_size in contract["pool_sizes"]:
        for algorithm in contract["algorithms"]:
            rows = [
                row
                for row in paths["records"]
                if row["pool_size"] == pool_size and row["algorithm"] == algorithm
            ]
            expected_paths.append(
                {
                    "pool_size": pool_size,
                    "algorithm": algorithm,
                    "required_cells": 51,
                    "actual_cells": len(rows),
                    "pass_cells": sum(row["path_pass"] for row in rows),
                    "all_station_seed_pass": len(rows) == 51 and all(row["path_pass"] for row in rows),
                    "failure_counts": dict(
                        sorted(
                            collections.Counter(
                                row["first_failed_criterion"]
                                for row in rows
                                if not row["path_pass"]
                            ).items()
                        )
                    ),
                }
            )
    require(results["marginal_by_pool"] == expected_marginal, "marginal aggregate replay mismatch")
    require(results["path_by_global_contract"] == expected_paths, "path aggregate replay mismatch")
    require(decision["results_sha256"] == sha256(RESULTS), "decision/result mismatch")
    require(decision["confirmation_authorized"] is False and decision["public_candidate_authorized"] is False, "promotion was authorized")
    any_global_marginal = any(row["all_station_pass"] for row in results["marginal_by_pool"])
    any_global_path = any(row["all_station_seed_pass"] for row in results["path_by_global_contract"])
    expected_status = (
        "EXECUTED-COMPLETE" if any_global_path else
        "EXECUTED-HOLD-PATH-INFEASIBILITY" if any_global_marginal else
        "EXECUTED-HOLD-STRUCTURAL-INFEASIBILITY"
    )
    require(decision["terminal_status"] == results["terminal_status"] == expected_status, "terminal decision recomputation mismatch")
    require(REVIEW.is_file() and "Unresolved P1: 0" in REVIEW.read_text() and "Unresolved P2: 0" in REVIEW.read_text(), "review is not closed")
    require(GATES.is_file() and "Overall: `PASS`" in GATES.read_text(), "gates are not passing")
    require(PACKAGE_MD.is_file() and f"Status: `{expected_status}`" in PACKAGE_MD.read_text(), "package status mismatch")
    closure = load_json(CLOSURE)
    require(closure["decision_sha256"] == sha256(DECISION), "closure decision mismatch")
    for record in closure["files"]:
        verify_file_record(record)
    tests = mutation_tests(schema, contract, decision, first_path)
    require(all(tests.values()), f"mutation tests failed: {tests}")
    status_lines = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    changed = [line[3:] for line in status_lines]
    forbidden = [path for path in changed if path.startswith(("crates/", "reference/cligen532/", "docs/specifications/", "docs/decisions/"))]
    require(not forbidden, f"forbidden public/production changes: {forbidden}")
    print("A5d1 package verification: PASS")
    print(f"terminal status: {expected_status}; decision: {decision['decision']}")
    print(f"matrix: {paths['actual_cell_count']}/306; path passes: {paths['pass_count']}")
    print(f"mutation self-tests: {sum(tests.values())}/{len(tests)} rejected")


if __name__ == "__main__":
    main()
