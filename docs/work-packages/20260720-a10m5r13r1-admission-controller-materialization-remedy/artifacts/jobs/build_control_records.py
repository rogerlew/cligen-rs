#!/usr/bin/env python3
"""Build fresh R13R1 authority/plan records from authenticated R13 code."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "c849cdd3e0fcf8abf496b6ff987776a08d8b30cf"
SOURCE = (
    PACKAGE.parent / "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
    / "artifacts/jobs/build_control_records.py"
)
TRANSITIVE_SOURCE = (
    PACKAGE.parent / "20260719-a10m5r12r1-admission-materialization-remedy"
    / "artifacts/jobs/build_control_records.py"
)
PACKAGE_ID = "20260720-a10m5r13r1-admission-controller-materialization-remedy"
RUN_ID = "a10m5r13r1-admission-controller-materialization-remedy-r0"
RECORD_TYPE = "a10m5r13r1-submission-admission"
ROLES = (
    ("selector-aligned-continuous-hierarchy-k2", "selector_aligned_continuous_hierarchy", "K2"),
    ("selector-aligned-shared-slow-climate-state-k2", "selector_aligned_shared_slow_climate_state", "K2"),
)
PREDECESSOR_FILES = (
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/artifacts/pre-submission-abort.json",
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/package.md",
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/scaffold-review.md",
)
SCIENCE_FILES = (
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/artifacts/science-contract.json",
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/artifacts/portfolio-contract.json",
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/artifacts/temporal-contract.json",
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/artifacts/jobs/continuous_core.py",
    "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy/artifacts/jobs/selector_loss.py",
)


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=REPO,
        check=True, capture_output=True,
    ).stdout


def verify_inherited_builder(
    commit: str, *, source: Path = SOURCE, published: bytes | None = None
) -> None:
    if published is None:
        published = git_bytes(commit, source.resolve().relative_to(REPO).as_posix())
    if source.read_bytes() != published:
        raise RuntimeError("inherited R13 builder differs from published bytes")


def verify_transitive_builder(
    commit: str, *, source: Path = TRANSITIVE_SOURCE, published: bytes | None = None
) -> None:
    if published is None:
        published = git_bytes(commit, source.resolve().relative_to(REPO).as_posix())
    if source.read_bytes() != published:
        raise RuntimeError("transitive R12R1 builder differs from published bytes")


_head = subprocess.run(
    ("git", "rev-parse", "HEAD"), cwd=REPO, check=True,
    capture_output=True, text=True,
).stdout.strip()
_upstream = subprocess.run(
    ("git", "rev-parse", "origin/main"), cwd=REPO, check=True,
    capture_output=True, text=True,
).stdout.strip()
if _head != _upstream:
    raise RuntimeError("cannot import inherited R13 builder off published main")
verify_inherited_builder(_head)
verify_transitive_builder(_head)

spec = importlib.util.spec_from_file_location("r13_control_builder", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited R13 control builder")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
delegated = builder.inherited


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    payload = json.dumps(
        semantic, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()
    return isinstance(recorded, str) and recorded == hashlib.sha256(payload).hexdigest()


def bundle(commit: str, package_id: str, files: tuple[str, ...]) -> dict:
    delegated.verify_commit(commit)
    rows = {}
    for relative in files:
        payload = git_bytes(commit, relative)
        if (REPO / relative).read_bytes() != payload:
            raise RuntimeError(f"inherited R13 source drift: {relative}")
        rows[relative] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return {"files": rows, "package_id": package_id, "record_commit": commit}


def predecessor_bundle() -> dict:
    value = bundle(
        PARENT_COMMIT,
        "20260720-a10m5r13-selector-aligned-continuous-hierarchy",
        PREDECESSOR_FILES,
    )
    abort = json.loads((REPO / PREDECESSOR_FILES[0]).read_text(encoding="utf-8"))
    if not (
        authenticated(abort)
        and abort.get("record_type") == "abort_receipt"
        and abort.get("terminal") == "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION"
        and abort.get("remote_absent") is True
        and abort.get("job_local_cleanup") == "not_started"
        and abort.get("package_id")
        == "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
    ):
        raise RuntimeError("R13 zero-allocation abort provenance drift")
    return value


def science_bundle(_source_commit: str) -> dict:
    return bundle(
        PARENT_COMMIT,
        "20260720-a10m5r13-selector-aligned-continuous-hierarchy",
        SCIENCE_FILES,
    )


def verify_published_source(source_commit: str) -> None:
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    branch = subprocess.run(
        ("git", "branch", "--show-current"), cwd=REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if not (
        source_commit == head == upstream and branch == "main"
        and Path(__file__).read_bytes() == git_bytes(source_commit, relative)
    ):
        raise RuntimeError("R13R1 builder is not exact published main")
    verify_inherited_builder(source_commit)
    verify_transitive_builder(source_commit)


base_authority = builder.authority
base_plan = builder.plan


def authority(options) -> None:
    base_authority(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    if value.get("resource_ceiling_gpu_minutes") != 515:
        raise RuntimeError("fresh R13R1 authority ceiling drift")


def plan(options) -> None:
    base_plan(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    if not (
        value.get("package_id") == PACKAGE_ID
        and value.get("run_id") == RUN_ID
        and value.get("admission_materialization", {}).get("record_type")
        == RECORD_TYPE
        and value.get("submission_waves")
        == [["control-materialization"], [ROLES[0][0], ROLES[1][0]]]
        and value.get("evidence_volume")
        == {
            "maximum_expanded_bytes": 128000000,
            "maximum_file_bytes": 64000000,
            "maximum_files": len(value["evidence_allowlist"]),
        }
    ):
        raise RuntimeError("R13R1 plan identity/volume/wave drift")


builder.RECORD_TYPE = RECORD_TYPE
delegated.PACKAGE_ID = PACKAGE_ID
delegated.RUN_ID = RUN_ID
delegated.AUTHORITY_ID = f"{RUN_ID}-authority"
delegated.BUDGET_ID = f"{RUN_ID}-budget"
delegated.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
delegated.ROLES = ROLES
delegated.PREDECESSOR_COMMIT = PARENT_COMMIT
delegated.predecessor_bundle = predecessor_bundle
delegated.operational_predecessor_bundle = science_bundle
delegated.verify_published_source = verify_published_source
delegated.authority = authority
delegated.plan = plan


if __name__ == "__main__":
    delegated.main()
