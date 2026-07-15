"""Data-role firewall and atomic one-shot confirmation transition."""

from __future__ import annotations

import copy
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .artifacts import logical_record_key, validate_role_manifest_semantics
from .canonical import read_json, sha256_file, validate_schema, write_canonical
from .errors import HarnessError, require
from .log import AttemptLog

PROHIBITED_CONFIRMATION_OPERATIONS = {"fit", "evaluate", "optimize", "calibrate-gates"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RoleFirewall:
    """Reject confirmation data through identity and filesystem aliases."""

    def __init__(
        self,
        manifest: dict[str, Any],
        schema: dict[str, Any],
        protected_paths: Iterable[Path | str] = (),
    ):
        validate_schema(manifest, schema)
        validate_role_manifest_semantics(manifest)
        confirmation = next(role for role in manifest["roles"] if role["role"] == "confirmation")
        self.object_hashes = {record["object_sha256"] for record in confirmation["records"] if record["object_sha256"]}
        self.logical_hashes = {record["logical_sha256"] for record in confirmation["records"] if record["logical_sha256"]}
        self.record_keys = {logical_record_key(record) for record in confirmation["records"]}
        self.paths = {Path(path).resolve() for path in protected_paths}

    def authorize(
        self,
        operation: str,
        *,
        paths: Iterable[Path | str] = (),
        object_hashes: Iterable[str] = (),
        logical_hashes: Iterable[str] = (),
        record_keys: Iterable[tuple[Any, ...]] = (),
    ) -> None:
        if operation not in PROHIBITED_CONFIRMATION_OPERATIONS:
            return
        for path_like in paths:
            path = Path(path_like)
            resolved = path.resolve()
            require(resolved not in self.paths, "CONFIRMATION_PATH_REJECTED", str(path))
            if path.is_file():
                require(sha256_file(path) not in self.object_hashes, "CONFIRMATION_BYTES_REJECTED", str(path))
        require(not (set(object_hashes) & self.object_hashes), "CONFIRMATION_OBJECT_HASH_REJECTED", operation)
        require(not (set(logical_hashes) & self.logical_hashes), "CONFIRMATION_LOGICAL_HASH_REJECTED", operation)
        require(not (set(record_keys) & self.record_keys), "CONFIRMATION_RECORD_KEY_REJECTED", operation)


def append_metadata_read(
    manifest: dict[str, Any], actor: str, timestamp: str, access_log_directory: Path | str
) -> dict[str, Any]:
    require(manifest["confirmation_access_state"] == "metadata_only", "CONFIRMATION_STATE", "metadata read")
    result = copy.deepcopy(manifest)
    result["access_log"].append(
        {"timestamp": timestamp, "actor": actor, "action": "metadata_read", "object_sha256": None}
    )
    AttemptLog(access_log_directory).append(
        {
            "state": "access_record",
            "manifest_id": manifest["manifest_id"],
            "timestamp": timestamp,
            "actor": actor,
            "action": "metadata_read",
            "object_sha256": None,
        }
    )
    return result


def consume_confirmation(
    manifest_path: Path | str,
    schema_path: Path | str,
    expected_freeze_sha256: str,
    actor: str,
    access_log_directory: Path | str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Serialize and atomically make the sole sealed->consumed transition."""

    path = Path(manifest_path)
    lock_path = path.with_name(f".{path.name}.consume.lock")
    try:
        lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise HarnessError("CONFIRMATION_LOCKED", str(path)) from error
    except OSError as error:
        raise HarnessError("CONFIRMATION_LOCK_FAILED", f"{path}: {error}") from error
    try:
        return _consume_confirmation_locked(
            path,
            schema_path,
            expected_freeze_sha256,
            actor,
            access_log_directory,
            timestamp,
        )
    finally:
        os.close(lock_descriptor)
        lock_path.unlink(missing_ok=True)


def _consume_confirmation_locked(
    manifest_path: Path | str,
    schema_path: Path | str,
    expected_freeze_sha256: str,
    actor: str,
    access_log_directory: Path | str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Atomically make the sole sealed->consumed transition."""

    path = Path(manifest_path)
    schema = read_json(schema_path)
    manifest = read_json(path)
    validate_schema(manifest, schema)
    validate_role_manifest_semantics(manifest)
    require(manifest["confirmation_access_state"] == "sealed", "CONFIRMATION_NOT_SEALED", str(path))
    require(manifest.get("freeze_sha256") == expected_freeze_sha256, "CONFIRMATION_FREEZE_MISMATCH", str(path))
    confirmation = next(role for role in manifest["roles"] if role["role"] == "confirmation")
    require(bool(confirmation["records"]), "CONFIRMATION_EMPTY", str(path))
    for record in confirmation["records"]:
        require(record["access_state"] == "sealed", "CONFIRMATION_RECORD_NOT_SEALED", record["station_id"])
        require(record["object_sha256"] is not None and record["logical_sha256"] is not None, "CONFIRMATION_RECORD_INCOMPLETE", record["station_id"])

    result = copy.deepcopy(manifest)
    result["confirmation_access_state"] = "consumed"
    result_confirmation = next(role for role in result["roles"] if role["role"] == "confirmation")
    for record in result_confirmation["records"]:
        record["access_state"] = "consumed"
    event_timestamp = timestamp or utc_now()
    result["access_log"].append(
        {
            "timestamp": event_timestamp,
            "actor": actor,
            "action": "confirmation_consumed",
            "object_sha256": expected_freeze_sha256,
        }
    )
    validate_schema(result, schema)
    validate_role_manifest_semantics(result)

    # The durable access intent precedes the atomic state transition. A crash
    # can therefore leave an auditable attempted consumption, never an
    # unrecorded target access.
    AttemptLog(access_log_directory).append(
        {
            "state": "access_record",
            "manifest_id": manifest["manifest_id"],
            "timestamp": event_timestamp,
            "actor": actor,
            "action": "confirmation_consumed",
            "object_sha256": expected_freeze_sha256,
        }
    )

    temporary = path.with_name(f".{path.name}.consume-{os.getpid()}")
    write_canonical(temporary, result, immutable=True)
    try:
        os.replace(temporary, path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise HarnessError("CONFIRMATION_ATOMIC_REPLACE_FAILED", str(error)) from error
    return result
