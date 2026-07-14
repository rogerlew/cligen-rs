#!/usr/bin/env python3
"""Post-result closure checks supplementing the frozen A5d1 verifier."""

from __future__ import annotations

import collections
import importlib.util
import json
import math
import sys
from pathlib import Path

from a5d1_common import (
    CONTRACT,
    FEATURE_DIR,
    FREEZE,
    PACKAGE,
    ROOT,
    load_json,
    sha256,
)


RESOURCE = PACKAGE / "resource-evidence-v1.json"
LIBRARY_MANIFEST = PACKAGE / "development-library-manifest-v1.json"
FEATURE_MANIFEST = PACKAGE / "year-feature-manifest-v1.json"
MARGINAL = PACKAGE / "marginal-results-v1.json"
PATHS = PACKAGE / "path-results-v1.json"
RESULTS = PACKAGE / "selector-feasibility-results-v1.json"
DECISION = PACKAGE / "a5d1-decision-v1.json"
DETAILED_MANIFEST = PACKAGE / "detailed-evidence-manifest-v1.json"
SEMANTIC_AUDIT = PACKAGE / "semantic-replay-audit-v1.json"
REPLAY_MANIFEST = PACKAGE / "replay-evidence-manifest-v1.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FROZEN = load_module("a5d1_frozen_verifier", PACKAGE / "verify-a5d1-package.py")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_record(record: dict) -> None:
    path = ROOT / record["path"]
    require(path.is_file(), f"manifest file missing: {path}")
    if "bytes" in record:
        require(path.stat().st_size == record["bytes"], f"manifest size mismatch: {path}")
    require(sha256(path) == record["sha256"], f"manifest hash mismatch: {path}")


def compare(actual, expected, label: str) -> None:
    if isinstance(actual, bool) or isinstance(expected, bool):
        require(actual is expected, f"semantic Boolean mismatch: {label}")
    elif isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        require(
            math.isclose(float(actual), float(expected), rel_tol=2.0e-10, abs_tol=2.0e-10),
            f"semantic numeric mismatch: {label}: {actual} != {expected}",
        )
    elif isinstance(actual, dict) and isinstance(expected, dict):
        require(set(actual) == set(expected), f"semantic key mismatch: {label}")
        for key in sorted(actual):
            compare(actual[key], expected[key], f"{label}.{key}")
    elif isinstance(actual, list) and isinstance(expected, list):
        require(len(actual) == len(expected), f"semantic list length mismatch: {label}")
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f"{label}[{index}]")
    else:
        require(actual == expected, f"semantic value mismatch: {label}")


def verify_resources(contract: dict, freeze: dict) -> None:
    resource = load_json(RESOURCE)
    paths = load_json(PATHS)
    marginal = load_json(MARGINAL)
    libraries = load_json(LIBRARY_MANIFEST)
    features = load_json(FEATURE_MANIFEST)
    audit = load_json(SEMANTIC_AUDIT)
    replay_manifest = load_json(REPLAY_MANIFEST)
    require(resource["post_result_closure_evidence"] is True, "resource role mismatch")
    require(resource["freeze_sha256"] == freeze["freeze_sha256"], "resource freeze mismatch")
    require(resource["contract_sha256"] == sha256(CONTRACT), "resource contract mismatch")
    require(
        resource["locked_path_tool_sha256"] == freeze["tool_hashes"]["run-path-feasibility.py"],
        "resource path-tool mismatch",
    )
    require(resource["published_path_results_sha256"] == sha256(PATHS), "resource path-result mismatch")
    require(resource["library_manifest_sha256"] == sha256(LIBRARY_MANIFEST), "resource library-manifest mismatch")
    require(resource["feature_manifest_sha256"] == sha256(FEATURE_MANIFEST), "resource feature-manifest mismatch")
    require(resource["marginal_results_sha256"] == sha256(MARGINAL), "resource marginal-result mismatch")
    require(resource["published_path_total_seconds"] == paths["total_wall_seconds"], "published path wall mismatch")
    require(
        resource["published_path_max_cell_seconds"]
        == max(row["wall_seconds"] for row in paths["records"]),
        "path cell wall mismatch",
    )
    require(
        resource["marginal_max_cell_seconds"]
        == max(row["wall_seconds"] for row in marginal["records"]),
        "solver wall mismatch",
    )
    require(resource["library_retained_bytes"] == libraries["total_retained_bytes"], "storage mismatch")
    require(resource["feature_stage_internal_seconds"] == features["wall_seconds"], "feature wall mismatch")
    require(resource["semantic_replay"]["match"] is True, "semantic replay did not match")
    require(
        resource["semantic_replay"]["audit_sha256"] == sha256(SEMANTIC_AUDIT),
        "semantic audit hash mismatch",
    )
    require(resource["semantic_replay"]["first_sha256"] == audit["first_semantic_sha256"], "first semantic hash mismatch")
    require(resource["semantic_replay"]["replay_sha256"] == audit["replay_semantic_sha256"], "replay semantic hash mismatch")
    require(resource["semantic_replay"]["exact_match"] == audit["exact_semantic_match"], "exact-match flag mismatch")
    require(resource["semantic_replay"]["match"] == audit["semantic_equivalent"], "semantic equivalence mismatch")
    require(resource["semantic_replay"]["numeric_mismatch_count"] == audit["numeric_mismatch_count"] == 0, "numeric replay mismatch")
    require(resource["semantic_replay"]["structural_mismatch_count"] == audit["structural_mismatch_count"] == 0, "structural replay mismatch")
    require(resource["semantic_replay"]["maximum_absolute_difference"] == audit["maximum_absolute_difference"], "semantic max-absolute mismatch")
    require(resource["semantic_replay"]["maximum_relative_difference"] == audit["maximum_relative_difference"], "semantic max-relative mismatch")
    require(resource["semantic_replay"]["replay_archive_sha256"] == replay_manifest["archive"]["sha256"], "replay archive mismatch")
    require(resource["resource_ceilings"] == contract["resource_ceilings"], "recorded resource ceilings differ")
    require(
        resource["maximum_resident_set_bytes"]
        == max(row["maximum_resident_set_bytes"] for row in resource["timed_commands"]),
        "maximum RSS summary mismatch",
    )
    first_roles = {
        "first_execution_library",
        "first_execution_features",
        "first_execution_marginal",
        "first_execution_path",
    }
    require(
        math.isclose(
            resource["first_execution_stage_wall_upper_bound_seconds"],
            math.fsum(
                row["real_seconds"]
                for row in resource["timed_commands"]
                if row["role"] in first_roles
            ),
            abs_tol=1.0e-9,
        ),
        "first-execution wall summary mismatch",
    )
    require(
        resource["library_retained_bytes"] <= contract["resource_ceilings"]["library_storage_bytes"],
        "library storage ceiling exceeded",
    )
    require(
        resource["maximum_resident_set_bytes"] <= contract["resource_ceilings"]["peak_rss_bytes"],
        "peak RSS ceiling exceeded",
    )
    require(
        resource["marginal_max_cell_seconds"]
        <= contract["resource_ceilings"]["solver_seconds_per_station_pool"],
        "solver cell ceiling exceeded",
    )
    require(
        resource["first_execution_stage_wall_upper_bound_seconds"]
        <= contract["resource_ceilings"]["total_wall_seconds"],
        "total wall ceiling exceeded",
    )
    require(all(row["exit_status"] == 0 for row in resource["timed_commands"]), "timed command failed")
    require(resource["ceiling_checks"] == {
        "library_storage": True,
        "peak_rss": True,
        "solver_per_station_pool": True,
        "total_wall": True,
    }, "resource ceiling flags mismatch")


def verify_manifests() -> None:
    libraries = load_json(LIBRARY_MANIFEST)
    canonical = {row["station_id"]: row for row in libraries["records"]}
    repeated = {row["station_id"]: row for row in libraries["repeat_record_identities"]}
    require(set(canonical) == set(repeated) and len(canonical) == 17, "library station set mismatch")
    for station_id in sorted(canonical):
        final = canonical[station_id]
        first = repeated[station_id]
        for name in ("cli", "quality", "provenance", "runspec"):
            verify_record(final[name])
            verify_record(first[name])
        for name in ("cli", "quality", "provenance"):
            require(
                final[name]["sha256"] == first[name]["sha256"],
                f"repeat identity mismatch: {station_id}/{name}",
            )
        require(final["runspec"]["sha256"] == first["runspec"]["sha256"], f"runspec semantic mismatch: {station_id}")
    features = load_json(FEATURE_MANIFEST)
    require(features["source_library_manifest_sha256"] == sha256(LIBRARY_MANIFEST), "feature/library manifest mismatch")
    require(len(features["records"]) == 17, "feature station count mismatch")
    for record in features["records"]:
        verify_record(record)


def verify_detailed_semantics(contract: dict) -> None:
    marginal = load_json(MARGINAL)
    paths = load_json(PATHS)
    detailed_manifest = load_json(DETAILED_MANIFEST)
    members = FROZEN.archive_members(detailed_manifest)
    marginal_pass, weight_index = FROZEN.numerical_marginal_replay(
        marginal, members, contract, load_json(FREEZE)["freeze_sha256"]
    )
    require(marginal["contract_sha256"] == sha256(CONTRACT), "marginal contract hash mismatch")
    require(marginal["pass_count"] == sum(row["marginal_pass"] for row in marginal["records"]), "marginal pass count mismatch")
    for row in marginal["records"]:
        name = "certificates/" + row["certificate"]["path"].rsplit("/", 1)[-1]
        certificate = FROZEN.parse_member(members, name)
        expected_failure = next(
            (
                name
                for name, passed in (
                    (
                        "solver_status_and_tie_break",
                        certificate["solver"]["success"]
                        and certificate["solver"]["tie_break"] is not None
                        and certificate["solver"]["tie_break"]["success"],
                    ),
                    ("independent_residual_replay", certificate["independent_replay_pass"]),
                    ("component_noninferiority", certificate["annual"]["noninferiority"]),
                    ("aggregate_strict_improvement", certificate["annual"]["strict_improvement"]),
                )
                if not passed
            ),
            None,
        )
        require(
            certificate["first_failed_criterion"] == row["first_failed_criterion"] == expected_failure,
            f"marginal first failure mismatch: {row['station_id']}/{row['pool_size']}",
        )
    require(paths["contract_sha256"] == sha256(CONTRACT), "path contract hash mismatch")
    require(paths["marginal_results_sha256"] == sha256(MARGINAL), "path marginal hash mismatch")
    require(paths["pass_count"] == sum(row["path_pass"] for row in paths["records"]), "path pass count mismatch")
    require(paths["actual_cell_count"] == paths["unique_cell_count"] == len(paths["records"]) == 306, "path count mismatch")
    FROZEN.numerical_path_replay(paths, members, contract, marginal_pass, weight_index)
    cache = {}
    for row in paths["records"]:
        key = (row["station_id"], row["pool_size"])
        if key not in cache:
            feature = load_json(FEATURE_DIR / f"{row['station_id']}-year-features-v1.json")
            blocks = feature["blocks"][: row["pool_size"]]
            cache[key] = (
                blocks,
                FROZEN.SOLVER.build_problem(blocks, feature["targets"], contract),
                FROZEN.PATH_TOOL.target_dependence(feature),
            )
        blocks, problem, target = cache[key]
        name = "paths/" + row["path_record"]["path"].rsplit("/", 1)[-1]
        path = FROZEN.parse_member(members, name)
        indices = path["source_year_indices_zero_based"]
        finite = {
            str(horizon): FROZEN.SOLVER.finite_prefix_replay(
                problem, blocks, indices, horizon, contract
            )
            for horizon in (30, 100)
        }
        compare(path["finite_prefix_marginal"], finite, f"finite.{row['cell_id']}")
        baseline_indices = list(range(100))
        baseline = FROZEN.PATH_TOOL.path_metrics(blocks, baseline_indices)
        actual = FROZEN.PATH_TOOL.path_metrics(blocks, indices)
        aggregate, components, baseline_components, scales = FROZEN.PATH_TOOL.distances(
            actual, target, baseline
        )
        expected_dependence = {
            "detrending": "OLS linear detrend applied identically to target, baseline, and candidate",
            "target": target,
            "baseline": baseline,
            "actual": actual,
            "scales": scales,
            "baseline_components": baseline_components,
            "actual_components": components,
            "baseline_aggregate": math.fsum(baseline_components.values()),
            "actual_aggregate": aggregate,
            "noninferiority": all(
                components[name] <= baseline_components[name] + 0.10 + 1.0e-9
                for name in components
            ),
            "strict_improvement": aggregate
            <= 0.95 * math.fsum(baseline_components.values()) + 1.0e-9,
        }
        compare(path["dependence"], expected_dependence, f"dependence.{row['cell_id']}")
        boundary = FROZEN.PATH_TOOL.boundary_replay(blocks, indices, baseline_indices, contract)
        compare(path["boundary"], boundary, f"boundary.{row['cell_id']}")


def verify_terminal_aggregates() -> None:
    marginal = load_json(MARGINAL)
    paths = load_json(PATHS)
    results = load_json(RESULTS)
    decision = load_json(DECISION)
    require(results["evidence"]["marginal_results_sha256"] == sha256(MARGINAL), "result marginal hash mismatch")
    require(results["evidence"]["path_results_sha256"] == sha256(PATHS), "result path hash mismatch")
    expected_marginal = []
    for pool_size in (128, 256):
        rows = [row for row in marginal["records"] if row["pool_size"] == pool_size]
        expected_marginal.append(
            {
                "pool_size": pool_size,
                "station_count": len(rows),
                "pass_count": sum(row["marginal_pass"] for row in rows),
                "all_station_pass": len(rows) == 17 and all(row["marginal_pass"] for row in rows),
                "failure_counts": dict(sorted(collections.Counter(
                    row["first_failed_criterion"] for row in rows if not row["marginal_pass"]
                ).items())),
            }
        )
    require(results["marginal_by_pool"] == expected_marginal, "terminal marginal summary mismatch")
    expected_paths = []
    for pool_size in (128, 256):
        for algorithm in load_json(CONTRACT)["algorithms"]:
            rows = [row for row in paths["records"] if row["pool_size"] == pool_size and row["algorithm"] == algorithm]
            expected_paths.append(
                {
                    "pool_size": pool_size,
                    "algorithm": algorithm,
                    "required_cells": 51,
                    "actual_cells": len(rows),
                    "pass_cells": sum(row["path_pass"] for row in rows),
                    "all_station_seed_pass": len(rows) == 51 and all(row["path_pass"] for row in rows),
                    "failure_counts": dict(sorted(collections.Counter(
                        row["first_failed_criterion"] for row in rows if not row["path_pass"]
                    ).items())),
                }
            )
    require(results["path_by_global_contract"] == expected_paths, "terminal path summary mismatch")
    require(decision["results_sha256"] == sha256(RESULTS), "decision/result hash mismatch")
    require(decision["terminal_status"] == "EXECUTED-HOLD-PATH-INFEASIBILITY", "decision status mismatch")
    require(decision["decision"] == "HOLD", "decision value mismatch")


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: verify-a5d1-closure-supplement.py")
    contract = load_json(CONTRACT)
    freeze = load_json(FREEZE)
    verify_resources(contract, freeze)
    verify_manifests()
    verify_detailed_semantics(contract)
    verify_terminal_aggregates()
    print("A5d1 post-result closure supplement: PASS")
    print("resources: 4/4 ceilings; manifests: 17 libraries + 17 features")
    print("semantic replay: 34 marginals + 306 paths + terminal aggregates")


if __name__ == "__main__":
    main()
