#!/usr/bin/env python3
"""Recover A10M5R12R1 evidence without mutating its toolkit state.

``recover`` is read-only with respect to the parent and the remote run.  It
authenticates the frozen parent, safely expands the already-downloaded archive,
and writes a fresh successor-private RAW_COLLECTED-equivalent plus projection-v5
tree.  ``cleanup`` is intentionally separate and is admitted only after a
successful selector replay receipt exists.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Iterator


HERE = Path(__file__).resolve().parent
SCRIPT = Path(__file__).resolve()
DEFAULT_IDENTITIES = HERE / "frozen-parent-identities.json"
EXPECTED_REPOSITORY_ROOT = Path("/Users/roger/src/cligen-rs")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
RESERVED_TOKEN = re.compile(r"<[A-Z][A-Z0-9_]*(?:_[0-9]+)?>")
PREDECESSOR_RESULT_PATH = Path(
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/"
    "artifacts/temporal-result.json"
)


class RecoveryError(RuntimeError):
    """A fail-closed recovery contract violation."""


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise RecoveryError(detail)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def record(value: dict[str, Any]) -> dict[str, Any]:
    require("record_sha256" not in value, "record already has an identity")
    output = dict(value)
    output["record_sha256"] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    return output


def read_json(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in items:
            require(key not in output, f"duplicate JSON key: {key}")
            output[key] = value
        return output

    def reject_constant(value: str) -> None:
        raise RecoveryError(f"non-finite JSON number: {value}")

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RecoveryError(f"cannot read JSON {path}: {error}") from error


def exact_file(path: Path, expected_sha256: str, expected_bytes: int | None = None) -> None:
    require(path.is_absolute(), f"path is not absolute: {path}")
    require(path.is_file() and not path.is_symlink(), f"missing/nonregular file: {path}")
    require(path.stat().st_nlink == 1, f"hardlinked file: {path}")
    if expected_bytes is not None:
        require(path.stat().st_size == expected_bytes, f"byte count changed: {path}")
    require(HEX64.fullmatch(expected_sha256) is not None, "invalid frozen SHA-256")
    require(digest(path) == expected_sha256, f"identity changed: {path}")


def authenticated(value: Any) -> bool:
    if not isinstance(value, dict) or HEX64.fullmatch(value.get("record_sha256", "")) is None:
        return False
    semantic = dict(value)
    expected = semantic.pop("record_sha256")
    return hashlib.sha256(canonical_bytes(semantic)).hexdigest() == expected


@contextlib.contextmanager
def parent_run_lock(config: dict[str, Any]) -> Iterator[None]:
    """Coordinate with the parent toolkit through its exact run lock."""

    lock = Path(config["parent"]["run_lock_path"])
    expected = Path(config["parent"]["state_path"]).parent.parent / ".run.lock"
    require(lock == expected and lock.is_absolute(), "parent run-lock path changed")
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as error:
        raise RecoveryError("parent run is locked") from error
    try:
        yield
    finally:
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass


def validate_published_source(config: dict[str, Any]) -> str:
    source = config["parent"]["source_commit"]
    published = config["published_source"]
    repository = Path(published["repository_root"])
    require(repository == EXPECTED_REPOSITORY_ROOT, "live repository root changed")
    require(
        published.get("remote") == "origin"
        and published.get("branch") == "refs/heads/main",
        "published-main target changed",
    )
    require(
        config.get("ssh") == {"executable": "/usr/bin/ssh", "target": "lemhi"},
        "live SSH contract changed",
    )
    require(repository.is_absolute() and (repository / ".git").exists(), "repository root invalid")
    result = subprocess.run(
        ["git", "ls-remote", published["remote"], published["branch"]],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    fields = result.stdout.strip().split()
    require(len(fields) == 2 and fields[1] == published["branch"], "published main unresolved")
    head = fields[0]
    require(re.fullmatch(r"[0-9a-f]{40}", head) is not None, "published main identity invalid")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source, head], cwd=repository
    )
    require(ancestor.returncode == 0, "frozen parent source is not published on main")
    for local in (SCRIPT, DEFAULT_IDENTITIES):
        repository_path = local.relative_to(repository).as_posix()
        committed = subprocess.run(
            ["git", "show", f"{head}:{repository_path}"],
            cwd=repository,
            check=True,
            capture_output=True,
        ).stdout
        require(local.read_bytes() == committed, f"recovery source is not published: {repository_path}")
    return head


def remote_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    parent = config["parent"]
    probe = b"""set -eu
archive=$1
marker=$2
[ -f \"$archive\" ] && [ ! -L \"$archive\" ] || exit 64
[ -f \"$marker\" ] && [ ! -L \"$marker\" ] || exit 64
[ \"$(stat -c %h \"$archive\")\" -eq 1 ]
[ \"$(stat -c %h \"$marker\")\" -eq 1 ]
printf '%s %s %s %s\\n' \"$(wc -c < \"$archive\" | tr -d ' ')\" \"$(sha256sum \"$archive\" | awk '{print $1}')\" \"$(wc -c < \"$marker\" | tr -d ' ')\" \"$(sha256sum \"$marker\" | awk '{print $1}')\"
"""
    command = [
        config["ssh"]["executable"],
        config["ssh"]["target"],
        "sh",
        "-s",
        "--",
        parent["remote_archive_path"],
        parent["remote_marker_path"],
    ]
    result = subprocess.run(command, input=probe, check=True, capture_output=True)
    fields = result.stdout.decode("ascii").strip().split()
    require(len(fields) == 4, "remote identity probe malformed")
    return {
        "archive_bytes": int(fields[0]),
        "archive_sha256": fields[1],
        "marker_bytes": int(fields[2]),
        "marker_sha256": fields[3],
    }


def validate_remote(config: dict[str, Any], snapshot: dict[str, Any]) -> None:
    parent, caps = config["parent"], config["caps"]
    require(snapshot.get("archive_bytes") == caps["archive_bytes"], "remote archive bytes changed")
    require(snapshot.get("archive_sha256") == parent["archive_sha256"], "remote archive changed")
    require(snapshot.get("marker_sha256") == parent["remote_marker_sha256"], "remote marker changed")
    require(isinstance(snapshot.get("marker_bytes"), int) and snapshot["marker_bytes"] > 0, "remote marker missing")


def remote_absence(config: dict[str, Any]) -> dict[str, bool]:
    """Independently prove that clean.sh removed the complete remote run root."""

    parent = config["parent"]
    probe = b"""set -eu
root=$1
archive=$2
marker=$3
[ ! -e \"$root\" ] && [ ! -L \"$root\" ]
[ ! -e \"$archive\" ] && [ ! -L \"$archive\" ]
[ ! -e \"$marker\" ] && [ ! -L \"$marker\" ]
printf 'RUN_ROOT_ABSENT\\n'
"""
    remote_root = f"{parent['remote_base']}/{parent['remote_run_root']}"
    command = [
        config["ssh"]["executable"],
        config["ssh"]["target"],
        "sh",
        "-s",
        "--",
        remote_root,
        parent["remote_archive_path"],
        parent["remote_marker_path"],
    ]
    result = subprocess.run(command, input=probe, check=True, capture_output=True)
    require(result.stdout.decode("ascii").strip() == "RUN_ROOT_ABSENT", "post-clean probe malformed")
    return {"archive_absent": True, "marker_absent": True, "run_root_absent": True}


def validate_parent(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    parent, caps = config["parent"], config["caps"]
    require(caps.get("archive_members") == 51, "recovery must bind exactly 51 members")
    require(caps.get("max_archive_bytes") == 100_000_000, "archive ceiling changed")
    require(caps.get("max_expanded_bytes") == 100_000_000, "expansion ceiling changed")
    require(caps.get("max_member_bytes") == 50_000_000, "member ceiling changed")
    require(caps.get("archive_bytes", 100_000_001) <= caps["max_archive_bytes"], "archive exceeds ceiling")
    require(config["recovery"].get("sanitizer_version") == "lemhi-evidence-projection-5", "projection version changed")
    state_path, plan_path, archive_path = map(
        Path, (parent["state_path"], parent["plan_path"], parent["archive_path"])
    )
    authority_path, ledger_path = Path(parent["authority_path"]), Path(parent["ledger_path"])
    exact_file(authority_path, parent["authority_sha256"], parent["authority_bytes"])
    exact_file(ledger_path, parent["ledger_sha256"], parent["ledger_bytes"])
    exact_file(state_path, parent["state_sha256"])
    exact_file(plan_path, parent["plan_sha256"])
    exact_file(archive_path, parent["archive_sha256"], caps["archive_bytes"])
    authority, ledger = read_json(authority_path), read_json(ledger_path)
    state, plan = read_json(state_path), read_json(plan_path)
    require(
        all(isinstance(value, dict) for value in (authority, ledger, state, plan)),
        "parent records must be objects",
    )
    require(authority.get("authority_id") == parent["authority_id"], "authority identity mismatch")
    require(
        hashlib.sha256(canonical_bytes(authority)).hexdigest()
        == parent["authority_canonical_sha256"],
        "authority canonical identity mismatch",
    )
    require(authority.get("package_id") == parent["package_id"], "authority package mismatch")
    require(authority.get("source_commit") == parent["source_commit"], "authority source mismatch")
    require(
        authority.get("resource_ceiling_gpu_minutes")
        == parent.get("resource_ceiling_gpu_minutes")
        == ledger.get("ceiling_gpu_minutes")
        == 395,
        "parent GPU ceiling changed",
    )
    require(ledger.get("authority_id") == parent["authority_id"], "ledger authority mismatch")
    predecessor = None
    entries = ledger.get("entries")
    require(isinstance(entries, list) and entries, "ledger entries missing")
    for sequence, entry in enumerate(entries):
        require(
            isinstance(entry, dict)
            and entry.get("sequence") == sequence
            and entry.get("predecessor_sha256") == predecessor,
            "ledger event chain changed",
        )
        semantic_event = dict(entry)
        event_sha256 = semantic_event.pop("event_sha256", None)
        require(
            HEX64.fullmatch(event_sha256 or "") is not None
            and hashlib.sha256(canonical_bytes(semantic_event)).hexdigest()
            == event_sha256,
            "ledger event authentication failed",
        )
        predecessor = event_sha256
    require(
        ledger.get("head_sha256") == predecessor == parent["ledger_head_sha256"],
        "ledger head changed",
    )
    recovery_reservations = [
        entry
        for entry in entries
        if entry.get("job_role") == "toolkit-recovery"
        and entry.get("status") == "reserved"
    ]
    require(
        len(recovery_reservations) == 1
        and recovery_reservations[0].get("token")
        == parent["reserved_recovery_token"]
        and recovery_reservations[0].get("requested_gpu_minutes")
        == parent["reserved_recovery_gpu_minutes"]
        == 5,
        "reserved parent recovery token changed",
    )
    for value in (state, plan):
        require(value.get("package_id") == parent["package_id"], "parent package mismatch")
        require(value.get("run_id") == parent["run_id"], "parent run mismatch")
        require(value.get("source_commit") == parent["source_commit"], "parent source mismatch")
    require(state.get("authority_id") == parent["authority_id"], "parent authority mismatch")
    require(state.get("authority_sha256") == parent["authority_canonical_sha256"], "state authority identity mismatch")
    require(state.get("cluster_profile_sha256") == parent["cluster_profile_sha256"], "state cluster profile mismatch")
    require(state.get("current_plan_id") == parent["plan_id"], "parent plan identity mismatch")
    revisions = state.get("plan_revisions")
    require(isinstance(revisions, list) and len(revisions) == 1, "plan revision count changed")
    revision = revisions[0]
    require(
        isinstance(revision, dict)
        and revision.get("revision") == 0
        and revision.get("plan_id") == parent["plan_id"]
        and isinstance(revision.get("semantic"), dict)
        and revision["semantic"].get("cluster_profile_sha256")
        == parent["cluster_profile_sha256"]
        and hashlib.sha256(canonical_bytes(revision["semantic"])).hexdigest()
        == parent["plan_id"],
        "current plan revision relation changed",
    )
    raw_semantic = dict(revision["semantic"])
    raw_semantic.pop("cluster_profile_sha256")
    raw_semantic.pop("provider_stack")
    require(raw_semantic == plan, "raw plan/current semantic relation changed")
    require(state.get("run_state") == "MATRIX_SETTLED", "parent is not collection-ready")
    require(plan.get("remote_run_root") == parent["remote_run_root"], "remote run root mismatch")
    require(plan.get("evidence_replacements") and isinstance(plan["evidence_replacements"], list), "projection rules missing")
    allowlist = plan.get("evidence_allowlist")
    require(isinstance(allowlist, list) and len(allowlist) == caps["archive_members"], "allowlist count changed")
    require(len(set(allowlist)) == len(allowlist), "duplicate allowlist member")
    attempts = state.get("attempts")
    expected_attempts = config["expected_attempts"]
    require(isinstance(attempts, dict) and set(attempts) == set(expected_attempts), "attempt matrix changed")
    total = 0
    jobs = {item["role"]: item for item in plan.get("jobs", []) if isinstance(item, dict) and isinstance(item.get("role"), str)}
    for key, expected in expected_attempts.items():
        attempt = attempts[key]
        role = key.rsplit(".", 1)[0]
        result = attempt.get("result", {})
        gates = result.get("gates")
        require(attempt.get("attempt_index") == 0 and attempt.get("job_role") == role, f"attempt identity changed: {key}")
        require(attempt.get("job_id") == expected["job_id"], f"job id changed: {key}")
        require(attempt.get("plan_id") == parent["plan_id"], f"attempt plan changed: {key}")
        require(attempt.get("state") == "RESULT_VALIDATED" and attempt.get("passed") is True, f"attempt did not pass: {key}")
        require(result.get("terminal") is True and result.get("state") == "COMPLETED", f"attempt terminal changed: {key}")
        require(result.get("exit_code") == 0 and result.get("accounting") == "available", f"attempt accounting changed: {key}")
        require(isinstance(gates, dict) and gates and all(value is True for value in gates.values()), f"attempt gate failed: {key}")
        require(HEX64.fullmatch(result.get("gate_receipt_sha256", "")) is not None, f"gate identity missing: {key}")
        require(
            role in jobs
            and jobs[role].get("max_attempts") == 1
            and jobs[role].get("retry_on") == []
            and jobs[role].get("gate_receipt") == expected["gate_receipt"],
            f"job contract changed: {key}",
        )
        require(expected["gate_receipt"] in allowlist, f"gate receipt not allowlisted: {key}")
        minutes = result.get("actual_gpu_minutes")
        require(minutes == expected["actual_gpu_minutes"], f"GPU accounting changed: {key}")
        total += minutes
        receipt_path = Path(parent["publication_dir"]) / f"job-{key}.json"
        frozen_receipt = config["job_receipts"][key]
        exact_file(receipt_path, frozen_receipt["sha256"], frozen_receipt["bytes"])
        receipt = read_json(receipt_path)
        require(authenticated(receipt), f"job receipt authentication failed: {key}")
        require(receipt.get("job_id") == expected["job_id"] and receipt.get("passed") is True, f"job receipt mismatch: {key}")
        require(receipt.get("result", {}).get("gate_receipt_sha256") == result["gate_receipt_sha256"], f"gate receipt mismatch: {key}")
    require(total == config["total_actual_gpu_minutes"] == 99, "actual GPU total changed")
    settled = [
        item.get("actual_gpu_minutes")
        for item in ledger.get("entries", [])
        if isinstance(item, dict) and item.get("status") == "settled"
    ]
    require(settled == [16, 34, 49] and sum(settled) == total, "ledger settlement changed")
    return state, plan


def safe_members(archive_path: Path, allowlist: list[str], caps: dict[str, int]) -> list[tarfile.TarInfo]:
    try:
        archive = tarfile.open(archive_path, mode="r:")
    except (OSError, tarfile.TarError) as error:
        raise RecoveryError("archive cannot be inspected") from error
    with archive:
        members = archive.getmembers()
    require(len(members) == caps["archive_members"] == len(allowlist), "archive member count changed")
    require(len({member.name for member in members}) == len(members), "duplicate archive member")
    require({member.name for member in members} == set(allowlist), "archive differs from exact allowlist")
    total = 0
    for member in members:
        path = PurePosixPath(member.name)
        require(not path.is_absolute() and ".." not in path.parts and "." not in path.parts, "unsafe archive path")
        require(member.isfile() and not member.issym() and not member.islnk(), "nonregular archive member")
        require(member.uid == 0 and member.gid == 0 and member.mode & 0o6000 == 0, "unsafe archive metadata")
        require(member.size <= caps["max_member_bytes"], f"member exceeds ceiling: {member.name}")
        total += member.size
        require(total <= caps["max_expanded_bytes"], "expanded archive exceeds ceiling")
    require(total == caps["expanded_bytes"], "expanded byte identity changed")
    return members


def extract(archive_path: Path, destination: Path, members: list[tarfile.TarInfo]) -> list[dict[str, Any]]:
    destination.mkdir(mode=0o700)
    files: list[dict[str, Any]] = []
    with tarfile.open(archive_path, mode="r:") as archive:
        for member in members:
            target = destination.joinpath(*PurePosixPath(member.name).parts)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            source = archive.extractfile(member)
            require(source is not None, f"member cannot be read: {member.name}")
            count = 0
            with source, target.open("xb") as output:
                os.chmod(target, 0o600)
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    count += len(block)
                    require(count <= member.size, f"member grew while extracting: {member.name}")
                    output.write(block)
            require(count == member.size, f"member truncated: {member.name}")
            files.append({"logical_name": member.name, "bytes": count, "sha256": digest(target)})
    return sorted(files, key=lambda item: item["logical_name"])


def replace_text(text: str, replacements: list[dict[str, str]]) -> tuple[str, dict[str, int], dict[str, int]]:
    escaped: dict[str, int] = {}

    def escape(match: re.Match[str]) -> str:
        name = match.group(0)[1:-1]
        escaped[name] = escaped.get(name, 0) + 1
        return f"[[RAW_RESERVED_TOKEN:{name}]]"

    output = RESERVED_TOKEN.sub(escape, text)
    counts: dict[str, int] = {}
    for item in sorted(replacements, key=lambda row: (-len(row["value"].encode()), row["token"])):
        value, token = item["value"], item["token"]
        require(item.get("kind") in {"identity", "path", "text"}, "invalid projection kind")
        require(RESERVED_TOKEN.fullmatch(token) is not None and value and token not in value, "invalid projection rule")
        if item["kind"] == "path":
            output, count = re.subn(re.escape(value) + r"(?=$|/|[\s\"'`:;,\]\[(){}])", token, output)
        else:
            count = output.count(value)
            output = output.replace(value, token)
        counts[token] = count
    return output, counts, escaped


def project(raw: bytes, suffix: str, replacements: list[dict[str, str]], forbidden: Iterable[str]) -> tuple[bytes, dict[str, Any]]:
    if suffix in {".npz", ".pt"}:
        projected, counts, escaped = raw, {row["token"]: 0 for row in replacements}, {}
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RecoveryError("non-binary evidence is not UTF-8") from error
        if suffix == ".json":
            def reject(value: str) -> None:
                raise RecoveryError(f"non-finite JSON number: {value}")

            def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
                output: dict[str, Any] = {}
                for key, value in items:
                    require(key not in output, f"duplicate JSON key: {key}")
                    output[key] = value
                return output

            value = json.loads(text, parse_constant=reject, object_pairs_hook=pairs)
            counts = {row["token"]: 0 for row in replacements}
            escaped = {}

            def visit(node: Any) -> Any:
                if isinstance(node, str):
                    value_text, local_counts, local_escaped = replace_text(node, replacements)
                    for key, count in local_counts.items():
                        counts[key] += count
                    for key, count in local_escaped.items():
                        escaped[key] = escaped.get(key, 0) + count
                    return value_text
                if isinstance(node, list):
                    return [visit(item) for item in node]
                if isinstance(node, dict):
                    return {key: visit(item) for key, item in node.items()}
                require(not isinstance(node, float) or math.isfinite(node), "non-finite JSON number")
                return node

            projected = canonical_bytes(visit(value)) + b"\n"
        else:
            value_text, counts, escaped = replace_text(text, replacements)
            projected = value_text.encode("utf-8")
    for value in forbidden:
        require(not value or value.encode() not in projected, "forbidden value remains after projection")
    return projected, {
        "escaped_reserved_token_counts": dict(sorted(escaped.items())),
        "sanitized_sha256": hashlib.sha256(projected).hexdigest(),
        "token_counts": dict(sorted(counts.items())),
    }


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.part")
    require(not temporary.exists(), f"stale temporary file: {temporary}")
    temporary.write_bytes(json.dumps(value, indent=2, sort_keys=True).encode() + b"\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _recover_phase_locked(
    config: dict[str, Any],
    *,
    source_validator: Callable[[dict[str, Any]], str],
    remote_probe: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    require(config.get("schema_version") == "a10m5r12r2-frozen-parent-identities-1", "identity schema changed")
    output = Path(config["recovery"]["output_root"])
    require(output.is_absolute() and not output.exists(), "successor output must be a fresh absolute path")
    published_head = source_validator(config)
    state_before = digest(Path(config["parent"]["state_path"]))
    state, plan = validate_parent(config)
    snapshot = remote_probe(config)
    validate_remote(config, snapshot)
    members = safe_members(Path(config["parent"]["archive_path"]), plan["evidence_allowlist"], config["caps"])
    staging = output.with_name(f".{output.name}.part-{os.getpid()}")
    require(not staging.exists(), "stale successor staging root")
    staging.mkdir(parents=True, mode=0o700)
    try:
        raw_root = staging / "raw"
        raw_root.mkdir(mode=0o700)
        raw_archive = raw_root / "evidence.tar"
        shutil.copyfile(config["parent"]["archive_path"], raw_archive)
        os.chmod(raw_archive, 0o600)
        require(digest(raw_archive) == config["parent"]["archive_sha256"], "successor raw archive copy changed")
        extracted = raw_root / "extracted"
        files = extract(raw_archive, extracted, members)
        files_by_name = {item["logical_name"]: item for item in files}
        for key, expected in config["expected_attempts"].items():
            require(
                files_by_name[expected["gate_receipt"]]["sha256"]
                == state["attempts"][key]["result"]["gate_receipt_sha256"],
                f"collected gate receipt changed after observation: {key}",
            )
        gate_map = {
            f"{key.rsplit('.', 1)[0]}.{name}": passed
            for key, attempt in read_json(Path(config["parent"]["state_path"]))["attempts"].items()
            for name, passed in attempt["result"]["gates"].items()
        }
        raw_record = record({
            "archive_bytes": config["caps"]["archive_bytes"],
            "archive_sha256": config["parent"]["archive_sha256"],
            "authority_id": config["parent"]["authority_id"],
            "cleanup_marker_sha256": config["parent"]["remote_marker_sha256"],
            "files": files,
            "gates": dict(sorted(gate_map.items())),
            "package_id": config["recovery"]["package_id"],
            "parent_package_id": config["parent"]["package_id"],
            "plan_id": config["parent"]["plan_id"],
            "producer": "recover_collection.py",
            "record_type": "RAW_COLLECTED_EQUIVALENT",
            "run_id": config["parent"]["run_id"],
            "schema_version": "a10m5r12r2-recovery-record-1",
            "source_commit": config["parent"]["source_commit"],
        })
        atomic_json(raw_root / "raw-collected-equivalent.json", raw_record)
        projection_root = staging / "evidence"
        projection_receipts = []
        forbidden = config["projection"]["forbidden_publication_substrings"]
        require(
            forbidden == ["rogerlew.ui", "/Users/roger", "/ceph/home/"],
            "forbidden projection set changed",
        )
        for item in files:
            logical = item["logical_name"]
            source = extracted.joinpath(*PurePosixPath(logical).parts)
            projected, projection = project(source.read_bytes(), source.suffix, plan["evidence_replacements"], forbidden)
            destination = projection_root.joinpath(*PurePosixPath(logical).parts)
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            destination.write_bytes(projected)
            os.chmod(destination, 0o600)
            if source.suffix in {".npz", ".pt"}:
                require(projected == source.read_bytes() and projection["sanitized_sha256"] == item["sha256"], f"binary projection changed: {logical}")
            projection_receipts.append({
                "logical_name": logical,
                "raw_parent_sha256": item["sha256"],
                "sanitizer_version": config["recovery"]["sanitizer_version"],
                **projection,
            })
        recovered_files = [
            {
                "logical_name": item["logical_name"],
                "bytes": (projection_root / item["logical_name"]).stat().st_size,
                "sha256": digest(projection_root / item["logical_name"]),
            }
            for item in files
        ]
        recovery = record({
            "actual_gpu_minutes": 0,
            "archive_remote_identity": snapshot,
            "files": recovered_files,
            "package_id": config["recovery"]["package_id"],
            "parent_plan_id": config["parent"]["plan_id"],
            "parent_plan_sha256": config["parent"]["plan_sha256"],
            "parent_run_id": config["parent"]["run_id"],
            "parent_state_sha256": state_before,
            "parent_actual_gpu_minutes": config["total_actual_gpu_minutes"],
            "projection_receipts": projection_receipts,
            "published_main_head": published_head,
            "record_type": "collection_recovery_receipt",
            "recovered_evidence_manifest_sha256": hashlib.sha256(
                canonical_bytes(recovered_files)
            ).hexdigest(),
            "remote_cleanup_performed": False,
            "sanitization_policy": config["recovery"]["sanitizer_version"],
            "schema_version": "a10m5r12r2-recovery-record-1",
            "source_commit": config["parent"]["source_commit"],
            "state": "RAW_COLLECTED_EQUIVALENT",
        })
        atomic_json(staging / "collection-recovery.json", recovery)
        require(digest(Path(config["parent"]["state_path"])) == state_before, "parent state mutated during recovery")
        os.replace(staging, output)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return recovery


def recover_phase(
    identity_path: Path = DEFAULT_IDENTITIES,
    *,
    source_validator: Callable[[dict[str, Any]], str] = validate_published_source,
    remote_probe: Callable[[dict[str, Any]], dict[str, Any]] = remote_snapshot,
) -> dict[str, Any]:
    config = read_json(identity_path)
    with parent_run_lock(config):
        return _recover_phase_locked(
            config, source_validator=source_validator, remote_probe=remote_probe
        )


def invoke_cleanup(config: dict[str, Any]) -> str:
    cleanup = config["cleanup"]
    script_path = Path(cleanup["script_path"])
    exact_file(script_path, cleanup["script_sha256"])
    repository = Path(config["published_source"]["repository_root"])
    committed = subprocess.run(
        ["git", "show", f"{config['parent']['source_commit']}:{cleanup['script_repository_path']}"],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout
    require(hashlib.sha256(committed).hexdigest() == cleanup["script_sha256"], "committed cleanup script changed")
    parent = config["parent"]
    command = [
        config["ssh"]["executable"], config["ssh"]["target"], "sh", "-s", "--",
        parent["remote_base"], parent["remote_run_root"], parent["run_id"],
        parent["package_id"], parent["source_commit"], parent["plan_id"],
    ]
    result = subprocess.run(command, input=committed, check=True, capture_output=True)
    return result.stdout.decode("ascii").strip()


def validate_replay(
    config: dict[str, Any],
    replay: Any,
    recovery: dict[str, Any],
    recovery_path: Path,
    replay_path: Path,
    published_head: str,
) -> None:
    """Validate the strict frozen selector-replay receipt and all parent bindings."""

    require(authenticated(replay), "selector replay receipt is not authenticated")
    contract = config["replay_contract"]
    expected_keys = {
        "byte_identical",
        "inputs",
        "package_id",
        "parent_package_id",
        "parent_plan_id",
        "parent_run_id",
        "pass_a_result_sha256",
        "pass_b_result_sha256",
        "protected_roles_opened",
        "record_sha256",
        "record_type",
        "replay_source_commit",
        "result_bytes",
        "schema_version",
        "source_commit",
        "temporal_result_sha256",
        "terminal",
    }
    require(set(replay) == expected_keys, "selector replay receipt schema changed")
    require(replay["schema_version"] == contract["schema_version"], "selector replay schema mismatch")
    require(replay["record_type"] == contract["record_type"], "selector replay type mismatch")
    require(replay["package_id"] == config["recovery"]["package_id"], "selector replay package mismatch")
    require(replay["parent_package_id"] == config["parent"]["package_id"], "selector replay parent mismatch")
    require(replay["parent_run_id"] == config["parent"]["run_id"], "selector replay run mismatch")
    require(replay["parent_plan_id"] == config["parent"]["plan_id"], "selector replay plan mismatch")
    require(replay["source_commit"] == config["parent"]["source_commit"], "selector replay source mismatch")
    inputs = replay["inputs"]
    require(isinstance(inputs, dict), "selector replay inputs missing")
    require(
        set(inputs)
        == {
            "binary",
            "collection_recovery_record_sha256",
            "collection_recovery_sha256",
            "corpus",
            "data_root",
            "evaluation_runtime",
            "observations",
            "predecessor_temporal_result",
            "published_main_head",
            "recovered_evidence_manifest_sha256",
            "selector_sources",
        },
        "selector replay input registry changed",
    )
    require(inputs.get("collection_recovery_record_sha256") == recovery["record_sha256"], "selector replay recovery-record binding mismatch")
    require(inputs.get("collection_recovery_sha256") == digest(recovery_path), "selector replay recovery-file binding mismatch")
    manifest_sha256 = hashlib.sha256(canonical_bytes(recovery["files"])).hexdigest()
    require(
        recovery.get("recovered_evidence_manifest_sha256") == manifest_sha256,
        "recovery evidence-manifest identity invalid",
    )
    require(inputs.get("recovered_evidence_manifest_sha256") == manifest_sha256, "selector replay evidence-manifest binding mismatch")
    runner = contract["runner"]
    runner_path = Path(runner["path"])
    exact_file(runner_path, runner["sha256"], runner["bytes"])
    repository = Path(config["published_source"]["repository_root"])
    committed = subprocess.run(
        ["git", "show", f"{replay['replay_source_commit']}:{runner['repository_path']}"],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout
    require(hashlib.sha256(committed).hexdigest() == runner["sha256"], "committed replay runner identity changed")
    require(
        GIT_COMMIT.fullmatch(replay.get("replay_source_commit", "")) is not None
        and inputs.get("published_main_head")
        == replay["replay_source_commit"]
        == published_head
        == recovery.get("published_main_head"),
        "published replay source mismatch",
    )
    require(inputs["binary"] == contract["binary"], "replay binary identity changed")
    require(inputs["corpus"] == contract["corpus"], "replay corpus identity changed")
    require(
        inputs["predecessor_temporal_result"] == contract["predecessor"],
        "replay predecessor identity changed",
    )
    runtime = inputs["evaluation_runtime"]
    require(
        isinstance(runtime, dict)
        and runtime.get("python") == "3.10.14"
        and runtime.get("numpy") == "2.2.6"
        and isinstance(runtime.get("executable"), dict)
        and set(runtime["executable"]) == {"bytes", "sha256"}
        and type(runtime["executable"]["bytes"]) is int
        and runtime["executable"]["bytes"] > 0
        and HEX64.fullmatch(runtime["executable"]["sha256"]) is not None,
        "replay runtime identity malformed",
    )
    observations = inputs["observations"]
    expected_observations = contract["observations"]
    require(
        isinstance(observations, dict)
        and observations.get("files") == expected_observations
        and observations.get("semantic_sha256")
        == hashlib.sha256(canonical_bytes(expected_observations)).hexdigest(),
        "replay observation identities changed",
    )
    data_root = inputs["data_root"]
    require(
        isinstance(data_root, dict)
        and set(data_root) == {"file_count", "semantic_sha256"}
        and type(data_root["file_count"]) is int
        and data_root["file_count"] > 0
        and HEX64.fullmatch(data_root["semantic_sha256"]) is not None,
        "replay data-root identity malformed",
    )
    sources = inputs.get("selector_sources")
    expected_source_names = {
        "artifacts/jobs/temporal_select.py",
        "artifacts/jobs/temporal_metrics.py",
        "artifacts/temporal-contract.json",
        "artifacts/portfolio-contract.json",
        "artifacts/sites.json",
        "artifacts/calendar-control-expectation.json",
    }
    require(isinstance(sources, dict) and set(sources) == expected_source_names, "selector source registry changed")
    for relative, identity in sources.items():
        require(isinstance(identity, dict) and set(identity) == {"bytes", "sha256"}, "selector source identity malformed")
        path = repository / config["parent"]["package_id"].replace("20260719-", "docs/work-packages/20260719-") / relative
        require(path.is_file(), f"selector source missing: {relative}")
        repository_path = path.relative_to(repository).as_posix()
        source_bytes = subprocess.run(
            ["git", "show", f"{config['parent']['source_commit']}:{repository_path}"],
            cwd=repository,
            check=True,
            capture_output=True,
        ).stdout
        require(identity == {"bytes": len(source_bytes), "sha256": hashlib.sha256(source_bytes).hexdigest()}, f"selector source identity changed: {relative}")
        require(path.read_bytes() == source_bytes, f"selector source working copy changed: {relative}")
    require(replay["byte_identical"] is True, "selector replay did not reproduce")
    require(replay["protected_roles_opened"] == [], "selector replay opened protected evidence")
    require(replay["terminal"] in contract["terminals"], "selector replay terminal invalid")
    pass_a = replay["pass_a_result_sha256"]
    pass_b = replay["pass_b_result_sha256"]
    require(HEX64.fullmatch(pass_a or "") is not None and pass_a == pass_b, "selector replay pass outputs differ")
    for relative in ("pass-a/temporal-result.json", "pass-b/temporal-result.json", "temporal-result.json"):
        result_path = replay_path.parent / relative
        exact_file(result_path, pass_a, replay["result_bytes"])
    require(replay["temporal_result_sha256"] == pass_a, "selector replay final-result binding mismatch")
    final_result = read_json(replay_path.parent / "temporal-result.json")
    require(
        final_result.get("terminal") == replay["terminal"]
        and final_result.get("protected_roles_opened") == []
        and final_result.get("prism_provenance")
        == read_json(repository / PREDECESSOR_RESULT_PATH).get("prism_provenance"),
        "selector replay final-result semantics changed",
    )


def _cleanup_phase_locked(
    config: dict[str, Any],
    *,
    source_validator: Callable[[dict[str, Any]], str],
    preclean_probe: Callable[[dict[str, Any]], dict[str, Any]],
    cleanup_invoker: Callable[[dict[str, Any]], str],
    postclean_probe: Callable[[dict[str, Any]], dict[str, bool]],
) -> dict[str, Any]:
    published_head = source_validator(config)
    output = Path(config["recovery"]["output_root"])
    recovery_path = output / "collection-recovery.json"
    require(
        output.is_dir()
        and not output.is_symlink()
        and recovery_path.is_file()
        and not recovery_path.is_symlink()
        and recovery_path.stat().st_nlink == 1,
        "recovery phase has not completed",
    )
    recovery = read_json(recovery_path)
    require(authenticated(recovery) and recovery.get("state") == "RAW_COLLECTED_EQUIVALENT", "recovery receipt invalid")
    cleanup_path = output / "cleanup-recovery.json"
    require(not cleanup_path.exists(), "cleanup already recorded")
    intent_path = output / "cleanup-intent.json"
    replay_path = Path(config["recovery"]["replay_receipt"])
    require(
        replay_path.is_absolute()
        and replay_path.is_file()
        and not replay_path.is_symlink()
        and replay_path.stat().st_nlink == 1
        and replay_path.resolve().is_relative_to(output.resolve()),
        "successor replay receipt missing",
    )
    replay = read_json(replay_path)
    validate_replay(
        config, replay, recovery, recovery_path, replay_path, published_head
    )
    recovery_file_sha256 = digest(recovery_path)
    replay_file_sha256 = digest(replay_path)
    state_before = digest(Path(config["parent"]["state_path"]))
    validate_parent(config)
    if intent_path.exists():
        require(intent_path.is_file() and not intent_path.is_symlink(), "cleanup intent invalid")
        intent = read_json(intent_path)
        require(authenticated(intent), "cleanup intent is not authenticated")
        before_cleanup = intent.get("preclean_remote_identity")
    else:
        before_cleanup = preclean_probe(config)
        validate_remote(config, before_cleanup)
        intent = record({
            "cleanup_marker_sha256": config["parent"]["remote_marker_sha256"],
            "cleanup_script_sha256": config["cleanup"]["script_sha256"],
            "evidence_manifest_sha256": replay["inputs"]["recovered_evidence_manifest_sha256"],
            "package_id": config["recovery"]["package_id"],
            "parent_package_id": config["parent"]["package_id"],
            "parent_plan_id": config["parent"]["plan_id"],
            "parent_state_sha256": state_before,
            "preclean_remote_identity": before_cleanup,
            "record_type": "collection_recovery_cleanup_intent",
            "recovery_receipt_file_sha256": recovery_file_sha256,
            "recovery_receipt_record_sha256": recovery["record_sha256"],
            "replay_receipt_file_sha256": replay_file_sha256,
            "replay_receipt_record_sha256": replay["record_sha256"],
            "schema_version": "a10m5r12r2-recovery-record-1",
            "replay_runner": config["replay_contract"]["runner"],
            "source_commit": config["parent"]["source_commit"],
        })
        atomic_json(intent_path, intent)
    expected_intent = {
        "cleanup_marker_sha256": config["parent"]["remote_marker_sha256"],
        "cleanup_script_sha256": config["cleanup"]["script_sha256"],
        "evidence_manifest_sha256": replay["inputs"]["recovered_evidence_manifest_sha256"],
        "package_id": config["recovery"]["package_id"],
        "parent_package_id": config["parent"]["package_id"],
        "parent_plan_id": config["parent"]["plan_id"],
        "parent_state_sha256": state_before,
        "preclean_remote_identity": before_cleanup,
        "record_type": "collection_recovery_cleanup_intent",
        "recovery_receipt_file_sha256": recovery_file_sha256,
        "recovery_receipt_record_sha256": recovery["record_sha256"],
        "replay_receipt_file_sha256": replay_file_sha256,
        "replay_receipt_record_sha256": replay["record_sha256"],
        "schema_version": "a10m5r12r2-recovery-record-1",
        "replay_runner": config["replay_contract"]["runner"],
        "source_commit": config["parent"]["source_commit"],
    }
    semantic_intent = dict(intent)
    semantic_intent.pop("record_sha256", None)
    require(semantic_intent == expected_intent, "cleanup intent binding changed")
    try:
        after_cleanup = postclean_probe(config)
    except (OSError, subprocess.SubprocessError, RecoveryError):
        after_cleanup = {}
    if after_cleanup != {"archive_absent": True, "marker_absent": True, "run_root_absent": True}:
        current = preclean_probe(config)
        validate_remote(config, current)
        require(current == before_cleanup, "remote evidence changed after cleanup intent")
        stdout = cleanup_invoker(config)
        require(stdout == "REMOTE_ABSENT", "remote cleanup did not prove absence")
        after_cleanup = postclean_probe(config)
    require(
        after_cleanup
        == {"archive_absent": True, "marker_absent": True, "run_root_absent": True},
        "post-clean remote absence not proven",
    )
    require(digest(recovery_path) == recovery_file_sha256, "recovery receipt changed during cleanup")
    require(digest(replay_path) == replay_file_sha256, "replay receipt changed during cleanup")
    require(digest(Path(config["parent"]["state_path"])) == state_before, "parent state mutated during cleanup")
    receipt = record({
        "cleanup_script_sha256": config["cleanup"]["script_sha256"],
        "package_id": config["recovery"]["package_id"],
        "parent_package_id": config["parent"]["package_id"],
        "parent_plan_id": config["parent"]["plan_id"],
        "parent_state_sha256": state_before,
        "preclean_remote_identity": before_cleanup,
        "record_type": "collection_recovery_cleanup_receipt",
        "recovery_receipt_sha256": digest(recovery_path),
        "remote_absent": True,
        "postclean_absence": after_cleanup,
        "cleanup_intent_record_sha256": intent["record_sha256"],
        "cleanup_intent_file_sha256": digest(intent_path),
        "replay_receipt_sha256": digest(replay_path),
        "schema_version": "a10m5r12r2-recovery-record-1",
        "source_commit": config["parent"]["source_commit"],
    })
    temporary_receipt = cleanup_path.with_name(f".{cleanup_path.name}.part")
    require(not temporary_receipt.exists(), "stale cleanup receipt temporary")
    temporary_receipt.write_bytes(
        json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n"
    )
    os.chmod(temporary_receipt, 0o600)
    require(digest(recovery_path) == recovery_file_sha256, "recovery receipt changed before cleanup receipt promotion")
    require(digest(replay_path) == replay_file_sha256, "replay receipt changed before cleanup receipt promotion")
    os.replace(temporary_receipt, cleanup_path)
    require(digest(recovery_path) == recovery_file_sha256, "recovery receipt changed through cleanup receipt write")
    require(digest(replay_path) == replay_file_sha256, "replay receipt changed through cleanup receipt write")
    return receipt


def cleanup_phase(
    identity_path: Path = DEFAULT_IDENTITIES,
    *,
    source_validator: Callable[[dict[str, Any]], str] = validate_published_source,
    preclean_probe: Callable[[dict[str, Any]], dict[str, Any]] = remote_snapshot,
    cleanup_invoker: Callable[[dict[str, Any]], str] = invoke_cleanup,
    postclean_probe: Callable[[dict[str, Any]], dict[str, bool]] = remote_absence,
) -> dict[str, Any]:
    config = read_json(identity_path)
    with parent_run_lock(config):
        return _cleanup_phase_locked(
            config,
            source_validator=source_validator,
            preclean_probe=preclean_probe,
            cleanup_invoker=cleanup_invoker,
            postclean_probe=postclean_probe,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("recover", "cleanup"))
    options = parser.parse_args()
    result = recover_phase() if options.phase == "recover" else cleanup_phase()
    print(result["record_sha256"])


if __name__ == "__main__":
    main()
