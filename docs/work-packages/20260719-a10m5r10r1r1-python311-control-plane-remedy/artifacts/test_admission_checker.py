#!/usr/bin/env python3
"""Self-tests for the staged A10M5R10R1R1 admission state machine."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

PACKAGE = Path(__file__).resolve().parents[1]
CHECKER_PATH = PACKAGE / "artifacts/jobs/admission_checker.py"
CONTRACT_PATH = PACKAGE / "artifacts/job-local-capacity-contract.json"

SPEC = importlib.util.spec_from_file_location("admission_checker", CHECKER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load admission checker")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finalize(value: dict[str, object]) -> dict[str, object]:
    result = dict(value)
    result["record_sha256"] = CHECKER.record_hash(result)
    return result


class AdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="a10m5r10r1r1-admission-")
        self.remote = Path(self.temporary.name) / "remote-run"
        self.contract = self.remote / "job-local-capacity-contract.json"
        self.manifest = self.remote / "asset-manifest.json"
        self.state = self.remote / "admission-input/state.json"
        self.publication = self.remote / "admission-input/publication"
        self.contract.parent.mkdir(parents=True)
        self.contract.write_bytes(CONTRACT_PATH.read_bytes())
        self.contract_value = json.loads(self.contract.read_text(encoding="utf-8"))
        self.roles = [
            role
            for wave in self.contract_value["admission"]["waves"]
            for role in wave
        ]
        self.source_commit = "f" * 40
        self.assets = {
            "runtime.tar.gz": {"bytes": 11, "sha256": "1" * 64},
            "wheelhouse.tar": {"bytes": 22, "sha256": "2" * 64},
            "requirements.lock": {"bytes": 33, "sha256": "3" * 64},
        }
        write(
            self.manifest,
            {
                "assets": self.assets,
                "package_id": CHECKER.PACKAGE_ID,
                "schema_version": 1,
                "source_commit": self.source_commit,
            },
        )
        self.manifest_sha = CHECKER.digest(self.manifest)
        self.plan = {
            "evidence_allowlist": [
                f"admissions/{role}.json"
                for role in (CHECKER.CONTROL_ROLE, *self.roles)
            ],
            "jobs": [
                {"max_attempts": 1, "retry_on": [], "role": role}
                for role in (CHECKER.CONTROL_ROLE, *self.roles)
            ],
            "package_id": CHECKER.PACKAGE_ID,
            "run_id": CHECKER.RUN_ID,
            "source_commit": self.source_commit,
        }
        self.plan_id = hashlib.sha256(CHECKER.canonical(self.plan)).hexdigest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def attempt(
        self, role: str, job_id: str, state: str, *, passed: bool | None = None
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "attempt_index": 0,
            "job_id": job_id,
            "job_role": role,
            "state": state,
        }
        if passed is not None:
            value["passed"] = passed
            value["result"] = {
                "exit_code": 0 if passed else 1,
                "gates": {"job_local_cleanup": True},
                "state": "COMPLETED" if passed else "FAILED",
                "terminal": True,
            }
        return value

    def publish_job(
        self, role: str, attempt: dict[str, object], *, passed: bool
    ) -> None:
        write(
            self.publication / f"job-{role}.0.json",
            finalize(
                {
                    "attempt_index": 0,
                    "job_id": attempt["job_id"],
                    "job_role": role,
                    "package_id": CHECKER.PACKAGE_ID,
                    "passed": passed,
                    "result": attempt["result"],
                    "run_id": CHECKER.RUN_ID,
                }
            ),
        )

    def write_state(self, run_state: str, attempts: dict[str, object]) -> None:
        write(
            self.state,
            {
                "attempts": attempts,
                "current_plan_id": self.plan_id,
                "package_id": CHECKER.PACKAGE_ID,
                "plan_revisions": [
                    {"plan_id": self.plan_id, "revision": 0, "semantic": self.plan}
                ],
                "run_id": CHECKER.RUN_ID,
                "run_state": run_state,
                "source_commit": self.source_commit,
            },
        )

    def write_setup(self, role: str, attempt: dict[str, object]) -> Path:
        path = self.remote / "results" / role / "setup.json"
        identities = {
            "runtime_archive": {**self.assets["runtime.tar.gz"], "exists": True},
            "wheelhouse_archive": {**self.assets["wheelhouse.tar"], "exists": True},
            "requirements_lock": {**self.assets["requirements.lock"], "exists": True},
            "asset_manifest": {
                "bytes": self.manifest.stat().st_size,
                "exists": True,
                "sha256": self.manifest_sha,
            },
        }
        write(
            path,
            finalize(
                {
                    "authentication": {
                        "asset_identities_authenticated": True,
                        "control_plane_python_authenticated": True,
                        "execution_identity_authenticated": True,
                        "submission_admission_authenticated": True,
                    },
                    "cleanup": {
                        "pip_cache_deleted_before_science": True,
                        "wheelhouse_deleted_before_science": True,
                    },
                    "execution_identity": {
                        "asset_manifest_sha256": self.manifest_sha,
                        "host_python_path": "/usr/bin/python3.11",
                        "host_python_version": "Python 3.11.9",
                        "job_id": attempt["job_id"],
                        "node": "node03",
                        "owner_marker_sha256": "4" * 64,
                        "role": role,
                        "run_id": CHECKER.RUN_ID,
                        "source_commit": self.source_commit,
                        "submission_admission_authenticated": True,
                        "submission_admission_record_sha256": "5" * 64,
                    },
                    "exit_codes": {
                        "host_python_version": 0,
                        "pip_check": 0,
                        "pip_install": 0,
                        "runtime_version": 0,
                    },
                    "identities": identities,
                    "ready_for_science": True,
                    "stage": "ready-for-science",
                    "valid": True,
                }
            ),
        )
        return path

    def options(self, role: str, setups: list[str] | None = None) -> argparse.Namespace:
        return argparse.Namespace(
            asset_manifest=self.manifest,
            control_plane_python={
                "identity": {"bytes": 1024, "sha256": "6" * 64},
                "path": "/usr/bin/python3.11",
                "resolved_path": "/usr/bin/python3.11",
                "version": "3.11.9",
            },
            contract=self.contract,
            created_at="2026-07-19T00:00:00Z",
            output=self.remote / "admissions" / f"{role}.json",
            publication_dir=self.publication,
            remote_run_root=self.remote,
            role=role,
            setup=setups or [],
            toolkit_state=self.state,
        )

    def test_control_attempt_is_admitted_only_from_verified(self) -> None:
        self.write_state("VERIFIED", {})
        receipt, passed = CHECKER.check(self.options(CHECKER.CONTROL_ROLE))
        self.assertTrue(passed)
        self.assertTrue(CHECKER.authenticate_record(receipt))
        self.write_state("MATRIX_ACTIVE", {})
        _, passed = CHECKER.check(self.options(CHECKER.CONTROL_ROLE))
        self.assertFalse(passed)

    def test_wrong_control_plane_python_fails_closed(self) -> None:
        self.write_state("VERIFIED", {})
        options = self.options(CHECKER.CONTROL_ROLE)
        options.control_plane_python["path"] = "/usr/bin/python3"
        _, passed = CHECKER.check(options)
        self.assertFalse(passed)

    def test_admission_receipt_is_atomic_and_never_overwritten(self) -> None:
        path = self.remote / "admissions/test.json"
        CHECKER.atomic_create(path, {"value": 1})
        with self.assertRaises(FileExistsError):
            CHECKER.atomic_create(path, {"value": 2})
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"value": 1})

    def test_first_candidate_requires_passed_observed_control(self) -> None:
        control = self.attempt(CHECKER.CONTROL_ROLE, "1001", "RESULT_VALIDATED", passed=True)
        self.write_state("MATRIX_ACTIVE", {f"{CHECKER.CONTROL_ROLE}.0": control})
        self.publish_job(CHECKER.CONTROL_ROLE, control, passed=True)
        _, passed = CHECKER.check(self.options(self.roles[0]))
        self.assertTrue(passed)
        control["passed"] = False
        self.write_state("MATRIX_ACTIVE", {f"{CHECKER.CONTROL_ROLE}.0": control})
        _, passed = CHECKER.check(self.options(self.roles[0]))
        self.assertFalse(passed)

    def test_second_candidate_requires_exact_ready_first_setup(self) -> None:
        control = self.attempt(CHECKER.CONTROL_ROLE, "1001", "RESULT_VALIDATED", passed=True)
        first = self.attempt(self.roles[0], "1002", "SUBMITTED")
        attempts = {
            f"{CHECKER.CONTROL_ROLE}.0": control,
            f"{self.roles[0]}.0": first,
        }
        self.write_state("MATRIX_ACTIVE", attempts)
        self.publish_job(CHECKER.CONTROL_ROLE, control, passed=True)
        _, passed = CHECKER.check(self.options(self.roles[1]))
        self.assertFalse(passed)
        setup = self.write_setup(self.roles[0], first)
        _, passed = CHECKER.check(
            self.options(self.roles[1], [f"{self.roles[0]}={setup}"])
        )
        self.assertTrue(passed)

    def test_terminal_first_member_keeps_exact_setup_requirement(self) -> None:
        control = self.attempt(CHECKER.CONTROL_ROLE, "1001", "RESULT_VALIDATED", passed=True)
        first = self.attempt(self.roles[0], "1002", "RESULT_VALIDATED", passed=False)
        attempts = {
            f"{CHECKER.CONTROL_ROLE}.0": control,
            f"{self.roles[0]}.0": first,
        }
        self.write_state("MATRIX_ACTIVE", attempts)
        self.publish_job(CHECKER.CONTROL_ROLE, control, passed=True)
        self.publish_job(self.roles[0], first, passed=False)
        setup = self.write_setup(self.roles[0], first)
        _, passed = CHECKER.check(
            self.options(self.roles[1], [f"{self.roles[0]}={setup}"])
        )
        self.assertTrue(passed)

    def test_next_wave_requires_both_observed_cleanup_receipts(self) -> None:
        attempts: dict[str, object] = {}
        control = self.attempt(CHECKER.CONTROL_ROLE, "1001", "RESULT_VALIDATED", passed=True)
        attempts[f"{CHECKER.CONTROL_ROLE}.0"] = control
        self.publish_job(CHECKER.CONTROL_ROLE, control, passed=True)
        for index, role in enumerate(self.roles[:2], start=2):
            prior = self.attempt(role, str(1000 + index), "RESULT_VALIDATED", passed=False)
            attempts[f"{role}.0"] = prior
            self.publish_job(role, prior, passed=False)
        self.write_state("MATRIX_ACTIVE", attempts)
        _, passed = CHECKER.check(self.options(self.roles[2]))
        self.assertTrue(passed)
        missing = self.publication / f"job-{self.roles[1]}.0.json"
        missing.rename(missing.with_suffix(".absent"))
        _, passed = CHECKER.check(self.options(self.roles[2]))
        self.assertFalse(passed)


if __name__ == "__main__":
    unittest.main()
