#!/usr/bin/env python3
"""Validate and compare the complete frozen A5b WEPP response campaign.

Production usage:
  analyze-wepp-v6.py CAMPAIGN_INDEX CAMPAIGN_ARCHIVE_DIR CLIMATE_ANALYSIS

The only production output is ``artifacts/wepp/a5b-wepp-analysis-v1.json``.
The program independently validates all 2,176 response and execution records,
their canonical archive bindings, the frozen response schema and semantic
validator, and the exact profile/station/horizon/replicate matrix.  It also
requires the climate analysis to bind the exact post-WEPP candidate-manifest
identity recorded by this campaign and to report complete climate evidence.

Aggregation contract ``a5b-wepp-paired-hierarchical-median-v1``:

* candidate and faithful-off values are paired by exact station, horizon, and
  replicate before any aggregation;
* signed difference is ``candidate - faithful_off``;
* ratio is ``candidate / faithful_off`` and is JSON null when the paired
  faithful-off value is zero, including zero divided by zero;
* station summaries describe the eight paired replicates with conventional
  median, nearest-rank p05/p95, minimum, and maximum;
* domain and corpus summaries apply those same statistics to station medians,
  giving every applicable station equal weight; and
* unavailable schema families remain explicit availability counts and never
  become numeric zero. No downstream numeric pass bound is introduced.

Climate Gates 1--6 are copied unchanged from the sealed climate analysis.
Gate 7 is true exactly when this complete WEPP campaign validates.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import gzip
import hashlib
import importlib.util
import io
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import sys
import tarfile
import tempfile
from typing import Any, Iterable, Sequence

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = ROOT / "docs/work-packages/20260713-a5b-interannual-candidate-spike"
A5A = ROOT / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
CAMPAIGN_CONTRACT = Path(__file__).with_name("wepp-campaign-v3.md")
CAMPAIGN_RUNNER = Path(__file__).with_name("run-wepp-matrix-v6.py")
V4_CAMPAIGN_CONTRACT = Path(__file__).with_name("wepp-campaign-v1.md")
V4_CAMPAIGN_RUNNER = Path(__file__).with_name("run-wepp-matrix.py")
V4_ANALYZER = Path(__file__).with_name("analyze-wepp.py")
V5_CAMPAIGN_CONTRACT = Path(__file__).with_name("wepp-campaign-v2.md")
V5_CAMPAIGN_RUNNER = Path(__file__).with_name("run-wepp-matrix-v5.py")
V5_ANALYZER = Path(__file__).with_name("analyze-wepp-v5.py")
V5_AMENDMENT = PACKAGE / "artifacts/freeze/post-climate-wepp-amendment-v1.md"
V5_FREEZE = PACKAGE / "artifacts/freeze/post-climate-wepp-freeze-v1.json"
POST_CLIMATE_AMENDMENT = (
    PACKAGE / "artifacts/freeze/post-climate-wepp-amendment-v2.md"
)
POST_CLIMATE_FREEZE = (
    PACKAGE / "artifacts/freeze/post-climate-wepp-freeze-v2.json"
)
RESPONSE_SCHEMA = ROOT / "docs/specifications/a5-wepp-response-v1.schema.json"
RESPONSE_PROTOCOL = A5A / "artifacts/wepp-response-protocol.md"
RESPONSE_VERIFIER = A5A / "artifacts/verify-wepp-response-schema.py"
PRE_CANDIDATE_FREEZE = PACKAGE / "artifacts/freeze/pre-candidate-freeze-v1.json"
CLIMATE_ANALYZER = PACKAGE / "artifacts/climate/analyze-a5b.py"
EXPECTED_CLIMATE_ANALYSIS = PACKAGE / "artifacts/climate/a5b-analysis-v1.json"
OUTPUT = PACKAGE / "artifacts/wepp/a5b-wepp-analysis-v1.json"
ANALYZER_SOURCE = Path(__file__).resolve()

CANDIDATES = (
    "rank_one_monthly_sd",
    "full_monthly_covariance",
    "fourier_eof",
    "vector_ar",
    "gaussian_hmm",
    "spectral_random_phase",
    "precip_counterfactual",
)
PROFILES = ("faithful_off", *CANDIDATES)
GENERATION_PROFILES = {
    "faithful_off": "faithful_5_32_3",
    "rank_one_monthly_sd": "a5b_rank_one_monthly_sd_v1",
    "full_monthly_covariance": "a5b_full_monthly_covariance_v1",
    "fourier_eof": "a5b_fourier_eof_v1",
    "vector_ar": "a5b_vector_ar_v1",
    "gaussian_hmm": "a5b_gaussian_hmm_v1",
    "spectral_random_phase": "a5b_spectral_random_phase_v1",
    "precip_counterfactual": "a5b_fourier_eof_precip_counterfactual_v1",
}
STATIONS = (
    "ak505769",
    "al015478",
    "az022664",
    "az028619",
    "az029654",
    "ca042257",
    "ca042319",
    "co051660",
    "fl083909",
    "fl086997",
    "id106388",
    "mn214026",
    "ms227840",
    "nm294426",
    "tx412797",
    "ut429382",
    "wy485345",
)
COLD_STATIONS = frozenset(
    {"co051660", "wy485345", "mn214026", "ak505769", "id106388"}
)
HORIZONS = (30, 100)
REPLICATES = (
    (0, 0, "0x0c8862ed55f21e2e"),
    (1, 17, "0x0c268832683959b1"),
    (2, 101, "0x1a237b2016b95a3f"),
    (3, 503, "0x91328e5fa9a0e916"),
    (4, 1009, "0x0ee45605e7d362c3"),
    (5, 5003, "0xc59c065475f321a3"),
    (6, 10007, "0x9d9ef1d097f866ab"),
    (7, 50021, "0x50984769b3e59a89"),
)
STATISTICS = ("mean", "sd", "p95", "max")
GENERAL_METRICS = ("annual_runoff", "annual_peak_runoff", "annual_soil_loss")
COLD_METRICS = (
    "annual_max_snow_water_state",
    "annual_snowmelt",
    "rain_on_snow_runoff",
    "winter_runoff",
    "winter_soil_loss",
)
METRICS = (*GENERAL_METRICS, *COLD_METRICS)
EXPECTED_RUNS = 2_176
EXPECTED_ARCHIVE_MEMBERS = 544
MATRIX_PROJECTION_SHA256 = "93c163f85b9de61c48fe97a16c343e1ab50debb22fc39add24aef39fa67eaee1"
SELF_TEST_PROJECTION_SHA256 = "c4eb5eec66e283d6c015b93d408f049f4d3f1f46cd24dc28a2b8e0b8590ece6c"
CANONICAL_GZIP_HEADER = bytes((0x1F, 0x8B, 8, 0, 0, 0, 0, 0, 2, 255))
AGGREGATION_CONTRACT_ID = "a5b-wepp-paired-hierarchical-median-v1"
MATRIX_COORDINATES = tuple(itertools.product(PROFILES, STATIONS, HORIZONS, REPLICATES))
EXTRACTION_ADAPTER_ID = "a5b_wepp_p326_response_extractor_v6"
ELEMENT_OVERFLOW_POLICY_ID = "a5b_wepp_element_sm_f7_3_overflow_v1"
ELEMENT_EFFINT_OVERFLOW_POLICY_ID = "a5b_wepp_element_effint_f7_3_overflow_v1"
ELEMENT_SAME_DAY_POLICY_ID = "a5b_wepp_element_same_day_aggregation_v1"
ELEMENT_PEAK_RECOVERY_POLICY_ID = "a5b_wepp_element_peakro_f7_3_recovery_v1"
ELEMENT_OVERFLOW_ALLOWED = {
    "field": "Sm",
    "numeric_index_after_key": 7,
    "token": "*******",
    "fortran_format": "F7.3",
    "response_status": "not_consumed_by_a5b_response",
}
ELEMENT_EFFINT_OVERFLOW_ALLOWED = {
    "field": "EffInt",
    "numeric_index_after_key": 2,
    "token": "*******",
    "fortran_format": "F7.3",
    "response_status": "not_consumed_by_a5b_response",
}
ELEMENT_PEAK_OVERFLOW = {
    "field": "PeakRO",
    "numeric_index_after_key": 3,
    "token": "*******",
    "fortran_format": "F7.3",
    "numeric_lexical": "canonical_space_padded_fortran_without_zero_padding",
}
ELEMENT_PEAK_RECOVERY = {
    "run_output_option": 3,
    "header": "Event-by-event; abbreviated (Metric Units)",
    "preamble": "pinned_wepp_p326_event_output_55_lines_station_text_only_variable",
    "field": "peak runoff rate",
    "fortran_format": "F8.2",
    "numeric_lexical": "canonical_space_padded_fortran_without_zero_padding",
    "aggregation": "maximum_by_mapped_simulation_year_ordinal_day_ofe",
    "crosscheck_absolute_tolerance_mm_per_hour": 0.006,
    "crosscheck_arithmetic": "integer_thousandths",
    "non_hydrology_sections": "hash_bound_not_response_parsed_hydrology_phrases_block_bound",
}


class AnalysisError(RuntimeError):
    """A frozen contract, evidence closure, or comparison failure."""


@dataclass(frozen=True)
class Artifact:
    sha256: str
    bytes: int


@dataclass(frozen=True)
class ResponseRecord:
    sequence: int
    profile_id: str
    station_id: str
    horizon: int
    replicate: int
    domain: str
    available: dict[tuple[str, str], tuple[float, str]]
    unavailable: frozenset[str]
    element_same_day_duplicate_rows: int
    element_fixed_width_overflow_count: int
    element_effint_fixed_width_overflow_count: int
    element_peakro_recovery_count: int


def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AnalysisError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def reject_constant(token: str) -> None:
    raise AnalysisError(f"nonfinite JSON token is forbidden: {token}")


def finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise AnalysisError(f"JSON number overflows finite range: {token}")
    return value


def strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_pairs,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AnalysisError(f"cannot parse {label}: {error}") from error


def strict_json(path: Path) -> Any:
    return strict_json_bytes(path.read_bytes(), str(path))


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def compact_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AnalysisError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise AnalysisError(f"{label} must be an array")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise AnalysisError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def require_artifact(value: Any, label: str) -> Artifact:
    record = require_dict(value, label)
    require_exact_keys(record, {"sha256", "bytes"}, label)
    digest = record["sha256"]
    size = record["bytes"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or isinstance(size, bool)
        or not isinstance(size, int)
        or size < 0
    ):
        raise AnalysisError(f"{label} is not a SHA-256/byte identity")
    return Artifact(digest, size)


def verify_artifact(path: Path, artifact: Artifact, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise AnalysisError(f"{label} is missing, nonregular, or a symlink: {path}")
    if path.stat().st_size != artifact.bytes or sha256_path(path) != artifact.sha256:
        raise AnalysisError(f"{label} identity differs: {path}")


def safe_repository_path(relative: str, label: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise AnalysisError(f"{label} path is unsafe: {relative!r}")
    root = ROOT.resolve(strict=True)
    lexical = root.joinpath(*pure.parts)
    if lexical.is_symlink():
        raise AnalysisError(f"{label} may not be a symlink: {relative}")
    resolved = lexical.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise AnalysisError(f"{label} escapes the repository: {relative}")
    return resolved


def conventional_median(values: Sequence[float]) -> float:
    if not values:
        raise AnalysisError("median input is empty")
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def nearest_rank(values: Sequence[float], numerator: int, denominator: int) -> float:
    if not values:
        raise AnalysisError("nearest-rank input is empty")
    ordered = sorted(float(value) for value in values)
    rank = (numerator * len(ordered) + denominator - 1) // denominator
    rank = max(1, min(len(ordered), rank))
    return ordered[rank - 1]


def numeric_summary(values: Sequence[float]) -> dict[str, Any]:
    checked = [float(value) for value in values]
    if any(not math.isfinite(value) for value in checked):
        raise AnalysisError("comparison summary contains a nonfinite value")
    if not checked:
        return {
            "n": 0,
            "median": None,
            "p05": None,
            "p95": None,
            "minimum": None,
            "maximum": None,
        }
    return {
        "n": len(checked),
        "median": conventional_median(checked),
        "p05": nearest_rank(checked, 1, 20),
        "p95": nearest_rank(checked, 19, 20),
        "minimum": min(checked),
        "maximum": max(checked),
    }


def load_response_validator() -> tuple[Draft202012Validator, Any]:
    schema = require_dict(strict_json(RESPONSE_SCHEMA), "WEPP response schema")
    Draft202012Validator.check_schema(schema)
    spec = importlib.util.spec_from_file_location(
        "a5_wepp_response_semantic_v1", RESPONSE_VERIFIER
    )
    if spec is None or spec.loader is None:
        raise AnalysisError("cannot import frozen WEPP semantic verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return Draft202012Validator(schema), module


def validate_response(
    validator: Draft202012Validator, semantic: Any, value: dict[str, Any]
) -> None:
    try:
        semantic.validate_contract(validator, value)
    except Exception as error:
        raise AnalysisError(f"WEPP response contract failure: {error}") from error


def verify_frozen_tooling(index: dict[str, Any], climate_path: Path) -> dict[str, Any]:
    if not PRE_CANDIDATE_FREEZE.is_file():
        raise AnalysisError("pre-candidate freeze is missing")
    freeze = require_dict(strict_json(PRE_CANDIDATE_FREEZE), "pre-candidate freeze")
    if (
        freeze.get("pre_candidate_freeze_version") != 1
        or freeze.get("status") != "passed"
        or freeze.get("candidate_output_absent") is not True
    ):
        raise AnalysisError("pre-candidate freeze is not a passing revision-1 freeze")
    inventories = (
        require_dict(freeze.get("a5a_pinned_artifacts"), "freeze A5a inventory"),
        require_dict(freeze.get("a5b_frozen_artifacts"), "freeze A5b inventory"),
    )

    def frozen_hash(path: Path) -> str:
        relative = path.relative_to(ROOT).as_posix()
        matches = [inventory[relative] for inventory in inventories if relative in inventory]
        if len(matches) != 1 or not isinstance(matches[0], str):
            raise AnalysisError(f"freeze does not uniquely bind {relative}")
        if sha256_path(path) != matches[0]:
            raise AnalysisError(f"frozen artifact differs: {relative}")
        return matches[0]

    post_freeze = require_dict(
        strict_json(POST_CLIMATE_FREEZE), "post-climate WEPP freeze"
    )
    if (
        post_freeze.get("post_climate_wepp_freeze_version") != 2
        or post_freeze.get("status") != "passed"
        or post_freeze.get("boundary")
        != {
            "candidate_climate_output_present": True,
            "candidate_response_values_inspected": True,
            "wepp_response_output_absent": True,
        }
    ):
        raise AnalysisError("post-climate WEPP freeze status/boundary differs")
    post_inventories = (
        require_dict(
            post_freeze.get("immutable_anchors"), "post-freeze immutable anchors"
        ),
        require_dict(post_freeze.get("v6_artifacts"), "post-freeze v6 artifacts"),
    )

    def post_hash(path: Path) -> str:
        relative = path.relative_to(ROOT).as_posix()
        matches = [
            inventory[relative] for inventory in post_inventories if relative in inventory
        ]
        if len(matches) != 1:
            raise AnalysisError(f"post-climate freeze does not uniquely bind {relative}")
        record = require_dict(matches[0], f"post-climate artifact {relative}")
        if set(record) != {"sha256", "bytes"}:
            raise AnalysisError(f"post-climate artifact record is not closed: {relative}")
        artifact = require_artifact(record, f"post-climate artifact {relative}")
        sha256 = artifact.sha256
        byte_count = artifact.bytes
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != byte_count
            or sha256_path(path) != sha256
        ):
            raise AnalysisError(f"post-climate frozen artifact differs: {relative}")
        return sha256

    for path in (
        RESPONSE_SCHEMA,
        RESPONSE_PROTOCOL,
        RESPONSE_VERIFIER,
        CLIMATE_ANALYZER,
    ):
        frozen_hash(path)
    for path in (
        PRE_CANDIDATE_FREEZE,
        V4_CAMPAIGN_CONTRACT,
        V4_CAMPAIGN_RUNNER,
        V4_ANALYZER,
        V5_FREEZE,
        V5_CAMPAIGN_CONTRACT,
        V5_CAMPAIGN_RUNNER,
        V5_ANALYZER,
        V5_AMENDMENT,
        ANALYZER_SOURCE,
        CAMPAIGN_CONTRACT,
        CAMPAIGN_RUNNER,
        POST_CLIMATE_AMENDMENT,
    ):
        post_hash(path)
    for path in (V4_CAMPAIGN_CONTRACT, V4_CAMPAIGN_RUNNER, V4_ANALYZER):
        if frozen_hash(path) != post_hash(path):
            raise AnalysisError(f"v4 immutable anchor differs across freezes: {path}")

    contracts = require_dict(index.get("contracts"), "campaign contracts")
    expected_contracts = {
        "campaign": (CAMPAIGN_CONTRACT, post_hash),
        "response_schema": (RESPONSE_SCHEMA, frozen_hash),
        "response_protocol": (RESPONSE_PROTOCOL, frozen_hash),
        "response_verifier": (RESPONSE_VERIFIER, frozen_hash),
        "runner": (CAMPAIGN_RUNNER, post_hash),
    }
    require_exact_keys(contracts, set(expected_contracts), "campaign contracts")
    for name, (path, hash_function) in expected_contracts.items():
        record = require_dict(contracts[name], f"campaign contract {name}")
        require_exact_keys(record, {"path", "sha256"}, f"campaign contract {name}")
        if (
            record["path"] != path.relative_to(ROOT).as_posix()
            or record["sha256"] != hash_function(path)
        ):
            raise AnalysisError(f"campaign contract differs from freeze: {name}")

    if climate_path.resolve(strict=True) != EXPECTED_CLIMATE_ANALYSIS.resolve(strict=True):
        raise AnalysisError("climate analysis path differs from the frozen A5b output")
    return {
        "pre_candidate_freeze_sha256": sha256_path(PRE_CANDIDATE_FREEZE),
        "analyzer_sha256": post_hash(ANALYZER_SOURCE),
    }


def validate_index_shape(index: dict[str, Any]) -> None:
    require_exact_keys(
        index,
        {
            "wepp_response_campaign_version",
            "status",
            "contracts",
            "matrix",
            "wepp",
            "baseline",
            "candidate",
            "archives",
            "runs",
            "execution",
        },
        "campaign index",
    )
    if index["wepp_response_campaign_version"] != 1 or index["status"] != "sealed":
        raise AnalysisError("campaign index is not sealed revision 1")
    matrix = require_dict(index["matrix"], "campaign matrix")
    require_exact_keys(
        matrix,
        {
            "stations",
            "horizons_years",
            "replicates",
            "profiles",
            "expected_runs",
            "actual_runs",
            "projection_sha256",
        },
        "campaign matrix",
    )
    if (
        matrix["stations"] != list(STATIONS)
        or matrix["horizons_years"] != list(HORIZONS)
        or matrix["profiles"] != list(PROFILES)
        or matrix["replicates"]
        != [
            {"replicate": replicate, "legacy_burn": burn, "extension_seed": seed}
            for replicate, burn, seed in REPLICATES
        ]
        or matrix["expected_runs"] != EXPECTED_RUNS
        or matrix["actual_runs"] != EXPECTED_RUNS
    ):
        raise AnalysisError("campaign matrix definition differs")
    if (
        matrix["projection_sha256"] != MATRIX_PROJECTION_SHA256
        or len(MATRIX_COORDINATES) != EXPECTED_RUNS
    ):
        raise AnalysisError("campaign matrix projection identity differs")
    wepp = require_dict(index["wepp"], "campaign WEPP identity")
    if wepp.get("extraction_adapter_id") != EXTRACTION_ADAPTER_ID:
        raise AnalysisError("campaign extraction-adapter identity differs")
    execution = require_dict(index["execution"], "campaign execution")
    if (
        execution.get("failures") != []
        or execution.get("candidate_cli_bytes_removed_after_wepp") is not True
        or execution.get("baseline_regenerations_removed") is not True
        or execution.get("raw_wepp_outputs_removed") is not True
        or execution.get("raw_wepp_outputs_redistributed") is not False
    ):
        raise AnalysisError("campaign execution closure is incomplete")


def validate_run_row(row: dict[str, Any], sequence: int) -> None:
    require_exact_keys(
        row,
        {
            "sequence",
            "record_id",
            "profile_id",
            "archive",
            "response",
            "execution",
            "raw_output_audit",
        },
        f"campaign run {sequence}",
    )
    if row["sequence"] != sequence or row["profile_id"] not in PROFILES:
        raise AnalysisError(f"campaign run sequence/profile differs: {sequence}")
    expected_archive = f"wepp-response-{row['profile_id']}-v1.tar.gz"
    if row["archive"] != expected_archive:
        raise AnalysisError(f"campaign run archive differs: {sequence}")
    for role in ("response", "execution"):
        binding = require_dict(row[role], f"run {sequence} {role}")
        require_exact_keys(binding, {"member", "sha256", "bytes"}, f"run {sequence} {role}")
        require_artifact(
            {"sha256": binding["sha256"], "bytes": binding["bytes"]},
            f"run {sequence} {role}",
        )
        expected_member = f"runs/{row['record_id']}/{role}.json"
        if binding["member"] != expected_member:
            raise AnalysisError(f"run {sequence} {role} member differs")
    audits = require_list(row["raw_output_audit"], f"run {sequence} raw audit")
    if not audits:
        raise AnalysisError(f"run {sequence} raw-output audit is empty")
    roles: set[str] = set()
    for audit in audits:
        checked = require_dict(audit, f"run {sequence} raw audit row")
        require_exact_keys(
            checked, {"role", "content", "retained"}, f"run {sequence} raw audit row"
        )
        if checked["retained"] is not False or checked["role"] in roles:
            raise AnalysisError(f"run {sequence} raw-output audit differs")
        roles.add(checked["role"])
        require_artifact(checked["content"], f"run {sequence} raw {checked['role']}")


def artifact_identity_map(
    value: Any,
    label: str,
    required_row_keys: set[str],
) -> dict[str, Artifact]:
    rows = require_list(value, label)
    identities: dict[str, Artifact] = {}
    for index, value_row in enumerate(rows):
        row = require_dict(value_row, f"{label}[{index}]")
        require_exact_keys(row, required_row_keys, f"{label}[{index}]")
        role = row.get("role")
        if not isinstance(role, str) or not role or role in identities:
            raise AnalysisError(f"{label}: artifact role differs")
        identities[role] = require_artifact(
            row.get("content"), f"{label}[{index}].content"
        )
    return identities


def validate_nonresponse_overflow_audit(
    value: Any,
    element_artifact: Artifact,
    element_rows: int,
    horizon: int,
    sequence: int,
    policy_id: str,
    expected_allowed: dict[str, Any],
    label: str,
) -> int:
    overflow = require_dict(value, f"run {sequence} {label} overflow audit")
    require_exact_keys(
        overflow,
        {
            "policy_id",
            "source_element_sha256",
            "allowed",
            "total_element_rows",
            "observed",
        },
        f"run {sequence} {label} overflow audit",
    )
    if (
        overflow["policy_id"] != policy_id
        or overflow["source_element_sha256"] != element_artifact.sha256
        or overflow["total_element_rows"] != element_rows
    ):
        raise AnalysisError(f"run {sequence}: {label} overflow policy/source differs")
    allowed = require_dict(
        overflow["allowed"], f"run {sequence} {label} overflow allowance"
    )
    require_exact_keys(
        allowed, set(expected_allowed), f"run {sequence} {label} overflow allowance"
    )
    if allowed != expected_allowed:
        raise AnalysisError(f"run {sequence}: {label} overflow allowance differs")
    observed = require_dict(
        overflow["observed"], f"run {sequence} {label} overflow observation"
    )
    if not observed:
        return 0
    require_exact_keys(
        observed,
        {"count", "first_mapped_key"},
        f"run {sequence} {label} overflow observation",
    )
    count = observed["count"]
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= element_rows:
        raise AnalysisError(f"run {sequence}: {label} overflow count is invalid")
    first_key = require_dict(
        observed["first_mapped_key"], f"run {sequence} first {label} overflow key"
    )
    require_exact_keys(
        first_key,
        {"simulation_year", "ordinal_day", "ofe"},
        f"run {sequence} first {label} overflow key",
    )
    simulation_year = first_key["simulation_year"]
    ordinal_day = first_key["ordinal_day"]
    ofe = first_key["ofe"]
    if any(
        isinstance(item, bool) or not isinstance(item, int)
        for item in (simulation_year, ordinal_day, ofe)
    ):
        raise AnalysisError(f"run {sequence}: first {label} overflow key is not integral")
    legacy_leap = simulation_year % 4 == 0 or (
        horizon == 100 and simulation_year == 100
    )
    if (
        not 1 <= simulation_year <= horizon
        or not 1 <= ordinal_day <= (366 if legacy_leap else 365)
        or ofe != 1
    ):
        raise AnalysisError(f"run {sequence}: first {label} overflow key is invalid")
    return count


def validate_element_fixed_width_overflow(
    parser: Any,
    raw_output_audits: Sequence[Any],
    horizon: int,
    sequence: int,
) -> tuple[int, int, int, int]:
    """Validate reduction, recovery, and both nonresponse F7.3 exceptions."""

    parser_record = require_dict(parser, f"run {sequence} parser audit")
    require_exact_keys(
        parser_record,
        {
            "adapter_id",
            "adapter_sha256",
            "element_record_rows",
            "element_record_keys",
            "hourly_record_dates",
            "rain_on_snow_eligible_dates",
            "rain_on_snow_join",
            "rain_on_snow_units",
            "element_same_day_aggregation",
            "element_fixed_width_overflow",
            "element_effint_fixed_width_overflow",
            "element_peakro_recovery",
        },
        f"run {sequence} parser audit",
    )
    if (
        parser_record["adapter_id"] != EXTRACTION_ADAPTER_ID
        or parser_record["adapter_sha256"] != sha256_path(CAMPAIGN_RUNNER)
    ):
        raise AnalysisError(f"run {sequence}: extraction-adapter identity differs")
    element_rows = parser_record["element_record_rows"]
    element_keys = parser_record["element_record_keys"]
    if (
        isinstance(element_rows, bool)
        or not isinstance(element_rows, int)
        or element_rows < 1
        or isinstance(element_keys, bool)
        or not isinstance(element_keys, int)
        or not 1 <= element_keys <= element_rows
    ):
        raise AnalysisError(f"run {sequence}: element record-key count is invalid")

    element_audits: list[dict[str, Any]] = []
    event_audits: list[dict[str, Any]] = []
    for value in raw_output_audits:
        audit = require_dict(value, f"run {sequence} execution raw audit")
        if audit.get("role") == "element":
            element_audits.append(audit)
        elif audit.get("role") == "soil_loss":
            event_audits.append(audit)
    if len(element_audits) != 1:
        raise AnalysisError(f"run {sequence}: expected exactly one element raw audit")
    element_audit = element_audits[0]
    if element_audit.get("retained") is not False:
        raise AnalysisError(f"run {sequence}: element raw output was retained")
    element_artifact = require_artifact(
        element_audit.get("content"), f"run {sequence} raw element"
    )
    if len(event_audits) != 1 or event_audits[0].get("retained") is not False:
        raise AnalysisError(f"run {sequence}: expected one removed event-hydrology audit")
    event_artifact = require_artifact(
        event_audits[0].get("content"), f"run {sequence} raw event hydrology"
    )

    same_day = require_dict(
        parser_record["element_same_day_aggregation"],
        f"run {sequence} element same-day aggregation audit",
    )
    require_exact_keys(
        same_day,
        {
            "policy_id",
            "source_element_sha256",
            "key",
            "aggregation",
            "total_element_rows",
            "unique_date_ofe_keys",
            "observed",
        },
        f"run {sequence} element same-day aggregation audit",
    )
    expected_aggregation = {
        "runoff": "sum",
        "peak_runoff": "max",
        "sediment_leave": "sum",
        "qrain": "sum_before_daily_rain_on_snow_join",
    }
    if (
        same_day["policy_id"] != ELEMENT_SAME_DAY_POLICY_ID
        or same_day["source_element_sha256"] != element_artifact.sha256
        or same_day["key"] != ["simulation_year", "ordinal_day", "ofe"]
        or same_day["aggregation"] != expected_aggregation
        or same_day["total_element_rows"] != element_rows
        or same_day["unique_date_ofe_keys"] != element_keys
    ):
        raise AnalysisError(f"run {sequence}: element same-day aggregation differs")
    duplicate_rows = element_rows - element_keys
    same_day_observed = require_dict(
        same_day["observed"], f"run {sequence} same-day aggregation observation"
    )
    if duplicate_rows == 0:
        if same_day_observed:
            raise AnalysisError(f"run {sequence}: unexpected same-day aggregation observation")
    else:
        require_exact_keys(
            same_day_observed,
            {"duplicate_rows", "first_mapped_key"},
            f"run {sequence} same-day aggregation observation",
        )
        if same_day_observed["duplicate_rows"] != duplicate_rows:
            raise AnalysisError(f"run {sequence}: same-day duplicate row count differs")
        duplicate_key = require_dict(
            same_day_observed["first_mapped_key"],
            f"run {sequence} first same-day duplicate key",
        )
        require_exact_keys(
            duplicate_key,
            {"simulation_year", "ordinal_day", "ofe"},
            f"run {sequence} first same-day duplicate key",
        )
        simulation_year = duplicate_key["simulation_year"]
        ordinal_day = duplicate_key["ordinal_day"]
        ofe = duplicate_key["ofe"]
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (simulation_year, ordinal_day, ofe)
        ):
            raise AnalysisError(f"run {sequence}: first same-day duplicate key is not integral")
        legacy_leap = simulation_year % 4 == 0 or (
            horizon == 100 and simulation_year == 100
        )
        if (
            not 1 <= simulation_year <= horizon
            or not 1 <= ordinal_day <= (366 if legacy_leap else 365)
            or ofe != 1
        ):
            raise AnalysisError(f"run {sequence}: first same-day duplicate key is invalid")

    peak_recovery = require_dict(
        parser_record["element_peakro_recovery"],
        f"run {sequence} element PeakRO recovery audit",
    )
    require_exact_keys(
        peak_recovery,
        {
            "policy_id",
            "source_element_sha256",
            "source_event_hydrology_sha256",
            "element_overflow",
            "recovery",
            "event_hydrology_records",
            "event_hydrology_unique_keys",
            "event_hydrology_duplicate_rows",
            "crosschecked_unique_keys",
            "observed",
        },
        f"run {sequence} element PeakRO recovery audit",
    )
    if (
        peak_recovery["policy_id"] != ELEMENT_PEAK_RECOVERY_POLICY_ID
        or peak_recovery["source_element_sha256"] != element_artifact.sha256
        or peak_recovery["source_event_hydrology_sha256"] != event_artifact.sha256
        or peak_recovery["element_overflow"] != ELEMENT_PEAK_OVERFLOW
        or peak_recovery["recovery"] != ELEMENT_PEAK_RECOVERY
    ):
        raise AnalysisError(f"run {sequence}: element PeakRO recovery differs")
    event_records = peak_recovery["event_hydrology_records"]
    event_keys = peak_recovery["event_hydrology_unique_keys"]
    event_duplicates = peak_recovery["event_hydrology_duplicate_rows"]
    event_crosschecked = peak_recovery["crosschecked_unique_keys"]
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in (event_records, event_keys, event_duplicates, event_crosschecked)
    ) or (
        event_records < 0
        or not 0 <= event_keys <= event_records
        or event_keys > element_keys
        or event_duplicates != event_records - event_keys
        or event_crosschecked != event_keys
    ):
        raise AnalysisError(f"run {sequence}: element PeakRO recovery counts differ")
    peak_observed = require_dict(
        peak_recovery["observed"], f"run {sequence} PeakRO recovery observation"
    )
    peak_count = 0
    if peak_observed:
        require_exact_keys(
            peak_observed,
            {"count", "first_mapped_key"},
            f"run {sequence} PeakRO recovery observation",
        )
        peak_count = peak_observed["count"]
        if (
            isinstance(peak_count, bool)
            or not isinstance(peak_count, int)
            or not 1 <= peak_count <= min(event_records, element_rows)
        ):
            raise AnalysisError(f"run {sequence}: PeakRO recovery count is invalid")
        peak_key = require_dict(
            peak_observed["first_mapped_key"],
            f"run {sequence} first PeakRO recovery key",
        )
        require_exact_keys(
            peak_key,
            {"simulation_year", "ordinal_day", "ofe"},
            f"run {sequence} first PeakRO recovery key",
        )
        simulation_year = peak_key["simulation_year"]
        ordinal_day = peak_key["ordinal_day"]
        ofe = peak_key["ofe"]
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (simulation_year, ordinal_day, ofe)
        ):
            raise AnalysisError(f"run {sequence}: PeakRO recovery key is not integral")
        legacy_leap = simulation_year % 4 == 0 or (
            horizon == 100 and simulation_year == 100
        )
        if (
            not 1 <= simulation_year <= horizon
            or not 1 <= ordinal_day <= (366 if legacy_leap else 365)
            or ofe != 1
        ):
            raise AnalysisError(f"run {sequence}: PeakRO recovery key is invalid")

    sm_count = validate_nonresponse_overflow_audit(
        parser_record["element_fixed_width_overflow"],
        element_artifact,
        element_rows,
        horizon,
        sequence,
        ELEMENT_OVERFLOW_POLICY_ID,
        ELEMENT_OVERFLOW_ALLOWED,
        "Sm",
    )
    effint_count = validate_nonresponse_overflow_audit(
        parser_record["element_effint_fixed_width_overflow"],
        element_artifact,
        element_rows,
        horizon,
        sequence,
        ELEMENT_EFFINT_OVERFLOW_POLICY_ID,
        ELEMENT_EFFINT_OVERFLOW_ALLOWED,
        "EffInt",
    )
    return sm_count, effint_count, duplicate_rows, peak_count


def response_record(
    row: dict[str, Any], response: dict[str, Any], execution: dict[str, Any]
) -> ResponseRecord:
    sequence = row["sequence"]
    if response["record_id"] != row["record_id"]:
        raise AnalysisError(f"run {sequence}: response record ID differs")
    if (
        execution.get("wepp_execution_record_version") != 1
        or execution.get("record_id") != row["record_id"]
        or execution.get("sequence") != sequence
    ):
        raise AnalysisError(f"run {sequence}: execution identity differs")
    climate = require_dict(response["climate"], f"run {sequence} climate")
    if execution.get("climate_lineage") != climate:
        raise AnalysisError(f"run {sequence}: response/execution climate lineage differs")
    profile = row["profile_id"]
    station = climate["station_id"]
    horizon = climate["horizon_years"]
    replicate_record = require_dict(climate["replicate"], f"run {sequence} replicate")
    key = replicate_record.get("key")
    if not isinstance(key, str) or not key.startswith("replicate-"):
        raise AnalysisError(f"run {sequence}: replicate key differs")
    try:
        replicate = int(key.removeprefix("replicate-"))
    except ValueError as error:
        raise AnalysisError(f"run {sequence}: replicate key is malformed") from error
    expected_tuple = MATRIX_COORDINATES[sequence]
    expected_profile, expected_station, expected_horizon, expected_replicate = expected_tuple
    rep, burn, seed = expected_replicate
    expected_record_id = (
        f"a5b-wepp-{expected_station}-{expected_profile}-{expected_horizon}yr-rep{rep}"
    )
    expected_domain = "cold_snow" if expected_station in COLD_STATIONS else "general"
    if (
        (profile, station, horizon, replicate)
        != (expected_profile, expected_station, expected_horizon, rep)
        or row["record_id"] != expected_record_id
        or response["domain"] != expected_domain
        or replicate_record.get("legacy_burn_offset") != burn
        or replicate_record.get("extension_seed_u64_hex")
        != (None if profile == "faithful_off" else seed)
    ):
        raise AnalysisError(f"run {sequence}: response matrix coordinates differ")
    if climate["generation_profile"] != GENERATION_PROFILES[profile]:
        raise AnalysisError(f"run {sequence}: generation profile identity differs")

    output_roles = {"element", "soil_loss"}
    if expected_domain == "cold_snow":
        output_roles.add("hourly_winter")
    raw_roles = output_roles | {"stdout", "stderr"}
    indexed_audit = artifact_identity_map(
        row["raw_output_audit"],
        f"run {sequence} indexed raw audit",
        {"role", "content", "retained"},
    )
    if any(
        require_dict(audit, f"run {sequence} indexed raw row").get("retained")
        is not False
        for audit in row["raw_output_audit"]
    ):
        raise AnalysisError(f"run {sequence}: indexed raw output was retained")
    execution_audits = require_list(
        execution.get("raw_output_audit"), f"run {sequence} execution raw audit"
    )
    execution_audit = artifact_identity_map(
        execution_audits,
        f"run {sequence} execution raw audit",
        {"role", "content", "retained", "source_audit"},
    )
    if any(
        require_dict(audit, f"run {sequence} execution raw row").get("retained")
        is not False
        or not isinstance(audit.get("source_audit"), str)
        or not audit["source_audit"]
        for audit in execution_audits
    ):
        raise AnalysisError(f"run {sequence}: execution raw-output audit differs")
    response_outputs = artifact_identity_map(
        response.get("outputs"),
        f"run {sequence} response outputs",
        {"role", "content"},
    )
    if (
        set(indexed_audit) != raw_roles
        or execution_audit != indexed_audit
        or set(response_outputs) != output_roles
        or response_outputs
        != {role: indexed_audit[role] for role in output_roles}
    ):
        raise AnalysisError(f"run {sequence}: raw-output identities are not cross-bound")
    process = require_dict(execution.get("process"), f"run {sequence} process")
    if (
        process.get("exit_code") != 0
        or process.get("success_banner_count") != 1
        or process.get("warning_tokens") != 0
    ):
        raise AnalysisError(f"run {sequence}: execution process is not successful")
    response_execution = require_dict(
        response.get("wepp_execution"), f"run {sequence} response WEPP execution"
    )
    response_adapter = require_dict(
        response_execution.get("extraction_adapter"),
        f"run {sequence} response extraction adapter",
    )
    require_exact_keys(
        response_adapter,
        {"adapter_id", "content_sha256"},
        f"run {sequence} response extraction adapter",
    )
    parser_record = require_dict(execution.get("parser"), f"run {sequence} parser audit")
    expected_adapter = {
        "adapter_id": EXTRACTION_ADAPTER_ID,
        "content_sha256": sha256_path(CAMPAIGN_RUNNER),
    }
    if (
        response_adapter != expected_adapter
        or parser_record.get("adapter_id") != response_adapter["adapter_id"]
        or parser_record.get("adapter_sha256") != response_adapter["content_sha256"]
    ):
        raise AnalysisError(f"run {sequence}: response/execution extractor identity differs")
    (
        element_overflow_count,
        element_effint_overflow_count,
        same_day_duplicate_rows,
        peakro_recovery_count,
    ) = validate_element_fixed_width_overflow(
        parser_record, execution_audits, horizon, sequence
    )

    available: dict[tuple[str, str], tuple[float, str]] = {}
    unavailable: set[str] = set()
    for value in response["responses"]:
        metric = value["metric_id"]
        if value["status"] == "unavailable":
            unavailable.add(metric)
            continue
        statistic = value["statistic"]
        item = (metric, statistic)
        if item in available:
            raise AnalysisError(f"run {sequence}: duplicate available response {item}")
        available[item] = (float(value["value"]), value["units"])
    return ResponseRecord(
        sequence,
        profile,
        station,
        horizon,
        replicate,
        expected_domain,
        available,
        frozenset(unavailable),
        same_day_duplicate_rows,
        element_overflow_count,
        element_effint_overflow_count,
        peakro_recovery_count,
    )


def validate_campaign_element_fixed_width_overflow_counts(
    index: dict[str, Any],
    records: Iterable[ResponseRecord],
) -> int:
    records = list(records)
    derived_overflow_counts = {
        "EffInt": sum(
            record.element_effint_fixed_width_overflow_count for record in records
        ),
        "Sm": sum(record.element_fixed_width_overflow_count for record in records),
    }
    campaign_execution = require_dict(index["execution"], "campaign execution")
    campaign_overflow_counts = require_dict(
        campaign_execution.get("element_fixed_width_overflow_counts"),
        "campaign element fixed-width overflow counts",
    )
    require_exact_keys(
        campaign_overflow_counts,
        {"EffInt", "Sm"},
        "campaign element fixed-width overflow counts",
    )
    for field, derived_count in derived_overflow_counts.items():
        recorded_count = campaign_overflow_counts[field]
        if (
            isinstance(recorded_count, bool)
            or not isinstance(recorded_count, int)
            or recorded_count < 0
            or recorded_count != derived_count
        ):
            raise AnalysisError(
                "campaign element fixed-width overflow aggregate differs from run audits"
            )
    return sum(derived_overflow_counts.values())


def validate_campaign_element_same_day_duplicate_rows(
    index: dict[str, Any], records: Iterable[ResponseRecord]
) -> int:
    derived = sum(record.element_same_day_duplicate_rows for record in records)
    campaign_execution = require_dict(index["execution"], "campaign execution")
    recorded = campaign_execution.get("element_same_day_duplicate_rows")
    if (
        isinstance(recorded, bool)
        or not isinstance(recorded, int)
        or recorded < 0
        or recorded != derived
    ):
        raise AnalysisError(
            "campaign same-day duplicate element rows differ from run audits"
        )
    return derived


def validate_campaign_element_peakro_recovery_counts(
    index: dict[str, Any], records: Iterable[ResponseRecord]
) -> int:
    derived = sum(record.element_peakro_recovery_count for record in records)
    campaign_execution = require_dict(index["execution"], "campaign execution")
    recorded_counts = require_dict(
        campaign_execution.get("element_response_recovery_counts"),
        "campaign element response recovery counts",
    )
    require_exact_keys(
        recorded_counts, {"PeakRO"}, "campaign element response recovery counts"
    )
    recorded = recorded_counts["PeakRO"]
    if (
        isinstance(recorded, bool)
        or not isinstance(recorded, int)
        or recorded < 0
        or recorded != derived
    ):
        raise AnalysisError("campaign PeakRO recovery aggregate differs from run audits")
    return derived


def load_campaign(
    index_path: Path,
    archive_dir: Path,
    validator: Draft202012Validator,
    semantic: Any,
) -> tuple[dict[str, Any], dict[tuple[str, str, int, int], ResponseRecord]]:
    if index_path.name != "wepp-response-campaign-v1.json":
        raise AnalysisError("campaign index filename differs")
    archive_dir = archive_dir.resolve(strict=True)
    if not archive_dir.is_dir() or archive_dir.is_symlink():
        raise AnalysisError("campaign archive directory is missing or a symlink")
    if index_path.resolve(strict=True).parent != archive_dir:
        raise AnalysisError("campaign index is outside the supplied archive directory")
    index = require_dict(strict_json(index_path), "WEPP campaign index")
    validate_index_shape(index)
    wepp = require_dict(index["wepp"], "campaign WEPP identity")
    expected_executable = require_artifact(
        wepp.get("executable"), "campaign WEPP executable"
    )
    rows = [require_dict(row, "campaign run") for row in require_list(index["runs"], "runs")]
    if len(rows) != EXPECTED_RUNS:
        raise AnalysisError(f"campaign contains {len(rows)} runs, expected {EXPECTED_RUNS}")
    for sequence, row in enumerate(rows):
        validate_run_row(row, sequence)

    archive_rows = [
        require_dict(row, "campaign archive")
        for row in require_list(index["archives"], "archives")
    ]
    if len(archive_rows) != len(PROFILES):
        raise AnalysisError("campaign archive count differs")
    rows_by_archive: dict[str, list[dict[str, Any]]] = {profile: [] for profile in PROFILES}
    for row in rows:
        rows_by_archive[row["profile_id"]].append(row)
    records: dict[tuple[str, str, int, int], ResponseRecord] = {}
    for expected_profile, archive_row in zip(PROFILES, archive_rows, strict=True):
        require_exact_keys(
            archive_row, {"profile_id", "format", "member_count", "artifact"},
            f"archive {expected_profile}",
        )
        if (
            archive_row["profile_id"] != expected_profile
            or archive_row["format"] != "tar+gzip-canonical-v1"
            or archive_row["member_count"] != EXPECTED_ARCHIVE_MEMBERS
        ):
            raise AnalysisError(f"archive declaration differs: {expected_profile}")
        artifact_record = require_dict(
            archive_row["artifact"], f"archive {expected_profile} artifact"
        )
        require_exact_keys(
            artifact_record, {"path", "sha256", "bytes"},
            f"archive {expected_profile} artifact",
        )
        expected_name = f"wepp-response-{expected_profile}-v1.tar.gz"
        if Path(artifact_record["path"]).name != expected_name:
            raise AnalysisError(f"archive filename differs: {expected_profile}")
        path = safe_repository_path(artifact_record["path"], "campaign archive")
        if path.parent != archive_dir:
            raise AnalysisError(f"archive path escapes supplied directory: {expected_profile}")
        archive_identity = require_artifact(
            {"sha256": artifact_record["sha256"], "bytes": artifact_record["bytes"]},
            f"archive {expected_profile}",
        )
        verify_artifact(path, archive_identity, f"archive {expected_profile}")
        with path.open("rb") as handle:
            if handle.read(10) != CANONICAL_GZIP_HEADER:
                raise AnalysisError(f"archive gzip header differs: {expected_profile}")
        expected_members: dict[str, tuple[dict[str, Any], str]] = {}
        for row in rows_by_archive[expected_profile]:
            for role in ("response", "execution"):
                member = row[role]["member"]
                if member in expected_members:
                    raise AnalysisError(f"duplicate archive member binding: {member}")
                expected_members[member] = (row, role)
        if len(expected_members) != EXPECTED_ARCHIVE_MEMBERS:
            raise AnalysisError(f"archive binding count differs: {expected_profile}")
        documents: dict[tuple[int, str], dict[str, Any]] = {}
        with tarfile.open(path, mode="r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            if names != sorted(expected_members) or set(names) != set(expected_members):
                raise AnalysisError(f"archive member set/order differs: {expected_profile}")
            for member in members:
                if (
                    not member.isfile()
                    or member.mode != 0o644
                    or member.mtime != 0
                    or member.uid != 0
                    or member.gid != 0
                    or member.uname != ""
                    or member.gname != ""
                    or member.pax_headers
                ):
                    raise AnalysisError(f"noncanonical archive metadata: {member.name}")
                handle = archive.extractfile(member)
                if handle is None:
                    raise AnalysisError(f"cannot read archive member: {member.name}")
                raw = handle.read()
                row, role = expected_members[member.name]
                binding = row[role]
                if len(raw) != binding["bytes"] or sha256_bytes(raw) != binding["sha256"]:
                    raise AnalysisError(f"archive member binding differs: {member.name}")
                document = require_dict(strict_json_bytes(raw, member.name), member.name)
                if role == "response":
                    validate_response(validator, semantic, document)
                    if require_artifact(
                        document["wepp_execution"]["executable"],
                        f"{member.name} WEPP executable",
                    ) != expected_executable:
                        raise AnalysisError(
                            f"response executable differs from campaign: {member.name}"
                        )
                documents[(row["sequence"], role)] = document
        for row in rows_by_archive[expected_profile]:
            response = documents[(row["sequence"], "response")]
            execution = documents[(row["sequence"], "execution")]
            record = response_record(row, response, execution)
            key = (record.profile_id, record.station_id, record.horizon, record.replicate)
            if key in records:
                raise AnalysisError(f"duplicate response matrix key: {key}")
            records[key] = record
    expected_keys = set(itertools.product(PROFILES, STATIONS, HORIZONS, range(8)))
    if set(records) != expected_keys:
        raise AnalysisError(
            f"response matrix differs: missing={len(expected_keys - set(records))}, "
            f"extra={len(set(records) - expected_keys)}"
        )
    validate_campaign_element_fixed_width_overflow_counts(index, records.values())
    validate_campaign_element_same_day_duplicate_rows(index, records.values())
    validate_campaign_element_peakro_recovery_counts(index, records.values())
    return index, records


def station_comparisons(
    records: dict[tuple[str, str, int, int], ResponseRecord]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        for horizon in HORIZONS:
            for station in STATIONS:
                domain = "cold_snow" if station in COLD_STATIONS else "general"
                metrics = GENERAL_METRICS + (COLD_METRICS if domain == "cold_snow" else ())
                for metric in metrics:
                    for statistic in STATISTICS:
                        differences: list[float] = []
                        ratios: list[float] = []
                        units: set[str] = set()
                        candidate_only = 0
                        baseline_only = 0
                        both_unavailable = 0
                        baseline_zero = 0
                        paired_values: list[dict[str, Any]] = []
                        for replicate in range(8):
                            candidate_row = records[(candidate, station, horizon, replicate)]
                            baseline_row = records[("faithful_off", station, horizon, replicate)]
                            item = (metric, statistic)
                            candidate_value = candidate_row.available.get(item)
                            baseline_value = baseline_row.available.get(item)
                            if candidate_value is None and baseline_value is None:
                                both_unavailable += 1
                                paired_values.append(
                                    {"replicate": replicate, "status": "both_unavailable"}
                                )
                                continue
                            if candidate_value is None:
                                baseline_only += 1
                                paired_values.append(
                                    {
                                        "replicate": replicate,
                                        "status": "baseline_only_available",
                                    }
                                )
                                continue
                            if baseline_value is None:
                                candidate_only += 1
                                paired_values.append(
                                    {
                                        "replicate": replicate,
                                        "status": "candidate_only_available",
                                    }
                                )
                                continue
                            if candidate_value[1] != baseline_value[1]:
                                raise AnalysisError(
                                    f"paired response units differ: {candidate}/{station}/{horizon}/{item}"
                                )
                            units.add(candidate_value[1])
                            candidate_number = candidate_value[0]
                            baseline_number = baseline_value[0]
                            differences.append(candidate_number - baseline_number)
                            pair_ratio = None
                            if baseline_number == 0.0:
                                baseline_zero += 1
                            else:
                                quotient = candidate_number / baseline_number
                                if not math.isfinite(quotient):
                                    raise AnalysisError("paired response ratio is nonfinite")
                                ratios.append(quotient)
                                pair_ratio = quotient
                            paired_values.append(
                                {
                                    "replicate": replicate,
                                    "status": "paired_available",
                                    "candidate": candidate_number,
                                    "faithful_off": baseline_number,
                                    "signed_difference": candidate_number - baseline_number,
                                    "ratio": pair_ratio,
                                }
                            )
                        paired = len(differences)
                        if paired == 0 and candidate_only == 0 and baseline_only == 0:
                            continue
                        if len(units) > 1:
                            raise AnalysisError("response units vary across replicates")
                        output.append(
                            {
                                "candidate_id": candidate,
                                "horizon_years": horizon,
                                "station_id": station,
                                "domain": domain,
                                "metric_id": metric,
                                "statistic": statistic,
                                "units": next(iter(units), None),
                                "availability": {
                                    "expected_replicate_pairs": 8,
                                    "paired_available": paired,
                                    "candidate_only_available": candidate_only,
                                    "baseline_only_available": baseline_only,
                                    "both_unavailable": both_unavailable,
                                    "baseline_zero_ratio_nulls": baseline_zero,
                                },
                                "replicate_pairs": paired_values,
                                "signed_difference": numeric_summary(differences),
                                "ratio": numeric_summary(ratios),
                            }
                        )
    return output


def aggregate_station_rows(
    station_rows: Sequence[dict[str, Any]], scope: str
) -> list[dict[str, Any]]:
    if scope not in {"domain", "corpus"}:
        raise AnalysisError(f"unknown comparison aggregation scope: {scope}")
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in station_rows:
        prefix: tuple[Any, ...] = (
            row["candidate_id"],
            row["horizon_years"],
            row["metric_id"],
            row["statistic"],
            row["units"],
        )
        key = (*prefix, row["domain"]) if scope == "domain" else prefix
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        rows = sorted(rows, key=lambda row: STATIONS.index(row["station_id"]))
        difference_values = [
            row["signed_difference"]["median"]
            for row in rows
            if row["signed_difference"]["median"] is not None
        ]
        ratio_values = [
            row["ratio"]["median"] for row in rows if row["ratio"]["median"] is not None
        ]
        candidate, horizon, metric, statistic, units, *tail = key
        result = {
            "candidate_id": candidate,
            "horizon_years": horizon,
            "metric_id": metric,
            "statistic": statistic,
            "units": units,
            "station_ids": [row["station_id"] for row in rows],
            "station_count": len(rows),
            "station_difference_available_count": len(difference_values),
            "station_ratio_available_count": len(ratio_values),
            "paired_available_total": sum(
                row["availability"]["paired_available"] for row in rows
            ),
            "baseline_zero_ratio_nulls_total": sum(
                row["availability"]["baseline_zero_ratio_nulls"] for row in rows
            ),
            "signed_difference_of_station_medians": numeric_summary(difference_values),
            "ratio_of_station_medians": numeric_summary(ratio_values),
        }
        if scope == "domain":
            result["domain"] = tail[0]
        output.append(result)
    candidate_order = {candidate: index for index, candidate in enumerate(CANDIDATES)}
    metric_order = {metric: index for index, metric in enumerate(METRICS)}
    statistic_order = {statistic: index for index, statistic in enumerate(STATISTICS)}
    domain_order = {"general": 0, "cold_snow": 1}
    output.sort(
        key=lambda row: (
            candidate_order[row["candidate_id"]],
            HORIZONS.index(row["horizon_years"]),
            metric_order[row["metric_id"]],
            statistic_order[row["statistic"]],
            domain_order.get(row.get("domain", "general"), 0),
        )
    )
    return output


def final_gate_table(climate: dict[str, Any], wepp_complete: bool) -> list[dict[str, Any]]:
    if (
        climate.get("a5b_climate_analysis_schema_version") != 1
        or climate.get("status") != "complete"
    ):
        raise AnalysisError("climate analysis is not complete revision 1")
    rows = require_list(climate.get("deterministic_gate_results"), "climate gate rows")
    expected = list(itertools.product(CANDIDATES, HORIZONS))
    if len(rows) != len(expected):
        raise AnalysisError("climate gate table row count differs")
    output = []
    for row, (candidate, horizon) in zip(rows, expected, strict=True):
        checked = require_dict(row, "climate gate row")
        if checked.get("candidate_id") != candidate or checked.get("horizon_years") != horizon:
            raise AnalysisError("climate gate table order differs")
        gates = require_list(checked.get("gates"), "climate gates")
        if len(gates) != 7 or [gate.get("gate_id") for gate in gates] != list(range(1, 8)):
            raise AnalysisError("climate gate IDs differ")
        climate_gates = copy.deepcopy(gates[:6])
        climate_pass = all(gate.get("passed") is True for gate in climate_gates)
        output.append(
            {
                "candidate_id": candidate,
                "horizon_years": horizon,
                "gates": [
                    *climate_gates,
                    {
                        "gate_id": 7,
                        "status": (
                            "complete_wepp_evidence"
                            if wepp_complete
                            else "incomplete_wepp_evidence"
                        ),
                        "passed": wepp_complete,
                        "rule": "true iff all 2,176 frozen WEPP response records validate",
                        "downstream_numeric_bound": None,
                    },
                ],
                "climate_gates_1_through_6_pass": climate_pass,
                "gate_7_complete_wepp_evidence_pass": wepp_complete,
                "all_seven_package_gates_pass": climate_pass and wepp_complete,
            }
        )
    return output


def validate_climate_campaign_binding(
    index: dict[str, Any], climate: dict[str, Any]
) -> dict[str, Any]:
    """Bind the climate gate input to this campaign's sole manifest transition."""

    candidate = require_dict(index.get("candidate"), "campaign candidate evidence")
    lifecycle = require_dict(candidate.get("lifecycle"), "campaign candidate lifecycle")
    post_manifest = require_artifact(
        lifecycle.get("post_manifest"), "campaign post-WEPP candidate manifest"
    )
    climate_inputs = require_dict(climate.get("inputs"), "climate analysis inputs")
    climate_manifest_sha256 = climate_inputs.get("candidate_manifest_sha256")
    if climate_manifest_sha256 != post_manifest.sha256:
        raise AnalysisError(
            "climate analysis does not bind this campaign's post-WEPP candidate manifest"
        )
    completeness = require_dict(
        climate.get("evidence_completeness"), "climate evidence completeness"
    )
    if completeness.get("climate_evidence_complete") is not True:
        raise AnalysisError("climate analysis does not report complete climate evidence")
    return {
        "candidate_manifest": {
            "lifecycle_state": "post_wepp_cli_removal",
            "sha256": post_manifest.sha256,
            "bytes": post_manifest.bytes,
        },
        "climate_evidence_complete": True,
    }


def analyze_values(
    index: dict[str, Any],
    records: dict[tuple[str, str, int, int], ResponseRecord],
    climate: dict[str, Any],
    index_sha256: str,
    climate_sha256: str,
    frozen_tooling: dict[str, Any],
) -> dict[str, Any]:
    climate_campaign_binding = validate_climate_campaign_binding(index, climate)
    station = station_comparisons(records)
    domain = aggregate_station_rows(station, "domain")
    corpus = aggregate_station_rows(station, "corpus")
    gate_table = final_gate_table(climate, True)
    archive_inputs = [
        {
            "profile_id": row["profile_id"],
            "path": row["artifact"]["path"],
            "sha256": row["artifact"]["sha256"],
            "bytes": row["artifact"]["bytes"],
            "member_count": row["member_count"],
        }
        for row in index["archives"]
    ]
    return {
        "a5b_wepp_analysis_schema_version": 1,
        "status": "complete",
        "decision_scope": "downstream_response_no_numeric_bound_no_profile_promotion",
        "inputs": {
            "campaign_index_sha256": index_sha256,
            "climate_analysis_sha256": climate_sha256,
            **climate_campaign_binding,
            **frozen_tooling,
            "response_schema_sha256": sha256_path(RESPONSE_SCHEMA),
            "response_protocol_sha256": sha256_path(RESPONSE_PROTOCOL),
            "response_semantic_verifier_sha256": sha256_path(RESPONSE_VERIFIER),
            "archives": archive_inputs,
        },
        "matrix": {
            "profiles": list(PROFILES),
            "candidate_profiles": list(CANDIDATES),
            "stations": list(STATIONS),
            "horizons_years": list(HORIZONS),
            "replicates": [row[0] for row in REPLICATES],
            "validated_response_records": len(records),
            "validated_execution_records": len(records),
            "expected_records": EXPECTED_RUNS,
        },
        "aggregation_contract": {
            "contract_id": AGGREGATION_CONTRACT_ID,
            "pair_key": ["station_id", "horizon_years", "replicate"],
            "signed_difference": "candidate - faithful_off",
            "ratio": "candidate / faithful_off; null when faithful_off is zero",
            "station": (
                "conventional median and nearest-rank p05/p95/min/max across exact "
                "replicate pairs"
            ),
            "domain": (
                "same summary across station medians within general or cold_snow; "
                "equal station weight"
            ),
            "corpus": "same summary across applicable station medians; equal station weight",
            "unavailable": "counted explicitly and never converted to numeric zero",
            "downstream_numeric_pass_bound": None,
        },
        "response_comparisons": {
            "station": station,
            "domain": domain,
            "corpus": corpus,
        },
        "gate_table": gate_table,
        "evidence_completeness": {
            "complete_wepp_evidence": True,
            "validated_response_records": len(records),
            "validated_execution_records": len(records),
            "campaign_failures": index["execution"]["failures"],
            "element_same_day_duplicate_rows": index["execution"][
                "element_same_day_duplicate_rows"
            ],
            "element_fixed_width_overflow_counts": copy.deepcopy(
                index["execution"]["element_fixed_width_overflow_counts"]
            ),
            "element_response_recovery_counts": copy.deepcopy(
                index["execution"]["element_response_recovery_counts"]
            ),
            "gate_7_passed": True,
        },
    }


def atomic_write(path: Path, raw: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise AnalysisError(f"refusing to overwrite downstream analysis: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    if temporary.exists() or temporary.is_symlink():
        raise AnalysisError(f"downstream analysis temporary exists: {temporary}")
    try:
        with temporary.open("wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def execute(index_path: Path, archive_dir: Path, climate_path: Path) -> None:
    if OUTPUT.exists() or OUTPUT.is_symlink():
        raise AnalysisError(f"refusing to overwrite downstream analysis: {OUTPUT}")
    index_preview = require_dict(strict_json(index_path), "WEPP campaign index")
    frozen_tooling = verify_frozen_tooling(index_preview, climate_path)
    validator, semantic = load_response_validator()
    index, records = load_campaign(index_path, archive_dir, validator, semantic)
    if index != index_preview:
        raise AnalysisError("campaign index changed during validation")
    climate_raw = climate_path.read_bytes()
    climate = require_dict(strict_json_bytes(climate_raw, str(climate_path)), "climate analysis")
    climate_inputs = require_dict(climate.get("inputs"), "climate analysis inputs")
    if (
        climate_inputs.get("pre_candidate_freeze_sha256")
        != frozen_tooling["pre_candidate_freeze_sha256"]
        or climate_inputs.get("analyzer_sha256") != sha256_path(CLIMATE_ANALYZER)
    ):
        raise AnalysisError("climate analysis does not bind the frozen analysis tooling")
    result = analyze_values(
        index,
        records,
        climate,
        sha256_path(index_path),
        sha256_bytes(climate_raw),
        frozen_tooling,
    )
    # Recheck mutable inputs immediately before publication.
    if sha256_path(index_path) != result["inputs"]["campaign_index_sha256"]:
        raise AnalysisError("campaign index changed during analysis")
    if sha256_path(climate_path) != result["inputs"]["climate_analysis_sha256"]:
        raise AnalysisError("climate analysis changed during analysis")
    for archive in result["inputs"]["archives"]:
        path = safe_repository_path(archive["path"], "campaign archive recheck")
        verify_artifact(
            path,
            Artifact(archive["sha256"], archive["bytes"]),
            f"campaign archive recheck {archive['profile_id']}",
        )
    atomic_write(OUTPUT, canonical_bytes(result))
    print(OUTPUT)


def deterministic_tar_gzip(members: list[tuple[str, bytes]], destination: Path) -> Artifact:
    if [name for name, _ in members] != sorted(name for name, _ in members):
        raise AssertionError("self-test archive members are not sorted")
    with destination.open("wb") as raw_handle:
        with gzip.GzipFile(
            filename="", mode="wb", compresslevel=9, mtime=0, fileobj=raw_handle
        ) as compressed:
            with tarfile.open(
                fileobj=compressed, mode="w|", format=tarfile.USTAR_FORMAT
            ) as archive:
                for name, raw in members:
                    info = tarfile.TarInfo(name)
                    info.size = len(raw)
                    info.mode = 0o644
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    archive.addfile(info, io.BytesIO(raw))
    return Artifact(sha256_path(destination), destination.stat().st_size)


def synthetic_raw_audit(domain: str) -> list[dict[str, Any]]:
    roles = [
        ("element", "0" * 64, 1),
        ("soil_loss", "4" * 64, 1),
    ]
    if domain == "cold_snow":
        roles.append(("hourly_winter", "5" * 64, 1))
    roles.extend((("stdout", "1" * 64, 1), ("stderr", "2" * 64, 0)))
    return [
        {
            "role": role,
            "content": {"sha256": digest, "bytes": size},
            "retained": False,
        }
        for role, digest, size in roles
    ]


def synthetic_response(
    semantic: Any,
    profile: str,
    station: str,
    horizon: int,
    replicate: int,
    candidate_index: int,
) -> dict[str, Any]:
    domain = "cold_snow" if station in COLD_STATIONS else "general"
    value = semantic.record(domain)
    value["record_id"] = f"a5b-wepp-{station}-{profile}-{horizon}yr-rep{replicate}"
    value["climate"]["station_id"] = station
    value["climate"]["generation_profile"] = GENERATION_PROFILES[profile]
    value["climate"]["horizon_years"] = horizon
    value["climate"]["replicate"] = {
        "key": f"replicate-{replicate}",
        "legacy_burn_offset": REPLICATES[replicate][1],
        "extension_seed_u64_hex": (
            None if profile == "faithful_off" else REPLICATES[replicate][2]
        ),
    }
    value["wepp_execution"]["extraction_adapter"] = {
        "adapter_id": EXTRACTION_ADAPTER_ID,
        "content_sha256": sha256_path(CAMPAIGN_RUNNER),
    }
    raw_audit = synthetic_raw_audit(domain)
    value["outputs"] = [
        {"role": row["role"], "content": copy.deepcopy(row["content"])}
        for row in raw_audit
        if row["role"] in {"element", "soil_loss", "hourly_winter"}
    ]
    semantic.replace_family_with_available(value, "annual_runoff")
    if domain == "cold_snow":
        semantic.replace_family_with_available(value, "annual_snowmelt")
    for response in value["responses"]:
        if response["status"] != "available":
            continue
        response["n_years"] = horizon
        statistic_index = STATISTICS.index(response["statistic"])
        response["value"] = float(replicate + statistic_index + candidate_index)
    return value


def synthetic_climate_analysis(candidate_manifest_sha256: str) -> dict[str, Any]:
    rows = []
    for candidate, horizon in itertools.product(CANDIDATES, HORIZONS):
        gates = [
            {
                "gate_id": gate_id,
                "status": "self_test",
                "passed": gate_id % 2 == 1,
                "sentinel": f"{candidate}-{horizon}-{gate_id}",
            }
            for gate_id in range(1, 7)
        ]
        gates.append({"gate_id": 7, "status": "pending_downstream_wepp", "passed": False})
        rows.append(
            {
                "candidate_id": candidate,
                "horizon_years": horizon,
                "gates": gates,
                "climate_gates_1_through_6_pass": False,
                "all_seven_package_gates_pass": False,
            }
        )
    return {
        "a5b_climate_analysis_schema_version": 1,
        "status": "complete",
        "inputs": {"candidate_manifest_sha256": candidate_manifest_sha256},
        "deterministic_gate_results": rows,
        "evidence_completeness": {"climate_evidence_complete": True},
    }


def synthetic_parser_audit(
    source_element_sha256: str,
    source_event_sha256: str,
    overflow_count: int,
    duplicate_rows: int = 0,
    peak_recovery_count: int = 0,
    effint_overflow_count: int = 0,
) -> dict[str, Any]:
    observed: dict[str, Any] = {}
    if overflow_count:
        observed = {
            "count": overflow_count,
            "first_mapped_key": {
                "simulation_year": 1,
                "ordinal_day": 1,
                "ofe": 1,
            },
        }
    effint_observed: dict[str, Any] = {}
    if effint_overflow_count:
        effint_observed = {
            "count": effint_overflow_count,
            "first_mapped_key": {
                "simulation_year": 1,
                "ordinal_day": 1,
                "ofe": 1,
            },
        }
    return {
        "adapter_id": EXTRACTION_ADAPTER_ID,
        "adapter_sha256": sha256_path(CAMPAIGN_RUNNER),
        "element_record_rows": 100 + duplicate_rows,
        "element_record_keys": 100,
        "hourly_record_dates": 0,
        "rain_on_snow_eligible_dates": 0,
        "rain_on_snow_join": "synthetic self-test join",
        "rain_on_snow_units": "element QRain millimetres",
        "element_same_day_aggregation": {
            "policy_id": ELEMENT_SAME_DAY_POLICY_ID,
            "source_element_sha256": source_element_sha256,
            "key": ["simulation_year", "ordinal_day", "ofe"],
            "aggregation": {
                "runoff": "sum",
                "peak_runoff": "max",
                "sediment_leave": "sum",
                "qrain": "sum_before_daily_rain_on_snow_join",
            },
            "total_element_rows": 100 + duplicate_rows,
            "unique_date_ofe_keys": 100,
            "observed": (
                {
                    "duplicate_rows": duplicate_rows,
                    "first_mapped_key": {
                        "simulation_year": 1,
                        "ordinal_day": 1,
                        "ofe": 1,
                    },
                }
                if duplicate_rows
                else {}
            ),
        },
        "element_fixed_width_overflow": {
            "policy_id": ELEMENT_OVERFLOW_POLICY_ID,
            "source_element_sha256": source_element_sha256,
            "allowed": copy.deepcopy(ELEMENT_OVERFLOW_ALLOWED),
            "total_element_rows": 100 + duplicate_rows,
            "observed": observed,
        },
        "element_effint_fixed_width_overflow": {
            "policy_id": ELEMENT_EFFINT_OVERFLOW_POLICY_ID,
            "source_element_sha256": source_element_sha256,
            "allowed": copy.deepcopy(ELEMENT_EFFINT_OVERFLOW_ALLOWED),
            "total_element_rows": 100 + duplicate_rows,
            "observed": effint_observed,
        },
        "element_peakro_recovery": {
            "policy_id": ELEMENT_PEAK_RECOVERY_POLICY_ID,
            "source_element_sha256": source_element_sha256,
            "source_event_hydrology_sha256": source_event_sha256,
            "element_overflow": copy.deepcopy(ELEMENT_PEAK_OVERFLOW),
            "recovery": copy.deepcopy(ELEMENT_PEAK_RECOVERY),
            "event_hydrology_records": 50,
            "event_hydrology_unique_keys": 50,
            "event_hydrology_duplicate_rows": 0,
            "crosschecked_unique_keys": 50,
            "observed": (
                {
                    "count": peak_recovery_count,
                    "first_mapped_key": {
                        "simulation_year": 1,
                        "ordinal_day": 1,
                        "ofe": 1,
                    },
                }
                if peak_recovery_count
                else {}
            ),
        },
    }


def synthetic_campaign(directory: Path, semantic: Any) -> tuple[Path, dict[str, Any]]:
    contracts = {
        name: {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_path(path)}
        for name, path in {
            "campaign": CAMPAIGN_CONTRACT,
            "response_schema": RESPONSE_SCHEMA,
            "response_protocol": RESPONSE_PROTOCOL,
            "response_verifier": RESPONSE_VERIFIER,
            "runner": CAMPAIGN_RUNNER,
        }.items()
    }
    runs: list[dict[str, Any]] = []
    archives: list[dict[str, Any]] = []
    sequence = 0
    for profile in PROFILES:
        members: list[tuple[str, bytes]] = []
        profile_rows: list[dict[str, Any]] = []
        candidate_index = 0 if profile == "faithful_off" else CANDIDATES.index(profile) + 1
        for station, horizon, (replicate, _burn, _seed) in itertools.product(
            STATIONS, HORIZONS, REPLICATES
        ):
            response = synthetic_response(
                semantic, profile, station, horizon, replicate, candidate_index
            )
            record_id = response["record_id"]
            raw_audit = synthetic_raw_audit(response["domain"])
            execution = {
                "wepp_execution_record_version": 1,
                "record_id": record_id,
                "sequence": sequence,
                "process": {
                    "exit_code": 0,
                    "success_banner_count": 1,
                    "warning_tokens": 0,
                },
                "raw_output_audit": [
                    {**row, "source_audit": "synthetic self-test raw bytes not retained"}
                    for row in raw_audit
                ],
                "parser": synthetic_parser_audit(
                    raw_audit[0]["content"]["sha256"],
                    raw_audit[1]["content"]["sha256"],
                    11 if sequence == 2 else 0,
                    1 if sequence == 3 else 0,
                    1 if sequence == 4 else 0,
                    7 if sequence == 5 else 0,
                ),
                "climate_lineage": copy.deepcopy(response["climate"]),
            }
            response_raw = canonical_bytes(response)
            execution_raw = canonical_bytes(execution)
            response_member = f"runs/{record_id}/response.json"
            execution_member = f"runs/{record_id}/execution.json"
            members.extend(
                ((execution_member, execution_raw), (response_member, response_raw))
            )
            row = {
                "sequence": sequence,
                "record_id": record_id,
                "profile_id": profile,
                "archive": f"wepp-response-{profile}-v1.tar.gz",
                "response": {
                    "member": response_member,
                    "sha256": sha256_bytes(response_raw),
                    "bytes": len(response_raw),
                },
                "execution": {
                    "member": execution_member,
                    "sha256": sha256_bytes(execution_raw),
                    "bytes": len(execution_raw),
                },
                "raw_output_audit": raw_audit,
            }
            profile_rows.append(row)
            runs.append(row)
            sequence += 1
        members.sort(key=lambda item: item[0])
        archive_path = directory / f"wepp-response-{profile}-v1.tar.gz"
        artifact = deterministic_tar_gzip(members, archive_path)
        archives.append(
            {
                "profile_id": profile,
                "format": "tar+gzip-canonical-v1",
                "member_count": len(members),
                "artifact": {
                    "path": archive_path.relative_to(ROOT).as_posix(),
                    "sha256": artifact.sha256,
                    "bytes": artifact.bytes,
                },
            }
        )
        if len(profile_rows) != 272:
            raise AssertionError("self-test profile matrix count differs")
    index = {
        "wepp_response_campaign_version": 1,
        "status": "sealed",
        "contracts": contracts,
        "matrix": {
            "stations": list(STATIONS),
            "horizons_years": list(HORIZONS),
            "replicates": [
                {"replicate": replicate, "legacy_burn": burn, "extension_seed": seed}
                for replicate, burn, seed in REPLICATES
            ],
            "profiles": list(PROFILES),
            "expected_runs": EXPECTED_RUNS,
            "actual_runs": EXPECTED_RUNS,
            "projection_sha256": MATRIX_PROJECTION_SHA256,
        },
        "wepp": {
            "executable": {"sha256": "0" * 64, "bytes": 1},
            "extraction_adapter_id": EXTRACTION_ADAPTER_ID,
        },
        "baseline": {},
        "candidate": {
            "lifecycle": {
                "post_manifest": {"sha256": "a" * 64, "bytes": 12_345}
            }
        },
        "archives": archives,
        "runs": runs,
        "execution": {
            "workers": 4,
            "failures": [],
            "candidate_cli_bytes_removed_after_wepp": True,
            "baseline_regenerations_removed": True,
            "raw_wepp_outputs_removed": True,
            "raw_wepp_outputs_redistributed": False,
            "element_same_day_duplicate_rows": 1,
            "element_fixed_width_overflow_counts": {"EffInt": 7, "Sm": 11},
            "element_response_recovery_counts": {"PeakRO": 1},
        },
    }
    index_path = directory / "wepp-response-campaign-v1.json"
    index_path.write_bytes(canonical_bytes(index))
    return index_path, index


def self_test() -> dict[str, Any]:
    validator, semantic = load_response_validator()
    target = ROOT / "target"
    target.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a5b-wepp-analysis-selftest-", dir=target) as raw:
        directory = Path(raw)
        index_path, fixture = synthetic_campaign(directory, semantic)
        index, records = load_campaign(index_path, directory, validator, semantic)
        if len(records) != EXPECTED_RUNS:
            raise AssertionError("self-test did not validate 2,176 records")
        overflow_record = records[("faithful_off", "ak505769", 30, 2)]
        if (
            overflow_record.element_fixed_width_overflow_count != 11
            or index["execution"]["element_fixed_width_overflow_counts"]
            != {"EffInt": 7, "Sm": 11}
        ):
            raise AssertionError("element fixed-width overflow audit was not retained")
        effint_record = records[("faithful_off", "ak505769", 30, 5)]
        if effint_record.element_effint_fixed_width_overflow_count != 7:
            raise AssertionError("EffInt fixed-width overflow audit was not retained")
        duplicate_record = records[("faithful_off", "ak505769", 30, 3)]
        if (
            duplicate_record.element_same_day_duplicate_rows != 1
            or index["execution"]["element_same_day_duplicate_rows"] != 1
        ):
            raise AssertionError("element same-day aggregation audit was not retained")
        peak_record = records[("faithful_off", "ak505769", 30, 4)]
        if (
            peak_record.element_peakro_recovery_count != 1
            or index["execution"]["element_response_recovery_counts"]
            != {"PeakRO": 1}
        ):
            raise AssertionError("element PeakRO recovery audit was not retained")

        element_audit = [
            {
                "role": "element",
                "content": {"sha256": "0" * 64, "bytes": 1},
                "retained": False,
                "source_audit": "synthetic self-test raw bytes not retained",
            },
            {
                "role": "soil_loss",
                "content": {"sha256": "4" * 64, "bytes": 1},
                "retained": False,
                "source_audit": "synthetic self-test raw bytes not retained",
            },
        ]
        valid_parser = synthetic_parser_audit("0" * 64, "4" * 64, 11, 1, 1)

        def must_reject_overflow(parser_value: dict[str, Any], label: str) -> None:
            try:
                validate_element_fixed_width_overflow(
                    parser_value, element_audit, 30, 0
                )
            except AnalysisError:
                return
            raise AssertionError(f"{label} was accepted")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_fixed_width_overflow"]["allowed"]["field"] = "Runoff"
        must_reject_overflow(mutated_parser, "response-bearing overflow allowance")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_fixed_width_overflow"]["unexpected"] = True
        must_reject_overflow(mutated_parser, "open fixed-width overflow audit")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_fixed_width_overflow"]["allowed"]["token"] = "******"
        must_reject_overflow(mutated_parser, "different fixed-width overflow token")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_fixed_width_overflow"]["source_element_sha256"] = "f" * 64
        must_reject_overflow(mutated_parser, "mismatched overflow source hash")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_fixed_width_overflow"]["total_element_rows"] = 99
        must_reject_overflow(mutated_parser, "inconsistent element row total")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_fixed_width_overflow"]["observed"]["count"] = 102
        must_reject_overflow(mutated_parser, "overflow count above element rows")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_fixed_width_overflow"]["observed"][
            "first_mapped_key"
        ]["simulation_year"] = 0
        must_reject_overflow(mutated_parser, "invalid first mapped overflow key")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_effint_fixed_width_overflow"]["allowed"]["field"] = (
            "Runoff"
        )
        must_reject_overflow(mutated_parser, "response-bearing EffInt allowance")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_effint_fixed_width_overflow"]["policy_id"] = (
            "contradictory_effint_policy"
        )
        must_reject_overflow(mutated_parser, "EffInt overflow policy mutation")

        zero_event_parser = synthetic_parser_audit("0" * 64, "4" * 64, 0)
        zero_event_peak = zero_event_parser["element_peakro_recovery"]
        zero_event_peak["event_hydrology_records"] = 0
        zero_event_peak["event_hydrology_unique_keys"] = 0
        zero_event_peak["event_hydrology_duplicate_rows"] = 0
        zero_event_peak["crosschecked_unique_keys"] = 0
        zero_event_peak["observed"] = {}
        validate_element_fixed_width_overflow(
            zero_event_parser, element_audit, 30, 0
        )

        try:
            strict_json_bytes(
                b'{"simulation_year":1,"ordinal_day":1,"ofe":1,"ofe":1}',
                "duplicate first mapped overflow key",
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("duplicate first mapped overflow key was accepted")

        for field, replacement in (
            ("policy_id", "contradictory_same_day_policy"),
            ("source_element_sha256", "f" * 64),
            ("key", ["simulation_year", "ofe"]),
            (
                "aggregation",
                {
                    "runoff": "max",
                    "peak_runoff": "max",
                    "sediment_leave": "sum",
                    "qrain": "sum_before_daily_rain_on_snow_join",
                },
            ),
            ("total_element_rows", 100),
            ("unique_date_ofe_keys", 99),
        ):
            mutated_parser = copy.deepcopy(valid_parser)
            mutated_parser["element_same_day_aggregation"][field] = replacement
            must_reject_overflow(mutated_parser, f"same-day aggregation {field} mutation")

        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_same_day_aggregation"]["observed"][
            "duplicate_rows"
        ] = 2
        must_reject_overflow(mutated_parser, "same-day duplicate count mutation")

        for field, replacement in (
            ("policy_id", "contradictory_peak_recovery_policy"),
            ("source_element_sha256", "f" * 64),
            ("source_event_hydrology_sha256", "e" * 64),
            ("event_hydrology_records", 49),
            ("event_hydrology_unique_keys", 49),
            ("event_hydrology_duplicate_rows", 1),
            ("crosschecked_unique_keys", 49),
        ):
            mutated_parser = copy.deepcopy(valid_parser)
            mutated_parser["element_peakro_recovery"][field] = replacement
            must_reject_overflow(mutated_parser, f"PeakRO recovery {field} mutation")
        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_peakro_recovery"]["element_overflow"]["field"] = (
            "Runoff"
        )
        must_reject_overflow(mutated_parser, "PeakRO recovery overflow-field mutation")
        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_peakro_recovery"]["recovery"]["fortran_format"] = (
            "F7.3"
        )
        must_reject_overflow(mutated_parser, "PeakRO recovery companion-format mutation")
        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_peakro_recovery"]["recovery"]["preamble"] = (
            "unbound_preamble"
        )
        must_reject_overflow(mutated_parser, "PeakRO recovery preamble mutation")
        mutated_parser = copy.deepcopy(valid_parser)
        mutated_parser["element_peakro_recovery"]["observed"]["count"] = 51
        must_reject_overflow(mutated_parser, "PeakRO recovery count mutation")

        mutated_parser = copy.deepcopy(valid_parser)
        peak_mutation = mutated_parser["element_peakro_recovery"]
        peak_mutation["event_hydrology_records"] = 102
        peak_mutation["event_hydrology_unique_keys"] = 102
        peak_mutation["event_hydrology_duplicate_rows"] = 0
        peak_mutation["crosschecked_unique_keys"] = 102
        peak_mutation["observed"]["count"] = 102
        must_reject_overflow(
            mutated_parser, "PeakRO recovery count above element row/key closure"
        )

        mutated_index = copy.deepcopy(index)
        mutated_index["execution"]["element_fixed_width_overflow_counts"]["Sm"] = 12
        try:
            validate_campaign_element_fixed_width_overflow_counts(
                mutated_index, records.values()
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("inconsistent campaign overflow aggregate was accepted")

        mutated_index = copy.deepcopy(index)
        mutated_index["execution"]["element_fixed_width_overflow_counts"][
            "EffInt"
        ] = 8
        try:
            validate_campaign_element_fixed_width_overflow_counts(
                mutated_index, records.values()
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("inconsistent campaign EffInt aggregate was accepted")

        mutated_index = copy.deepcopy(index)
        mutated_index["execution"]["element_fixed_width_overflow_counts"]["Runoff"] = 0
        try:
            validate_campaign_element_fixed_width_overflow_counts(
                mutated_index, records.values()
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("open campaign overflow aggregate was accepted")

        mutated_index = copy.deepcopy(index)
        mutated_index["execution"]["element_same_day_duplicate_rows"] = 2
        try:
            validate_campaign_element_same_day_duplicate_rows(
                mutated_index, records.values()
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("inconsistent same-day campaign aggregate was accepted")

        mutated_index = copy.deepcopy(index)
        mutated_index["execution"]["element_response_recovery_counts"]["PeakRO"] = 2
        try:
            validate_campaign_element_peakro_recovery_counts(
                mutated_index, records.values()
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("inconsistent PeakRO recovery aggregate was accepted")

        mutated_index = copy.deepcopy(index)
        mutated_index["execution"]["element_response_recovery_counts"]["Runoff"] = 0
        try:
            validate_campaign_element_peakro_recovery_counts(
                mutated_index, records.values()
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("open PeakRO recovery aggregate was accepted")

        mutated_index = copy.deepcopy(index)
        mutated_index["wepp"]["extraction_adapter_id"] = "contradictory_extractor_v1"
        try:
            validate_index_shape(mutated_index)
        except AnalysisError:
            pass
        else:
            raise AssertionError("contradictory campaign extractor was accepted")

        response = synthetic_response(
            semantic, "faithful_off", "ak505769", 30, 0, 0
        )
        record_id = response["record_id"]
        indexed_raw_audit = synthetic_raw_audit(response["domain"])
        execution = {
            "wepp_execution_record_version": 1,
            "record_id": record_id,
            "sequence": 0,
            "process": {
                "exit_code": 0,
                "success_banner_count": 1,
                "warning_tokens": 0,
            },
            "raw_output_audit": [
                {**row, "source_audit": "synthetic extractor-binding mutation"}
                for row in indexed_raw_audit
            ],
            "parser": synthetic_parser_audit("0" * 64, "4" * 64, 0),
            "climate_lineage": copy.deepcopy(response["climate"]),
        }
        run_row = {
            "sequence": 0,
            "record_id": record_id,
            "profile_id": "faithful_off",
            "raw_output_audit": indexed_raw_audit,
        }
        response_record(run_row, response, execution)
        for surface in ("index", "response", "execution"):
            mutated_row = copy.deepcopy(run_row)
            mutated_response = copy.deepcopy(response)
            mutated_execution = copy.deepcopy(execution)
            if surface == "index":
                next(
                    row
                    for row in mutated_row["raw_output_audit"]
                    if row["role"] == "soil_loss"
                )["content"]["sha256"] = "f" * 64
            elif surface == "response":
                next(
                    row
                    for row in mutated_response["outputs"]
                    if row["role"] == "soil_loss"
                )["content"]["sha256"] = "f" * 64
            else:
                next(
                    row
                    for row in mutated_execution["raw_output_audit"]
                    if row["role"] == "soil_loss"
                )["content"]["sha256"] = "f" * 64
            try:
                response_record(mutated_row, mutated_response, mutated_execution)
            except AnalysisError:
                pass
            else:
                raise AssertionError(
                    f"contradictory {surface} raw-output identity was accepted"
                )

        changed_domain_row = copy.deepcopy(run_row)
        changed_domain_response = copy.deepcopy(response)
        changed_domain_execution = copy.deepcopy(execution)
        changed_domain_response["domain"] = "general"
        changed_domain_response["outputs"] = [
            row
            for row in changed_domain_response["outputs"]
            if row["role"] != "hourly_winter"
        ]
        changed_domain_row["raw_output_audit"] = [
            row
            for row in changed_domain_row["raw_output_audit"]
            if row["role"] != "hourly_winter"
        ]
        changed_domain_execution["raw_output_audit"] = [
            row
            for row in changed_domain_execution["raw_output_audit"]
            if row["role"] != "hourly_winter"
        ]
        try:
            response_record(
                changed_domain_row, changed_domain_response, changed_domain_execution
            )
        except AnalysisError:
            pass
        else:
            raise AssertionError("cold response was accepted as general without winter output")
        for field, replacement in (
            ("adapter_id", "contradictory_extractor_v1"),
            ("content_sha256", "f" * 64),
        ):
            mutated_response = copy.deepcopy(response)
            mutated_response["wepp_execution"]["extraction_adapter"][field] = replacement
            try:
                response_record(run_row, mutated_response, execution)
            except AnalysisError:
                pass
            else:
                raise AssertionError(
                    f"contradictory response extractor {field} was accepted"
                )

        climate = synthetic_climate_analysis(
            fixture["candidate"]["lifecycle"]["post_manifest"]["sha256"]
        )
        binding = validate_climate_campaign_binding(fixture, climate)
        if binding["candidate_manifest"]["bytes"] != 12_345:
            raise AssertionError("post-WEPP candidate-manifest binding was not retained")
        mutated_climate = copy.deepcopy(climate)
        mutated_climate["inputs"]["candidate_manifest_sha256"] = "b" * 64
        try:
            validate_climate_campaign_binding(fixture, mutated_climate)
        except AnalysisError:
            pass
        else:
            raise AssertionError("mismatched climate/campaign manifest binding was accepted")
        mutated_climate = copy.deepcopy(climate)
        mutated_climate["evidence_completeness"]["climate_evidence_complete"] = False
        try:
            validate_climate_campaign_binding(fixture, mutated_climate)
        except AnalysisError:
            pass
        else:
            raise AssertionError("incomplete climate evidence was accepted")
        result = analyze_values(
            index,
            records,
            climate,
            sha256_path(index_path),
            sha256_bytes(canonical_bytes(climate)),
            {
                "pre_candidate_freeze_sha256": "f" * 64,
                "analyzer_sha256": sha256_path(ANALYZER_SOURCE),
            },
        )
        station = next(
            row
            for row in result["response_comparisons"]["station"]
            if row["candidate_id"] == "rank_one_monthly_sd"
            and row["horizon_years"] == 30
            and row["station_id"] == "al015478"
            and row["metric_id"] == "annual_runoff"
            and row["statistic"] == "mean"
        )
        if (
            station["signed_difference"]["median"] != 1.0
            or station["ratio"]["median"] != 1.25
            or station["availability"]["baseline_zero_ratio_nulls"] != 1
        ):
            raise AssertionError("paired difference/zero-baseline ratio aggregation differs")
        climate_first_six = climate["deterministic_gate_results"][0]["gates"][:6]
        final_first_six = result["gate_table"][0]["gates"][:6]
        if final_first_six != climate_first_six or result["gate_table"][0]["gates"][6][
            "passed"
        ] is not True:
            raise AssertionError("climate gates changed or Gate 7 did not close")

        mutated = copy.deepcopy(fixture)
        mutated["runs"][0]["response"]["sha256"] = "f" * 64
        original_index_raw = index_path.read_bytes()
        index_path.write_bytes(canonical_bytes(mutated))
        try:
            load_campaign(index_path, directory, validator, semantic)
        except AnalysisError:
            pass
        else:
            raise AssertionError("mutated response binding was accepted")
        finally:
            index_path.write_bytes(original_index_raw)

        semantic_mutation = synthetic_response(
            semantic, "faithful_off", "al015478", 30, 0, 0
        )
        available = next(
            row for row in semantic_mutation["responses"] if row["status"] == "available"
        )
        available["value"] = -1.0
        try:
            validate_response(validator, semantic, semantic_mutation)
        except AnalysisError:
            pass
        else:
            raise AssertionError("semantic response mutation was accepted")

        projection = {
            "records": len(records),
            "station_rows": len(result["response_comparisons"]["station"]),
            "domain_rows": len(result["response_comparisons"]["domain"]),
            "corpus_rows": len(result["response_comparisons"]["corpus"]),
            "gate_rows": len(result["gate_table"]),
            "sentinel_station": station,
            "first_gate_row": result["gate_table"][0],
        }
        projection_sha256 = sha256_bytes(compact_bytes(projection))
        if projection_sha256 != SELF_TEST_PROJECTION_SHA256:
            raise AssertionError(
                "self-test projection differs: "
                f"{projection_sha256} != {SELF_TEST_PROJECTION_SHA256}"
            )
    return {
        "status": "pass",
        "validated_response_records": EXPECTED_RUNS,
        "validated_execution_records": EXPECTED_RUNS,
        "aggregation_contract": AGGREGATION_CONTRACT_ID,
        "projection_sha256": projection_sha256,
        "checks": [
            "strict_complete_matrix_and_archive_bindings",
            "response_schema_and_semantic_validation",
            "paired_difference_and_zero_baseline_ratio",
            "equal_station_domain_and_corpus_hierarchy",
            "climate_gates_1_through_6_unchanged",
            "post_wepp_candidate_manifest_climate_binding",
            "incomplete_climate_evidence_mutation",
            "gate_7_complete_wepp_evidence",
            "response_binding_mutation",
            "semantic_response_mutation",
            "closed_same_day_element_aggregation_audit",
            "same_day_aggregation_rule_and_count_mutations",
            "campaign_same_day_duplicate_row_aggregate",
            "closed_peakro_companion_recovery_audit",
            "peakro_recovery_source_rule_and_count_mutations",
            "campaign_peakro_recovery_aggregate",
            "closed_nonresponse_element_overflow_audit",
            "closed_nonresponse_effint_overflow_audit",
            "response_field_overflow_mutations",
            "element_overflow_source_and_count_mutations",
            "effint_overflow_source_rule_and_count_mutations",
            "campaign_element_overflow_aggregate",
            "campaign_extractor_identity_mutation",
            "response_execution_extractor_cross_binding",
            "response_index_execution_raw_output_identity_map",
            "station_derived_conditional_winter_output_roles",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign_index", type=Path, nargs="?")
    parser.add_argument("campaign_archive_dir", type=Path, nargs="?")
    parser.add_argument("climate_analysis", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    positional = (
        args.campaign_index,
        args.campaign_archive_dir,
        args.climate_analysis,
    )
    if args.self_test:
        if any(value is not None for value in positional):
            parser.error("--self-test does not accept production inputs")
        print(json.dumps(self_test(), allow_nan=False, indent=2, sort_keys=True))
        return
    if any(value is None for value in positional):
        parser.error("campaign index, archive directory, and climate analysis are required")
    execute(
        args.campaign_index.resolve(strict=True),
        args.campaign_archive_dir.resolve(strict=True),
        args.climate_analysis.resolve(strict=True),
    )


if __name__ == "__main__":
    try:
        main()
    except (AnalysisError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"analyze-wepp: {error}", file=sys.stderr)
        raise SystemExit(1) from error
