#!/usr/bin/env python3
"""Independently verify the sealed A5b candidate evidence.

Usage:
  verify-a5b-evidence.py [candidate-evidence-manifest-v1.json]
      [--candidate-cli-dir DIR] [--archive-dir DIR]
  verify-a5b-evidence.py --self-test

All paths carried by evidence are repository-root-relative.  The verifier
never searches an alternate evidence directory and never extracts a tarball.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import gzip
import hashlib
import io
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import tarfile
import tempfile
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = ROOT / "docs/work-packages/20260713-a5b-interannual-candidate-spike"
DEFAULT_MANIFEST = PACKAGE / "artifacts/climate/candidate-evidence-manifest-v1.json"
OBSERVED_CORPUS = (
    ROOT
    / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
    / "artifacts/corpus/observed-target-corpus-v1.json"
)
CORPUS_CONFIG = (
    ROOT
    / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
    / "artifacts/corpus/corpus-config-v1.json"
)
A5A_SOURCE_MANIFEST = (
    ROOT
    / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
    / "artifacts/corpus/source-manifest-v1.json"
)
EVIDENCE_SCHEMA = ROOT / "docs/specifications/a5b-candidate-evidence-v1.schema.json"
RUN_SCHEMA = ROOT / "docs/specifications/a5b-run-record-v1.schema.json"
PLAN_SCHEMA = ROOT / "docs/specifications/a5b-overlay-plan-v1.schema.json"
BUNDLE_SCHEMA = ROOT / "docs/specifications/a5b-augmented-station-v1.schema.json"
BASE_STATION_SCHEMA = ROOT / "docs/specifications/station-document.schema.json"
QUALITY_SCHEMA = ROOT / "docs/specifications/quality-report-s2-m3.schema.json"
PROVENANCE_SCHEMA = ROOT / "docs/specifications/provenance-v1.schema.json"

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
CANDIDATES = (
    (
        "rank_one_monthly_sd",
        "interannual_rank_one_monthly_sd_v1",
        "a5b_rank_one_monthly_sd_v1",
    ),
    (
        "full_monthly_covariance",
        "interannual_full_monthly_covariance_v1",
        "a5b_full_monthly_covariance_v1",
    ),
    ("fourier_eof", "interannual_fourier_eof_v1", "a5b_fourier_eof_v1"),
    ("vector_ar", "interannual_fourier_eof_var1_v1", "a5b_vector_ar_v1"),
    (
        "gaussian_hmm",
        "interannual_fourier_eof_hmm2_v1",
        "a5b_gaussian_hmm_v1",
    ),
    (
        "spectral_random_phase",
        "interannual_fourier_eof_spectral_v1",
        "a5b_spectral_random_phase_v1",
    ),
    (
        "precip_counterfactual",
        "interannual_fourier_eof_precip_counterfactual_v1",
        "a5b_fourier_eof_precip_counterfactual_v1",
    ),
)
CANDIDATE_BY_ID = {row[0]: row for row in CANDIDATES}
CANDIDATE_INDEX = {row[0]: index for index, row in enumerate(CANDIDATES)}
REPLICATE_BY_INDEX = {row[0]: row for row in REPLICATES}
MONTH_NAMES = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)
FEATURE_ORDER = (
    *(f"prcp_log1p_total_mm_{month}" for month in MONTH_NAMES),
    *(f"tmax_mean_deg_c_{month}" for month in MONTH_NAMES),
    *(f"tmin_mean_deg_c_{month}" for month in MONTH_NAMES),
)

RUN_CONTRACT_KEYS = (
    "candidate_spec",
    "evaluation_spec",
    "metric_manifest",
    "metric_schema",
    "metric_verifier",
    "bootstrap_reference",
    "bootstrap_golden",
    "quality_schema",
    "station_schema",
    "base_station_schema",
    "plan_schema",
    "run_record_schema",
    "wepp_schema",
    "wepp_protocol",
    "wepp_verifier",
)
EXTRA_CONTRACT_KEYS = (
    "evidence_schema",
    "evidence_verifier",
    "matrix_runner",
    "plan_generator",
    "overlay_source",
    "fitter",
    "pre_candidate_freeze",
    "pre_output_amendments",
)
CONTRACT_PATHS = {
    "candidate_spec": "docs/specifications/SPEC-A5B-CANDIDATES.md",
    "evaluation_spec": "docs/specifications/SPEC-A5-EVALUATION.md",
    "metric_manifest": "docs/specifications/a5-climate-gate-metrics-v1.json",
    "metric_schema": "docs/specifications/a5-climate-gate-metrics-v1.schema.json",
    "metric_verifier": (
        "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/"
        "artifacts/verify-a5-climate-gate-metrics-v1.py"
    ),
    "bootstrap_reference": (
        "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/"
        "artifacts/observed-bootstrap-v1.py"
    ),
    "bootstrap_golden": (
        "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/"
        "artifacts/observed-bootstrap-v1-golden.json"
    ),
    "quality_schema": "docs/specifications/quality-report-s2-m3.schema.json",
    "station_schema": "docs/specifications/a5b-augmented-station-v1.schema.json",
    "base_station_schema": "docs/specifications/station-document.schema.json",
    "plan_schema": "docs/specifications/a5b-overlay-plan-v1.schema.json",
    "run_record_schema": "docs/specifications/a5b-run-record-v1.schema.json",
    "wepp_schema": "docs/specifications/a5-wepp-response-v1.schema.json",
    "wepp_protocol": (
        "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/"
        "artifacts/wepp-response-protocol.md"
    ),
    "wepp_verifier": (
        "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/"
        "artifacts/verify-wepp-response-schema.py"
    ),
    "evidence_schema": "docs/specifications/a5b-candidate-evidence-v1.schema.json",
    "evidence_verifier": (
        "docs/work-packages/20260713-a5b-interannual-candidate-spike/"
        "artifacts/runtime/verify-a5b-evidence.py"
    ),
    "matrix_runner": (
        "docs/work-packages/20260713-a5b-interannual-candidate-spike/"
        "artifacts/runtime/run-a5b-matrix.py"
    ),
    "plan_generator": (
        "docs/work-packages/20260713-a5b-interannual-candidate-spike/"
        "artifacts/runtime/generate-a5b-plan.py"
    ),
    "overlay_source": "crates/cligen/src/bin/cligen-a5b-overlay.rs",
    "fitter": (
        "docs/work-packages/20260713-a5b-interannual-candidate-spike/"
        "artifacts/fit/fit-a5b-models.py"
    ),
    "pre_candidate_freeze": (
        "docs/work-packages/20260713-a5b-interannual-candidate-spike/"
        "artifacts/freeze/pre-candidate-freeze-v1.json"
    ),
    "pre_output_amendments": (
        "docs/work-packages/20260713-a5b-interannual-candidate-spike/"
        "artifacts/freeze/pre-output-amendments.md"
    ),
}

MAIN_DOMAIN = b"cligen-a5b-extension-v1\0"
COUNTERFACTUAL_DOMAIN = b"cligen-a5b-counterfactual-v1\0"
ARCHIVE_DIRECTORY = PurePosixPath(
    "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/climate"
)
EXPECTED_RUNS = 1904
RUNS_PER_CANDIDATE = 272
PLANS_PER_CANDIDATE = 136
MEMBERS_PER_CANDIDATE = 952
SHARED_BASE_COUNT = 272
SHARED_BASE_MEMBER_COUNT = 544
SHARED_BASE_ARCHIVE_NAME = "shared-base-evidence-v1.tar.gz"
MAX_RENDERABLE_PRECIP_MM = struct.unpack(">f", struct.pack(">f", 999.9))[0]
NEUTRAL_BASE_COMMAND_ECHO = "--a5b-base faithful_5_32_3"
CANONICAL_GZIP_HEADER = bytes((0x1F, 0x8B, 8, 0, 0, 0, 0, 0, 2, 255))
SELF_TEST_GOLDEN_SHA256 = (
    "56af448a9cdac00a64e23bb89ac9b4045fc6418c4d91cdf6057a7de753ea96e4"
)

SOURCE_MANIFEST_KEYS = {
    "source_manifest_version",
    "source_snapshot_id",
    "calendar_transform",
    "fit_period",
    "heldout_period",
    "corpus_config",
    "a5a_source_manifest",
    "stations",
}
SOURCE_STATION_KEYS = {
    "station_id",
    "archive_path",
    "archive_bytes",
    "archive_sha256",
    "decompressed_bytes",
    "decompressed_sha256",
    "configured_decompressed_sha256",
    "full_years",
    "fit_years",
    "fit_rows",
    "post_fit_rows",
    "returned_grid",
}
FIT_MANIFEST_KEYS = {
    "fit_manifest_version",
    "coefficient_payload_schema",
    "fit_recipe_id",
    "implementation_base_commit",
    "fitter",
    "inputs",
    "output_contract",
    "repeatability",
    "diagnostics",
    "stations",
}
FIT_STATION_KEYS = {
    "station_id",
    "station_bundle",
    "station_bundle_sha256",
    "station_bundle_bytes",
    "base_par_sha256",
    "base_station_document_sha256",
    "source_decompressed_sha256",
    "retained_rank",
    "candidate_fits",
}
FIT_CANDIDATE_KEYS = {
    "candidate_id",
    "runtime_parameter_count",
    "serialized_numeric_count",
    "payload_sha256",
    "fit_identity_sha256",
    "fit_status",
}

DIAGNOSTIC_KEYS = {
    "diagnostics_schema_version",
    "station_id",
    "station_model",
    "candidate_profile",
    "extension_seed",
    "coefficient_payload_sha256",
    "state_table_sha256",
    "input_runspec_sha256",
    "plan_sha256",
    "faithful_cli_sha256",
    "output_cli_sha256",
    "row_count",
    "plan_state_years",
    "consumed_prefix_years",
    "wet_days_before",
    "wet_days_after",
    "temperature_order_repairs",
    "dewpoint_caps",
    "counterfactual_applied",
    "counterfactual_months",
    "relocated_wet_days",
    "reassigned_storm_tuples",
    "counterfactual_rng_final_state",
    "precipitation_render_limit_adjustments",
    "precipitation_factor_adjustments",
}


class EvidenceError(RuntimeError):
    """A fail-closed evidence, archive, schema, or lineage violation."""


@dataclass(frozen=True)
class ResolvedArtifact:
    record: dict[str, Any]
    path: Path


@dataclass(frozen=True)
class FitStation:
    station_id: str
    bundle_artifact: dict[str, Any]
    bundle: dict[str, Any]
    par_sha256: str
    extensions: dict[str, dict[str, Any]]


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def reject_constant(token: str) -> None:
    raise EvidenceError(f"nonfinite JSON token is forbidden: {token}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise EvidenceError(f"JSON number overflows binary64: {token}")
    return value


def strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_constant,
            parse_float=parse_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"{label}: invalid strict JSON: {error}") from error


def strict_json(path: Path) -> Any:
    try:
        return strict_json_bytes(path.read_bytes(), str(path))
    except OSError as error:
        raise EvidenceError(f"cannot read {path}: {error}") from error


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def declaration_order_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=False,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def compact_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def declaration_order_compact_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=False,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_named_bytes(items: Iterable[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, raw in items:
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be an object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise EvidenceError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def validate_schema(value: Any, validator: Draft202012Validator, label: str) -> None:
    errors = sorted(
        validator.iter_errors(value),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if errors:
        rendered = "; ".join(
            f"/{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
            for error in errors[:6]
        )
        raise EvidenceError(f"{label}: schema validation failed: {rendered}")


def plain_validator(path: Path) -> Draft202012Validator:
    schema = require_dict(strict_json(path), f"schema {path}")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def bundle_validator() -> Draft202012Validator:
    schema = require_dict(strict_json(BUNDLE_SCHEMA), "station bundle schema")
    base = require_dict(strict_json(BASE_STATION_SCHEMA), "base station schema")
    resolved = (
        "https://raw.githubusercontent.com/rogerlew/cligen-rs/main/"
        "docs/specifications/station-document.schema.json"
    )
    registry = Registry().with_resources(
        [
            (schema["$id"], Resource.from_contents(schema)),
            (base["$id"], Resource.from_contents(base)),
            (resolved, Resource.from_contents(base)),
        ]
    )
    return Draft202012Validator(schema, registry=registry)


def quality_validator() -> Draft202012Validator:
    schema = copy.deepcopy(require_dict(strict_json(QUALITY_SCHEMA), "quality schema"))
    provenance = require_dict(strict_json(PROVENANCE_SCHEMA), "provenance schema")
    if schema.get("$defs", {}).get("provenance") != {
        "$ref": "provenance-v1.schema.json"
    }:
        raise EvidenceError("quality schema provenance reference differs")
    schema["$defs"]["provenance"] = provenance
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_safe_relative_path(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{label} must be a nonempty repository-relative path")
    path = PurePosixPath(value)
    if (
        value.startswith("/")
        or "\\" in value
        or any(part in ("", ".", "..") for part in path.parts)
        or path.as_posix() != value
    ):
        raise EvidenceError(f"{label} is unsafe or noncanonical: {value!r}")
    return path


def resolve_artifact(
    record_value: Any,
    label: str,
    root: Path = ROOT,
) -> ResolvedArtifact:
    record = require_dict(record_value, label)
    require_exact_keys(record, {"path", "sha256", "bytes"}, label)
    relative = validate_safe_relative_path(record["path"], f"{label}.path")
    lexical = root.joinpath(*relative.parts)
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as error:
        raise EvidenceError(f"{label} does not resolve to a file: {error}") from error
    root_resolved = root.resolve(strict=True)
    if not resolved.is_relative_to(root_resolved) or not resolved.is_file():
        raise EvidenceError(f"{label} escapes the repository or is not a file")
    if isinstance(record["bytes"], bool) or not isinstance(record["bytes"], int):
        raise EvidenceError(f"{label}.bytes must be an integer")
    if resolved.stat().st_size != record["bytes"]:
        raise EvidenceError(f"{label} byte count mismatch")
    digest = sha256_path(resolved)
    if digest != record["sha256"]:
        raise EvidenceError(f"{label} SHA-256 mismatch")
    return ResolvedArtifact(record, resolved)


def resolve_archive_artifact(
    record_value: Any,
    label: str,
    archive_dir: Path | None,
    root: Path = ROOT,
) -> ResolvedArtifact:
    if archive_dir is None:
        return resolve_artifact(record_value, label, root)
    record = require_dict(record_value, label)
    require_exact_keys(record, {"path", "sha256", "bytes"}, label)
    relative = validate_safe_relative_path(record["path"], f"{label}.path")
    staged = archive_dir / relative.name
    try:
        resolved = staged.resolve(strict=True)
    except OSError as error:
        raise EvidenceError(f"{label} staging substitute is missing: {error}") from error
    if (
        not resolved.is_relative_to(archive_dir.resolve(strict=True))
        or not resolved.is_file()
        or isinstance(record["bytes"], bool)
        or not isinstance(record["bytes"], int)
        or resolved.stat().st_size != record["bytes"]
        or sha256_path(resolved) != record["sha256"]
    ):
        raise EvidenceError(f"{label} staging substitute identity differs")
    return ResolvedArtifact(record, resolved)


def member_identity(value: Any, label: str) -> tuple[str, str, int]:
    record = require_dict(value, label)
    require_exact_keys(record, {"member", "sha256", "bytes"}, label)
    name = validate_safe_relative_path(record["member"], f"{label}.member").as_posix()
    digest = record["sha256"]
    size = record["bytes"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EvidenceError(f"{label}.sha256 is not lowercase SHA-256")
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise EvidenceError(f"{label}.bytes must be a positive integer")
    return name, digest, size


def artifact_as_member(value: dict[str, Any]) -> dict[str, Any]:
    return {"member": value["path"], "sha256": value["sha256"], "bytes": value["bytes"]}


def days_in_horizon(years: int) -> int:
    leap_years = sum(
        year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        for year in range(1, years + 1)
    )
    return years * 365 + leap_years


def domain_sha256(domain: bytes, station_id: str, profile: str, seed: str) -> str:
    seed_bytes = int(seed[2:], 16).to_bytes(8, "big")
    return sha256_bytes(
        domain
        + station_id.encode("ascii")
        + b"\0"
        + profile.encode("ascii")
        + b"\0"
        + seed_bytes
    )


def verify_contracts(manifest: dict[str, Any], root: Path = ROOT) -> None:
    contracts = require_dict(manifest["contracts"], "evidence contracts")
    expected_keys = set(RUN_CONTRACT_KEYS) | set(EXTRA_CONTRACT_KEYS)
    require_exact_keys(contracts, expected_keys, "evidence contracts")
    for key, relative in CONTRACT_PATHS.items():
        record = require_dict(contracts[key], f"contract {key}")
        require_exact_keys(record, {"path", "sha256"}, f"contract {key}")
        if record["path"] != relative:
            raise EvidenceError(f"contract {key} path differs from the frozen path")
        path = root.joinpath(*validate_safe_relative_path(relative, key).parts)
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise EvidenceError(f"contract {key} is missing: {error}") from error
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            raise EvidenceError(f"contract {key} escapes the repository")
        if record["sha256"] != sha256_path(resolved):
            raise EvidenceError(
                f"contract {key} hash differs from the current artifact"
            )
    freeze_record = contracts["pre_candidate_freeze"]
    freeze_path = root.joinpath(
        *validate_safe_relative_path(
            freeze_record["path"], "pre-candidate freeze contract path"
        ).parts
    )
    freeze = require_dict(strict_json(freeze_path), "pre-candidate freeze")
    frozen_a5b = require_dict(
        freeze.get("a5b_frozen_artifacts"), "pre-candidate frozen A5b artifacts"
    )
    frozen_a5a = require_dict(
        freeze.get("a5a_pinned_artifacts"), "pre-candidate pinned A5a artifacts"
    )
    for key, record in contracts.items():
        if key == "pre_candidate_freeze":
            continue
        expected = frozen_a5b.get(record["path"], frozen_a5a.get(record["path"]))
        if expected != record["sha256"]:
            raise EvidenceError(
                f"contract {key} differs from the pre-candidate freeze inventory"
            )


def observed_station_catalog(
    manifest: dict[str, Any], root: Path = ROOT
) -> tuple[list[str], dict[str, str]]:
    corpus_path = root / OBSERVED_CORPUS.relative_to(ROOT)
    corpus = require_dict(strict_json(corpus_path), "observed target corpus")
    if manifest["corpus"]["content_sha256"] != sha256_path(corpus_path):
        raise EvidenceError(
            "evidence corpus hash differs from the frozen observed corpus"
        )
    if manifest["corpus"]["schema_version"] != 1:
        raise EvidenceError("evidence corpus schema version differs")
    station_rows = corpus.get("stations")
    if not isinstance(station_rows, list) or len(station_rows) != 17:
        raise EvidenceError("observed target corpus must contain exactly 17 stations")
    station_ids = [row["station_id"] for row in station_rows]
    if manifest["corpus"]["station_ids"] != station_ids:
        raise EvidenceError("evidence station order/set differs from observed corpus")
    regimes = {row["station_id"]: row["regime"] for row in station_rows}
    if len(regimes) != 17:
        raise EvidenceError("observed target station IDs are not unique")
    return station_ids, regimes


def expected_matrix_keys(station_ids: Iterable[str]) -> set[tuple[str, str, int, int]]:
    return set(
        itertools.product(
            (candidate[0] for candidate in CANDIDATES), station_ids, HORIZONS, range(8)
        )
    )


def verify_matrix(
    manifest: dict[str, Any], station_ids: list[str], regimes: dict[str, str]
) -> dict[tuple[str, str, int, int], dict[str, Any]]:
    matrix = manifest["matrix"]
    if matrix["horizons"] != list(HORIZONS):
        raise EvidenceError("matrix horizons differ from [30,100]")
    expected_replicates = [
        {"replicate": index, "legacy_burn": burn, "extension_seed": seed}
        for index, burn, seed in REPLICATES
    ]
    if matrix["replicates"] != expected_replicates:
        raise EvidenceError("matrix replicate records differ from preregistration")
    expected_candidates = [
        {
            "candidate_id": candidate_id,
            "station_model": station_model,
            "generation_profile": profile,
        }
        for candidate_id, station_model, profile in CANDIDATES
    ]
    if (
        matrix["candidates"] != expected_candidates
        or matrix["expected_runs"] != EXPECTED_RUNS
    ):
        raise EvidenceError(
            "matrix candidate declaration differs from the frozen contract"
        )

    rows = manifest["runs"]
    if not isinstance(rows, list):
        raise EvidenceError("evidence runs must be an array")
    indexed: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    ordered_keys: list[tuple[str, str, int, int]] = []
    for row in rows:
        key = (
            row.get("candidate_id"),
            row.get("station_id"),
            row.get("horizon_years"),
            row.get("replicate"),
        )
        if key in indexed:
            raise EvidenceError(f"duplicate candidate run key: {key}")
        indexed[key] = row
        ordered_keys.append(key)
        candidate_id, station_id, horizon, replicate = key
        if station_id not in regimes or candidate_id not in CANDIDATE_BY_ID:
            continue
        if row.get("regime") != regimes[station_id]:
            raise EvidenceError(f"{key}: run regime differs from corpus")
        expected_replicate = REPLICATE_BY_INDEX.get(replicate)
        if expected_replicate is None:
            continue
        if (
            row.get("legacy_burn") != expected_replicate[1]
            or row.get("extension_seed") != expected_replicate[2]
        ):
            raise EvidenceError(f"{key}: burn/extension seed differs from replicate")
        if row.get("archive_candidate_id") != candidate_id:
            raise EvidenceError(f"{key}: archive candidate identity differs")

    expected = expected_matrix_keys(station_ids)
    actual = set(indexed)
    if len(rows) != EXPECTED_RUNS or actual != expected:
        raise EvidenceError(
            "candidate run matrix differs: "
            f"count={len(rows)}, missing={len(expected - actual)}, "
            f"extra={len(actual - expected)}"
        )
    expected_order = [
        (candidate[0], station_id, horizon, replicate)
        for candidate in CANDIDATES
        for station_id in station_ids
        for horizon in HORIZONS
        for replicate in range(8)
    ]
    if ordered_keys != expected_order:
        raise EvidenceError("candidate run index is not in frozen canonical order")
    return indexed


def serialized_numeric_count(value: Any) -> int:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return 0
    if isinstance(value, (int, float)):
        return 1
    if isinstance(value, list):
        return sum(serialized_numeric_count(item) for item in value)
    if isinstance(value, dict):
        return sum(serialized_numeric_count(item) for item in value.values())
    raise EvidenceError(f"unsupported coefficient payload type: {type(value).__name__}")


def require_numeric_vector(value: Any, length: int, label: str) -> list[Any]:
    if not isinstance(value, list) or len(value) != length:
        raise EvidenceError(f"{label} must have length {length}")
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise EvidenceError(f"{label} contains a nonnumeric value")
        try:
            finite = math.isfinite(item)
        except (OverflowError, TypeError):
            finite = False
        if not finite:
            raise EvidenceError(f"{label} contains a nonfinite/overflowing value")
    return value


def require_numeric_matrix(
    value: Any, rows: int, columns: int, label: str
) -> list[list[Any]]:
    if not isinstance(value, list) or len(value) != rows:
        raise EvidenceError(f"{label} must have {rows} rows")
    return [
        require_numeric_vector(row, columns, f"{label}[{index}]")
        for index, row in enumerate(value)
    ]


def require_lower_triangle(value: Any, size: int, label: str) -> None:
    if not isinstance(value, list) or len(value) != size:
        raise EvidenceError(f"{label} must have {size} rows")
    for index, row in enumerate(value):
        require_numeric_vector(row, index + 1, f"{label}[{index}]")


def validate_extension_semantics(
    extension: dict[str, Any],
    station_id: str,
    source_sha256: str,
    par_sha256: str,
    fitter_sha256: str,
    implementation_commit: str,
) -> None:
    candidate_id = extension["candidate_id"]
    payload = extension["payload"]
    diagnostics = extension["diagnostics"]
    rank: int | None = None
    if candidate_id == "rank_one_monthly_sd":
        standard_deviations = require_numeric_vector(
            payload["standard_deviations"], 36, f"{station_id}/{candidate_id} SDs"
        )
        if any(value < 0.0 for value in standard_deviations):
            raise EvidenceError(f"{station_id}/{candidate_id}: negative SD")
        expected_runtime = 36
    elif candidate_id == "full_monthly_covariance":
        require_lower_triangle(
            payload["cholesky_lower"], 36, f"{station_id}/{candidate_id} Cholesky"
        )
        if any(row[-1] <= 0.0 for row in payload["cholesky_lower"]):
            raise EvidenceError(
                f"{station_id}/{candidate_id}: nonpositive Cholesky diagonal"
            )
        expected_runtime = 666
    else:
        rank = payload["rank"]
        if isinstance(rank, bool) or not isinstance(rank, int) or not 3 <= rank <= 10:
            raise EvidenceError(f"{station_id}/{candidate_id}: EOF rank differs")
        require_numeric_matrix(
            payload["reconstruction"],
            36,
            rank,
            f"{station_id}/{candidate_id} reconstruction",
        )
        if candidate_id == "fourier_eof":
            expected_runtime = 36 * rank
        elif candidate_id == "vector_ar":
            require_numeric_matrix(
                payload["transition"],
                rank,
                rank,
                f"{station_id}/{candidate_id} transition",
            )
            require_lower_triangle(
                payload["innovation_cholesky_lower"],
                rank,
                f"{station_id}/{candidate_id} innovation Cholesky",
            )
            if any(row[-1] <= 0.0 for row in payload["innovation_cholesky_lower"]):
                raise EvidenceError(
                    f"{station_id}/{candidate_id}: nonpositive innovation diagonal"
                )
            if payload["warmup_years"] != 256:
                raise EvidenceError(f"{station_id}/{candidate_id}: warmup differs")
            expected_runtime = 36 * rank + rank * rank + rank * (rank + 1) // 2
        elif candidate_id == "gaussian_hmm":
            require_numeric_matrix(
                payload["transition"],
                2,
                2,
                f"{station_id}/{candidate_id} transition",
            )
            require_numeric_vector(
                payload["stationary"], 2, f"{station_id}/{candidate_id} stationary"
            )
            require_numeric_matrix(
                payload["emission_means"],
                2,
                rank,
                f"{station_id}/{candidate_id} emission means",
            )
            require_numeric_matrix(
                payload["emission_standard_deviations"],
                2,
                rank,
                f"{station_id}/{candidate_id} emission SDs",
            )
            if any(
                not math.isclose(math.fsum(row), 1.0, rel_tol=0.0, abs_tol=2e-15)
                or any(value <= 0.0 or value >= 1.0 for value in row)
                for row in payload["transition"]
            ):
                raise EvidenceError(
                    f"{station_id}/{candidate_id}: HMM transition differs"
                )
            if not math.isclose(
                math.fsum(payload["stationary"]), 1.0, rel_tol=0.0, abs_tol=2e-15
            ) or any(value <= 0.0 for value in payload["stationary"]):
                raise EvidenceError(
                    f"{station_id}/{candidate_id}: HMM stationary differs"
                )
            if any(
                value < 0.001
                for row in payload["emission_standard_deviations"]
                for value in row
            ):
                raise EvidenceError(
                    f"{station_id}/{candidate_id}: HMM emission floor differs"
                )
            expected_runtime = 36 * rank + 2 + 4 * rank
        elif candidate_id == "spectral_random_phase":
            require_numeric_matrix(
                payload["non_dc_amplitudes"],
                rank,
                15,
                f"{station_id}/{candidate_id} amplitudes",
            )
            expected_runtime = 36 * rank + 15 * rank
        elif candidate_id == "precip_counterfactual":
            require_numeric_matrix(
                payload["second_order_wet_probabilities"],
                12,
                4,
                f"{station_id}/{candidate_id} wet probabilities",
            )
            require_numeric_vector(
                payload["amount_rank_rho"],
                12,
                f"{station_id}/{candidate_id} amount correlations",
            )
            if any(
                value <= 0.0 or value >= 1.0
                for row in payload["second_order_wet_probabilities"]
                for value in row
            ) or any(abs(value) > 0.95 for value in payload["amount_rank_rho"]):
                raise EvidenceError(
                    f"{station_id}/{candidate_id}: counterfactual coefficient range differs"
                )
            expected_runtime = 36 * rank + 60
        else:
            raise EvidenceError(f"{station_id}: unknown coefficient candidate")

    payload_sha = sha256_bytes(canonical_json_bytes(payload))
    if diagnostics["payload_sha256"] != payload_sha:
        raise EvidenceError(f"{station_id}/{candidate_id}: payload hash differs")
    if diagnostics["serialized_numeric_count"] != serialized_numeric_count(payload):
        raise EvidenceError(
            f"{station_id}/{candidate_id}: serialized numeric count differs"
        )
    if extension["runtime_parameter_count"] != expected_runtime:
        raise EvidenceError(f"{station_id}/{candidate_id}: runtime count differs")
    if diagnostics["warnings"] != sorted(diagnostics["warnings"]) or diagnostics[
        "interventions"
    ] != sorted(diagnostics["interventions"]):
        raise EvidenceError(f"{station_id}/{candidate_id}: diagnostics are not sorted")
    identity_material = {
        "candidate_id": candidate_id,
        "coefficient_payload_schema": "a5b_interannual_coefficients_v1",
        "fit_recipe_id": "a5b_monthly_state_fit_v1",
        "fitter_sha256": fitter_sha256,
        "implementation_base_commit": implementation_commit,
        "legacy_par_sha256": par_sha256,
        "payload_sha256": payload_sha,
        "source_decompressed_sha256": source_sha256,
        "station_id": station_id,
    }
    if extension["fit_identity_sha256"] != sha256_bytes(
        canonical_json_bytes(identity_material)
    ):
        raise EvidenceError(f"{station_id}/{candidate_id}: fit identity differs")


def verify_fit_artifacts(
    manifest: dict[str, Any],
    station_ids: list[str],
    validator: Draft202012Validator,
    cligen: ResolvedArtifact,
    root: Path = ROOT,
) -> tuple[dict[str, FitStation], str]:
    source_artifact = resolve_artifact(
        manifest["fit"]["source_manifest"], "fit source manifest", root
    )
    fit_artifact = resolve_artifact(
        manifest["fit"]["fit_manifest"], "fit manifest", root
    )
    if (
        source_artifact.path.name != "source-manifest-v1.json"
        or fit_artifact.path.name != "fit-manifest-v1.json"
        or source_artifact.path.parent != fit_artifact.path.parent
    ):
        raise EvidenceError("fit manifest filenames/directories differ")
    source = require_dict(strict_json(source_artifact.path), "fit source manifest")
    fit = require_dict(strict_json(fit_artifact.path), "fit manifest")
    require_exact_keys(source, SOURCE_MANIFEST_KEYS, "fit source manifest")
    require_exact_keys(
        require_dict(source["corpus_config"], "fit source corpus config"),
        {"path", "sha256"},
        "fit source corpus config",
    )
    require_exact_keys(
        require_dict(source["a5a_source_manifest"], "fit A5a source manifest"),
        {"path", "sha256"},
        "fit A5a source manifest",
    )
    config_path = root / CORPUS_CONFIG.relative_to(ROOT)
    a5a_source_path = root / A5A_SOURCE_MANIFEST.relative_to(ROOT)
    expected_source_references = (
        (source["corpus_config"], config_path, "fit corpus config"),
        (source["a5a_source_manifest"], a5a_source_path, "fit A5a source manifest"),
    )
    for reference, expected_path, label in expected_source_references:
        expected_relative = expected_path.relative_to(root).as_posix()
        if reference["path"] != expected_relative or reference["sha256"] != sha256_path(
            expected_path
        ):
            raise EvidenceError(f"{label} identity differs")
    config = require_dict(strict_json(config_path), "A5a corpus config")
    a5a_source = require_dict(strict_json(a5a_source_path), "A5a source manifest")
    config_rows = config.get("stations")
    a5a_rows = a5a_source.get("stations")
    if (
        config.get("periods")
        != {
            "evaluation": [2010, 2025],
            "fit": [1980, 2009],
            "full": [1980, 2025],
        }
        or not isinstance(config_rows, list)
        or [row.get("station_id") for row in config_rows] != station_ids
        or not isinstance(a5a_rows, list)
        or [row.get("station_id") for row in a5a_rows] != station_ids
    ):
        raise EvidenceError("fit source inputs differ from the frozen A5a corpus")
    config_by_id = {row["station_id"]: row for row in config_rows}
    a5a_by_id = {row["station_id"]: row for row in a5a_rows}
    if source.get("source_manifest_version") != 1:
        raise EvidenceError("fit source manifest version differs")
    if source.get("source_snapshot_id") != "daymet_v4r1_a5a17_fit1980_2009_noleap_v1":
        raise EvidenceError("fit source snapshot identity differs")
    if source.get("fit_period") != [1980, 2009] or source.get("heldout_period") != [
        2010,
        2025,
    ]:
        raise EvidenceError("fit source/held-out period differs")
    if source.get("calendar_transform") != "noleap_365_v1":
        raise EvidenceError("fit source calendar transform differs")
    source_rows = source.get("stations")
    if (
        not isinstance(source_rows, list)
        or [row.get("station_id") for row in source_rows] != station_ids
    ):
        raise EvidenceError("fit source station order/set differs from corpus")
    for row in source_rows:
        station_id = row.get("station_id")
        require_exact_keys(row, SOURCE_STATION_KEYS, f"{station_id} fit source")
        if row.get("fit_years") != 30 or row.get("fit_rows") != 10950:
            raise EvidenceError(
                f"{row.get('station_id')}: fit source row boundary differs"
            )
        if row.get("post_fit_rows") != 5840:
            raise EvidenceError(
                f"{row.get('station_id')}: held-out structural count differs"
            )
        if row.get("decompressed_sha256") != row.get("configured_decompressed_sha256"):
            raise EvidenceError(
                f"{row.get('station_id')}: fit source hash/config hash differs"
            )
        config_row = config_by_id[station_id]
        daymet = require_dict(
            require_dict(a5a_by_id[station_id].get("sources"), "A5a sources").get(
                "daymet"
            ),
            f"{station_id} A5a Daymet source",
        )
        expected_archive = f"references/observed/a5a-v1/daymet/{station_id}.csv.gz"
        if (
            row.get("full_years") != [1980, 2025]
            or row["archive_path"] != expected_archive
            or row["archive_path"] != daymet.get("archive_path")
            or row["archive_sha256"] != daymet.get("archive_sha256")
            or row["archive_bytes"] != daymet.get("archive_bytes")
            or row["decompressed_sha256"] != daymet.get("source_sha256")
            or row["decompressed_bytes"] != daymet.get("source_bytes")
            or row["configured_decompressed_sha256"]
            != config_row.get("daymet_source_sha256")
        ):
            raise EvidenceError(f"{station_id}: fit/A5a source lineage differs")
        resolve_artifact(
            {
                "path": row["archive_path"],
                "sha256": row["archive_sha256"],
                "bytes": row["archive_bytes"],
            },
            f"{station_id} archived Daymet source",
            root,
        )

    require_exact_keys(fit, FIT_MANIFEST_KEYS, "fit manifest")
    if fit.get("fit_manifest_version") != 1:
        raise EvidenceError("fit manifest version differs")
    if fit.get("coefficient_payload_schema") != "a5b_interannual_coefficients_v1":
        raise EvidenceError("fit coefficient payload schema differs")
    if fit.get("fit_recipe_id") != "a5b_monthly_state_fit_v1":
        raise EvidenceError("fit recipe identity differs")
    if (
        fit.get("implementation_base_commit")
        != manifest["build"]["implementation_commit"]
    ):
        raise EvidenceError("fit/build implementation commit differs")
    fitter = require_dict(fit["fitter"], "fit manifest fitter")
    require_exact_keys(
        fitter,
        {"path", "sha256", "python_version", "numpy_version", "scipy_version"},
        "fit manifest fitter",
    )
    if {"path": fitter["path"], "sha256": fitter["sha256"]} != manifest["contracts"][
        "fitter"
    ] or any(
        not isinstance(fitter[field], str) or not fitter[field]
        for field in ("python_version", "numpy_version", "scipy_version")
    ):
        raise EvidenceError("fit manifest fitter identity differs")
    inputs = require_dict(fit["inputs"], "fit manifest inputs")
    require_exact_keys(
        inputs,
        {
            "corpus_config_sha256",
            "a5a_source_manifest_sha256",
            "cligen_executable_sha256",
            "cligen_executable_bytes",
            "station_collection",
            "station_par_aggregate_sha256",
        },
        "fit manifest inputs",
    )
    if (
        inputs["corpus_config_sha256"] != sha256_path(config_path)
        or inputs["a5a_source_manifest_sha256"] != sha256_path(a5a_source_path)
        or inputs["cligen_executable_sha256"] != cligen.record["sha256"]
        or inputs["cligen_executable_bytes"] != cligen.record["bytes"]
        or inputs["station_collection"] != config.get("station_collection")
    ):
        raise EvidenceError("fit manifest input identity differs")
    output_contract = require_dict(fit["output_contract"], "fit output contract")
    require_exact_keys(
        output_contract,
        {
            "station_schema_version",
            "station_document_role",
            "bundle_schema_path",
            "bundle_schema_sha256",
            "station_count",
            "candidate_order",
        },
        "fit output contract",
    )
    if output_contract != {
        "station_schema_version": 2,
        "station_document_role": "a5b_interannual_candidate_bundle_v1",
        "bundle_schema_path": BUNDLE_SCHEMA.relative_to(ROOT).as_posix(),
        "bundle_schema_sha256": sha256_path(root / BUNDLE_SCHEMA.relative_to(ROOT)),
        "station_count": 17,
        "candidate_order": [candidate[0] for candidate in CANDIDATES],
    }:
        raise EvidenceError("fit output contract differs")
    repeatability = require_dict(fit["repeatability"], "fit repeatability")
    require_exact_keys(
        repeatability,
        {"passes", "byte_identical", "bundle_aggregate_sha256"},
        "fit repeatability",
    )
    if repeatability["passes"] != 2 or repeatability["byte_identical"] is not True:
        raise EvidenceError("fit repeatability evidence differs")
    diagnostics = require_dict(fit["diagnostics"], "fit diagnostics")
    require_exact_keys(diagnostics, {"path", "sha256", "bytes"}, "fit diagnostics")
    diagnostics_relative = validate_safe_relative_path(
        diagnostics["path"], "fit diagnostics path"
    )
    if diagnostics_relative != PurePosixPath("diagnostics/fit-diagnostics-v1.json"):
        raise EvidenceError("fit diagnostics deterministic path differs")
    diagnostics_path = fit_artifact.path.parent.joinpath(
        *diagnostics_relative.parts
    ).resolve(strict=True)
    if (
        not diagnostics_path.is_relative_to(fit_artifact.path.parent.resolve())
        or not diagnostics_path.is_file()
        or diagnostics_path.stat().st_size != diagnostics["bytes"]
        or sha256_path(diagnostics_path) != diagnostics["sha256"]
    ):
        raise EvidenceError("fit diagnostics identity differs")
    fit_rows = fit.get("stations")
    if (
        not isinstance(fit_rows, list)
        or [row.get("station_id") for row in fit_rows] != station_ids
    ):
        raise EvidenceError("fit manifest station order/set differs from corpus")
    fit_by_id = {row["station_id"]: row for row in fit_rows}
    source_by_id = {row["station_id"]: row for row in source_rows}
    for row in fit_rows:
        require_exact_keys(row, FIT_STATION_KEYS, f"{row.get('station_id')} fit row")
        candidate_fits = row.get("candidate_fits")
        if not isinstance(candidate_fits, list):
            raise EvidenceError(
                f"{row.get('station_id')}: candidate fits are not an array"
            )
        for candidate_fit in candidate_fits:
            require_exact_keys(
                candidate_fit,
                FIT_CANDIDATE_KEYS,
                f"{row.get('station_id')} candidate fit",
            )

    bundle_records = manifest["fit"]["bundles"]
    if not isinstance(bundle_records, list) or len(bundle_records) != 17:
        raise EvidenceError("evidence must bind exactly 17 station bundles")
    result: dict[str, FitStation] = {}
    bundle_items: list[tuple[str, bytes]] = []
    for station_id, artifact_record in zip(station_ids, bundle_records):
        artifact = resolve_artifact(
            artifact_record, f"{station_id} station bundle", root
        )
        bundle = require_dict(
            strict_json(artifact.path), f"{station_id} station bundle"
        )
        validate_schema(bundle, validator, f"{station_id} station bundle")
        if bundle["station_id"] != station_id:
            raise EvidenceError(f"{station_id}: station bundle identity differs")
        fit_contract = bundle["fit_contract"]
        if (
            fit_contract["implementation_base_commit"]
            != manifest["build"]["implementation_commit"]
            or fit_contract["fitter_sha256"] != fitter["sha256"]
            or fit_contract["python_version"] != fitter["python_version"]
            or fit_contract["numpy_version"] != fitter["numpy_version"]
            or fit_contract["scipy_version"] != fitter["scipy_version"]
            or fit_contract["feature_order"] != list(FEATURE_ORDER)
        ):
            raise EvidenceError(f"{station_id}: bundle fit contract differs")
        if bundle["source_lineage"]["fit_period"] != [1980, 2009]:
            raise EvidenceError(f"{station_id}: bundle fit period differs")
        if bundle["source_lineage"]["heldout_excluded_after"] != 2009:
            raise EvidenceError(f"{station_id}: bundle held-out boundary differs")
        if (
            bundle["source_lineage"]["decompressed_sha256"]
            != source_by_id[station_id]["decompressed_sha256"]
        ):
            raise EvidenceError(f"{station_id}: bundle/source input hash differs")
        if (
            bundle["source_lineage"]["archive_path"]
            != source_by_id[station_id]["archive_path"]
            or bundle["source_lineage"]["archive_sha256"]
            != source_by_id[station_id]["archive_sha256"]
            or bundle["source_lineage"]["returned_grid"]
            != source_by_id[station_id]["returned_grid"]
        ):
            raise EvidenceError(f"{station_id}: bundle/source lineage differs")
        fit_row = fit_by_id[station_id]
        if artifact.record["sha256"] != fit_row["station_bundle_sha256"]:
            raise EvidenceError(f"{station_id}: evidence/fit bundle hash differs")
        if artifact.record["bytes"] != fit_row["station_bundle_bytes"]:
            raise EvidenceError(f"{station_id}: evidence/fit bundle bytes differ")
        fit_bundle_relative = validate_safe_relative_path(
            fit_row["station_bundle"], f"{station_id} fit bundle path"
        )
        if fit_bundle_relative != PurePosixPath(
            f"station-bundles/{station_id}.a5b.station.json"
        ):
            raise EvidenceError(f"{station_id}: fit bundle path differs")
        artifact_relative = PurePosixPath(artifact.record["path"])
        if (
            fit_bundle_relative.parts[-2:] != artifact_relative.parts[-2:]
            or fit_bundle_relative.name != artifact.path.name
        ):
            raise EvidenceError(f"{station_id}: evidence/fit bundle filename differs")
        par_sha = fit_row["base_par_sha256"]
        if (
            par_sha != config_by_id[station_id]["par_sha256"]
            or bundle["base_station"]["lineage"]["source_sha256"] != par_sha
            or fit_row["source_decompressed_sha256"]
            != source_by_id[station_id]["decompressed_sha256"]
            or re.fullmatch(r"[0-9a-f]{64}", fit_row["base_station_document_sha256"])
            is None
        ):
            raise EvidenceError(f"{station_id}: bundle base-station .par hash differs")
        extensions = bundle["extensions"]
        if [extension["candidate_id"] for extension in extensions] != [
            candidate[0] for candidate in CANDIDATES
        ]:
            raise EvidenceError(f"{station_id}: bundle candidate order differs")
        extension_by_id = {
            extension["candidate_id"]: extension for extension in extensions
        }
        for extension in extensions:
            validate_extension_semantics(
                extension,
                station_id,
                source_by_id[station_id]["decompressed_sha256"],
                par_sha,
                fitter["sha256"],
                fit["implementation_base_commit"],
            )
        common_rank = extension_by_id["fourier_eof"]["payload"]["rank"]
        common_reconstruction = extension_by_id["fourier_eof"]["payload"][
            "reconstruction"
        ]
        for common_candidate in (
            "vector_ar",
            "gaussian_hmm",
            "spectral_random_phase",
            "precip_counterfactual",
        ):
            payload = extension_by_id[common_candidate]["payload"]
            if (
                payload["rank"] != common_rank
                or payload["reconstruction"] != common_reconstruction
            ):
                raise EvidenceError(
                    f"{station_id}/{common_candidate}: common EOF basis differs"
                )
        if (
            fit_row["retained_rank"]
            != extension_by_id["fourier_eof"]["payload"]["rank"]
        ):
            raise EvidenceError(f"{station_id}: retained EOF rank differs")
        candidate_fits = fit_row["candidate_fits"]
        if [row["candidate_id"] for row in candidate_fits] != [
            candidate[0] for candidate in CANDIDATES
        ]:
            raise EvidenceError(f"{station_id}: fit candidate order differs")
        for candidate_row in candidate_fits:
            extension = extension_by_id[candidate_row["candidate_id"]]
            comparisons = {
                "runtime_parameter_count": extension["runtime_parameter_count"],
                "serialized_numeric_count": extension["diagnostics"][
                    "serialized_numeric_count"
                ],
                "payload_sha256": extension["diagnostics"]["payload_sha256"],
                "fit_identity_sha256": extension["fit_identity_sha256"],
                "fit_status": extension["diagnostics"]["fit_status"],
            }
            if any(
                candidate_row.get(key) != value for key, value in comparisons.items()
            ):
                raise EvidenceError(
                    f"{station_id}/{candidate_row['candidate_id']}: fit lineage differs"
                )
            if extension["diagnostics"]["payload_sha256"] != sha256_bytes(
                canonical_json_bytes(extension["payload"])
            ):
                raise EvidenceError(
                    f"{station_id}/{candidate_row['candidate_id']}: payload hash differs"
                )
        result[station_id] = FitStation(
            station_id,
            artifact.record,
            bundle,
            par_sha,
            extension_by_id,
        )
        bundle_items.append((station_id, artifact.path.read_bytes()))
    if aggregate_named_bytes(bundle_items) != repeatability["bundle_aggregate_sha256"]:
        raise EvidenceError("fit repeatability bundle aggregate differs")
    return result, inputs["station_par_aggregate_sha256"]


def verify_build_artifacts(
    manifest: dict[str, Any], root: Path = ROOT
) -> tuple[ResolvedArtifact, ResolvedArtifact]:
    build = manifest["build"]
    if build["cargo_lock_sha256"] != sha256_path(root / "Cargo.lock"):
        raise EvidenceError("build Cargo.lock hash differs from current lockfile")
    if not isinstance(build["rustc_version"], str) or not build["rustc_version"]:
        raise EvidenceError("build rustc version is empty")
    if re.fullmatch(r"[0-9a-f]{40}", build["implementation_commit"]) is None:
        raise EvidenceError("build implementation commit is not a full Git commit")
    preflight = require_dict(build["plan_preflight"], "build plan preflight")
    require_exact_keys(
        preflight, {"plans", "aggregate_sha256"}, "build plan preflight"
    )
    if (
        preflight["plans"] != 952
        or not isinstance(preflight["aggregate_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", preflight["aggregate_sha256"]) is None
    ):
        raise EvidenceError("build plan preflight declaration differs")
    cligen = resolve_artifact(build["cligen_binary"], "cligen binary", root)
    overlay = resolve_artifact(build["overlay_binary"], "A5b overlay binary", root)
    if cligen.path.name != "cligen" or overlay.path.name != "cligen-a5b-overlay":
        raise EvidenceError("build executable filenames differ")
    return cligen, overlay


def validate_gzip_header(path: Path) -> None:
    with path.open("rb") as handle:
        header = handle.read(10)
    if header != CANONICAL_GZIP_HEADER:
        raise EvidenceError(
            f"archive gzip header is not canonical: observed {header.hex()}"
        )


def expected_archive_bindings(
    candidate_id: str, rows: list[dict[str, Any]]
) -> dict[str, tuple[str, int, str]]:
    if len(rows) != RUNS_PER_CANDIDATE:
        raise EvidenceError(f"{candidate_id}: candidate run count is not 272")
    bindings: dict[str, tuple[str, int, str]] = {}
    unique_by_kind: dict[str, set[str]] = {
        "run_record": set(),
        "quality_report": set(),
        "overlay_diagnostics": set(),
        "plan": set(),
    }
    for row in rows:
        for kind, prefix in (
            ("run_record", "run-records/"),
            ("quality_report", "quality-reports/"),
            ("overlay_diagnostics", "overlay-diagnostics/"),
            ("plan", "plans/"),
        ):
            name, digest, size = member_identity(row[kind], f"{candidate_id} {kind}")
            expected_name = {
                "run_record": f"run-records/{run_stem(row)}.run.json",
                "quality_report": f"quality-reports/{run_stem(row)}.quality.json",
                "overlay_diagnostics": (
                    f"overlay-diagnostics/{run_stem(row)}.diagnostics.json"
                ),
                "plan": (
                    f"plans/{row['station_id']}-{candidate_id}-rep{row['replicate']}-"
                    f"burn{row['legacy_burn']}.plan.json"
                ),
            }[kind]
            if not name.startswith(prefix) or name != expected_name:
                raise EvidenceError(
                    f"{candidate_id}: {kind} member differs from deterministic name"
                )
            prior = bindings.get(name)
            identity = (digest, size, kind)
            if prior is not None and prior != identity:
                raise EvidenceError(f"{candidate_id}: conflicting identity for {name}")
            bindings[name] = identity
            unique_by_kind[kind].add(name)
    expected_counts = {
        "run_record": RUNS_PER_CANDIDATE,
        "quality_report": RUNS_PER_CANDIDATE,
        "overlay_diagnostics": RUNS_PER_CANDIDATE,
        "plan": PLANS_PER_CANDIDATE,
    }
    actual_counts = {key: len(value) for key, value in unique_by_kind.items()}
    if actual_counts != expected_counts:
        raise EvidenceError(
            f"{candidate_id}: archive binding counts differ: {actual_counts}"
        )
    if len(bindings) != MEMBERS_PER_CANDIDATE:
        raise EvidenceError(f"{candidate_id}: archive binding total is not 952")

    plan_by_key: dict[tuple[str, int], tuple[str, str, int]] = {}
    for row in rows:
        key = (row["station_id"], row["replicate"])
        identity = member_identity(row["plan"], f"{candidate_id} plan")
        prior = plan_by_key.setdefault(key, identity)
        if prior != identity:
            raise EvidenceError(f"{candidate_id}/{key}: horizon plans differ")
    if len(plan_by_key) != PLANS_PER_CANDIDATE:
        raise EvidenceError(f"{candidate_id}: plan sharing key count differs")
    return bindings


def read_canonical_archive(
    path: Path,
    bindings: dict[str, tuple[str, int, str]],
    declared_member_count: int,
) -> dict[str, bytes]:
    validate_gzip_header(path)
    documents: dict[str, bytes] = {}
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            if archive.pax_headers:
                raise EvidenceError("archive contains global PAX metadata")
            members = archive.getmembers()
            names = [member.name for member in members]
            if len(names) != declared_member_count or declared_member_count != len(
                bindings
            ):
                raise EvidenceError(
                    "archive member count differs from manifest/bindings"
                )
            if len(names) != len(set(names)):
                raise EvidenceError("archive contains duplicate member names")
            if names != sorted(names):
                raise EvidenceError("archive members are not lexicographically sorted")
            for name in names:
                validate_safe_relative_path(name, "archive member")
            if set(names) != set(bindings):
                raise EvidenceError(
                    "archive member set differs: "
                    f"missing={len(set(bindings) - set(names))}, "
                    f"extra={len(set(names) - set(bindings))}"
                )
            for member in members:
                if not member.isfile() or member.islnk() or member.issym():
                    raise EvidenceError(
                        f"archive member is not a regular file: {member.name}"
                    )
                if member.pax_headers:
                    raise EvidenceError(
                        f"archive member has PAX metadata: {member.name}"
                    )
                if (
                    member.mtime != 0
                    or member.mode != 0o644
                    or member.uid != 0
                    or member.gid != 0
                    or member.uname != ""
                    or member.gname != ""
                ):
                    raise EvidenceError(
                        f"archive metadata is not canonical: {member.name}"
                    )
                archive.fileobj.seek(member.offset)
                header = archive.fileobj.read(512)
                if len(header) != 512 or header[257:263] != b"ustar\0":
                    raise EvidenceError(f"archive member is not ustar: {member.name}")
                expected_hash, expected_size, _ = bindings[member.name]
                if member.size != expected_size:
                    raise EvidenceError(f"archive member size mismatch: {member.name}")
                handle = archive.extractfile(member)
                if handle is None:
                    raise EvidenceError(f"archive member cannot be read: {member.name}")
                raw = handle.read()
                if len(raw) != expected_size or sha256_bytes(raw) != expected_hash:
                    raise EvidenceError(
                        f"archive member content mismatch: {member.name}"
                    )
                documents[member.name] = raw
    except (tarfile.TarError, OSError) as error:
        raise EvidenceError(f"cannot read evidence archive {path}: {error}") from error
    return documents


def shared_base_stem(
    station_id: str, horizon_years: int, replicate: int, legacy_burn: int
) -> str:
    return (
        f"{station_id}-{horizon_years}yr-rep{replicate}-burn{legacy_burn}"
    )


def shared_runspec_bytes(
    station_id: str,
    horizon_years: int,
    replicate: int,
    legacy_burn: int,
    campaign_root: Path,
) -> tuple[bytes, Path, Path]:
    par = campaign_root / ".a5b-input-snapshot/stations" / f"{station_id}.par"
    stem = shared_base_stem(station_id, horizon_years, replicate, legacy_burn)
    base_cli = campaign_root / ".work/faithful-bases" / stem / "base.cli"
    text = "\n".join(
        [
            "cligen_runspec: 1",
            "station:",
            f"  par: {json.dumps(str(par))}",
            "mode: continuous",
            "simulation:",
            "  begin_year: 1",
            f"  years: {horizon_years}",
            "  interpolation: none",
            "rng:",
            f"  burn: {legacy_burn}",
            "generation_profile: faithful_5_32_3",
            "qc_filter: off",
            "output:",
            f"  cli: {json.dumps(str(base_cli))}",
            "  overwrite: false",
            f"  command_echo: {json.dumps(NEUTRAL_BASE_COMMAND_ECHO)}",
            "  quality: false",
            "",
        ]
    )
    return text.encode("utf-8"), par, base_cli


def expected_shared_base_bindings(
    records: list[dict[str, Any]], station_ids: list[str]
) -> dict[str, tuple[str, int, str]]:
    expected_keys = [
        (station_id, horizon, replicate)
        for station_id in station_ids
        for horizon in HORIZONS
        for replicate in range(8)
    ]
    actual_keys = [
        (row.get("station_id"), row.get("horizon_years"), row.get("replicate"))
        for row in records
    ]
    if len(records) != SHARED_BASE_COUNT or actual_keys != expected_keys:
        raise EvidenceError("shared-base record order/closure differs")
    bindings: dict[str, tuple[str, int, str]] = {}
    for row in records:
        require_exact_keys(
            row,
            {
                "station_id",
                "horizon_years",
                "replicate",
                "legacy_burn",
                "runspec",
                "provenance",
                "base_cli_sha256",
                "base_run_id",
                "parameter_set_sha256",
            },
            "shared-base record",
        )
        replicate = REPLICATE_BY_INDEX.get(row["replicate"])
        if replicate is None or row["legacy_burn"] != replicate[1]:
            raise EvidenceError("shared-base burn differs from replicate")
        stem = shared_base_stem(
            row["station_id"],
            row["horizon_years"],
            row["replicate"],
            row["legacy_burn"],
        )
        for field, expected_name in (
            ("runspec", f"runspecs/{stem}.yaml"),
            ("provenance", f"provenance/{stem}.provenance.json"),
        ):
            name, digest, size = member_identity(row[field], f"shared base {field}")
            if name != expected_name or name in bindings:
                raise EvidenceError(f"shared-base {field} member mapping differs")
            bindings[name] = (digest, size, field)
        for field in ("base_cli_sha256", "base_run_id", "parameter_set_sha256"):
            if (
                not isinstance(row[field], str)
                or re.fullmatch(r"[0-9a-f]{64}", row[field]) is None
            ):
                raise EvidenceError(f"shared-base {field} is not SHA-256")
    if len(bindings) != SHARED_BASE_MEMBER_COUNT:
        raise EvidenceError("shared-base archive bindings are not 544 unique members")
    return bindings


def validate_shared_base_provenance(
    provenance: dict[str, Any],
    row: dict[str, Any],
    par: Path,
    base_cli: Path,
    validator: Draft202012Validator,
) -> None:
    label = (
        f"{row['station_id']}/{row['horizon_years']}yr/rep{row['replicate']} "
        "base provenance"
    )
    validate_schema(provenance, validator, label)
    expected_station = {
        "input_schema": {"id": "cligen_par", "version": "5.32.3"},
        "input_sha256": row["par_sha256"],
        "model": "fixed_monthly_5_32_3",
        "parameter_set_sha256": row["parameter_set_sha256"],
        "fit": {"status": "unreported", "id": None},
        "collection": {
            "status": "unreported",
            "name": None,
            "version": None,
            "archive_sha256": None,
        },
        "legacy_source_sha256": row["par_sha256"],
    }
    expected_generation = {
        "profile": "faithful_5_32_3",
        "qc_policy": "off",
        "mode": "continuous",
        "interpolation": "none",
        "rng_scheme": "cligen_randn_5_32_3",
        "burn_per_stream": row["legacy_burn"],
    }
    expected_effective = {
        "cligen_runspec": 1,
        "station": {
            "selector": "par",
            "lexical_path": str(par),
            "input_sha256": row["par_sha256"],
        },
        "mode": "continuous",
        "begin_year": 1,
        "years": row["horizon_years"],
        "interpolation": "none",
        "burn": row["legacy_burn"],
        "generation_profile": "faithful_5_32_3",
        "qc_filter": "off",
        "observed": None,
        "storm": None,
        "output": {
            "cli_lexical_path": str(base_cli),
            "parquet_lexical_path": None,
            "quality": False,
            "overwrite": False,
            "command_echo": f"{NEUTRAL_BASE_COMMAND_ECHO} --qc-filter off",
        },
    }
    expected_artifact = {
        "output_schema": {"id": "org.openwepp.cligen.cli.text", "version": "1"},
        "media_type": "text/plain; charset=utf-8",
        "calendar": "proleptic_gregorian",
        "precipitation_representation": "parametric",
        "numeric_origin": "cligen_f32_daily_row",
        "content_sha256": row["base_cli_sha256"],
    }
    if (
        provenance["provenance_schema_version"] != 1
        or provenance["origin"] != "generated"
        or provenance["station"] != expected_station
        or provenance["generation"] != expected_generation
        or provenance["effective_runspec"] != expected_effective
        or provenance["observed_input"] is not None
        or provenance["actual"]
        != {
            "emitted_day_count": days_in_horizon(row["horizon_years"]),
            "first_date": {"year": 1, "month": 1, "day": 1},
            "last_date": {
                "year": row["horizon_years"],
                "month": 12,
                "day": 31,
            },
            "coverage": "complete_run",
        }
        or provenance["artifact"] != expected_artifact
    ):
        raise EvidenceError(f"{label} semantics differ")
    effective_raw = declaration_order_compact_json_bytes(
        provenance["effective_runspec"]
    )
    if effective_raw != declaration_order_compact_json_bytes(expected_effective):
        raise EvidenceError(f"{label} declaration order differs")
    run_id = sha256_bytes(effective_raw)
    if (
        provenance["effective_runspec_sha256"] != run_id
        or row["base_run_id"] != run_id
    ):
        raise EvidenceError(f"{label} effective-runspec run ID differs")


def verify_shared_bases(
    manifest: dict[str, Any],
    fit_stations: dict[str, FitStation],
    cligen: ResolvedArtifact,
    archive_dir: Path | None,
    root: Path = ROOT,
    lexical_campaign_root: Path | None = None,
) -> dict[tuple[str, int, int], dict[str, Any]]:
    shared = require_dict(manifest["shared_bases"], "shared-base evidence")
    require_exact_keys(
        shared,
        {"format", "artifact", "base_count", "member_count", "records"},
        "shared-base evidence",
    )
    if (
        shared["format"] != "tar+gzip-canonical-v1"
        or shared["base_count"] != SHARED_BASE_COUNT
        or shared["member_count"] != SHARED_BASE_MEMBER_COUNT
    ):
        raise EvidenceError("shared-base archive format/count differs")
    relative = validate_safe_relative_path(
        shared["artifact"]["path"], "shared-base archive path"
    )
    if (
        relative.parent != ARCHIVE_DIRECTORY
        or relative.name != SHARED_BASE_ARCHIVE_NAME
    ):
        raise EvidenceError("shared-base archive deterministic path differs")
    station_ids = manifest["corpus"]["station_ids"]
    records = shared["records"]
    bindings = expected_shared_base_bindings(records, station_ids)
    artifact = resolve_archive_artifact(
        shared["artifact"], "shared-base archive", archive_dir, root
    )
    documents = read_canonical_archive(
        artifact.path, bindings, SHARED_BASE_MEMBER_COUNT
    )
    campaign_root = cligen.path.parent.parent.parent
    if cligen.path != campaign_root / ".a5b-input-snapshot/binaries/cligen":
        raise EvidenceError("cligen binary is outside the deterministic campaign snapshot")
    lexical_root = lexical_campaign_root or campaign_root
    provenance_validator = plain_validator(PROVENANCE_SCHEMA)
    result: dict[tuple[str, int, int], dict[str, Any]] = {}
    for record in records:
        key = (
            record["station_id"],
            record["horizon_years"],
            record["replicate"],
        )
        fit_station = fit_stations[record["station_id"]]
        expected_runspec, lexical_par, lexical_base_cli = shared_runspec_bytes(
            record["station_id"],
            record["horizon_years"],
            record["replicate"],
            record["legacy_burn"],
            lexical_root,
        )
        actual_par = (
            campaign_root
            / ".a5b-input-snapshot/stations"
            / f"{record['station_id']}.par"
        )
        runspec_name, runspec_sha, _ = member_identity(
            record["runspec"], f"{key} shared runspec"
        )
        if (
            documents[runspec_name] != expected_runspec
            or runspec_sha != sha256_bytes(expected_runspec)
            or not actual_par.is_file()
            or sha256_path(actual_par) != fit_station.par_sha256
        ):
            raise EvidenceError(f"{key}: shared runspec or station identity differs")
        provenance_name, provenance_sha, _ = member_identity(
            record["provenance"], f"{key} shared provenance"
        )
        provenance_raw = documents[provenance_name]
        if provenance_sha != sha256_bytes(provenance_raw):
            raise EvidenceError(f"{key}: shared provenance hash differs")
        provenance = require_dict(
            strict_json_bytes(provenance_raw, provenance_name), provenance_name
        )
        validation_row = {**record, "par_sha256": fit_station.par_sha256}
        validate_shared_base_provenance(
            provenance,
            validation_row,
            lexical_par,
            lexical_base_cli,
            provenance_validator,
        )
        result[key] = record
    if len(result) != SHARED_BASE_COUNT:
        raise EvidenceError("verified shared-base count is not 272")
    return result


def validate_plan_document(
    plan: dict[str, Any],
    row: dict[str, Any],
    extension: dict[str, Any],
    validator: Draft202012Validator,
) -> None:
    key = (
        row["candidate_id"],
        row["station_id"],
        row["horizon_years"],
        row["replicate"],
    )
    validate_schema(plan, validator, f"{key} plan")
    _, station_model, profile = CANDIDATE_BY_ID[row["candidate_id"]]
    comparisons = {
        "plan_schema_version": 1,
        "station_id": row["station_id"],
        "station_model": station_model,
        "candidate_profile": profile,
        "extension_seed": row["extension_seed"],
        "coefficient_payload_sha256": extension["diagnostics"]["payload_sha256"],
    }
    if any(plan.get(field) != value for field, value in comparisons.items()):
        raise EvidenceError(f"{key}: plan identity differs")
    states = plan["annual_states"]
    if [state["simulation_year"] for state in states] != list(range(1, 129)):
        raise EvidenceError(f"{key}: annual-state years are not contiguous 1..128")
    if plan["state_table_sha256"] != sha256_bytes(compact_json_bytes(states)):
        raise EvidenceError(f"{key}: annual-state table hash differs")
    normalization = plan["normalization"]
    if normalization != {
        "fixed_years": 128,
        "precipitation_clip_count": normalization["precipitation_clip_count"],
        "temperature_centered": True,
    }:
        raise EvidenceError(f"{key}: plan normalization identity differs")
    precipitation_bound_count = 0
    for month in range(12):
        precipitation_values = [state["precip_factor"][month] for state in states]
        precipitation_sum = math.fsum(precipitation_values)
        tmax_mean = math.fsum(state["tmax_delta_c"][month] for state in states) / 128.0
        tmin_mean = math.fsum(state["tmin_delta_c"][month] for state in states) / 128.0
        if precipitation_sum != 128.0:
            raise EvidenceError(f"{key}: precipitation normalization differs")
        precipitation_bound_count += sum(
            value == 0.05 or value == 20.0 for value in precipitation_values
        )
        if not math.isclose(tmax_mean, 0.0, rel_tol=0.0, abs_tol=2e-15):
            raise EvidenceError(f"{key}: Tmax centering differs")
        if not math.isclose(tmin_mean, 0.0, rel_tol=0.0, abs_tol=2e-15):
            raise EvidenceError(f"{key}: Tmin centering differs")
    if normalization["precipitation_clip_count"] != precipitation_bound_count:
        raise EvidenceError(f"{key}: precipitation bound-intervention count differs")
    is_counterfactual = row["candidate_id"] == "precip_counterfactual"
    if is_counterfactual != ("counterfactual" in plan):
        raise EvidenceError(f"{key}: counterfactual plan presence differs")
    if is_counterfactual:
        counterfactual = plan["counterfactual"]
        payload = extension["payload"]
        if (
            counterfactual["second_order_prob"]
            != payload["second_order_wet_probabilities"]
            or counterfactual["amount_rank_rho"] != payload["amount_rank_rho"]
        ):
            raise EvidenceError(f"{key}: counterfactual coefficients differ")
        expected_state = domain_sha256(
            COUNTERFACTUAL_DOMAIN,
            row["station_id"],
            profile,
            row["extension_seed"],
        )[:16]
        if counterfactual["rng_state"] != f"0x{expected_state}":
            raise EvidenceError(f"{key}: counterfactual RNG state differs")


def validate_quality_document(
    report: dict[str, Any],
    row: dict[str, Any],
    fit_station: FitStation,
    validator: Draft202012Validator | None,
) -> None:
    key = (
        row["candidate_id"],
        row["station_id"],
        row["horizon_years"],
        row["replicate"],
    )
    if validator is not None:
        validate_schema(report, validator, f"{key} quality report")
    if (
        report.get("quality_report_schema_version") != 2
        or report.get("metrics_version") != 3
    ):
        raise EvidenceError(f"{key}: quality report revision differs")
    if report.get("process") is not None:
        raise EvidenceError(f"{key}: post-hoc quality process must be null")
    identity = require_dict(report.get("identity"), f"{key} quality identity")
    if identity.get("provenance") is not None:
        raise EvidenceError(f"{key}: post-hoc quality provenance must be null")
    content = require_dict(identity.get("content"), f"{key} quality content")
    if content.get("cli_sha256") != row["candidate_cli_sha256"]:
        raise EvidenceError(f"{key}: quality/candidate CLI hash differs")
    if content.get("station_source_sha256") != fit_station.par_sha256:
        raise EvidenceError(f"{key}: quality/base station source hash differs")
    horizon = row["horizon_years"]
    if (
        content.get("years") != horizon
        or content.get("span") != [1, horizon]
        or content.get("days") != days_in_horizon(horizon)
    ):
        raise EvidenceError(f"{key}: quality report period differs")
    for field in ("par_convergence", "interannual", "covariation", "tails"):
        if report.get(field) is None:
            raise EvidenceError(
                f"{key}: quality report omits required metric group {field}"
            )


def validate_overlay_diagnostics(
    diagnostics: dict[str, Any],
    row: dict[str, Any],
    record: dict[str, Any],
    plan: dict[str, Any],
) -> None:
    key = (
        row["candidate_id"],
        row["station_id"],
        row["horizon_years"],
        row["replicate"],
    )
    require_exact_keys(diagnostics, DIAGNOSTIC_KEYS, f"{key} overlay diagnostics")
    _, station_model, profile = CANDIDATE_BY_ID[row["candidate_id"]]
    plan_name, plan_sha, _ = member_identity(row["plan"], f"{key} plan")
    del plan_name
    comparisons = {
        "diagnostics_schema_version": 1,
        "station_id": row["station_id"],
        "station_model": station_model,
        "candidate_profile": profile,
        "extension_seed": row["extension_seed"],
        "coefficient_payload_sha256": record["inputs"]["coefficient_payload_sha256"],
        "state_table_sha256": plan["state_table_sha256"],
        "input_runspec_sha256": record["inputs"]["base_runspec_sha256"],
        "plan_sha256": plan_sha,
        "faithful_cli_sha256": record["inputs"]["base_cli_sha256"],
        "output_cli_sha256": row["candidate_cli_sha256"],
        "row_count": days_in_horizon(row["horizon_years"]),
        "plan_state_years": 128,
        "consumed_prefix_years": row["horizon_years"],
    }
    if any(diagnostics.get(field) != value for field, value in comparisons.items()):
        raise EvidenceError(f"{key}: overlay diagnostics identity/period differs")
    if diagnostics["wet_days_before"] != diagnostics["wet_days_after"]:
        raise EvidenceError(f"{key}: overlay changed wet-day count")
    execution = record["execution"]
    if (
        diagnostics["temperature_order_repairs"]
        != execution["temperature_order_repair_count"]
    ):
        raise EvidenceError(f"{key}: temperature repair count differs")
    if diagnostics["dewpoint_caps"] != execution["dewpoint_cap_count"]:
        raise EvidenceError(f"{key}: dewpoint cap count differs")
    if diagnostics["counterfactual_months"] != execution["counterfactual_month_count"]:
        raise EvidenceError(f"{key}: counterfactual month count differs")
    is_counterfactual = row["candidate_id"] == "precip_counterfactual"
    if diagnostics["counterfactual_applied"] is not is_counterfactual:
        raise EvidenceError(f"{key}: counterfactual diagnostic presence differs")
    expected_months = row["horizon_years"] * 12 if is_counterfactual else 0
    if diagnostics["counterfactual_months"] != expected_months:
        raise EvidenceError(f"{key}: counterfactual month total differs")
    if is_counterfactual:
        value = diagnostics["counterfactual_rng_final_state"]
        if not isinstance(value, str) or re.fullmatch(r"0x[0-9a-f]{16}", value) is None:
            raise EvidenceError(f"{key}: counterfactual final RNG state differs")
    elif diagnostics["counterfactual_rng_final_state"] is not None:
        raise EvidenceError(f"{key}: non-counterfactual carries final RNG state")
    adjustments = diagnostics["precipitation_factor_adjustments"]
    if not isinstance(adjustments, list) or len(adjustments) != row["horizon_years"] * 12:
        raise EvidenceError(f"{key}: precipitation adjustment table differs")
    adjusted_count = 0
    for index, adjustment_value in enumerate(adjustments):
        adjustment = require_dict(
            adjustment_value, f"{key} precipitation adjustment {index}"
        )
        require_exact_keys(
            adjustment,
            {
                "simulation_year",
                "month",
                "requested_factor",
                "effective_factor",
                "base_max_precip_mm",
                "render_limit_mm",
                "adjusted",
            },
            f"{key} precipitation adjustment {index}",
        )
        year = index // 12 + 1
        month = index % 12 + 1
        requested = adjustment["requested_factor"]
        effective = adjustment["effective_factor"]
        base_max = adjustment["base_max_precip_mm"]
        render_limit = adjustment["render_limit_mm"]
        if (
            adjustment["simulation_year"] != year
            or adjustment["month"] != month
            or not isinstance(adjustment["adjusted"], bool)
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in (requested, effective, base_max, render_limit)
            )
            or requested
            != plan["annual_states"][year - 1]["precip_factor"][month - 1]
            or requested <= 0.0
            or effective <= 0.0
            or base_max < 0.0
            or render_limit != MAX_RENDERABLE_PRECIP_MM
        ):
            raise EvidenceError(
                f"{key}: precipitation adjustment identity differs at "
                f"year {year} month {month}"
            )
        expected_effective = (
            requested
            if base_max == 0.0
            else min(requested, render_limit / base_max)
        )
        expected_adjusted = expected_effective < requested
        if (
            effective != expected_effective
            or adjustment["adjusted"] is not expected_adjusted
            or effective * base_max > math.nextafter(render_limit, math.inf)
        ):
            raise EvidenceError(
                f"{key}: precipitation adjustment arithmetic differs at "
                f"year {year} month {month}"
            )
        adjusted_count += int(expected_adjusted)
    if (
        diagnostics["precipitation_render_limit_adjustments"] != adjusted_count
        or execution["precipitation_render_limit_adjustment_count"] != adjusted_count
    ):
        raise EvidenceError(f"{key}: precipitation adjustment count differs")


def run_stem(row: dict[str, Any]) -> str:
    return (
        f"{row['station_id']}-{row['candidate_id']}-{row['horizon_years']}yr-"
        f"rep{row['replicate']}-burn{row['legacy_burn']}"
    )


def expected_cli_path(row: dict[str, Any], candidate_cli_dir: Path) -> Path:
    return candidate_cli_dir / row["candidate_id"] / f"{run_stem(row)}.cli"


def root_relative(path: Path, root: Path, label: str) -> str:
    resolved = path.resolve(strict=False)
    root_resolved = root.resolve(strict=True)
    if not resolved.is_relative_to(root_resolved):
        raise EvidenceError(f"{label} must remain inside the repository")
    return resolved.relative_to(root_resolved).as_posix()


def validate_run_record(
    record: dict[str, Any],
    row: dict[str, Any],
    manifest: dict[str, Any],
    fit_station: FitStation,
    plan: dict[str, Any],
    cligen: ResolvedArtifact,
    overlay: ResolvedArtifact,
    validator: Draft202012Validator | None,
    candidate_cli_dir: Path | None,
    root: Path,
) -> None:
    key = (
        row["candidate_id"],
        row["station_id"],
        row["horizon_years"],
        row["replicate"],
    )
    if validator is not None:
        validate_schema(record, validator, f"{key} run record")
    candidate_id, station_model, profile = CANDIDATE_BY_ID[row["candidate_id"]]
    expected_matrix = {
        "station_id": row["station_id"],
        "regime": row["regime"],
        "candidate_id": candidate_id,
        "station_model": station_model,
        "generation_profile": profile,
        "horizon_years": row["horizon_years"],
        "replicate": row["replicate"],
        "legacy_burn": row["legacy_burn"],
        "extension_seed": row["extension_seed"],
    }
    if record.get("matrix") != expected_matrix:
        raise EvidenceError(f"{key}: run-record matrix differs from index")
    expected_contracts = {
        name: manifest["contracts"][name] for name in RUN_CONTRACT_KEYS
    }
    if record.get("contracts") != expected_contracts:
        raise EvidenceError(f"{key}: run-record contracts differ from evidence")
    inputs = record["inputs"]
    if (
        inputs["corpus_schema_version"] != manifest["corpus"]["schema_version"]
        or inputs["corpus_content_sha256"] != manifest["corpus"]["content_sha256"]
    ):
        raise EvidenceError(f"{key}: run-record corpus differs")
    legacy_name, legacy_sha, legacy_bytes = member_identity(
        inputs["legacy_par"], f"{key} legacy .par"
    )
    if legacy_sha != fit_station.par_sha256:
        raise EvidenceError(f"{key}: run-record .par hash differs from fit")
    legacy_record = {"path": legacy_name, "sha256": legacy_sha, "bytes": legacy_bytes}
    resolve_artifact(legacy_record, f"{key} legacy .par", root)
    if inputs["augmented_station"] != artifact_as_member(fit_station.bundle_artifact):
        raise EvidenceError(f"{key}: run-record station bundle differs")
    extension = fit_station.extensions[candidate_id]
    if (
        inputs["coefficient_payload_sha256"]
        != extension["diagnostics"]["payload_sha256"]
        or inputs["fit_identity_sha256"] != extension["fit_identity_sha256"]
    ):
        raise EvidenceError(f"{key}: run-record fit identity differs")
    if inputs["plan"] != row["plan"]:
        raise EvidenceError(f"{key}: run-record plan identity differs")

    runtime = record["runtime"]
    if runtime["cligen_binary"] != artifact_as_member(cligen.record):
        raise EvidenceError(f"{key}: run-record cligen binary differs")
    if runtime["overlay_binary"] != artifact_as_member(overlay.record):
        raise EvidenceError(f"{key}: run-record overlay binary differs")
    if runtime["implementation_commit"] != manifest["build"]["implementation_commit"]:
        raise EvidenceError(f"{key}: implementation commit differs")
    expected_domain = domain_sha256(
        MAIN_DOMAIN, row["station_id"], profile, row["extension_seed"]
    )
    if runtime["extension_domain_sha256"] != expected_domain:
        raise EvidenceError(f"{key}: extension RNG domain differs")

    outputs = record["outputs"]
    cli_name, cli_sha, cli_bytes = member_identity(
        outputs["candidate_cli"], f"{key} candidate CLI"
    )
    if (
        cli_sha != row["candidate_cli_sha256"]
        or cli_bytes != row["candidate_cli_bytes"]
    ):
        raise EvidenceError(f"{key}: candidate CLI identity differs")
    cli_path = PurePosixPath(cli_name)
    if cli_path.name != f"{run_stem(row)}.cli" or cli_path.parent.name != candidate_id:
        raise EvidenceError(f"{key}: candidate CLI path convention differs")
    if candidate_cli_dir is not None:
        expected_path = expected_cli_path(row, candidate_cli_dir)
        if cli_name != root_relative(expected_path, root, "candidate CLI"):
            raise EvidenceError(f"{key}: candidate CLI directory/path differs")
    if outputs["quality_report"] != row["quality_report"]:
        raise EvidenceError(f"{key}: run-record quality identity differs")
    if outputs["overlay_diagnostics"] != row["overlay_diagnostics"]:
        raise EvidenceError(f"{key}: run-record diagnostics identity differs")
    execution = record["execution"]
    if (
        execution["precipitation_clip_count"]
        != plan["normalization"]["precipitation_clip_count"]
    ):
        raise EvidenceError(f"{key}: precipitation clip count differs")


def verify_candidate_cli_state(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    records: dict[tuple[str, str, int, int], dict[str, Any]],
    candidate_cli_dir: Path | None,
    root: Path,
) -> None:
    removed = manifest["execution"]["candidate_cli_bytes_removed_after_wepp"]
    if not removed and candidate_cli_dir is None:
        raise EvidenceError(
            "--candidate-cli-dir is required while candidate CLIs are retained"
        )
    indexed_roots: set[str] = set()
    for row in rows:
        key = (
            row["candidate_id"],
            row["station_id"],
            row["horizon_years"],
            row["replicate"],
        )
        record = records[key]
        name, digest, size = member_identity(
            record["outputs"]["candidate_cli"], f"{key} candidate CLI"
        )
        member_path = PurePosixPath(name)
        indexed_root = member_path.parent.parent
        if indexed_root == PurePosixPath("."):
            raise EvidenceError(f"{key}: candidate CLI index omits its root directory")
        indexed_roots.add(indexed_root.as_posix())
        if candidate_cli_dir is None:
            continue
        path = expected_cli_path(row, candidate_cli_dir)
        if removed:
            if path.exists():
                raise EvidenceError(
                    f"{key}: candidate CLI remains after declared removal"
                )
            continue
        if not path.is_file():
            raise EvidenceError(f"{key}: retained candidate CLI is missing")
        if root_relative(path, root, "candidate CLI") != name:
            raise EvidenceError(f"{key}: retained candidate CLI path differs")
        if path.stat().st_size != size or sha256_path(path) != digest:
            raise EvidenceError(f"{key}: retained candidate CLI identity differs")
    if len(indexed_roots) != 1:
        raise EvidenceError("candidate CLI index does not share one deterministic root")
    if removed and candidate_cli_dir is None:
        indexed_relative = validate_safe_relative_path(
            next(iter(indexed_roots)), "indexed candidate CLI root"
        )
        inferred_root = root.joinpath(*indexed_relative.parts).resolve(strict=False)
        if not inferred_root.is_relative_to(root.resolve(strict=True)):
            raise EvidenceError("indexed candidate CLI root escapes the repository")
        for row in rows:
            key = (
                row["candidate_id"],
                row["station_id"],
                row["horizon_years"],
                row["replicate"],
            )
            record = records[key]
            name, _, _ = member_identity(
                record["outputs"]["candidate_cli"], f"{key} candidate CLI"
            )
            path = expected_cli_path(row, inferred_root)
            if root_relative(path, root, "candidate CLI") != name:
                raise EvidenceError(f"{key}: inferred candidate CLI path differs")
            if path.exists():
                raise EvidenceError(
                    f"{key}: candidate CLI remains after declared removal"
                )
    if candidate_cli_dir is not None:
        supplied_root = root_relative(candidate_cli_dir, root, "candidate CLI root")
        if indexed_roots != {supplied_root}:
            raise EvidenceError(
                "candidate CLI index root differs from --candidate-cli-dir"
            )


def verify_archives(
    manifest: dict[str, Any],
    fit_stations: dict[str, FitStation],
    shared_bases: dict[tuple[str, int, int], dict[str, Any]],
    expected_par_aggregate_sha256: str,
    cligen: ResolvedArtifact,
    overlay: ResolvedArtifact,
    run_validator: Draft202012Validator | None,
    plan_validator: Draft202012Validator | None,
    report_validator: Draft202012Validator | None,
    candidate_cli_dir: Path | None,
    archive_dir: Path | None,
    root: Path = ROOT,
) -> dict[tuple[str, str, int, int], dict[str, Any]]:
    archive_rows = manifest["archives"]
    if [row["candidate_id"] for row in archive_rows] != [
        candidate[0] for candidate in CANDIDATES
    ]:
        raise EvidenceError("candidate archive order differs from frozen order")
    rows_by_candidate = {
        candidate[0]: [
            row for row in manifest["runs"] if row["candidate_id"] == candidate[0]
        ]
        for candidate in CANDIDATES
    }
    records: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    plan_items: list[tuple[str, bytes]] = []
    base_identity: dict[tuple[str, int, int], tuple[Any, ...]] = {}
    station_legacy_identity: dict[str, tuple[str, str, int]] = {}
    station_parameter_sets: dict[str, str] = {}
    for archive_row in archive_rows:
        candidate_id = archive_row["candidate_id"]
        if archive_row["format"] != "tar+gzip-canonical-v1":
            raise EvidenceError(f"{candidate_id}: archive format differs")
        if archive_row["member_count"] != MEMBERS_PER_CANDIDATE:
            raise EvidenceError(f"{candidate_id}: archive member count is not 952")
        archive_relative = validate_safe_relative_path(
            archive_row["artifact"]["path"], f"{candidate_id} archive path"
        )
        if archive_relative.parent != ARCHIVE_DIRECTORY:
            raise EvidenceError(f"{candidate_id}: archive is outside artifacts/climate")
        if not archive_relative.name.endswith(".tar.gz"):
            raise EvidenceError(f"{candidate_id}: archive filename is not .tar.gz")
        if archive_relative.name != f"candidate-evidence-{candidate_id}-v1.tar.gz":
            raise EvidenceError(f"{candidate_id}: archive filename differs")
        artifact = resolve_archive_artifact(
            archive_row["artifact"], f"{candidate_id} archive", archive_dir, root
        )
        rows = rows_by_candidate[candidate_id]
        bindings = expected_archive_bindings(candidate_id, rows)
        documents = read_canonical_archive(
            artifact.path, bindings, archive_row["member_count"]
        )
        plan_cache: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = (
                candidate_id,
                row["station_id"],
                row["horizon_years"],
                row["replicate"],
            )
            fit_station = fit_stations[row["station_id"]]
            extension = fit_station.extensions[candidate_id]
            plan_name = row["plan"]["member"]
            plan = plan_cache.get(plan_name)
            if plan is None:
                plan_items.append((plan_name, documents[plan_name]))
                plan = require_dict(
                    strict_json_bytes(documents[plan_name], plan_name), plan_name
                )
                plan_cache[plan_name] = plan
            if plan_validator is not None:
                validate_plan_document(plan, row, extension, plan_validator)
            else:
                # Synthetic self-tests still exercise all cross-field semantics.
                validate_plan_document(
                    plan, row, extension, plain_validator(PLAN_SCHEMA)
                )

            record_name = row["run_record"]["member"]
            record = require_dict(
                strict_json_bytes(documents[record_name], record_name), record_name
            )
            validate_run_record(
                record,
                row,
                manifest,
                fit_station,
                plan,
                cligen,
                overlay,
                run_validator,
                candidate_cli_dir,
                root,
            )
            records[key] = record

            report_name = row["quality_report"]["member"]
            report = require_dict(
                strict_json_bytes(documents[report_name], report_name), report_name
            )
            validate_quality_document(report, row, fit_station, report_validator)
            parameter_set = report["identity"]["content"].get(
                "station_parameter_set_sha256"
            )
            prior_parameter_set = station_parameter_sets.setdefault(
                row["station_id"], parameter_set
            )
            if prior_parameter_set != parameter_set:
                raise EvidenceError(f"{key}: station parameter-set hash differs")

            diagnostics_name = row["overlay_diagnostics"]["member"]
            diagnostics = require_dict(
                strict_json_bytes(documents[diagnostics_name], diagnostics_name),
                diagnostics_name,
            )
            validate_overlay_diagnostics(diagnostics, row, record, plan)

            base_key = (row["station_id"], row["horizon_years"], row["replicate"])
            shared_base = shared_bases[base_key]
            legacy_identity = member_identity(
                record["inputs"]["legacy_par"], "legacy .par"
            )
            prior_legacy = station_legacy_identity.setdefault(
                row["station_id"], legacy_identity
            )
            if prior_legacy != legacy_identity:
                raise EvidenceError(
                    f"{key}: legacy .par identity differs within station"
                )
            base_value = (
                record["inputs"]["base_runspec_sha256"],
                record["inputs"]["base_provenance_sha256"],
                record["inputs"]["base_cli_sha256"],
                record["inputs"]["base_run_id"],
                legacy_identity,
            )
            if (
                record["inputs"]["base_runspec_sha256"]
                != shared_base["runspec"]["sha256"]
                or record["inputs"]["base_provenance_sha256"]
                != shared_base["provenance"]["sha256"]
                or record["inputs"]["base_cli_sha256"]
                != shared_base["base_cli_sha256"]
                or record["inputs"]["base_run_id"] != shared_base["base_run_id"]
                or parameter_set != shared_base["parameter_set_sha256"]
            ):
                raise EvidenceError(f"{key}: run differs from shared-base evidence")
            prior_base = base_identity.setdefault(base_key, base_value)
            if prior_base != base_value:
                raise EvidenceError(
                    f"{key}: faithful base identity differs across candidates"
                )
        if len(plan_cache) != PLANS_PER_CANDIDATE:
            raise EvidenceError(f"{candidate_id}: parsed plan count is not 136")
    if (
        len(plan_items) != 952
        or aggregate_named_bytes(plan_items)
        != manifest["build"]["plan_preflight"]["aggregate_sha256"]
    ):
        raise EvidenceError("archive plans differ from the pre-target plan preflight")
    if len(records) != EXPECTED_RUNS:
        raise EvidenceError("verified run-record count is not 1,904")
    if len(base_identity) != 17 * 2 * 8:
        raise EvidenceError("faithful base identity key count is not 272")
    if len(station_legacy_identity) != 17:
        raise EvidenceError("legacy .par station identity count is not 17")
    par_items: list[tuple[str, bytes]] = []
    for station_id in fit_stations:
        name, digest, size = station_legacy_identity[station_id]
        artifact = resolve_artifact(
            {"path": name, "sha256": digest, "bytes": size},
            f"{station_id} aggregate legacy .par",
            root,
        )
        par_items.append((station_id, artifact.path.read_bytes()))
    if aggregate_named_bytes(par_items) != expected_par_aggregate_sha256:
        raise EvidenceError("fit/runtime station-parameter aggregate differs")
    verify_candidate_cli_state(
        manifest,
        manifest["runs"],
        records,
        candidate_cli_dir,
        root,
    )
    return records


def verify_execution(manifest: dict[str, Any]) -> None:
    execution = manifest["execution"]
    if execution["failures"] != []:
        raise EvidenceError("sealed evidence records execution failures")
    if not isinstance(execution["workers"], int) or execution["workers"] < 1:
        raise EvidenceError("execution worker count differs")
    wall = execution["wall_time_seconds"]
    if (
        isinstance(wall, bool)
        or not isinstance(wall, (int, float))
        or not math.isfinite(wall)
        or wall < 0
    ):
        raise EvidenceError("execution wall time is invalid")
    # The schema's format keyword is annotation-only without a format checker;
    # retain a strict UTC lexical gate here.
    timestamp = re.compile(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z$"
    )
    if (
        timestamp.fullmatch(execution["started_utc"]) is None
        or timestamp.fullmatch(execution["completed_utc"]) is None
    ):
        raise EvidenceError("execution timestamps are not canonical UTC")
    if execution["completed_utc"] < execution["started_utc"]:
        raise EvidenceError("execution completion precedes start")


def normalized_cli_directory(value: Path | None, root: Path = ROOT) -> Path | None:
    if value is None:
        return None
    path = value if value.is_absolute() else root / value
    resolved = path.resolve(strict=False)
    if not resolved.is_relative_to(root.resolve(strict=True)):
        raise EvidenceError("candidate CLI directory must be inside the repository")
    return resolved


def normalized_archive_directory(value: Path | None, root: Path = ROOT) -> Path | None:
    if value is None:
        return None
    path = value if value.is_absolute() else root / value
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root.resolve(strict=True)) or not resolved.is_dir():
        raise EvidenceError("archive staging directory must be inside the repository")
    return resolved


def verify(
    manifest_path: Path,
    candidate_cli_dir: Path | None,
    archive_dir: Path | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    evidence_validator = plain_validator(EVIDENCE_SCHEMA)
    run_validator = plain_validator(RUN_SCHEMA)
    plan_validator = plain_validator(PLAN_SCHEMA)
    station_validator = bundle_validator()
    report_validator = quality_validator()
    manifest = require_dict(strict_json(manifest_path), "candidate evidence manifest")
    validate_schema(manifest, evidence_validator, "candidate evidence manifest")
    if (
        manifest["candidate_evidence_manifest_version"] != 1
        or manifest["status"] != "sealed"
    ):
        raise EvidenceError("candidate evidence is not sealed revision 1")
    verify_contracts(manifest, root)
    station_ids, regimes = observed_station_catalog(manifest, root)
    verify_matrix(manifest, station_ids, regimes)
    cligen, overlay = verify_build_artifacts(manifest, root)
    fit_stations, expected_par_aggregate = verify_fit_artifacts(
        manifest, station_ids, station_validator, cligen, root
    )
    cli_dir = normalized_cli_directory(candidate_cli_dir, root)
    archive_root = normalized_archive_directory(archive_dir, root)
    shared_bases = verify_shared_bases(
        manifest, fit_stations, cligen, archive_root, root
    )
    records = verify_archives(
        manifest,
        fit_stations,
        shared_bases,
        expected_par_aggregate,
        cligen,
        overlay,
        run_validator,
        plan_validator,
        report_validator,
        cli_dir,
        archive_root,
        root,
    )
    verify_execution(manifest)
    return {
        "status": "passed",
        "manifest_sha256": sha256_path(manifest_path),
        "stations": len(station_ids),
        "candidates": len(CANDIDATES),
        "runs": len(records),
        "archives": len(manifest["archives"]),
        "shared_bases": len(shared_bases),
        "archive_members": sum(row["member_count"] for row in manifest["archives"]),
        "candidate_cli_bytes_removed_after_wepp": manifest["execution"][
            "candidate_cli_bytes_removed_after_wepp"
        ],
    }


def canonical_archive_bytes(
    members: list[tuple[str, bytes]],
    *,
    gzip_mtime: int = 0,
    mode_override: int | None = None,
) -> bytes:
    tar_buffer = io.BytesIO()
    with tarfile.open(
        fileobj=tar_buffer, mode="w", format=tarfile.USTAR_FORMAT
    ) as archive:
        for name, raw in sorted(members, key=lambda item: item[0]):
            info = tarfile.TarInfo(name)
            info.size = len(raw)
            info.mode = 0o644 if mode_override is None else mode_override
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(raw))
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        mtime=gzip_mtime,
        fileobj=output,
    ) as compressed:
        compressed.write(tar_buffer.getvalue())
    return output.getvalue()


def synthetic_plan(
    candidate_id: str,
    station_id: str,
    extension_seed: str,
    payload_sha: str,
) -> dict[str, Any]:
    _, station_model, profile = CANDIDATE_BY_ID[candidate_id]
    states = [
        {
            "simulation_year": year,
            "precip_factor": [1.0] * 12,
            "tmax_delta_c": [0.0] * 12,
            "tmin_delta_c": [0.0] * 12,
        }
        for year in range(1, 129)
    ]
    result: dict[str, Any] = {
        "plan_schema_version": 1,
        "station_id": station_id,
        "station_model": station_model,
        "candidate_profile": profile,
        "extension_seed": extension_seed,
        "coefficient_payload_sha256": payload_sha,
        "state_table_sha256": sha256_bytes(compact_json_bytes(states)),
        "normalization": {
            "fixed_years": 128,
            "precipitation_clip_count": 0,
            "temperature_centered": True,
        },
        "annual_states": states,
    }
    if candidate_id == "precip_counterfactual":
        result["counterfactual"] = {
            "second_order_prob": [[0.5] * 4 for _ in range(12)],
            "amount_rank_rho": [0.0] * 12,
            "rng_state": "0x"
            + domain_sha256(COUNTERFACTUAL_DOMAIN, station_id, profile, extension_seed)[
                :16
            ],
        }
    return result


def synthetic_quality(
    row: dict[str, Any], par_sha: str, parameter_sha: str
) -> dict[str, Any]:
    years = row["horizon_years"]
    return {
        "quality_report_schema_version": 2,
        "metrics_version": 3,
        "identity": {
            "content": {
                "tool": "synthetic-post-hoc-quality",
                "station_model": "fixed_monthly_5_32_3",
                "station_parameter_set_sha256": parameter_sha,
                "station_source_sha256": par_sha,
                "cli_sha256": row["candidate_cli_sha256"],
                "days": days_in_horizon(years),
                "years": years,
                "span": [1, years],
            },
            "provenance": None,
        },
        "par_convergence": {},
        "interannual": {},
        "covariation": {},
        "tails": {},
        "process": None,
    }


def synthetic_base_provenance(
    station_id: str,
    horizon_years: int,
    replicate: int,
    legacy_burn: int,
    par_sha256: str,
    parameter_set_sha256: str,
    base_cli_sha256: str,
    campaign_root: Path,
) -> tuple[dict[str, Any], str]:
    _, par, base_cli = shared_runspec_bytes(
        station_id,
        horizon_years,
        replicate,
        legacy_burn,
        campaign_root,
    )
    effective = {
        "cligen_runspec": 1,
        "station": {
            "selector": "par",
            "lexical_path": str(par),
            "input_sha256": par_sha256,
        },
        "mode": "continuous",
        "begin_year": 1,
        "years": horizon_years,
        "interpolation": "none",
        "burn": legacy_burn,
        "generation_profile": "faithful_5_32_3",
        "qc_filter": "off",
        "observed": None,
        "storm": None,
        "output": {
            "cli_lexical_path": str(base_cli),
            "parquet_lexical_path": None,
            "quality": False,
            "overwrite": False,
            "command_echo": f"{NEUTRAL_BASE_COMMAND_ECHO} --qc-filter off",
        },
    }
    run_id = sha256_bytes(declaration_order_compact_json_bytes(effective))
    return (
        {
            "provenance_schema_version": 1,
            "producer": {
                "name": "cligen-rs",
                "version": "synthetic",
                "repository": "https://github.com/rogerlew/cligen-rs",
                "implementation_revision": None,
            },
            "origin": "generated",
            "source_authority": {
                "cligen_version": "5.32.3",
                "reference_tree_sha256": (
                    "24966eaed920c2b9fd0b8a9ab1242b32053a730f0691a6a18dc4f44a3096bd5b"
                ),
            },
            "station": {
                "input_schema": {"id": "cligen_par", "version": "5.32.3"},
                "input_sha256": par_sha256,
                "model": "fixed_monthly_5_32_3",
                "parameter_set_sha256": parameter_set_sha256,
                "fit": {"status": "unreported", "id": None},
                "collection": {
                    "status": "unreported",
                    "name": None,
                    "version": None,
                    "archive_sha256": None,
                },
                "legacy_source_sha256": par_sha256,
            },
            "generation": {
                "profile": "faithful_5_32_3",
                "qc_policy": "off",
                "mode": "continuous",
                "interpolation": "none",
                "rng_scheme": "cligen_randn_5_32_3",
                "burn_per_stream": legacy_burn,
            },
            "effective_runspec": effective,
            "effective_runspec_sha256": run_id,
            "observed_input": None,
            "actual": {
                "emitted_day_count": days_in_horizon(horizon_years),
                "first_date": {"year": 1, "month": 1, "day": 1},
                "last_date": {"year": horizon_years, "month": 12, "day": 31},
                "coverage": "complete_run",
            },
            "artifact": {
                "output_schema": {
                    "id": "org.openwepp.cligen.cli.text",
                    "version": "1",
                },
                "media_type": "text/plain; charset=utf-8",
                "calendar": "proleptic_gregorian",
                "precipitation_representation": "parametric",
                "numeric_origin": "cligen_f32_daily_row",
                "content_sha256": base_cli_sha256,
            },
        },
        run_id,
    )


def synthetic_overlay_diagnostics(
    row: dict[str, Any],
    plan: dict[str, Any],
    plan_raw: bytes,
    runspec_sha: str,
    base_cli_sha: str,
    payload_sha: str,
) -> dict[str, Any]:
    _, station_model, profile = CANDIDATE_BY_ID[row["candidate_id"]]
    counterfactual = row["candidate_id"] == "precip_counterfactual"
    return {
        "diagnostics_schema_version": 1,
        "station_id": row["station_id"],
        "station_model": station_model,
        "candidate_profile": profile,
        "extension_seed": row["extension_seed"],
        "coefficient_payload_sha256": payload_sha,
        "state_table_sha256": plan["state_table_sha256"],
        "input_runspec_sha256": runspec_sha,
        "plan_sha256": sha256_bytes(plan_raw),
        "faithful_cli_sha256": base_cli_sha,
        "output_cli_sha256": row["candidate_cli_sha256"],
        "row_count": days_in_horizon(row["horizon_years"]),
        "plan_state_years": 128,
        "consumed_prefix_years": row["horizon_years"],
        "wet_days_before": 10,
        "wet_days_after": 10,
        "temperature_order_repairs": 0,
        "dewpoint_caps": 0,
        "counterfactual_applied": counterfactual,
        "counterfactual_months": row["horizon_years"] * 12 if counterfactual else 0,
        "relocated_wet_days": 0,
        "reassigned_storm_tuples": 0,
        "counterfactual_rng_final_state": (
            "0x0000000000000001" if counterfactual else None
        ),
        "precipitation_render_limit_adjustments": 0,
        "precipitation_factor_adjustments": [
            {
                "simulation_year": year,
                "month": month,
                "requested_factor": 1.0,
                "effective_factor": 1.0,
                "base_max_precip_mm": 1.0,
                "render_limit_mm": MAX_RENDERABLE_PRECIP_MM,
                "adjusted": False,
            }
            for year in range(1, row["horizon_years"] + 1)
            for month in range(1, 13)
        ],
    }


def synthetic_run_record(
    row: dict[str, Any],
    manifest: dict[str, Any],
    fit_station: FitStation,
    extension: dict[str, Any],
    plan_identity: dict[str, Any],
    quality_identity: dict[str, Any],
    diagnostics_identity: dict[str, Any],
    cli_identity: dict[str, Any],
    cligen: ResolvedArtifact,
    overlay: ResolvedArtifact,
    legacy_identity: dict[str, Any],
    runspec_sha: str,
    provenance_sha: str,
    base_cli_sha: str,
    base_run_id: str,
) -> dict[str, Any]:
    candidate_id, station_model, profile = CANDIDATE_BY_ID[row["candidate_id"]]
    counterfactual = candidate_id == "precip_counterfactual"
    return {
        "run_record_schema_version": 1,
        "matrix": {
            "station_id": row["station_id"],
            "regime": row["regime"],
            "candidate_id": candidate_id,
            "station_model": station_model,
            "generation_profile": profile,
            "horizon_years": row["horizon_years"],
            "replicate": row["replicate"],
            "legacy_burn": row["legacy_burn"],
            "extension_seed": row["extension_seed"],
        },
        "contracts": {key: manifest["contracts"][key] for key in RUN_CONTRACT_KEYS},
        "inputs": {
            "corpus_schema_version": 1,
            "corpus_content_sha256": manifest["corpus"]["content_sha256"],
            "legacy_par": legacy_identity,
            "augmented_station": artifact_as_member(fit_station.bundle_artifact),
            "coefficient_payload_sha256": extension["diagnostics"]["payload_sha256"],
            "fit_identity_sha256": extension["fit_identity_sha256"],
            "plan": plan_identity,
            "base_runspec_sha256": runspec_sha,
            "base_provenance_sha256": provenance_sha,
            "base_cli_sha256": base_cli_sha,
            "base_run_id": base_run_id,
        },
        "runtime": {
            "base_generation_profile": "faithful_5_32_3",
            "base_qc_filter": "off",
            "extension_prng": "splitmix64_box_muller_v1",
            "extension_domain_sha256": domain_sha256(
                MAIN_DOMAIN, row["station_id"], profile, row["extension_seed"]
            ),
            "cligen_binary": artifact_as_member(cligen.record),
            "overlay_binary": artifact_as_member(overlay.record),
            "implementation_commit": manifest["build"]["implementation_commit"],
        },
        "outputs": {
            "candidate_cli": cli_identity,
            "quality_report": quality_identity,
            "overlay_diagnostics": diagnostics_identity,
        },
        "execution": {
            "host_os": "synthetic",
            "host_arch": "synthetic",
            "wall_time_ms": 1,
            "precipitation_clip_count": 0,
            "precipitation_render_limit_adjustment_count": 0,
            "temperature_order_repair_count": 0,
            "dewpoint_cap_count": 0,
            "counterfactual_month_count": (
                row["horizon_years"] * 12 if counterfactual else 0
            ),
            "sealed": True,
        },
    }


def identity_for_member(name: str, raw: bytes) -> dict[str, Any]:
    return {"member": name, "sha256": sha256_bytes(raw), "bytes": len(raw)}


def identity_for_path(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": root_relative(path, root, "synthetic artifact"),
        "sha256": sha256_path(path),
        "bytes": path.stat().st_size,
    }


def write_synthetic_file(root: Path, relative: str, raw: bytes) -> Path:
    path = root.joinpath(*PurePosixPath(relative).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


@dataclass
class SyntheticEvidence:
    root: Path
    manifest: dict[str, Any]
    station_ids: list[str]
    regimes: dict[str, str]
    fit_stations: dict[str, FitStation]
    cligen: ResolvedArtifact
    overlay: ResolvedArtifact
    cli_dir: Path
    lexical_campaign_root: Path
    shared_bases: dict[tuple[str, int, int], dict[str, Any]]
    shared_archive_path: Path
    shared_archive_bindings: dict[str, tuple[str, int, str]]
    first_candidate_rows: list[dict[str, Any]]
    first_archive_path: Path
    first_archive_bindings: dict[str, tuple[str, int, str]]
    first_documents: dict[str, bytes]


def build_synthetic_evidence(root: Path) -> SyntheticEvidence:
    observed = require_dict(strict_json(OBSERVED_CORPUS), "observed corpus")
    station_ids = [row["station_id"] for row in observed["stations"]]
    regimes = {row["station_id"]: row["regime"] for row in observed["stations"]}
    contracts = {
        key: {"path": CONTRACT_PATHS[key], "sha256": sha256_bytes(key.encode())}
        for key in CONTRACT_PATHS
    }
    corpus_sha = sha256_bytes(b"synthetic-observed-corpus")
    manifest: dict[str, Any] = {
        "candidate_evidence_manifest_version": 1,
        "status": "sealed",
        "contracts": contracts,
        "corpus": {
            "schema_version": 1,
            "content_sha256": corpus_sha,
            "station_ids": station_ids,
        },
        "matrix": {
            "horizons": list(HORIZONS),
            "replicates": [
                {"replicate": index, "legacy_burn": burn, "extension_seed": seed}
                for index, burn, seed in REPLICATES
            ],
            "candidates": [
                {
                    "candidate_id": candidate_id,
                    "station_model": station_model,
                    "generation_profile": profile,
                }
                for candidate_id, station_model, profile in CANDIDATES
            ],
            "expected_runs": EXPECTED_RUNS,
        },
        "fit": {},
        "build": {},
        "shared_bases": {},
        "archives": [],
        "runs": [],
        "execution": {
            "workers": 1,
            "started_utc": "2026-07-13T00:00:00Z",
            "completed_utc": "2026-07-13T00:00:01Z",
            "wall_time_seconds": 1.0,
            "failures": [],
            "candidate_cli_bytes_removed_after_wepp": True,
        },
    }
    campaign_root = root / "target/a5b-candidate-v1"
    lexical_campaign_root = Path("/synthetic/repository/target/a5b-candidate-v1")
    cligen_path = write_synthetic_file(
        root,
        "target/a5b-candidate-v1/.a5b-input-snapshot/binaries/cligen",
        b"cligen",
    )
    overlay_path = write_synthetic_file(
        root,
        "target/a5b-candidate-v1/.a5b-input-snapshot/binaries/cligen-a5b-overlay",
        b"overlay",
    )
    cligen_record = identity_for_path(cligen_path, root)
    overlay_record = identity_for_path(overlay_path, root)
    cligen = ResolvedArtifact(cligen_record, cligen_path)
    overlay = ResolvedArtifact(overlay_record, overlay_path)
    manifest["build"] = {
        "implementation_commit": "a" * 40,
        "cligen_binary": cligen_record,
        "overlay_binary": overlay_record,
        "cargo_lock_sha256": "b" * 64,
        "rustc_version": "rustc synthetic",
        "plan_preflight": {"plans": 952, "aggregate_sha256": "0" * 64},
    }
    source_path = write_synthetic_file(
        root, "target/self-test/fit/source.json", b"{}\n"
    )
    fit_path = write_synthetic_file(root, "target/self-test/fit/fit.json", b"{}\n")
    fit_stations: dict[str, FitStation] = {}
    bundle_records = []
    for station_id in station_ids:
        bundle_path = write_synthetic_file(
            root, f"target/self-test/fit/{station_id}.a5b.station.json", b"{}\n"
        )
        bundle_record = identity_for_path(bundle_path, root)
        bundle_records.append(bundle_record)
        par_raw = f"synthetic-par-{station_id}\n".encode()
        par_path = write_synthetic_file(
            root,
            f"target/a5b-candidate-v1/.a5b-input-snapshot/stations/{station_id}.par",
            par_raw,
        )
        par_sha = sha256_bytes(par_raw)
        extensions: dict[str, dict[str, Any]] = {}
        for candidate_id, _, _ in CANDIDATES:
            payload = (
                {
                    "second_order_wet_probabilities": [[0.5] * 4 for _ in range(12)],
                    "amount_rank_rho": [0.0] * 12,
                }
                if candidate_id == "precip_counterfactual"
                else {}
            )
            payload_sha = sha256_bytes(f"payload-{station_id}-{candidate_id}".encode())
            extensions[candidate_id] = {
                "candidate_id": candidate_id,
                "fit_identity_sha256": sha256_bytes(
                    f"fit-{station_id}-{candidate_id}".encode()
                ),
                "runtime_parameter_count": 1,
                "payload": payload,
                "diagnostics": {"payload_sha256": payload_sha},
            }
        fit_stations[station_id] = FitStation(
            station_id,
            bundle_record,
            {},
            par_sha,
            extensions,
        )
        del par_path
    manifest["fit"] = {
        "source_manifest": identity_for_path(source_path, root),
        "fit_manifest": identity_for_path(fit_path, root),
        "bundles": bundle_records,
    }

    shared_records: list[dict[str, Any]] = []
    shared_documents: dict[str, bytes] = {}
    shared_lookup: dict[tuple[str, int, int], dict[str, Any]] = {}
    for station_id in station_ids:
        fit_station = fit_stations[station_id]
        parameter_sha = sha256_bytes(f"parameter-{station_id}".encode())
        for horizon in HORIZONS:
            for replicate, burn, _ in REPLICATES:
                stem = shared_base_stem(station_id, horizon, replicate, burn)
                runspec_raw, _, _ = shared_runspec_bytes(
                    station_id, horizon, replicate, burn, lexical_campaign_root
                )
                runspec_identity = identity_for_member(
                    f"runspecs/{stem}.yaml", runspec_raw
                )
                base_cli_sha = sha256_bytes(
                    f"base-cli-{station_id}-{horizon}-{replicate}".encode()
                )
                provenance, run_id = synthetic_base_provenance(
                    station_id,
                    horizon,
                    replicate,
                    burn,
                    fit_station.par_sha256,
                    parameter_sha,
                    base_cli_sha,
                    lexical_campaign_root,
                )
                provenance_raw = declaration_order_json_bytes(provenance)
                provenance_identity = identity_for_member(
                    f"provenance/{stem}.provenance.json", provenance_raw
                )
                record = {
                    "station_id": station_id,
                    "horizon_years": horizon,
                    "replicate": replicate,
                    "legacy_burn": burn,
                    "runspec": runspec_identity,
                    "provenance": provenance_identity,
                    "base_cli_sha256": base_cli_sha,
                    "base_run_id": run_id,
                    "parameter_set_sha256": parameter_sha,
                }
                shared_records.append(record)
                shared_lookup[(station_id, horizon, replicate)] = record
                shared_documents[runspec_identity["member"]] = runspec_raw
                shared_documents[provenance_identity["member"]] = provenance_raw
    shared_relative = (ARCHIVE_DIRECTORY / SHARED_BASE_ARCHIVE_NAME).as_posix()
    shared_archive_raw = canonical_archive_bytes(list(shared_documents.items()))
    shared_archive_path = write_synthetic_file(
        root, shared_relative, shared_archive_raw
    )
    manifest["shared_bases"] = {
        "format": "tar+gzip-canonical-v1",
        "artifact": identity_for_path(shared_archive_path, root),
        "base_count": SHARED_BASE_COUNT,
        "member_count": SHARED_BASE_MEMBER_COUNT,
        "records": shared_records,
    }

    cli_dir = campaign_root / "candidate-climates"
    first_documents: dict[str, bytes] = {}
    first_rows: list[dict[str, Any]] = []
    archive_records: list[dict[str, Any]] = []
    plan_items: list[tuple[str, bytes]] = []
    for candidate_id, _, _ in CANDIDATES:
        documents: dict[str, bytes] = {}
        rows: list[dict[str, Any]] = []
        plan_cache: dict[
            tuple[str, int], tuple[dict[str, Any], bytes, dict[str, Any]]
        ] = {}
        for station_id in station_ids:
            fit_station = fit_stations[station_id]
            extension = fit_station.extensions[candidate_id]
            parameter_sha = sha256_bytes(f"parameter-{station_id}".encode())
            legacy_path = (
                campaign_root
                / ".a5b-input-snapshot/stations"
                / f"{station_id}.par"
            )
            legacy_identity = artifact_as_member(identity_for_path(legacy_path, root))
            for horizon in HORIZONS:
                for replicate, burn, seed in REPLICATES:
                    stem_data = {
                        "station_id": station_id,
                        "regime": regimes[station_id],
                        "candidate_id": candidate_id,
                        "horizon_years": horizon,
                        "replicate": replicate,
                        "legacy_burn": burn,
                        "extension_seed": seed,
                    }
                    stem = run_stem(stem_data)
                    cli_raw = f"candidate-cli-{stem}\n".encode()
                    cli_path = cli_dir / candidate_id / f"{stem}.cli"
                    cli_identity = {
                        "member": root_relative(cli_path, root, "synthetic CLI"),
                        "sha256": sha256_bytes(cli_raw),
                        "bytes": len(cli_raw),
                    }
                    row = {
                        **stem_data,
                        "archive_candidate_id": candidate_id,
                        "candidate_cli_sha256": cli_identity["sha256"],
                        "candidate_cli_bytes": cli_identity["bytes"],
                    }
                    plan_key = (station_id, replicate)
                    if plan_key not in plan_cache:
                        plan = synthetic_plan(
                            candidate_id,
                            station_id,
                            seed,
                            extension["diagnostics"]["payload_sha256"],
                        )
                        plan_raw = canonical_json_bytes(plan)
                        plan_name = (
                            f"plans/{station_id}-{candidate_id}-rep{replicate}-"
                            f"burn{burn}.plan.json"
                        )
                        plan_identity = identity_for_member(plan_name, plan_raw)
                        plan_cache[plan_key] = (plan, plan_raw, plan_identity)
                        documents[plan_name] = plan_raw
                        plan_items.append((plan_name, plan_raw))
                    plan, plan_raw, plan_identity = plan_cache[plan_key]
                    row["plan"] = plan_identity
                    report = synthetic_quality(
                        row, fit_station.par_sha256, parameter_sha
                    )
                    report_raw = canonical_json_bytes(report)
                    report_identity = identity_for_member(
                        f"quality-reports/{stem}.quality.json", report_raw
                    )
                    shared_base = shared_lookup[(station_id, horizon, replicate)]
                    runspec_sha = shared_base["runspec"]["sha256"]
                    provenance_sha = shared_base["provenance"]["sha256"]
                    base_cli_sha = shared_base["base_cli_sha256"]
                    base_run_id = shared_base["base_run_id"]
                    diagnostics = synthetic_overlay_diagnostics(
                        row,
                        plan,
                        plan_raw,
                        runspec_sha,
                        base_cli_sha,
                        extension["diagnostics"]["payload_sha256"],
                    )
                    diagnostics_raw = canonical_json_bytes(diagnostics)
                    diagnostics_identity = identity_for_member(
                        f"overlay-diagnostics/{stem}.diagnostics.json", diagnostics_raw
                    )
                    record = synthetic_run_record(
                        row,
                        manifest,
                        fit_station,
                        extension,
                        plan_identity,
                        report_identity,
                        diagnostics_identity,
                        cli_identity,
                        cligen,
                        overlay,
                        legacy_identity,
                        runspec_sha,
                        provenance_sha,
                        base_cli_sha,
                        base_run_id,
                    )
                    record_raw = canonical_json_bytes(record)
                    record_identity = identity_for_member(
                        f"run-records/{stem}.run.json", record_raw
                    )
                    row["run_record"] = record_identity
                    row["quality_report"] = report_identity
                    row["overlay_diagnostics"] = diagnostics_identity
                    documents[record_identity["member"]] = record_raw
                    documents[report_identity["member"]] = report_raw
                    documents[diagnostics_identity["member"]] = diagnostics_raw
                    rows.append(row)
        manifest["runs"].extend(rows)
        archive_relative = (
            ARCHIVE_DIRECTORY / f"candidate-evidence-{candidate_id}-v1.tar.gz"
        ).as_posix()
        if candidate_id == CANDIDATES[0][0]:
            archive_raw = canonical_archive_bytes(list(documents.items()))
            archive_path = write_synthetic_file(root, archive_relative, archive_raw)
            archive_record = identity_for_path(archive_path, root)
            first_documents = documents
            first_rows = rows
            first_archive_path = archive_path
        else:
            placeholder = write_synthetic_file(
                root, archive_relative, f"placeholder-{candidate_id}".encode()
            )
            archive_record = identity_for_path(placeholder, root)
        archive_records.append(
            {
                "candidate_id": candidate_id,
                "format": "tar+gzip-canonical-v1",
                "artifact": archive_record,
                "member_count": MEMBERS_PER_CANDIDATE,
            }
        )
    manifest["archives"] = archive_records
    manifest["build"]["plan_preflight"] = {
        "plans": len(plan_items),
        "aggregate_sha256": aggregate_named_bytes(plan_items),
    }
    bindings = expected_archive_bindings(CANDIDATES[0][0], first_rows)
    shared_bindings = expected_shared_base_bindings(shared_records, station_ids)
    return SyntheticEvidence(
        root,
        manifest,
        station_ids,
        regimes,
        fit_stations,
        cligen,
        overlay,
        cli_dir,
        lexical_campaign_root,
        shared_lookup,
        shared_archive_path,
        shared_bindings,
        first_rows,
        first_archive_path,
        bindings,
        first_documents,
    )


def expect_self_test_rejection(
    label: str,
    operation: Any,
    checks: list[str],
) -> None:
    try:
        operation()
    except EvidenceError:
        checks.append(label)
        return
    raise EvidenceError(f"self-test mutation was incorrectly accepted: {label}")


def self_test() -> dict[str, Any]:
    """Exercise positive evidence and explicit fail-closed mutations."""

    checks: list[str] = []

    def accept(label: str, operation: Any) -> Any:
        value = operation()
        checks.append(label)
        return value

    with tempfile.TemporaryDirectory(prefix="cligen-a5b-verifier-") as directory:
        evidence = build_synthetic_evidence(Path(directory))
        manifest = evidence.manifest
        evidence_schema = plain_validator(EVIDENCE_SCHEMA)
        run_schema = plain_validator(RUN_SCHEMA)
        plan_schema = plain_validator(PLAN_SCHEMA)

        contract_manifest = {"contracts": {}}
        frozen_inventory: dict[str, str] = {}
        for key, relative in CONTRACT_PATHS.items():
            if key == "pre_candidate_freeze":
                continue
            raw = f"synthetic-contract-{key}\n".encode()
            path = write_synthetic_file(evidence.root, relative, raw)
            digest = sha256_path(path)
            contract_manifest["contracts"][key] = {
                "path": relative,
                "sha256": digest,
            }
            frozen_inventory[relative] = digest
        freeze_relative = CONTRACT_PATHS["pre_candidate_freeze"]
        freeze_path = write_synthetic_file(
            evidence.root,
            freeze_relative,
            canonical_json_bytes(
                {
                    "a5b_frozen_artifacts": frozen_inventory,
                    "a5a_pinned_artifacts": {},
                }
            ),
        )
        contract_manifest["contracts"]["pre_candidate_freeze"] = {
            "path": freeze_relative,
            "sha256": sha256_path(freeze_path),
        }
        accept(
            "current contracts match pre-candidate freeze inventory",
            lambda: verify_contracts(contract_manifest, evidence.root),
        )
        mutated_contracts = copy.deepcopy(contract_manifest)
        mutated_key = "candidate_spec"
        mutated_path = evidence.root.joinpath(*PurePosixPath(CONTRACT_PATHS[mutated_key]).parts)
        original_contract_raw = mutated_path.read_bytes()
        mutated_path.write_bytes(b"post-freeze-contract-mutation\n")
        mutated_contracts["contracts"][mutated_key]["sha256"] = sha256_path(
            mutated_path
        )
        try:
            expect_self_test_rejection(
                "contract current hash cannot bypass freeze inventory",
                lambda: verify_contracts(mutated_contracts, evidence.root),
                checks,
            )
        finally:
            mutated_path.write_bytes(original_contract_raw)

        accept(
            "synthetic evidence schema",
            lambda: validate_schema(
                manifest, evidence_schema, "synthetic candidate evidence manifest"
            ),
        )
        accept(
            "complete canonical matrix",
            lambda: verify_matrix(manifest, evidence.station_ids, evidence.regimes),
        )
        verified_shared = accept(
            "canonical 544-member shared-base archive and provenance",
            lambda: verify_shared_bases(
                manifest,
                evidence.fit_stations,
                evidence.cligen,
                None,
                evidence.root,
                evidence.lexical_campaign_root,
            ),
        )
        if verified_shared != evidence.shared_bases:
            raise EvidenceError("self-test shared-base index differs")
        shared_documents = read_canonical_archive(
            evidence.shared_archive_path,
            evidence.shared_archive_bindings,
            SHARED_BASE_MEMBER_COUNT,
        )
        first_shared = manifest["shared_bases"]["records"][0]
        first_shared_provenance = require_dict(
            strict_json_bytes(
                shared_documents[first_shared["provenance"]["member"]],
                "synthetic shared provenance",
            ),
            "synthetic shared provenance",
        )
        _, first_par, first_base_cli = shared_runspec_bytes(
            first_shared["station_id"],
            first_shared["horizon_years"],
            first_shared["replicate"],
            first_shared["legacy_burn"],
            evidence.lexical_campaign_root,
        )
        mutated_provenance = copy.deepcopy(first_shared_provenance)
        mutated_provenance["effective_runspec"]["output"]["quality"] = True
        expect_self_test_rejection(
            "shared-base provenance semantic mutation rejected",
            lambda: validate_shared_base_provenance(
                mutated_provenance,
                {
                    **first_shared,
                    "par_sha256": evidence.fit_stations[
                        first_shared["station_id"]
                    ].par_sha256,
                },
                first_par,
                first_base_cli,
                plain_validator(PROVENANCE_SCHEMA),
            ),
            checks,
        )
        documents = accept(
            "canonical 952-member archive",
            lambda: read_canonical_archive(
                evidence.first_archive_path,
                evidence.first_archive_bindings,
                MEMBERS_PER_CANDIDATE,
            ),
        )
        staged_archive_dir = evidence.root / "target/self-test/staged-archives"
        staged_archive = write_synthetic_file(
            evidence.root,
            (
                "target/self-test/staged-archives/"
                + evidence.first_archive_path.name
            ),
            evidence.first_archive_path.read_bytes(),
        )
        accept(
            "explicit staged archive substitution",
            lambda: resolve_archive_artifact(
                manifest["archives"][0]["artifact"],
                "staged candidate archive",
                staged_archive_dir,
                evidence.root,
            ),
        )
        staged_raw = staged_archive.read_bytes()
        staged_archive.write_bytes(staged_raw + b"mutation")
        try:
            expect_self_test_rejection(
                "staged archive identity mutation rejected",
                lambda: resolve_archive_artifact(
                    manifest["archives"][0]["artifact"],
                    "staged candidate archive",
                    staged_archive_dir,
                    evidence.root,
                ),
                checks,
            )
        finally:
            staged_archive.write_bytes(staged_raw)

        records: dict[tuple[str, str, int, int], dict[str, Any]] = {}
        plans: dict[str, dict[str, Any]] = {}
        first_report: dict[str, Any] | None = None
        first_record: dict[str, Any] | None = None
        first_plan: dict[str, Any] | None = None
        first_diagnostics: dict[str, Any] | None = None
        for row in evidence.first_candidate_rows:
            plan_name = row["plan"]["member"]
            plan = plans.get(plan_name)
            fit_station = evidence.fit_stations[row["station_id"]]
            extension = fit_station.extensions[row["candidate_id"]]
            if plan is None:
                plan = require_dict(
                    strict_json_bytes(documents[plan_name], plan_name), plan_name
                )
                validate_plan_document(plan, row, extension, plan_schema)
                plans[plan_name] = plan

            record_name = row["run_record"]["member"]
            record = require_dict(
                strict_json_bytes(documents[record_name], record_name), record_name
            )
            validate_run_record(
                record,
                row,
                manifest,
                fit_station,
                plan,
                evidence.cligen,
                evidence.overlay,
                run_schema,
                evidence.cli_dir,
                evidence.root,
            )
            report_name = row["quality_report"]["member"]
            report = require_dict(
                strict_json_bytes(documents[report_name], report_name), report_name
            )
            # The compact synthetic report exercises A5b's post-hoc semantics.  Real
            # evidence is additionally checked against the complete S2/M3 schema.
            validate_quality_document(report, row, fit_station, None)
            diagnostics_name = row["overlay_diagnostics"]["member"]
            diagnostics = require_dict(
                strict_json_bytes(documents[diagnostics_name], diagnostics_name),
                diagnostics_name,
            )
            validate_overlay_diagnostics(diagnostics, row, record, plan)
            key = (
                row["candidate_id"],
                row["station_id"],
                row["horizon_years"],
                row["replicate"],
            )
            records[key] = record
            if first_record is None:
                first_record = record
                first_report = report
                first_plan = plan
                first_diagnostics = diagnostics
        if len(plans) != PLANS_PER_CANDIDATE or len(records) != RUNS_PER_CANDIDATE:
            raise EvidenceError(
                "self-test did not validate the complete candidate archive"
            )
        checks.append("272 semantic run bundles and 136 shared plans")
        accept(
            "declared CLI removal with no retained files",
            lambda: verify_candidate_cli_state(
                manifest,
                evidence.first_candidate_rows,
                records,
                evidence.cli_dir,
                evidence.root,
            ),
        )
        accept(
            "sealed CLI index needs no raw CLI directory",
            lambda: verify_candidate_cli_state(
                manifest,
                evidence.first_candidate_rows,
                records,
                None,
                evidence.root,
            ),
        )

        first_row = evidence.first_candidate_rows[0]
        if (
            first_record is None
            or first_report is None
            or first_plan is None
            or first_diagnostics is None
        ):
            raise EvidenceError("self-test failed to capture its first semantic bundle")
        fit_station = evidence.fit_stations[first_row["station_id"]]

        missing_run = copy.deepcopy(manifest)
        missing_run["runs"].pop()
        expect_self_test_rejection(
            "missing run rejected",
            lambda: verify_matrix(missing_run, evidence.station_ids, evidence.regimes),
            checks,
        )

        extra_run = copy.deepcopy(manifest)
        unknown = copy.deepcopy(extra_run["runs"][0])
        unknown["station_id"] = "zz999999"
        extra_run["runs"].append(unknown)
        expect_self_test_rejection(
            "extra run rejected",
            lambda: verify_matrix(extra_run, evidence.station_ids, evidence.regimes),
            checks,
        )

        duplicate_run = copy.deepcopy(manifest)
        duplicate_run["runs"][-1] = copy.deepcopy(duplicate_run["runs"][0])
        expect_self_test_rejection(
            "duplicate run rejected",
            lambda: verify_matrix(
                duplicate_run, evidence.station_ids, evidence.regimes
            ),
            checks,
        )

        first_member = sorted(evidence.first_archive_bindings)[0]
        digest, size, kind = evidence.first_archive_bindings[first_member]
        bad_hash = dict(evidence.first_archive_bindings)
        bad_hash[first_member] = (
            "0" * 64 if digest != "0" * 64 else "1" * 64,
            size,
            kind,
        )
        expect_self_test_rejection(
            "archive member hash mismatch rejected",
            lambda: read_canonical_archive(
                evidence.first_archive_path, bad_hash, MEMBERS_PER_CANDIDATE
            ),
            checks,
        )

        bad_bytes = dict(evidence.first_archive_bindings)
        bad_bytes[first_member] = (digest, size + 1, kind)
        expect_self_test_rejection(
            "archive member byte mismatch rejected",
            lambda: read_canonical_archive(
                evidence.first_archive_path, bad_bytes, MEMBERS_PER_CANDIDATE
            ),
            checks,
        )

        bad_member = dict(evidence.first_archive_bindings)
        displaced = bad_member.pop(first_member)
        bad_member["run-records/unbound-self-test.json"] = displaced
        expect_self_test_rejection(
            "archive member-set mismatch rejected",
            lambda: read_canonical_archive(
                evidence.first_archive_path, bad_member, MEMBERS_PER_CANDIDATE
            ),
            checks,
        )

        traversal_raw = b"{}\n"
        traversal_name = "../escape.json"
        traversal_path = write_synthetic_file(
            evidence.root,
            "target/self-test/mutations/traversal.tar.gz",
            canonical_archive_bytes([(traversal_name, traversal_raw)]),
        )
        traversal_binding = {
            traversal_name: (
                sha256_bytes(traversal_raw),
                len(traversal_raw),
                "self-test",
            )
        }
        expect_self_test_rejection(
            "archive traversal rejected",
            lambda: read_canonical_archive(traversal_path, traversal_binding, 1),
            checks,
        )

        singleton_name = "run-records/self-test.json"
        singleton_raw = b"{}\n"
        singleton_binding = {
            singleton_name: (
                sha256_bytes(singleton_raw),
                len(singleton_raw),
                "self-test",
            )
        }
        noncanonical_gzip = write_synthetic_file(
            evidence.root,
            "target/self-test/mutations/noncanonical-gzip.tar.gz",
            canonical_archive_bytes([(singleton_name, singleton_raw)], gzip_mtime=1),
        )
        expect_self_test_rejection(
            "noncanonical gzip header rejected",
            lambda: read_canonical_archive(noncanonical_gzip, singleton_binding, 1),
            checks,
        )

        noncanonical_tar = write_synthetic_file(
            evidence.root,
            "target/self-test/mutations/noncanonical-tar.tar.gz",
            canonical_archive_bytes(
                [(singleton_name, singleton_raw)], mode_override=0o600
            ),
        )
        expect_self_test_rejection(
            "noncanonical tar metadata rejected",
            lambda: read_canonical_archive(noncanonical_tar, singleton_binding, 1),
            checks,
        )

        expect_self_test_rejection(
            "repository path traversal rejected",
            lambda: resolve_artifact(
                {"path": "../escape", "sha256": "0" * 64, "bytes": 1},
                "self-test escaped artifact",
                evidence.root,
            ),
            checks,
        )

        def reject_record_mutation(label: str, field: str, value: Any) -> None:
            mutated = copy.deepcopy(first_record)
            mutated["matrix"][field] = value
            expect_self_test_rejection(
                label,
                lambda: validate_run_record(
                    mutated,
                    first_row,
                    manifest,
                    fit_station,
                    first_plan,
                    evidence.cligen,
                    evidence.overlay,
                    run_schema,
                    evidence.cli_dir,
                    evidence.root,
                ),
                checks,
            )

        reject_record_mutation(
            "cross-field seed mismatch rejected",
            "extension_seed",
            "0x0000000000000001",
        )
        reject_record_mutation(
            "cross-field profile mismatch rejected",
            "generation_profile",
            CANDIDATES[1][2],
        )
        reject_record_mutation(
            "cross-field station mismatch rejected",
            "station_id",
            evidence.station_ids[1],
        )

        period_report = copy.deepcopy(first_report)
        period_report["identity"]["content"]["years"] += 1
        expect_self_test_rejection(
            "quality period mismatch rejected",
            lambda: validate_quality_document(
                period_report, first_row, fit_station, None
            ),
            checks,
        )

        provenance_report = copy.deepcopy(first_report)
        provenance_report["identity"]["provenance"] = {}
        expect_self_test_rejection(
            "post-hoc provenance non-null rejected",
            lambda: validate_quality_document(
                provenance_report, first_row, fit_station, None
            ),
            checks,
        )

        process_report = copy.deepcopy(first_report)
        process_report["process"] = {}
        expect_self_test_rejection(
            "post-hoc quality process non-null rejected",
            lambda: validate_quality_document(
                process_report, first_row, fit_station, None
            ),
            checks,
        )

        bad_plan = copy.deepcopy(first_plan)
        bad_plan["state_table_sha256"] = "0" * 64
        expect_self_test_rejection(
            "plan state-table hash mismatch rejected",
            lambda: validate_plan_document(
                bad_plan,
                first_row,
                fit_station.extensions[first_row["candidate_id"]],
                plan_schema,
            ),
            checks,
        )

        bad_adjustment = copy.deepcopy(first_diagnostics)
        bad_adjustment["precipitation_factor_adjustments"][0][
            "effective_factor"
        ] = 0.5
        expect_self_test_rejection(
            "precipitation effective-factor mutation rejected",
            lambda: validate_overlay_diagnostics(
                bad_adjustment, first_row, first_record, first_plan
            ),
            checks,
        )

        retained_manifest = copy.deepcopy(manifest)
        retained_manifest["execution"]["candidate_cli_bytes_removed_after_wepp"] = False
        expect_self_test_rejection(
            "retained CLI directory requirement enforced",
            lambda: verify_candidate_cli_state(
                retained_manifest,
                [first_row],
                {
                    (
                        first_row["candidate_id"],
                        first_row["station_id"],
                        first_row["horizon_years"],
                        first_row["replicate"],
                    ): first_record
                },
                None,
                evidence.root,
            ),
            checks,
        )

        leftover = expected_cli_path(first_row, evidence.cli_dir)
        leftover.parent.mkdir(parents=True, exist_ok=True)
        leftover.write_bytes(b"unexpected retained CLI\n")
        try:
            expect_self_test_rejection(
                "declared CLI removal rejects retained bytes",
                lambda: verify_candidate_cli_state(
                    manifest,
                    [first_row],
                    {
                        (
                            first_row["candidate_id"],
                            first_row["station_id"],
                            first_row["horizon_years"],
                            first_row["replicate"],
                        ): first_record
                    },
                    evidence.cli_dir,
                    evidence.root,
                ),
                checks,
            )
            expect_self_test_rejection(
                "inferred CLI root rejects retained bytes without option",
                lambda: verify_candidate_cli_state(
                    manifest,
                    [first_row],
                    {
                        (
                            first_row["candidate_id"],
                            first_row["station_id"],
                            first_row["horizon_years"],
                            first_row["replicate"],
                        ): first_record
                    },
                    None,
                    evidence.root,
                ),
                checks,
            )
        finally:
            leftover.unlink()

        manifest_sha = sha256_bytes(canonical_json_bytes(manifest))
        archive_sha = sha256_path(evidence.first_archive_path)
        fixture_sha = sha256_bytes(
            compact_json_bytes(
                {
                    "archive_sha256": archive_sha,
                    "manifest_sha256": manifest_sha,
                }
            )
        )
        if fixture_sha != SELF_TEST_GOLDEN_SHA256:
            raise EvidenceError(
                "self-test synthetic fixture hash differs: "
                f"expected {SELF_TEST_GOLDEN_SHA256}, observed {fixture_sha}"
            )
        checks.append("synthetic fixture golden hash")

    return {
        "status": "passed",
        "checks": len(checks),
        "check_names": checks,
        "synthetic_manifest_sha256": manifest_sha,
        "synthetic_archive_sha256": archive_sha,
        "synthetic_fixture_sha256": fixture_sha,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        help="candidate evidence manifest (default: package canonical path)",
    )
    parser.add_argument(
        "--candidate-cli-dir",
        type=Path,
        help="repository-contained candidate CLI root used for byte verification",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        help="repository-contained staging directory substituting sealed archives",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run canonical synthetic positive and mutation-rejection checks",
    )
    arguments = parser.parse_args(argv)
    if arguments.self_test and (
        arguments.manifest is not None
        or arguments.candidate_cli_dir is not None
        or arguments.archive_dir is not None
    ):
        parser.error("--self-test cannot be combined with a manifest or CLI directory")
    return arguments


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        if arguments.self_test:
            result = self_test()
        else:
            manifest_path = arguments.manifest or DEFAULT_MANIFEST
            if not manifest_path.is_absolute():
                manifest_path = Path.cwd() / manifest_path
            result = verify(
                manifest_path.resolve(strict=True),
                arguments.candidate_cli_dir,
                arguments.archive_dir,
            )
    except Exception as error:  # Fail closed for malformed or incomplete evidence.
        print(f"A5b evidence verification failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
