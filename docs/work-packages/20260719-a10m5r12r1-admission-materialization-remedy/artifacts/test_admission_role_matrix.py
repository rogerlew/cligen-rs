#!/usr/bin/env python3
"""Executable admission-sequence guards for the A10M5R12R1 role matrix."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[1]
CHECKER_SOURCE = PACKAGE / "artifacts/jobs/admission_checker.py"
SPEC = importlib.util.spec_from_file_location("admission_checker", CHECKER_SOURCE)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)

FIRST_ROLE = "continuous-medium-latent-process-k2"
SECOND_ROLE = "continuous-hierarchical-latent-process-k2"
SOURCE_COMMIT = "a" * 40
CONTROL_PLANE_PYTHON = {
    "identity": {"bytes": 1, "sha256": "b" * 64},
    "path": "/usr/bin/python3.11",
    "resolved_path": "/usr/bin/python3.11",
    "version": "3.11.9",
}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def authenticate(value: dict[str, Any]) -> dict[str, Any]:
    value["record_sha256"] = CHECKER.record_hash(value)
    return value


class AdmissionFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.contract = root / "job-local-capacity-contract.json"
        self.manifest = root / "asset-manifest.json"
        self.state = root / "admission-input/state.json"
        self.publication = root / "admission-input/publication"
        self.publication.mkdir(parents=True)
        self.assets = {
            "runtime.tar.gz": {"bytes": 101, "sha256": "1" * 64},
            "wheelhouse.tar": {"bytes": 102, "sha256": "2" * 64},
            "requirements.lock": {"bytes": 103, "sha256": "3" * 64},
        }
        write_json(
            self.contract,
            {
                "package_id": CHECKER.PACKAGE_ID,
                "admission": {
                    "admission_closes_after_any_observed_candidate_failure": True,
                    "maximum_live_candidate_jobs": 2,
                    "maximum_simultaneous_bootstraps": 1,
                    "waves": [[FIRST_ROLE, SECOND_ROLE]],
                },
                "resources": {"candidate_role_count": 2},
            },
        )
        write_json(
            self.manifest,
            {"assets": self.assets, "source_commit": SOURCE_COMMIT},
        )
        self.plan = self._plan()

    def _plan(self) -> dict[str, Any]:
        manifest_identity = {
            "bytes": self.manifest.stat().st_size,
            "logical_name": "asset-manifest.json",
            "sha256": CHECKER.digest(self.manifest),
        }
        checker_identity = {
            "bytes": CHECKER_SOURCE.stat().st_size,
            "logical_name": "admission_checker.py",
            "sha256": CHECKER.digest(CHECKER_SOURCE),
        }
        roles = [CHECKER.CONTROL_ROLE, FIRST_ROLE, SECOND_ROLE]
        return {
            "admission_materialization": {
                "asset": "materialize_admission.py",
                "receipt_directory": "/private/controller-admissions",
                "record_type": "a10m5r12-submission-admission",
                "required_before_each_submit": True,
                "required_roles": roles,
                "snapshot": "exact private toolkit state plus authenticated job receipts",
                "toolkit_submit_invokes_package_checker": False,
            },
            "assets": [manifest_identity, checker_identity],
            "evidence_allowlist": [f"admissions/{role}.json" for role in roles],
            "jobs": [
                {"max_attempts": 1, "retry_on": [], "role": role} for role in roles
            ],
            "source_commit": SOURCE_COMMIT,
        }

    @staticmethod
    def attempt(role: str, state: str, job_id: str, passed: bool | None = None) -> dict[str, Any]:
        return {
            "attempt_index": 0,
            "job_id": job_id,
            "job_role": role,
            "passed": passed,
            "state": state,
        }

    def write_state(self, run_state: str, attempts: dict[str, Any]) -> None:
        plan_id = CHECKER.record_hash(self.plan)
        write_json(
            self.state,
            {
                "attempts": attempts,
                "authority_id": "authority-fixture",
                "current_plan_id": plan_id,
                "package_id": CHECKER.PACKAGE_ID,
                "plan_revisions": [{"plan_id": plan_id, "semantic": self.plan}],
                "run_id": CHECKER.RUN_ID,
                "run_state": run_state,
                "source_commit": SOURCE_COMMIT,
            },
        )

    def write_job_receipt(self, role: str, attempt: dict[str, Any]) -> None:
        write_json(
            self.publication / f"job-{role}.0.json",
            authenticate(
                {
                    "attempt_index": 0,
                    "job_id": attempt["job_id"],
                    "job_role": role,
                    "package_id": CHECKER.PACKAGE_ID,
                    "passed": True,
                    "result": {
                        "gates": {"job_local_cleanup": True},
                        "terminal": True,
                    },
                    "run_id": CHECKER.RUN_ID,
                }
            ),
        )

    def write_ready_setup(self, role: str, job_id: str) -> Path:
        path = self.root / f"results/{role}/setup.json"
        manifest_identity = {
            "bytes": self.manifest.stat().st_size,
            "sha256": CHECKER.digest(self.manifest),
        }
        setup = {
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
                "node": "fixture-node",
                "owner_marker_sha256": "4" * 64,
                "role": role,
                "run_id": CHECKER.RUN_ID,
                "source_commit": SOURCE_COMMIT,
                "submission_admission_authenticated": True,
                "submission_admission_record_sha256": "5" * 64,
            },
            "exit_codes": {
                "host_python_version": 0,
                "pip_check": 0,
                "pip_install": 0,
                "runtime_version": 0,
            },
            "identities": {
                "asset_manifest": manifest_identity,
                "requirements_lock": self.assets["requirements.lock"],
                "runtime_archive": self.assets["runtime.tar.gz"],
                "wheelhouse_archive": self.assets["wheelhouse.tar"],
            },
            "ready_for_science": True,
            "stage": "ready-for-science",
            "valid": True,
        }
        write_json(path, authenticate(setup))
        return path

    def check(self, role: str, setups: list[str] | None = None) -> tuple[dict[str, Any], bool]:
        options = argparse.Namespace(
            asset_manifest=self.manifest,
            contract=self.contract,
            control_plane_python=CONTROL_PLANE_PYTHON,
            created_at="2026-07-20T00:00:00Z",
            output=self.root / f"admissions/{role}.json",
            publication_dir=self.publication,
            remote_run_root=self.root,
            role=role,
            setup=setups or [],
            toolkit_state=self.state,
        )
        return CHECKER.check(options)


class AdmissionRoleMatrixTest(unittest.TestCase):
    def test_contract_and_checker_use_derived_three_role_total(self) -> None:
        contract = json.loads(
            (PACKAGE / "artifacts/job-local-capacity-contract.json").read_text(
                encoding="utf-8"
            )
        )
        waves = contract["admission"]["waves"]
        roles = [role for wave in waves for role in wave]
        self.assertEqual(len(roles), contract["resources"]["candidate_role_count"])
        self.assertEqual(len(set(roles)), 2)
        self.assertTrue(
            contract["admission"]["admission_closes_after_any_observed_candidate_failure"]
        )
        source = CHECKER_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("len(set(plan_roles)) == 11", source)
        self.assertIn("len(set(plan_roles)) == len(all_roles)", source)
        self.assertIn('1 + contract["resources"]["candidate_role_count"]', source)
        self.assertIn('"admission_materialization_protocol"', source)
        self.assertIn('materialization.get("required_before_each_submit") is True', source)

    def test_control_admission_passes_from_verified_unattempted_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = AdmissionFixture(Path(raw))
            fixture.write_state("VERIFIED", {})
            receipt, passed = fixture.check(CHECKER.CONTROL_ROLE)
            self.assertTrue(passed, receipt["gates"])
            self.assertEqual(receipt["decision"], "PASS")
            self.assertEqual(receipt["admission_sequence"]["kind"], "control")

    def test_first_candidate_passes_after_authenticated_control(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = AdmissionFixture(Path(raw))
            control = fixture.attempt(
                CHECKER.CONTROL_ROLE, "RESULT_VALIDATED", "control-job", True
            )
            fixture.write_job_receipt(CHECKER.CONTROL_ROLE, control)
            fixture.write_state("MATRIX_ACTIVE", {f"{CHECKER.CONTROL_ROLE}.0": control})
            receipt, passed = fixture.check(FIRST_ROLE)
            self.assertTrue(passed, receipt["gates"])
            self.assertEqual(receipt["admission_sequence"]["member_index"], 0)
            self.assertTrue(receipt["gates"]["control_predecessor"])

    def test_second_candidate_passes_after_first_is_submitted_and_ready(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = AdmissionFixture(Path(raw))
            control = fixture.attempt(
                CHECKER.CONTROL_ROLE, "RESULT_VALIDATED", "control-job", True
            )
            first = fixture.attempt(FIRST_ROLE, "SUBMITTED", "first-job")
            fixture.write_job_receipt(CHECKER.CONTROL_ROLE, control)
            setup = fixture.write_ready_setup(FIRST_ROLE, first["job_id"])
            fixture.write_state(
                "MATRIX_ACTIVE",
                {f"{CHECKER.CONTROL_ROLE}.0": control, f"{FIRST_ROLE}.0": first},
            )
            receipt, passed = fixture.check(SECOND_ROLE, [f"{FIRST_ROLE}={setup}"])
            self.assertTrue(passed, receipt["gates"])
            self.assertEqual(receipt["admission_sequence"]["member_index"], 1)
            self.assertTrue(receipt["gates"]["first_role_setup_ready"])

    def test_second_candidate_rejects_setup_stale_against_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = AdmissionFixture(Path(raw))
            control = fixture.attempt(
                CHECKER.CONTROL_ROLE, "RESULT_VALIDATED", "control-job", True
            )
            first = fixture.attempt(FIRST_ROLE, "SUBMITTED", "current-first-job")
            fixture.write_job_receipt(CHECKER.CONTROL_ROLE, control)
            stale_setup = fixture.write_ready_setup(FIRST_ROLE, "stale-first-job")
            fixture.write_state(
                "MATRIX_ACTIVE",
                {f"{CHECKER.CONTROL_ROLE}.0": control, f"{FIRST_ROLE}.0": first},
            )
            receipt, passed = fixture.check(
                SECOND_ROLE, [f"{FIRST_ROLE}={stale_setup}"]
            )
            self.assertFalse(passed)
            self.assertEqual(receipt["decision"], "FAIL")
            self.assertFalse(receipt["gates"]["first_role_setup_ready"])
            self.assertFalse(receipt["gates"]["maximum_simultaneous_bootstraps"])


if __name__ == "__main__":
    unittest.main()
