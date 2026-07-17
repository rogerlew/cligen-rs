"""Command-line surface for the Lemhi workflow toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .adapters import FixtureAdapter, OpenSSHSlurmAdapter
from .core import Toolkit, ToolkitError, canonical_bytes, read_json

ERROR_ACTIONS = {
    "AUTH_BOOTSTRAP_REQUIRED": "operator must launch and verify both warm SSH masters",
    "CAPABILITY_STALE": "rerun probe before planning",
    "SUBMISSION_OUTCOME_UNKNOWN": "retain private state and reconcile the registered token; do not resubmit",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lemhi-toolkit")
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--provider-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--adapter", choices=("fixture", "live"), default="live")
    parser.add_argument("--fixture-root", type=Path)
    parser.add_argument("--scenario", type=Path)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in ("doctor", "probe", "prepare", "stage", "verify", "collect", "clean", "close"):
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
    cancel = subcommands.add_parser("cancel")
    cancel.add_argument("--job-role", required=True)
    cancel.add_argument("--attempt-index", required=True, type=int)
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
        profile = read_json(options.profile)
        if options.adapter == "fixture":
            if options.fixture_root is None:
                parser.error("--fixture-root is required for fixture adapter")
            scenario: dict[str, Any] = read_json(options.scenario) if options.scenario else {}
            adapter = FixtureAdapter(options.fixture_root, scenario)
        else:
            scripts = Path(__file__).with_name("remote")
            adapter = OpenSSHSlurmAdapter(scripts)
        toolkit = Toolkit(
            options.state_root,
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
        elif command in {"submit", "observe", "cancel"}:
            result = getattr(toolkit, command)(options.job_role, options.attempt_index)
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
