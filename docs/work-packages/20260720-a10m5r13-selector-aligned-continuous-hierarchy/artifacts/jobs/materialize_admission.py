#!/usr/bin/env python3
"""Materialize R13 admissions through the reviewed R12R1 implementation."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
SOURCE = (
    PACKAGE.parent
    / "20260719-a10m5r12r1-admission-materialization-remedy"
    / "artifacts"
    / "jobs"
    / "materialize_admission.py"
)
PACKAGE_ID = "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
RUN_ID = "a10m5r13-selector-aligned-continuous-hierarchy-r0"


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def verify_published_source(source_commit: str) -> None:
    identities = {
        subprocess.run(
            ("git", "rev-parse", name),
            cwd=REPO,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        for name in ("HEAD", "origin/main")
    }
    branch = subprocess.run(
        ("git", "branch", "--show-current"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if (
        identities != {source_commit}
        or branch != "main"
        or Path(__file__).read_bytes() != git_bytes(source_commit, relative)
    ):
        raise RuntimeError("R13 admission materializer is not exact published main")
    verify_inherited_source(source_commit)


def verify_inherited_source(
    source_commit: str,
    *,
    source: Path = SOURCE,
    published: bytes | None = None,
) -> None:
    if published is None:
        relative = source.resolve().relative_to(REPO).as_posix()
        published = git_bytes(source_commit, relative)
    if source.read_bytes() != published:
        raise RuntimeError("inherited admission materializer differs from published bytes")


# Authenticate delegated code before importing or executing it. The later
# source-commit check repeats this binding against the exact run authority.
_head = subprocess.run(
    ("git", "rev-parse", "HEAD"),
    cwd=REPO,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
_upstream = subprocess.run(
    ("git", "rev-parse", "origin/main"),
    cwd=REPO,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
if _head != _upstream:
    raise RuntimeError("cannot import inherited admission code off published main")
verify_inherited_source(_head)


spec = importlib.util.spec_from_file_location("r12r1_admission", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited admission materializer")
inherited = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inherited)
inherited.PACKAGE = PACKAGE
inherited.REPO = REPO
inherited.PACKAGE_ID = PACKAGE_ID
inherited.RUN_ID = RUN_ID
inherited.REMOTE_ROOT = f"/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/{RUN_ID}"
inherited.ROLES = {
    "control-materialization",
    "selector-aligned-continuous-hierarchy-k2",
    "selector-aligned-shared-slow-climate-state-k2",
}
inherited.verify_published_source = verify_published_source


def fetch_and_verify(
    target: Path,
    *,
    role: str,
    state_sha256: str,
    source_commit: str,
) -> dict[str, Any]:
    inherited.run(
        [
            "scp",
            "-oBatchMode=yes",
            f"{inherited.REMOTE_HOST}:{inherited.REMOTE_ROOT}/admissions/{role}.json",
            str(target),
        ]
    )
    receipt = inherited.read(target)
    if not (
        inherited.authenticated(receipt)
        and receipt.get("schema_version") == "lemhi-toolkit-record-2"
        and receipt.get("record_type") == "a10m5r13-submission-admission"
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
        raise RuntimeError("materialized R13 admission receipt failed authentication")
    return receipt


inherited.fetch_and_verify = fetch_and_verify


if __name__ == "__main__":
    inherited.main()
