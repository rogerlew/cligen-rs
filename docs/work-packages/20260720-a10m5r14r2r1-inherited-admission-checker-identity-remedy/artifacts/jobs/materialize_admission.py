#!/usr/bin/env python3
"""Materialize R14R2R1 receipts with exact composed-checker projection."""

from __future__ import annotations

import datetime as dt
import importlib.util
import subprocess
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "3a9f2aedab1f7be5202a141c7d32350d7fe6f5e3"
SOURCE = PACKAGE.parent / "20260720-a10m5r14r2-shared-environment-four-l40-portfolio/artifacts/jobs/materialize_admission.py"
PACKAGE_ID = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
RUN_ID = "a10m5r14r2r1-inherited-admission-checker-identity-remedy-r0"
RECORD_TYPE = "a10m5r14r2r1-submission-admission"
ROLES = {"control-materialization", "continuous-distribution-head-factorial-portfolio"}
SLOTS = ["admission_checker.py", "inherited_admission_checker.py"]
EXPECTED_PROJECTION: dict[str, Any] | None = None
EXPECTED_AUTHORITY_ID: str | None = None


def git_bytes(relative: str) -> bytes:
    return subprocess.run(("git", "show", f"{PARENT_COMMIT}:{relative}"), cwd=REPO, check=True, capture_output=True).stdout


def verify_parent() -> None:
    if SOURCE.read_bytes() != git_bytes(SOURCE.relative_to(REPO).as_posix()):
        raise RuntimeError("R14R2 materializer differs from published parent bytes")


verify_parent()
spec = importlib.util.spec_from_file_location("r14r2_materialize_admission", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14R2 materializer")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
delegated = parent.delegated
base_verify_local_paths = delegated.verify_local_paths
delegated.PACKAGE = PACKAGE
delegated.REPO = REPO
delegated.PACKAGE_ID = PACKAGE_ID
delegated.RUN_ID = RUN_ID
delegated.REMOTE_ROOT = f"/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/{RUN_ID}"
delegated.ROLES = ROLES


def verify_published_source(source_commit: str) -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if not (source_commit == head == upstream and branch == "main" and Path(__file__).read_bytes() == subprocess.run(("git", "show", f"{source_commit}:{relative}"), cwd=REPO, check=True, capture_output=True).stdout):
        raise RuntimeError("R14R2R1 materializer is not exact published main")
    verify_parent()


def projection_from_state(state: dict) -> dict:
    plan = delegated.current_plan(state)
    contract = plan.get("admission_materialization", {}).get("checker_assets")
    if contract != {"logical_names": SLOTS, "protocol": "ordered-plan-assets-v1"}:
        raise RuntimeError("composed checker contract drift")
    assets = {item.get("logical_name"): item for item in plan.get("assets", []) if isinstance(item, dict)}
    projected = []
    for name in SLOTS:
        item = assets.get(name, {})
        identity = {key: item.get(key) for key in ("bytes", "sha256")}
        if not (isinstance(identity["bytes"], int) and identity["bytes"] > 0 and isinstance(identity["sha256"], str) and len(identity["sha256"]) == 64):
            raise RuntimeError(f"malformed checker plan identity: {name}")
        projected.append({"logical_name": name, **identity})
    return {"assets": projected, "protocol": "ordered-plan-assets-v1"}


def verify_local_paths(state_path: Path, publication_dir: Path, source_commit: str) -> dict:
    global EXPECTED_AUTHORITY_ID, EXPECTED_PROJECTION
    state = base_verify_local_paths(state_path, publication_dir, source_commit)
    EXPECTED_PROJECTION = projection_from_state(state)
    EXPECTED_AUTHORITY_ID = state.get("authority_id")
    if not isinstance(EXPECTED_AUTHORITY_ID, str) or not EXPECTED_AUTHORITY_ID:
        raise RuntimeError("fresh authority identity missing from toolkit state")
    return state


def fetch_and_verify(target: Path, *, role: str, state_sha256: str, source_commit: str) -> dict[str, Any]:
    delegated.run(["scp", "-oBatchMode=yes", f"{delegated.REMOTE_HOST}:{delegated.REMOTE_ROOT}/admissions/{role}.json", str(target)])
    receipt = delegated.read(target)
    occupancy_fresh = True
    if role == "continuous-distribution-head-factorial-portfolio":
        try:
            captured_at = dt.datetime.fromisoformat(receipt["occupancy_captured_at"].replace("Z", "+00:00"))
            age = (dt.datetime.now(dt.timezone.utc) - captured_at).total_seconds()
            occupancy_fresh = 0 <= age <= 60 and receipt.get("occupancy_node") == "node03"
        except (KeyError, AttributeError, TypeError, ValueError):
            occupancy_fresh = False
    if not (
        EXPECTED_PROJECTION is not None
        and EXPECTED_AUTHORITY_ID is not None
        and delegated.authenticated(receipt)
        and receipt.get("schema_version") == "lemhi-toolkit-record-2"
        and receipt.get("record_type") == RECORD_TYPE
        and receipt.get("package_id") == PACKAGE_ID
        and receipt.get("authority_id") == EXPECTED_AUTHORITY_ID
        and receipt.get("run_id") == RUN_ID
        and receipt.get("role") == role
        and receipt.get("attempt_index") == 0
        and receipt.get("source_commit") == source_commit
        and receipt.get("decision") == "PASS"
        and receipt.get("valid") is True
        and occupancy_fresh
        and receipt.get("input_identities", {}).get("toolkit_state_sha256") == state_sha256
        and receipt.get("input_identities", {}).get("checker_assets") == EXPECTED_PROJECTION
        and isinstance(receipt.get("gates"), dict)
        and receipt["gates"]
        and all(value is True for value in receipt["gates"].values())
    ):
        raise RuntimeError("materialized R14R2R1 admission receipt failed authentication")
    return receipt


delegated.verify_published_source = verify_published_source
delegated.verify_local_paths = verify_local_paths
delegated.fetch_and_verify = fetch_and_verify


if __name__ == "__main__":
    delegated.main()
