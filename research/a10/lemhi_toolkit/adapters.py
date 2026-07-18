"""Injected fixture and OpenSSH/Slurm adapters for the Lemhi toolkit."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol

from .core import (
    ToolkitError,
    canonical_bytes,
    read_json,
    require,
    sha256_bytes,
    sha256_file,
    validate_relative_path,
    validate_shell_scalar,
)

REMOTE_ARGUMENT = re.compile(r"^[A-Za-z0-9_./+=:@,-]+$")


class CommandRunner(Protocol):
    """The only process-execution seam used by the live adapter."""

    def run(self, arguments: list[str], *, stdin: bytes | None = None, timeout: int = 60) -> subprocess.CompletedProcess[bytes]: ...


class SubprocessRunner:
    """Execute fixed argument vectors without a local shell."""

    def run(self, arguments: list[str], *, stdin: bytes | None = None, timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
        try:
            return subprocess.run(
                arguments,
                input=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ToolkitError("EVIDENCE_INCOMPLETE", f"command unavailable: {arguments[0]}") from error


class FixtureAdapter:
    """Deterministic filesystem-backed Lemhi substitute used by acceptance tests."""

    def __init__(self, root: Path, scenario: dict[str, Any] | None = None):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.remote = self.root / "remote"
        self.backend_path = self.root / "backend.json"
        self.scenario = scenario or {}
        if not self.backend_path.exists():
            self._save_backend({"next_job_id": 1000, "jobs": {}, "tokens": {}, "submit_calls": 0})

    def _backend(self) -> dict[str, Any]:
        return read_json(self.backend_path)

    def _save_backend(self, value: dict[str, Any]) -> None:
        temporary = self.backend_path.with_suffix(".part")
        temporary.write_bytes(canonical_bytes(value) + b"\n")
        os.replace(temporary, self.backend_path)

    def check_masters(self, profile: dict[str, Any]) -> None:
        del profile
        masters = self.scenario.get("masters", {"gateway": True, "target": True})
        require(masters.get("gateway") is True and masters.get("target") is True, "AUTH_BOOTSTRAP_REQUIRED", "launch both warm masters")

    def probe(self, profile: dict[str, Any]) -> dict[str, Any]:
        del profile
        require(not self.scenario.get("probe_allocates", False), "CAPABILITY_SCOPE_MISMATCH", "probe attempted allocation")
        return {
            "scope": "login",
            "observation_method": "fixture-login-probe",
            "platform": self.scenario.get("platform", "linux-x86_64-glibc"),
            "scheduler": "slurm",
            "unavailable": [],
            "untested": ["compute", "cuda"],
        }

    def _run_root(self, plan: dict[str, Any]) -> Path:
        relative = validate_relative_path(plan["remote_run_root"], "remote_run_root")
        return self.remote / relative

    def stage(self, profile: dict[str, Any], plan: dict[str, Any], assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.check_masters({})
        if self.scenario.get("stage_failure"):
            raise ToolkitError("TRANSFER_INCOMPLETE", "fixture transfer failed; no fallback")
        root = self._run_root(plan)
        root.mkdir(parents=True, exist_ok=True)
        marker = {
            "canonical_root": str(root.resolve()),
            "run_id": plan["run_id"],
            "package_id": plan["package_id"],
            "plan_sha256": sha256_bytes(canonical_bytes(plan)),
            "source_commit": plan["source_commit"],
            "remote_run_root": plan["remote_run_root"],
        }
        (root / ".lemhi-toolkit-owner.json").write_bytes(canonical_bytes(marker) + b"\n")
        receipts = []
        for asset in assets:
            started_ns = time.monotonic_ns()
            destination = root / asset["logical_name"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            partial = destination.with_name(destination.name + ".part")
            shutil.copyfile(asset["local_path"], partial)
            if self.scenario.get("corrupt_upload"):
                partial.write_bytes(partial.read_bytes() + b"corrupt")
            complete = partial.stat().st_size == asset["bytes"] and sha256_file(partial) == asset["sha256"]
            if complete:
                os.replace(partial, destination)
            receipt = {
                "logical_name": asset["logical_name"],
                "bytes": partial.stat().st_size if partial.exists() else destination.stat().st_size,
                "sha256": sha256_file(partial if partial.exists() else destination),
                "method": "fixture-scp",
                "partial_name": asset["logical_name"] + ".part",
                "promoted": complete,
            }
            if profile.get("provider_api_version") == 2:
                from .hardening import transfer_receipt

                receipt.update(transfer_receipt(
                    logical_name=asset["logical_name"],
                    byte_count=receipt["bytes"],
                    elapsed_ns=max(1, time.monotonic_ns() - started_ns),
                    method="fixture-scp",
                    identity_sha256=receipt["sha256"],
                    state="uploaded",
                    remote_revalidated=True,
                ))
            receipts.append(receipt)
        return receipts

    def verify(self, profile: dict[str, Any], plan: dict[str, Any], assets: list[dict[str, Any]]) -> None:
        del profile
        self.check_masters({})
        root = self._run_root(plan)
        for asset in assets:
            started_ns = time.monotonic_ns()
            destination = root / asset["logical_name"]
            require(destination.is_file(), "TRANSFER_INCOMPLETE", asset["logical_name"])
            require(destination.stat().st_size == asset["bytes"], "TRANSFER_INCOMPLETE", asset["logical_name"])
            require(sha256_file(destination) == asset["sha256"], "TRANSFER_INCOMPLETE", asset["logical_name"])

    def submit(self, profile: dict[str, Any], plan: dict[str, Any], job: dict[str, Any], token: str) -> str:
        del profile, plan
        self.check_masters({})
        backend = self._backend()
        backend["submit_calls"] += 1
        job_id = str(backend["next_job_id"])
        backend["next_job_id"] += 1
        backend["jobs"][job_id] = {"role": job["role"], "token": token, "cancelled": False, "job": job}
        backend["tokens"].setdefault(token, []).append(job_id)
        self._save_backend(backend)
        if token in self.scenario.get("lost_response_tokens", []) or self.scenario.get("lose_next_response"):
            self.scenario["lose_next_response"] = False
            raise ToolkitError("SUBMISSION_OUTCOME_UNKNOWN", "fixture accepted but response was lost")
        return job_id

    def reconcile(self, profile: dict[str, Any], token: str) -> list[str]:
        del profile
        forced = self.scenario.get("reconcile_matches")
        if forced is not None:
            return list(forced)
        return list(self._backend()["tokens"].get(token, []))

    def reconcile_authority(self, profile: dict[str, Any], authority_token: str) -> list[str]:
        del profile, authority_token
        if self.scenario.get("authority_reconciled", True) is not True:
            raise ToolkitError("AUTHORITY_RECONCILIATION_REQUIRED", "fixture accounting unavailable")
        forced = self.scenario.get("authority_job_ids")
        if forced is not None:
            return list(forced)
        return sorted(self._backend()["jobs"].keys())

    def observe(self, profile: dict[str, Any], plan: dict[str, Any], planned_job: dict[str, Any], job_id: str) -> dict[str, Any]:
        del profile, plan, planned_job
        self.check_masters({})
        job = self._backend()["jobs"].get(job_id)
        require(isinstance(job, dict), "JOB_TERMINAL_MISMATCH", job_id)
        configured = self.scenario.get("results", {}).get(job["role"], {})
        if job["cancelled"]:
            return {"terminal": True, "state": "CANCELLED", "exit_code": 1, "gates": {"cancelled": False}, "actual_gpu_minutes": 0}
        return {
            "terminal": configured.get("terminal", True),
            "state": configured.get("state", "COMPLETED"),
            "exit_code": configured.get("exit_code", job["job"].get("expected_exit_code", 0)),
            "gates": configured.get("gates", {"registered": True}),
            "actual_gpu_minutes": configured.get("actual_gpu_minutes"),
            "accounting": "unavailable" if configured.get("actual_gpu_minutes") is None else "available",
        }

    def cancel(self, profile: dict[str, Any], job_id: str) -> dict[str, Any]:
        del profile
        self.check_masters({})
        backend = self._backend()
        require(job_id in backend["jobs"], "JOB_TERMINAL_MISMATCH", job_id)
        backend["jobs"][job_id]["cancelled"] = True
        self._save_backend(backend)
        return {"job_id": job_id, "acknowledged": True}

    def collect(self, profile: dict[str, Any], plan: dict[str, Any], quarantine: Path) -> dict[str, Any]:
        del profile
        self.check_masters({})
        partial = quarantine / "evidence.json.part"
        final = quarantine / "evidence.json"
        content = self.scenario.get("evidence", {"classification": "synthetic", "verdict": "PASS"})
        partial.write_bytes(canonical_bytes(content) + b"\n")
        remote_hash = self.scenario.get("remote_evidence_sha256", sha256_file(partial))
        remote_bytes = self.scenario.get("remote_evidence_bytes", partial.stat().st_size)
        promoted = sha256_file(partial) == remote_hash and partial.stat().st_size == remote_bytes
        if promoted:
            os.replace(partial, final)
        result = {
            "logical_name": "evidence.json",
            "bytes": remote_bytes,
            "sha256": remote_hash,
            "download_promoted": promoted,
            "sanitization_policy": "fixture-publication-v1",
        }
        marker = self._run_root(plan) / ".lemhi-toolkit-owner.json"
        if marker.is_file():
            result["cleanup_marker_sha256"] = sha256_file(marker)
        return result

    def clean(self, profile: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        del profile
        self.check_masters({})
        root = self._run_root(plan)
        require(root.is_dir() and not root.is_symlink(), "CLEANUP_TARGET_INVALID", "registered root absent or escaped")
        marker_path = root / ".lemhi-toolkit-owner.json"
        require(marker_path.is_file() and not marker_path.is_symlink(), "CLEANUP_TARGET_INVALID", "owner marker")
        marker = read_json(marker_path)
        expected = {
            "canonical_root": str(root.resolve()),
            "run_id": plan["run_id"],
            "package_id": plan["package_id"],
            "plan_sha256": sha256_bytes(canonical_bytes(plan)),
            "source_commit": plan["source_commit"],
            "remote_run_root": plan["remote_run_root"],
        }
        require(marker == expected, "CLEANUP_TARGET_INVALID", "owner marker mismatch")
        if self.scenario.get("replace_before_cleanup"):
            marker_path.write_text("{}\n", encoding="utf-8")
        require(read_json(marker_path) == expected, "CLEANUP_TARGET_INVALID", "owner marker changed")
        shutil.rmtree(root)
        default_cleanup = "verified_absent" if plan.get("job_local_cleanup") == "toolkit_recoverable" else "scheduler_purged"
        job_local = self.scenario.get("job_local_cleanup", default_cleanup)
        return {"remote_absent": not root.exists(), "job_local_cleanup": job_local}


class OpenSSHSlurmAdapter:
    """Live Lemhi adapter; it never opens an interactive authentication path."""

    def __init__(self, scripts_root: Path, runner: CommandRunner | None = None):
        self.scripts_root = scripts_root.resolve()
        self.runner = runner or SubprocessRunner()

    @staticmethod
    def _ssh_options(profile: dict[str, Any]) -> list[str]:
        timeout = str(profile.get("connect_timeout_seconds", 10))
        return ["-oBatchMode=yes", f"-oConnectTimeout={timeout}", "-oStrictHostKeyChecking=yes"]

    def _run(self, arguments: list[str], *, stdin: bytes | None = None, timeout: int = 60, code: str = "EVIDENCE_INCOMPLETE") -> bytes:
        result = self.runner.run(arguments, stdin=stdin, timeout=timeout)
        if result.returncode != 0:
            raise ToolkitError(code, f"{arguments[0]} operation failed with status {result.returncode}")
        return result.stdout

    def _remote_script(self, profile: dict[str, Any], name: str, arguments: list[str], *, timeout: int | None = None) -> bytes:
        target = validate_shell_scalar(profile["target"], "target")
        require(all(REMOTE_ARGUMENT.fullmatch(item) is not None for item in arguments), "ALLOWLIST_VIOLATION", "unsafe remote argument")
        script = (self.scripts_root / name).read_bytes()
        command = ["ssh", *self._ssh_options(profile), target, "sh", "-s", "--", *arguments]
        return self._run(command, stdin=script, timeout=timeout or profile.get("operation_timeout_seconds", 120))

    def check_masters(self, profile: dict[str, Any]) -> None:
        for endpoint in (profile["gateway"], profile["target"]):
            endpoint = validate_shell_scalar(endpoint, "endpoint")
            result = self.runner.run(["ssh", "-oBatchMode=yes", "-O", "check", endpoint], timeout=10)
            require(result.returncode == 0, "AUTH_BOOTSTRAP_REQUIRED", "launch both warm masters")

    def probe(self, profile: dict[str, Any]) -> dict[str, Any]:
        output = self._remote_script(profile, "probe.sh", [])
        try:
            facts = json.loads(output)
        except json.JSONDecodeError as error:
            raise ToolkitError("EVIDENCE_INCOMPLETE", "invalid probe response") from error
        require(isinstance(facts, dict), "EVIDENCE_INCOMPLETE", "invalid probe response")
        return facts

    def stage(self, profile: dict[str, Any], plan: dict[str, Any], assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        remote_base = validate_shell_scalar(profile["remote_base"], "remote_base")
        run_root = validate_relative_path(plan["remote_run_root"], "remote_run_root")
        self._remote_script(profile, "create_run.sh", [remote_base, run_root], timeout=30)
        self._remote_script(
            profile,
            "write_marker.sh",
            [remote_base, run_root, plan["run_id"], plan["package_id"], plan["source_commit"], sha256_bytes(canonical_bytes(plan))],
            timeout=30,
        )
        receipts = []
        target = validate_shell_scalar(profile["target"], "target")
        for asset in assets:
            started_ns = time.monotonic_ns()
            logical = validate_relative_path(asset["logical_name"], "logical_name")
            remote_part = f"{remote_base}/{run_root}/{logical}.part"
            self._run(["scp", *self._ssh_options(profile), "--", asset["local_path"], f"{target}:{remote_part}"], timeout=profile.get("transfer_timeout_seconds", 600), code="TRANSFER_INCOMPLETE")
            self._remote_script(profile, "promote.sh", [remote_base, run_root, logical, str(asset["bytes"]), asset["sha256"]])
            receipt = {"logical_name": logical, "bytes": asset["bytes"], "sha256": asset["sha256"], "method": "scp", "partial_name": logical + ".part", "promoted": True}
            if profile.get("provider_api_version") == 2:
                from .hardening import transfer_receipt

                receipt.update(transfer_receipt(
                    logical_name=logical,
                    byte_count=asset["bytes"],
                    elapsed_ns=max(1, time.monotonic_ns() - started_ns),
                    method="scp",
                    identity_sha256=asset["sha256"],
                    state="uploaded",
                    remote_revalidated=True,
                ))
            receipts.append(receipt)
        return receipts

    def verify(self, profile: dict[str, Any], plan: dict[str, Any], assets: list[dict[str, Any]]) -> None:
        for asset in assets:
            self._remote_script(profile, "verify.sh", [profile["remote_base"], plan["remote_run_root"], asset["logical_name"], str(asset["bytes"]), asset["sha256"]])

    def submit(self, profile: dict[str, Any], plan: dict[str, Any], job: dict[str, Any], token: str) -> str:
        stdout = f"slurm/{job['role']}.{job['attempt_index']}.out"
        stderr = f"slurm/{job['role']}.{job['attempt_index']}.err"
        require(stdout in plan["evidence_allowlist"] and stderr in plan["evidence_allowlist"], "ALLOWLIST_VIOLATION", "job logs not allowlisted")
        arguments = [profile["remote_base"], plan["remote_run_root"], job["script"], job["partition"], job["gres"], str(job["cpus"]), str(job["memory_mb"]), str(job["time_limit_minutes"]), token]
        if profile.get("provider_api_version") == 2:
            arguments.append(plan["scheduler_authority_token"])
        arguments.extend([stdout, stderr])
        submit_script = "submit_v2.sh" if profile.get("provider_api_version") == 2 else "submit.sh"
        output = self._remote_script(profile, submit_script, arguments).decode("utf-8").strip()
        if not output.isdigit():
            raise ToolkitError("SUBMISSION_OUTCOME_UNKNOWN", "sbatch response requires token reconciliation")
        return output

    def reconcile(self, profile: dict[str, Any], token: str) -> list[str]:
        output = self._remote_script(profile, "reconcile.sh", [token]).decode("utf-8")
        return [line for line in output.splitlines() if line.isdigit()]

    def reconcile_authority(self, profile: dict[str, Any], authority_token: str) -> list[str]:
        output = self._remote_script(profile, "reconcile_authority.sh", [validate_shell_scalar(authority_token, "authority token")]).decode("utf-8")
        job_ids = [line for line in output.splitlines() if line]
        require(all(item.isdigit() for item in job_ids), "AUTHORITY_RECONCILIATION_REQUIRED", "invalid authority accounting")
        require(len(job_ids) == len(set(job_ids)), "AUTHORITY_RECONCILIATION_REQUIRED", "duplicate authority accounting")
        return job_ids

    def observe(self, profile: dict[str, Any], plan: dict[str, Any], job: dict[str, Any], job_id: str) -> dict[str, Any]:
        output = self._remote_script(profile, "observe.sh", [validate_shell_scalar(job_id, "job_id")]).decode("utf-8")
        try:
            value = json.loads(output)
        except json.JSONDecodeError as error:
            raise ToolkitError("EVIDENCE_INCOMPLETE", "invalid accounting response") from error
        require(isinstance(value, dict), "EVIDENCE_INCOMPLETE", "invalid accounting response")
        if value.get("terminal") is True and value.get("exit_code") == job.get("expected_exit_code", 0):
            receipt = self._remote_script(
                profile,
                "read_gate.sh",
                [profile["remote_base"], plan["remote_run_root"], job["gate_receipt"]],
            )
            try:
                evidence = json.loads(receipt)
            except json.JSONDecodeError as error:
                raise ToolkitError("EVIDENCE_INCOMPLETE", "invalid gate receipt") from error
            gates = evidence.get("gates") if isinstance(evidence, dict) else None
            require(isinstance(gates, dict) and gates, "EVIDENCE_INCOMPLETE", "gate receipt has no gates")
            require(all(isinstance(name, str) and isinstance(passed, bool) for name, passed in gates.items()), "EVIDENCE_INCOMPLETE", "invalid gates")
            value["gates"] = gates
            value["gate_receipt_sha256"] = sha256_bytes(receipt)
        return value

    def cancel(self, profile: dict[str, Any], job_id: str) -> dict[str, Any]:
        self._remote_script(profile, "cancel.sh", [validate_shell_scalar(job_id, "job_id")])
        return {"job_id": job_id, "acknowledged": True}

    def collect(self, profile: dict[str, Any], plan: dict[str, Any], quarantine: Path) -> dict[str, Any]:
        metadata = json.loads(self._remote_script(profile, "pack_evidence.sh", [profile["remote_base"], plan["remote_run_root"], *plan["evidence_allowlist"]]))
        logical = validate_relative_path(metadata["logical_name"], "evidence archive")
        partial = quarantine / (logical + ".part")
        partial.parent.mkdir(parents=True, exist_ok=True)
        target = validate_shell_scalar(profile["target"], "target")
        remote = f"{profile['remote_base']}/{plan['remote_run_root']}/{logical}"
        self._run(["scp", *self._ssh_options(profile), "--", f"{target}:{remote}", str(partial)], timeout=profile.get("transfer_timeout_seconds", 600), code="TRANSFER_INCOMPLETE")
        promoted = partial.stat().st_size == metadata["bytes"] and sha256_file(partial) == metadata["sha256"]
        if promoted:
            os.replace(partial, quarantine / logical)
        result = {**metadata, "download_promoted": promoted, "sanitization_policy": "lemhi-evidence-v1"}
        if profile.get("provider_api_version") == 2:
            result["cleanup_marker_sha256"] = self._remote_script(
                profile,
                "hash_marker.sh",
                [profile["remote_base"], plan["remote_run_root"]],
            ).decode("utf-8").strip()
            result["sanitization_policy"] = "lemhi-evidence-projection-2"
        return result

    def clean(self, profile: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        job_local_cleanup = plan["job_local_cleanup"]
        if profile.get("provider_api_version") == 2:
            for gate_receipt in sorted({job["gate_receipt"] for job in plan["jobs"]}):
                receipt = self._remote_script(
                    profile,
                    "read_gate.sh",
                    [profile["remote_base"], plan["remote_run_root"], gate_receipt],
                )
                try:
                    evidence = json.loads(receipt)
                except json.JSONDecodeError as error:
                    raise ToolkitError("CLEANUP_INCOMPLETE", "invalid job-local cleanup receipt") from error
                gates = evidence.get("gates") if isinstance(evidence, dict) else None
                require(
                    isinstance(gates, dict) and gates.get("job_local_cleanup") is True,
                    "CLEANUP_INCOMPLETE",
                    "job-local absence not authenticated",
                )
            job_local_cleanup = "verified_absent"
        output = self._remote_script(profile, "clean.sh", [profile["remote_base"], plan["remote_run_root"], plan["run_id"], plan["package_id"], plan["source_commit"], sha256_bytes(canonical_bytes(plan))]).decode("utf-8").strip()
        require(output == "REMOTE_ABSENT", "CLEANUP_INCOMPLETE", "remote cleanup not proven")
        return {"remote_absent": True, "job_local_cleanup": job_local_cleanup}
