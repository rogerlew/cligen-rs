#!/usr/bin/env python3
"""Build fresh R14R1 authority and plan records over unchanged R14 science."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "7b44bfae967d0f030c2f521ad5777547bb13b3b0"
PARENT_BUILDER = (
    PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial"
    / "artifacts/jobs/build_control_records.py"
)
PARENT_ABORT_SHA256 = "590b69e6f2ec986d8af0f7890d43f0ce4d24d8c5e23a4a85e88bd0f3df675f23"
PACKAGE_ID = "20260720-a10m5r14r1-admission-role-matrix-remedy"
RUN_ID = "a10m5r14r1-admission-role-matrix-remedy-r0"
RECORD_TYPE = "a10m5r14r1-submission-admission"
ROLES = (
    ("continuous-location-ou-k2", "centered_location_ou", "K2"),
    (
        "continuous-location-ou-smooth-climatology-k2",
        "centered_location_ou_smooth_climatology",
        "K2",
    ),
    (
        "continuous-location-scale-ou-k2",
        "centered_location_and_scale_ou",
        "K2",
    ),
    (
        "continuous-location-scale-ou-smooth-climatology-k2",
        "centered_location_and_scale_ou_smooth_climatology",
        "K2",
    ),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def verify_parent_builder(
    *, source: Path = PARENT_BUILDER, published: bytes | None = None
) -> None:
    if published is None:
        relative = source.resolve().relative_to(REPO).as_posix()
        published = git_bytes(PARENT_COMMIT, relative)
    if source.read_bytes() != published:
        raise RuntimeError("R14 parent authority builder differs from published bytes")


def abort_bundle(record_commit: str | None = None) -> dict[str, object]:
    path = PACKAGE / "artifacts/parent-pre-submission-abort.json"
    if digest(path) != PARENT_ABORT_SHA256:
        raise RuntimeError("exact R14 pre-submission abort byte identity drift")
    value = json.loads(path.read_text(encoding="utf-8"))
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    if (
        recorded != hashlib.sha256(canonical(semantic)).hexdigest()
        or value.get("package_id")
        != "20260720-a10m5r14-continuous-distribution-head-factorial"
        or value.get("run_id")
        != "a10m5r14-continuous-distribution-head-factorial-r0"
        or value.get("source_commit") != PARENT_COMMIT
        or value.get("terminal") != "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION"
        or value.get("remote_absent") is not True
    ):
        raise RuntimeError("R14 pre-submission abort authentication drift")
    result: dict[str, object] = {
        "artifact": {"bytes": path.stat().st_size, "sha256": digest(path)},
        "artifact_source_path": path.relative_to(REPO).as_posix(),
        "package_id": value["package_id"],
        "parent_receipt_source_commit": PARENT_COMMIT,
        "plan_id": value["plan_id"],
        "record_sha256": value["record_sha256"],
        "terminal": value["terminal"],
    }
    if record_commit is not None:
        delegated.verify_commit(record_commit)
        relative = path.relative_to(REPO).as_posix()
        published = git_bytes(record_commit, relative)
        if published != path.read_bytes():
            raise RuntimeError("R14 abort copy differs from R14R1 record commit")
        result["artifact_record_commit"] = record_commit
    return result


# Authenticate the complete published R14 builder before executing it.
verify_parent_builder()
spec = importlib.util.spec_from_file_location("r14_build_control_records", PARENT_BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14 authority builder")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
delegated = parent.inherited
base_authority = parent.authority
base_plan = parent.plan


def rewrite_record(path: Path, changes: dict) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(changes)
    delegated.write(path, value)


def authority(options) -> None:
    predecessor = abort_bundle(getattr(options, "source_commit", None))
    delegated.predecessor_bundle = lambda: predecessor
    base_authority(options)
    rewrite_record(
        options.output,
        {
            "predecessor_package_evidence": predecessor,
            "resource_ceiling_gpu_minutes": 995,
            "resource_class": "four-concurrent-l40-continuous-distribution-head-factorial",
        },
    )


def plan(options) -> None:
    predecessor = abort_bundle(getattr(options, "source_commit", None))
    delegated.predecessor_bundle = lambda: predecessor
    base_plan(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    expected_roles = ["control-materialization", *(row[0] for row in ROLES)]
    if [job.get("role") for job in value.get("jobs", [])] != expected_roles:
        raise RuntimeError("R14R1 plan role matrix drift")
    value["admission_materialization"]["record_type"] = RECORD_TYPE
    value["admission_materialization"]["required_roles"] = expected_roles
    value["predecessor_package_evidence"] = predecessor
    value["submission_waves"] = [
        ["control-materialization"],
        [row[0] for row in ROLES],
    ]
    delegated.write(options.output, value)


delegated.PACKAGE_ID = PACKAGE_ID
delegated.RUN_ID = RUN_ID
delegated.AUTHORITY_ID = f"{RUN_ID}-authority"
delegated.BUDGET_ID = f"{RUN_ID}-budget"
delegated.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
delegated.ROLES = ROLES
delegated.PREDECESSOR_COMMIT = PARENT_COMMIT
delegated.predecessor_bundle = abort_bundle
delegated.operational_predecessor_bundle = parent.science_bundle
delegated.authority = authority
delegated.plan = plan


if __name__ == "__main__":
    delegated.main()
