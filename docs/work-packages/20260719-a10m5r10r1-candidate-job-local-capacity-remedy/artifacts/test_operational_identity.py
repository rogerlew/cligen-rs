#!/usr/bin/env python3
"""Self-tests for setup identities and bound predecessor evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]


def load(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


SETUP = load("setup_diagnostics", PACKAGE / "artifacts/jobs/setup_diagnostics.py")
BUILDER = load(
    "build_control_records", PACKAGE / "artifacts/jobs/build_control_records.py"
)


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class SetupIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="a10m5r10r1-setup-")
        self.root = Path(self.temporary.name)
        self.local = self.root / "job-local"
        for name in ("tmp", "cache", "torch-cache", "runtime/environment"):
            (self.local / name).mkdir(parents=True)
        self.runtime = self.root / "runtime.tar.gz"
        self.wheels = self.root / "wheelhouse.tar"
        self.requirements = self.root / "requirements.lock"
        self.runtime.write_bytes(b"runtime")
        self.wheels.write_bytes(b"wheels")
        self.requirements.write_bytes(b"requirements")
        self.source_commit = "f" * 40
        self.manifest = self.root / "asset-manifest.json"
        write(
            self.manifest,
            {
                "assets": {
                    self.runtime.name: SETUP.identity(self.runtime),
                    self.wheels.name: SETUP.identity(self.wheels),
                    self.requirements.name: SETUP.identity(self.requirements),
                },
                "source_commit": self.source_commit,
            },
        )
        self.admission = self.root / "admissions/test-role.json"
        admission = {
            "asset_manifest_sha256": SETUP.digest(self.manifest),
            "decision": "PASS",
            "gates": {"machine_admission": True},
            "record_type": "a10m5r10r1-submission-admission",
            "role": "test-role",
            "run_id": "a10m5r10r1-candidate-job-local-capacity-remedy-r0",
            "source_commit": self.source_commit,
            "valid": True,
        }
        admission["record_sha256"] = SETUP.record_hash(admission)
        write(self.admission, admission)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def options(self, output: Path) -> argparse.Namespace:
        return argparse.Namespace(
            admission_receipt=self.admission,
            asset_manifest=self.manifest,
            job_id="12345",
            job_local=self.local,
            node="node03",
            output=output,
            owner_marker_sha256="4" * 64,
            pip_check_exit=0,
            pip_install_exit=0,
            ready_for_science=True,
            requirements=self.requirements,
            role="test-role",
            run_root=self.root,
            run_id="a10m5r10r1-candidate-job-local-capacity-remedy-r0",
            runtime_archive=self.runtime,
            runtime_version_exit=0,
            stage="ready-for-science",
            wheel_archive=self.wheels,
        )

    def test_ready_receipt_authenticates_execution_assets_and_admission(self) -> None:
        output = self.root / "results/test-role/setup.json"
        SETUP.record(self.options(output))
        value = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(value["valid"])
        self.assertTrue(SETUP.authenticate_record(value))
        self.assertTrue(all(value["authentication"].values()))
        self.assertEqual(value["execution_identity"]["job_id"], "12345")

    def test_wrong_role_admission_fails_closed(self) -> None:
        admission = json.loads(self.admission.read_text(encoding="utf-8"))
        admission["role"] = "wrong-role"
        admission["record_sha256"] = SETUP.record_hash(admission)
        write(self.admission, admission)
        output = self.root / "results/test-role/setup.json"
        SETUP.record(self.options(output))
        value = json.loads(output.read_text(encoding="utf-8"))
        self.assertFalse(value["valid"])
        self.assertFalse(
            value["authentication"]["submission_admission_authenticated"]
        )

    def test_runtime_identity_drift_fails_closed(self) -> None:
        self.runtime.write_bytes(b"drift")
        output = self.root / "results/test-role/setup.json"
        SETUP.record(self.options(output))
        value = json.loads(output.read_text(encoding="utf-8"))
        self.assertFalse(value["valid"])
        self.assertFalse(value["authentication"]["asset_identities_authenticated"])


class PredecessorBindingTests(unittest.TestCase):
    def paths(self) -> argparse.Namespace:
        root = (
            REPO
            / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio"
            / "artifacts"
        )
        values = {
            "predecessor_r0_cleanup": root / "toolkit-recovered/cleanup.json",
            "predecessor_r0_operational_summary": root / "operational-summary.json",
            "predecessor_r0_resource_ledger": root / "resource-ledger.md",
            "predecessor_r0_terminal": root / "toolkit-recovered/terminal.json",
        }
        return argparse.Namespace(
            **values,
            **{f"{name}_sha256": BUILDER.digest(path) for name, path in values.items()},
        )

    def test_four_closed_r0_records_are_bound(self) -> None:
        result = BUILDER.predecessor_bundle(self.paths())
        self.assertEqual(
            set(result),
            {
                "cleanup_receipt",
                "operational_summary",
                "resource_ledger",
                "terminal_receipt",
            },
        )
        self.assertEqual(len({item["sha256"] for item in result.values()}), 4)

    def test_wrong_operator_supplied_hash_fails_closed(self) -> None:
        options = self.paths()
        options.predecessor_r0_operational_summary_sha256 = "0" * 64
        with self.assertRaises(RuntimeError):
            BUILDER.predecessor_bundle(options)

    def test_authority_and_plan_preserve_predecessor_and_admissions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="a10m5r10r1-builder-") as temporary:
            root = Path(temporary)
            (root / "job-local-capacity-contract.json").write_bytes(
                (PACKAGE / "artifacts/job-local-capacity-contract.json").read_bytes()
            )
            (root / "portfolio-contract.json").write_bytes(
                (
                    REPO
                    / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio"
                    / "artifacts/portfolio-contract.json"
                ).read_bytes()
            )
            write(
                root / "asset-manifest.json",
                {
                    "assets": {
                        "admission_checker.py": {"bytes": 1, "sha256": "1" * 64}
                    },
                    "package_id": BUILDER.PACKAGE_ID,
                    "source_commit": "f" * 40,
                },
            )
            authority_options = self.paths()
            authority_options.asset_root = root
            authority_options.output = root / "authority.json"
            authority_options.source_commit = "f" * 40
            authority_options.state_root = root / "state"
            BUILDER.authority(authority_options)
            authority = json.loads(authority_options.output.read_text(encoding="utf-8"))
            authority["authority_revision_sha256"] = "2" * 64
            write(authority_options.output, authority)
            plan_path = root / "plan.json"
            BUILDER.plan(
                argparse.Namespace(
                    asset_root=root,
                    authority=authority_options.output,
                    output=plan_path,
                    source_commit="f" * 40,
                )
            )
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(
                plan["predecessor_r0_evidence"], authority["predecessor_r0_evidence"]
            )
            self.assertIn(
                "asset-manifest.json",
                {item["logical_name"] for item in plan["assets"]},
            )
            self.assertTrue(
                all(
                    f"admissions/{job['role']}.json" in plan["evidence_allowlist"]
                    for job in plan["jobs"]
                )
            )


if __name__ == "__main__":
    unittest.main()
