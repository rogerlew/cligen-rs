#!/usr/bin/env python3
"""Source-bound A12R3 localizable-selector corpus evaluation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
R2_PATH = ROOT / "docs/work-packages/20260826-a12r2-localizability-repair-comparison/artifacts/evaluate.py"
R2_FEASIBILITY = ROOT / "docs/work-packages/20260826-a12r2-localizability-repair-comparison/artifacts/feasibility-evidence-v1.json"
FROZEN_PREDECESSOR = {
    "a12r2_closure_commit": "9b7fd39bf1cec21a2307c8851bc393cf538deb8c",
    "a12r2_evaluator_sha256": "cc1ec0b5474e506a98514fc8f23fcf0791ae06cc75bb2ffd932e9dd2bdebfe5d",
    "a12r2_feasibility_file_sha256": "9523b1a27d09affd755fde1c701ae6b26f7d31be883e054c78b99aee5a84d508",
    "a12r2_source_commit": "866d0401ab757708d80a58ad9dda5683f6e000bc",
}


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode().strip())
    return result.stdout


def authenticate_predecessor() -> dict[str, str]:
    relative = R2_PATH.relative_to(ROOT).as_posix()
    committed = git("show", f"{FROZEN_PREDECESSOR['a12r2_source_commit']}:{relative}")
    if (digest_bytes(committed) != FROZEN_PREDECESSOR["a12r2_evaluator_sha256"]
            or digest_bytes(R2_PATH.read_bytes()) != FROZEN_PREDECESSOR["a12r2_evaluator_sha256"]):
        raise RuntimeError("A12R2 evaluator identity differs")
    feasibility_relative = R2_FEASIBILITY.relative_to(ROOT).as_posix()
    closure_value = git("show", f"{FROZEN_PREDECESSOR['a12r2_closure_commit']}:{feasibility_relative}")
    expected = FROZEN_PREDECESSOR["a12r2_feasibility_file_sha256"]
    if digest_bytes(closure_value) != expected or digest_bytes(R2_FEASIBILITY.read_bytes()) != expected:
        raise RuntimeError("A12R2 feasibility identity differs")
    return dict(FROZEN_PREDECESSOR)


AUTHENTICATED_PREDECESSOR = authenticate_predecessor()
R2_SPEC = importlib.util.spec_from_file_location("a12r2_evaluate", R2_PATH)
if R2_SPEC is None or R2_SPEC.loader is None:
    raise RuntimeError("cannot load A12R2 evaluator")
R2 = importlib.util.module_from_spec(R2_SPEC)
sys.modules[R2_SPEC.name] = R2
R2_SPEC.loader.exec_module(R2)
BASE = R2.BASE
EvaluationError = BASE.EvaluationError

MANIFEST_PATH = PACKAGE / "evaluation-manifest-v1.json"
SCHEMA_PATH = PACKAGE / "evaluation-manifest-v1.schema.json"
SPEC_PATH = ROOT / "docs/specifications/SPEC-A12R3-LOCALIZABLE-SELECTOR-QUALITY.md"
PACKAGE_PATH = PACKAGE.parent / "package.md"
PLAN_PATH = ROOT / "docs/exec-plans/20260826-a12r3-localizable-selector-quality.md"
REVIEW_PATH = PACKAGE / "review.md"
TEST_RESULTS_PATH = PACKAGE / "test-results.md"
POLICIES = (
    "closest_localizable_v1",
    "cligen_prism_rank_sum_localizable_v1",
    "elevation_prism_reference_localizable_v1",
)
SELECTORS = ("closest", "current", "reference")
ARM = dict(zip(SELECTORS, POLICIES))
METRICS = BASE.METRICS


def validate_manifest(value: Any) -> dict[str, Any]:
    fields = {"bootstrap", "corpus", "decision", "evaluation_id", "input_hashes",
              "metrics", "policies", "predecessor", "runtime", "schema_version"}
    if not isinstance(value, dict) or set(value) != fields:
        raise EvaluationError("manifest fields differ")
    if value["schema_version"] != 1 or value["evaluation_id"] != "a12r3-localizable-selector-quality-v1":
        raise EvaluationError("manifest identity differs")
    if tuple(value["metrics"]) != METRICS or tuple(value["policies"]) != POLICIES:
        raise EvaluationError("metric or policy roster differs")
    if value["predecessor"] != AUTHENTICATED_PREDECESSOR:
        raise EvaluationError("predecessor identity differs")
    if value["runtime"] != {"python": "3.12.13", "numpy": "2.3.5"}:
        raise EvaluationError("runtime differs")
    if value["bootstrap"] != {
        "algorithm": "numpy_philox", "common_resamples": True,
        "domain": "a12r3_localizable_selector_site_median_v1",
        "quantile_method": "linear", "replicates": 10000, "seed": 1201203,
        "seed_derivation": "numpy_seedsequence_u32le_sha256_domain_plus_integer_seed",
    }:
        raise EvaluationError("bootstrap contract differs")
    if value["decision"] != {
        "family_worsening_limit_fraction": 0.05,
        "support_rule": "paired_composite_median_lt_0_and_bootstrap_upper_lt_0_and_site_win_fraction_gt_0.5_and_no_family_median_more_than_5pct_above_baseline",
        "winner_rule": "current_if_supported_and_reference_unsupported_or_current_arm_median_le_reference_else_reference_if_supported_else_closest",
    }:
        raise EvaluationError("decision contract differs")
    expected_corpus = {
        "calendar_axis_rows": 10958,
        "masked_dates": [f"{year}-12-31" for year in range(1980, 2010) if year % 4 == 0],
        "observed_rows": 10950, "period_end_inclusive": "2009-12-31",
        "period_start": "1980-01-01", "role": "fit_validation", "site_count": 240,
        "source_transform": "daymet_official_365_v1",
    }
    if value["corpus"] != expected_corpus:
        raise EvaluationError("corpus contract differs")
    BASE.verify_inputs(value)
    return value


def source_paths() -> list[Path]:
    return [
        Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_evaluate.py",
        SPEC_PATH, PACKAGE_PATH, PLAN_PATH, REVIEW_PATH, TEST_RESULTS_PATH,
        R2_PATH, R2.BASE_PATH, R2.LOCALIZE_PATH, R2.RUN_PATH,
        ROOT / "crates/cligen/src/prism/distribution.rs",
        BASE.PRISM_DISTRIBUTION, BASE.STATION_MANIFESTS, ROOT / "Cargo.lock",
        ROOT / "rust-toolchain.toml",
    ]


def verify_source(source_commit: str, require_clean: bool = False) -> dict[str, str]:
    if (len(source_commit) != 40
            or source_commit != git("rev-parse", "origin/main").decode().strip()
            or source_commit != git("rev-parse", "HEAD").decode().strip()):
        raise EvaluationError("source commit is not exact HEAD and origin/main")
    if require_clean and git("status", "--porcelain"):
        raise EvaluationError("build checkout is not clean")
    identities = {}
    for path in source_paths():
        relative = path.relative_to(ROOT).as_posix()
        current = path.read_bytes()
        if current != git("show", f"{source_commit}:{relative}"):
            raise EvaluationError(f"working source differs from commit: {relative}")
        identities[relative] = digest_bytes(current)
    return identities


def build_release(source_commit: str) -> None:
    source_hashes = verify_source(source_commit, require_clean=True)
    command = ["cargo", "build", "--release", "--locked", "--bin", "cligen"]
    subprocess.run(command, cwd=ROOT, check=True)
    binary = ROOT / "target/release/cligen"
    receipt = {
        "schema_version": "a12r3-build-receipt-1", "source_commit": source_commit,
        "source_hashes": source_hashes, "cargo_lock_sha256": BASE.digest(ROOT / "Cargo.lock"),
        "rust_toolchain_sha256": BASE.digest(ROOT / "rust-toolchain.toml"),
        "rustc_verbose": BASE.command_output("rustc", "-vV"),
        "cargo_version": BASE.command_output("cargo", "--version"), "build_command": command,
        "features": "default", "binary_path": "target/release/cligen",
        "cligen_binary_sha256": BASE.digest(binary),
    }
    BASE.atomic_json(PACKAGE / "build-receipt-v1.json", receipt)


def verify_build(source_commit: str, binary: Path, receipt_path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    source_hashes = verify_source(source_commit)
    receipt = json.loads(receipt_path.read_text())
    expected = {
        "schema_version": "a12r3-build-receipt-1", "source_commit": source_commit,
        "source_hashes": source_hashes, "cargo_lock_sha256": BASE.digest(ROOT / "Cargo.lock"),
        "rust_toolchain_sha256": BASE.digest(ROOT / "rust-toolchain.toml"),
        "rustc_verbose": BASE.command_output("rustc", "-vV"),
        "cargo_version": BASE.command_output("cargo", "--version"),
        "build_command": ["cargo", "build", "--release", "--locked", "--bin", "cligen"],
        "features": "default", "binary_path": "target/release/cligen",
        "cligen_binary_sha256": BASE.digest(binary),
    }
    if receipt != expected:
        raise EvaluationError("build receipt differs")
    return source_hashes, receipt


def arm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return R2.arm_summary(rows)


def paired_comparison(candidate: list[dict[str, Any]], baseline: list[dict[str, Any]],
                      manifest: dict[str, Any]) -> dict[str, Any]:
    return R2.paired_comparison(candidate, baseline, manifest)


def summarize(site_rows: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    by_arm = {arm: [row["policies"][arm] for row in site_rows] for arm in POLICIES}
    summaries = {arm: arm_summary(rows) for arm, rows in by_arm.items()}
    comparisons = {
        selector: paired_comparison(by_arm[ARM[selector]], by_arm[ARM["closest"]], manifest)
        for selector in ("current", "reference")
    }
    current, reference = comparisons["current"]["supported"], comparisons["reference"]["supported"]
    if current and (not reference or summaries[ARM["current"]]["median_composite"]
                    <= summaries[ARM["reference"]]["median_composite"]):
        disposition = "CURRENT_HEURISTIC_APPROPRIATE"
    elif reference:
        disposition = "ELEVATION_REFERENCE_BETTER"
    else:
        disposition = "CLOSEST_PREFERRED"
    decision = {
        "schema_version": "a12r3-station-selection-decision-1",
        "evaluation_id": manifest["evaluation_id"], "terminal": "EXECUTED-COMPLETE",
        "disposition": disposition, "runtime_default_change_authorized": False,
        "confirmation_authorized": False,
    }
    return {"arm_summaries": summaries, "comparisons_to_closest": comparisons}, decision


def paths(replay: bool, root: Path = PACKAGE) -> dict[str, Path]:
    marker = "-replay" if replay else ""
    return {
        "preflight": root / f"calendar-preflight{marker}-v1.json",
        "evidence": root / f"station-selection-evidence{marker}-v1.json",
        "decision": root / f"station-selection-decision{marker}-v1.json",
        "receipt": root / f"execution{marker}-receipt-v1.json",
    }


def execute_science(source_commit: str, binary: Path, build_receipt_path: Path,
                    station_archive: Path, replay: bool, output_root: Path) -> None:
    started = time.perf_counter()
    output = paths(replay, output_root)
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if {"python": platform.python_version(), "numpy": np.__version__} != manifest["runtime"]:
        raise EvaluationError("scientific runtime differs")
    input_hashes = BASE.verify_inputs(manifest)
    source_hashes, _ = verify_build(source_commit, binary.resolve(), build_receipt_path)
    predecessor = json.loads(R2_FEASIBILITY.read_text())
    predecessor_by_site = {row["point_id"]: row for row in predecessor["site_results"]}
    prism_identity = BASE.verify_prism_cache(BASE.cache_root())
    prism_runtime = Path(prism_identity.pop("_runtime_path"))
    with tempfile.TemporaryDirectory(prefix="cligen-a12r3-") as temporary:
        isolated = Path(temporary)
        collection_root, station_identity = BASE.extract_registered_station_archive(station_archive, isolated)
        isolated_prism = isolated / "prism" / prism_identity["bundle_id"] / prism_identity["bundle_version"]
        isolated_prism.parent.mkdir(parents=True)
        shutil.copytree(prism_runtime, isolated_prism, copy_function=shutil.copy2)
        isolated_binary = isolated / "bin/cligen"
        isolated_binary.parent.mkdir()
        shutil.copy2(binary, isolated_binary)
        rows = BASE.station_rows(collection_root)
        objects, preflight = BASE.load_fit_validation(manifest)
        preflight["schema_version"] = "a12r3-calendar-preflight-1"
        BASE.atomic_json(output["preflight"], preflight)
        par_cache: dict[Path, dict[str, Any]] = {}
        prepared_sites = []
        grid_identities = set()
        for value in objects:
            target = {key: value[key] for key in ("point_id", "latitude", "longitude", "elevation_m")}
            normals = BASE.query_normals(isolated_binary, isolated, target["latitude"], target["longitude"])
            all_arms, matrix, displacements = R2.select_arms(rows, target, normals, par_cache)
            prior = predecessor_by_site[target["point_id"]]
            if (matrix != prior["candidate_pool"] or displacements != prior["policy_displacements"]
                    or sum(row["ordinary_localizable"] for row in matrix) != prior["eligible_candidate_count"]):
                raise EvaluationError(f"A12R2 feasibility reproduction differs: {target['point_id']}")
            grid_identities.add((normals["bundle_id"], normals["bundle_version"],
                                 normals["grid_manifest_sha256"], normals["source_manifest_sha256"]))
            prepared_sites.append((value, normals, all_arms, matrix, displacements, prior))
        if len(prepared_sites) != 240 or len(predecessor_by_site) != 240 or len(grid_identities) != 1:
            raise EvaluationError("corpus or PRISM identity count differs")
        final_prism = BASE.verify_prism_cache(isolated)
        final_prism.pop("_runtime_path")
        final_count, final_tree = R2.extracted_tree_identity(collection_root)
        if (BASE.digest(isolated_binary) != BASE.digest(binary)
                or BASE.digest(station_archive) != station_identity["archive_sha256"]
                or final_count != station_identity["extracted_file_count"]
                or final_tree != station_identity["extracted_tree_sha256"]
                or final_prism != prism_identity):
            raise EvaluationError("isolated runtime input identity changed during feasibility")
        # Only after the complete 240-site/2,400-cell feasibility reproduction
        # has passed may observed descriptors be read or any quality metric computed.
        site_rows = []
        for value, normals, all_arms, matrix, displacements, prior in prepared_sites:
            observed = BASE.observed_descriptors(value)
            policy_rows = {}
            for selector in SELECTORS:
                station = all_arms[ARM[selector]]
                par = par_cache[station["path"]]
                localized = BASE.localized_parameters(par, normals)
                policy_rows[ARM[selector]] = {
                    "selected_station_id": station["id"],
                    "selected_source_par_sha256": par["sha256"],
                    "distance_km": station["distance_km"],
                    "metrics": BASE.errors(par, observed, normals, localized),
                }
            site_rows.append({
                "point_id": value["point_id"], "regime": value["regime"],
                "eligible_candidate_count": prior["eligible_candidate_count"],
                "candidate_pool_sha256": BASE.canonical_digest(matrix),
                "policy_displacements": displacements, "policies": policy_rows,
            })
    summaries, decision = summarize(site_rows, manifest)
    evidence = {
        "schema_version": "a12r3-station-selection-evidence-1",
        "evaluation_id": manifest["evaluation_id"], "source_commit": source_commit,
        "cligen_binary_sha256": BASE.digest(binary),
        "build_receipt_sha256": BASE.digest(build_receipt_path),
        "station_collection": station_identity, "prism_identity": list(next(iter(grid_identities))),
        "prism_cache_identity": prism_identity,
        "preflight_identity": {"sha256": BASE.digest(output["preflight"]),
                               "object_set_sha256": preflight["object_set_sha256"],
                               "shard_set_sha256": preflight["shard_set_sha256"]},
        "authenticated_predecessor": AUTHENTICATED_PREDECESSOR,
        "predecessor_feasibility_evidence_sha256": BASE.digest(R2_FEASIBILITY),
        "feasibility_reproduction": {"site_count": 240, "candidate_count": 2400,
                                     "exact_match": True},
        "site_count": 240, "quality_summary": summaries, "site_results": site_rows,
        "confirmation_target_series_accessed": False,
    }
    evidence["evidence_sha256"] = BASE.canonical_digest(evidence)
    BASE.atomic_json(output["evidence"], evidence)
    BASE.atomic_json(output["decision"], decision)
    receipt = {
        "schema_version": "a12r3-execution-receipt-1", "evaluation_id": manifest["evaluation_id"],
        "source_commit": source_commit, "source_hashes": source_hashes,
        "input_hashes": input_hashes, "cligen_binary_sha256": BASE.digest(binary),
        "build_receipt_sha256": BASE.digest(build_receipt_path),
        "station_archive_sha256": BASE.digest(station_archive),
        "prism_cache_file_set_sha256": prism_identity["file_set_sha256"],
        "authenticated_predecessor": AUTHENTICATED_PREDECESSOR,
        "selected_source_par_identities": {
            row["point_id"]: {
                policy: {
                    "station_id": row["policies"][policy]["selected_station_id"],
                    "source_par_sha256": row["policies"][policy]["selected_source_par_sha256"],
                } for policy in POLICIES
            } for row in site_rows
        },
        "outputs": {path.name: {"sha256": BASE.digest(path), "bytes": path.stat().st_size}
                    for path in (output["preflight"], output["evidence"], output["decision"])},
        "elapsed_seconds": time.perf_counter() - started,
        "confirmation_target_series_accessed": False,
    }
    BASE.atomic_json(output["receipt"], receipt)


def execute(source_commit: str, binary: Path, build_receipt_path: Path, station_archive: Path) -> None:
    first = paths(False)
    if not any(path.exists() for path in first.values()):
        with tempfile.TemporaryDirectory(prefix="a12r3-publish-") as temporary:
            staged_root = Path(temporary)
            execute_science(source_commit, binary, build_receipt_path, station_archive, False, staged_root)
            for name, staged in paths(False, staged_root).items():
                shutil.copy2(staged, first[name])
        return
    if not all(path.exists() for path in first.values()):
        raise EvaluationError("partial first execution artifact set")
    replay = paths(True)
    if any(path.exists() for path in replay.values()) or (PACKAGE / "replay-receipt-v1.json").exists():
        raise EvaluationError("replay artifacts already exist")
    with tempfile.TemporaryDirectory(prefix="a12r3-replay-") as temporary:
        staged_root = Path(temporary)
        execute_science(source_commit, binary, build_receipt_path, station_archive, True, staged_root)
        comparisons = {}
        for name in ("preflight", "evidence", "decision"):
            first_hash = BASE.digest(first[name])
            replay_hash = BASE.digest(paths(True, staged_root)[name])
            comparisons[name] = {"first_sha256": first_hash, "replay_sha256": replay_hash,
                                 "identical": first_hash == replay_hash}
        if not all(row["identical"] for row in comparisons.values()):
            raise EvaluationError("scientific replay differs")
        for name, staged in paths(True, staged_root).items():
            shutil.copy2(staged, replay[name])
    BASE.atomic_json(PACKAGE / "replay-receipt-v1.json", {
        "schema_version": "a12r3-replay-receipt-1", "source_commit": source_commit,
        "comparisons": comparisons, "scientific_replay_identical": True,
        "first_execution_receipt_sha256": BASE.digest(first["receipt"]),
        "replay_execution_receipt_sha256": BASE.digest(replay["receipt"]),
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-manifest", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--cligen-binary", type=Path)
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--station-archive", type=Path)
    arguments = parser.parse_args()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if arguments.validate_manifest:
        print(BASE.canonical_digest(manifest))
    elif arguments.build and arguments.source_commit:
        build_release(arguments.source_commit)
    elif (arguments.execute and arguments.source_commit and arguments.cligen_binary
          and arguments.build_receipt and arguments.station_archive):
        execute(arguments.source_commit, arguments.cligen_binary, arguments.build_receipt,
                arguments.station_archive)
    else:
        parser.error("select one complete operation")


if __name__ == "__main__":
    main()
