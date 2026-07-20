#!/usr/bin/env python3
"""Verify the operational-only R13R1 successor without creating authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
import subprocess
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PARENT = REPO / "docs/work-packages/20260720-a10m5r13-selector-aligned-continuous-hierarchy"
PARENT_COMMIT = "c849cdd3e0fcf8abf496b6ff987776a08d8b30cf"
PACKAGE_ID = "20260720-a10m5r13r1-admission-controller-materialization-remedy"
RUN_ID = "a10m5r13r1-admission-controller-materialization-remedy-r0"

parser = argparse.ArgumentParser()
parser.add_argument("--science-python", type=Path)
parser.add_argument("--real-parent-assets", type=Path)
options = parser.parse_args()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: dict) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return isinstance(recorded, str) and recorded == hashlib.sha256(canonical(semantic)).hexdigest()


head = subprocess.run(
    ("git", "rev-parse", "HEAD"), cwd=REPO, check=True,
    capture_output=True, text=True,
).stdout.strip()
upstream = subprocess.run(
    ("git", "rev-parse", "origin/main"), cwd=REPO, check=True,
    capture_output=True, text=True,
).stdout.strip()
if head != upstream or head != PARENT_COMMIT:
    raise RuntimeError("R13R1 must scaffold from exact published R13 parent")

inheritance = read(PACKAGE / "artifacts/inheritance-manifest.json")
if not (
    inheritance["parent_commit"] == PARENT_COMMIT
    and inheritance["parent_package"]
    == "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
    and inheritance["parent_abort_terminal"]
    == "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION"
    and inheritance["fresh_gpu_minute_ceiling"] == 515
    and inheritance["protected_roles_opened"] == []
    and inheritance["solar_opened"] is False
):
    raise RuntimeError("R13R1 inheritance/firewall identity drift")

for relative, expected in inheritance["science_assets"].items():
    parent = PARENT / relative
    local = PACKAGE / relative
    committed = subprocess.run(
        ("git", "show", f"{PARENT_COMMIT}:{parent.relative_to(REPO).as_posix()}"),
        cwd=REPO, check=True, capture_output=True,
    ).stdout
    if (
        parent.read_bytes() != committed or local.read_bytes() != committed
        or hashlib.sha256(committed).hexdigest() != expected
    ):
        raise RuntimeError(f"R13 science asset changed in R13R1: {relative}")

abort = read(PACKAGE / "artifacts/parent-pre-submission-abort.json")
if not (
    (PACKAGE / "artifacts/parent-pre-submission-abort.json").read_bytes()
    == (PARENT / "artifacts/pre-submission-abort.json").read_bytes()
    and authenticated(abort)
    and abort["record_sha256"] == inheritance["parent_abort_record_sha256"]
    and abort["terminal"] == inheritance["parent_abort_terminal"]
    and abort["remote_absent"] is True
    and abort["job_local_cleanup"] == "not_started"
):
    raise RuntimeError("authenticated zero-allocation R13 abort drift")

capacity = read(PACKAGE / "artifacts/job-local-capacity-contract.json")
template = read(PACKAGE / "artifacts/execution-plan-template.json")
if not (
    capacity["package_id"] == PACKAGE_ID
    and capacity["resources"]["total_gpu_minute_ceiling"] == 515
    and capacity["resources"]["candidate_minutes_each"] == 240
    and template["package_id"] == PACKAGE_ID
    and template["run_id"] == RUN_ID
    and template["admission_materialization"]["record_type"]
    == "a10m5r13r1-submission-admission"
    and template["science_terminals"] == inheritance["science_terminals"]
):
    raise RuntimeError("R13R1 resource/plan identity drift")

for name in ("build_control_records.py", "materialize_admission.py"):
    source = (PACKAGE / "artifacts/jobs" / name).read_text(encoding="utf-8")
    if (
        PACKAGE_ID not in source or RUN_ID not in source
        or PARENT_COMMIT not in source
        or "a10m5r13r1-submission-admission" not in source
    ):
        raise RuntimeError(f"R13R1 committed controller identity incomplete: {name}")
admission_source = (PACKAGE / "artifacts/jobs/materialize_admission.py").read_text(encoding="utf-8")
if admission_source.index("verify_inherited_controller(_head)") > admission_source.index("spec.loader.exec_module(controller)"):
    raise RuntimeError("R13 controller is imported before authentication")
builder_source = (PACKAGE / "artifacts/jobs/build_control_records.py").read_text(encoding="utf-8")
if builder_source.index("verify_transitive_builder(_head)") > builder_source.index(
    "spec.loader.exec_module(builder)"
):
    raise RuntimeError("R12R1 builder is imported transitively before authentication")

for path in (PACKAGE / "artifacts/jobs").glob("*.py"):
    py_compile.compile(str(path), doraise=True)
for path in (PACKAGE / "artifacts").glob("*.py"):
    py_compile.compile(str(path), doraise=True)

for script in (
    "test_admission_wrapper.py", "test_builder.py", "test_prepare_assets.py",
    "test_replay_contract.py",
):
    subprocess.run(["python3", str(PACKAGE / "artifacts" / script)], check=True)

if options.real_parent_assets is None:
    print("A10M5R13R1-REAL-PARENT-NOT-RUN (supply --real-parent-assets)")
else:
    subprocess.run([
        "python3", str(PACKAGE / "artifacts/test_real_parent_assets.py"),
        "--parent-assets", str(options.real_parent_assets),
    ], check=True)

if options.science_python is None:
    print("A10M5R13R1-SCIENCE-TESTS-NOT-RUN (supply --science-python)")
else:
    for script in (
        "test_calendar.py", "test_selector_loss.py",
        "test_staged_continuous_core.py",
    ):
        subprocess.run([
            str(options.science_python), str(PACKAGE / "artifacts" / script)
        ], check=True)

print("A10M5R13R1-FREEZE-VERIFY-PASS")
