#!/usr/bin/env python3
"""Materialize fresh A10M5R15R2 composed-checker admissions."""

from __future__ import annotations

import importlib.util
import datetime as dt
import subprocess
import sys
from pathlib import Path

import campaign_accounting as campaign


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "719d83451ddff698b280219708f7648ff73c8f9d"
PARENT_PACKAGE = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
SOURCE = PACKAGE.parent / PARENT_PACKAGE / "artifacts/jobs/materialize_admission.py"
PACKAGE_ID = "20260722-a10m5r15r2r2-successor-control-execution"
RUN_ID = "a10m5r15r2r2-successor-control-execution-r0"
RECORD_TYPE = "a10m5r15r2r2-submission-admission"
PORTFOLIO_ROLE = "external-normal-conditioning-portfolio"
ROLES = {"control-materialization", PORTFOLIO_ROLE}


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


if SOURCE.read_bytes() != git_bytes(PARENT_COMMIT, SOURCE):
    raise RuntimeError("R14R2R2 materializer differs from published parent bytes")
spec = importlib.util.spec_from_file_location("inherited_r15r2_materializer", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited admission materializer")
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
delegated = parent.delegated
checker = parent.parent
base_fetch_and_verify = delegated.fetch_and_verify


def verify_published_source(source_commit: str) -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    accounting = campaign.validate(source_commit)
    actual = accounting["realized_l40_minutes"]
    if not (
        source_commit == head == upstream
        and branch == "main"
        and Path(__file__).read_bytes() == git_bytes(source_commit, Path(__file__).resolve())
        and actual == accounting.get("realized_l40_minutes") == 38
        and accounting.get("outstanding_study_ceiling_l40_minutes") == 515
        and accounting.get("bounded_maximum_l40_minutes") == actual + 515 == 553
        and accounting.get("authorized_outer_ceiling_l40_minutes") == 597
    ):
        raise RuntimeError("A10M5R15R2 materializer is not exact published main")


parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
parent.PORTFOLIO_ROLE = PORTFOLIO_ROLE
delegated.PACKAGE = PACKAGE
delegated.REPO = REPO
delegated.PACKAGE_ID = PACKAGE_ID
delegated.RUN_ID = RUN_ID
delegated.REMOTE_ROOT = f"/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/{RUN_ID}"
delegated.ROLES = ROLES
checker.PACKAGE_ID = PACKAGE_ID
checker.RUN_ID = RUN_ID
checker.RECORD_TYPE = RECORD_TYPE
checker.ROLES = ROLES
delegated.verify_published_source = verify_published_source


def fetch_and_verify(target: Path, *, role: str, state_sha256: str, source_commit: str):
    receipt = base_fetch_and_verify(
        target, role=role, state_sha256=state_sha256, source_commit=source_commit
    )
    if role == PORTFOLIO_ROLE:
        try:
            captured_at = dt.datetime.fromisoformat(
                receipt["occupancy_captured_at"].replace("Z", "+00:00")
            )
            age = (dt.datetime.now(dt.timezone.utc) - captured_at).total_seconds()
            fresh = 0 <= age <= 60 and receipt.get("occupancy_node") == "node03"
        except (KeyError, AttributeError, TypeError, ValueError):
            fresh = False
        if not fresh:
            raise RuntimeError("R2 portfolio admission occupancy is stale")
    return receipt


delegated.fetch_and_verify = fetch_and_verify


if __name__ == "__main__":
    delegated.main()
