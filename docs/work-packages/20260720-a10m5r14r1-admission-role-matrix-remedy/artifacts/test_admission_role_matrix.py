#!/usr/bin/env python3
"""Exercise control and exact-prefix admissions for the four-role R14 wave."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import types
from pathlib import Path

path = Path(__file__).parent / "jobs/admission_checker.py"
spec = importlib.util.spec_from_file_location("r14r1_checker", path)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

ROLES = [
    "continuous-location-ou-k2",
    "continuous-location-ou-smooth-climatology-k2",
    "continuous-location-scale-ou-k2",
    "continuous-location-scale-ou-smooth-climatology-k2",
]
SOURCE_COMMIT = "f" * 40


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def sign(value: dict) -> dict:
    value.pop("record_sha256", None)
    value["record_sha256"] = hashlib.sha256(checker.canonical(value)).hexdigest()
    return value


def job_receipt(role: str, job_id: str) -> dict:
    return sign(
        {
            "attempt_index": 0,
            "job_id": job_id,
            "job_role": role,
            "package_id": checker.PACKAGE_ID,
            "passed": True,
            "result": {
                "gates": {"job_local_cleanup": True},
                "terminal": True,
            },
            "run_id": checker.RUN_ID,
        }
    )


with tempfile.TemporaryDirectory() as scratch:
    remote = Path(scratch) / "remote"
    admissions = remote / "admissions"
    publication = remote / "admission-input/publication"
    admissions.mkdir(parents=True)
    publication.mkdir(parents=True)
    contract_path = remote / "job-local-capacity-contract.json"
    manifest_path = remote / "asset-manifest.json"
    state_path = remote / "admission-input/state.json"

    contract = {
        "admission": {
            "admission_closes_after_any_observed_candidate_failure": True,
            "control_must_pass_before_candidates": True,
            "maximum_live_candidate_jobs": 4,
            "maximum_simultaneous_bootstraps": 1,
            "waves": [ROLES],
        },
        "package_id": checker.PACKAGE_ID,
        "resources": {"candidate_role_count": 4},
    }
    write(contract_path, contract)
    archive_identities = {
        "runtime.tar.gz": {"bytes": 11, "sha256": "1" * 64},
        "wheelhouse.tar": {"bytes": 22, "sha256": "2" * 64},
        "requirements.lock": {"bytes": 33, "sha256": "3" * 64},
    }
    manifest = {
        "assets": {
            **archive_identities,
            "admission_checker.py": {
                "bytes": path.stat().st_size,
                "sha256": checker.digest(path),
            },
        },
        "package_id": checker.PACKAGE_ID,
        "source_commit": SOURCE_COMMIT,
    }
    write(manifest_path, manifest)
    manifest_identity = {
        "bytes": manifest_path.stat().st_size,
        "sha256": checker.digest(manifest_path),
    }

    all_roles = [checker.CONTROL_ROLE, *ROLES]
    plan = {
        "admission_materialization": {
            "asset": "materialize_admission.py",
            "receipt_directory": str(admissions.resolve()),
            "record_type": "a10m5r14r1-submission-admission",
            "required_before_each_submit": True,
            "required_roles": all_roles,
            "snapshot": "exact private toolkit state plus authenticated job receipts",
            "toolkit_submit_invokes_package_checker": False,
        },
        "assets": [
            {"logical_name": "asset-manifest.json", **manifest_identity},
            {
                "logical_name": "admission_checker.py",
                "bytes": path.stat().st_size,
                "sha256": checker.digest(path),
            },
        ],
        "evidence_allowlist": [f"admissions/{role}.json" for role in all_roles],
        "jobs": [
            {"max_attempts": 1, "retry_on": [], "role": role}
            for role in all_roles
        ],
        "source_commit": SOURCE_COMMIT,
    }
    plan_id = hashlib.sha256(checker.canonical(plan)).hexdigest()
    attempts: dict[str, dict] = {}

    host_python = {
        "identity": {"bytes": 100, "sha256": "4" * 64},
        "path": "/usr/bin/python3.11",
        "resolved_path": "/usr/bin/python3.11",
        "version": "3.11.9",
    }

    def write_state(run_state: str) -> None:
        write(
            state_path,
            {
                "attempts": attempts,
                "authority_id": f"{checker.RUN_ID}-authority",
                "current_plan_id": plan_id,
                "package_id": checker.PACKAGE_ID,
                "plan_revisions": [{"plan_id": plan_id, "semantic": plan}],
                "run_id": checker.RUN_ID,
                "run_state": run_state,
                "source_commit": SOURCE_COMMIT,
            },
        )

    def options(role: str, setups: list[str]) -> types.SimpleNamespace:
        return types.SimpleNamespace(
            asset_manifest=manifest_path,
            contract=contract_path,
            control_plane_python=host_python,
            created_at="2026-07-20T00:00:00Z",
            output=admissions / f"{role}.json",
            publication_dir=publication,
            remote_run_root=remote,
            role=role,
            setup=setups,
            toolkit_state=state_path,
        )

    def setup_receipt(role: str, job_id: str) -> Path:
        target = remote / f"results/{role}/setup.json"
        value = sign(
            {
                "authentication": {
                    "asset_identities_authenticated": True,
                    "execution_identity_authenticated": True,
                    "portable_compute_python_authenticated": True,
                    "submission_admission_authenticated": True,
                },
                "cleanup": {
                    "pip_cache_deleted_before_science": True,
                    "wheelhouse_deleted_before_science": True,
                },
                "execution_identity": {
                    "asset_manifest_sha256": manifest_identity["sha256"],
                    "host_python_path": "[JOB_LOCAL]/runtime/cpython/bin/python3",
                    "host_python_version": "Python 3.11.9",
                    "job_id": job_id,
                    "node": "gpu001",
                    "owner_marker_sha256": "5" * 64,
                    "role": role,
                    "run_id": checker.RUN_ID,
                    "source_commit": SOURCE_COMMIT,
                    "submission_admission_authenticated": True,
                    "submission_admission_record_sha256": "6" * 64,
                },
                "exit_codes": {
                    "host_python_version": 0,
                    "pip_check": 0,
                    "pip_install": 0,
                    "runtime_version": 0,
                },
                "identities": {
                    "asset_manifest": manifest_identity,
                    "requirements_lock": archive_identities["requirements.lock"],
                    "runtime_archive": archive_identities["runtime.tar.gz"],
                    "wheelhouse_archive": archive_identities["wheelhouse.tar"],
                },
                "ready_for_science": True,
                "stage": "ready-for-science",
                "valid": True,
            }
        )
        write(target, value)
        return target

    # Control admission must pass from a realistic verified, zero-attempt state.
    write_state("VERIFIED")
    receipt, passed = checker.check(options(checker.CONTROL_ROLE, []))
    if not passed or receipt["decision"] != "PASS" or not all(receipt["gates"].values()):
        raise RuntimeError("control admission did not pass realistic verified state")

    control_job_id = "1000"
    attempts[f"{checker.CONTROL_ROLE}.0"] = {
        "attempt_index": 0,
        "job_id": control_job_id,
        "job_role": checker.CONTROL_ROLE,
        "passed": True,
        "state": "RESULT_VALIDATED",
    }
    write(publication / f"job-{checker.CONTROL_ROLE}.0.json", job_receipt(checker.CONTROL_ROLE, control_job_id))

    setup_paths: dict[str, Path] = {}
    # Admit each role from an exact prefix. Earlier submitted roles supply
    # authenticated setup receipts, allowing all four science phases live.
    for index, role in enumerate(ROLES):
        write_state("MATRIX_ACTIVE")
        setup_args = [f"{prior}={setup_paths[prior]}" for prior in ROLES[:index]]
        receipt, passed = checker.check(options(role, setup_args))
        if not passed or receipt["admission_sequence"] != {
            "kind": "candidate",
            "member_index": index,
            "wave_index": 0,
        }:
            failed = [name for name, value in receipt["gates"].items() if not value]
            raise RuntimeError(f"candidate {index + 1} admission failed: {failed}")
        job_id = str(1001 + index)
        attempts[f"{role}.0"] = {
            "attempt_index": 0,
            "job_id": job_id,
            "job_role": role,
            "passed": None,
            "state": "SUBMITTED",
        }
        setup_paths[role] = setup_receipt(role, job_id)

    # A validated same-wave predecessor uses its passed cleanup receipt and
    # must not also appear in --setup; a still-submitted predecessor must.
    first = ROLES[0]
    attempts[f"{first}.0"]["state"] = "RESULT_VALIDATED"
    attempts[f"{first}.0"]["passed"] = True
    write(publication / f"job-{first}.0.json", job_receipt(first, "1001"))
    del attempts[f"{ROLES[2]}.0"]
    del attempts[f"{ROLES[3]}.0"]
    write_state("MATRIX_ACTIVE")
    receipt, passed = checker.check(
        options(ROLES[2], [f"{ROLES[1]}={setup_paths[ROLES[1]]}"])
    )
    if not passed:
        raise RuntimeError("validated/submitted mixed exact prefix was rejected")
    _, passed_with_extra_setup = checker.check(
        options(
            ROLES[2],
            [
                f"{first}={setup_paths[first]}",
                f"{ROLES[1]}={setup_paths[ROLES[1]]}",
            ],
        )
    )
    if passed_with_extra_setup:
        raise RuntimeError("setup input for validated predecessor was accepted")

    # Gaps, future roles, noncanonical attempt keys, and intermediate states
    # must all fail closed.
    saved_second = attempts.pop(f"{ROLES[1]}.0")
    write_state("MATRIX_ACTIVE")
    _, gap_passed = checker.check(options(ROLES[2], []))
    attempts[f"{ROLES[1]}.0"] = saved_second
    attempts["duplicate.0"] = dict(saved_second)
    write_state("MATRIX_ACTIVE")
    _, duplicate_passed = checker.check(
        options(ROLES[2], [f"{ROLES[1]}={setup_paths[ROLES[1]]}"])
    )
    del attempts["duplicate.0"]
    attempts["miskeyed.0"] = attempts.pop(f"{ROLES[1]}.0")
    write_state("MATRIX_ACTIVE")
    _, miskey_passed = checker.check(options(ROLES[2], []))
    attempts[f"{ROLES[1]}.0"] = attempts.pop("miskeyed.0")
    attempts[f"{ROLES[3]}.0"] = {
        "attempt_index": 0,
        "job_id": "1004",
        "job_role": ROLES[3],
        "passed": None,
        "state": "SUBMITTED",
    }
    write_state("MATRIX_ACTIVE")
    _, future_passed = checker.check(
        options(ROLES[2], [f"{ROLES[1]}={setup_paths[ROLES[1]]}"])
    )
    del attempts[f"{ROLES[3]}.0"]
    intermediate_passes = []
    for state_name in ("REGISTERED", "RESERVED", "TERMINAL_OBSERVED"):
        attempts[f"{ROLES[1]}.0"]["state"] = state_name
        write_state("MATRIX_ACTIVE")
        _, admitted = checker.check(options(ROLES[2], []))
        intermediate_passes.append(admitted)
    if (
        gap_passed
        or duplicate_passed
        or miskey_passed
        or future_passed
        or any(intermediate_passes)
    ):
        raise RuntimeError("non-prefix or intermediate state was admitted")

print("A10M5R14R1-ADMISSION-ROLE-MATRIX-TEST-PASS")
