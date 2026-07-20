#!/usr/bin/env python3
"""Materialize R14R1 admissions through the authenticated R14 controller."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "7b44bfae967d0f030c2f521ad5777547bb13b3b0"
SOURCE = (
    PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial"
    / "artifacts/jobs/materialize_admission.py"
)
PACKAGE_ID = "20260720-a10m5r14r1-admission-role-matrix-remedy"
RUN_ID = "a10m5r14r1-admission-role-matrix-remedy-r0"
RECORD_TYPE = "a10m5r14r1-submission-admission"
ROLES = {
    "control-materialization",
    "continuous-location-ou-k2",
    "continuous-location-ou-smooth-climatology-k2",
    "continuous-location-scale-ou-k2",
    "continuous-location-scale-ou-smooth-climatology-k2",
}


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def verify_parent_wrapper(
    *, source: Path = SOURCE, published: bytes | None = None
) -> None:
    if published is None:
        published = git_bytes(
            PARENT_COMMIT, source.resolve().relative_to(REPO).as_posix()
        )
    if source.read_bytes() != published:
        raise RuntimeError("R14 admission wrapper differs from published bytes")


def verify_published_source(source_commit: str) -> None:
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    branch = subprocess.run(
        ("git", "branch", "--show-current"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if not (
        source_commit == head == upstream
        and branch == "main"
        and Path(__file__).read_bytes() == git_bytes(source_commit, relative)
    ):
        raise RuntimeError("R14R1 admission wrapper is not exact published main")
    verify_parent_wrapper()


# Authenticate the published R14 materializer before import.
verify_parent_wrapper()
spec = importlib.util.spec_from_file_location("r14_materialize_admission", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14 admission materializer")
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


def fetch_and_verify(
    target: Path, *, role: str, state_sha256: str, source_commit: str
) -> dict[str, Any]:
    delegated.run(
        [
            "scp",
            "-oBatchMode=yes",
            f"{delegated.REMOTE_HOST}:{delegated.REMOTE_ROOT}/admissions/{role}.json",
            str(target),
        ]
    )
    receipt = delegated.read(target)
    if not (
        delegated.authenticated(receipt)
        and receipt.get("schema_version") == "lemhi-toolkit-record-2"
        and receipt.get("record_type") == RECORD_TYPE
        and isinstance(receipt.get("authority_id"), str)
        and receipt.get("package_id") == PACKAGE_ID
        and receipt.get("run_id") == RUN_ID
        and receipt.get("role") == role
        and receipt.get("attempt_index") == 0
        and receipt.get("source_commit") == source_commit
        and receipt.get("decision") == "PASS"
        and receipt.get("valid") is True
        and receipt.get("input_identities", {}).get("toolkit_state_sha256")
        == state_sha256
        and isinstance(receipt.get("gates"), dict)
        and receipt["gates"]
        and all(value is True for value in receipt["gates"].values())
    ):
        raise RuntimeError("materialized R14R1 admission receipt failed authentication")
    return receipt


delegated.fetch_and_verify = fetch_and_verify


if __name__ == "__main__":
    delegated.main()
