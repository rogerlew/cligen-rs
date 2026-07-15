"""Immutable fit artifacts and cross-schema semantic validation."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .canonical import (
    finalize_self_hash,
    read_json,
    validate_schema,
    verify_self_hash,
    write_canonical,
)
from .errors import HarnessError, require


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise HarnessError("INVALID_DATE", field) from error


def validate_period(start: str, end: str) -> None:
    require(_parse_date(start, "period_start") <= _parse_date(end, "period_end"), "REVERSED_PERIOD", f"{start}>{end}")


def validate_role_manifest_semantics(manifest: dict[str, Any]) -> None:
    roles = manifest["roles"]
    names = [role["role"] for role in roles]
    require(len(names) == 4 and set(names) == {"coefficient_fit", "development", "gate_calibration", "confirmation"}, "ROLE_SET_INVALID", repr(names))

    identities: dict[tuple[Any, ...], str] = {}
    object_hashes: dict[str, str] = {}
    logical_hashes: dict[str, str] = {}
    for role in roles:
        for record in role["records"]:
            validate_period(record["period_start"], record["period_end"])
            key = logical_record_key(record)
            previous = identities.setdefault(key, role["role"])
            require(previous == role["role"], "ROLE_LOGICAL_OVERLAP", repr(key))
            for field, table in (("object_sha256", object_hashes), ("logical_sha256", logical_hashes)):
                value = record[field]
                if value is not None:
                    prior = table.setdefault(value, role["role"])
                    require(prior == role["role"], "ROLE_HASH_OVERLAP", f"{field}:{value}")

    exposed_keys = set()
    exposed_objects = set()
    exposed_logical = set()
    for record in manifest["exposed_logical_records"]:
        validate_period(record["period_start"], record["period_end"])
        exposed_keys.add(logical_record_key(record))
        if record["object_sha256"] is not None:
            exposed_objects.add(record["object_sha256"])
        if record["logical_sha256"] is not None:
            exposed_logical.add(record["logical_sha256"])
    confirmation = next(role for role in roles if role["role"] == "confirmation")
    for record in confirmation["records"]:
        require(logical_record_key(record) not in exposed_keys, "EXPOSED_CONFIRMATION_RECORD", record["station_id"])
        require(record["object_sha256"] not in exposed_objects, "EXPOSED_CONFIRMATION_RECORD", record["station_id"])
        require(record["logical_sha256"] not in exposed_logical, "EXPOSED_CONFIRMATION_RECORD", record["station_id"])


def logical_record_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record["source_id"],
        record["product_version"],
        record["station_id"],
        tuple(sorted(record["variables"])),
        record["calendar"],
        record["day_boundary"],
        record["period_start"],
        record["period_end"],
    )


def validate_fit_semantics(artifact: dict[str, Any]) -> None:
    for source in artifact["sources"]:
        validate_period(source["period_start"], source["period_end"])
        require(source.get("role", "coefficient_fit") == "coefficient_fit", "FIT_ROLE_VIOLATION", source["source_id"])
    if artifact["fit_status"] == "fit_valid":
        require(bool(artifact["parameters"]), "FIT_VALID_WITHOUT_PARAMETERS", artifact["fit_id"])
        hard_checks = artifact["diagnostics"]["hard_checks"]
        moment_checks = artifact["diagnostics"]["monthly_moment_checks"]
        require(bool(hard_checks) and all(check["status"] == "pass" for check in hard_checks), "FIT_VALID_HARD_CHECK", artifact["fit_id"])
        require(bool(moment_checks) and all(check["status"] == "pass" for check in moment_checks), "FIT_VALID_MONTHLY_MOMENT", artifact["fit_id"])
        require(artifact["diagnostics"]["identifiability"]["status"] == "pass", "FIT_VALID_IDENTIFIABILITY", artifact["fit_id"])
    else:
        require(artifact.get("status_reason") is not None, "FIT_STATUS_REASON_MISSING", artifact["fit_id"])


class FitArtifactStore:
    """Validate and persist immutable self-hashed fit artifacts."""

    def __init__(self, schema_path: Path | str):
        self.schema = read_json(schema_path)

    def finalize(self, artifact: dict[str, Any]) -> dict[str, Any]:
        result = finalize_self_hash(artifact, "content_sha256")
        validate_schema(result, self.schema)
        validate_fit_semantics(result)
        return result

    def write(self, path: Path | str, artifact: dict[str, Any]) -> dict[str, Any]:
        result = self.finalize(artifact)
        write_canonical(path, result, immutable=True)
        return result

    def read(self, path: Path | str) -> dict[str, Any]:
        artifact = read_json(path)
        require(isinstance(artifact, dict), "FIT_ARTIFACT_TYPE", "object required")
        validate_schema(artifact, self.schema)
        verify_self_hash(artifact, "content_sha256")
        validate_fit_semantics(artifact)
        return artifact
