#!/usr/bin/python3.11
"""Fail-closed admission checker for staged A10M5R10R1R4 submissions."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

PACKAGE_ID = "20260719-a10m5r10r1r4-science-environment-closure-remedy"
RUN_ID = "a10m5r10r1r4-science-environment-closure-remedy-r0"
CONTROL_ROLE = "control-materialization"
ACTIVE_STATES = {"REGISTERED", "RESERVED", "SUBMITTED", "TERMINAL_OBSERVED"}
HEX64 = re.compile(r"[0-9a-f]{64}")


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def control_plane_python() -> dict[str, Any]:
    executable = Path(sys.executable)
    return {
        "identity": {
            "bytes": executable.stat().st_size,
            "sha256": digest(executable),
        },
        "path": sys.executable,
        "resolved_path": str(executable.resolve()),
        "version": sys.version.split()[0],
    }


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def record_hash(value: dict[str, Any]) -> str:
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    return hashlib.sha256(canonical(semantic)).hexdigest()


def authenticate_record(value: dict[str, Any]) -> bool:
    recorded = value.get("record_sha256")
    return isinstance(recorded, str) and HEX64.fullmatch(recorded) is not None and (
        recorded == record_hash(value)
    )


def atomic_create(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".promote.{os.getpid()}")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        os.link(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def current_plan(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    plan_id = state.get("current_plan_id")
    if not isinstance(plan_id, str) or HEX64.fullmatch(plan_id) is None:
        raise ValueError("toolkit state lacks a current plan identity")
    matches = [
        item.get("semantic")
        for item in state.get("plan_revisions", [])
        if isinstance(item, dict) and item.get("plan_id") == plan_id
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise ValueError("toolkit current plan is absent or ambiguous")
    return plan_id, matches[0]


def parse_setups(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for item in values:
        role, separator, raw_path = item.partition("=")
        if not separator or not role or not raw_path or role in result:
            raise ValueError(f"invalid or duplicate --setup value: {item}")
        result[role] = Path(raw_path)
    return result


def expected_asset_identity(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    value = manifest.get("assets", {}).get(name)
    if not isinstance(value, dict):
        raise ValueError(f"asset manifest lacks {name}")
    return {"bytes": value.get("bytes"), "sha256": value.get("sha256")}


def setup_ready(
    path: Path,
    *,
    role: str,
    attempt: dict[str, Any],
    source_commit: str,
    manifest: dict[str, Any],
    manifest_sha256: str,
    manifest_bytes: int,
) -> tuple[bool, str | None]:
    if not path.is_file():
        return False, None
    setup = read_json(path)
    execution = setup.get("execution_identity", {})
    identities = setup.get("identities", {})
    cleanup = setup.get("cleanup", {})
    exits = setup.get("exit_codes", {})
    authentication = setup.get("authentication", {})
    expected_identities = {
        "runtime_archive": expected_asset_identity(manifest, "runtime.tar.gz"),
        "wheelhouse_archive": expected_asset_identity(manifest, "wheelhouse.tar"),
        "requirements_lock": expected_asset_identity(manifest, "requirements.lock"),
    }
    actual_identities = {
        name: {
            "bytes": identities.get(name, {}).get("bytes"),
            "sha256": identities.get(name, {}).get("sha256"),
        }
        for name in expected_identities
    }
    ready = (
        authenticate_record(setup)
        and setup.get("valid") is True
        and setup.get("ready_for_science") is True
        and setup.get("stage") == "ready-for-science"
        and execution.get("run_id") == RUN_ID
        and execution.get("role") == role
        and execution.get("job_id") == attempt.get("job_id")
        and isinstance(execution.get("node"), str)
        and bool(execution.get("node"))
        and isinstance(execution.get("owner_marker_sha256"), str)
        and HEX64.fullmatch(execution["owner_marker_sha256"]) is not None
        and execution.get("source_commit") == source_commit
        and execution.get("host_python_path")
        == "[JOB_LOCAL]/runtime/cpython/bin/python3"
        and isinstance(execution.get("host_python_version"), str)
        and re.fullmatch(r"Python 3\.11\.\d+", execution["host_python_version"])
        is not None
        and execution.get("asset_manifest_sha256") == manifest_sha256
        and execution.get("submission_admission_authenticated") is True
        and isinstance(execution.get("submission_admission_record_sha256"), str)
        and HEX64.fullmatch(execution["submission_admission_record_sha256"])
        is not None
        and authentication
        == {
            "asset_identities_authenticated": True,
            "execution_identity_authenticated": True,
            "portable_compute_python_authenticated": True,
            "submission_admission_authenticated": True,
        }
        and identities.get("asset_manifest", {}).get("bytes") == manifest_bytes
        and identities.get("asset_manifest", {}).get("sha256")
        == manifest_sha256
        and actual_identities == expected_identities
        and exits
        == {
            "host_python_version": 0,
            "pip_check": 0,
            "pip_install": 0,
            "runtime_version": 0,
        }
        and cleanup.get("wheelhouse_deleted_before_science") is True
        and cleanup.get("pip_cache_deleted_before_science") is True
    )
    return ready, digest(path)


def job_receipt(
    publication: Path,
    role: str,
    attempt: dict[str, Any],
    *,
    require_pass: bool,
) -> tuple[bool, str | None]:
    path = publication / f"job-{role}.0.json"
    if not path.is_file():
        return False, None
    receipt = read_json(path)
    result = receipt.get("result", {})
    gates = result.get("gates", {})
    valid = (
        authenticate_record(receipt)
        and receipt.get("run_id") == RUN_ID
        and receipt.get("package_id") == PACKAGE_ID
        and receipt.get("job_role") == role
        and receipt.get("attempt_index") == 0
        and receipt.get("job_id") == attempt.get("job_id")
        and result.get("terminal") is True
        and gates.get("job_local_cleanup") is True
        and (
            receipt.get("passed") is True and attempt.get("passed") is True
            if require_pass
            else True
        )
    )
    return valid, digest(path)


def check(options: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    contract = read_json(options.contract)
    manifest = read_json(options.asset_manifest)
    state = read_json(options.toolkit_state)
    setups = parse_setups(options.setup)
    plan_id, plan = current_plan(state)
    waves = contract.get("admission", {}).get("waves", [])
    roles = [role for wave in waves for role in wave]
    all_roles = [CONTROL_ROLE, *roles]
    plan_jobs = plan.get("jobs", [])
    plan_roles = [item.get("role") for item in plan_jobs if isinstance(item, dict)]
    allowlist = set(plan.get("evidence_allowlist", []))
    manifest_sha256 = digest(options.asset_manifest)
    manifest_bytes = options.asset_manifest.stat().st_size
    source_commit = manifest.get("source_commit")
    attempts = state.get("attempts", {})
    host_python = options.control_plane_python
    if not isinstance(attempts, dict):
        attempts = {}
    target = options.role
    target_key = f"{target}.0"
    remote_root = options.remote_run_root.resolve()
    expected_output = remote_root / "admissions" / f"{target}.json"
    remote_paths_exact = (
        options.contract.resolve() == remote_root / "job-local-capacity-contract.json"
        and options.asset_manifest.resolve() == remote_root / "asset-manifest.json"
        and options.output.resolve() == expected_output
        and options.toolkit_state.resolve()
        == remote_root / "admission-input" / "state.json"
        and options.publication_dir.resolve()
        == remote_root / "admission-input" / "publication"
    )
    for setup_role, setup_path in setups.items():
        remote_paths_exact = remote_paths_exact and (
            setup_path.resolve()
            == remote_root / "results" / setup_role / "setup.json"
        )
    gates: dict[str, bool] = {
        "asset_manifest_identity": (
            isinstance(source_commit, str)
            and state.get("source_commit") == source_commit
            and plan.get("source_commit") == source_commit
        ),
        "contract_identity": (
            contract.get("package_id") == PACKAGE_ID
            and state.get("package_id") == PACKAGE_ID
            and state.get("run_id") == RUN_ID
        ),
        "exact_role_matrix": plan_roles == all_roles and len(set(plan_roles)) == 11,
        "plan_record_identity": hashlib.sha256(canonical(plan)).hexdigest()
        == plan_id,
        "admission_receipts_allowlisted": all(
            f"admissions/{role}.json" in allowlist for role in all_roles
        ),
        "single_attempt_plan": all(
            item.get("max_attempts") == 1 and item.get("retry_on") == []
            for item in plan_jobs
            if isinstance(item, dict)
        ),
        "target_role_unattempted": target_key not in attempts,
        "staged_remote_paths_exact": remote_paths_exact,
        "control_plane_python311": (
            host_python.get("path") == "/usr/bin/python3.11"
            and isinstance(host_python.get("resolved_path"), str)
            and host_python["resolved_path"].startswith("/")
            and isinstance(host_python.get("version"), str)
            and re.fullmatch(r"3\.11\.\d+", host_python["version"]) is not None
            and isinstance(host_python.get("identity"), dict)
            and isinstance(host_python["identity"].get("bytes"), int)
            and host_python["identity"]["bytes"] > 0
            and isinstance(host_python["identity"].get("sha256"), str)
            and HEX64.fullmatch(host_python["identity"]["sha256"]) is not None
        ),
    }
    input_hashes: dict[str, Any] = {
        "asset_manifest_sha256": manifest_sha256,
        "control_plane_python": host_python,
        "contract_sha256": digest(options.contract),
        "plan_id": plan_id,
        "toolkit_state_sha256": digest(options.toolkit_state),
    }
    sequence: dict[str, Any]

    if target == CONTROL_ROLE:
        gates.update(
            {
                "control_predecessor": True,
                "first_role_setup_ready": True,
                "maximum_live_candidate_jobs": len(attempts) == 0,
                "maximum_simultaneous_bootstraps": len(attempts) == 0,
                "prior_wave_terminal_observed_cleanup": True,
                "run_verified_before_control": state.get("run_state") == "VERIFIED",
            }
        )
        gates["setup_inputs_exact"] = not setups
        sequence = {"kind": "control", "member_index": 0, "wave_index": None}
    else:
        if target not in roles:
            raise ValueError(f"role is outside the frozen matrix: {target}")
        wave_index = next(index for index, wave in enumerate(waves) if target in wave)
        member_index = waves[wave_index].index(target)
        control = attempts.get(f"{CONTROL_ROLE}.0")
        control_valid = isinstance(control, dict) and control.get("state") == "RESULT_VALIDATED"
        control_hash = None
        if control_valid:
            control_valid, control_hash = job_receipt(
                options.publication_dir, CONTROL_ROLE, control, require_pass=True
            )
        gates["control_predecessor"] = control_valid
        if control_hash is not None:
            input_hashes["control_job_receipt_sha256"] = control_hash
        gates["no_observed_candidate_failure"] = (
            contract["admission"].get(
                "admission_closes_after_any_observed_candidate_failure"
            )
            is True
            and not any(
                isinstance(attempt, dict)
                and attempt.get("job_role") in roles
                and attempt.get("state") == "RESULT_VALIDATED"
                and attempt.get("passed") is False
                for attempt in attempts.values()
            )
        )

        prior_roles = [role for wave in waves[:wave_index] for role in wave]
        prior_valid = True
        prior_hashes: dict[str, str] = {}
        for role in prior_roles:
            attempt = attempts.get(f"{role}.0")
            valid = isinstance(attempt, dict) and attempt.get("state") == "RESULT_VALIDATED"
            receipt_hash = None
            if valid:
                valid, receipt_hash = job_receipt(
                    options.publication_dir, role, attempt, require_pass=True
                )
            prior_valid = prior_valid and valid
            if receipt_hash is not None:
                prior_hashes[role] = receipt_hash
        gates["prior_wave_terminal_observed_cleanup"] = prior_valid
        input_hashes["prior_wave_job_receipts"] = prior_hashes

        active = {
            item.get("job_role"): item
            for item in attempts.values()
            if isinstance(item, dict)
            and item.get("job_role") in roles
            and item.get("state") in ACTIVE_STATES
        }
        gates["maximum_live_candidate_jobs"] = len(active) + 1 <= contract[
            "admission"
        ]["maximum_live_candidate_jobs"]
        setup_hashes: dict[str, str] = {}
        active_ready = True
        for role, attempt in active.items():
            ready, setup_hash = setup_ready(
                setups.get(role, Path("/nonexistent")),
                role=role,
                attempt=attempt,
                source_commit=source_commit,
                manifest=manifest,
                manifest_sha256=manifest_sha256,
                manifest_bytes=manifest_bytes,
            )
            active_ready = active_ready and ready
            if setup_hash is not None:
                setup_hashes[role] = setup_hash
        gates["maximum_simultaneous_bootstraps"] = (
            active_ready
            and 1 <= contract["admission"]["maximum_simultaneous_bootstraps"]
        )

        first_role = waves[wave_index][0]
        if member_index == 0:
            gates["first_role_setup_ready"] = True
            gates["same_wave_order"] = not active
            expected_setup_roles: set[str] = set()
        else:
            first_attempt = attempts.get(f"{first_role}.0")
            first_state_valid = isinstance(first_attempt, dict) and first_attempt.get(
                "state"
            ) in {"SUBMITTED", "RESULT_VALIDATED"}
            first_ready = False
            first_setup_hash = None
            if first_state_valid:
                first_ready, first_setup_hash = setup_ready(
                    setups.get(first_role, Path("/nonexistent")),
                    role=first_role,
                    attempt=first_attempt,
                    source_commit=source_commit,
                    manifest=manifest,
                    manifest_sha256=manifest_sha256,
                    manifest_bytes=manifest_bytes,
                )
            gates["first_role_setup_ready"] = first_state_valid and first_ready
            gates["same_wave_order"] = set(active) <= {first_role}
            expected_setup_roles = {first_role}
            if first_setup_hash is not None:
                setup_hashes[first_role] = first_setup_hash
            if isinstance(first_attempt, dict) and first_attempt.get("state") == "RESULT_VALIDATED":
                first_terminal, first_receipt_hash = job_receipt(
                    options.publication_dir, first_role, first_attempt, require_pass=True
                )
                gates["same_wave_terminal_cleanup"] = first_terminal
                if first_receipt_hash is not None:
                    input_hashes["same_wave_job_receipt_sha256"] = first_receipt_hash
            else:
                gates["same_wave_terminal_cleanup"] = True
        gates["setup_inputs_exact"] = set(setups) == expected_setup_roles
        input_hashes["ready_setup_receipts"] = setup_hashes

        attempted_roles = {
            item.get("job_role")
            for item in attempts.values()
            if isinstance(item, dict) and item.get("job_role") in roles
        }
        allowed_attempted = set(prior_roles)
        if member_index == 1:
            allowed_attempted.add(first_role)
        gates["no_future_or_out_of_order_attempts"] = attempted_roles <= allowed_attempted
        gates["run_active_for_candidates"] = state.get("run_state") == "MATRIX_ACTIVE"
        sequence = {
            "kind": "candidate",
            "member_index": member_index,
            "wave_index": wave_index,
        }

    passed = bool(gates) and all(gates.values())
    receipt: dict[str, Any] = {
        "admission_sequence": sequence,
        "asset_manifest_sha256": manifest_sha256,
        "created_at": options.created_at,
        "decision": "PASS" if passed else "FAIL",
        "gates": dict(sorted(gates.items())),
        "input_identities": input_hashes,
        "package_id": PACKAGE_ID,
        "plan_id": plan_id,
        "pre_submission_attempts": {
            key: {
                "attempt_index": item.get("attempt_index"),
                "job_id": item.get("job_id"),
                "job_role": item.get("job_role"),
                "passed": item.get("passed"),
                "state": item.get("state"),
            }
            for key, item in sorted(attempts.items())
            if isinstance(item, dict)
        },
        "record_type": "a10m5r10r1r4-submission-admission",
        "role": target,
        "run_id": RUN_ID,
        "schema_version": 1,
        "source_commit": source_commit,
        "valid": passed,
    }
    receipt["record_sha256"] = record_hash(receipt)
    return receipt, passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--asset-manifest", type=Path, required=True)
    parser.add_argument("--toolkit-state", type=Path, required=True)
    parser.add_argument("--publication-dir", type=Path, required=True)
    parser.add_argument("--remote-run-root", type=Path, required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--setup", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--created-at",
        default=dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    options = parser.parse_args()
    options.control_plane_python = control_plane_python()
    try:
        if options.output.exists():
            raise ValueError(f"admission receipt already exists: {options.output}")
        receipt, passed = check(options)
        if not passed:
            print(json.dumps(receipt, indent=2, sort_keys=True), file=sys.stderr)
            return 1
        atomic_create(options.output, receipt)
        print(receipt["record_sha256"])
        return 0
    except (AssertionError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ADMISSION-CHECK-ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
