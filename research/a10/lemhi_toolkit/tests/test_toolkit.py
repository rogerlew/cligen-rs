from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
import threading
import unittest
from pathlib import Path

from research.a10.lemhi_toolkit.adapters import FixtureAdapter, OpenSSHSlurmAdapter
from research.a10.lemhi_toolkit.cli import main
from research.a10.lemhi_toolkit.core import (
    Toolkit,
    ToolkitError,
    canonical_bytes,
    loads_strict,
    read_json,
    read_record,
    sha256_bytes,
    sha256_file,
    validate_archive,
    validate_relative_path,
    validate_shell_scalar,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PROFILE_PATH = REPOSITORY_ROOT / "research/a10/lemhi_toolkit/profiles/lemhi-v1.json"
PROVIDERS = [
    "research/a10/lemhi_toolkit/providers/transport-scp-v1.json",
    "research/a10/lemhi_toolkit/providers/scheduler-slurm-v1.json",
    "research/a10/lemhi_toolkit/providers/storage-ceph-v1.json",
    "research/a10/lemhi_toolkit/providers/accelerator-l40-v1.json",
]
NOW = "2026-07-17T18:00:00Z"


class ToolkitFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.script = self.assets / "job.sh"
        self.script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.profile = read_json(PROFILE_PATH)
        self.authority = {
            "allowed_roots": [str(self.assets)],
            "authority_id": "a10-toolkit-test",
            "confirmation_classification": "development-only",
            "package_id": "a10-toolkit-foundation",
            "resource_budget_id": "a10-toolkit-budget",
            "resource_ceiling_gpu_minutes": 90,
            "source_commit": "abcdef0",
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def plan(self, run_id: str, *, jobs: list[dict] | None = None) -> dict:
        selected_jobs = jobs or [
            {
                "cpus": 2,
                "expected_exit_code": 0,
                "gate_receipt": "evidence.json",
                "gpus": 1,
                "gres": "gpu:l40:1",
                "max_attempts": 2,
                "memory_mb": 1024,
                "partition": "icrews",
                "retry_on": ["gate-failed"],
                "role": "smoke",
                "script": "job.sh",
                "time_limit_minutes": 10,
            }
        ]
        for job in selected_jobs:
            job.setdefault("gate_receipt", "evidence.json")
        return {
            "assets": [{
                "bytes": self.script.stat().st_size,
                "license_provenance": "repository license with human-readable provenance",
                "local_path": str(self.script),
                "logical_name": "job.sh",
                "sha256": sha256_bytes(self.script.read_bytes()),
                "source_class": "repository-owned",
                "target_platform": self.profile["platform"],
            }],
            "authority_id": self.authority["authority_id"],
            "confirmation_classification": self.authority["confirmation_classification"],
            "evidence_allowlist": ["evidence.json", "slurm/smoke.0.out", "slurm/smoke.0.err", "slurm/positive.0.out", "slurm/positive.0.err", "slurm/negative.0.out", "slurm/negative.0.err"],
            "job_local_cleanup": "scheduler_purged",
            "jobs": selected_jobs,
            "package_id": self.authority["package_id"],
            "providers": PROVIDERS,
            "remote_run_root": f"runs/{run_id}",
            "required_capability_scope": "login",
            "resource_budget_id": self.authority["resource_budget_id"],
            "run_id": run_id,
            "source_commit": self.authority["source_commit"],
            "stop_rules": {"ambiguity": "stop", "gate_failure": "authorized-retry-only", "resource_ceiling": "stop"},
            "submission_mode": "operator-explicit",
            "target_platform": self.profile["platform"],
        }

    def toolkit(self, run_id: str = "run-one", *, scenario: dict | None = None, authority: dict | None = None, clock=None) -> Toolkit:
        adapter = FixtureAdapter(self.root / f"fixture-{run_id}", scenario)
        return Toolkit(
            self.root / "state",
            authority or self.authority,
            self.profile,
            run_id,
            adapter,
            clock=clock or (lambda: NOW),
            provider_root=REPOSITORY_ROOT,
        )

    def verified(self, toolkit: Toolkit, plan: dict) -> None:
        toolkit.doctor()
        toolkit.probe()
        toolkit.plan(plan)
        toolkit.prepare()
        toolkit.stage()
        toolkit.verify()


class FoundationAcceptance(ToolkitFixture):
    def test_complete_parallel_matrix_expected_nonzero_and_close(self) -> None:
        jobs = [
            {
                "cpus": 2, "expected_exit_code": 0, "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 2,
                "memory_mb": 1024, "partition": "icrews", "retry_on": ["gate-failed"], "role": "positive", "script": "job.sh", "time_limit_minutes": 10,
            },
            {
                "cpus": 2, "expected_exit_code": 7, "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1,
                "memory_mb": 1024, "partition": "icrews", "retry_on": [], "role": "negative", "script": "job.sh", "time_limit_minutes": 10,
            },
        ]
        toolkit = self.toolkit("matrix", scenario={"results": {"negative": {"exit_code": 7}}})
        self.verified(toolkit, self.plan("matrix", jobs=jobs))
        first = toolkit.submit("positive", 0)
        second = toolkit.submit("negative", 0)
        self.assertNotEqual(first, second)
        self.assertTrue(toolkit.observe("negative", 0)["passed"])
        self.assertTrue(toolkit.observe("positive", 0)["passed"])
        self.assertEqual(read_json(toolkit.private_path)["run_state"], "MATRIX_SETTLED")
        self.assertTrue(toolkit.collect()["download_promoted"])
        self.assertTrue(toolkit.clean()["remote_absent"])
        self.assertEqual(toolkit.close()["terminal"], "LEMHI-TOOLKIT-RUN-CLOSED")
        self.assertFalse(toolkit.private_path.parent.exists())
        publication = b"".join(path.read_bytes() for path in toolkit.publication_dir.glob("*.json"))
        self.assertNotIn(b"rogerlew.ui", publication)
        self.assertNotIn(str(self.root).encode(), publication)

    def test_retry_and_failed_gate_do_not_settle_early(self) -> None:
        scenario = {"results": {"smoke": {"gates": {"registered": False}}}}
        toolkit = self.toolkit("retry", scenario=scenario)
        self.verified(toolkit, self.plan("retry"))
        with self.assertRaisesRegex(ToolkitError, "PLAN_DRIFT"):
            toolkit.submit("smoke", 1)
        toolkit.submit("smoke", 0)
        self.assertFalse(toolkit.observe("smoke", 0)["passed"])
        self.assertEqual(read_json(toolkit.private_path)["run_state"], "MATRIX_ACTIVE")
        scenario["results"]["smoke"] = {"gates": {"registered": True}}
        toolkit.submit("smoke", 1)
        self.assertTrue(toolkit.observe("smoke", 1)["passed"])

    def test_exhausted_failed_role_settles_for_evidence_and_cleanup(self) -> None:
        jobs = self.plan("exhausted")["jobs"]
        jobs[0]["max_attempts"] = 1
        jobs[0]["retry_on"] = []
        toolkit = self.toolkit("exhausted", scenario={"results": {"smoke": {"gates": {"registered": False}}}})
        self.verified(toolkit, self.plan("exhausted", jobs=jobs))
        toolkit.submit("smoke", 0)
        self.assertFalse(toolkit.observe("smoke", 0)["passed"])
        self.assertEqual(read_json(toolkit.private_path)["run_state"], "MATRIX_SETTLED")
        self.assertTrue(toolkit.collect()["download_promoted"])
        self.assertTrue(toolkit.clean()["remote_absent"])

    def test_cancel_is_exact_and_requires_terminal_observation(self) -> None:
        toolkit = self.toolkit("cancel")
        self.verified(toolkit, self.plan("cancel"))
        job_id = toolkit.submit("smoke", 0)
        self.assertEqual(toolkit.cancel("smoke", 0)["job_id"], job_id)
        receipt = toolkit.observe("smoke", 0)
        self.assertFalse(receipt["passed"])
        self.assertEqual(receipt["result"]["state"], "CANCELLED")

    def test_missing_accounting_remains_unavailable(self) -> None:
        toolkit = self.toolkit("accounting")
        self.verified(toolkit, self.plan("accounting"))
        toolkit.submit("smoke", 0)
        result = toolkit.observe("smoke", 0)["result"]
        self.assertIsNone(result["actual_gpu_minutes"])
        self.assertEqual(result["accounting"], "unavailable")

    def test_masters_are_required_at_doctor_and_again_at_stage(self) -> None:
        scenario = {"masters": {"gateway": False, "target": False}}
        with self.assertRaisesRegex(ToolkitError, "AUTH_BOOTSTRAP_REQUIRED"):
            self.toolkit("cold", scenario=scenario).doctor()
        scenario = {"masters": {"gateway": True, "target": True}}
        toolkit = self.toolkit("expires", scenario=scenario)
        toolkit.doctor(); toolkit.probe(); toolkit.plan(self.plan("expires")); toolkit.prepare()
        scenario["masters"]["target"] = False
        with self.assertRaisesRegex(ToolkitError, "AUTH_BOOTSTRAP_REQUIRED"):
            toolkit.stage()

    def test_probe_never_allocates_and_scope_is_not_compute(self) -> None:
        with self.assertRaisesRegex(ToolkitError, "CAPABILITY_SCOPE_MISMATCH"):
            toolkit = self.toolkit("alloc-probe", scenario={"probe_allocates": True}); toolkit.doctor(); toolkit.probe()
        toolkit = self.toolkit("scope")
        toolkit.doctor(); toolkit.probe()
        plan = self.plan("scope"); plan["required_capability_scope"] = "compute"
        with self.assertRaisesRegex(ToolkitError, "CAPABILITY_SCOPE_MISMATCH"):
            toolkit.plan(plan)

    def test_stale_capability_and_platform_mismatch_fail_planning(self) -> None:
        current = [NOW]
        toolkit = self.toolkit("stale", clock=lambda: current[0])
        toolkit.doctor(); toolkit.probe(); current[0] = "2026-07-17T18:06:00Z"
        with self.assertRaisesRegex(ToolkitError, "CAPABILITY_STALE"):
            toolkit.plan(self.plan("stale"))
        current[0] = "2026-07-17T18:06:01Z"; self.assertEqual(toolkit.probe()["scope"], "login")
        toolkit = self.toolkit("mac", scenario={"platform": "macos-arm64"})
        toolkit.doctor(); toolkit.probe()
        with self.assertRaisesRegex(ToolkitError, "PLATFORM_MISMATCH"):
            toolkit.plan(self.plan("mac"))
        toolkit = self.toolkit("mac-asset"); toolkit.doctor(); toolkit.probe()
        plan = self.plan("mac-asset"); plan["assets"][0]["target_platform"] = "macos-arm64"
        with self.assertRaisesRegex(ToolkitError, "PLATFORM_MISMATCH"):
            toolkit.plan(plan)

    def test_provider_mismatch_and_failure_have_no_fallback(self) -> None:
        original = self.profile["provides"]["scheduler"]
        self.profile["provides"]["scheduler"] = "not-slurm"
        toolkit = self.toolkit("provider")
        toolkit.doctor(); toolkit.probe()
        with self.assertRaisesRegex(ToolkitError, "PLATFORM_MISMATCH"):
            toolkit.plan(self.plan("provider"))
        self.profile["provides"]["scheduler"] = original
        provider_root = self.root / "provider-root"; provider_root.mkdir()
        provider = read_json(REPOSITORY_ROOT / PROVIDERS[1])
        provider["name"] = "runtime-cp311-incompatible"
        provider["provider_class"] = "runtime"
        provider["requires"]["python_abi"] = "cp311"
        (provider_root / "runtime.json").write_text(json.dumps(provider), encoding="utf-8")
        toolkit = Toolkit(self.root / "state-runtime", self.authority, self.profile, "runtime-stack", FixtureAdapter(self.root / "fixture-runtime"), clock=lambda: NOW, provider_root=provider_root)
        toolkit.doctor(); toolkit.probe(); plan = self.plan("runtime-stack"); plan["providers"] = ["runtime.json"]
        with self.assertRaisesRegex(ToolkitError, "PLATFORM_MISMATCH"):
            toolkit.plan(plan)
        toolkit = self.toolkit("no-fallback", scenario={"stage_failure": True})
        toolkit.doctor(); toolkit.probe(); toolkit.plan(self.plan("no-fallback")); toolkit.prepare()
        with self.assertRaisesRegex(ToolkitError, "TRANSFER_INCOMPLETE"):
            toolkit.stage()
        self.assertEqual(read_json(toolkit.private_path)["run_state"], "PREPARED")

    def test_transfer_hash_and_download_promotion_fail_closed(self) -> None:
        toolkit = self.toolkit("upload-bad", scenario={"corrupt_upload": True})
        toolkit.doctor(); toolkit.probe(); toolkit.plan(self.plan("upload-bad")); toolkit.prepare()
        with self.assertRaisesRegex(ToolkitError, "TRANSFER_INCOMPLETE"):
            toolkit.stage()
        toolkit = self.toolkit("download-bad", scenario={"remote_evidence_sha256": "0" * 64})
        self.verified(toolkit, self.plan("download-bad")); toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
        with self.assertRaisesRegex(ToolkitError, "TRANSFER_INCOMPLETE"):
            toolkit.collect()

    def test_resource_budget_is_shared_across_runs(self) -> None:
        authority = dict(self.authority); authority["resource_ceiling_gpu_minutes"] = 10
        one = self.toolkit("budget-one", authority=authority); two = self.toolkit("budget-two", authority=authority)
        self.verified(one, self.plan("budget-one")); self.verified(two, self.plan("budget-two"))
        one.submit("smoke", 0)
        with self.assertRaisesRegex(ToolkitError, "RESOURCE_CEILING"):
            two.submit("smoke", 0)
        self.assertEqual(read_json(self.root / "fixture-budget-two/backend.json")["submit_calls"], 0)

    def test_concurrent_runs_cannot_double_spend_budget(self) -> None:
        authority = dict(self.authority); authority["resource_ceiling_gpu_minutes"] = 10
        one = self.toolkit("concurrent-one", authority=authority); two = self.toolkit("concurrent-two", authority=authority)
        self.verified(one, self.plan("concurrent-one")); self.verified(two, self.plan("concurrent-two"))
        barrier = threading.Barrier(3)
        outcomes = []
        def submit(toolkit):
            barrier.wait()
            try:
                outcomes.append(("job", toolkit.submit("smoke", 0)))
            except ToolkitError as error:
                outcomes.append(("error", error.code))
        threads = [threading.Thread(target=submit, args=(toolkit,)) for toolkit in (one, two)]
        for thread in threads: thread.start()
        barrier.wait()
        for thread in threads: thread.join()
        self.assertEqual(sum(kind == "job" for kind, _ in outcomes), 1)
        self.assertIn(next(value for kind, value in outcomes if kind == "error"), {"RUN_LOCKED", "RESOURCE_CEILING"})

    def test_response_lost_reconciles_once_or_stays_ambiguous(self) -> None:
        scenario = {"lose_next_response": True}
        toolkit = self.toolkit("reconcile", scenario=scenario); self.verified(toolkit, self.plan("reconcile"))
        self.assertTrue(toolkit.submit("smoke", 0).isdigit())
        self.assertEqual(read_json(self.root / "fixture-reconcile/backend.json")["submit_calls"], 1)
        toolkit = self.toolkit("ambiguous", scenario={"lose_next_response": True, "reconcile_matches": []})
        self.verified(toolkit, self.plan("ambiguous"))
        with self.assertRaisesRegex(ToolkitError, "SUBMISSION_OUTCOME_UNKNOWN"):
            toolkit.submit("smoke", 0)
        self.assertEqual(read_json(self.root / "fixture-ambiguous/backend.json")["submit_calls"], 1)

    def test_run_and_budget_locks_reject_concurrent_writer(self) -> None:
        toolkit = self.toolkit("locked")
        toolkit.run_lock.mkdir(parents=True)
        with self.assertRaisesRegex(ToolkitError, "RUN_LOCKED"):
            toolkit.doctor()

    def test_amendment_preserves_started_work_and_budget(self) -> None:
        jobs = self.plan("amend")["jobs"] + [{
            "cpus": 2, "expected_exit_code": 0, "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1,
            "memory_mb": 1024, "partition": "icrews", "retry_on": [], "role": "later", "script": "job.sh", "time_limit_minutes": 10,
        }]
        toolkit = self.toolkit("amend"); plan = self.plan("amend", jobs=jobs); self.verified(toolkit, plan)
        toolkit.submit("smoke", 0)
        replacement = json.loads(json.dumps(plan)); replacement["jobs"][1]["memory_mb"] = 2048
        new_id = toolkit.amend(replacement, "increase memory for unstarted role", ["jobs"])
        state = read_json(toolkit.private_path)
        self.assertEqual(state["attempts"]["smoke.0"]["plan_id"], state["plan_revisions"][0]["plan_id"])
        self.assertEqual(state["current_plan_id"], new_id)
        bad = json.loads(json.dumps(replacement)); bad["jobs"][0]["memory_mb"] = 4096
        with self.assertRaisesRegex(ToolkitError, "PLAN_DRIFT"):
            toolkit.amend(bad, "mutate started role", ["jobs"])
        ledger = read_json(toolkit.ledger_path)
        self.assertEqual({entry["token"] for entry in ledger["entries"]}, {state["attempts"]["smoke.0"]["token"]})
        self.assertEqual(ledger["entries"][-1]["status"], "submitted")

    def test_sanitization_and_cleanup_safety(self) -> None:
        toolkit = self.toolkit("sanitize", scenario={"evidence": {"path": "/Users/roger/private"}})
        self.verified(toolkit, self.plan("sanitize")); toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
        with self.assertRaisesRegex(ToolkitError, "SANITIZATION_FAILED"):
            toolkit.collect()
        toolkit.adapter.scenario["evidence"] = {"classification": "synthetic", "verdict": "PASS"}
        self.assertEqual(toolkit.collect()["record_type"], "collection_receipt")
        self.assertTrue((toolkit.run_dir / "private/quarantine.failed-1/evidence.json").is_file())
        toolkit = self.toolkit("cleanup-race", scenario={"replace_before_cleanup": True})
        self.verified(toolkit, self.plan("cleanup-race")); toolkit.submit("smoke", 0); toolkit.observe("smoke", 0); toolkit.collect()
        with self.assertRaisesRegex(ToolkitError, "CLEANUP_TARGET_INVALID"):
            toolkit.clean()
        toolkit = self.toolkit("cleanup-unmarked")
        plan = self.plan("cleanup-unmarked"); self.verified(toolkit, plan); toolkit.submit("smoke", 0); toolkit.observe("smoke", 0); toolkit.collect()
        (toolkit.adapter._run_root(read_json(toolkit.private_path)["plan_revisions"][0]["semantic"]) / ".lemhi-toolkit-owner.json").unlink()
        with self.assertRaisesRegex(ToolkitError, "CLEANUP_TARGET_INVALID"):
            toolkit.clean()
        toolkit = self.toolkit("cleanup-symlink")
        plan = self.plan("cleanup-symlink"); self.verified(toolkit, plan); toolkit.submit("smoke", 0); toolkit.observe("smoke", 0); toolkit.collect()
        semantic = read_json(toolkit.private_path)["plan_revisions"][0]["semantic"]
        remote = toolkit.adapter._run_root(semantic); moved = remote.with_name(remote.name + "-moved"); remote.rename(moved); remote.symlink_to(moved)
        with self.assertRaisesRegex(ToolkitError, "CLEANUP_TARGET_INVALID"):
            toolkit.clean()
        toolkit = self.toolkit("purge-missing", scenario={"job_local_cleanup": "unknown"})
        self.verified(toolkit, self.plan("purge-missing")); toolkit.submit("smoke", 0); toolkit.observe("smoke", 0); toolkit.collect()
        with self.assertRaisesRegex(ToolkitError, "CLEANUP_INCOMPLETE"):
            toolkit.clean()

    def test_cli_executes_production_command_path(self) -> None:
        authority = self.root / "authority.json"; authority.write_text(json.dumps(self.authority), encoding="utf-8")
        arguments = ["--state-root", str(self.root / "cli-state"), "--authority", str(authority), "--profile", str(PROFILE_PATH), "--provider-root", str(REPOSITORY_ROOT), "--run-id", "cli-run", "--adapter", "fixture", "--fixture-root", str(self.root / "cli-fixture"), "doctor"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(arguments), 0)


class SerializationAndFirewall(ToolkitFixture):
    def test_canonical_a10_configuration_binds_all_repository_inputs(self) -> None:
        path = REPOSITORY_ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v1.json"
        record = read_json(path)
        self.assertEqual(record["configuration_id"], "lemhi-a10-py311-l40-v1")
        self.assertEqual(record["configuration_status"], "current-canonical")
        recorded = record.pop("configuration_semantic_sha256")
        self.assertEqual(sha256_bytes(canonical_bytes(record)), recorded)
        pinned = [record["toolkit_profile"], *record["provider_stack"]]
        pinned.extend((record["framework"]["requirements_lock"], record["framework"]["wheel_manifest"]))
        pinned.append({
            "path": record["evidence"]["gate_receipt_path"],
            "sha256": record["evidence"]["gate_receipt_sha256"],
        })
        for item in pinned:
            target = REPOSITORY_ROOT / item["path"]
            self.assertTrue(target.is_file() and not target.is_symlink())
            self.assertEqual(sha256_file(target), item["sha256"])
            if "bytes" in item:
                self.assertEqual(target.stat().st_size, item["bytes"])

    def test_jcs_unicode_escaping_duplicates_and_history(self) -> None:
        value = {"\U0001f600": "line\nquote\"", "\ue000": 1, "a": [True, None]}
        expected = '{"a":[true,null],"😀":"line\\nquote\\\"","":1}'.encode()
        self.assertEqual(canonical_bytes(value), expected)
        self.assertEqual(sha256_bytes(canonical_bytes(value)), sha256_bytes(expected))
        with self.assertRaisesRegex(ToolkitError, "INVALID_JSON"):
            loads_strict('{"a":1,"a":2}')
        with self.assertRaisesRegex(ToolkitError, "INVALID_JSON"):
            loads_strict('{"a":1.0}')
        toolkit = self.toolkit("history"); toolkit.doctor()
        receipt = toolkit.publication_dir / "doctor.json"; before = receipt.read_bytes()
        self.assertEqual(read_record(receipt)["producer_version"], "lemhi-toolkit-foundation-1")
        self.assertEqual(receipt.read_bytes(), before)

    def test_shell_and_path_injection_are_rejected(self) -> None:
        for value in ("-option", "$(id)", "${HOME}", "a\nb", "`id`", "x;rm", "x|id", "x&y", "x y", "x'quote"):
            with self.subTest(value=value), self.assertRaisesRegex(ToolkitError, "ALLOWLIST_VIOLATION"):
                validate_shell_scalar(value, "fixture")
        for value in ("../secret", "/absolute", "a//b", "a/./b", "*.txt"):
            with self.subTest(value=value), self.assertRaisesRegex(ToolkitError, "ALLOWLIST_VIOLATION"):
                validate_relative_path(value, "fixture")

    def test_symlink_and_hardlink_assets_are_rejected_before_hashing(self) -> None:
        symlink = self.assets / "link.sh"; symlink.symlink_to(self.script)
        plan = self.plan("links"); plan["assets"][0]["local_path"] = str(symlink)
        toolkit = self.toolkit("links"); toolkit.doctor(); toolkit.probe(); toolkit.plan(plan)
        with self.assertRaisesRegex(ToolkitError, "ALLOWLIST_VIOLATION"):
            toolkit.prepare()
        hardlink = self.assets / "hard.sh"; os.link(self.script, hardlink)
        plan = self.plan("hard"); plan["assets"][0]["local_path"] = str(hardlink)
        toolkit = self.toolkit("hard"); toolkit.doctor(); toolkit.probe(); toolkit.plan(plan)
        with self.assertRaisesRegex(ToolkitError, "ALLOWLIST_VIOLATION"):
            toolkit.prepare()

    def test_archive_firewall_rejects_parent_links_devices_and_setid(self) -> None:
        cases = []
        for name, configure in (
            ("parent", lambda item: setattr(item, "name", "../secret")),
            ("link", lambda item: setattr(item, "type", tarfile.SYMTYPE)),
            ("device", lambda item: setattr(item, "type", tarfile.CHRTYPE)),
            ("setid", lambda item: setattr(item, "mode", 0o4755)),
            ("owner", lambda item: setattr(item, "uid", 501)),
        ):
            archive = self.root / f"{name}.tar"
            with tarfile.open(archive, "w") as stream:
                item = tarfile.TarInfo("safe.txt"); item.size = 1; item.uid = 0; item.gid = 0; item.mode = 0o600
                configure(item); stream.addfile(item, io.BytesIO(b"x"))
            cases.append(archive)
        for archive in cases:
            with self.subTest(archive=archive.name), self.assertRaisesRegex(ToolkitError, "ARCHIVE_UNSAFE"):
                validate_archive(archive, max_files=10, max_bytes=100)
        safe = self.root / "not-allowed.tar"
        with tarfile.open(safe, "w") as stream:
            item = tarfile.TarInfo("protected.txt"); item.size = 1; item.uid = 0; item.gid = 0; item.mode = 0o600
            stream.addfile(item, io.BytesIO(b"x"))
        with self.assertRaisesRegex(ToolkitError, "ARCHIVE_UNSAFE"):
            validate_archive(safe, max_files=10, max_bytes=100, allowed_members={"evidence.json"})

    def test_archive_firewall_applies_aggregate_and_member_byte_ceilings_pre_extract(self) -> None:
        archive = self.root / "volume.tar"
        with tarfile.open(archive, "w") as stream:
            for name in ("one.bin", "two.bin"):
                item = tarfile.TarInfo(name)
                item.size = 6
                item.uid = item.gid = 0
                item.mode = 0o600
                stream.addfile(item, io.BytesIO(b"123456"))
        with self.assertRaisesRegex(ToolkitError, "member byte ceiling"):
            validate_archive(
                archive,
                max_files=2,
                max_bytes=12,
                max_file_bytes=5,
            )
        with self.assertRaisesRegex(ToolkitError, "expansion ceiling"):
            validate_archive(
                archive,
                max_files=2,
                max_bytes=11,
                max_file_bytes=6,
            )


class RecordingRunner:
    def __init__(self, root: Path):
        self.calls = []
        archive = root / "remote-evidence.tar"
        with tarfile.open(archive, "w") as stream:
            item = tarfile.TarInfo("slurm/smoke.0.out"); item.size = 5; item.uid = 0; item.gid = 0; item.mode = 0o600
            stream.addfile(item, io.BytesIO(b"PASS\n"))
        self.archive = archive.read_bytes()

    def run(self, arguments, *, stdin=None, timeout=60):
        self.calls.append((list(arguments), stdin, timeout))
        output = b""
        if arguments[0] == "ssh" and "-O" in arguments:
            output = b"Master running\n"
        elif stdin and b"posix-login-probe" in stdin:
            output = b'{"scope":"login","observation_method":"fake","platform":"linux-x86_64-glibc","scheduler":"slurm","unavailable":[],"untested":["compute"]}\n'
        elif stdin and b"exec sbatch" in stdin:
            output = b"1000\n"
        elif stdin and b"squeue -h" in stdin:
            output = b"1000\n"
        elif stdin and b"ElapsedRaw" in stdin:
            output = b'{"terminal":true,"state":"COMPLETED","exit_code":0,"elapsed_seconds":61,"gates":{"scheduler_terminal":true},"actual_gpu_minutes":null,"accounting":"available"}\n'
        elif stdin and b'gate_receipt=$3' in stdin:
            output = b'{"gates":{"runtime":true,"framework":true}}\n'
        elif stdin and b"tar --format" in stdin:
            output = json.dumps({"bytes": len(self.archive), "logical_name": "evidence.tar", "sha256": sha256_bytes(self.archive)}, separators=(",", ":")).encode()
        elif arguments[0] == "scp" and arguments[-1].endswith(".part") and arguments[-2].startswith("lemhi:"):
            Path(arguments[-1]).write_bytes(self.archive)
        elif stdin and b"REMOTE_ABSENT" in stdin:
            output = b"REMOTE_ABSENT\n"
        return subprocess.CompletedProcess(arguments, 0, output, b"")


class LiveAdapterCommandPaths(ToolkitFixture):
    def test_all_live_operations_use_fixed_batch_commands(self) -> None:
        runner = RecordingRunner(self.root)
        adapter = OpenSSHSlurmAdapter(REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote", runner)
        plan = self.plan("live")
        job = plan["jobs"][0]
        prepared = [{"logical_name": "job.sh", "local_path": str(self.script), "bytes": self.script.stat().st_size, "sha256": sha256_bytes(self.script.read_bytes())}]
        adapter.check_masters(self.profile)
        self.assertEqual(adapter.probe(self.profile)["scope"], "login")
        self.assertTrue(adapter.stage(self.profile, plan, prepared)[0]["promoted"])
        adapter.verify(self.profile, plan, prepared)
        job = dict(job); job["attempt_index"] = 0
        self.assertEqual(adapter.submit(self.profile, plan, job, "a" * 32), "1000")
        self.assertEqual(adapter.reconcile(self.profile, "a" * 32), ["1000"])
        self.assertTrue(adapter.observe(self.profile, plan, job, "1000")["terminal"])
        self.assertTrue(adapter.cancel(self.profile, "1000")["acknowledged"])
        quarantine = self.root / "quarantine"; quarantine.mkdir()
        collection = adapter.collect(self.profile, plan, quarantine)
        self.assertTrue(collection["download_promoted"])
        self.assertEqual(collection["sanitization_policy"], "lemhi-evidence-v1")
        quarantine_v2 = self.root / "quarantine-v2"; quarantine_v2.mkdir()
        profile_v2 = {**self.profile, "provider_api_version": 2}
        collection_v2 = adapter.collect(profile_v2, plan, quarantine_v2)
        self.assertEqual(collection_v2["sanitization_policy"], "lemhi-evidence-projection-5")
        self.assertTrue(adapter.clean(self.profile, plan)["remote_absent"])
        flattened = [argument for arguments, _, _ in runner.calls for argument in arguments]
        self.assertIn("-oBatchMode=yes", flattened)
        self.assertNotIn("-oBatchMode=no", flattened)
        self.assertTrue(all(arguments[0] in {"ssh", "scp"} for arguments, _, _ in runner.calls))

    def test_cancelled_live_job_settles_without_gate_receipt(self) -> None:
        class CancelledRunner(RecordingRunner):
            def run(self, arguments, *, stdin=None, timeout=60):
                if stdin and b"ElapsedRaw" in stdin:
                    output = b'{"terminal":true,"state":"CANCELLED","exit_code":0,"elapsed_seconds":519,"node":"node03","accounting":"available"}\n'
                    self.calls.append((list(arguments), stdin, timeout))
                    return subprocess.CompletedProcess(arguments, 0, output, b"")
                return super().run(arguments, stdin=stdin, timeout=timeout)

        runner = CancelledRunner(self.root)
        adapter = OpenSSHSlurmAdapter(
            REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote", runner
        )
        plan = self.plan("cancelled-live")
        job = {**plan["jobs"][0], "attempt_index": 0}
        observed = adapter.observe(self.profile, plan, job, "1058096")
        self.assertEqual(observed["state"], "CANCELLED")
        self.assertEqual(observed["actual_gpu_minutes"], 9)
        self.assertNotIn("gates", observed)
        self.assertFalse(
            any(stdin and b"gate_receipt=$3" in stdin for _, stdin, _ in runner.calls)
        )


if __name__ == "__main__":
    unittest.main()
