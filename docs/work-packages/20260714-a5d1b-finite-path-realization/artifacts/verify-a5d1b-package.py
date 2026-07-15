#!/usr/bin/env python3
"""Fail-closed terminal verifier for the A5d1b work package."""

from __future__ import annotations

import copy
import io
import json
import math
import sys
import tarfile

from jsonschema import Draft202012Validator, ValidationError

from a5d1b_common import (
    A5D1_CONTRACT,
    ARTIFACTS,
    CONTRACT,
    CONTRACT_SCHEMA,
    COUNT_RESULTS,
    DIAGNOSTIC_RESULTS,
    FREEZE,
    LOCK,
    PATH_RESULTS,
    ROOT,
    a5d1_modules,
    canonical_sha256,
    certificate_path,
    count_only_replay,
    feature_path,
    load_json,
    reject_duplicate_keys,
    reject_nonfinite,
    sha256,
    validate_counts,
)


FIXTURE_RESULTS = ARTIFACTS / "synthetic-fixture-results-v1.json"
INCUMBENT_FIXTURE_RESULTS = ARTIFACTS / "incumbent-acceptance-fixture-results-v1.json"
COUNT_WITNESS_AUDIT = ARTIFACTS / "count-witness-replay-audit-v1.json"
DETAILED_ARCHIVE = ARTIFACTS / "detailed-evidence-v1.tar.gz"
DETAILED_MANIFEST = ARTIFACTS / "detailed-evidence-manifest-v1.json"
RESULTS = ARTIFACTS / "a5d1b-results-v1.json"
DECISION = ARTIFACTS / "a5d1b-decision-v1.json"
REVIEW = ARTIFACTS / "review.md"
GATES = ARTIFACTS / "gate-results.md"
CLOSURE = ARTIFACTS / "closure-evidence-v1.json"
AMENDMENT_001 = ARTIFACTS / "pre-outcome-freeze-amendment-001.json"
AMENDMENT_002 = ARTIFACTS / "pre-outcome-freeze-amendment-002.json"
AMENDMENT_003 = ARTIFACTS / "post-outcome-correction-amendment-003.json"
AMENDMENT_004 = ARTIFACTS / "post-outcome-correction-amendment-004.json"
FREEZE_V2 = ARTIFACTS / "pre-outcome-freeze-v2.json"
FREEZE_V3 = ARTIFACTS / "pre-outcome-freeze-v3.json"
FREEZE_V4 = ARTIFACTS / "corrected-execution-freeze-v4.json"
V3_TOOL_HISTORY = ARTIFACTS / "history/v3-tools"
V4_TOOL_HISTORY = ARTIFACTS / "history/v4-tools"
REPORT = ROOT / "docs/reports/a5d1b-finite-path-realization-report.md"
REPORT_MANIFEST = REPORT.with_suffix(".manifest.json")
PACKAGE_MD = ARTIFACTS.parent / "package.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def close(actual: float, expected: float, tolerance: float = 2.0e-8) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def verify_identity(record: dict) -> None:
    path = ROOT / record["path"]
    require(path.is_file(), f"locked file missing: {path}")
    require(path.stat().st_size == record["bytes"], f"locked byte count changed: {path}")
    require(sha256(path) == record["sha256"], f"locked hash changed: {path}")


def strict_json_mutations() -> int:
    rejected = 0
    for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
        try:
            json.loads(text, parse_constant=reject_nonfinite, object_pairs_hook=reject_duplicate_keys)
        except ValueError:
            rejected += 1
    try:
        json.loads('{"x":1e9999}', parse_float=lambda token: (_ for _ in ()).throw(ValueError("overflow")) if not math.isfinite(float(token)) else float(token))
    except ValueError:
        rejected += 1
    return rejected


def verify_archive(manifest: dict) -> None:
    require(manifest["archive"]["sha256"] == sha256(DETAILED_ARCHIVE), "archive hash mismatch")
    require(manifest["archive"]["bytes"] == DETAILED_ARCHIVE.stat().st_size, "archive byte mismatch")
    records = {row["member"]: row for row in manifest["members"]}
    with tarfile.open(DETAILED_ARCHIVE, "r:gz") as archive:
        names = archive.getnames()
        require(names == sorted(names), "archive ordering is not deterministic")
        require(len(names) == len(set(names)) == manifest["member_count"], "archive member closure mismatch")
        require(set(names) == set(records), "archive manifest set mismatch")
        for member in archive.getmembers():
            handle = archive.extractfile(member)
            require(handle is not None, f"archive member unreadable: {member.name}")
            payload = handle.read()
            digest = __import__("hashlib").sha256(payload).hexdigest()
            require(len(payload) == records[member.name]["bytes"], f"archive member bytes mismatch: {member.name}")
            require(digest == records[member.name]["sha256"], f"archive member hash mismatch: {member.name}")


def verify_count_results(contract: dict, a5d1_contract: dict, freeze_sha256: str) -> dict[str, dict]:
    results = load_json(COUNT_RESULTS)
    require(results["freeze_sha256"] == freeze_sha256, "count freeze mismatch")
    require(results["expected_station_count"] == results["actual_station_count"] == results["unique_station_count"] == 17, "count matrix closure failure")
    solver, _ = a5d1_modules()
    index = {}
    pass_count = 0
    linear_count = 0
    for row in results["records"]:
        verify_identity(row["certificate"])
        certificate = load_json(ROOT / row["certificate"]["path"])
        station_id = row["station_id"]
        require(certificate["station_id"] == station_id and certificate["freeze_sha256"] == freeze_sha256, f"count certificate identity mismatch: {station_id}")
        require(certificate["source_feature"]["sha256"] == sha256(feature_path(station_id)), f"feature identity mismatch: {station_id}")
        require(certificate["source_marginal_certificate"]["sha256"] == sha256(certificate_path(station_id)), f"stationary certificate identity mismatch: {station_id}")
        feature = load_json(feature_path(station_id))
        stationary = load_json(certificate_path(station_id))
        blocks = feature["blocks"][:256]
        problem = solver.build_problem(blocks, feature["targets"], a5d1_contract)
        witness = certificate["count_witness"]
        replay_pass = False
        if witness is not None:
            validation = validate_counts(blocks, stationary["weights"], witness["counts_30"], witness["counts_100"], contract["nested_count_constraints"]["positive_weight_threshold"])
            replay30 = count_only_replay(problem, blocks, witness["counts_30"], 30, a5d1_contract)
            replay100 = count_only_replay(problem, blocks, witness["counts_100"], 100, a5d1_contract)
            require(validation == witness["validation"], f"count invariant replay mismatch: {station_id}")
            for horizon, replay in (("30", replay30), ("100", replay100)):
                stored = witness["replay"][horizon]
                require(replay["pass"] == stored["pass"], f"count replay pass mismatch: {station_id}:{horizon}")
                require(close(replay["violation_objective"], stored["violation_objective"]), f"count replay objective mismatch: {station_id}:{horizon}")
                require(close(replay["preservation_maximum_residual"], stored["preservation_maximum_residual"]), f"count replay residual mismatch: {station_id}:{horizon}")
            replay_pass = validation["pass"] and replay30["pass"] and replay100["pass"]
        require(certificate["count_pass"] == row["count_pass"] == replay_pass, f"count pass mismatch: {station_id}")
        require(certificate["linear_necessary_system_witness"] == row["linear_necessary_system_witness"], f"linear status mismatch: {station_id}")
        pass_count += replay_pass
        linear_count += certificate["linear_necessary_system_witness"]
        index[station_id] = certificate
    require(pass_count == results["count_pass_count"], "count pass aggregate mismatch")
    require(linear_count == results["linear_necessary_system_witness_count"], "linear witness aggregate mismatch")
    return index


def verify_path_results(contract: dict, counts: dict[str, dict], freeze_sha256: str) -> None:
    results = load_json(PATH_RESULTS)
    require(results["freeze_sha256"] == freeze_sha256, "path freeze mismatch")
    if sum(certificate["count_pass"] for certificate in counts.values()) != 17:
        require(not results["executed"] and results["actual_cells"] == results["pass_count"] == 0 and results["records"] == [], "ordering ran before complete count gate")
        return
    require(results["executed"], "ordering did not run after count gate")
    require(results["expected_cells_if_executed"] == results["actual_cells"] == results["unique_cells"] == 51, "ordered matrix closure failure")
    pass_count = 0
    for row in results["records"]:
        verify_identity(row["path_record"])
        record = load_json(ROOT / row["path_record"]["path"])
        require(record["freeze_sha256"] == freeze_sha256 and record["cell_id"] == row["cell_id"], f"path identity mismatch: {row['cell_id']}")
        exact_pass = (
            all(value["pass"] for value in record["finite_prefix"].values())
            and record["dependence"]["noninferiority"]
            and record["dependence"]["strict_improvement"]
            and record["boundary"]["pass"]
            and record["invariants"]["pass"]
            and not record["search"]["resource_exhausted"]
        )
        require(exact_pass == record["path_pass"] == row["path_pass"], f"path pass mismatch: {row['cell_id']}")
        pass_count += exact_pass
    require(pass_count == results["pass_count"], "path pass aggregate mismatch")


def verify_closure() -> None:
    closure = load_json(CLOSURE)
    for record in closure["files"]:
        verify_identity(record)
    require(closure["report_sha256"] == sha256(REPORT), "closure report mismatch")
    require(closure["decision_sha256"] == sha256(DECISION), "closure decision mismatch")


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: verify-a5d1b-package.py")
    contract = load_json(CONTRACT)
    schema = load_json(CONTRACT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    freeze = load_json(FREEZE)
    body = dict(freeze)
    claimed = body.pop("freeze_sha256")
    require(canonical_sha256(body) == claimed, "freeze canonical identity mismatch")
    lock = load_json(LOCK)
    require(sha256(LOCK) == freeze["evidence_lock_sha256"], "freeze/lock mismatch")
    for record in lock["authority_inputs"]:
        verify_identity(record)
    amendment_001 = load_json(AMENDMENT_001)
    amendment_002 = load_json(AMENDMENT_002)
    amendment_003 = load_json(AMENDMENT_003)
    amendment_004 = load_json(AMENDMENT_004)
    freeze_v2 = load_json(FREEZE_V2)
    freeze_v3 = load_json(FREEZE_V3)
    freeze_v4 = load_json(FREEZE_V4)
    freeze_v2_body = dict(freeze_v2)
    freeze_v2_claimed = freeze_v2_body.pop("freeze_sha256")
    require(canonical_sha256(freeze_v2_body) == freeze_v2_claimed, "freeze v2 identity mismatch")
    require(amendment_001["parent_freeze_sha256"] == freeze_v2["parent_freeze_sha256"], "amendment 001 parent mismatch")
    require(freeze_v2["amendment_sha256"] == sha256(AMENDMENT_001), "amendment 001 hash mismatch")
    freeze_v3_body = dict(freeze_v3)
    freeze_v3_claimed = freeze_v3_body.pop("freeze_sha256")
    require(canonical_sha256(freeze_v3_body) == freeze_v3_claimed, "freeze v3 identity mismatch")
    require(freeze_v3["parent_freeze_sha256"] == freeze_v2_claimed, "freeze v3 parent mismatch")
    require(amendment_002["parent_freeze_sha256"] == freeze_v2_claimed, "amendment 002 parent mismatch")
    require(freeze_v3["amendment_sha256"] == sha256(AMENDMENT_002), "amendment 002 hash mismatch")
    freeze_v4_body = dict(freeze_v4)
    freeze_v4_claimed = freeze_v4_body.pop("freeze_sha256")
    require(canonical_sha256(freeze_v4_body) == freeze_v4_claimed, "freeze v4 identity mismatch")
    require(freeze_v4["parent_freeze_sha256"] == freeze_v3_claimed, "freeze v4 parent mismatch")
    require(amendment_003["parent_freeze_sha256"] == freeze_v3_claimed, "amendment 003 parent mismatch")
    require(freeze_v4["amendment_sha256"] == sha256(AMENDMENT_003), "amendment 003 hash mismatch")
    require(amendment_003["scientific_contract_changed"] is False, "correction changed scientific contract")
    require(amendment_003["algorithm_implementation_changed"] is True, "correction implementation not disclosed")
    require(freeze["parent_freeze_sha256"] == freeze_v4_claimed, "freeze v5 parent mismatch")
    require(amendment_004["parent_freeze_sha256"] == freeze_v4_claimed, "amendment 004 parent mismatch")
    require(freeze["amendment_sha256"] == sha256(AMENDMENT_004), "amendment 004 hash mismatch")
    require(amendment_004["scientific_contract_changed"] is False, "aggregate correction changed scientific contract")
    require(amendment_004["algorithm_implementation_changed"] is False, "aggregate correction algorithm disclosure mismatch")
    for name, digest in freeze_v3["tool_hashes"].items():
        require(sha256(V3_TOOL_HISTORY / name) == digest, f"historical v3 tool hash mismatch: {name}")
    for name, digest in freeze_v4["tool_hashes"].items():
        require(sha256(V4_TOOL_HISTORY / name) == digest, f"historical v4 tool hash mismatch: {name}")
    for name, digest in freeze["tool_hashes"].items():
        require(sha256(ARTIFACTS / name) == digest, f"amended tool hash mismatch: {name}")
    for name in ("contract", "contract_schema", "synthetic_fixtures", "synthetic_fixture_results"):
        verify_identity(lock[name])
    for station in lock["stations"]:
        for name in ("feature", "marginal_certificate", "faithful_off_library"):
            verify_identity(station[name])
    require(lock["station_count"] == 17, "lock station count mismatch")
    require(lock["production_source_changes"] == lock["public_surface_changes"] == 0, "production/public surface exposure")
    require(all(lock["exposure"][name] == 0 for name in ("confirmation_objects_accessed", "confirmation_target_values_accessed", "confirmation_wepp_responses_accessed")), "confirmation exposure")
    fixtures = load_json(FIXTURE_RESULTS)
    require(fixtures["expected_count"] == fixtures["actual_count"] == fixtures["pass_count"] == 12, "synthetic fixture closure failure")
    incumbent_fixtures = load_json(INCUMBENT_FIXTURE_RESULTS)
    require(incumbent_fixtures["expected_count"] == incumbent_fixtures["actual_count"] == incumbent_fixtures["pass_count"] == 4, "incumbent fixture closure failure")
    diagnostics = load_json(DIAGNOSTIC_RESULTS)
    require(diagnostics["freeze_sha256"] == freeze["diagnostic_freeze_sha256"], "diagnostic parent-freeze mismatch")
    require(diagnostics["expected_cells"] == diagnostics["actual_cells"] == diagnostics["unique_cells"] == 153, "diagnostic matrix closure failure")
    require(diagnostics["published_first_failure_counts"] == {"dependence_noninferiority": 2, "finite_prefix_marginal": 151}, "inherited failure surface mismatch")
    a5d1_contract = load_json(A5D1_CONTRACT)
    counts = verify_count_results(contract, a5d1_contract, claimed)
    count_results = load_json(COUNT_RESULTS)
    require(count_results["station_budget_scheduler_pass_count"] == 17, "station solver scheduling budget failure")
    require(count_results["total_wall_seconds"] <= contract["resource_ceilings"]["total_wall_seconds"], "total solver wall ceiling failure")
    require(count_results["peak_rss_bytes"] <= contract["resource_ceilings"]["peak_rss_bytes"], "solver peak RSS ceiling failure")
    witness_audit = load_json(COUNT_WITNESS_AUDIT)
    require(witness_audit["pass"] and witness_audit["station_count"] == 17, "count witness replay audit failure")
    require(witness_audit["joint_exact_pass_count"] == count_results["count_pass_count"], "count witness audit joint aggregate mismatch")
    require(witness_audit["separate_horizon_replay"]["100"]["exact"] == count_results["separate_horizon_summary"]["100"]["exact_pass_count"], "count witness audit separate aggregate mismatch")
    require(witness_audit["mutation_self_test_rejected"], "count witness mutation gate failure")
    verify_path_results(contract, counts, claimed)
    manifest = load_json(DETAILED_MANIFEST)
    verify_archive(manifest)
    results = load_json(RESULTS)
    decision = load_json(DECISION)
    require(decision["results_sha256"] == sha256(RESULTS), "decision/results mismatch")
    require(decision["terminal_status"] == results["terminal_status"], "terminal status mismatch")
    require(not decision["confirmation_authorized"] and not decision["public_candidate_authorized"], "candidate/confirmation authorization")
    require(results["count_pass_count"] == sum(certificate["count_pass"] for certificate in counts.values()), "terminal count mismatch")
    require(REPORT.is_file() and REPORT_MANIFEST.is_file() and REVIEW.is_file() and GATES.is_file() and CLOSURE.is_file(), "terminal report/review/gate/closure record missing")
    verify_closure()
    require(results["terminal_status"] in PACKAGE_MD.read_text(encoding="utf-8"), "package terminal status mismatch")
    require(strict_json_mutations() == 4, "strict JSON mutation gate failure")
    schema_mutation = copy.deepcopy(contract)
    schema_mutation["unexpected"] = True
    try:
        Draft202012Validator(schema).validate(schema_mutation)
    except ValidationError:
        pass
    else:
        raise ValueError("schema accepted unknown property")
    print(
        f"A5d1b package verification: PASS\nterminal: {results['terminal_status']}\n"
        f"diagnostics: 153/153; counts: {results['count_pass_count']}/17; "
        f"paths: {results['ordered_path_pass_count']}/{results['ordered_path_actual_cells']}\n"
        "mutation self-tests: 5/5 rejected"
    )


if __name__ == "__main__":
    main()
