#!/usr/bin/env python3
"""Materialize the single-role successor control-calibration admission."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "b38f695697a8636e67f041ccae373107cb5cb5bc"
SOURCE = (
    PACKAGE.parent
    / "20260721-a10m5r15r2-external-normal-conditioning-execution"
    / "artifacts/jobs/materialize_admission.py"
)
PACKAGE_ID = "20260722-a10m5r15r2r1-successor-control-identity-calibration"
RUN_ID = "a10m5r15r2r1-successor-control-identity-calibration-r0"
RECORD_TYPE = "a10m5r15r2r1-submission-admission"


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


if SOURCE.read_bytes() != git_bytes(PARENT_COMMIT, SOURCE):
    raise RuntimeError("R2 admission materializer differs from published bytes")
spec = importlib.util.spec_from_file_location("r15r2_materialize_admission", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R2 admission materializer")
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
delegated = parent.delegated
checker = parent.checker


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
    if not (
        source_commit == head == upstream
        and branch == "main"
        and Path(__file__).read_bytes()
        == git_bytes(source_commit, Path(__file__).resolve())
    ):
        raise RuntimeError("calibration materializer is not exact published main")


parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
parent.ROLES = {"control-materialization"}
delegated.PACKAGE = PACKAGE
delegated.REPO = REPO
delegated.PACKAGE_ID = PACKAGE_ID
delegated.RUN_ID = RUN_ID
delegated.REMOTE_ROOT = f"/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/{RUN_ID}"
delegated.ROLES = {"control-materialization"}
checker.PACKAGE_ID = PACKAGE_ID
checker.RUN_ID = RUN_ID
checker.RECORD_TYPE = RECORD_TYPE
checker.ROLES = {"control-materialization"}
delegated.verify_published_source = verify_published_source


if __name__ == "__main__":
    delegated.main()
