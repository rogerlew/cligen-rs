#!/usr/bin/env python3
"""Authenticate R2 evidence, replay twice, and apply rev-2 selection."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from rev2_selector import digest, extract_observations, run_selector


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
RUN_ID = "a10m5r15r2-external-normal-conditioning-execution-r0"
PORTFOLIO_ROLE = "external-normal-conditioning-portfolio"
BASE_SOURCE = (
    PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial"
    / "artifacts/run_temporal_replay.py"
)
PARAMETER_COUNTS = {
    "centered_location_ou_smooth_climatology": (1820, 278747),
    "normal_conditioned_smooth_climatology": (2540, 279467),
    "descriptor_anchored_residual": (2040, 2040),
    "normal_anchored_residual": (2760, 2760),
}
PAIRINGS = {
    "normal_conditioned_smooth_climatology-k2": "centered_location_ou_smooth_climatology-k2",
    "normal_anchored_residual-v1": "descriptor_anchored_residual-v1",
}
CONFIGURATION_CANDIDATES = {
    "centered_location_ou_smooth_climatology-k2": "centered_location_ou_smooth_climatology",
    "normal_conditioned_smooth_climatology-k2": "normal_conditioned_smooth_climatology",
    "descriptor_anchored_residual-v1": "descriptor_anchored_residual",
    "normal_anchored_residual-v1": "normal_anchored_residual",
}
TERMINALS = {
    "FAIL-A10M5R15-INVALID-EVIDENCE",
    "HOLD-A10M5R15-ENGINEERING-INCOMPLETE",
    "HOLD-A10M5R15-RUNTIME-INELIGIBLE",
    "HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED",
    "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT",
    "A10M5R15-TEMPORAL-READY",
}


spec = importlib.util.spec_from_file_location("r15r2_replay_base", BASE_SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated replay base")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.PACKAGE_ID = PACKAGE_ID
base.RUN_ID = RUN_ID


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    payload = json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return isinstance(recorded, str) and recorded == hashlib.sha256(payload).hexdigest()


def require_published(path: Path, head: str) -> None:
    relative = path.relative_to(REPO).as_posix()
    payload = subprocess.run(
        ("git", "show", f"{head}:{relative}"), cwd=REPO, check=True, capture_output=True
    ).stdout
    if payload != path.read_bytes():
        raise RuntimeError(f"replay source differs from published main: {path.name}")


def verify_collection(options, head: str) -> tuple[dict, dict, dict]:
    raw = base.read_toolkit_object(options.semantic_plan)
    receipt = base.read_toolkit_object(options.plan_receipt)
    collection = base.read_toolkit_object(options.collection)
    plan = base.authenticate_plan(raw, receipt, head)
    if not (
        base.authenticated(collection)
        and collection.get("package_id") == PACKAGE_ID
        and collection.get("run_id") == RUN_ID
        and collection.get("source_commit") == head
        and collection.get("plan_id") == receipt.get("plan_id")
        and collection.get("download_promoted") is True
        and collection.get("remote_cleanup_performed") is not True
    ):
        raise RuntimeError("collection/plan authentication failed")
    allowlist = set(plan["evidence_allowlist"])
    present = set(collection.get("present", []))
    rows = collection.get("sanitized_files", [])
    if {row["logical_name"] for row in rows} != present:
        raise RuntimeError("collection identity roster drift")
    for row in rows:
        logical = row["logical_name"]
        path = options.evidence_root / logical
        if logical not in allowlist or path.is_symlink() or not path.is_file():
            raise RuntimeError(f"collected evidence outside allowlist: {logical}")
        if {"bytes": path.stat().st_size, "sha256": digest(path)} != {
            "bytes": row["bytes"], "sha256": row["sha256"]
        }:
            raise RuntimeError(f"collected evidence identity drift: {logical}")
    return plan, receipt, collection


def verify_provenance(
    options, manifest: dict, plan: dict, runtime: dict, execution: dict
) -> tuple[dict, list[dict]]:
    role_map_path = options.asset_root / "portfolio-role-map.json"
    role_map = json.loads(role_map_path.read_text(encoding="utf-8"))
    if {"bytes": role_map_path.stat().st_size, "sha256": digest(role_map_path)} != {
        key: manifest["assets"]["portfolio-role-map.json"][key] for key in ("bytes", "sha256")
    }:
        raise RuntimeError("role-map identity drift")
    closures = []
    arm_by_candidate = {row["candidate"]: row for row in execution["arms"]}
    for process in role_map["processes"]:
        root = options.evidence_root / "results" / process["role"]
        training = json.loads((root / "training.json").read_text(encoding="utf-8"))
        streams = json.loads((root / "streams.json").read_text(encoding="utf-8"))
        expected_adapter, expected_total = PARAMETER_COUNTS[process["candidate"]]
        if not (
            training.get("architecture") == process["candidate"]
            and len(training.get("seeds", [])) == 3
            and streams.get("architecture") == process["candidate"]
            and streams.get("stream_count") == 144
            and len(streams.get("streams", [])) == 144
        ):
            raise RuntimeError(f"candidate evidence roster drift: {process['role']}")
        conditioned = process["candidate"] in {
            "normal_conditioned_smooth_climatology", "normal_anchored_residual"
        }
        arm = arm_by_candidate[process["candidate"]]
        final_runtime = runtime["arms"][process["candidate"]]["classification"]

        def verified_provenance(provenance: dict, seed: int) -> dict:
            expected_normals = execution["conditioning"] if conditioned else None
            mapping = provenance.get("mapping_sha256")
            if not (
                provenance.get("model")
                == {"arm": arm["arm"], "candidate": arm["candidate"], "role": arm["role"]}
                and provenance.get("seed") == seed
                and provenance.get("normals_bundle") == expected_normals
                and provenance.get("normals_excluded") is (not conditioned)
                and isinstance(provenance.get("normals_window_limitation"), str)
                and bool(provenance["normals_window_limitation"])
                and provenance.get("calendar", {}).get("profile_id") == "daymet_official_365_v1"
                and isinstance(provenance.get("calendar", {}).get("preflight_sha256"), str)
                and len(provenance["calendar"]["preflight_sha256"]) == 64
                and provenance.get("corpus") == execution["corpus"]
                and provenance.get("runtime_classification")
                == "PENDING-NORMATIVE-ADR-0006-BENCHMARK"
                and ((isinstance(mapping, str) and len(mapping) == 64) if conditioned else mapping is None)
            ):
                raise RuntimeError(f"rev2 provenance drift: {process['role']}/{seed}")
            closed = dict(provenance)
            closed["provisional_runtime_classification"] = closed.pop(
                "runtime_classification"
            )
            closed["runtime_classification"] = final_runtime
            return closed

        mapping_hashes = set()
        checkpoint_rows = []
        evaluation_rows = []
        for row in training["seeds"]:
            provenance = row.get("provenance", {})
            closed = verified_provenance(provenance, row["seed"])
            mapping_hashes.add(provenance.get("mapping_sha256"))
            checkpoint_path = root / "seed-work" / str(row["seed"]) / "checkpoint.pt"
            seed_path = root / "seeds" / f"{row['seed']}.json"
            seed_record = json.loads(seed_path.read_text(encoding="utf-8"))
            if not (
                row.get("parameter_count") == expected_adapter
                and row.get("candidate_adapter_parameter_count") == expected_adapter
                and row.get("total_parameter_count") == expected_total
                and row.get("parameter_accounting_interface")
                == "adapter-only-parameter_count-plus-explicit-total"
                and digest(checkpoint_path) == row.get("checkpoint_sha256")
                and seed_record.get("provenance") == provenance
                and (
                    isinstance(row.get("portable_control_export_sha256"), str)
                    if arm["uses_p2"]
                    else row.get("portable_control_export_sha256") is None
                )
            ):
                raise RuntimeError(f"checkpoint provenance drift: {process['role']}")
            if arm["uses_p2"]:
                export = root / "seed-work" / str(row["seed"]) / "control-export.pt"
                if digest(export) != row["portable_control_export_sha256"]:
                    raise RuntimeError(f"portable control export drift: {process['role']}")
            checkpoint_rows.append(
                {
                    "checkpoint_sha256": row["checkpoint_sha256"],
                    "provenance": closed,
                    "seed": row["seed"],
                }
            )
            evaluation_rows.append(
                {
                    "evaluation_record_sha256": digest(seed_path),
                    "provenance": closed,
                    "seed": row["seed"],
                }
            )
        if conditioned and (None in mapping_hashes or any(len(value) != 64 for value in mapping_hashes)):
            raise RuntimeError(f"conditioned mapping hash absent: {process['role']}")
        stream_closure = []
        for row in streams["streams"]:
            closed = verified_provenance(row.get("provenance", {}), row["training_seed"])
            if not isinstance(row.get("stream_sha256"), str) or len(row["stream_sha256"]) != 64:
                raise RuntimeError(f"stream identity drift: {process['role']}")
            stream_closure.append(
                {
                    "member_id": row["member_id"],
                    "point_id": row["point_id"],
                    "provenance": closed,
                    "stream_sha256": row["stream_sha256"],
                    "training_seed": row["training_seed"],
                }
            )
        closures.append(
            {
                "candidate": process["candidate"],
                "checkpoints": checkpoint_rows,
                "checkpoint_mapping_sha256": sorted(value for value in mapping_hashes if value),
                "evaluations": evaluation_rows,
                "role": process["role"],
                "stream_count": streams["stream_count"],
                "streams": stream_closure,
                "streams_json_sha256": digest(root / "streams.json"),
                "training_json_sha256": digest(root / "training.json"),
            }
        )
    return role_map, closures


def terminal_for(result: dict, attribution: dict, runtime: dict) -> str:
    runtime_valid = {
        treatment: (
            runtime["arms"][CONFIGURATION_CANDIDATES[treatment]]["classification"] != "FAIL"
            and runtime["arms"][CONFIGURATION_CANDIDATES[control]]["classification"] != "FAIL"
        )
        for treatment, control in PAIRINGS.items()
    }
    temporal = {
        treatment: bool(result["candidate_decisions"][treatment]["temporally_eligible"])
        for treatment in PAIRINGS
    }
    full = {
        treatment: runtime_valid[treatment] and temporal[treatment] and attribution[treatment]["passes"]
        for treatment in PAIRINGS
    }
    if not any(runtime_valid.values()):
        return "HOLD-A10M5R15-RUNTIME-INELIGIBLE"
    if any(runtime_valid[t] and temporal[t] for t in PAIRINGS) and not any(full.values()):
        return "HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED"
    if not any(runtime_valid[t] and temporal[t] for t in PAIRINGS):
        return "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT"
    return "A10M5R15-TEMPORAL-READY"


def verify_analysis_receipts(options, manifest: dict, head: str) -> tuple[dict, dict]:
    calibration = json.loads(options.calibration_receipt.read_text(encoding="utf-8"))
    runtime = json.loads(options.runtime_receipt.read_text(encoding="utf-8"))
    manifest_sha256 = digest(options.asset_root / "asset-manifest.json")
    calibration_identity = {
        "bytes": options.calibration_receipt.stat().st_size,
        "sha256": digest(options.calibration_receipt),
    }
    calibration_commit = calibration.get("source_commit", "")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", calibration_commit, head),
        cwd=REPO,
        check=False,
    ).returncode == 0
    if not (
        authenticated(calibration)
        and calibration_identity
        == {key: manifest["assets"]["attribution-calibration.json"][key] for key in ("bytes", "sha256")}
        and calibration.get("package_id") == PACKAGE_ID
        and calibration.get("valid") is True
        and calibration.get("candidate_output_accessed") is False
        and calibration.get("protected_roles_opened") == []
        and calibration.get("asset_manifest_sha256")
        == "7988efbb342045f0df5ce05ddb810cc36c8be46f145f4c0bc531d02c56291c05"
        and calibration.get("calibration_source_commit")
        == "719d83451ddff698b280219708f7648ff73c8f9d"
        and calibration.get("calibration_stream_sha256")
        == "2bb8379f639712dc864308510bd2a8c10ac9c39ea3cae609abdc2a2bf51384ff"
        and calibration.get("sequence_seeds") == [410542, 410543]
        and calibration.get("replicates") == 1000
        and calibration.get("nearest_rank_zero_based_index") == 899
        and isinstance(calibration.get("gates"), dict)
        and calibration["gates"]
        and all(calibration["gates"].values())
        and math.isfinite(calibration.get("margin", math.nan))
        and calibration["margin"] > 0
        and ancestor
    ):
        raise RuntimeError("attribution calibration receipt authentication failed")
    binary_identity = {"bytes": options.binary.stat().st_size, "sha256": digest(options.binary)}
    if not (
        authenticated(runtime)
        and runtime.get("package_id") == PACKAGE_ID
        and runtime.get("source_commit") == head
        and runtime.get("asset_manifest_sha256") == manifest_sha256
        and runtime.get("binary") == binary_identity
        and runtime.get("runtime_rule") == {"pass_below": 5.0, "warn_below": 30.0}
        and runtime.get("protected_roles_opened") == []
        and runtime.get("valid") is True
        and isinstance(runtime.get("gates"), dict)
        and runtime["gates"]
        and all(runtime["gates"].values())
        and len(runtime.get("rows", [])) == 48
        and all(row.get("complete") is True for row in runtime["rows"])
        and set(runtime.get("arms", {})) == set(PARAMETER_COUNTS)
        and all(
            row.get("classification") in {"PASS", "WARN", "FAIL"}
            and math.isfinite(row.get("worst_ratio", math.nan))
            for row in runtime["arms"].values()
        )
    ):
        raise RuntimeError("ADR-0006 runtime receipt authentication failed")
    return calibration, runtime


def non_gating_diagnostics(options, runtime: dict) -> dict:
    aligned = __import__("importlib.util").util.spec_from_file_location(
        "r15r2_aligned_diagnostics", options.asset_root / "aligned_objective.py"
    )
    if aligned is None or aligned.loader is None:
        raise RuntimeError("cannot load dispersion family registry")
    module = __import__("importlib.util").util.module_from_spec(aligned)
    aligned.loader.exec_module(module)
    roles = {
        "E2C": "e2c-descriptor-anchored-residual-v1",
        "E2": "e2-normal-anchored-residual-v1",
    }
    dispersion = {}
    for arm, role in roles.items():
        values = []
        for seed in (147031, 271828, 314159):
            record = json.loads(
                (options.evidence_root / "results" / role / "seeds" / f"{seed}.json").read_text(
                    encoding="utf-8"
                )
            )
            scores = record["candidate"]["block_scores"]
            selected = [
                float(value)
                for name, value in scores.items()
                if module.family_name(name)
                in {"monthly_interannual_dispersion", "annual_interannual_dispersion"}
            ]
            if not selected or not all(math.isfinite(value) for value in selected):
                raise RuntimeError("replacement dispersion diagnostic incomplete")
            values.append(float(np.mean(selected)))
        dispersion[arm] = float(np.median(values))
    runtime_rows = runtime["rows"]
    e2_seconds = sum(
        row["candidate_median_seconds"]
        for row in runtime_rows
        if row["candidate"] == "normal_anchored_residual"
    )
    e1_seconds = sum(
        row["candidate_median_seconds"]
        for row in runtime_rows
        if row["candidate"] == "normal_conditioned_smooth_climatology"
    )
    if min(dispersion.values()) <= 0 or e1_seconds <= 0:
        raise RuntimeError("non-gating diagnostic denominator invalid")
    return {
        "e2_over_e1_warm_runtime_ratio": e2_seconds / e1_seconds,
        "e2_over_e2c_combined_monthly_and_annual_interannual_dispersion_ratio": (
            dispersion["E2"] / dispersion["E2C"]
        ),
        "replacement_dispersion_components": dispersion,
        "selection_gating": False,
    }


def execute() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--semantic-plan", type=Path, required=True)
    parser.add_argument("--plan-receipt", type=Path, required=True)
    parser.add_argument("--calibration-receipt", type=Path, required=True)
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()
    if options.output_root.exists():
        raise RuntimeError("fresh replay output required")
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    require_published(Path(__file__).resolve(), head)
    require_published(PACKAGE / "artifacts/rev2_selector.py", head)
    if head != upstream:
        raise RuntimeError("replay requires exact published main")
    manifest = json.loads((options.asset_root / "asset-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("source_commit") != head or manifest.get("package_id") != PACKAGE_ID:
        raise RuntimeError("asset publication identity drift")
    if {"bytes": options.corpus.stat().st_size, "sha256": digest(options.corpus)} != manifest["assets"]["corpus.tar"]:
        raise RuntimeError("corpus identity drift")
    plan, plan_receipt, collection = verify_collection(options, head)
    calibration, runtime = verify_analysis_receipts(options, manifest, head)
    execution = json.loads((options.asset_root / "execution-contract.json").read_text(encoding="utf-8"))
    _, provenance_closure = verify_provenance(
        options, manifest, plan, runtime, execution
    )
    options.output_root.mkdir(mode=0o700)
    observations = options.output_root / "observations"
    sites = json.loads((options.asset_root / "sites.json").read_text(encoding="utf-8"))["sites"]
    extract_observations(options.corpus, observations, sites)
    try:
        first, first_sequences = run_selector(
            asset_root=options.asset_root, binary=options.binary, data_root=options.data_root,
            evidence_root=options.evidence_root, observations=observations,
            output_root=options.output_root / "pass-a", bootstrap_seed=410542,
        )
        second, second_sequences = run_selector(
            asset_root=options.asset_root, binary=options.binary, data_root=options.data_root,
            evidence_root=options.evidence_root, observations=observations,
            output_root=options.output_root / "pass-b", bootstrap_seed=410542,
        )
        first_bytes = (options.output_root / "pass-a/temporal-result.json").read_bytes()
        second_bytes = (options.output_root / "pass-b/temporal-result.json").read_bytes()
        if first_bytes != second_bytes or first_sequences != second_sequences:
            raise RuntimeError("selector replays differ")
        attribution = {}
        for treatment, control in PAIRINGS.items():
            treatment_u90 = float(np.quantile(first_sequences[treatment], 0.90))
            control_u90 = float(np.quantile(first_sequences[control], 0.90))
            if not all(math.isfinite(value) and value > 0 for value in (treatment_u90, control_u90)):
                raise RuntimeError("non-finite attribution input")
            gain = 1.0 - treatment_u90 / control_u90
            attribution[treatment] = {
                "bootstrap_seed": 410542,
                "control": control,
                "control_u90": control_u90,
                "gain": gain,
                "margin": calibration["margin"],
                "passes": gain >= calibration["margin"],
                "treatment_u90": treatment_u90,
            }
        result = dict(first)
        result["attribution"] = attribution
        result["runtime"] = runtime["arms"]
        result["non_gating_diagnostics"] = non_gating_diagnostics(options, runtime)
        result["selector_replays_byte_identical"] = True
        result["terminal"] = terminal_for(result, attribution, runtime)
        if result["terminal"] not in TERMINALS:
            raise RuntimeError("terminal precedence failure")
        result_path = options.output_root / "temporal-result.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        closure = {
            "arms": [
                {**row, "runtime_classification": runtime["arms"][row["candidate"]]["classification"]}
                for row in provenance_closure
            ],
            "calendar_profile_id": "daymet_official_365_v1",
            "package_id": PACKAGE_ID,
            "protected_roles_opened": [],
            "runtime_receipt_sha256": digest(options.runtime_receipt),
            "schema_version": 1,
            "valid": True,
        }
        (options.output_root / "provenance-closure.json").write_text(
            json.dumps(closure, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        replay = {
            "asset_manifest_sha256": digest(options.asset_root / "asset-manifest.json"),
            "attribution_calibration_receipt_sha256": digest(options.calibration_receipt),
            "byte_identical_passes": True,
            "collection_record_sha256": collection["record_sha256"],
            "package_id": PACKAGE_ID,
            "plan_id": collection["plan_id"],
            "plan_receipt_record_sha256": plan_receipt["record_sha256"],
            "protected_roles_opened": [],
            "provenance_closure_sha256": digest(options.output_root / "provenance-closure.json"),
            "record_type": "a10m5r15r2-precleanup-replay",
            "run_id": RUN_ID,
            "runtime_receipt_sha256": digest(options.runtime_receipt),
            "source_commit": head,
            "temporal_result_sha256": digest(result_path),
            "terminal": result["terminal"],
        }
        replay["record_sha256"] = hashlib.sha256(
            json.dumps(replay, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        (options.output_root / "replay-identity.json").write_text(
            json.dumps(replay, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(result["terminal"])
    except BaseException:
        shutil.rmtree(options.output_root, ignore_errors=True)
        raise


def main() -> None:
    try:
        execute()
    except SystemExit:
        raise
    except BaseException as error:
        try:
            index = sys.argv.index("--output-root")
            output_root = Path(sys.argv[index + 1])
        except (ValueError, IndexError):
            raise
        output_root.mkdir(parents=True, exist_ok=True)
        terminal = (
            "HOLD-A10M5R15-ENGINEERING-INCOMPLETE"
            if isinstance(error, (FileNotFoundError, subprocess.CalledProcessError))
            else "FAIL-A10M5R15-INVALID-EVIDENCE"
        )
        record = {
            "error": {"message": str(error), "type": type(error).__name__},
            "package_id": PACKAGE_ID,
            "protected_roles_opened": [],
            "record_type": "a10m5r15r2-terminal-failure",
            "run_id": RUN_ID,
            "terminal": terminal,
            "valid": False,
        }
        record["record_sha256"] = hashlib.sha256(
            json.dumps(record, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        (output_root / "terminal-failure.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(terminal)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
