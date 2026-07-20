#!/usr/bin/env python3
"""Materialize fresh R14R2R2 composed-checker admissions."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "6463ab2bebcf016c371afc56e31ffc7156a2fb95"
PARENT_PACKAGE = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
SOURCE = PACKAGE.parent / PARENT_PACKAGE / "artifacts/jobs/materialize_admission.py"
PACKAGE_ID = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
RUN_ID = "a10m5r14r2r2-two-l40-two-wave-portfolio-r0"
RECORD_TYPE = "a10m5r14r2r2-submission-admission"


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=REPO, check=True, capture_output=True
    ).stdout


def verify_parent() -> None:
    if SOURCE.read_bytes() != git_bytes(PARENT_COMMIT, SOURCE.relative_to(REPO).as_posix()):
        raise RuntimeError("R14R2R1 materializer differs from published parent bytes")


verify_parent()
spec = importlib.util.spec_from_file_location("r14r2r1_materialize_admission", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14R2R1 materializer")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
delegated = parent.delegated


def verify_published_source(source_commit: str) -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if not (
        source_commit == head == upstream
        and branch == "main"
        and Path(__file__).read_bytes() == git_bytes(source_commit, relative)
    ):
        raise RuntimeError("R14R2R2 materializer is not exact published main")
    verify_parent()


parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
delegated.PACKAGE = PACKAGE
delegated.REPO = REPO
delegated.PACKAGE_ID = PACKAGE_ID
delegated.RUN_ID = RUN_ID
delegated.REMOTE_ROOT = f"/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/{RUN_ID}"
delegated.verify_published_source = verify_published_source


if __name__ == "__main__":
    delegated.main()
