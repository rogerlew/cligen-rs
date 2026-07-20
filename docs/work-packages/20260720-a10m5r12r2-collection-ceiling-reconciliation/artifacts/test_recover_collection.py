#!/usr/bin/env python3
"""Executable fixtures for the zero-allocation collection recovery."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


SCRIPT = Path(__file__).with_name("recover_collection.py")
SPEC = importlib.util.spec_from_file_location("recover_collection", SCRIPT)
assert SPEC and SPEC.loader
RECOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVERY)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def signed(value: dict[str, Any]) -> dict[str, Any]:
    output = dict(value)
    output["record_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return output


class Fixture:
    package = "20260719-a10m5r12r1-admission-materialization-remedy"
    successor = "successor-package"
    run = "parent-run"
    authority = "parent-authority"
    source = "87d38996e1f46ddb47b80c16c9625c16beaede9b"
    plan_id = "2" * 64
    marker_sha = "3" * 64
    roles = (
        "control-materialization",
        "continuous-medium-latent-process-k2",
        "continuous-hierarchical-latent-process-k2",
    )
    minutes = (16, 34, 49)

    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "parent" / "private" / "state.json"
        self.plan_path = root / "parent" / "records" / "plan.json"
        self.authority_path = root / "parent" / "records" / "authority.json"
        self.ledger_path = root / "parent" / "private" / "ledger.json"
        self.archive_path = root / "parent" / "private" / "quarantine" / "evidence.tar"
        self.publication = root / "parent" / "publication"
        self.output = root / "successor" / "private"
        self.replay = self.output / "replay" / "replay-identity.json"
        self.clean = root / "repo" / "clean.sh"
        self.clean.parent.mkdir(parents=True)
        self.clean.write_bytes(b"#!/bin/sh\nprintf 'REMOTE_ABSENT\\n'\n")
        self.contents: dict[str, bytes] = {
            "results/continuous-medium-latent-process-k2/streams.npz": b"PK\x03\x04opaque-npz",
            "results/continuous-hierarchical-latent-process-k2/checkpoint.pt": b"opaque-torch-checkpoint",
            "results/control-materialization/evidence.json": json.dumps(
                {"remote": "/ceph/home/rogerlew.ui/run", "user": "rogerlew.ui"}
            ).encode(),
            "results/continuous-medium-latent-process-k2/evidence.json": b'{"gates":{"science":true}}',
            "results/continuous-hierarchical-latent-process-k2/evidence.json": b'{"gates":{"science":true}}',
        }
        for index in range(46):
            self.contents[f"logs/{index:02d}.txt"] = f"safe log {index}\n".encode()
        assert len(self.contents) == 51
        self.make_archive()
        self.make_parent()
        self.make_config()

    def make_archive(self) -> None:
        self.archive_path.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(self.archive_path, mode="w", format=tarfile.USTAR_FORMAT) as archive:
            for name, payload in self.contents.items():
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                member.uid = member.gid = 0
                member.mode = 0o600
                archive.addfile(member, io.BytesIO(payload))

    def make_parent(self) -> None:
        self.cluster_sha = "8" * 64
        self.authority_value = {
            "authority_id": self.authority,
            "package_id": self.package,
            "resource_ceiling_gpu_minutes": 395,
            "source_commit": self.source,
        }
        self.authority_canonical_sha = hashlib.sha256(
            json.dumps(
                self.authority_value, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        jobs = [
            {"role": role, "max_attempts": 1, "retry_on": [], "gate_receipt": f"results/{role}/evidence.json"}
            for role in self.roles
        ]
        self.plan = {
            "package_id": self.package,
            "run_id": self.run,
            "source_commit": self.source,
            "remote_run_root": f"runs/{self.run}",
            "evidence_allowlist": list(self.contents),
            "evidence_replacements": [
                {"kind": "path", "token": "<REMOTE_RUN_ROOT>", "value": "/ceph/home/rogerlew.ui/run"},
                {"kind": "identity", "token": "<IDENTITY_1>", "value": "rogerlew.ui"},
            ],
            "jobs": jobs,
        }
        self.plan_semantic = {
            **self.plan,
            "cluster_profile_sha256": self.cluster_sha,
            "provider_stack": [],
        }
        self.plan_id = hashlib.sha256(
            json.dumps(
                self.plan_semantic, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        write_json(self.plan_path, self.plan)
        attempts = {}
        self.job_receipts = {}
        for index, (role, minutes) in enumerate(zip(self.roles, self.minutes)):
            key = f"{role}.0"
            gate_receipt = f"results/{role}/evidence.json"
            result = {
                "accounting": "available",
                "actual_gpu_minutes": minutes,
                "exit_code": 0,
                "gate_receipt_sha256": hashlib.sha256(
                    self.contents[gate_receipt]
                ).hexdigest(),
                "gates": {"science": True, "job_local_cleanup": True},
                "state": "COMPLETED",
                "terminal": True,
            }
            attempts[key] = {
                "attempt_index": 0,
                "job_id": f"job-{index}",
                "job_role": role,
                "passed": True,
                "plan_id": self.plan_id,
                "result": result,
                "state": "RESULT_VALIDATED",
            }
            receipt = signed(
                {
                    "job_id": f"job-{index}",
                    "passed": True,
                    "record_type": "job_receipt",
                    "result": result,
                }
            )
            receipt_path = self.publication / f"job-{key}.json"
            write_json(receipt_path, receipt)
            self.job_receipts[key] = {
                "bytes": receipt_path.stat().st_size,
                "sha256": sha(receipt_path),
            }
        self.state = {
            "attempts": attempts,
            "authority_id": self.authority,
            "authority_sha256": self.authority_canonical_sha,
            "cluster_profile_sha256": self.cluster_sha,
            "current_plan_id": self.plan_id,
            "package_id": self.package,
            "run_id": self.run,
            "run_state": "MATRIX_SETTLED",
            "source_commit": self.source,
            "plan_revisions": [
                {
                    "plan_id": self.plan_id,
                    "revision": 0,
                    "semantic": self.plan_semantic,
                }
            ],
        }
        write_json(self.state_path, self.state)
        write_json(self.authority_path, self.authority_value)
        ledger_entries = []
        predecessor = None
        semantics = [
            {"event": "genesis"},
            {
                "job_role": "toolkit-recovery",
                "requested_gpu_minutes": 5,
                "status": "reserved",
                "token": "fixture-recovery-token",
            },
            *[
                {"actual_gpu_minutes": minutes, "status": "settled"}
                for minutes in self.minutes
            ],
        ]
        for sequence, fields in enumerate(semantics):
            event = {
                **fields,
                "predecessor_sha256": predecessor,
                "sequence": sequence,
            }
            event["event_sha256"] = hashlib.sha256(
                json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            predecessor = event["event_sha256"]
            ledger_entries.append(event)
        self.ledger_head_sha = predecessor
        write_json(
            self.ledger_path,
            {
                "authority_id": self.authority,
                "ceiling_gpu_minutes": 395,
                "entries": ledger_entries,
                "head_sha256": self.ledger_head_sha,
            },
        )

    def make_config(self) -> None:
        expanded = sum(len(value) for value in self.contents.values())
        self.config = {
            "schema_version": "a10m5r12r2-frozen-parent-identities-1",
            "caps": {
                "archive_bytes": self.archive_path.stat().st_size,
                "archive_members": 51,
                "expanded_bytes": expanded,
                "max_archive_bytes": 100_000_000,
                "max_expanded_bytes": 100_000_000,
                "max_member_bytes": 50_000_000,
            },
            "cleanup": {
                "script_path": str(self.clean),
                "script_repository_path": "clean.sh",
                "script_sha256": sha(self.clean),
            },
            "expected_attempts": {
                f"{role}.0": {
                    "actual_gpu_minutes": minutes,
                    "gate_receipt": f"results/{role}/evidence.json",
                    "job_id": f"job-{index}",
                }
                for index, (role, minutes) in enumerate(zip(self.roles, self.minutes))
            },
            "job_receipts": self.job_receipts,
            "parent": {
                "archive_path": str(self.archive_path),
                "archive_sha256": sha(self.archive_path),
                "authority_bytes": self.authority_path.stat().st_size,
                "authority_canonical_sha256": self.authority_canonical_sha,
                "authority_id": self.authority,
                "authority_path": str(self.authority_path),
                "authority_sha256": sha(self.authority_path),
                "cluster_profile_sha256": self.cluster_sha,
                "ledger_bytes": self.ledger_path.stat().st_size,
                "ledger_path": str(self.ledger_path),
                "ledger_sha256": sha(self.ledger_path),
                "ledger_head_sha256": self.ledger_head_sha,
                "package_id": self.package,
                "plan_id": self.plan_id,
                "plan_path": str(self.plan_path),
                "plan_sha256": sha(self.plan_path),
                "publication_dir": str(self.publication),
                "remote_archive_path": f"/remote/runs/{self.run}/evidence.tar",
                "remote_base": "/remote",
                "remote_marker_path": f"/remote/runs/{self.run}/.lemhi-toolkit-owner.json",
                "remote_marker_sha256": self.marker_sha,
                "remote_run_root": f"runs/{self.run}",
                "resource_ceiling_gpu_minutes": 395,
                "reserved_recovery_gpu_minutes": 5,
                "reserved_recovery_token": "fixture-recovery-token",
                "run_lock_path": str(self.state_path.parent.parent / ".run.lock"),
                "run_id": self.run,
                "source_commit": self.source,
                "state_path": str(self.state_path),
                "state_sha256": sha(self.state_path),
            },
            "published_source": {
                "branch": "refs/heads/main",
                "remote": "origin",
                "repository_root": str(Path.cwd()),
            },
            "projection": {
                "forbidden_publication_substrings": [
                    "rogerlew.ui",
                    "/Users/roger",
                    "/ceph/home/",
                ]
            },
            "recovery": {
                "output_root": str(self.output),
                "package_id": self.successor,
                "replay_receipt": str(self.replay),
                "sanitizer_version": "lemhi-evidence-projection-5",
            },
            "replay_contract": {
                "binary": {"bytes": 1, "sha256": "a" * 64},
                "corpus": {"bytes": 2, "sha256": "b" * 64},
                "observations": [],
                "predecessor": {"commit": "c" * 40, "sha256": "d" * 64},
                "record_type": "a10m5r12r2_replay_identity",
                "runner": {
                    "bytes": 33610,
                    "path": str(
                        Path.cwd()
                        / "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy/artifacts/jobs/temporal_select.py"
                    ),
                    "repository_path": "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy/artifacts/jobs/temporal_select.py",
                    "sha256": "49f25fdd453143a1a94eefed2cdf7aaede88f54e75894469eb9395e280f059e7",
                },
                "schema_version": "a10m5r12r2-replay-identity-1",
                "terminals": ["A10M5R12-TEMPORAL-READY"],
            },
            "ssh": {"executable": "/usr/bin/ssh", "target": "fixture"},
            "total_actual_gpu_minutes": 99,
        }
        self.identity_path = self.root / "identities.json"
        write_json(self.identity_path, self.config)

    def remote(self, config: dict[str, Any]) -> dict[str, Any]:
        assert Path(config["parent"]["run_lock_path"]).is_dir()
        return {
            "archive_bytes": self.archive_path.stat().st_size,
            "archive_sha256": sha(self.archive_path),
            "marker_bytes": 449,
            "marker_sha256": self.marker_sha,
        }

    def published(self, _config: dict[str, Any]) -> str:
        return self.source

    def write_replay(self, **changes: Any) -> None:
        recovery_path = self.output / "collection-recovery.json"
        recovery = json.loads(recovery_path.read_text())
        predecessor_result = json.loads(
            (
                Path.cwd()
                / "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/artifacts/temporal-result.json"
            ).read_text()
        )
        pass_value = (
            json.dumps(
                {
                    "prism_provenance": predecessor_result["prism_provenance"],
                    "protected_roles_opened": [],
                    "terminal": "A10M5R12-TEMPORAL-READY",
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
            + b"\n"
        )
        pass_sha = hashlib.sha256(pass_value).hexdigest()
        for relative in (
            "pass-a/temporal-result.json",
            "pass-b/temporal-result.json",
            "temporal-result.json",
        ):
            path = self.replay.parent / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pass_value)
        parent_package = (
            Path.cwd()
            / "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy"
        )
        selector_sources = {}
        for relative in (
            "artifacts/jobs/temporal_select.py",
            "artifacts/jobs/temporal_metrics.py",
            "artifacts/temporal-contract.json",
            "artifacts/portfolio-contract.json",
            "artifacts/sites.json",
            "artifacts/calendar-control-expectation.json",
        ):
            path = parent_package / relative
            selector_sources[relative] = {
                "bytes": path.stat().st_size,
                "sha256": sha(path),
            }
        inputs = {
            "binary": self.config["replay_contract"]["binary"],
            "collection_recovery_record_sha256": recovery["record_sha256"],
            "collection_recovery_sha256": sha(recovery_path),
            "corpus": self.config["replay_contract"]["corpus"],
            "data_root": {"file_count": 1, "semantic_sha256": "e" * 64},
            "evaluation_runtime": {
                "executable": {"bytes": 1, "sha256": "f" * 64},
                "numpy": "2.2.6",
                "python": "3.10.14",
            },
            "observations": {
                "files": [],
                "semantic_sha256": hashlib.sha256(b"[]").hexdigest(),
            },
            "predecessor_temporal_result": self.config["replay_contract"][
                "predecessor"
            ],
            "published_main_head": self.source,
            "recovered_evidence_manifest_sha256": recovery[
                "recovered_evidence_manifest_sha256"
            ],
            "selector_sources": selector_sources,
        }
        if "collection_recovery_record_sha256" in changes:
            inputs["collection_recovery_record_sha256"] = changes.pop(
                "collection_recovery_record_sha256"
            )
        value = {
            "byte_identical": True,
            "inputs": inputs,
            "package_id": self.successor,
            "parent_package_id": self.package,
            "parent_plan_id": self.plan_id,
            "parent_run_id": self.run,
            "pass_a_result_sha256": pass_sha,
            "pass_b_result_sha256": pass_sha,
            "protected_roles_opened": [],
            "record_type": "a10m5r12r2_replay_identity",
            "replay_source_commit": self.source,
            "result_bytes": len(pass_value),
            "schema_version": "a10m5r12r2-replay-identity-1",
            "source_commit": self.source,
            "temporal_result_sha256": pass_sha,
            "terminal": "A10M5R12-TEMPORAL-READY",
        }
        value.update(changes)
        write_json(self.replay, signed(value))


class RecoveryTests(unittest.TestCase):
    def test_default_source_validator_checks_the_published_recovery_files(self) -> None:
        repository = SCRIPT.parents[4]
        head = "a" * 40
        config = {
            "parent": {"source_commit": "1" * 40},
            "published_source": {
                "branch": "refs/heads/main",
                "remote": "origin",
                "repository_root": str(repository),
            },
            "ssh": {"executable": "/usr/bin/ssh", "target": "lemhi"},
        }
        results = [
            mock.Mock(stdout=f"{head}\trefs/heads/main\n", returncode=0),
            mock.Mock(returncode=0),
            mock.Mock(stdout=RECOVERY.SCRIPT.read_bytes(), returncode=0),
            mock.Mock(stdout=RECOVERY.DEFAULT_IDENTITIES.read_bytes(), returncode=0),
        ]
        with mock.patch.object(RECOVERY.subprocess, "run", side_effect=results) as run:
            self.assertEqual(RECOVERY.validate_published_source(config), head)
        self.assertEqual(run.call_count, 4)
        config["ssh"]["target"] = "attacker"
        with self.assertRaisesRegex(RECOVERY.RecoveryError, "live SSH contract changed"):
            RECOVERY.validate_published_source(config)

    def test_production_cli_rejects_identity_override(self) -> None:
        with mock.patch("sys.argv", ["recover_collection.py", "recover", "--identities", "/tmp/evil"]):
            with self.assertRaises(SystemExit):
                RECOVERY.main()

    def test_recover_authenticates_51_files_and_preserves_binary_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            state_before = fixture.state_path.read_bytes()
            receipt = RECOVERY.recover_phase(
                fixture.identity_path,
                source_validator=fixture.published,
                remote_probe=fixture.remote,
            )
            self.assertEqual(receipt["actual_gpu_minutes"], 0)
            self.assertEqual(receipt["parent_actual_gpu_minutes"], 99)
            self.assertEqual(receipt["state"], "RAW_COLLECTED_EQUIVALENT")
            self.assertFalse(receipt["remote_cleanup_performed"])
            self.assertEqual(fixture.state_path.read_bytes(), state_before)
            self.assertEqual(
                (
                    fixture.output
                    / "evidence/results/continuous-medium-latent-process-k2/streams.npz"
                ).read_bytes(),
                fixture.contents[
                    "results/continuous-medium-latent-process-k2/streams.npz"
                ],
            )
            self.assertEqual(
                (
                    fixture.output
                    / "evidence/results/continuous-hierarchical-latent-process-k2/checkpoint.pt"
                ).read_bytes(),
                fixture.contents[
                    "results/continuous-hierarchical-latent-process-k2/checkpoint.pt"
                ],
            )
            projected = (
                fixture.output
                / "evidence/results/control-materialization/evidence.json"
            ).read_text()
            self.assertIn("<REMOTE_RUN_ROOT>", projected)
            self.assertIn("<IDENTITY_1>", projected)
            raw = json.loads((fixture.output / "raw/raw-collected-equivalent.json").read_text())
            self.assertEqual(len(raw["files"]), 51)
            self.assertTrue(RECOVERY.authenticated(raw))

    def test_cleanup_is_separate_and_requires_successful_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            RECOVERY.recover_phase(
                fixture.identity_path,
                source_validator=fixture.published,
                remote_probe=fixture.remote,
            )
            called: list[bool] = []
            remote_present = [True]

            def clean(_config: dict[str, Any]) -> str:
                called.append(True)
                remote_present[0] = False
                return "REMOTE_ABSENT"

            def absent(_config: dict[str, Any]) -> dict[str, bool]:
                return {
                    "archive_absent": not remote_present[0],
                    "marker_absent": not remote_present[0],
                    "run_root_absent": not remote_present[0],
                }

            with self.assertRaisesRegex(RECOVERY.RecoveryError, "replay receipt missing"):
                RECOVERY.cleanup_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    preclean_probe=fixture.remote,
                    cleanup_invoker=clean,
                    postclean_probe=absent,
                )
            self.assertEqual(called, [])
            fixture.write_replay()
            state_before = fixture.state_path.read_bytes()
            receipt = RECOVERY.cleanup_phase(
                fixture.identity_path,
                source_validator=fixture.published,
                preclean_probe=fixture.remote,
                cleanup_invoker=clean,
                postclean_probe=absent,
            )
            self.assertEqual(called, [True])
            self.assertTrue(receipt["remote_absent"])
            self.assertEqual(fixture.state_path.read_bytes(), state_before)
            self.assertTrue(RECOVERY.authenticated(receipt))

    def test_cleanup_rejects_unauthenticated_and_misbound_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            RECOVERY.recover_phase(
                fixture.identity_path,
                source_validator=fixture.published,
                remote_probe=fixture.remote,
            )
            fixture.write_replay()
            replay = json.loads(fixture.replay.read_text())
            replay["terminal"] = "tampered"
            write_json(fixture.replay, replay)
            called: list[bool] = []
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "not authenticated"):
                RECOVERY.cleanup_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    preclean_probe=fixture.remote,
                    cleanup_invoker=lambda _config: called.append(True) or "REMOTE_ABSENT",
                    postclean_probe=lambda _config: {},
                )
            self.assertEqual(called, [])
            fixture.write_replay(collection_recovery_record_sha256="0" * 64)
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "recovery-record binding"):
                RECOVERY.cleanup_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    preclean_probe=fixture.remote,
                    cleanup_invoker=lambda _config: called.append(True) or "REMOTE_ABSENT",
                    postclean_probe=lambda _config: {},
                )
            self.assertEqual(called, [])

    def test_cleanup_revalidates_before_and_proves_absence_after(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            RECOVERY.recover_phase(
                fixture.identity_path,
                source_validator=fixture.published,
                remote_probe=fixture.remote,
            )
            fixture.write_replay()
            called: list[bool] = []
            bad_snapshot = {
                "archive_bytes": fixture.archive_path.stat().st_size,
                "archive_sha256": "0" * 64,
                "marker_bytes": 449,
                "marker_sha256": fixture.marker_sha,
            }
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "remote archive changed"):
                RECOVERY.cleanup_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    preclean_probe=lambda _config: bad_snapshot,
                    cleanup_invoker=lambda _config: called.append(True) or "REMOTE_ABSENT",
                    postclean_probe=lambda _config: {},
                )
            self.assertEqual(called, [])
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "post-clean remote absence"):
                RECOVERY.cleanup_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    preclean_probe=fixture.remote,
                    cleanup_invoker=lambda _config: called.append(True) or "REMOTE_ABSENT",
                    postclean_probe=lambda _config: {},
                )
            self.assertEqual(called, [True])
            self.assertTrue((fixture.output / "cleanup-intent.json").is_file())
            self.assertFalse((fixture.output / "cleanup-recovery.json").exists())

    def test_cleanup_resumes_from_intent_after_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            RECOVERY.recover_phase(
                fixture.identity_path,
                source_validator=fixture.published,
                remote_probe=fixture.remote,
            )
            fixture.write_replay()
            remote_present = [True]
            calls: list[str] = []

            def interrupted(_config: dict[str, Any]) -> str:
                calls.append("clean")
                remote_present[0] = False
                raise RuntimeError("controller interrupted after remote deletion")

            def absence(_config: dict[str, Any]) -> dict[str, bool]:
                return {
                    "archive_absent": not remote_present[0],
                    "marker_absent": not remote_present[0],
                    "run_root_absent": not remote_present[0],
                }

            with self.assertRaisesRegex(RuntimeError, "controller interrupted"):
                RECOVERY.cleanup_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    preclean_probe=fixture.remote,
                    cleanup_invoker=interrupted,
                    postclean_probe=absence,
                )
            self.assertTrue((fixture.output / "cleanup-intent.json").is_file())
            receipt = RECOVERY.cleanup_phase(
                fixture.identity_path,
                source_validator=fixture.published,
                preclean_probe=fixture.remote,
                cleanup_invoker=lambda _config: calls.append("unexpected") or "REMOTE_ABSENT",
                postclean_probe=absence,
            )
            self.assertTrue(receipt["remote_absent"])
            self.assertEqual(calls, ["clean"])

    def test_extracted_gate_receipt_must_match_observed_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            role = fixture.roles[0]
            fixture.contents[f"results/{role}/evidence.json"] += b" "
            fixture.make_archive()
            fixture.config["caps"]["archive_bytes"] = fixture.archive_path.stat().st_size
            fixture.config["caps"]["expanded_bytes"] = sum(
                len(value) for value in fixture.contents.values()
            )
            fixture.config["parent"]["archive_sha256"] = sha(fixture.archive_path)
            write_json(fixture.identity_path, fixture.config)
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "collected gate receipt changed"):
                RECOVERY.recover_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    remote_probe=fixture.remote,
                )
            self.assertFalse(fixture.output.exists())

    def test_parent_run_lock_blocks_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            lock = Path(fixture.config["parent"]["run_lock_path"])
            lock.mkdir()
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "parent run is locked"):
                RECOVERY.recover_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    remote_probe=fixture.remote,
                )

    def test_frozen_archive_ceiling_cannot_be_relaxed_or_reduced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.config["caps"]["max_member_bytes"] = 4
            write_json(fixture.identity_path, fixture.config)
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "member ceiling changed"):
                RECOVERY.recover_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    remote_probe=fixture.remote,
                )
            self.assertFalse(fixture.output.exists())

    def test_stale_parent_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            fixture.state_path.write_bytes(fixture.state_path.read_bytes() + b" ")
            with self.assertRaisesRegex(RECOVERY.RecoveryError, "identity changed"):
                RECOVERY.recover_phase(
                    fixture.identity_path,
                    source_validator=fixture.published,
                    remote_probe=fixture.remote,
                )
            self.assertFalse(fixture.output.exists())


if __name__ == "__main__":
    unittest.main()
