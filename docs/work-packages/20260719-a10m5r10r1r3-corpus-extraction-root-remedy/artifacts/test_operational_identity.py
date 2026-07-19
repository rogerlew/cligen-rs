#!/usr/bin/env python3
"""Self-tests for setup identities and bound predecessor evidence."""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(REPO))

from research.a10.lemhi_toolkit.cli import main as toolkit_main


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
CORPUS = load("verify_corpus_layout", PACKAGE / "artifacts/verify_corpus_layout.py")
FREEZE = load("verify_freeze", PACKAGE / "artifacts/verify_freeze.py")


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class SetupIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="a10m5r10r1r3-setup-")
        self.host_python_patcher = mock.patch.object(
            SETUP,
            "host_python_identity",
            return_value={"bytes": 1024, "exists": True, "sha256": "6" * 64},
        )
        self.host_python_patcher.start()
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
            "record_type": "a10m5r10r1r3-submission-admission",
            "role": "test-role",
            "run_id": "a10m5r10r1r3-corpus-extraction-root-remedy-r0",
            "source_commit": self.source_commit,
            "valid": True,
        }
        admission["record_sha256"] = SETUP.record_hash(admission)
        write(self.admission, admission)

    def tearDown(self) -> None:
        self.host_python_patcher.stop()
        self.temporary.cleanup()

    def options(self, output: Path) -> argparse.Namespace:
        return argparse.Namespace(
            admission_receipt=self.admission,
            asset_manifest=self.manifest,
            job_id="12345",
            job_local=self.local,
            host_python_path=str(self.local / "runtime/cpython/bin/python3"),
            host_python_version="Python 3.11.9",
            host_python_version_exit=0,
            node="node03",
            output=output,
            owner_marker_sha256="4" * 64,
            pip_check_exit=0,
            pip_install_exit=0,
            ready_for_science=True,
            requirements=self.requirements,
            role="test-role",
            run_root=self.root,
            run_id="a10m5r10r1r3-corpus-extraction-root-remedy-r0",
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


class PortableBootstrapTests(unittest.TestCase):
    def test_runtime_extraction_precedes_compute_python(self) -> None:
        source = (
            PACKAGE / "artifacts/jobs/bootstrap_environment.sh"
        ).read_text(encoding="utf-8")
        extraction = source.index(
            "if run_pre_python_logged runtime-extract tar -xzf"
        )
        version = source.index(
            'if run_pre_python_logged runtime-version "$host_python" --version'
        )
        diagnostics = source.index(
            '"$runtime_root/bin/python3" "$run_root/setup_diagnostics.py" record'
        )
        inline_check = source.index('"$runtime_root/bin/python3" -c')
        self.assertLess(extraction, version)
        self.assertLess(version, diagnostics)
        self.assertLess(diagnostics, inline_check)
        self.assertNotIn("/usr/bin/python3", source)

    def test_terminal_finalizers_parse_as_python36(self) -> None:
        for name in ("job-control-materialization.sh", "job-common-candidate.sh"):
            source = (PACKAGE / "artifacts/jobs" / name).read_text(encoding="utf-8")
            snippets = source.split("<<'PY'\n")[1:]
            self.assertEqual(len(snippets), 2, name)
            self.assertEqual(source.count("/usr/bin/python3 -"), 2, name)
            self.assertNotIn("/usr/bin/python3.11", source)
            for snippet in snippets:
                code = snippet.split("\nPY", 1)[0]
                self.assertNotIn("from __future__", code)
                ast.parse(code, filename=name, feature_version=(3, 6))

    def test_missing_runtime_publishes_minimal_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="a10m5r10r1r3-missing-runtime-") as temporary:
            root = Path(temporary)
            run_root = root / BUILDER.RUN_ID
            run_root.mkdir()
            jobs = PACKAGE / "artifacts/jobs"
            for name in (
                "job-control-materialization.sh",
                "run_control.sh",
                "bootstrap_environment.sh",
                "setup_diagnostics.py",
            ):
                shutil.copy2(jobs / name, run_root / name)
                (run_root / name).chmod(0o700)
            supervisor = run_root / "supervise-v2.sh"
            supervisor.write_text(
                "#!/bin/sh\n"
                "set -u\n"
                "attempt_root=$1\n"
                "durable=$3\n"
                "shift 3\n"
                "set +e\n"
                '"$@"\n'
                "status=$?\n"
                "set -e\n"
                "printf '{\"application_exit\":%s}\\n' \"$status\" >\"$durable\"\n"
                'rm -rf -- "$attempt_root"\n'
                'exit "$status"\n',
                encoding="utf-8",
            )
            supervisor.chmod(0o700)
            (run_root / "admissions").mkdir()
            write(run_root / "admissions/control-materialization.json", {})
            write(
                run_root / "asset-manifest.json",
                {"assets": {}, "source_commit": "f" * 40},
            )
            tool_bin = root / "bin"
            tool_bin.mkdir()
            stat = tool_bin / "stat"
            stat.write_text("#!/bin/sh\nprintf '%s\\n' 1\n", encoding="utf-8")
            stat.chmod(0o700)
            temporary_root = root / "job-tmp"
            temporary_root.mkdir()
            environment = {
                **os.environ,
                "PATH": f"{tool_bin}:/sbin:/usr/bin:/bin",
                "SLURM_JOB_ID": "12345",
                "SLURMD_NODENAME": "test-node",
                "TMPDIR": str(temporary_root),
            }
            result = subprocess.run(
                ("./job-control-materialization.sh",),
                cwd=run_root,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            gate = json.loads(
                (
                    run_root
                    / "results/control-materialization/evidence.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(gate["run_id"], BUILDER.RUN_ID)
            self.assertEqual(gate["job_id"], "12345")
            self.assertEqual(gate["failure_stage"], "setup-not-started")
            self.assertFalse(gate["gates"]["portable_runtime_available"])
            self.assertTrue(gate["gates"]["job_local_cleanup"])
            self.assertTrue(all(isinstance(value, bool) for value in gate["gates"].values()))
            self.assertFalse(gate["valid"])
            self.assertEqual(gate["verdict"], "FAIL")

    def test_oversized_pre_python_failure_log_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="a10m5r10r1r3-large-log-") as temporary:
            root = Path(temporary)
            run_root = root / BUILDER.RUN_ID
            run_root.mkdir()
            bootstrap = run_root / "bootstrap_environment.sh"
            shutil.copy2(
                PACKAGE / "artifacts/jobs/bootstrap_environment.sh", bootstrap
            )
            bootstrap.chmod(0o700)
            archive_path = run_root / "runtime.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                blocker = tarfile.TarInfo("root/blocker")
                blocker.size = 1
                archive.addfile(blocker, io.BytesIO(b"x"))
                for index in range(4000):
                    item = tarfile.TarInfo(
                        f"root/blocker/child-{index:04d}-cannot-be-created"
                    )
                    item.size = 1
                    archive.addfile(item, io.BytesIO(b"x"))
            output = run_root / "results/control-materialization"
            job_local = root / "job-local"
            result = subprocess.run(
                (
                    "./bootstrap_environment.sh",
                    str(job_local),
                    str(output),
                    BUILDER.RUN_ID,
                    "control-materialization",
                    "12345",
                    "test-node",
                    "4" * 64,
                    str(run_root / "admissions/control-materialization.json"),
                ),
                cwd=run_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            setup_log = output / "setup.log"
            self.assertEqual(setup_log.stat().st_size, 65536)
            self.assertNotIn(str(run_root), setup_log.read_text(errors="replace"))
            self.assertNotIn(str(job_local), setup_log.read_text(errors="replace"))


class CorpusExtractionRootTests(unittest.TestCase):
    REQUIRED = (
        "corpus/artifacts/offline-transfer-manifest-v1.json",
        "corpus/artifacts/normalization-statistics-v1.json",
        "corpus/artifacts/normalized-manifest-v1.json",
    )

    def make_archive(self, path: Path) -> None:
        with tarfile.open(path, "w:") as archive:
            for name in self.REQUIRED:
                payload = b"{}\n"
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))

    def test_old_destination_nests_and_fixed_destination_exposes_corpus(self) -> None:
        with tempfile.TemporaryDirectory(prefix="a10m5r10r1r3-corpus-root-") as temporary:
            root = Path(temporary)
            archive = root / "corpus.tar"
            self.make_archive(archive)
            old_job_local = root / "old-job-local"
            (old_job_local / "corpus").mkdir(parents=True)
            subprocess.run(
                ("tar", "-xf", str(archive), "-C", str(old_job_local / "corpus")),
                check=True,
                capture_output=True,
            )
            self.assertFalse(
                (old_job_local / "corpus/artifacts/offline-transfer-manifest-v1.json").exists()
            )
            self.assertTrue(
                (
                    old_job_local
                    / "corpus/corpus/artifacts/offline-transfer-manifest-v1.json"
                ).is_file()
            )

            fixed_job_local = root / "fixed-job-local"
            (fixed_job_local / "corpus").mkdir(parents=True)
            subprocess.run(
                ("tar", "-xf", str(archive), "-C", str(fixed_job_local)),
                check=True,
                capture_output=True,
            )
            self.assertTrue(
                (
                    fixed_job_local
                    / "corpus/artifacts/offline-transfer-manifest-v1.json"
                ).is_file()
            )
            self.assertFalse((fixed_job_local / "corpus/corpus").exists())
            layout = CORPUS.inspect_layout(archive)
            self.assertEqual(layout["sole_top_level_prefix"], "corpus")
            self.assertTrue(layout["all_members_regular"])
            self.assertFalse(layout["absolute_paths_allowed"])
            self.assertFalse(layout["parent_components_allowed"])

    def test_both_wrappers_have_only_normalized_corpus_target_delta(self) -> None:
        FREEZE.verify_two_file_corpus_delta()

    def test_authority_preflight_rejects_unpinned_corpus(self) -> None:
        with tempfile.TemporaryDirectory(prefix="a10m5r10r1r3-corpus-pin-") as temporary:
            root = Path(temporary)
            archive = root / "corpus.tar"
            self.make_archive(archive)
            write(
                root / "asset-manifest.json",
                {
                    "assets": {"corpus.tar": CORPUS.identity(archive)},
                    "package_id": BUILDER.PACKAGE_ID,
                },
            )
            with self.assertRaises(RuntimeError):
                BUILDER.verify_corpus_asset_root(root)

    def test_authority_rejects_coordinated_pin_archive_manifest_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="a10m5r10r1r3-pin-drift-") as temporary:
            root = Path(temporary)
            fake_package = root / "package"
            altered_pin = fake_package / "artifacts/corpus-layout-pin.json"
            asset_root = root / "assets"
            archive = asset_root / "corpus.tar"
            asset_root.mkdir()
            self.make_archive(archive)
            archive_identity = CORPUS.identity(archive)
            write(
                altered_pin,
                {
                    "archive": archive_identity,
                    "layout": CORPUS.inspect_layout(archive),
                    "package_id": BUILDER.PACKAGE_ID,
                    "schema_version": 1,
                },
            )
            write(
                asset_root / "asset-manifest.json",
                {
                    "assets": {"corpus.tar": archive_identity},
                    "package_id": BUILDER.PACKAGE_ID,
                },
            )
            options = argparse.Namespace(
                asset_root=asset_root,
                output=root / "authority.json",
                source_commit="f" * 40,
                state_root=root / "state",
            )
            with (
                mock.patch.object(BUILDER, "PACKAGE", fake_package),
                mock.patch.object(BUILDER, "CORPUS_LAYOUT_PIN", altered_pin),
                self.assertRaisesRegex(
                    RuntimeError, "corpus layout pin byte identity drift"
                ),
            ):
                BUILDER.authority(options)


class PredecessorBindingTests(unittest.TestCase):
    def source_commit(self) -> str:
        result = BUILDER.subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=REPO,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_all_operational_holds_and_toolkit_hardening_are_bound(self) -> None:
        result = BUILDER.predecessor_bundle()
        self.assertEqual(
            set(result["predecessors"]),
            {
                "a10m5r10r1r2_corpus_root_hold",
                "a10m5r10r1r1_compute_python_hold",
                "a10m5r10r1_operational_hold",
                "a10m5o1r2_toolkit_hardening",
            },
        )
        self.assertEqual(
            result["predecessors"]["a10m5r10r1r2_corpus_root_hold"]["terminal"],
            "HOLD-A10M5R10R1R2-CORPUS-ROOT-NESTING",
        )
        self.assertEqual(
            result["predecessors"]["a10m5r10r1r1_compute_python_hold"]["terminal"],
            "HOLD-A10M5R10R1R1-COMPUTE-PYTHON311-ABSENT",
        )
        self.assertEqual(
            result["predecessors"]["a10m5r10r1_operational_hold"]["terminal"],
            "HOLD-A10M5R10R1-PYTHON311-CONTROL-PLANE",
        )

    def test_predecessor_manifest_identity_drift_fails_closed(self) -> None:
        with mock.patch.object(BUILDER, "PREDECESSOR_MANIFEST_SHA256", "0" * 64):
            with self.assertRaises(RuntimeError):
                BUILDER.predecessor_bundle()

    def test_toolkit_ancestry_and_empty_diff_are_proved(self) -> None:
        proof = BUILDER.toolkit_ancestry(self.source_commit())
        self.assertTrue(proof["hardening_commit_is_ancestor"])
        self.assertTrue(proof["diff_from_hardening_commit_empty"])

    def test_unknown_source_commit_fails_toolkit_proof(self) -> None:
        with self.assertRaises(RuntimeError):
            BUILDER.toolkit_ancestry("f" * 40)

    def test_authority_and_plan_preserve_predecessor_and_admissions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="a10m5r10r1r3-builder-") as temporary:
            root = Path(temporary)
            source_commit = self.source_commit()
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
                    "source_commit": source_commit,
                },
            )
            authority_options = argparse.Namespace(
                asset_root=root,
                output=root / "authority.json",
                source_commit=source_commit,
                state_root=root / "state",
            )
            with mock.patch.object(BUILDER, "verify_corpus_asset_root") as preflight:
                BUILDER.authority(authority_options)
                preflight.assert_called_once_with(root)
            initialized_authority = root / "initialized-authority.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    toolkit_main(
                        [
                            "--authority",
                            str(authority_options.output),
                            "initialize-authority",
                            "--output",
                            str(initialized_authority),
                        ]
                    ),
                    0,
                )
            authority = json.loads(
                initialized_authority.read_text(encoding="utf-8")
            )
            self.assertNotIn("genesis_authorized", authority)
            self.assertEqual(authority["predecessor_package_evidence"], BUILDER.predecessor_bundle())
            plan_path = root / "plan.json"
            with mock.patch.object(BUILDER, "verify_corpus_asset_root") as preflight:
                BUILDER.plan(
                    argparse.Namespace(
                        asset_root=root,
                        authority=initialized_authority,
                        output=plan_path,
                        source_commit=source_commit,
                    )
                )
                preflight.assert_called_once_with(root)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(
                plan["predecessor_package_evidence"],
                authority["predecessor_package_evidence"],
            )
            self.assertEqual(
                plan["toolkit_hardening_proof"], authority["toolkit_hardening_proof"]
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
