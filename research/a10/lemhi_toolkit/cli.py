"""Command-line surface for the Lemhi workflow toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .adapters import FixtureAdapter, OpenSSHSlurmAdapter
from .core import Toolkit, ToolkitError, atomic_write, canonical_bytes, read_json, require, sha256_bytes
from .hardening import LedgerAnchor, derive_authority_revision

ERROR_ACTIONS = {
    "AUTH_BOOTSTRAP_REQUIRED": "operator must launch and verify both warm SSH masters",
    "CAPABILITY_STALE": "rerun probe before planning",
    "SUBMISSION_OUTCOME_UNKNOWN": "retain private state and reconcile the registered token; do not resubmit",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lemhi-toolkit")
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--provider-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-id")
    parser.add_argument("--adapter", choices=("fixture", "live"), default="live")
    parser.add_argument("--fixture-root", type=Path)
    parser.add_argument("--scenario", type=Path)
    subcommands = parser.add_subparsers(dest="command", required=True)
    initialize = subcommands.add_parser("initialize-authority")
    initialize.add_argument("--output", type=Path, required=True)
    derive = subcommands.add_parser("derive-run")
    derive.add_argument("--input", type=Path, required=True)
    derive.add_argument("--output", type=Path, required=True)
    for command in ("doctor", "probe", "prepare", "stage", "verify", "collect", "clean", "close", "abort"):
        subcommands.add_parser(command)
    plan = subcommands.add_parser("plan")
    plan.add_argument("--input", type=Path, required=True)
    amend = subcommands.add_parser("amend")
    amend.add_argument("--input", type=Path, required=True)
    amend.add_argument("--reason", required=True)
    amend.add_argument("--changed-field", action="append", default=[])
    submit = subcommands.add_parser("submit")
    submit.add_argument("--job-role", required=True)
    submit.add_argument("--attempt-index", required=True, type=int)
    observe = subcommands.add_parser("observe")
    observe.add_argument("--job-role", required=True)
    observe.add_argument("--attempt-index", required=True, type=int)
    stop_matrix = subcommands.add_parser("stop-matrix")
    stop_matrix.add_argument("--trigger-job-role", required=True)
    stop_matrix.add_argument(
        "--reason-code",
        choices=("upstream-role-exhausted",),
        required=True,
    )
    recover = subcommands.add_parser("recover")
    recover.add_argument("--job-role", required=True)
    recover.add_argument("--attempt-index", required=True, type=int)
    subcommands.add_parser("observe-recovery")
    cancel = subcommands.add_parser("cancel")
    cancel.add_argument("--job-role", required=True)
    cancel.add_argument("--attempt-index", required=True, type=int)
    register_cancelled = subcommands.add_parser("register-cancelled-recovery")
    register_cancelled.add_argument("--job-role", required=True)
    register_cancelled.add_argument("--attempt-index", required=True, type=int)
    register_cancelled.add_argument("--input", type=Path, required=True)
    register_external = subcommands.add_parser("register-external-cleanup")
    register_external.add_argument("--job-role", required=True)
    register_external.add_argument("--attempt-index", required=True, type=int)
    register_external.add_argument("--input", type=Path, required=True)
    return parser


def _output(value: Any) -> None:
    if value is None:
        value = {"status": "PASS"}
    elif isinstance(value, str):
        value = {"result": value}
    sys.stdout.write(canonical_bytes(value).decode("utf-8") + "\n")


def main(arguments: list[str] | None = None) -> int:
    parser = _parser()
    options = parser.parse_args(arguments)
    try:
        authority = read_json(options.authority)
        if options.command == "initialize-authority":
            anchor_path = Path(authority["ledger_anchor"])
            anchor = LedgerAnchor(
                anchor_path,
                authority["authority_id"],
                authority["resource_budget_id"],
                authority["resource_ceiling_gpu_minutes"],
            )
            genesis = anchor.initialize(
                authorized=authority.get("genesis_authorized") is True,
                predecessor_evidence=authority.get("predecessor_evidence", []),
                scheduler_evidence=authority.get("scheduler_evidence", []),
            )
            initialized = dict(authority)
            initialized.pop("genesis_authorized", None)
            initialized.pop("predecessor_evidence", None)
            initialized.pop("scheduler_evidence", None)
            initialized.update({
                "schema_version": "lemhi-authority-revision-2",
                "authority_revision": 0,
                "ledger_genesis_sha256": genesis,
                "ledger_head_checkpoint": genesis,
            })
            initialized["authority_revision_sha256"] = sha256_bytes(canonical_bytes(initialized))
            atomic_write(options.output, initialized, private=True)
            _output({"authority_revision_sha256": initialized["authority_revision_sha256"], "ledger_head_checkpoint": genesis})
            return 0
        if options.command == "derive-run":
            revision = derive_authority_revision(authority, read_json(options.input))
            atomic_write(options.output, revision, private=True)
            _output({"authority_revision_sha256": revision["authority_revision_sha256"], "run_id": revision["run_id"]})
            return 0
        require(options.profile is not None, "AUTHORITY_INVALID", "--profile is required")
        require(options.run_id is not None, "AUTHORITY_INVALID", "--run-id is required")
        profile = read_json(options.profile)
        if profile.get("provider_api_version") == 2:
            require(options.state_root is None or options.adapter == "fixture", "AUTHORITY_INVALID", "live v2 state root comes from authority ledger anchor")
            state_root = Path(authority["ledger_anchor"]).resolve().parents[2]
        else:
            require(options.state_root is not None, "AUTHORITY_INVALID", "--state-root is required for revision 1")
            state_root = options.state_root
        if options.adapter == "fixture":
            if options.fixture_root is None:
                parser.error("--fixture-root is required for fixture adapter")
            scenario: dict[str, Any] = read_json(options.scenario) if options.scenario else {}
            adapter = FixtureAdapter(options.fixture_root, scenario)
        else:
            scripts = Path(__file__).with_name("remote")
            adapter = OpenSSHSlurmAdapter(scripts)
        toolkit = Toolkit(
            state_root,
            authority,
            profile,
            options.run_id,
            adapter,
            provider_root=options.provider_root,
        )
        command = options.command
        if command == "plan":
            result = toolkit.plan(read_json(options.input))
        elif command == "amend":
            result = toolkit.amend(read_json(options.input), options.reason, options.changed_field)
        elif command in {"submit", "observe", "cancel", "recover"}:
            result = getattr(toolkit, command)(options.job_role, options.attempt_index)
        elif command == "register-cancelled-recovery":
            result = toolkit.register_cancelled_recovery(
                options.job_role, options.attempt_index, read_json(options.input)
            )
        elif command == "register-external-cleanup":
            result = toolkit.register_external_cleanup(
                options.job_role, options.attempt_index, read_json(options.input)
            )
        elif command == "stop-matrix":
            result = toolkit.stop_matrix(
                options.trigger_job_role, options.reason_code
            )
        elif command == "observe-recovery":
            result = toolkit.observe_recovery()
        else:
            result = getattr(toolkit, command)()
        if command in {"doctor", "prepare"}:
            result = read_json(toolkit.publication_dir / f"{command}.json")
        _output(result)
        return 0
    except ToolkitError as error:
        safe = {
            "error": error.code,
            "operation": options.command,
            "next_action": ERROR_ACTIONS.get(error.code, "inspect restricted private state and correct the frozen input; do not broaden authority"),
        }
        sys.stderr.write(json.dumps(safe, separators=(",", ":")) + "\n")
        return 2
