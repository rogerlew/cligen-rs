#!/usr/bin/env python3
"""Materialize R14R2 admissions through the authenticated R14R1 wrapper."""

from __future__ import annotations

import importlib.util
import datetime as dt
import subprocess
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "bbb3075109ce06dabda13d43862cd94d375225bd"
SOURCE = (
    PACKAGE.parent
    / "20260720-a10m5r14r1-admission-role-matrix-remedy"
    / "artifacts/jobs/materialize_admission.py"
)
PACKAGE_ID = "20260720-a10m5r14r2-shared-environment-four-l40-portfolio"
RUN_ID = "a10m5r14r2-shared-environment-four-l40-portfolio-r0"
RECORD_TYPE = "a10m5r14r2-submission-admission"
ROLES = {"control-materialization", "continuous-distribution-head-factorial-portfolio"}


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=REPO, check=True, capture_output=True
    ).stdout


def verify_parent_wrapper(*, source: Path = SOURCE, published: bytes | None = None) -> None:
    if published is None:
        published = git_bytes(PARENT_COMMIT, source.resolve().relative_to(REPO).as_posix())
    if source.read_bytes() != published:
        raise RuntimeError("R14R1 admission wrapper differs from published bytes")


def verify_published_source(source_commit: str) -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if not (source_commit == head == upstream and branch == "main" and Path(__file__).read_bytes() == git_bytes(source_commit, relative)):
        raise RuntimeError("R14R2 admission wrapper is not exact published main")
    verify_parent_wrapper()


verify_parent_wrapper()
spec = importlib.util.spec_from_file_location("r14r1_materialize_admission", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14R1 admission materializer")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
delegated = parent.delegated
delegated.PACKAGE = PACKAGE
delegated.REPO = REPO
delegated.PACKAGE_ID = PACKAGE_ID
delegated.RUN_ID = RUN_ID
delegated.REMOTE_ROOT = f"/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/{RUN_ID}"
delegated.ROLES = ROLES
delegated.verify_published_source = verify_published_source


def fetch_and_verify(target: Path, *, role: str, state_sha256: str, source_commit: str) -> dict[str, Any]:
    delegated.run(["scp", "-oBatchMode=yes", f"{delegated.REMOTE_HOST}:{delegated.REMOTE_ROOT}/admissions/{role}.json", str(target)])
    receipt = delegated.read(target)
    occupancy_fresh = True
    if role == "continuous-distribution-head-factorial-portfolio":
        captured = receipt.get("occupancy_captured_at")
        try:
            captured_at = dt.datetime.fromisoformat(captured.replace("Z", "+00:00"))
            age = (dt.datetime.now(dt.timezone.utc) - captured_at).total_seconds()
            occupancy_fresh = 0 <= age <= 60
        except (AttributeError, TypeError, ValueError):
            occupancy_fresh = False
    if not (
        delegated.authenticated(receipt)
        and receipt.get("schema_version") == "lemhi-toolkit-record-2"
        and receipt.get("record_type") == RECORD_TYPE
        and receipt.get("package_id") == PACKAGE_ID
        and receipt.get("run_id") == RUN_ID
        and receipt.get("role") == role
        and receipt.get("attempt_index") == 0
        and receipt.get("source_commit") == source_commit
        and receipt.get("decision") == "PASS"
        and receipt.get("valid") is True
        and occupancy_fresh
        and (
            role != "continuous-distribution-head-factorial-portfolio"
            or receipt.get("occupancy_node") == "node03"
        )
        and receipt.get("input_identities", {}).get("toolkit_state_sha256") == state_sha256
        and isinstance(receipt.get("gates"), dict)
        and receipt["gates"]
        and all(value is True for value in receipt["gates"].values())
    ):
        raise RuntimeError("materialized R14R2 admission receipt failed authentication or freshness")
    return receipt


delegated.fetch_and_verify = fetch_and_verify

if __name__ == "__main__":
    delegated.main()
