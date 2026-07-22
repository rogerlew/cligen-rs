#!/usr/bin/env python3
"""Authenticate the outer A10M5R15 campaign accounting boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
ACCOUNTING = PACKAGE / "artifacts/campaign-accounting.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    encoded = json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode()
    return recorded == hashlib.sha256(encoded).hexdigest()


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def validate(source_commit: str | None = None) -> dict:
    if source_commit is not None:
        source_path = Path(__file__).resolve()
        if source_path.read_bytes() != git_bytes(source_commit, source_path):
            raise RuntimeError("campaign accounting validator differs from published source")
    value = json.loads(ACCOUNTING.read_text(encoding="utf-8"))
    components = value.get("components", [])
    actual = sum(row.get("actual_l40_minutes", -1) for row in components)
    expected_kinds = [
        "failed-r2-control",
        "canceled-control-calibration",
        "out-of-band-corrective-cleanup",
        "successful-successor-control-calibration",
        "successful-r2r2-control",
        "failed-r2r2-portfolio-launcher",
    ]
    if not (
        value.get("valid") is True
        and value.get("package_id") == PACKAGE.name
        and actual == value.get("realized_l40_minutes") == 60
        and value.get("outstanding_study_ceiling_l40_minutes") == 515
        and value.get("bounded_maximum_l40_minutes") == actual + 515 == 575
        and value.get("authorized_outer_ceiling_l40_minutes") == 597
        and value["bounded_maximum_l40_minutes"]
        <= value["authorized_outer_ceiling_l40_minutes"]
        and len(value.get("released_recovery_reserves", [])) == 3
        and [row.get("kind") for row in components] == expected_kinds
        and len({row.get("evidence_path") for row in components}) == 6
        and len({row.get("record_sha256") for row in components}) == 6
    ):
        raise RuntimeError("campaign accounting identity or arithmetic drift")
    for row in components:
        path = REPO / row["evidence_path"]
        evidence = json.loads(path.read_text(encoding="utf-8"))
        if digest(path) != row["evidence_sha256"]:
            raise RuntimeError(f"campaign evidence digest drift: {row['kind']}")
        kind = row["kind"]
        if kind == "failed-r2-control":
            valid = (
                evidence.get("actual_gpu_minutes") == row["actual_l40_minutes"] == 8
                and evidence.get("control", {}).get("job_id") == "1057354"
                and evidence.get("control", {}).get("job_receipt_record_sha256")
                == row["record_sha256"]
                and evidence.get("run_id")
                == "a10m5r15r2-external-normal-conditioning-execution-r0"
            )
        elif kind == "canceled-control-calibration":
            valid = (
                authenticated(evidence)
                and evidence.get("record_sha256") == row["record_sha256"]
                and evidence.get("job_id") == "1058096"
                and evidence.get("run_id")
                == "a10m5r15r2r1-successor-control-identity-calibration-r2"
                and evidence.get("result", {}).get("state") == "CANCELLED"
                and evidence.get("result", {}).get("actual_gpu_minutes")
                == row["actual_l40_minutes"]
                == 9
            )
        elif kind == "out-of-band-corrective-cleanup":
            valid = (
                authenticated(evidence)
                and evidence.get("record_sha256") == row["record_sha256"]
                and evidence.get("cleanup_job_id") == "1060849"
                and evidence.get("cleanup_actual_l40_minutes")
                == row["actual_l40_minutes"]
                == 1
                and evidence.get("accounting_classification")
                == "out-of-band-corrective-cleanup"
            )
        elif kind == "successful-successor-control-calibration":
            valid = (
                authenticated(evidence)
                and evidence.get("record_sha256") == row["record_sha256"]
                and evidence.get("job_id") == "1060850"
                and evidence.get("run_id")
                == "a10m5r15r2r1-successor-control-identity-calibration-r3"
                and evidence.get("result", {}).get("state") == "COMPLETED"
                and evidence.get("result", {}).get("actual_gpu_minutes")
                == row["actual_l40_minutes"]
                == 20
            )
        elif kind == "successful-r2r2-control":
            valid = (
                authenticated(evidence)
                and evidence.get("record_sha256") == row["record_sha256"]
                and evidence.get("job_id") == "1060866"
                and evidence.get("run_id")
                == "a10m5r15r2r2-successor-control-execution-r0"
                and evidence.get("result", {}).get("state") == "COMPLETED"
                and evidence.get("result", {}).get("actual_gpu_minutes")
                == row["actual_l40_minutes"]
                == 19
            )
        elif kind == "failed-r2r2-portfolio-launcher":
            valid = (
                authenticated(evidence)
                and evidence.get("record_sha256") == row["record_sha256"]
                and evidence.get("job_id") == "1060868"
                and evidence.get("run_id")
                == "a10m5r15r2r2-successor-control-execution-r0"
                and evidence.get("result", {}).get("state") == "FAILED"
                and evidence.get("result", {}).get("actual_gpu_minutes")
                == row["actual_l40_minutes"]
                == 3
            )
        else:
            valid = False
        if not valid:
            raise RuntimeError(f"campaign evidence semantic drift: {kind}")
        if source_commit is not None and path.read_bytes() != git_bytes(source_commit, path):
            raise RuntimeError(f"campaign evidence differs from published source: {kind}")
    releases = value["released_recovery_reserves"]
    if not (
        len({row.get("evidence_path") for row in releases}) == 3
        and len({row.get("event_sha256") for row in releases}) == 3
    ):
        raise RuntimeError("campaign recovery releases are not distinct")
    expected_release_runs = [
        "a10m5r15r2r1-successor-control-identity-calibration-r2",
        "a10m5r15r2r1-successor-control-identity-calibration-r3",
        "a10m5r15r2r2-successor-control-execution-r0",
    ]
    for release, expected_run in zip(releases, expected_release_runs):
        path = REPO / release["evidence_path"]
        evidence = json.loads(path.read_text(encoding="utf-8"))
        semantic_event = dict(evidence)
        recorded_event = semantic_event.pop("event_sha256", None)
        computed_event = hashlib.sha256(
            json.dumps(semantic_event, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()
        if not (
            digest(path) == release["evidence_sha256"]
            and recorded_event == computed_event == release["event_sha256"]
            and evidence.get("run_id") == expected_run
            and evidence.get("job_role") == "toolkit-recovery"
            and evidence.get("status") == "released"
            and evidence.get("release_reason") == "verified-cleanup"
            and evidence.get("requested_gpu_minutes") == 5
        ):
            raise RuntimeError("campaign recovery-release evidence drift")
        if source_commit is not None and path.read_bytes() != git_bytes(source_commit, path):
            raise RuntimeError("campaign recovery release differs from published source")
    if source_commit is not None and ACCOUNTING.read_bytes() != git_bytes(source_commit, ACCOUNTING):
        raise RuntimeError("campaign accounting differs from published source")
    return value
