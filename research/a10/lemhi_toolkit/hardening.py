"""Revision-2 operational contracts for safe Lemhi work.

The helpers in this module are dependency-free and deliberately separate from
scientific application semantics.  Live side effects remain adapter-owned;
these functions validate and authenticate their inputs and receipts.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterable

from .core import (
    HEX64_PATTERN,
    ToolkitError,
    atomic_write,
    canonical_bytes,
    directory_lock,
    read_json,
    require,
    sha256_bytes,
    sha256_file,
    validate_id,
    validate_json_value,
)

RECORD_SCHEMA_V2 = "lemhi-toolkit-record-2"
PRODUCER_V2 = "lemhi-toolkit-hardening-2"
PROVIDER_API_V2 = 2
SANITIZER_VERSION = "lemhi-evidence-projection-4"
RESERVED_TOKEN = re.compile(r"<[A-Z][A-Z0-9_]*(?:_[0-9]+)?>")
ENVIRONMENT_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
ALLOWED_PROVIDER_CLASSES = {
    "accelerator",
    "framework",
    "runtime",
    "scheduler",
    "storage",
    "toolchain",
    "transport",
}


def _strict_object(value: Any, code: str, detail: str) -> dict[str, Any]:
    require(isinstance(value, dict), code, detail)
    return value


def validate_v2_provider_stack(providers: list[dict[str, Any]]) -> None:
    """Require one coherent declarative provider-API-v2 execution stack."""

    require(isinstance(providers, list) and providers, "PROVIDER_UNAVAILABLE", "empty provider stack")
    classes: set[str] = set()
    for provider in providers:
        _strict_object(provider, "PROVIDER_UNAVAILABLE", "provider object")
        require(provider.get("provider_api_version") == PROVIDER_API_V2, "PROVIDER_UNAVAILABLE", "mixed provider API")
        provider_class = provider.get("provider_class")
        require(provider_class in ALLOWED_PROVIDER_CLASSES, "PROVIDER_UNAVAILABLE", "unknown provider class")
        require(provider_class not in classes, "PROVIDER_UNAVAILABLE", f"duplicate provider class {provider_class}")
        classes.add(provider_class)
        require(provider.get("executes_provider_code") is False, "PROVIDER_UNAVAILABLE", "provider must remain declarative")
    require("storage" in classes and "scheduler" in classes and "transport" in classes, "PROVIDER_UNAVAILABLE", "incomplete operational stack")
    storage = next(item for item in providers if item["provider_class"] == "storage")
    require(storage.get("provides", {}).get("job_local_cleanup") == "toolkit_recoverable", "PROVIDER_UNAVAILABLE", "v2 storage must be toolkit-recoverable")


def validate_toolchain_closure(
    provider: dict[str, Any],
    controller: dict[str, Any],
    compute: dict[str, Any],
) -> dict[str, Any]:
    """Validate the declared native-build closure at both control surfaces."""

    require(provider.get("provider_class") == "toolchain", "PROVIDER_UNAVAILABLE", "toolchain provider required")
    require(provider.get("provider_api_version") == PROVIDER_API_V2, "PROVIDER_UNAVAILABLE", "toolchain API")
    contract = _strict_object(provider.get("toolchain_contract"), "PROVIDER_UNAVAILABLE", "toolchain contract")
    required = {
        "cargo_path",
        "rustc_path",
        "target_triple",
        "target_std_path",
        "host_cxx_path",
        "vendor_root_relative_to_source",
        "offline_metadata_probe",
        "offline_build_probe",
        "license_provenance",
    }
    require(required <= contract.keys(), "PROVIDER_UNAVAILABLE", "incomplete toolchain contract")
    for surface_name, surface in (("controller", controller), ("compute", compute)):
        _strict_object(surface, "GATE_FAILED", f"{surface_name} toolchain observation")
        require(surface.get("target_triple") == contract["target_triple"], "PLATFORM_MISMATCH", f"{surface_name} target")
        require(surface.get("source_vendor_relation") == contract["vendor_root_relative_to_source"], "GATE_FAILED", f"{surface_name} vendor layout")
        require(surface.get("archive_layout_passed") is True, "GATE_FAILED", f"{surface_name} archive layout")
    for field in ("cargo_path", "rustc_path", "target_std_path", "host_cxx_path"):
        require(compute.get(field) == contract[field], "GATE_FAILED", f"compute {field}")
    for gate in ("loader_resolution_passed", "compiler_probe_passed", "offline_metadata_passed", "offline_build_passed"):
        require(compute.get(gate) is True, "GATE_FAILED", gate)
    return {
        "controller_layout": True,
        "compute_build": True,
        "target_triple": contract["target_triple"],
        "toolchain_provider": provider["name"],
    }


def close_job_environment(
    required: dict[str, str],
    ambient: dict[str, str],
    registered_runtime: dict[str, str],
    *,
    deterministic_cuda: bool,
) -> dict[str, str]:
    """Build the exact job environment from an empty Slurm export."""

    _strict_object(required, "PLAN_DRIFT", "required job environment")
    _strict_object(ambient, "PLAN_DRIFT", "ambient environment")
    _strict_object(registered_runtime, "PLAN_DRIFT", "registered runtime environment")
    closed: dict[str, str] = {}
    for source in (registered_runtime, required):
        for name, value in source.items():
            require(ENVIRONMENT_NAME.fullmatch(name) is not None, "PLAN_DRIFT", f"environment name {name!r}")
            require(isinstance(value, str) and value and "\x00" not in value and "\n" not in value, "PLAN_DRIFT", f"environment value {name}")
            require(name not in closed or closed[name] == value, "PLAN_DRIFT", f"environment conflict {name}")
            closed[name] = value
    for name, value in closed.items():
        require(name not in ambient or ambient[name] == value, "PLAN_DRIFT", f"ambient override {name}")
    if deterministic_cuda:
        require(closed.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", "PLAN_DRIFT", "deterministic CUDA environment")
    for prohibited in ("LD_LIBRARY_PATH", "PYTHONHOME", "PYTHONPATH"):
        require(prohibited not in ambient or prohibited in closed, "PLAN_DRIFT", f"unregistered ambient {prohibited}")
    return dict(sorted(closed.items()))


def environment_receipt(environment: dict[str, str], safe_public_values: set[str]) -> dict[str, Any]:
    values = []
    for name, value in sorted(environment.items()):
        item: dict[str, Any] = {"name": name, "value_sha256": sha256_bytes(value.encode("utf-8"))}
        if name in safe_public_values:
            item["safe_value"] = value
        values.append(item)
    return {"slurm_export": "NONE", "values": values}


def create_raw_collected(
    authority_id: str,
    run_id: str,
    plan_id: str,
    files: list[dict[str, Any]],
    gates: dict[str, bool],
    cleanup_marker_sha256: str,
) -> dict[str, Any]:
    """Authenticate raw collection before any fallible projection."""

    validate_id(authority_id, "authority_id")
    validate_id(run_id, "run_id")
    require(HEX64_PATTERN.fullmatch(plan_id) is not None, "EVIDENCE_INCOMPLETE", "plan hash")
    require(HEX64_PATTERN.fullmatch(cleanup_marker_sha256) is not None, "EVIDENCE_INCOMPLETE", "cleanup marker hash")
    require(isinstance(gates, dict) and gates and all(isinstance(key, str) and isinstance(value, bool) for key, value in gates.items()), "EVIDENCE_INCOMPLETE", "gates")
    for item in files:
        require(set(item) == {"logical_name", "bytes", "sha256"}, "EVIDENCE_INCOMPLETE", "raw file record")
        require(isinstance(item["bytes"], int) and item["bytes"] >= 0, "EVIDENCE_INCOMPLETE", "raw bytes")
        require(HEX64_PATTERN.fullmatch(item["sha256"]) is not None, "EVIDENCE_INCOMPLETE", "raw hash")
    semantic = {
        "schema_version": RECORD_SCHEMA_V2,
        "record_type": "RAW_COLLECTED",
        "producer_version": PRODUCER_V2,
        "authority_id": authority_id,
        "run_id": run_id,
        "plan_id": plan_id,
        "files": sorted(files, key=lambda item: item["logical_name"]),
        "gates": dict(sorted(gates.items())),
        "cleanup_marker_sha256": cleanup_marker_sha256,
    }
    semantic["record_sha256"] = sha256_bytes(canonical_bytes(semantic))
    return semantic


def _replace_text(
    text: str, replacements: list[dict[str, str]]
) -> tuple[str, dict[str, int], dict[str, int]]:
    escaped: dict[str, int] = {}

    def escape_raw_token(match: re.Match[str]) -> str:
        name = match.group(0)[1:-1]
        escaped[name] = escaped.get(name, 0) + 1
        return f"[[RAW_RESERVED_TOKEN:{name}]]"

    # Untrusted tools sometimes print angle-bracket placeholders which collide
    # with toolkit-owned projection tokens. Escape those first so raw text can
    # never masquerade as an authorized replacement; only the rules below may
    # introduce reserved-token syntax into a projection.
    output = RESERVED_TOKEN.sub(escape_raw_token, text)
    ordered = sorted(replacements, key=lambda item: (-len(item["value"].encode("utf-8")), item["token"]))
    counts: dict[str, int] = {}
    for item in ordered:
        value = item["value"]
        token = item["token"]
        require(RESERVED_TOKEN.fullmatch(token) is not None, "SANITIZATION_FAILED", "invalid replacement token")
        require(value and token not in value, "SANITIZATION_FAILED", "invalid replacement value")
        if item["kind"] == "path":
            pattern = re.compile(re.escape(value) + r"(?=$|/|[\s\"'`:;,\]\[(){}])")
            output, count = pattern.subn(token, output)
        else:
            output, count = output.replace(value, token), output.count(value)
        counts[token] = count
    return output, counts, escaped


def validate_evidence_replacements(replacements: Any) -> list[dict[str, str]]:
    """Validate projection rules while a plan can still fail prospectively."""

    require(isinstance(replacements, list), "SANITIZATION_FAILED", "replacements must be a list")
    normalized: list[dict[str, str]] = []
    seen_tokens: set[str] = set()
    seen_values: set[tuple[str, str]] = set()
    for item in replacements:
        require(isinstance(item, dict) and set(item) == {"kind", "value", "token"}, "SANITIZATION_FAILED", "replacement shape")
        require(item["kind"] in {"identity", "path", "text"}, "SANITIZATION_FAILED", "replacement kind")
        require(isinstance(item["value"], str) and isinstance(item["token"], str), "SANITIZATION_FAILED", "replacement strings")
        require(RESERVED_TOKEN.fullmatch(item["token"]) is not None, "SANITIZATION_FAILED", "invalid replacement token")
        require(item["value"] and item["token"] not in item["value"], "SANITIZATION_FAILED", "invalid replacement value")
        require(item["token"] not in seen_tokens, "SANITIZATION_FAILED", "duplicate token")
        require((item["kind"], item["value"]) not in seen_values, "SANITIZATION_FAILED", "duplicate replacement")
        seen_tokens.add(item["token"])
        seen_values.add((item["kind"], item["value"]))
        normalized.append(dict(item))
    return normalized


def _loads_evidence_json(text: str) -> Any:
    """Parse scientific JSON strictly while admitting finite JSON numbers."""

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, "INVALID_JSON", f"duplicate key: {key}")
            value[key] = item
        return value

    def invalid_constant(value: str) -> None:
        raise ToolkitError("INVALID_JSON", f"non-finite number prohibited: {value}")

    try:
        return json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_constant=invalid_constant,
        )
    except json.JSONDecodeError as error:
        raise ToolkitError("INVALID_JSON", str(error)) from error


def project_evidence(
    raw: bytes,
    *,
    media_type: str,
    replacements: list[dict[str, str]],
    forbidden: Iterable[str],
    raw_parent_sha256: str,
) -> tuple[bytes, dict[str, Any]]:
    """Apply deterministic typed projection and return its private receipt."""

    require(HEX64_PATTERN.fullmatch(raw_parent_sha256) is not None, "SANITIZATION_FAILED", "raw parent hash")
    normalized = validate_evidence_replacements(replacements)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ToolkitError("SANITIZATION_FAILED", "invalid UTF-8 evidence") from error
    if media_type == "application/json":
        value = _loads_evidence_json(text)

        counts: dict[str, int] = {item["token"]: 0 for item in normalized}
        escaped: dict[str, int] = {}

        def visit(node: Any) -> Any:
            if isinstance(node, str):
                projected, local_counts, local_escaped = _replace_text(node, normalized)
                for token, count in local_counts.items():
                    counts[token] += count
                for name, count in local_escaped.items():
                    escaped[name] = escaped.get(name, 0) + count
                return projected
            if isinstance(node, list):
                return [visit(item) for item in node]
            if isinstance(node, dict):
                return {key: visit(item) for key, item in node.items()}
            return node

        try:
            projected_bytes = (
                json.dumps(
                    visit(value),
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            )
        except (TypeError, ValueError) as error:
            raise ToolkitError("INVALID_JSON", str(error)) from error
    elif media_type == "text/plain":
        projected, counts, escaped = _replace_text(text, normalized)
        projected_bytes = projected.encode("utf-8")
    else:
        raise ToolkitError("SANITIZATION_FAILED", "binary projection requires an exact unchanged allowlist")
    for secret in forbidden:
        require(not secret or secret.encode("utf-8") not in projected_bytes, "SANITIZATION_FAILED", "unknown forbidden value")
    receipt = {
        "sanitizer_version": SANITIZER_VERSION,
        "raw_parent_sha256": raw_parent_sha256,
        "sanitized_sha256": sha256_bytes(projected_bytes),
        "escaped_reserved_token_counts": dict(sorted(escaped.items())),
        "token_counts": dict(sorted(counts.items())),
    }
    return projected_bytes, receipt


def transfer_receipt(
    *,
    logical_name: str,
    byte_count: int,
    elapsed_ns: int,
    method: str,
    identity_sha256: str,
    state: str,
    remote_revalidated: bool,
    range_integrity: bool = False,
) -> dict[str, Any]:
    require(isinstance(byte_count, int) and byte_count >= 0, "TRANSFER_INCOMPLETE", "bytes")
    require(isinstance(elapsed_ns, int) and elapsed_ns > 0, "TRANSFER_INCOMPLETE", "elapsed_ns")
    require(elapsed_ns <= 9_007_199_254_740_991, "TRANSFER_INCOMPLETE", "elapsed overflow")
    require(state in {"uploaded", "resumed", "already_verified"}, "TRANSFER_INCOMPLETE", "transfer state")
    require(HEX64_PATTERN.fullmatch(identity_sha256) is not None, "TRANSFER_INCOMPLETE", "transfer identity")
    if state == "already_verified":
        require(remote_revalidated, "TRANSFER_INCOMPLETE", "skip requires remote revalidation")
    if state == "resumed":
        require(range_integrity, "TRANSFER_INCOMPLETE", "resume requires range integrity")
    rate = (byte_count * 1_000_000_000) // elapsed_ns
    require(rate <= 9_007_199_254_740_991, "TRANSFER_INCOMPLETE", "rate overflow")
    return {
        "logical_name": logical_name,
        "bytes": byte_count,
        "elapsed_ns": elapsed_ns,
        "method": method,
        "identity_sha256": identity_sha256,
        "state": state,
        "remote_revalidated": remote_revalidated,
        "observed_bytes_per_second": rate,
    }


def append_manifest_revision(path: Path, revision: dict[str, Any]) -> str:
    """Append immutable content identities without overwriting prior revisions."""

    validate_json_value(revision)
    require(isinstance(revision.get("revision"), int) and revision["revision"] >= 0, "PLAN_DRIFT", "manifest revision")
    assets = revision.get("assets")
    require(isinstance(assets, list), "PLAN_DRIFT", "manifest assets")
    identities: set[str] = set()
    names: dict[str, str] = {}
    for asset in assets:
        digest = asset.get("sha256")
        name = asset.get("logical_name")
        require(isinstance(name, str) and HEX64_PATTERN.fullmatch(digest or "") is not None, "PLAN_DRIFT", "manifest asset")
        require(digest not in identities, "PLAN_DRIFT", "duplicate asset identity")
        require(name not in names or names[name] == digest, "PLAN_DRIFT", "same name different hash")
        identities.add(digest)
        names[name] = digest
    document = {"schema_version": "lemhi-run-asset-manifest-2", "revisions": []}
    if path.exists():
        document = read_json(path)
    revisions = document.get("revisions")
    require(isinstance(revisions, list), "PLAN_DRIFT", "manifest history")
    require(revision["revision"] == len(revisions), "PLAN_DRIFT", "nonappend manifest revision")
    prior_names: dict[str, str] = {}
    for prior in revisions:
        for asset in prior["assets"]:
            prior_names[asset["logical_name"]] = asset["sha256"]
    for name, digest in names.items():
        require(name not in prior_names or prior_names[name] == digest, "PLAN_DRIFT", "same name different hash")
    entry = dict(revision)
    entry["predecessor_sha256"] = sha256_bytes(canonical_bytes(revisions[-1])) if revisions else None
    document["revisions"].append(entry)
    atomic_write(path, document, private=True)
    return sha256_bytes(canonical_bytes(entry))


class LedgerAnchor:
    """Private append-only ledger with explicit genesis and reviewed heads."""

    def __init__(self, path: Path, authority_id: str, budget_id: str, ceiling: int):
        self.path = path.resolve()
        self.authority_id = validate_id(authority_id, "authority_id")
        self.budget_id = validate_id(budget_id, "resource_budget_id")
        require(isinstance(ceiling, int) and ceiling >= 0, "AUTHORITY_INVALID", "ceiling")
        self.ceiling = ceiling

    def initialize(self, *, authorized: bool, predecessor_evidence: list[Any], scheduler_evidence: list[Any]) -> str:
        require(authorized, "AUTHORITY_INVALID", "genesis not authorized")
        require(not self.path.exists(), "AUTHORITY_INVALID", "duplicate genesis")
        require(not predecessor_evidence and not scheduler_evidence, "AUTHORITY_INVALID", "preexisting authority evidence")
        genesis = {
            "authority_id": self.authority_id,
            "resource_budget_id": self.budget_id,
            "ceiling_gpu_minutes": self.ceiling,
            "sequence": 0,
            "event": "genesis",
            "predecessor_sha256": None,
        }
        genesis["event_sha256"] = sha256_bytes(canonical_bytes(genesis))
        ledger = {
            "schema_version": "lemhi-resource-ledger-2",
            "authority_id": self.authority_id,
            "resource_budget_id": self.budget_id,
            "ceiling_gpu_minutes": self.ceiling,
            "entries": [genesis],
            "head_sha256": genesis["event_sha256"],
        }
        atomic_write(self.path, ledger, private=True)
        return genesis["event_sha256"]

    def load(self, *, checkpoint: str | None = None) -> dict[str, Any]:
        require(self.path.exists(), "AUTHORITY_INVALID", "ledger missing")
        ledger = read_json(self.path)
        require(ledger.get("schema_version") == "lemhi-resource-ledger-2", "AUTHORITY_INVALID", "ledger schema")
        require(ledger.get("authority_id") == self.authority_id, "AUTHORITY_INVALID", "ledger authority")
        require(ledger.get("resource_budget_id") == self.budget_id, "AUTHORITY_INVALID", "ledger budget")
        require(ledger.get("ceiling_gpu_minutes") == self.ceiling, "AUTHORITY_INVALID", "ledger ceiling")
        prior: str | None = None
        for sequence, event in enumerate(ledger.get("entries", [])):
            require(event.get("sequence") == sequence and event.get("predecessor_sha256") == prior, "AUTHORITY_INVALID", "ledger chain")
            recorded = event.get("event_sha256")
            semantic = dict(event)
            semantic.pop("event_sha256", None)
            require(recorded == sha256_bytes(canonical_bytes(semantic)), "AUTHORITY_INVALID", "ledger event hash")
            prior = recorded
        require(prior is not None and ledger.get("head_sha256") == prior, "AUTHORITY_INVALID", "ledger head")
        if checkpoint is not None:
            require(any(item.get("event_sha256") == checkpoint for item in ledger["entries"]), "AUTHORITY_INVALID", "ledger truncated before checkpoint")
        return ledger

    def append(self, event: dict[str, Any], *, checkpoint: str, scheduler_reconciled: bool) -> str:
        require(scheduler_reconciled, "AUTHORITY_RECONCILIATION_REQUIRED", "scheduler accounting unavailable or ambiguous")
        ledger = self.load(checkpoint=checkpoint)
        entry = dict(event)
        require("event_sha256" not in entry and "sequence" not in entry, "AUTHORITY_INVALID", "ledger event fields")
        entry.update({
            "sequence": len(ledger["entries"]),
            "predecessor_sha256": ledger["head_sha256"],
        })
        entry["event_sha256"] = sha256_bytes(canonical_bytes(entry))
        ledger["entries"].append(entry)
        ledger["head_sha256"] = entry["event_sha256"]
        atomic_write(self.path, ledger, private=True)
        return entry["event_sha256"]


IMMUTABLE_AUTHORITY_FIELDS = (
    "allowed_roots",
    "authority_id",
    "confirmation_classification",
    "package_id",
    "resource_budget_id",
    "resource_ceiling_gpu_minutes",
    "resource_class",
    "starting_branch",
    "push_target",
    "ledger_anchor",
    "ledger_genesis_sha256",
    "scheduler_authority_token",
)


def derive_authority_revision(authority: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Derive one immutable run authority without widening the dispatch."""

    for field in IMMUTABLE_AUTHORITY_FIELDS:
        require(field in authority, "AUTHORITY_INVALID", f"authority field {field}")
    commit = request.get("source_commit")
    published = authority.get("published_source_commits")
    require(isinstance(published, list) and commit in published, "AUTHORITY_INVALID", "source commit is not published")
    run_id = validate_id(request.get("run_id"), "run_id")
    predecessor = authority.get("authority_revision_sha256")
    require(isinstance(predecessor, str) and HEX64_PATTERN.fullmatch(predecessor) is not None, "AUTHORITY_INVALID", "authority predecessor")
    for field in IMMUTABLE_AUTHORITY_FIELDS:
        require(field not in request or request[field] == authority[field], "AUTHORITY_INVALID", f"authority drift {field}")
    revision = {field: authority[field] for field in IMMUTABLE_AUTHORITY_FIELDS}
    revision.update({
        "schema_version": "lemhi-authority-revision-2",
        "authority_revision": authority.get("authority_revision", 0) + 1,
        "predecessor_authority_revision_sha256": predecessor,
        "ledger_head_checkpoint": authority.get("ledger_head_checkpoint"),
        "run_id": run_id,
        "run_relative_root": f"runs/{run_id}",
        "source_commit": commit,
        "asset_manifest_sha256": request.get("asset_manifest_sha256"),
        "plan_input_sha256": request.get("plan_input_sha256"),
    })
    for field in ("ledger_head_checkpoint", "asset_manifest_sha256", "plan_input_sha256"):
        require(isinstance(revision[field], str) and HEX64_PATTERN.fullmatch(revision[field]) is not None, "AUTHORITY_INVALID", field)
    revision["authority_revision_sha256"] = sha256_bytes(canonical_bytes(revision))
    return revision


def admit_job_local(
    base: Path,
    *,
    required_bytes: int,
    required_inodes: int,
    minimum_free_bytes: int,
    expected_uid: int,
) -> dict[str, Any]:
    """Perform race-bounded capacity admission against one declared base."""

    resolved = base.resolve(strict=True)
    metadata = resolved.stat()
    require(metadata.st_uid == expected_uid, "JOB_LOCAL_CAPACITY", "job-local owner")
    require(metadata.st_mode & 0o022 == 0, "JOB_LOCAL_CAPACITY", "job-local permissions")
    require(all(isinstance(item, int) and item >= 0 for item in (required_bytes, required_inodes, minimum_free_bytes)), "JOB_LOCAL_CAPACITY", "capacity request")
    stats = os.statvfs(resolved)
    free_bytes = stats.f_bavail * stats.f_frsize
    free_inodes = stats.f_favail
    require(free_bytes - required_bytes >= minimum_free_bytes, "JOB_LOCAL_CAPACITY", "insufficient bytes")
    require(free_inodes >= required_inodes, "JOB_LOCAL_CAPACITY", "insufficient inodes")
    return {
        "canonical_base": str(resolved),
        "filesystem_device": metadata.st_dev,
        "owner_uid": metadata.st_uid,
        "required_bytes": required_bytes,
        "required_inodes": required_inodes,
        "free_bytes_observed": free_bytes,
        "free_inodes_observed": free_inodes,
    }


def claim_job_local(
    base: Path,
    claim_id: str,
    *,
    required_bytes: int,
    required_inodes: int,
    minimum_free_bytes: int,
    expected_uid: int,
) -> dict[str, Any]:
    """Serialize admission and retain an exact active capacity claim."""

    validate_id(claim_id, "job-local claim")
    resolved = base.resolve(strict=True)
    claims_root = resolved / ".lemhi-toolkit-claims"
    lock = resolved / ".lemhi-toolkit-admission.lock"
    with directory_lock(lock):
        claims_root.mkdir(mode=0o700, exist_ok=True)
        active_bytes = 0
        active_inodes = 0
        for path in claims_root.glob("*.json"):
            claim = read_json(path)
            active_bytes += claim["required_bytes"]
            active_inodes += claim["required_inodes"]
        receipt = admit_job_local(
            resolved,
            required_bytes=required_bytes + active_bytes,
            required_inodes=required_inodes + active_inodes,
            minimum_free_bytes=minimum_free_bytes,
            expected_uid=expected_uid,
        )
        claim_path = claims_root / f"{claim_id}.json"
        require(not claim_path.exists(), "JOB_LOCAL_CAPACITY", "duplicate capacity claim")
        claim = {
            "claim_id": claim_id,
            "canonical_base": str(resolved),
            "filesystem_device": receipt["filesystem_device"],
            "owner_uid": expected_uid,
            "required_bytes": required_bytes,
            "required_inodes": required_inodes,
        }
        claim["claim_sha256"] = sha256_bytes(canonical_bytes(claim))
        atomic_write(claim_path, claim, private=True)
        return claim


def release_job_local_claim(base: Path, claim: dict[str, Any]) -> None:
    resolved = base.resolve(strict=True)
    claim_id = validate_id(claim.get("claim_id"), "job-local claim")
    path = resolved / ".lemhi-toolkit-claims" / f"{claim_id}.json"
    require(path.is_file() and not path.is_symlink(), "JOB_LOCAL_CAPACITY", "capacity claim missing")
    require(read_json(path) == claim, "JOB_LOCAL_CAPACITY", "capacity claim mismatch")
    path.unlink()


def validate_recovery_target(marker: dict[str, Any], scheduler: dict[str, Any], observation: dict[str, Any]) -> None:
    """Validate settled exact-node recovery before a deletion adapter runs."""

    require(scheduler.get("squeue_absent") is True, "CLEANUP_INCOMPLETE", "job or step still live")
    require(scheduler.get("sacct_settled") is True, "CLEANUP_INCOMPLETE", "accounting unsettled")
    require(scheduler.get("requeues_settled") is True, "CLEANUP_INCOMPLETE", "requeue unsettled")
    for field in ("job_id", "node", "uid", "canonical_base", "canonical_target", "filesystem_device"):
        require(marker.get(field) == observation.get(field), "CLEANUP_TARGET_INVALID", f"recovery {field}")
    require(observation.get("marker_pass_one") is True and observation.get("marker_pass_two") is True, "CLEANUP_TARGET_INVALID", "marker changed")
    require(observation.get("ancestors_safe") is True, "CLEANUP_TARGET_INVALID", "unsafe ancestor")


def reserve_primary_and_recovery(ceiling: int, consumed: int, primary: int, contingency: int) -> dict[str, int]:
    require(all(isinstance(item, int) and item >= 0 for item in (ceiling, consumed, primary, contingency)), "RESOURCE_CEILING", "reservation")
    require(consumed + primary + contingency <= ceiling, "RESOURCE_CEILING", "primary plus recovery contingency")
    return {"primary_reserved_gpu_minutes": primary, "recovery_reserved_gpu_minutes": contingency, "remaining_gpu_minutes": ceiling - consumed - primary - contingency}


def supervise_process(
    command: list[str],
    *,
    attempt_root: Path,
    expected_marker: dict[str, Any],
    durable_status: Path,
    environment: dict[str, str],
    status_writer: Callable[[Path, Any], Any] = atomic_write,
) -> dict[str, Any]:
    """Supervise one process group and make cleanup uncertainty dominant."""

    marker_path = attempt_root / ".lemhi-toolkit-owner.json"
    require(attempt_root.is_dir() and not attempt_root.is_symlink(), "CLEANUP_TARGET_INVALID", "attempt root")
    require(read_json(marker_path) == expected_marker, "CLEANUP_TARGET_INVALID", "attempt marker")
    child = subprocess.Popen(command, cwd=attempt_root, env=environment, start_new_session=True)
    forwarded: list[int] = []
    prior_handlers: dict[int, Any] = {}

    def forward(signum: int, _frame: Any) -> None:
        forwarded.append(signum)
        try:
            os.killpg(child.pid, signum)
        except ProcessLookupError:
            pass

    handled = [item for item in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP) if item is not None]
    try:
        for item in handled:
            prior_handlers[item] = signal.signal(item, forward)
        return_code = child.wait()
    finally:
        for item, handler in prior_handlers.items():
            signal.signal(item, handler)
    status_ok = True
    status = {"return_code": return_code, "forwarded_signals": forwarded}
    try:
        status_writer(durable_status, status)
    except (OSError, ToolkitError):
        status_ok = False
    cleanup_ok = False
    try:
        require(read_json(marker_path) == expected_marker, "CLEANUP_TARGET_INVALID", "attempt marker changed")
        shutil.rmtree(attempt_root)
        cleanup_ok = not attempt_root.exists()
    except (OSError, ToolkitError):
        cleanup_ok = False
    terminal = "APPLICATION_EXIT" if status_ok and cleanup_ok else "CLEANUP_INCOMPLETE"
    return {"terminal": terminal, "application_return_code": return_code, "status_written": status_ok, "cleanup_verified": cleanup_ok}
