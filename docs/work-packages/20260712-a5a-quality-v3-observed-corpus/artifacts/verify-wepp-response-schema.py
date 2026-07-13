#!/usr/bin/env python3
"""Offline structural and semantic vectors for the A5 WEPP response contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "docs/specifications/a5-wepp-response-v1.schema.json"
PROTOCOL_PATH = Path(__file__).with_name("wepp-response-protocol.md")
SCHEMA_ID = "cligen-a5-wepp-response-v1"
PROTOCOL_ID = "cligen-a5-wepp-response-protocol-v1"
SEMANTIC_VALIDATOR_ID = "cligen-a5-wepp-response-semantic-v1"
SHA = "0" * 64
UNDECLARED_SHA = "f" * 64
STATISTICS = ("mean", "sd", "p95", "max")
GENERAL_METRICS = ("annual_runoff", "annual_peak_runoff", "annual_soil_loss")
COLD_METRICS = (
    "annual_max_snow_water_state",
    "annual_snowmelt",
    "rain_on_snow_runoff",
    "winter_runoff",
    "winter_soil_loss",
)


def semantic_validator_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def content_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SemanticError(ValueError):
    """Raised when a structurally valid record violates cross-row semantics."""


def reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON token: {token}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"JSON number overflows binary64: {token}")
    return value


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = child
    return value


def parse_json_bytes(value: bytes, label: str) -> object:
    try:
        return json.loads(
            value,
            parse_constant=reject_nonfinite,
            parse_float=parse_finite_float,
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{label}: invalid strict JSON: {error}") from error


def load_json(path: Path) -> object:
    return parse_json_bytes(path.read_bytes(), str(path))


def unavailable(metric_id: str) -> dict:
    return {
        "status": "unavailable",
        "metric_id": metric_id,
        "reason": "test vector: pinned output surface lacks this field",
        "source_audit": "test vector inspected every declared output",
    }


def available(metric_id: str, statistic: str, output_sha256: str = SHA) -> dict:
    return {
        "status": "available",
        "metric_id": metric_id,
        "statistic": statistic,
        "value": float(STATISTICS.index(statistic) + 1),
        "units": "test-unit",
        "n_years": 30,
        "source": {
            "output_sha256": output_sha256,
            "selector": f"{metric_id}[year]",
            "record_meaning": f"annual {metric_id} test records",
            "aggregation": "complete simulation years",
            "missing_value_rule": "reject a year containing a missing record",
        },
    }


def available_family(metric_id: str) -> list[dict]:
    return [available(metric_id, statistic) for statistic in STATISTICS]


def record(domain: str) -> dict:
    metrics = GENERAL_METRICS + (COLD_METRICS if domain == "cold_snow" else ())
    return {
        "wepp_response_schema_version": 1,
        "validation_contract": {
            "schema_id": SCHEMA_ID,
            "schema_sha256": content_sha256(SCHEMA_PATH),
            "protocol_id": PROTOCOL_ID,
            "protocol_sha256": content_sha256(PROTOCOL_PATH),
            "semantic_validator_id": SEMANTIC_VALIDATOR_ID,
            "semantic_validator_sha256": semantic_validator_sha256(),
        },
        "record_id": f"schema-vector-{domain}",
        "domain": domain,
        "climate": {
            "station_id": "id106388",
            "generation_profile": "faithful_5_32_3",
            "forcing_label": "synthetic",
            "horizon_years": 30,
            "replicate": {
                "key": "replicate-0",
                "legacy_burn_offset": 0,
                "extension_seed_u64_hex": None,
            },
            "parameter_fit": {
                "schema_id": "faithful-fixed-monthly",
                "model_id": "fixed_monthly_5_32_3",
                "fit_period": [1980, 2009],
                "content_sha256": SHA,
            },
            "runspec_sha256": SHA,
            "cli_sha256": SHA,
            "provenance_sha256": SHA,
            "quality_report_sha256": SHA,
            "quality_report_schema_version": 2,
            "metrics_version": 3,
        },
        "wepp_execution": {
            "executable": {"sha256": SHA, "bytes": 1},
            "version_output": "WEPP schema vector",
            "platform": "test-only",
            "invocation": ["wepp", "test.run"],
            "inputs": [
                {"role": role, "content": {"sha256": SHA, "bytes": 1}}
                for role in ("run", "management", "soil", "slope")
            ],
            "climate_installation": {
                "method_id": "test-only",
                "description": "test vector climate substitution",
            },
            "extraction_adapter": {
                "adapter_id": "schema-vector-v1",
                "content_sha256": SHA,
            },
        },
        "outputs": [{"role": "annual", "content": {"sha256": SHA, "bytes": 1}}],
        "responses": [unavailable(metric) for metric in metrics],
    }


def replace_family_with_available(value: dict, metric_id: str) -> None:
    value["responses"] = [
        row for row in value["responses"] if row["metric_id"] != metric_id
    ]
    value["responses"].extend(available_family(metric_id))


def family_row(value: dict, metric_id: str, statistic: str) -> dict:
    return next(
        row
        for row in value["responses"]
        if row["metric_id"] == metric_id and row.get("statistic") == statistic
    )


def validate_semantics(value: dict) -> None:
    """Enforce cross-row and cross-array response invariants deterministically."""

    expected_schema_sha256 = content_sha256(SCHEMA_PATH)
    if value["validation_contract"]["schema_sha256"] != expected_schema_sha256:
        raise SemanticError(
            "validation_contract.schema_sha256 does not identify the executing schema"
        )

    expected_protocol_sha256 = content_sha256(PROTOCOL_PATH)
    if value["validation_contract"]["protocol_sha256"] != expected_protocol_sha256:
        raise SemanticError(
            "validation_contract.protocol_sha256 does not identify the executing protocol"
        )

    expected_validator_sha256 = semantic_validator_sha256()
    if (
        value["validation_contract"]["semantic_validator_sha256"]
        != expected_validator_sha256
    ):
        raise SemanticError(
            "validation_contract.semantic_validator_sha256 does not identify "
            "the executing semantic validator"
        )

    output_hashes = [row["content"]["sha256"] for row in value["outputs"]]
    duplicate_output_hashes = sorted(
        sha256 for sha256, count in Counter(output_hashes).items() if count > 1
    )
    if duplicate_output_hashes:
        raise SemanticError(
            f"duplicate outputs[].content.sha256: {duplicate_output_hashes}"
        )
    declared_output_hashes = set(output_hashes)

    families: dict[str, list[dict]] = defaultdict(list)
    for row in value["responses"]:
        families[row["metric_id"]].append(row)

    required = set(GENERAL_METRICS)
    if value["domain"] == "cold_snow":
        required.update(COLD_METRICS)
    missing = sorted(required.difference(families))
    if missing:
        raise SemanticError(f"missing required response families: {missing}")

    for metric_id, rows in sorted(families.items()):
        statuses = {row["status"] for row in rows}
        if len(statuses) != 1:
            raise SemanticError(
                f"{metric_id}: available and unavailable rows may not be mixed"
            )
        if statuses == {"unavailable"}:
            if len(rows) != 1:
                raise SemanticError(
                    f"{metric_id}: expected exactly one unavailable row, got {len(rows)}"
                )
            continue

        if len(rows) != len(STATISTICS):
            raise SemanticError(
                f"{metric_id}: expected four available rows, got {len(rows)}"
            )
        statistics = [row["statistic"] for row in rows]
        duplicates = sorted(
            statistic for statistic, count in Counter(statistics).items() if count > 1
        )
        if duplicates:
            raise SemanticError(
                f"{metric_id}: duplicate family/statistic rows: {duplicates}"
            )
        missing_statistics = sorted(set(STATISTICS).difference(statistics))
        if missing_statistics:
            raise SemanticError(
                f"{metric_id}: missing statistics: {missing_statistics}"
            )

        horizon_years = value["climate"]["horizon_years"]
        n_years = {row["n_years"] for row in rows}
        if n_years != {horizon_years}:
            raise SemanticError(
                f"{metric_id}: every n_years must equal climate.horizon_years "
                f"{horizon_years}, got {sorted(n_years)}"
            )

        units = {row["units"] for row in rows}
        if len(units) != 1:
            raise SemanticError(
                f"{metric_id}: all four summaries must use identical units"
            )

        source = rows[0]["source"]
        if any(row["source"] != source for row in rows[1:]):
            raise SemanticError(
                f"{metric_id}: all four summaries must use identical source semantics"
            )

        values = {row["statistic"]: row["value"] for row in rows}
        if values["sd"] < 0.0:
            raise SemanticError(f"{metric_id}: sd must be nonnegative")
        negative_magnitudes = sorted(
            statistic
            for statistic, summary_value in values.items()
            if summary_value < 0.0
        )
        if negative_magnitudes:
            raise SemanticError(
                f"{metric_id}: all available response values must be nonnegative; "
                f"negative statistics: {negative_magnitudes}"
            )
        if values["mean"] > values["max"]:
            raise SemanticError(f"{metric_id}: mean may not exceed max")
        if values["p95"] > values["max"]:
            raise SemanticError(f"{metric_id}: p95 may not exceed max")

        for row in rows:
            output_sha256 = row["source"]["output_sha256"]
            if output_sha256 not in declared_output_hashes:
                raise SemanticError(
                    f"{metric_id}/{row['statistic']}: undeclared output hash "
                    f"{output_sha256}"
                )


def validate_contract(validator: Draft202012Validator, value: dict) -> None:
    validator.validate(value)
    validate_semantics(value)


def rejection_layer(validator: Draft202012Validator, value: dict) -> str | None:
    try:
        validator.validate(value)
    except ValidationError:
        return "schema"
    try:
        validate_semantics(value)
    except SemanticError:
        return "semantic"
    return None


def must_reject(
    validator: Draft202012Validator,
    value: dict,
    label: str,
    expected_layer: str,
) -> None:
    layer = rejection_layer(validator, value)
    if layer is None:
        raise AssertionError(f"negative vector unexpectedly passed: {label}")
    if layer != expected_layer:
        raise AssertionError(
            f"negative vector {label!r} failed in {layer}, expected {expected_layer}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record",
        action="append",
        default=[],
        type=Path,
        help="strict-parse and validate a response record; repeatable",
    )
    args = parser.parse_args()
    schema = load_json(SCHEMA_PATH)
    if not isinstance(schema, dict):
        raise ValueError("WEPP response schema is not a JSON object")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    unavailable_general = record("general")
    available_general = record("general")
    for metric_id in GENERAL_METRICS:
        replace_family_with_available(available_general, metric_id)
    available_hundred_year = copy.deepcopy(available_general)
    available_hundred_year["climate"]["horizon_years"] = 100
    for row in available_hundred_year["responses"]:
        row["n_years"] = 100
    mixed_cold = record("cold_snow")
    replace_family_with_available(mixed_cold, "annual_runoff")
    for positive in (
        unavailable_general,
        available_general,
        available_hundred_year,
        mixed_cold,
    ):
        validate_contract(validator, positive)

    unknown = copy.deepcopy(unavailable_general)
    unknown["undeclared"] = True
    must_reject(validator, unknown, "unknown top-level field", "schema")

    wrong_validator_id = copy.deepcopy(unavailable_general)
    wrong_validator_id["validation_contract"]["semantic_validator_id"] = "changed"
    must_reject(validator, wrong_validator_id, "wrong semantic-validator ID", "schema")

    wrong_schema_id = copy.deepcopy(unavailable_general)
    wrong_schema_id["validation_contract"]["schema_id"] = "changed"
    must_reject(validator, wrong_schema_id, "wrong schema ID", "schema")

    wrong_schema_hash = copy.deepcopy(unavailable_general)
    wrong_schema_hash["validation_contract"]["schema_sha256"] = "f" * 64
    must_reject(validator, wrong_schema_hash, "wrong schema content hash", "semantic")

    wrong_protocol_id = copy.deepcopy(unavailable_general)
    wrong_protocol_id["validation_contract"]["protocol_id"] = "changed"
    must_reject(validator, wrong_protocol_id, "wrong protocol ID", "schema")

    wrong_protocol_hash = copy.deepcopy(unavailable_general)
    wrong_protocol_hash["validation_contract"]["protocol_sha256"] = "f" * 64
    must_reject(
        validator, wrong_protocol_hash, "wrong protocol content hash", "semantic"
    )

    wrong_validator_hash = copy.deepcopy(unavailable_general)
    wrong_validator_hash["validation_contract"]["semantic_validator_sha256"] = "f" * 64
    must_reject(
        validator,
        wrong_validator_hash,
        "wrong semantic-validator content hash",
        "semantic",
    )

    missing_general = copy.deepcopy(unavailable_general)
    missing_general["responses"] = missing_general["responses"][:-1]
    must_reject(validator, missing_general, "missing annual soil-loss family", "schema")

    missing_cold = record("cold_snow")
    missing_cold["responses"] = [
        row
        for row in missing_cold["responses"]
        if row["metric_id"] != "rain_on_snow_runoff"
    ]
    must_reject(validator, missing_cold, "missing cold-domain family", "schema")

    missing_input = copy.deepcopy(unavailable_general)
    missing_input["wepp_execution"]["inputs"] = missing_input["wepp_execution"][
        "inputs"
    ][:-1]
    must_reject(validator, missing_input, "missing slope input binding", "schema")

    wrong_quality_version = copy.deepcopy(unavailable_general)
    wrong_quality_version["climate"]["metrics_version"] = 2
    must_reject(
        validator, wrong_quality_version, "wrong quality metric version", "schema"
    )

    missing_statistic = copy.deepcopy(available_general)
    missing_statistic["responses"] = [
        row
        for row in missing_statistic["responses"]
        if not (row["metric_id"] == "annual_runoff" and row["statistic"] == "max")
    ]
    must_reject(
        validator, missing_statistic, "missing available-family statistic", "schema"
    )

    mixed_status = copy.deepcopy(unavailable_general)
    mixed_status["responses"].append(available("annual_runoff", "mean"))
    must_reject(validator, mixed_status, "mixed available/unavailable family", "schema")

    duplicate_family_statistic = copy.deepcopy(available_general)
    duplicate_row = family_row(duplicate_family_statistic, "annual_runoff", "max")
    duplicate_row["statistic"] = "mean"
    duplicate_row["value"] = 99.0
    must_reject(
        validator,
        duplicate_family_statistic,
        "duplicate family/statistic row",
        "semantic",
    )

    undeclared_output = copy.deepcopy(available_general)
    for statistic in STATISTICS:
        family_row(undeclared_output, "annual_runoff", statistic)["source"][
            "output_sha256"
        ] = UNDECLARED_SHA
    must_reject(
        validator, undeclared_output, "undeclared response output hash", "semantic"
    )

    duplicate_output_hash = copy.deepcopy(available_general)
    duplicate_output_hash["outputs"].append(
        {"role": "events", "content": {"sha256": SHA, "bytes": 2}}
    )
    must_reject(
        validator,
        duplicate_output_hash,
        "duplicate outputs content hash",
        "semantic",
    )

    duplicate_unavailable = copy.deepcopy(unavailable_general)
    extra = unavailable("annual_runoff")
    extra["reason"] = "second unavailable row"
    duplicate_unavailable["responses"].append(extra)
    must_reject(
        validator, duplicate_unavailable, "duplicate unavailable family", "schema"
    )

    wrong_horizon_count = copy.deepcopy(available_hundred_year)
    for row in wrong_horizon_count["responses"]:
        row["n_years"] = 1
    must_reject(
        validator,
        wrong_horizon_count,
        "100-year horizon represented by one year",
        "semantic",
    )

    negative_sd = copy.deepcopy(available_general)
    family_row(negative_sd, "annual_runoff", "sd")["value"] = -0.1
    must_reject(validator, negative_sd, "negative sample SD", "semantic")

    mean_above_max = copy.deepcopy(available_general)
    family_row(mean_above_max, "annual_runoff", "mean")["value"] = 5.0
    must_reject(validator, mean_above_max, "mean exceeds maximum", "semantic")

    p95_above_max = copy.deepcopy(available_general)
    family_row(p95_above_max, "annual_runoff", "p95")["value"] = 5.0
    must_reject(validator, p95_above_max, "p95 exceeds maximum", "semantic")

    negative_response_magnitudes = copy.deepcopy(available_general)
    family_row(negative_response_magnitudes, "annual_runoff", "mean")["value"] = -1.0
    family_row(negative_response_magnitudes, "annual_runoff", "sd")["value"] = 0.0
    family_row(negative_response_magnitudes, "annual_runoff", "p95")["value"] = -0.5
    family_row(negative_response_magnitudes, "annual_runoff", "max")["value"] = 0.0
    must_reject(
        validator,
        negative_response_magnitudes,
        "negative non-SD response magnitudes",
        "semantic",
    )

    incoherent_units = copy.deepcopy(available_general)
    family_row(incoherent_units, "annual_runoff", "sd")["units"] = "other-unit"
    must_reject(validator, incoherent_units, "incoherent family units", "semantic")

    incoherent_source = copy.deepcopy(available_general)
    family_row(incoherent_source, "annual_runoff", "sd")["source"][
        "selector"
    ] = "different annual-series selector"
    must_reject(
        validator,
        incoherent_source,
        "incoherent family source semantics",
        "semantic",
    )

    parser_negatives = (
        (b'{"a":1,"a":2}', "duplicate object key"),
        (b'{"a":NaN}', "non-finite numeric token"),
        (b'{"a":1e400}', "positive binary64 overflow"),
        (b'{"a":-1e400}', "negative binary64 overflow"),
    )
    for payload, label in parser_negatives:
        try:
            parse_json_bytes(payload, label)
        except ValueError:
            pass
        else:
            raise AssertionError(f"strict JSON negative unexpectedly passed: {label}")

    for path in args.record:
        response = load_json(path)
        if not isinstance(response, dict):
            raise ValueError(f"{path}: response record is not a JSON object")
        validate_contract(validator, response)

    print(
        "WEPP response contract: Draft 2020-12 valid; "
        "4 positive and 28 negative structural/semantic/parser vectors pass; "
        f"{len(args.record)} external records validate"
    )


if __name__ == "__main__":
    main()
