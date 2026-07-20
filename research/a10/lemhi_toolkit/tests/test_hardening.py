from __future__ import annotations

import json
import io
import os
import subprocess
import tarfile
import tempfile
import threading
import unittest
from pathlib import Path

from research.a10.lemhi_toolkit.adapters import FixtureAdapter, OpenSSHSlurmAdapter
from research.a10.lemhi_toolkit.cli import main
from research.a10.lemhi_toolkit.core import Toolkit, ToolkitError, atomic_write, canonical_bytes, parse_typed_gres, read_json, read_record, sha256_bytes, sha256_file
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
MULTI_GPU_PROVIDER = "research/a10/lemhi_toolkit/providers/accelerator-l40-multigpu-v1.json"
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
            def __init__(self):
                self.gate_calls = []

            def run(self, arguments, *, stdin=None, timeout=60):
                del timeout
                if stdin and b"gate_receipt=$3" in stdin:
                    self.gate_calls.append((arguments, stdin))
                    if any("dependent-evidence.json" in item for item in arguments):
                        return subprocess.CompletedProcess(
                            arguments, 1, b"", b"dependent role was not submitted"
                        )
                    output = b'{"gates":{"job_local_cleanup":true}}\n'
                elif stdin and b"REMOTE_ABSENT" in stdin:
                    output = b"REMOTE_ABSENT\n"
                else:
                    output = b"Master running\n"
                return subprocess.CompletedProcess(arguments, 0, output, b"")

        runner = Runner()
        adapter = OpenSSHSlurmAdapter(
            REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote", runner
        )
        profile = read_json(PROFILE_V2)
        plan = {
            "job_local_cleanup": "toolkit_recoverable",
            "jobs": [
                {"gate_receipt": "evidence.json", "role": "smoke"},
                {
                    "gate_receipt": "dependent-evidence.json",
                    "role": "dependent",
                },
            ],
            "remote_run_root": "runs/v2-smoke",
            "run_id": "v2-smoke",
            "package_id": "v2-package",
            "source_commit": "abcdef0",
        }
        with self.assertRaisesRegex(ToolkitError, "EVIDENCE_INCOMPLETE"):
            adapter.clean(profile, plan)
        runner.gate_calls.clear()
        self.assertEqual(
            adapter.clean(profile, plan, stopped_roles={"dependent"}),
            {"remote_absent": True, "job_local_cleanup": "verified_absent"},
        )
        self.assertEqual(len(runner.gate_calls), 1)
        self.assertFalse(
            any(
                "dependent-evidence.json" in item
                for item in runner.gate_calls[0][0]
            )
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

    def test_projection_escapes_raw_reserved_tokens_before_replacement(self) -> None:
        projected, receipt = project_evidence(
            b"launcher <NO_OTHER_FAILURES> /ceph/home/user/run/file",
            media_type="text/plain",
            replacements=self.replacements(),
            forbidden=["/ceph/home/"],
            raw_parent_sha256=HEX_A,
        )
        self.assertIn(b"[[RAW_RESERVED_TOKEN:NO_OTHER_FAILURES]]", projected)
        self.assertIn(b"<REMOTE_RUN_ROOT>/file", projected)
        self.assertEqual(receipt["escaped_reserved_token_counts"], {"NO_OTHER_FAILURES": 1})

    def test_projection_rejects_invalid_utf8_and_unknown_leak(self) -> None:
        with self.assertRaisesRegex(ToolkitError, "SANITIZATION_FAILED"):
            project_evidence(b"\xff", media_type="text/plain", replacements=self.replacements(), forbidden=[], raw_parent_sha256=HEX_A)
        with self.assertRaisesRegex(ToolkitError, "unknown forbidden"):
            project_evidence(b"unregistered-secret", media_type="text/plain", replacements=[], forbidden=["unregistered-secret"], raw_parent_sha256=HEX_A)

    def test_binary_projection_is_exact_and_still_scans_forbidden_bytes(self) -> None:
        raw = b"\x93NUMPY\x00\xff\x01\x02"
        projected, receipt = project_evidence(
            raw,
            media_type="application/octet-stream",
            replacements=self.replacements(),
            forbidden=[],
            raw_parent_sha256=HEX_A,
        )
        self.assertEqual(projected, raw)
        self.assertEqual(receipt["sanitized_sha256"], sha256_bytes(raw))
        self.assertTrue(all(value == 0 for value in receipt["token_counts"].values()))
        with self.assertRaisesRegex(ToolkitError, "unknown forbidden"):
            project_evidence(
                b"binary-private-user-payload",
                media_type="application/octet-stream",
                replacements=self.replacements(),
                forbidden=["private-user"],
                raw_parent_sha256=HEX_A,
            )

    def test_json_projection_is_structural_and_rejects_duplicates(self) -> None:
        projected, receipt = project_evidence(b'{"path":"/ceph/home/user/run/file"}', media_type="application/json", replacements=self.replacements(), forbidden=["/ceph/home/"], raw_parent_sha256=HEX_A)
        self.assertEqual(json.loads(projected)["path"], "<REMOTE_RUN_ROOT>/file")
        self.assertEqual(receipt["sanitizer_version"], "lemhi-evidence-projection-5")
        with self.assertRaisesRegex(ToolkitError, "INVALID_JSON"):
            project_evidence(b'{"a":1,"a":2}', media_type="application/json", replacements=[], forbidden=[], raw_parent_sha256=HEX_A)

    def test_json_projection_accepts_finite_scientific_numbers(self) -> None:
        projected, _ = project_evidence(
            b'{"elapsed":1.0,"score":-3.25e-4}',
            media_type="application/json",
            replacements=[],
            forbidden=[],
            raw_parent_sha256=HEX_A,
        )
        self.assertEqual(
            json.loads(projected),
            {"elapsed": 1.0, "score": -3.25e-4},
        )
        for raw in (b'{"score":NaN}', b'{"score":Infinity}', b'{"score":1e999}'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ToolkitError, "INVALID_JSON"):
                project_evidence(
                    raw,
                    media_type="application/json",
                    replacements=[],
                    forbidden=[],
                    raw_parent_sha256=HEX_A,
                )


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
        self.assertEqual(revision["allowed_roots"], authority["allowed_roots"])
        self.assertEqual(
            revision["confirmation_classification"],
            authority["confirmation_classification"],
        )
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
    def test_submit_authenticates_current_state_admission_under_run_lock(self) -> None:
        authority, state_root = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        script.chmod(0o700)
        receipt_root = self.root / "assets/admissions"
        receipt_root.mkdir()
        toolkit = Toolkit(
            state_root,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-admission"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.plan(authority, script)
        plan["assets"][0]["executable"] = True
        plan["admission_materialization"] = {
            "asset": "job.sh",
            "receipt_directory": str(receipt_root),
            "record_type": "test-submission-admission",
            "required_before_each_submit": True,
            "required_roles": ["smoke"],
            "snapshot": "exact private toolkit state plus authenticated job receipts",
            "toolkit_submit_invokes_package_checker": False,
        }
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()

        def publish_receipt() -> None:
            state = read_json(toolkit.private_path)
            semantic = {
                "attempt_index": 0,
                "authority_id": authority["authority_id"],
                "decision": "PASS",
                "gates": {"fixture_admission": True},
                "input_identities": {
                    "toolkit_state_sha256": sha256_file(toolkit.private_path)
                },
                "package_id": authority["package_id"],
                "plan_id": state["current_plan_id"],
                "record_type": "test-submission-admission",
                "role": "smoke",
                "run_id": "v2-run",
                "schema_version": "lemhi-toolkit-record-2",
                "source_commit": authority["source_commit"],
                "valid": True,
            }
            semantic["record_sha256"] = sha256_bytes(canonical_bytes(semantic))
            atomic_write(receipt_root / "smoke.json", semantic, private=True)

        publish_receipt()
        changed = read_json(toolkit.private_path)
        changed["injected_state_transition"] = True
        atomic_write(toolkit.private_path, changed, private=True)
        with self.assertRaisesRegex(ToolkitError, "stale or invalid"):
            toolkit.submit("smoke", 0)
        publish_receipt()
        self.assertEqual(toolkit.submit("smoke", 0), "1000")
        recorded = read_json(toolkit.private_path)["attempts"]["smoke.0"]
        self.assertEqual(
            recorded["submission_admission_record_sha256"],
            read_json(receipt_root / "smoke.json")["record_sha256"],
        )

    def test_typed_gres_parser_and_plan_counts_fail_closed(self) -> None:
        self.assertEqual(parse_typed_gres("gpu:l40:4", "job gres"), ("gpu", "l40", 4))
        for value in ("gpu:4", "gpu:l40:0", "gpu:l40:-1", "gpu::2", 2):
            with self.subTest(value=value), self.assertRaisesRegex(ToolkitError, "PLAN_DRIFT"):
                parse_typed_gres(value, "job gres")

        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        profile = read_json(PROFILE_V2)
        for index, (gpus, gres, expected) in enumerate((
            (1, "gpu:l40:2", "count mismatch"),
            (1, "gpu:rtxa6000:1", "provider mismatch"),
            (2, "gpu:l40:2", "provider maximum"),
        )):
            with self.subTest(gpus=gpus, gres=gres), self.assertRaisesRegex(ToolkitError, expected):
                run_id = f"v2-invalid-{index}"
                toolkit = Toolkit(state, authority, profile, run_id, FixtureAdapter(self.root / f"fixture-{index}"), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
                toolkit.doctor(); toolkit.probe()
                plan = self.plan(authority, script)
                plan.update({"remote_run_root": f"runs/{run_id}", "run_id": run_id})
                plan["jobs"][0].update({"gpus": gpus, "gres": gres})
                toolkit.plan(plan)

    def test_multigpu_provider_accepts_two_and_four_and_rejects_five(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        for count in (2, 4):
            with self.subTest(count=count):
                run_id = f"v2-run-{count}"
                toolkit = Toolkit(state, authority, read_json(PROFILE_V2), run_id, FixtureAdapter(self.root / f"fixture-valid-{count}"), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
                toolkit.doctor(); toolkit.probe()
                plan = self.plan(authority, script)
                plan.update({"remote_run_root": f"runs/{run_id}", "run_id": run_id})
                plan["providers"][3] = MULTI_GPU_PROVIDER
                plan["jobs"][0].update({"gpus": count, "gres": f"gpu:l40:{count}"})
                toolkit.plan(plan)

        toolkit = Toolkit(state, authority, read_json(PROFILE_V2), "v2-run-5", FixtureAdapter(self.root / "fixture-invalid-5"), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        plan.update({"remote_run_root": "runs/v2-run-5", "run_id": "v2-run-5"})
        plan["providers"][3] = MULTI_GPU_PROVIDER
        plan["jobs"][0].update({"gpus": 5, "gres": "gpu:l40:5"})
        with self.assertRaisesRegex(ToolkitError, "provider maximum"):
            toolkit.plan(plan)

    def test_recovery_gres_count_must_match_ledger_multiplier(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(state, authority, read_json(PROFILE_V2), "v2-run", FixtureAdapter(self.root / "fixture-recovery-mismatch"), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        plan["recovery_contingency"]["gres"] = "gpu:l40:2"
        with self.assertRaisesRegex(ToolkitError, "recovery gpus and gres count mismatch"):
            toolkit.plan(plan)

    def test_live_elapsed_accounting_uses_four_validated_gpus(self) -> None:
        class Runner:
            def run(self, arguments, *, stdin=None, timeout=60):
                del arguments, timeout
                if stdin and b"ElapsedRaw" in stdin:
                    output = b'{"terminal":true,"state":"COMPLETED","exit_code":0,"elapsed_seconds":61,"gates":{"scheduler_terminal":true},"actual_gpu_minutes":null,"accounting":"available","node":"node03"}\n'
                elif stdin and b"gate_receipt=$3" in stdin:
                    output = b'{"gates":{"collective_correct":true,"job_local_cleanup":true}}\n'
                else:
                    output = b""
                return subprocess.CompletedProcess([], 0, output, b"")

        adapter = OpenSSHSlurmAdapter(REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote", Runner())
        observed = adapter.observe(
            read_json(PROFILE_V2),
            {"remote_run_root": "runs/v2-run"},
            {"expected_exit_code": 0, "gate_receipt": "evidence.json", "gpus": 4},
            "1000",
        )
        self.assertEqual(observed["actual_gpu_seconds"], 244)
        self.assertEqual(observed["actual_gpu_minutes"], 5)

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
        recovery_source = REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote/recover_job_local_v2.sh"
        recovery_script = script.parent / "recover.sh"
        recovery_script.write_bytes(recovery_source.read_bytes())
        recovery_script.chmod(0o700)
        return {
            "assets": [
                {"bytes": script.stat().st_size, "license_provenance": "repository license", "local_path": str(script), "logical_name": "job.sh", "sha256": sha256_bytes(script.read_bytes()), "source_class": "repository-owned", "target_platform": "linux-x86_64-glibc"},
                {"bytes": recovery_script.stat().st_size, "executable": True, "license_provenance": "repository license", "local_path": str(recovery_script), "logical_name": "recover.sh", "sha256": sha256_bytes(recovery_script.read_bytes()), "source_class": "repository-owned", "target_platform": "linux-x86_64-glibc"},
            ],
            "authority_id": authority["authority_id"],
            "authority_revision_sha256": authority["authority_revision_sha256"],
            "confirmation_classification": "development-only",
            "deterministic_cuda": True,
            "evidence_allowlist": ["evidence.json", "recovery.json", "slurm/smoke.0.out", "slurm/smoke.0.err", "slurm/toolkit-recovery.0.out", "slurm/toolkit-recovery.0.err"],
            "evidence_replacements": [],
            "job_local_capacity": {"expanded_asset_bytes": 1, "product_bytes": 1, "checkpoint_bytes": 1, "margin_bytes": 1, "minimum_free_bytes": 1, "required_inodes": 4},
            "job_local_cleanup": "toolkit_recoverable",
            "jobs": [{"cpus": 2, "expected_exit_code": 0, "gate_receipt": "evidence.json", "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1, "memory_mb": 1024, "partition": "icrews", "retry_on": [], "role": "smoke", "script": "job.sh", "time_limit_minutes": 5}],
            "package_id": authority["package_id"],
            "providers": list(PROVIDERS_V2),
            "recovery_contingency": {"ambiguity": "retain-reserve", "cpus": 2, "exact_node_only": True, "gate_receipt": "recovery.json", "gpu_minutes": 5, "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1, "memory_mb": 1024, "partition": "icrews", "script": "recover.sh", "time_limit_minutes": 5},
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

    @staticmethod
    def with_dependent(plan: dict) -> dict:
        dependent = dict(plan["jobs"][0])
        dependent.update(
            {
                "gate_receipt": "dependent-evidence.json",
                "max_attempts": 1,
                "retry_on": [],
                "role": "dependent",
            }
        )
        plan["jobs"].append(dependent)
        plan["evidence_allowlist"].extend(
            [
                "dependent-evidence.json",
                "slurm/dependent.0.out",
                "slurm/dependent.0.err",
            ]
        )
        return plan

    def test_v2_failed_matrix_stop_closes_without_dependent_submission(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        scenario = {
            "job_local_cleanup": "verified_absent",
            "results": {
                "smoke": {
                    "actual_gpu_minutes": 1,
                    "exit_code": 1,
                    "gates": {"job_local_cleanup": True, "runtime": False},
                }
            },
        }
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-stop", scenario),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.with_dependent(self.plan(authority, script))
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        self.assertEqual(toolkit.submit("smoke", 0), "1000")
        self.assertFalse(toolkit.observe("smoke", 0)["passed"])
        authority_path = self.root / "authority.json"
        authority_path.write_text(json.dumps(authority), encoding="utf-8")
        self.assertEqual(
            main(
                [
                    "--authority", str(authority_path),
                    "--profile", str(PROFILE_V2),
                    "--provider-root", str(REPOSITORY_ROOT),
                    "--run-id", "v2-run",
                    "--adapter", "fixture",
                    "--fixture-root", str(self.root / "fixture-stop"),
                    "stop-matrix",
                    "--trigger-job-role", "smoke",
                    "--reason-code", "upstream-role-exhausted",
                ]
            ),
            0,
        )
        receipt = read_record(toolkit.publication_dir / "matrix-stop.json")
        self.assertEqual(receipt["stopped_roles"], ["dependent"])
        self.assertEqual(receipt["classification"], "NOT_EXECUTED_UPSTREAM_FAILURE")
        self.assertEqual(read_json(toolkit.private_path)["run_state"], "MATRIX_SETTLED")
        ledger_before_close = read_json(toolkit.ledger_path)
        self.assertEqual(
            {
                item.get("job_id")
                for item in ledger_before_close["entries"]
                if item.get("job_id") is not None
            },
            {"1000"},
        )
        self.assertEqual(
            toolkit.stop_matrix("smoke", "upstream-role-exhausted")[
                "record_sha256"
            ],
            receipt["record_sha256"],
        )
        (toolkit.publication_dir / "matrix-stop.json").unlink()
        toolkit.adapter.scenario["authority_reconciled"] = False
        toolkit.adapter.scenario["masters"] = {"gateway": False, "target": False}
        self.assertEqual(
            toolkit.stop_matrix("smoke", "upstream-role-exhausted")[
                "record_sha256"
            ],
            receipt["record_sha256"],
        )
        toolkit.adapter.scenario["masters"] = {"gateway": True, "target": True}
        toolkit.collect(); toolkit.clean()
        self.assertEqual(toolkit.close()["stopped_role_count"], 1)
        latest_recovery = next(
            item
            for item in reversed(read_json(toolkit.ledger_path)["entries"])
            if item.get("job_role") == "toolkit-recovery"
        )
        self.assertEqual(latest_recovery["status"], "released")

    def test_v2_matrix_stop_rejects_nonexhausted_or_unsettled_work(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        scenario = {
            "results": {"smoke": {"exit_code": 1, "gates": {"runtime": False}}}
        }
        plan = self.with_dependent(self.plan(authority, script))
        plan["jobs"][0]["max_attempts"] = 2
        plan["jobs"][0]["retry_on"] = ["gate-failed"]
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-nonexhausted", scenario),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
        with self.assertRaisesRegex(ToolkitError, "trigger is not exhausted"):
            toolkit.stop_matrix("smoke", "upstream-role-exhausted")
        toolkit.submit("smoke", 1)
        with self.assertRaisesRegex(ToolkitError, "every attempt settled"):
            toolkit.stop_matrix("smoke", "upstream-role-exhausted")

    def test_v2_matrix_stop_requires_authority_reconciliation(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        scenario = {
            "results": {"smoke": {"exit_code": 1, "gates": {"runtime": False}}}
        }
        adapter = FixtureAdapter(self.root / "fixture-stop-reconcile", scenario)
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            adapter,
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.with_dependent(self.plan(authority, script))
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
        adapter.scenario["authority_job_ids"] = []
        with self.assertRaisesRegex(ToolkitError, "AUTHORITY_RECONCILIATION_REQUIRED"):
            toolkit.stop_matrix("smoke", "upstream-role-exhausted")

    def test_v2_matrix_stop_rejects_a_passing_trigger(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-stop-passed"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.with_dependent(self.plan(authority, script))
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        toolkit.submit("smoke", 0); self.assertTrue(toolkit.observe("smoke", 0)["passed"])
        with self.assertRaisesRegex(ToolkitError, "trigger is not exhausted"):
            toolkit.stop_matrix("smoke", "upstream-role-exhausted")

    def test_v2_matrix_stop_rejects_tampered_trigger_receipt(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(
                self.root / "fixture-stop-tamper",
                {"results": {"smoke": {"exit_code": 1, "gates": {"runtime": False}}}},
            ),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.with_dependent(self.plan(authority, script))
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
        receipt_path = toolkit.publication_dir / "job-smoke.0.json"
        receipt = read_json(receipt_path)
        receipt["passed"] = True
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(ToolkitError, "record hash mismatch"):
            toolkit.stop_matrix("smoke", "upstream-role-exhausted")

    def test_v2_submit_and_matrix_stop_share_the_budget_lock(self) -> None:
        class BlockingAdapter(FixtureAdapter):
            def __init__(self, root: Path, scenario: dict):
                super().__init__(root, scenario)
                self.block_reconcile = False
                self.entered = threading.Event()
                self.release = threading.Event()

            def reconcile_authority(self, profile, authority_token):
                if self.block_reconcile:
                    self.entered.set()
                    self.release.wait(timeout=5)
                return super().reconcile_authority(profile, authority_token)

        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        adapter = BlockingAdapter(
            self.root / "fixture-stop-race",
            {"results": {"smoke": {"exit_code": 1, "gates": {"runtime": False}}}},
        )
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            adapter,
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.with_dependent(self.plan(authority, script))
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
        adapter.block_reconcile = True
        outcomes = []

        def stop() -> None:
            try:
                toolkit.stop_matrix("smoke", "upstream-role-exhausted")
                outcomes.append("stop")
            except ToolkitError as error:
                outcomes.append(error.code)

        thread = threading.Thread(target=stop)
        thread.start()
        self.assertTrue(adapter.entered.wait(timeout=5))
        with self.assertRaisesRegex(ToolkitError, "RUN_LOCKED"):
            toolkit.submit("dependent", 0)
        adapter.release.set()
        thread.join(timeout=5)
        self.assertEqual(outcomes, ["stop"])
        self.assertEqual(read_json(toolkit.private_path)["run_state"], "MATRIX_SETTLED")

    def test_v2_sparse_collection_requires_submitted_evidence_and_gate_identity(self) -> None:
        class SparseAdapter(FixtureAdapter):
            def __init__(
                self,
                root: Path,
                *,
                allowlisted_directory: bool = False,
                extra_directory: bool = False,
                omit_stderr: bool = False,
                mutate_gate: bool = False,
            ):
                super().__init__(root)
                self.allowlisted_directory = allowlisted_directory
                self.extra_directory = extra_directory
                self.omit_stderr = omit_stderr
                self.mutate_gate = mutate_gate
                self.observed_gate = b'{"gates":{"job_local_cleanup":true}}\n'

            def observe(self, profile, plan, planned_job, job_id):
                result = super().observe(profile, plan, planned_job, job_id)
                result["gate_receipt_sha256"] = sha256_bytes(self.observed_gate)
                return result

            def collect(self, profile, plan, quarantine):
                del profile
                gate = (
                    b'{"gates":{"job_local_cleanup":false}}\n'
                    if self.mutate_gate
                    else self.observed_gate
                )
                content = {
                    "evidence.json": gate,
                    "slurm/smoke.0.out": b"PASS\n",
                    "streams.npz": b"\x93NUMPY\x00\xff\x01\x02",
                }
                if not self.omit_stderr:
                    content["slurm/smoke.0.err"] = b""
                archive = quarantine / "evidence.tar"
                with tarfile.open(archive, "w") as stream:
                    if self.allowlisted_directory:
                        directory = tarfile.TarInfo("recovery.json")
                        directory.type = tarfile.DIRTYPE
                        directory.uid = 0
                        directory.gid = 0
                        directory.mode = 0o700
                        stream.addfile(directory)
                    if self.extra_directory:
                        directory = tarfile.TarInfo("unexpected")
                        directory.type = tarfile.DIRTYPE
                        directory.uid = 0
                        directory.gid = 0
                        directory.mode = 0o700
                        stream.addfile(directory)
                    for name, payload in sorted(content.items()):
                        item = tarfile.TarInfo(name)
                        item.size = len(payload)
                        item.uid = 0
                        item.gid = 0
                        item.mode = 0o600
                        stream.addfile(item, io.BytesIO(payload))
                present = sorted(
                    [*content, *(["recovery.json"] if self.allowlisted_directory else [])]
                )
                return {
                    "absent": sorted(set(plan["evidence_allowlist"]) - set(present)),
                    "bytes": archive.stat().st_size,
                    "cleanup_marker_sha256": sha256_file(
                        self._run_root(plan) / ".lemhi-toolkit-owner.json"
                    ),
                    "download_promoted": True,
                    "logical_name": "evidence.tar",
                    "present": present,
                    "sanitization_policy": "fixture-sparse-v2",
                    "sha256": sha256_file(archive),
                }

        def settled_toolkit(adapter: SparseAdapter) -> Toolkit:
            authority, state = self.authority()
            script = self.root / "assets/job.sh"
            script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            toolkit = Toolkit(
                state,
                authority,
                read_json(PROFILE_V2),
                "v2-run",
                adapter,
                clock=lambda: "2026-07-19T20:00:00Z",
                provider_root=REPOSITORY_ROOT,
            )
            plan = self.plan(authority, script)
            plan["evidence_allowlist"].append("streams.npz")
            toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
            toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
            return toolkit

        toolkit = settled_toolkit(SparseAdapter(self.root / "sparse-pass"))
        self.assertTrue(toolkit.collect()["download_promoted"])
        self.assertEqual(
            (toolkit.publication_dir / "evidence/streams.npz").read_bytes(),
            b"\x93NUMPY\x00\xff\x01\x02",
        )

        self.temporary.cleanup()
        self.setUp()
        toolkit = settled_toolkit(
            SparseAdapter(self.root / "sparse-missing", omit_stderr=True)
        )
        with self.assertRaisesRegex(ToolkitError, "submitted attempt evidence missing"):
            toolkit.collect()

        self.temporary.cleanup()
        self.setUp()
        toolkit = settled_toolkit(
            SparseAdapter(self.root / "sparse-mutated", mutate_gate=True)
        )
        with self.assertRaisesRegex(ToolkitError, "gate receipt changed"):
            toolkit.collect()

        self.temporary.cleanup()
        self.setUp()
        toolkit = settled_toolkit(
            SparseAdapter(self.root / "sparse-directory", extra_directory=True)
        )
        with self.assertRaisesRegex(ToolkitError, "archive members differ"):
            toolkit.collect()

        self.temporary.cleanup()
        self.setUp()
        toolkit = settled_toolkit(
            SparseAdapter(
                self.root / "sparse-allowlisted-directory",
                allowlisted_directory=True,
            )
        )
        with self.assertRaisesRegex(ToolkitError, "nonregular member"):
            toolkit.collect()

    def test_v2_collection_rejects_direct_adapter_or_missing_gate_hash(self) -> None:
        class DirectAdapter(FixtureAdapter):
            def collect(self, profile, plan, quarantine):
                return super().collect(
                    {**profile, "provider_api_version": 1}, plan, quarantine
                )

        class MissingHashAdapter(FixtureAdapter):
            def observe(self, profile, plan, planned_job, job_id):
                result = super().observe(profile, plan, planned_job, job_id)
                result.pop("gate_receipt_sha256")
                return result

        def settled(adapter: FixtureAdapter) -> Toolkit:
            authority, state = self.authority()
            script = self.root / "assets/job.sh"
            script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            toolkit = Toolkit(
                state,
                authority,
                read_json(PROFILE_V2),
                "v2-run",
                adapter,
                clock=lambda: "2026-07-19T20:00:00Z",
                provider_root=REPOSITORY_ROOT,
            )
            toolkit.doctor(); toolkit.probe(); toolkit.plan(self.plan(authority, script)); toolkit.prepare(); toolkit.stage(); toolkit.verify()
            toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
            return toolkit

        toolkit = settled(DirectAdapter(self.root / "direct-v2"))
        with self.assertRaisesRegex(ToolkitError, "requires sparse archive"):
            toolkit.collect()

        self.temporary.cleanup()
        self.setUp()
        toolkit = settled(MissingHashAdapter(self.root / "missing-hash-v2"))
        with self.assertRaisesRegex(ToolkitError, "observed gate receipt identity missing"):
            toolkit.collect()

    def test_v2_collection_rejects_conflicting_retry_gate_hashes(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        scenario = {
            "results": {"smoke": {"exit_code": 1, "gates": {"runtime": False}}}
        }
        adapter = FixtureAdapter(self.root / "retry-gate-hash", scenario)
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            adapter,
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.plan(authority, script)
        plan["jobs"][0]["max_attempts"] = 2
        plan["jobs"][0]["retry_on"] = ["gate-failed"]
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        toolkit.submit("smoke", 0); toolkit.observe("smoke", 0)
        adapter.scenario["results"]["smoke"] = {
            "exit_code": 0,
            "gates": {"runtime": True},
        }
        toolkit.submit("smoke", 1); toolkit.observe("smoke", 1)
        with self.assertRaisesRegex(ToolkitError, "conflicting identities"):
            toolkit.collect()


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

    def test_v2_plan_rejects_collection_invalid_replacement_token(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        profile = read_json(PROFILE_V2)
        toolkit = Toolkit(state, authority, profile, "v2-run", FixtureAdapter(self.root / "fixture"), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor()
        toolkit.probe()
        plan = self.plan(authority, script)
        plan["evidence_replacements"] = [
            {"kind": "path", "value": "/ceph/home/user/run", "token": "[REMOTE_RUN_ROOT]"}
        ]
        with self.assertRaisesRegex(ToolkitError, "invalid replacement token"):
            toolkit.plan(plan)

    def test_v2_plan_rejects_gate_and_slurm_stream_collision(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-gate-log-collision"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        plan["jobs"][0]["gate_receipt"] = "slurm/smoke.0.out"
        with self.assertRaisesRegex(ToolkitError, "collides with Slurm stream"):
            toolkit.plan(plan)

    def test_v2_plan_rejects_cross_role_gate_and_slurm_stream_collision(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-cross-role-gate-log-collision"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe()
        plan = self.with_dependent(self.plan(authority, script))
        plan["jobs"][0]["gate_receipt"] = "slurm/dependent.0.out"
        with self.assertRaisesRegex(ToolkitError, "collides with Slurm stream"):
            toolkit.plan(plan)

    def test_v2_plan_rejects_recovery_gate_and_job_stream_collision(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-recovery-gate-log-collision"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        plan["recovery_contingency"]["gate_receipt"] = "slurm/smoke.0.out"
        with self.assertRaisesRegex(ToolkitError, "collides with Slurm stream"):
            toolkit.plan(plan)

    def test_v2_plan_rejects_job_gate_and_recovery_stream_collision(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-job-gate-recovery-log-collision"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        plan["jobs"][0]["gate_receipt"] = "slurm/toolkit-recovery.0.out"
        with self.assertRaisesRegex(ToolkitError, "collides with Slurm stream"):
            toolkit.plan(plan)

    def test_v2_plan_rejects_recovery_gate_and_recovery_stream_collision(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-recovery-gate-own-log-collision"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        plan["recovery_contingency"]["gate_receipt"] = (
            "slurm/toolkit-recovery.0.err"
        )
        with self.assertRaisesRegex(ToolkitError, "collides with Slurm stream"):
            toolkit.plan(plan)

    def test_v2_plan_rejects_planned_recovery_role_stream_ownership(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-duplicate-recovery-stream-owner"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        plan["jobs"][0]["role"] = "toolkit-recovery"
        with self.assertRaisesRegex(ToolkitError, "Slurm stream has multiple owners"):
            toolkit.plan(plan)

    def test_v2_amend_rejects_job_gate_and_recovery_stream_collision(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            FixtureAdapter(self.root / "fixture-amend-gate-recovery-log-collision"),
            clock=lambda: "2026-07-19T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        toolkit.doctor(); toolkit.probe()
        plan = self.plan(authority, script)
        toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        replacement = json.loads(json.dumps(plan))
        replacement["jobs"][0]["gate_receipt"] = "slurm/toolkit-recovery.0.out"
        with self.assertRaisesRegex(ToolkitError, "collides with Slurm stream"):
            toolkit.amend(replacement, "exercise global collision check", ["jobs"])

    def test_v2_submission_holds_when_authority_reconciliation_fails(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"; script.write_text("#!/bin/sh\n", encoding="utf-8")
        toolkit = Toolkit(state, authority, read_json(PROFILE_V2), "v2-run", FixtureAdapter(self.root / "fixture-hold", {"authority_reconciled": False}), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor(); toolkit.probe(); toolkit.plan(self.plan(authority, script)); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        with self.assertRaisesRegex(ToolkitError, "AUTHORITY_RECONCILIATION_REQUIRED"):
            toolkit.submit("smoke", 0)

    def _settled_recovery_fixture(
        self, fixture_name: str
    ) -> tuple[Toolkit, FixtureAdapter, dict]:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
        scenario = {
            "results": {
                "smoke": {
                    "actual_gpu_minutes": 1,
                    "exit_code": 7,
                    "gates": {"job_local_cleanup": False, "registered_failure": True},
                    "node": "node03",
                    "recovery_target": {
                        "device": 9,
                        "job_id": "1000",
                        "marker_sha256": HEX_A,
                        "node": "node03",
                        "target": "/tmp/lemhi-toolkit-1/v2-run-smoke-0-1000",
                        "uid": 1,
                    },
                }
            }
        }
        adapter = FixtureAdapter(self.root / fixture_name, scenario)
        toolkit = Toolkit(
            state,
            authority,
            read_json(PROFILE_V2),
            "v2-run",
            adapter,
            clock=lambda: "2026-07-17T20:00:00Z",
            provider_root=REPOSITORY_ROOT,
        )
        plan = self.plan(authority, script)
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage(); toolkit.verify()
        self.assertEqual(toolkit.submit("smoke", 0), "1000")
        self.assertFalse(toolkit.observe("smoke", 0)["passed"])
        self.assertEqual(toolkit.recover("smoke", 0), "1001")
        self.assertTrue(toolkit.observe_recovery()["passed"])
        return toolkit, adapter, plan

    def test_v2_reserved_recovery_is_submitted_settled_and_consumed(self) -> None:
        toolkit, _, _ = self._settled_recovery_fixture("fixture-recovery")
        toolkit.collect()
        raw = read_json(toolkit.private_path)["raw_collected"]
        self.assertTrue(raw["gates"]["toolkit-recovery.job_local_cleanup"])
        self.assertTrue(raw["gates"]["toolkit-recovery.recovery_exact_node"])
        toolkit.clean(); toolkit.close()
        ledger = read_json(toolkit.ledger_path)
        latest = next(item for item in reversed(ledger["entries"]) if item.get("job_role") == "toolkit-recovery")
        self.assertEqual(latest["status"], "settled")
        self.assertEqual(latest["absence_proof"], "JOB_LOCAL_ABSENT")

    def test_v2_recovery_collection_requires_all_recovery_evidence(self) -> None:
        toolkit, adapter, plan = self._settled_recovery_fixture(
            "fixture-recovery-missing-evidence"
        )
        (adapter._run_root(plan) / "slurm/toolkit-recovery.0.err").unlink()
        with self.assertRaisesRegex(ToolkitError, "recovery evidence missing"):
            toolkit.collect()

    def test_v2_recovery_collection_rejects_mutated_gate_receipt(self) -> None:
        toolkit, adapter, plan = self._settled_recovery_fixture(
            "fixture-recovery-mutated-gate"
        )
        (adapter._run_root(plan) / "recovery.json").write_bytes(
            b'{"gates":{"job_local_cleanup":false}}\n'
        )
        with self.assertRaisesRegex(
            ToolkitError,
            "collected recovery gate receipt changed after observation",
        ):
            toolkit.collect()

    def test_v2_pre_submission_abort_removes_exact_staged_root(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\n", encoding="utf-8")
        plan = self.plan(authority, script)
        adapter = FixtureAdapter(self.root / "fixture-abort")
        toolkit = Toolkit(state, authority, read_json(PROFILE_V2), "v2-run", adapter, clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan); toolkit.prepare(); toolkit.stage()
        receipt = toolkit.abort()
        self.assertEqual(receipt["terminal"], "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION")
        self.assertFalse((adapter.remote / "runs/v2-run").exists())
        self.assertEqual(read_json(toolkit.private_path)["run_state"], "ABORTED")

    def test_executable_intent_is_prepared_and_verified(self) -> None:
        authority, state = self.authority()
        script = self.root / "assets/job.sh"
        script.write_text("#!/bin/sh\n", encoding="utf-8")
        plan = self.plan(authority, script)
        plan["assets"][0]["executable"] = True
        toolkit = Toolkit(state, authority, read_json(PROFILE_V2), "v2-run", FixtureAdapter(self.root / "fixture-mode"), clock=lambda: "2026-07-17T20:00:00Z", provider_root=REPOSITORY_ROOT)
        toolkit.doctor(); toolkit.probe(); toolkit.plan(plan)
        with self.assertRaisesRegex(ToolkitError, "not executable"):
            toolkit.prepare()
        script.chmod(0o700)
        prepared = toolkit.prepare()
        self.assertTrue(prepared[0]["executable"])
        toolkit.stage(); toolkit.verify()

    def test_live_observe_reads_failure_gate_receipt(self) -> None:
        class Runner:
            def run(self, arguments, *, stdin=None, timeout=60):
                del arguments, timeout
                if stdin and b"ElapsedRaw" in stdin:
                    output = b'{"terminal":true,"state":"FAILED","exit_code":1,"elapsed_seconds":61,"gates":{"scheduler_terminal":true},"actual_gpu_minutes":null,"accounting":"available","node":"node03"}\n'
                elif stdin and b"gate_receipt=$3" in stdin:
                    output = b'{"gates":{"environment_closure":false,"job_local_cleanup":true}}\n'
                else:
                    output = b""
                return subprocess.CompletedProcess([], 0, output, b"")

        adapter = OpenSSHSlurmAdapter(REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote", Runner())
        plan = {"remote_run_root": "runs/v2-run"}
        job = {"expected_exit_code": 0, "gate_receipt": "evidence.json", "gpus": 1}
        observed = adapter.observe(read_json(PROFILE_V2), plan, job, "1000")
        self.assertFalse(observed["gates"]["environment_closure"])
        self.assertTrue(observed["gates"]["job_local_cleanup"])
        self.assertEqual(observed["actual_gpu_seconds"], 61)
        self.assertEqual(observed["actual_gpu_minutes"], 2)
        self.assertIn("gate_receipt_sha256", observed)

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


class EvidencePackingTests(HardeningFixture):
    def setUp(self) -> None:
        super().setUp()
        self.base = self.root / "remote"
        self.run = self.base / "runs/test-run"
        self.run.mkdir(parents=True)
        (self.run / ".lemhi-toolkit-owner.json").write_text("{}\n", encoding="utf-8")
        self.script = REPOSITORY_ROOT / "research/a10/lemhi_toolkit/remote/pack_evidence.sh"

    def invoke(self, *members: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", str(self.script), str(self.base), "runs/test-run", *members],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_sparse_pack_reports_exact_present_absent_partition(self) -> None:
        (self.run / "present.json").write_text('{"valid":true}\n', encoding="utf-8")
        result = self.invoke("missing.json", "present.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        metadata = json.loads(result.stdout)
        self.assertEqual(metadata["present"], ["present.json"])
        self.assertEqual(metadata["absent"], ["missing.json"])
        with tarfile.open(self.run / "evidence.tar") as archive:
            self.assertEqual(archive.getnames(), ["present.json"])

    def test_sparse_pack_rejects_empty_or_unsafe_present_member(self) -> None:
        self.assertNotEqual(self.invoke("missing.json").returncode, 0)
        (self.run / "real.json").write_text("{}\n", encoding="utf-8")
        (self.run / "linked.json").symlink_to("real.json")
        self.assertNotEqual(self.invoke("linked.json").returncode, 0)
        (self.run / "dangling.json").symlink_to("absent-target.json")
        self.assertNotEqual(self.invoke("dangling.json").returncode, 0)
        (self.run / "directory.json").mkdir()
        self.assertNotEqual(self.invoke("directory.json").returncode, 0)
        os.mkfifo(self.run / "pipe.json")
        self.assertNotEqual(self.invoke("pipe.json").returncode, 0)
        real_directory = self.run / "real-directory"
        real_directory.mkdir()
        (real_directory / "value.json").write_text("{}\n", encoding="utf-8")
        (self.run / "alias").symlink_to(real_directory, target_is_directory=True)
        self.assertNotEqual(self.invoke("alias/value.json").returncode, 0)

    def test_sparse_pack_rejects_symlinked_run_root(self) -> None:
        actual = self.base / "runs/actual-run"
        actual.mkdir()
        (actual / ".lemhi-toolkit-owner.json").write_text("{}\n", encoding="utf-8")
        (actual / "value.json").write_text("{}\n", encoding="utf-8")
        linked = self.base / "runs/linked-run"
        linked.symlink_to(actual, target_is_directory=True)
        result = subprocess.run(
            [
                "sh",
                str(self.script),
                str(self.base),
                "runs/linked-run",
                "value.json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_sparse_pack_rejects_hardlinked_member(self) -> None:
        first = self.run / "first.json"
        first.write_text("{}\n", encoding="utf-8")
        os.link(first, self.run / "second.json")
        self.assertNotEqual(self.invoke("first.json").returncode, 0)

    def test_sparse_pack_preplanted_temporary_root_only_denies_service(self) -> None:
        (self.run / "value.json").write_text("{}\n", encoding="utf-8")
        record = self.base / "preplanted-path"
        command = (
            'temporary="$1/runs/test-run/.evidence-pack.$$"; '
            'mkdir "$temporary"; printf keep >"$temporary/sentinel"; '
            'printf "%s" "$temporary" >"$1/preplanted-path"; '
            'exec sh "$2" "$1" runs/test-run value.json'
        )
        result = subprocess.run(
            ["sh", "-c", command, "pack-test", str(self.base), str(self.script)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        temporary = Path(record.read_text(encoding="utf-8"))
        self.assertEqual((temporary / "sentinel").read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
