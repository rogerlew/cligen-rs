#!/usr/bin/env python3
"""Run the accepted A5a verifier while admitting one frozen A5b source extension.

The accepted verifier binds the *entire* historical ``crates/**/*.rs`` file
set. A5b necessarily adds ``cligen-a5b-overlay.rs``, so invoking that verifier
against the extended checkout would reject the new file before examining the
accepted evidence. This wrapper proves every historical file still has its
accepted hash, proves that the overlay is the sole extra implementation file,
then runs every original verification check with the historical identity from
the accepted manifest. No accepted A5a byte or verifier is modified.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
A5A = ROOT / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts"
VERIFIER = A5A / "verify-baseline-evidence.py"
MANIFEST = A5A / "baseline-run-manifest-v1.json"
VERIFIER_SHA256 = "9a3fbdb4d35ec693db6bad916b1cb941c3c3ebec93340a05899f103f269b32f1"
MANIFEST_SHA256 = "e6e12a08b7d552edd45481b929271af87530d2821b9b51d5cec066dc76867cbc"
SNAPSHOT_COMMIT = "10df134607fcf9c22d27aa38a0e27b457f7c176c"
EVALUATION_SPEC = "docs/specifications/SPEC-A5-EVALUATION.md"
SUCCESSOR_EVALUATION_SPEC_SHA256 = (
    "e8149a416cacc8ec57fa9a211d272993071e0c1cfc580d3b39601910e03aac88"
)
ALLOWED_A5B_IMPLEMENTATION_EXTENSIONS = {
    "crates/cligen/src/bin/cligen-a5b-overlay.rs": (
        "05cc96dcf12a7855d883aef573c16f8e6a4691beece58c0bfe20a222ea102ec9"
    )
}


class WrapperError(RuntimeError):
    """The accepted source identity or verifier wrapper contract failed."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WrapperError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(token: str) -> None:
    raise WrapperError(f"nonfinite JSON token: {token}")


def finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise WrapperError(f"JSON number overflows finite range: {token}")
    return value


def strict_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_pairs,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WrapperError(f"cannot parse {path}: {error}") from error
    if not isinstance(value, dict):
        raise WrapperError(f"expected object: {path}")
    return value


def load_verifier() -> Any:
    if sha256(VERIFIER) != VERIFIER_SHA256:
        raise WrapperError("accepted A5a verifier identity differs")
    spec = importlib.util.spec_from_file_location("accepted_a5a_baseline_verifier", VERIFIER)
    if spec is None or spec.loader is None:
        raise WrapperError("cannot import accepted A5a verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_snapshot_bytes(relative: str) -> bytes:
    checked = subprocess.run(
        ["git", "cat-file", "-e", f"{SNAPSHOT_COMMIT}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if checked.returncode != 0:
        raise WrapperError(f"pinned A5a Git snapshot is unavailable: {SNAPSHOT_COMMIT}")
    result = subprocess.run(
        ["git", "show", f"{SNAPSHOT_COMMIT}:{relative}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise WrapperError(f"pinned A5a snapshot lacks {relative}")
    return result.stdout


def verify_extension_boundary(current: dict[str, Any], historical: dict[str, Any]) -> None:
    historical_files = historical.get("files")
    if not isinstance(historical_files, dict):
        raise WrapperError("accepted implementation file inventory is malformed")
    current_files = current.get("files")
    if not isinstance(current_files, dict):
        raise WrapperError("current implementation file inventory is malformed")
    missing = set(historical_files) - set(current_files)
    changed = {
        path
        for path, digest in historical_files.items()
        if current_files.get(path) != digest
    }
    if canonical_sha256(historical_files) != historical.get("sha256"):
        raise WrapperError("accepted implementation canonical hash differs")
    extra = set(current_files) - set(historical_files)
    if missing or changed or extra != set(ALLOWED_A5B_IMPLEMENTATION_EXTENSIONS):
        raise WrapperError(
            "accepted A5a implementation boundary differs: "
            f"missing={sorted(missing)}, changed={sorted(changed)}, "
            f"extra={sorted(extra)}"
        )
    for relative, expected_sha256 in ALLOWED_A5B_IMPLEMENTATION_EXTENSIONS.items():
        path = ROOT / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or current_files.get(relative) != expected_sha256
            or sha256(path) != expected_sha256
        ):
            raise WrapperError(f"declared A5b extension is missing or unsafe: {relative}")


def verify_evaluation_boundary(historical: dict[str, Any]) -> None:
    expected_names = {
        "evaluation_spec",
        "metric_manifest",
        "metric_manifest_schema",
        "metric_manifest_verifier",
        "observed_bootstrap_reference",
        "observed_bootstrap_golden",
        "wepp_response_schema",
        "wepp_response_verifier",
        "wepp_response_protocol",
    }
    if set(historical) != expected_names:
        raise WrapperError("accepted evaluation-contract artifact set differs")
    for name, value in historical.items():
        if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
            raise WrapperError(f"accepted evaluation binding is malformed: {name}")
        relative = value["path"]
        snapshot_sha256 = hashlib.sha256(git_snapshot_bytes(relative)).hexdigest()
        if snapshot_sha256 != value["sha256"]:
            raise WrapperError(
                f"pinned Git snapshot does not reproduce accepted evaluation binding: {name}"
            )
        current = ROOT / relative
        if not current.is_file() or current.is_symlink():
            raise WrapperError(f"current evaluation artifact is missing: {relative}")
        expected_current = (
            SUCCESSOR_EVALUATION_SPEC_SHA256
            if relative == EVALUATION_SPEC
            else value["sha256"]
        )
        if sha256(current) != expected_current:
            raise WrapperError(f"current evaluation artifact differs: {relative}")


def mutation_self_test(
    current: dict[str, Any],
    historical_implementation: dict[str, Any],
    historical_evaluation: dict[str, Any],
) -> list[str]:
    checks: list[str] = []
    mutated = copy.deepcopy(current)
    mutated["files"]["crates/cligen/src/bin/unregistered-a5b.rs"] = "0" * 64
    try:
        verify_extension_boundary(mutated, historical_implementation)
    except WrapperError:
        checks.append("unexpected implementation extension rejected")
    else:
        raise WrapperError("implementation-extension mutation was accepted")
    mutated_implementation = copy.deepcopy(historical_implementation)
    first = sorted(mutated_implementation["files"])[0]
    mutated_implementation["files"][first] = "0" * 64
    try:
        verify_extension_boundary(current, mutated_implementation)
    except WrapperError:
        checks.append("historical implementation hash mutation rejected")
    else:
        raise WrapperError("historical implementation mutation was accepted")
    mutated_evaluation = copy.deepcopy(historical_evaluation)
    mutated_evaluation["evaluation_spec"]["sha256"] = "0" * 64
    try:
        verify_evaluation_boundary(mutated_evaluation)
    except WrapperError:
        checks.append("historical evaluation snapshot mutation rejected")
    else:
        raise WrapperError("historical evaluation mutation was accepted")
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if sha256(MANIFEST) != MANIFEST_SHA256:
        raise WrapperError("accepted A5a manifest identity differs")
    manifest = strict_json(MANIFEST)
    historical = manifest.get("execution", {}).get("implementation")
    if not isinstance(historical, dict):
        raise WrapperError("accepted A5a manifest lacks implementation identity")
    module = load_verifier()
    current_identity = module.implementation_identity
    verify_extension_boundary(current_identity(), historical)
    historical_evaluation = manifest.get("inputs", {}).get("evaluation_contract")
    if not isinstance(historical_evaluation, dict):
        raise WrapperError("accepted A5a manifest lacks evaluation-contract identity")
    verify_evaluation_boundary(historical_evaluation)
    module.implementation_identity = lambda: historical
    module.evaluation_contract_identity = lambda: historical_evaluation
    module.verify()
    verify_extension_boundary(current_identity(), historical)
    verify_evaluation_boundary(historical_evaluation)
    checks = (
        mutation_self_test(current_identity(), historical, historical_evaluation)
        if args.self_test
        else []
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "accepted_manifest_sha256": MANIFEST_SHA256,
                "accepted_verifier_sha256": VERIFIER_SHA256,
                "historical_source_snapshot": SNAPSHOT_COMMIT,
                "allowed_a5b_implementation_extensions": ALLOWED_A5B_IMPLEMENTATION_EXTENSIONS,
                "successor_evaluation_spec_sha256": SUCCESSOR_EVALUATION_SPEC_SHA256,
                "mutation_checks": checks,
            },
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (WrapperError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"verify-accepted-a5a-baseline: {error}", file=sys.stderr)
        raise SystemExit(1) from error
