from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from research.a10.lemhi_toolkit.adapters import FixtureAdapter, OpenSSHSlurmAdapter
from research.a10.lemhi_toolkit.cli import main
from research.a10.lemhi_toolkit.core import Toolkit, ToolkitError, atomic_write, canonical_bytes, read_json, read_record, sha256_bytes, sha256_file
from research.a10.lemhi_toolkit.hardening import (
    LedgerAnchor,
    admit_job_local,
    append_manifest_revision,
    close_job_environment,
    claim_job_local,
    create_raw_collected,
    derive_authority_revision,
    environment_receipt,
    project_evidence,
    release_job_local_claim,
    reserve_primary_and_recovery,
    supervise_process,
    transfer_receipt,
    validate_recovery_target,
    validate_toolchain_closure,
    validate_v2_provider_stack,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PROFILE_V2 = REPOSITORY_ROOT / "research/a10/lemhi_toolkit/profiles/lemhi-v2.json"
PROVIDERS_V2 = [
    "research/a10/lemhi_toolkit/providers/transport-scp-v2.json",
    "research/a10/lemhi_toolkit/providers/scheduler-slurm-v2.json",
    "research/a10/lemhi_toolkit/providers/storage-ceph-v2.json",
    "research/a10/lemhi_toolkit/providers/accelerator-l40-v2.json",
    "research/a10/lemhi_toolkit/providers/runtime-cpython311-portable-v2.json",
    "research/a10/lemhi_toolkit/providers/framework-pytorch271-cu128-numpy226-v2.json",
    "research/a10/lemhi_toolkit/providers/toolchain-rust192-linux-x86_64-v2.json",
]
HEX_A = "a" * 64
HEX_B = "b" * 64


class HardeningFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def authority(self, *, initialize: bool = True) -> tuple[dict, Path]:
        state = self.root / "state"
        anchor_path = state / "authorities" / "v2-budget" / "ledger.json"
        authority = {
            "allowed_roots": [str(self.root / "assets")],
            "authority_id": "v2-authority",
            "confirmation_classification": "development-only",
            "ledger_anchor": str(anchor_path),
            "package_id": "a10m4o1-hardening",
            "published_source_commits": ["abcdef0", "abcdef1"],
            "push_target": "main",
            "resource_budget_id": "v2-budget",
            "resource_ceiling_gpu_minutes": 30,
            "resource_class": "one-l40",
            "scheduler_authority_token": "v2-authority-token",
            "source_commit": "abcdef0",
            "starting_branch": "main",
        }
        (self.root / "assets").mkdir()
        if initialize:
            genesis = LedgerAnchor(anchor_path, authority["authority_id"], authority["resource_budget_id"], 30).initialize(
                authorized=True,
                predecessor_evidence=[],
                scheduler_evidence=[],
            )
            authority.update({
                "authority_revision": 0,
                "ledger_genesis_sha256": genesis,
                "ledger_head_checkpoint": genesis,
                "schema_version": "lemhi-authority-revision-2",
            })
            authority["authority_revision_sha256"] = sha256_bytes(canonical_bytes(authority))
        return authority, state


class ProviderAndEnvironmentTests(HardeningFixture):
    def test_v2_live_cleanup_requires_authenticated_job_local_absence(self) -> None:
        class Runner:
            def run(self, arguments, *, stdin=None, timeout=60):
                del timeout
                if stdin and b"gate_receipt=$3" in stdin:
                    output = b'{"gates":{"job_local_cleanup":true}}\n'
                elif stdin and b"REMOTE_ABSENT" in stdin:
                    output = b"REMOTE_ABSENT\n"
                else:
                    output = b"Master running\n"
                return subprocess.CompletedProcess(arguments, 0, output, b"")

        adapter = OpenSSHSlurmAdapter(
            REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote", Runner()
        )
        profile = read_json(PROFILE_V2)
        plan = {
            "job_local_cleanup": "toolkit_recoverable",
            "jobs": [{"gate_receipt": "evidence.json"}],
            "remote_run_root": "runs/v2-smoke",
            "run_id": "v2-smoke",
            "package_id": "v2-package",
            "source_commit": "abcdef0",
        }
        self.assertEqual(
            adapter.clean(profile, plan),
            {"remote_absent": True, "job_local_cleanup": "verified_absent"},
        )

    def test_v2_live_adapter_uses_export_none_and_authority_reconciliation(self) -> None:
        class Runner:
            def __init__(self):
                self.scripts = []

            def run(self, arguments, *, stdin=None, timeout=60):
                del timeout
                if stdin:
                    self.scripts.append(stdin)
                if stdin and b"JobIDRaw,Comment" in stdin:
                    output = b""
                elif stdin and b"--export=NONE" in stdin:
                    output = b"1000\n"
                else:
                    output = b"Master running\n"
                return subprocess.CompletedProcess(arguments, 0, output, b"")

        runner = Runner()
        adapter = OpenSSHSlurmAdapter(REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote", runner)
        profile = read_json(PROFILE_V2)
        self.assertEqual(adapter.reconcile_authority(profile, "authority-token"), [])
        plan = {"remote_run_root": "runs/v2", "scheduler_authority_token": "authority-token", "evidence_allowlist": ["slurm/smoke.0.out", "slurm/smoke.0.err"]}
        job = {"role": "smoke", "attempt_index": 0, "script": "job.sh", "partition": "gpu-icrews", "gres": "gpu:l40:1", "cpus": 2, "memory_mb": 1024, "time_limit_minutes": 5}
        self.assertEqual(adapter.submit(profile, plan, job, "a" * 32), "1000")
        self.assertTrue(any(b"--export=NONE" in script and b"--comment" in script for script in runner.scripts))

    def test_v2_stack_is_coherent_and_mixed_stack_fails(self) -> None:
        providers = [read_json(REPOSITORY_ROOT / path) for path in PROVIDERS_V2]
        validate_v2_provider_stack(providers)
        providers[0]["provider_api_version"] = 1
        with self.assertRaisesRegex(ToolkitError, "PROVIDER_UNAVAILABLE"):
            validate_v2_provider_stack(providers)

    def test_toolchain_requires_controller_and_compute_closure(self) -> None:
        provider = read_json(REPOSITORY_ROOT / PROVIDERS_V2[-1])
        contract = provider["toolchain_contract"]
        controller = {
            "archive_layout_passed": True,
            "source_vendor_relation": "vendor",
            "target_triple": contract["target_triple"],
        }
        compute = {
            **{field: contract[field] for field in ("cargo_path", "rustc_path", "target_std_path", "host_cxx_path")},
            **controller,
            "loader_resolution_passed": True,
            "compiler_probe_passed": True,
            "offline_metadata_passed": True,
            "offline_build_passed": True,
        }
        self.assertTrue(validate_toolchain_closure(provider, controller, compute)["compute_build"])
        compute["target_std_path"] = "missing"
        with self.assertRaisesRegex(ToolkitError, "GATE_FAILED"):
            validate_toolchain_closure(provider, controller, compute)

    def test_environment_closure_rejects_ambient_and_requires_cublas(self) -> None:
        required = {"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "PYTHONNOUSERSITE": "1"}
        runtime = {"PATH": "/runtime/bin:/usr/bin", "TMPDIR": "/tmp/attempt"}
        closed = close_job_environment(required, {}, runtime, deterministic_cuda=True)
        self.assertEqual(closed["CUBLAS_WORKSPACE_CONFIG"], ":4096:8")
        receipt = environment_receipt(closed, {"CUBLAS_WORKSPACE_CONFIG"})
        self.assertEqual(receipt["slurm_export"], "NONE")
        self.assertNotIn("safe_value", next(item for item in receipt["values"] if item["name"] == "PATH"))
        with self.assertRaisesRegex(ToolkitError, "ambient override"):
            close_job_environment(required, {"PATH": "/host/bin"}, runtime, deterministic_cuda=True)
        with self.assertRaisesRegex(ToolkitError, "deterministic CUDA"):
            close_job_environment({}, {}, runtime, deterministic_cuda=True)


class EvidenceProjectionTests(HardeningFixture):
    def replacements(self) -> list[dict[str, str]]:
        return [
            {"kind": "path", "value": "/ceph/home/user/run/deep", "token": "<JOB_LOCAL_ROOT>"},
            {"kind": "path", "value": "/ceph/home/user/run", "token": "<REMOTE_RUN_ROOT>"},
            {"kind": "identity", "value": "private-user", "token": "<IDENTITY_1>"},
        ]

    def test_raw_record_precedes_projection_and_binds_gates(self) -> None:
        raw = create_raw_collected("authority", "run", HEX_A, [{"logical_name": "evidence.json", "bytes": 2, "sha256": HEX_B}], {"gate": True}, HEX_A)
        self.assertEqual(raw["record_type"], "RAW_COLLECTED")
        self.assertTrue(raw["gates"]["gate"])
        self.assertEqual(raw["schema_version"], "lemhi-toolkit-record-2")

    def test_projection_is_longest_first_and_path_boundary_safe(self) -> None:
        raw = b'/ceph/home/user/run/deep/file /ceph/home/user/run/file /ceph/home/user/runner private-user'
        projected, receipt = project_evidence(raw, media_type="text/plain", replacements=self.replacements(), forbidden=["private-user"], raw_parent_sha256=HEX_A)
        self.assertIn(b"<JOB_LOCAL_ROOT>/file", projected)
        self.assertIn(b"<REMOTE_RUN_ROOT>/file", projected)
        self.assertIn(b"/ceph/home/user/runner", projected)
        self.assertEqual(receipt["token_counts"]["<IDENTITY_1>"], 1)

    def test_projection_rejects_reserved_tokens_invalid_utf8_and_unknown_leak(self) -> None:
        for raw in (b"already <REMOTE_RUN_ROOT>", b"\xff"):
            with self.subTest(raw=raw), self.assertRaisesRegex(ToolkitError, "SANITIZATION_FAILED"):
                project_evidence(raw, media_type="text/plain", replacements=self.replacements(), forbidden=[], raw_parent_sha256=HEX_A)
        with self.assertRaisesRegex(ToolkitError, "unknown forbidden"):
            project_evidence(b"unregistered-secret", media_type="text/plain", replacements=[], forbidden=["unregistered-secret"], raw_parent_sha256=HEX_A)

    def test_json_projection_is_structural_and_rejects_duplicates(self) -> None:
        projected, receipt = project_evidence(b'{"path":"/ceph/home/user/run/file"}', media_type="application/json", replacements=self.replacements(), forbidden=["/ceph/home/"], raw_parent_sha256=HEX_A)
        self.assertEqual(json.loads(projected)["path"], "<REMOTE_RUN_ROOT>/file")
        self.assertEqual(receipt["sanitizer_version"], "lemhi-evidence-projection-2")
        with self.assertRaisesRegex(ToolkitError, "INVALID_JSON"):
            project_evidence(b'{"a":1,"a":2}', media_type="application/json", replacements=[], forbidden=[], raw_parent_sha256=HEX_A)


class LedgerAndLineageTests(HardeningFixture):
    def test_genesis_is_exclusive_and_checkpoint_detects_old_prefix(self) -> None:
        authority, _ = self.authority(initialize=False)
        anchor = LedgerAnchor(Path(authority["ledger_anchor"]), "v2-authority", "v2-budget", 30)
        genesis = anchor.initialize(authorized=True, predecessor_evidence=[], scheduler_evidence=[])
        with self.assertRaisesRegex(ToolkitError, "duplicate genesis"):
            anchor.initialize(authorized=True, predecessor_evidence=[], scheduler_evidence=[])
        head = anchor.append({"event": "reserve", "token": "one", "requested_gpu_minutes": 5, "status": "reserved"}, checkpoint=genesis, scheduler_reconciled=True)
        ledger = anchor.load(checkpoint=head)
        old = {**ledger, "entries": ledger["entries"][:1], "head_sha256": genesis}
        atomic_write(anchor.path, old, private=True)
        with self.assertRaisesRegex(ToolkitError, "truncated before checkpoint"):
            anchor.load(checkpoint=head)

    def test_scheduler_ambiguity_holds_before_append(self) -> None:
        authority, _ = self.authority(initialize=False)
        anchor = LedgerAnchor(Path(authority["ledger_anchor"]), "v2-authority", "v2-budget", 30)
        genesis = anchor.initialize(authorized=True, predecessor_evidence=[], scheduler_evidence=[])
        with self.assertRaisesRegex(ToolkitError, "AUTHORITY_RECONCILIATION_REQUIRED"):
            anchor.append({"event": "reserve"}, checkpoint=genesis, scheduler_reconciled=False)

    def test_authority_derivation_preserves_immutable_fields(self) -> None:
        authority, _ = self.authority()
        request = {"run_id": "second-run", "source_commit": "abcdef1", "asset_manifest_sha256": HEX_A, "plan_input_sha256": HEX_B}
        revision = derive_authority_revision(authority, request)
        self.assertEqual(revision["resource_budget_id"], authority["resource_budget_id"])
        self.assertEqual(revision["predecessor_authority_revision_sha256"], authority["authority_revision_sha256"])
        bad = dict(request, resource_ceiling_gpu_minutes=999)
        with self.assertRaisesRegex(ToolkitError, "authority drift"):
            derive_authority_revision(authority, bad)
        bad = dict(request, source_commit="unpublished")
        with self.assertRaisesRegex(ToolkitError, "not published"):
            derive_authority_revision(authority, bad)


class StorageTransferAndSupervisorTests(HardeningFixture):
    def test_capacity_reservation_and_recovery_target(self) -> None:
        base = self.root / "job-local"
        base.mkdir(mode=0o700)
        receipt = admit_job_local(base, required_bytes=1, required_inodes=1, minimum_free_bytes=0, expected_uid=os.getuid())
        self.assertEqual(receipt["owner_uid"], os.getuid())
        reserve = reserve_primary_and_recovery(30, 5, 10, 5)
        self.assertEqual(reserve["remaining_gpu_minutes"], 10)
        with self.assertRaisesRegex(ToolkitError, "RESOURCE_CEILING"):
            reserve_primary_and_recovery(10, 0, 10, 1)

    def test_capacity_claims_serialize_and_release_exactly(self) -> None:
        base = self.root / "claims"
        base.mkdir(mode=0o700)
        barrier = threading.Barrier(3)
        outcomes = []

        def claim() -> None:
            barrier.wait()
            try:
                outcomes.append(claim_job_local(base, "same-claim", required_bytes=1, required_inodes=1, minimum_free_bytes=0, expected_uid=os.getuid()))
            except ToolkitError as error:
                outcomes.append(error.code)

        threads = [threading.Thread(target=claim) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()
        claims = [item for item in outcomes if isinstance(item, dict)]
        self.assertEqual(len(claims), 1)
        self.assertIn(next(item for item in outcomes if isinstance(item, str)), {"RUN_LOCKED", "JOB_LOCAL_CAPACITY"})
        release_job_local_claim(base, claims[0])
        self.assertFalse((base / ".lemhi-toolkit-claims/same-claim.json").exists())

    def test_recovery_requires_settlement_and_double_identity(self) -> None:
        marker = {"job_id": "1", "node": "node03", "uid": 1, "canonical_base": "/tmp", "canonical_target": "/tmp/a", "filesystem_device": 2}
        scheduler = {"squeue_absent": True, "sacct_settled": True, "requeues_settled": True}
        observation = {**marker, "marker_pass_one": True, "marker_pass_two": True, "ancestors_safe": True}
        validate_recovery_target(marker, scheduler, observation)
        scheduler["squeue_absent"] = False
        with self.assertRaisesRegex(ToolkitError, "CLEANUP_INCOMPLETE"):
            validate_recovery_target(marker, scheduler, observation)

    def test_transfer_states_are_integer_and_fail_closed(self) -> None:
        receipt = transfer_receipt(logical_name="asset", byte_count=100, elapsed_ns=10, method="scp", identity_sha256=HEX_A, state="uploaded", remote_revalidated=True)
        self.assertIsInstance(receipt["observed_bytes_per_second"], int)
        with self.assertRaisesRegex(ToolkitError, "remote revalidation"):
            transfer_receipt(logical_name="asset", byte_count=1, elapsed_ns=1, method="scp", identity_sha256=HEX_A, state="already_verified", remote_revalidated=False)
        with self.assertRaisesRegex(ToolkitError, "range integrity"):
            transfer_receipt(logical_name="asset", byte_count=1, elapsed_ns=1, method="scp", identity_sha256=HEX_A, state="resumed", remote_revalidated=True)

    def test_manifest_is_append_only_and_rejects_same_name_new_hash(self) -> None:
        path = self.root / "manifest.json"
        append_manifest_revision(path, {"revision": 0, "assets": [{"logical_name": "source", "sha256": HEX_A}]})
        append_manifest_revision(path, {"revision": 1, "assets": [{"logical_name": "new", "sha256": HEX_B}]})
        with self.assertRaisesRegex(ToolkitError, "same name different hash"):
            append_manifest_revision(path, {"revision": 2, "assets": [{"logical_name": "source", "sha256": HEX_B}]})

    def test_supervisor_preserves_exit_but_cleanup_uncertainty_dominates(self) -> None:
        attempt = self.root / "attempt"
        attempt.mkdir()
        marker = {"run_id": "run", "attempt": 0}
        atomic_write(attempt / ".lemhi-toolkit-owner.json", marker, private=True)
        status = self.root / "status.json"
        result = supervise_process(["/bin/sh", "-c", "exit 7"], attempt_root=attempt, expected_marker=marker, durable_status=status, environment={"PATH": "/usr/bin:/bin"})
        self.assertEqual(result["terminal"], "APPLICATION_EXIT")
        self.assertEqual(result["application_return_code"], 7)
        self.assertFalse(attempt.exists())

        failed = self.root / "attempt-failed-status"
        failed.mkdir()
        atomic_write(failed / ".lemhi-toolkit-owner.json", marker, private=True)

        def fail_write(_path, _value):
            raise OSError("injected")

        result = supervise_process(["/bin/sh", "-c", "exit 0"], attempt_root=failed, expected_marker=marker, durable_status=status, environment={"PATH": "/usr/bin:/bin"}, status_writer=fail_write)
        self.assertEqual(result["terminal"], "CLEANUP_INCOMPLETE")
        self.assertFalse(failed.exists(), "status failure must not disable local cleanup")


class V2IntegrationTests(HardeningFixture):
    def test_candidate_semantics_are_immutable_and_have_no_promotion_state(self) -> None:
        path = REPOSITORY_ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json"
        candidate = read_json(path)
        recorded = candidate.pop("configuration_semantic_sha256")
        self.assertEqual(recorded, sha256_bytes(canonical_bytes(candidate)))
        self.assertNotIn("configuration_status", candidate)
        self.assertNotIn("evidence", candidate)
        for item in [candidate["toolkit_profile"], *candidate["provider_stack"]]:
            self.assertEqual(sha256_file(REPOSITORY_ROOT / item["path"]), item["sha256"])

    def plan(self, authority: dict, script: Path) -> dict:
        return {
            "assets": [{"bytes": script.stat().st_size, "license_provenance": "repository license", "local_path": str(script), "logical_name": "job.sh", "sha256": sha256_bytes(script.read_bytes()), "source_class": "repository-owned", "target_platform": "linux-x86_64-glibc"}],
            "authority_id": authority["authority_id"],
            "authority_revision_sha256": authority["authority_revision_sha256"],
            "confirmation_classification": "development-only",
            "deterministic_cuda": True,
            "evidence_allowlist": ["evidence.json", "slurm/smoke.0.out", "slurm/smoke.0.err"],
            "evidence_replacements": [],
            "job_local_capacity": {"expanded_asset_bytes": 1, "product_bytes": 1, "checkpoint_bytes": 1, "margin_bytes": 1, "minimum_free_bytes": 1, "required_inodes": 4},
            "job_local_cleanup": "toolkit_recoverable",
            "jobs": [{"cpus": 2, "expected_exit_code": 0, "gate_receipt": "evidence.json", "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1, "memory_mb": 1024, "partition": "icrews", "retry_on": [], "role": "smoke", "script": "job.sh", "time_limit_minutes": 5}],
            "package_id": authority["package_id"],
            "providers": PROVIDERS_V2,
            "recovery_contingency": {"gpu_minutes": 5, "max_attempts": 1, "time_limit_minutes": 5, "exact_node_only": True, "ambiguity": "retain-reserve"},
            "remote_run_root": "runs/v2-run",
            "required_capability_scope": "login",
            "required_job_environment": {"CUBLAS_WORKSPACE_CONFIG": ":4096:8", "PATH": "/run/runtime/bin:/run/toolchain/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "TMPDIR": "/tmp/toolkit-attempt"},
            "resource_budget_id": authority["resource_budget_id"],
            "run_id": "v2-run",
            "scheduler_authority_token": authority["scheduler_authority_token"],
            "source_commit": authority["source_commit"],
            "stop_rules": {"ambiguity": "stop", "gate_failure": "authorized-retry-only", "resource_ceiling": "stop"},
            "submission_mode": "operator-explicit",
            "target_platform": "linux-x86_64-glibc",
        }

    def test_v2_full_fixture_lifecycle_emits_v2_and_keeps_v1_reader(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        profile = read_json(PROFILE_V2)
        toolkit = Toolkit(state, authority, profile, "v2-run", FixtureAdapter(self.root / "fixture", {"job_local_cleanup": "verified_absent"}), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor(); toolkit.probe(); toolkit.plan(self.plan(authority, script)); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        toolkit.submit("smoke", 0); toolkit.observe("smoke", 0); toolkit.collect(); toolkit.clean(); toolkit.close()
        self.assertEqual(read_record(toolkit.publication_dir / "terminal.json")["schema_version"], "lemhi-toolkit-record-2")
        ledger = read_json(toolkit.ledger_path)
        self.assertEqual(next(item for item in reversed(ledger["entries"]) if item.get("job_role") == "toolkit-recovery")["status"], "released")
        v1 = REPOSITORY_ROOT / "docs/work-packages/20260717-a10-lemhi-toolkit-foundation/artifacts/toolkit-fixtures/complete/publication/terminal.json"
        if v1.exists():
            self.assertEqual(read_record(v1)["schema_version"], "lemhi-toolkit-record-1")

    def test_v2_submission_holds_when_authority_reconciliation_fails(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"; script.write_text("#!/bin/sh\n", encoding="utf-8")
        toolkit = Toolkit(state, authority, read_json(PROFILE_V2), "v2-run", FixtureAdapter(self.root / "fixture-hold", {"authority_reconciled": False}), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor(); toolkit.probe(); toolkit.plan(self.plan(authority, script)); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        with self.assertRaisesRegex(ToolkitError, "AUTHORITY_RECONCILIATION_REQUIRED"):
            toolkit.submit("smoke", 0)

    def test_cli_initializes_and_derives_without_allocation(self) -> None:
        authority, _ = self.authority(initialize=False)
        authority.update({"genesis_authorized": True, "predecessor_evidence": [], "scheduler_evidence": []})
        authority_path = self.root / "authority-input.json"; authority_path.write_text(json.dumps(authority), encoding="utf-8")
        initialized = self.root / "authority.json"
        self.assertEqual(main(["--authority", str(authority_path), "initialize-authority", "--output", str(initialized)]), 0)
        request = self.root / "request.json"; request.write_text(json.dumps({"run_id": "derived-run", "source_commit": "abcdef1", "asset_manifest_sha256": HEX_A, "plan_input_sha256": HEX_B}), encoding="utf-8")
        output = self.root / "derived.json"
        self.assertEqual(main(["--authority", str(initialized), "derive-run", "--input", str(request), "--output", str(output)]), 0)
        self.assertEqual(read_json(output)["run_id"], "derived-run")


if __name__ == "__main__":
    unittest.main()
