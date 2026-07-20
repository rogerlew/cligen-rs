#!/usr/bin/env python3
"""Authenticate R14R2R1 portfolio evidence and run the inherited selector twice."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

PACKAGE_ID = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
RUN_ID = "a10m5r14r2r1-inherited-admission-checker-identity-remedy-r0"
PORTFOLIO_ROLE = "continuous-distribution-head-factorial-portfolio"
PARAMETER_COUNTS = {
    "centered_location_ou": (1740, 278667),
    "centered_location_ou_smooth_climatology": (1820, 278747),
    "centered_location_and_scale_ou": (2892, 279819),
    "centered_location_and_scale_ou_smooth_climatology": (2972, 279899),
}
PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PARENT = (
    PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial"
    / "artifacts/run_temporal_replay.py"
)


def simple_canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def simple_authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return recorded == hashlib.sha256(simple_canonical(semantic)).hexdigest()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def option(name: str) -> Path:
    try:
        return Path(sys.argv[sys.argv.index(name) + 1])
    except (ValueError, IndexError) as error:
        raise RuntimeError(f"missing replay option: {name}") from error


spec = importlib.util.spec_from_file_location("r14_temporal_replay", PARENT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited R14 replay")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID


def verify_portfolio_records(evidence_root: Path, plan: dict, collection: dict) -> dict:
    manifest_path = option("--asset-root") / "asset-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    role_map_path = option("--asset-root") / "portfolio-role-map.json"
    role_map_identity = {"bytes": role_map_path.stat().st_size, "sha256": digest(role_map_path)}
    if role_map_identity != {
        key: manifest.get("assets", {}).get("portfolio-role-map.json", {}).get(key)
        for key in ("bytes", "sha256")
    }:
        raise RuntimeError("replay role-map asset identity drift")
    role_map = json.loads(role_map_path.read_text())
    rows = role_map.get("processes", [])
    publication = {
        "asset_manifest_sha256": digest(manifest_path),
        "run_id": RUN_ID,
        "source_commit": plan.get("source_commit"),
    }
    required = {
        f"admissions/{row['role']}.json" for row in rows
    } | {
        f"admissions/{PORTFOLIO_ROLE}.json",
        f"results/{PORTFOLIO_ROLE}/evidence.json",
        f"results/{PORTFOLIO_ROLE}/launcher.json",
        *(f"results/{row['role']}/process.json" for row in rows),
        *(f"results/{row['role']}/evidence.json" for row in rows),
        *(f"results/{row['role']}/training.json" for row in rows),
        *(f"results/{row['role']}/streams.npz" for row in rows),
    }
    allowlist = set(plan.get("evidence_allowlist", []))
    present = set(collection.get("present", []))
    if len(rows) != 4 or not required <= allowlist or not required <= present:
        raise RuntimeError("R14R2R1 portfolio evidence roster incomplete")
    identities = {}
    portfolio = json.loads((evidence_root / f"results/{PORTFOLIO_ROLE}/evidence.json").read_text())
    launcher = json.loads((evidence_root / f"results/{PORTFOLIO_ROLE}/launcher.json").read_text())
    submission = json.loads(
        (evidence_root / f"admissions/{PORTFOLIO_ROLE}.json").read_text()
    )
    checker_names = ["admission_checker.py", "inherited_admission_checker.py"]
    checker_projection = {
        "assets": [
            {
                "logical_name": name,
                **{
                    key: manifest.get("assets", {}).get(name, {}).get(key)
                    for key in ("bytes", "sha256")
                },
            }
            for name in checker_names
        ],
        "protocol": "ordered-plan-assets-v1",
    }
    submission_sha256 = launcher.get("publication_identity", {}).get(
        "submission_admission_record_sha256"
    )
    allocation_tokens = launcher.get("allocation_tokens", [])
    launcher_children = launcher.get("children", [])
    launcher_devices = launcher.get("devices", [])
    if not (
        simple_authenticated(portfolio)
        and simple_authenticated(launcher)
        and simple_authenticated(submission)
        and submission.get("record_type")
        == "a10m5r14r2r1-submission-admission"
        and submission.get("package_id") == PACKAGE_ID
        and submission.get("run_id") == RUN_ID
        and submission.get("source_commit") == publication["source_commit"]
        and submission.get("role") == PORTFOLIO_ROLE
        and submission.get("decision") == "PASS"
        and submission.get("valid") is True
        and isinstance(submission.get("gates"), dict)
        and bool(submission["gates"])
        and all(value is True for value in submission["gates"].values())
        and submission.get("input_identities", {}).get("checker_assets")
        == checker_projection
        and portfolio.get("role") == PORTFOLIO_ROLE
        and portfolio.get("exit_code") == 0
        and portfolio.get("valid") is True
        and portfolio.get("verdict") == "PASS"
        and portfolio.get("protected_roles_opened") == []
        and isinstance(portfolio.get("gates"), dict)
        and bool(portfolio["gates"])
        and all(value is True for value in portfolio["gates"].values())
        and portfolio.get("asset_manifest_sha256")
        == publication["asset_manifest_sha256"]
        and portfolio.get("run_id") == RUN_ID
        and portfolio.get("source_commit") == publication["source_commit"]
        and portfolio.get("submission_admission_record_sha256") == submission_sha256
        and launcher.get("role") == PORTFOLIO_ROLE
        and launcher.get("valid") is True
        and launcher.get("protected_roles_opened") == []
        and isinstance(launcher.get("gates"), dict)
        and bool(launcher["gates"])
        and all(value is True for value in launcher["gates"].values())
        and launcher.get("role_map_identity") == role_map_identity
        and all(
            launcher.get("publication_identity", {}).get(key) == value
            for key, value in publication.items()
        )
        and isinstance(submission_sha256, str)
        and len(submission_sha256) == 64
        and submission.get("record_sha256") == submission_sha256
        and len(allocation_tokens) == 4
        and len(set(allocation_tokens)) == 4
        and len(launcher_children) == 4
        and [(child.get("role"), child.get("slot"), child.get("exit_code")) for child in launcher_children]
        == [(row["role"], row["slot"], 0) for row in rows]
        and len(launcher_devices) == 4
        and [device.get("index") for device in launcher_devices] == [0, 1, 2, 3]
        and all(device.get("name") == "NVIDIA L40" for device in launcher_devices)
    ):
        raise RuntimeError("R14R2R1 portfolio operational evidence authentication failed")
    for row in rows:
        root = evidence_root / "results" / row["role"]
        process = json.loads((root / "process.json").read_text())
        evidence = json.loads((root / "evidence.json").read_text())
        training = json.loads((root / "training.json").read_text())
        child_admission = json.loads(
            (evidence_root / "admissions" / f"{row['role']}.json").read_text()
        )
        adapter_count, total_count = PARAMETER_COUNTS[row["candidate"]]
        training_rows = training.get("seeds", [])
        if not (
            simple_authenticated(process)
            and simple_authenticated(evidence)
            and simple_authenticated(training)
            and simple_authenticated(child_admission)
            and process.get("valid") is True
            and process.get("exit_code") == 0
            and process.get("protected_roles_opened") == []
            and isinstance(process.get("gates"), dict)
            and bool(process["gates"])
            and all(value is True for value in process["gates"].values())
            and process.get("role") == row["role"]
            and process.get("slot") == row["slot"]
            and process.get("candidate") == row["candidate"]
            and process.get("capacity") == row["capacity"]
            and process.get("allocation_token") == allocation_tokens[row["slot"]]
            and process.get("device_name") == "NVIDIA L40"
            and process.get("training_record_sha256")
            == training.get("record_sha256")
            and all(process.get(key) == value for key, value in publication.items())
            and process.get("submission_admission_record_sha256")
            == submission_sha256
            and evidence.get("valid") is True
            and evidence.get("verdict") == "PASS"
            and evidence.get("exit_code") == 0
            and isinstance(evidence.get("gates"), dict)
            and bool(evidence["gates"])
            and all(value is True for value in evidence["gates"].values())
            and evidence.get("role") == row["role"]
            and evidence.get("slot") == row["slot"]
            and evidence.get("candidate_id") == row["candidate"]
            and evidence.get("capacity_id") == row["capacity"]
            and evidence.get("protected_roles_opened") == []
            and all(evidence.get(key) == value for key, value in publication.items())
            and evidence.get("submission_admission_record_sha256")
            == submission_sha256
            and child_admission.get("record_type")
            == "a10m5r14r2r1-submission-admission"
            and child_admission.get("package_id") == PACKAGE_ID
            and child_admission.get("run_id") == RUN_ID
            and child_admission.get("source_commit") == publication["source_commit"]
            and child_admission.get("role") == row["role"]
            and child_admission.get("attempt_index") == 0
            and child_admission.get("asset_manifest_sha256")
            == publication["asset_manifest_sha256"]
            and child_admission.get("decision") == "PASS"
            and child_admission.get("valid") is True
            and isinstance(child_admission.get("gates"), dict)
            and bool(child_admission["gates"])
            and all(value is True for value in child_admission["gates"].values())
            and child_admission.get("input_identities", {}).get(
                "parent_portfolio_admission_record_sha256"
            )
            == submission_sha256
            and child_admission.get("input_identities", {}).get(
                "portfolio_launcher_record_sha256"
            )
            == launcher.get("record_sha256")
            and training.get("architecture") == row["candidate"]
            and training.get("capacity") == row["capacity"]
            and isinstance(training_rows, list)
            and bool(training_rows)
            and all(
                seed.get("parameter_count") == adapter_count
                and seed.get("candidate_adapter_parameter_count") == adapter_count
                and seed.get("total_parameter_count") == total_count
                and seed.get("parameter_accounting_interface")
                == "adapter-only-parameter_count-plus-explicit-total"
                for seed in training_rows
            )
            and evidence.get("training_record_sha256")
            == training.get("record_sha256")
        ):
            raise RuntimeError(f"R14R2R1 child evidence authentication failed: {row['role']}")
        identities[row["role"]] = {
            "admission_record_sha256": child_admission["record_sha256"],
            "evidence_record_sha256": evidence["record_sha256"],
            "process_record_sha256": process["record_sha256"],
            "streams_sha256": digest(root / "streams.npz"),
            "training_record_sha256": training["record_sha256"],
        }
    identities[PORTFOLIO_ROLE] = {
        "evidence_record_sha256": portfolio["record_sha256"],
        "launcher_record_sha256": launcher["record_sha256"],
        "role_map": role_map_identity,
    }
    return identities


def main() -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if subprocess.run(("git", "show", f"{head}:{relative}"), cwd=REPO, check=True, capture_output=True).stdout != Path(__file__).read_bytes():
        raise RuntimeError("R14R2R1 replay differs from published source")
    raw = parent.read_toolkit_object(option("--semantic-plan"))
    receipt = parent.read_toolkit_object(option("--plan-receipt"))
    collection = parent.read_toolkit_object(option("--collection"))
    plan = parent.authenticate_plan(raw, receipt, head)
    if not (
        parent.authenticated(collection)
        and collection.get("package_id") == PACKAGE_ID
        and collection.get("run_id") == RUN_ID
        and collection.get("source_commit") == head
        and collection.get("plan_id") == receipt.get("plan_id")
        and collection.get("remote_cleanup_performed") is not True
    ):
        raise RuntimeError("R14R2R1 collection authentication failed before replay")
    identities = verify_portfolio_records(option("--evidence-root"), plan, collection)
    parent.main()
    replay_path = option("--output-root") / "replay-identity.json"
    replay = json.loads(replay_path.read_text())
    if replay.get("package_id") != PACKAGE_ID or replay.get("run_id") != RUN_ID:
        raise RuntimeError("inherited replay identity was not rebound to R14R2")
    replay["record_type"] = "a10m5r14r2r1-precleanup-replay"
    replay["portfolio_evidence"] = identities
    replay.pop("record_sha256", None)
    replay["record_sha256"] = hashlib.sha256(parent.canonical(replay)).hexdigest()
    temporary = replay_path.with_suffix(".json.promote")
    temporary.write_text(json.dumps(replay, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, replay_path)


if __name__ == "__main__":
    main()
