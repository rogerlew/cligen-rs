"""Strict JSON parsing, canonical bytes, hashes, and schema validation."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

from .errors import HarnessError, require


def _reject_constant(value: str) -> None:
    raise HarnessError("NONFINITE_JSON", f"JSON constant {value!r} is prohibited")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HarnessError("DUPLICATE_JSON_KEY", f"duplicate object key {key!r}")
        result[key] = value
    return result


def ensure_finite(value: Any, path: str = "$") -> None:
    """Reject nonfinite numbers recursively before science computation."""

    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        require(math.isfinite(value), "NONFINITE_VALUE", f"nonfinite number at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            ensure_finite(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            ensure_finite(item, f"{path}.{key}")
        return
    raise HarnessError("UNSUPPORTED_JSON_TYPE", f"{type(value).__name__} at {path}")


def loads_strict(text: str) -> Any:
    """Parse JSON while rejecting duplicates and nonfinite constants."""

    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except HarnessError:
        raise
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HarnessError("INVALID_JSON", str(error)) from error
    ensure_finite(value)
    return value


def read_json(path: Path | str) -> Any:
    try:
        return loads_strict(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise HarnessError("READ_FAILED", f"{path}: {error}") from error


def canonical_bytes(value: Any) -> bytes:
    """Encode the A9 canonical JSON representation."""

    ensure_finite(value)
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise HarnessError("CANONICALIZATION_FAILED", str(error)) from error
    return (encoded + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise HarnessError("READ_FAILED", f"{path}: {error}") from error
    return digest.hexdigest()


def self_hash(value: dict[str, Any], field: str) -> str:
    require(field in value, "SELF_HASH_FIELD_MISSING", field)
    material = dict(value)
    del material[field]
    return sha256_bytes(canonical_bytes(material))


def finalize_self_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result[field] = "0" * 64
    result[field] = self_hash(result, field)
    return result


def verify_self_hash(value: dict[str, Any], field: str) -> None:
    expected = value.get(field)
    require(isinstance(expected, str), "SELF_HASH_FIELD_MISSING", field)
    require(expected == self_hash(value, field), "CONTENT_HASH_MISMATCH", field)


def validate_schema(instance: Any, schema: Any) -> None:
    """Validate a Draft 2020-12 schema and instance with format checking."""

    try:
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
            key=lambda error: list(error.absolute_path),
        )
    except SchemaError as schema_error:
        raise HarnessError("INVALID_SCHEMA", schema_error.message) from schema_error
    if errors:
        validation_error: ValidationError = errors[0]
        location = "$" + "".join(f"[{item!r}]" for item in validation_error.absolute_path)
        raise HarnessError("SCHEMA_VALIDATION_FAILED", f"{location}: {validation_error.message}")


def validate_file(path: Path | str, schema_path: Path | str) -> Any:
    instance = read_json(path)
    schema = read_json(schema_path)
    validate_schema(instance, schema)
    return instance


def write_canonical(path: Path | str, value: Any, *, immutable: bool = False) -> str:
    """Write canonical bytes atomically, optionally refusing replacement."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_bytes(value)
    if immutable:
        try:
            with destination.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as error:
            raise HarnessError("IMMUTABLE_ARTIFACT_EXISTS", str(destination)) from error
        except OSError as error:
            raise HarnessError("WRITE_FAILED", f"{destination}: {error}") from error
    else:
        temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        except OSError as error:
            temporary.unlink(missing_ok=True)
            raise HarnessError("WRITE_FAILED", f"{destination}: {error}") from error
    return sha256_bytes(data)
