#!/usr/bin/env python3
"""Execute and seal the frozen 1,904-run A5b candidate climate matrix.

Usage:
  run-a5b-matrix.py <release-cligen> <release-overlay> <us-2015-cache> \
      <fit-directory> <target-directory> [--workers 1..4]
  run-a5b-matrix.py --self-test

The target directory is the campaign root.  Candidate CLIs remain under its
``candidate-climates`` child for the downstream WEPP campaign; all scientific
reports stay sealed in seven deterministic candidate archives.  This runner
checks identities and schema/lineage closure but never computes or inspects a
candidate climate metric.
"""

from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime, timezone
import functools
import gzip
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Callable, Sequence
import warnings
import zlib

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = Path(__file__).resolve().parents[2]
A5A = ROOT / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts"
CLIMATE_DIR = PACKAGE / "artifacts/climate"

CORPUS_CONFIG = A5A / "corpus/corpus-config-v1.json"
OBSERVED_CORPUS = A5A / "corpus/observed-target-corpus-v1.json"
A5A_SOURCE_MANIFEST = A5A / "corpus/source-manifest-v1.json"
FIT_SOURCE_NAME = "source-manifest-v1.json"
FIT_MANIFEST_NAME = "fit-manifest-v1.json"
FIT_GOLDEN_NAME = "fit-golden-v1.json"
FIT_BUNDLE_DIRECTORY = "station-bundles"

PLAN_GENERATOR = PACKAGE / "artifacts/runtime/generate-a5b-plan.py"
FITTER = PACKAGE / "artifacts/fit/fit-a5b-models.py"
EVIDENCE_VERIFIER = PACKAGE / "artifacts/runtime/verify-a5b-evidence.py"
PRE_CANDIDATE_FREEZE = PACKAGE / "artifacts/freeze/pre-candidate-freeze-v1.json"
PRE_OUTPUT_AMENDMENTS = PACKAGE / "artifacts/freeze/pre-output-amendments.md"

QUALITY_SCHEMA = ROOT / "docs/specifications/quality-report-s2-m3.schema.json"
PROVENANCE_SCHEMA = ROOT / "docs/specifications/provenance-v1.schema.json"
STATION_SCHEMA = ROOT / "docs/specifications/a5b-augmented-station-v1.schema.json"
BASE_STATION_SCHEMA = ROOT / "docs/specifications/station-document.schema.json"
PLAN_SCHEMA = ROOT / "docs/specifications/a5b-overlay-plan-v1.schema.json"
RUN_RECORD_SCHEMA = ROOT / "docs/specifications/a5b-run-record-v1.schema.json"
EVIDENCE_SCHEMA = ROOT / "docs/specifications/a5b-candidate-evidence-v1.schema.json"

EXPECTED_CLIGEN = ROOT / "target/release/cligen"
EXPECTED_OVERLAY = ROOT / "target/release/cligen-a5b-overlay"
EXPECTED_FIT_DIRECTORY = PACKAGE / "artifacts/fit/evidence-v1"
EXPECTED_TARGET = ROOT / "target/a5b-candidate-v1"
MANIFEST_PATH = CLIMATE_DIR / "candidate-evidence-manifest-v1.json"

SNAPSHOT_NAME = ".a5b-input-snapshot"
STAGING_NAME = ".archive-staging"
WORK_NAME = ".work"
CLI_DIRECTORY_NAME = "candidate-climates"
PUBLICATION_STAGING_NAME = "publication"
ROLLBACK_MARKER_NAME = ".a5b-unsealed-owner"

FIXED_ARCHIVE_MTIME = 0
FIXED_ARCHIVE_MODE = 0o644
GZIP_COMPRESSLEVEL = 9
MAX_WORKERS = 4
EXPECTED_RUNS = 1904
RUNS_PER_CANDIDATE = 272
PLANS_PER_CANDIDATE = 136
MEMBERS_PER_CANDIDATE = 952
SHARED_BASE_COUNT = 272
SHARED_BASE_MEMBER_COUNT = 544
MAX_RENDERABLE_PRECIP_MM = struct.unpack(">f", struct.pack(">f", 999.9))[0]

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
CANDIDATE_ORDER = {row[0]: index for index, row in enumerate(CANDIDATES)}
REPLICATE_BY_INDEX = {row[0]: row for row in REPLICATES}

CONTRACT_PATHS = {
    "candidate_spec": ROOT / "docs/specifications/SPEC-A5B-CANDIDATES.md",
    "evaluation_spec": ROOT / "docs/specifications/SPEC-A5-EVALUATION.md",
    "metric_manifest": ROOT / "docs/specifications/a5-climate-gate-metrics-v1.json",
    "metric_schema": ROOT / "docs/specifications/a5-climate-gate-metrics-v1.schema.json",
    "metric_verifier": A5A / "verify-a5-climate-gate-metrics-v1.py",
    "bootstrap_reference": A5A / "observed-bootstrap-v1.py",
    "bootstrap_golden": A5A / "observed-bootstrap-v1-golden.json",
    "quality_schema": QUALITY_SCHEMA,
    "station_schema": STATION_SCHEMA,
    "base_station_schema": BASE_STATION_SCHEMA,
    "plan_schema": PLAN_SCHEMA,
    "run_record_schema": RUN_RECORD_SCHEMA,
    "wepp_schema": ROOT / "docs/specifications/a5-wepp-response-v1.schema.json",
    "wepp_protocol": A5A / "wepp-response-protocol.md",
    "wepp_verifier": A5A / "verify-wepp-response-schema.py",
    "evidence_schema": EVIDENCE_SCHEMA,
    "evidence_verifier": EVIDENCE_VERIFIER,
    "matrix_runner": Path(__file__).resolve(),
    "plan_generator": PLAN_GENERATOR,
    "overlay_source": ROOT / "crates/cligen/src/bin/cligen-a5b-overlay.rs",
    "fitter": FITTER,
    "pre_candidate_freeze": PRE_CANDIDATE_FREEZE,
    "pre_output_amendments": PRE_OUTPUT_AMENDMENTS,
}
RUN_RECORD_CONTRACT_KEYS = (
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

BUILD_COMMAND = (
    "cargo",
    "build",
    "--locked",
    "--offline",
    "--release",
    "--bin",
    "cligen",
    "--bin",
    "cligen-a5b-overlay",
)
SAFE_CARGO_RUST_ENV = {
    "CARGO_NET_OFFLINE",
    "RUST_BACKTRACE",
    "RUST_LIB_BACKTRACE",
    "RUST_LOG",
}
SAFE_CARGO_RUST_ENV_PREFIXES = ("CARGO_TERM_",)

SELF_TEST_MANIFEST_SHA256 = "e4bb73897b17df902a2aea862fe362aee251e21cbe91b1713f217b9ebb946ffc"
SELF_TEST_ARCHIVE_SHA256 = "850366ee85b5a0ee80f500c93c2d44970005ad2ce552c7d170887a6b340bcacd"
NEUTRAL_BASE_COMMAND_ECHO = "--a5b-base faithful_5_32_3"


class MatrixError(RuntimeError):
    """A frozen input, execution, schema, or evidence-closure violation."""


@dataclass(frozen=True)
class StationInput:
    station_id: str
    regime: str
    par: Path
    par_sha256: str
    bundle: Path
    bundle_snapshot: Path
    bundle_sha256: str
    bundle_value: dict[str, Any]
    extensions: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class Job:
    station_id: str
    regime: str
    candidate_id: str
    station_model: str
    generation_profile: str
    horizon_years: int
    replicate: int
    legacy_burn: int
    extension_seed: str


@dataclass(frozen=True)
class BaseJob:
    station_id: str
    regime: str
    horizon_years: int
    replicate: int
    legacy_burn: int


@dataclass(frozen=True)
class BaseInput:
    runspec: Path
    runspec_sha256: str
    runspec_member: dict[str, Any]
    provenance: Path
    provenance_sha256: str
    provenance_member: dict[str, Any]
    cli: Path
    cli_sha256: str
    run_id: str
    parameter_set_sha256: str


@dataclass(frozen=True)
class PlanInput:
    path: Path
    member: dict[str, Any]
    value: dict[str, Any]


@dataclass
class ExecutionOwnership:
    token: bytes
    target_created: bool = False
    temporary_manifest_created: bool = False
    manifest_published: bool = False
    public_paths: list[Path] = field(default_factory=list)


def reject_constant(token: str) -> None:
    raise MatrixError(f"nonfinite JSON token is forbidden: {token}")


def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MatrixError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise MatrixError(f"JSON number overflows finite binary64: {token}")
    return value


def strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_pairs,
            parse_constant=reject_constant,
            parse_float=parse_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MatrixError(f"cannot parse {label}: {error}") from error


def strict_json(path: Path) -> Any:
    try:
        return strict_json_bytes(path.read_bytes(), str(path))
    except OSError as error:
        raise MatrixError(f"cannot read JSON artifact {path}: {error}") from error


def canonical_json_bytes(value: Any) -> bytes:
    try:
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
    except (TypeError, ValueError) as error:
        raise MatrixError(f"cannot serialize canonical JSON: {error}") from error


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_named_bytes(items: Sequence[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, raw in items:
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MatrixError(f"{label} must be an object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise MatrixError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise MatrixError(f"{label} must be 64 lowercase hexadecimal digits")
    return value


def repo_relative(path: Path) -> str:
    resolved = path.resolve(strict=False)
    root = ROOT.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise MatrixError(f"artifact path is outside the repository: {path}")
    return resolved.relative_to(root).as_posix()


def resolve_repo_path(relative: str, label: str, require_file: bool = True) -> Path:
    lexical = PurePosixPath(relative)
    if lexical.is_absolute() or ".." in lexical.parts or "\\" in relative:
        raise MatrixError(f"{label} is not a safe repository-relative path: {relative!r}")
    path = (ROOT / Path(*lexical.parts)).resolve(strict=False)
    if not path.is_relative_to(ROOT.resolve(strict=True)):
        raise MatrixError(f"{label} escapes the repository: {relative!r}")
    if require_file and not path.is_file():
        raise MatrixError(f"{label} is missing: {path}")
    return path


def safe_member_name(name: str) -> None:
    lexical = PurePosixPath(name)
    if (
        not name
        or lexical.is_absolute()
        or ".." in lexical.parts
        or "\\" in name
        or any(part in ("", ".") for part in lexical.parts)
    ):
        raise MatrixError(f"unsafe archive member name: {name!r}")


def artifact_for_path(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size < 1:
        raise MatrixError(f"artifact is missing or empty: {path}")
    return {
        "path": repo_relative(path),
        "sha256": sha256_path(path),
        "bytes": path.stat().st_size,
    }


def member_for_path(member: str, path: Path) -> dict[str, Any]:
    safe_member_name(member)
    if not path.is_file() or path.stat().st_size < 1:
        raise MatrixError(f"member source is missing or empty: {member}: {path}")
    return {
        "member": member,
        "sha256": sha256_path(path),
        "bytes": path.stat().st_size,
    }


def external_member_with_sha256(path: Path, expected_sha256: str) -> dict[str, Any]:
    require_sha256(expected_sha256, f"known artifact identity for {path}")
    if not path.is_file() or path.stat().st_size < 1:
        raise MatrixError(f"known artifact is missing or empty: {path}")
    return {
        "member": repo_relative(path),
        "sha256": expected_sha256,
        "bytes": path.stat().st_size,
    }


def identity_for_path(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise MatrixError(f"contract is missing: {path}")
    return {"path": repo_relative(path), "sha256": sha256_path(path)}


@functools.lru_cache(maxsize=None)
def schema_validator(schema_path: str) -> Draft202012Validator:
    schema = strict_json(Path(schema_path))
    Draft202012Validator.check_schema(schema)
    schema_id = schema.get("$id")
    if not isinstance(schema_id, str) or not schema_id:
        raise MatrixError(f"schema $id is missing for {schema_path}")
    resources = {schema_id: Resource.from_contents(schema)}
    local_dependencies = (
        (
            BASE_STATION_SCHEMA,
            (
                "https://raw.githubusercontent.com/rogerlew/cligen-rs/main/"
                "docs/specifications/station-document.schema.json",
            ),
        ),
        (PROVENANCE_SCHEMA, ()),
    )
    for dependency_path, aliases in local_dependencies:
        dependency = strict_json(dependency_path)
        Draft202012Validator.check_schema(dependency)
        dependency_id = dependency.get("$id")
        if not isinstance(dependency_id, str) or not dependency_id:
            raise MatrixError(f"local schema $id is missing for {dependency_path}")
        resource = Resource.from_contents(dependency)
        for uri in (dependency_id, *aliases):
            resources[uri] = resource
    return Draft202012Validator(
        schema,
        registry=Registry().with_resources(resources.items()),
    )


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    validator = schema_validator(str(schema_path.resolve(strict=True)))
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path)
        raise MatrixError(f"{label} schema failure at /{location}: {first.message}")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise MatrixError(f"cannot load frozen helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def current_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise MatrixError(f"cannot resolve implementation commit: {completed.stderr.decode(errors='replace').strip()}")
    value = completed.stdout.decode("ascii", errors="strict").strip()
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise MatrixError(f"git returned a noncanonical commit ID: {value!r}")
    return value


def contract_identities() -> dict[str, dict[str, str]]:
    if len(CONTRACT_PATHS) != 23 or set(RUN_RECORD_CONTRACT_KEYS) - set(CONTRACT_PATHS):
        raise MatrixError("A5b contract inventory is not the frozen 23/15-key set")
    return {name: identity_for_path(path) for name, path in CONTRACT_PATHS.items()}


def validate_pre_candidate_freeze(contracts: dict[str, dict[str, str]]) -> dict[str, Any]:
    freeze = require_object(strict_json(PRE_CANDIDATE_FREEZE), "pre-candidate freeze")
    if (
        freeze.get("pre_candidate_freeze_version") != 1
        or freeze.get("status") != "passed"
        or freeze.get("candidate_output_absent") is not True
        or freeze.get("matrix_contract")
        != {
            "stations": 17,
            "horizons": [30, 100],
            "replicates": 8,
            "candidates": 7,
            "expected_runs": EXPECTED_RUNS,
        }
    ):
        raise MatrixError("pre-candidate freeze status or matrix contract differs")
    frozen_a5b = require_object(freeze.get("a5b_frozen_artifacts"), "frozen A5b artifacts")
    frozen_a5a = require_object(freeze.get("a5a_pinned_artifacts"), "pinned A5a artifacts")
    for name, identity in contracts.items():
        if name == "pre_candidate_freeze":
            continue
        relative = identity["path"]
        expected = frozen_a5b.get(relative, frozen_a5a.get(relative))
        if expected != identity["sha256"]:
            raise MatrixError(f"contract differs from pre-candidate freeze: {relative}")
    return freeze


def cargo_environment_audit() -> dict[str, str]:
    relevant = {
        name: value
        for name, value in sorted(os.environ.items())
        if name.startswith(("CARGO", "RUST"))
    }
    unsafe = [
        name
        for name in relevant
        if name not in SAFE_CARGO_RUST_ENV
        and not name.startswith(SAFE_CARGO_RUST_ENV_PREFIXES)
    ]
    if unsafe:
        raise MatrixError(f"compiler-affecting Cargo/Rust environment must be unset: {unsafe}")
    return relevant


def cargo_configuration_audit() -> list[str]:
    candidates: set[Path] = set()
    for directory in (ROOT, *ROOT.parents):
        candidates.add(directory / ".cargo/config")
        candidates.add(directory / ".cargo/config.toml")
    candidates.add(Path.home() / ".cargo/config")
    candidates.add(Path.home() / ".cargo/config.toml")
    active = sorted(str(path) for path in candidates if path.is_file())
    if active:
        raise MatrixError(f"Cargo configuration is forbidden for the evidence build: {active}")
    return active


def command_output(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise MatrixError(f"command failed: {command}: {completed.stderr.decode(errors='replace').strip()}")
    return completed.stdout.decode("utf-8", errors="strict").rstrip("\n")


def build_binaries(cligen: Path, overlay: Path) -> dict[str, Any]:
    if cligen.resolve(strict=False) != EXPECTED_CLIGEN.resolve(strict=False):
        raise MatrixError(f"release cligen must be {EXPECTED_CLIGEN}")
    if overlay.resolve(strict=False) != EXPECTED_OVERLAY.resolve(strict=False):
        raise MatrixError(f"release overlay must be {EXPECTED_OVERLAY}")
    environment = cargo_environment_audit()
    configuration = cargo_configuration_audit()
    if any(os.environ.get(name) for name in ("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CARGO_TARGET_DIR", "CARGO_BUILD_TARGET")):
        raise MatrixError("custom Rust flags, wrappers, target directory, or build target are forbidden")
    cargo = shutil.which("cargo")
    rustc = shutil.which(os.environ.get("RUSTC", "rustc"))
    if cargo is None or rustc is None:
        raise MatrixError("cargo and rustc must resolve to executable files")
    completed = subprocess.run(
        [cargo, *BUILD_COMMAND[1:]], cwd=ROOT, stdin=subprocess.DEVNULL, check=False
    )
    if completed.returncode != 0:
        raise MatrixError("pinned release build failed")
    if cargo_environment_audit() != environment or cargo_configuration_audit() != configuration:
        raise MatrixError("Cargo environment/configuration changed during build")
    for path in (cligen, overlay):
        if not path.is_file() or not os.access(path, os.X_OK):
            raise MatrixError(f"release executable is missing: {path}")
    return {
        "command": list(BUILD_COMMAND),
        "cargo": cargo,
        "rustc": rustc,
        "rustc_version": command_output([rustc, "--version", "--verbose"]),
        "cargo_version": command_output([cargo, "--version", "--verbose"]),
        "cargo_environment": environment,
        "active_cargo_configuration": configuration,
    }


def copy_file_exact(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise MatrixError(f"snapshot destination already exists: {destination}")
    shutil.copy2(source, destination)
    if sha256_path(destination) != sha256_path(source) or destination.stat().st_size != source.stat().st_size:
        raise MatrixError(f"snapshot copy differs: {source} -> {destination}")


def load_fit_inputs(
    cache: Path,
    fit_directory: Path,
    snapshot: Path,
    cligen_sha256: str,
    implementation_commit: str,
) -> tuple[list[StationInput], dict[str, Any]]:
    if fit_directory.resolve(strict=False) != EXPECTED_FIT_DIRECTORY.resolve(strict=False):
        raise MatrixError(f"fit directory must be {EXPECTED_FIT_DIRECTORY}")
    if not fit_directory.is_dir():
        raise MatrixError(f"fit directory is missing: {fit_directory}")
    config = require_object(strict_json(CORPUS_CONFIG), "A5a corpus config")
    stations_value = config.get("stations")
    if not isinstance(stations_value, list) or len(stations_value) != 17:
        raise MatrixError("A5a corpus does not contain exactly 17 stations")
    station_ids = [station.get("station_id") for station in stations_value]
    if any(not isinstance(station_id, str) for station_id in station_ids) or len(set(station_ids)) != 17:
        raise MatrixError("A5a corpus station order contains invalid or duplicate IDs")
    config_sha = sha256_path(CORPUS_CONFIG)
    a5a_source_sha = sha256_path(A5A_SOURCE_MANIFEST)
    observed_sha = sha256_path(OBSERVED_CORPUS)

    source_path = fit_directory / FIT_SOURCE_NAME
    manifest_path = fit_directory / FIT_MANIFEST_NAME
    golden_path = fit_directory / FIT_GOLDEN_NAME
    source = require_object(strict_json(source_path), "fit source manifest")
    manifest = require_object(strict_json(manifest_path), "fit manifest")
    golden = require_object(strict_json(golden_path), "fit golden")
    fitter_module = load_module("a5b_fit_models_runtime_v1", FITTER)
    fitter_module.validate_source_manifest_shape(source)
    fitter_module.validate_fit_manifest_shape(manifest)
    fitter_module.validate_golden_shape(golden)
    fitter_sha = sha256_path(FITTER)
    if (
        manifest["fitter"]["path"] != repo_relative(FITTER)
        or manifest["fitter"]["sha256"] != fitter_sha
    ):
        raise MatrixError("fit manifest binds a different fitter")
    if (
        manifest["implementation_base_commit"] != implementation_commit
        or golden["implementation_base_commit"] != implementation_commit
    ):
        raise MatrixError("fit manifest implementation base commit differs from HEAD")
    if (
        manifest["inputs"]["cligen_executable_sha256"] != cligen_sha256
        or manifest["inputs"]["corpus_config_sha256"] != config_sha
        or manifest["inputs"]["a5a_source_manifest_sha256"] != a5a_source_sha
        or manifest["inputs"]["station_collection"] != config["station_collection"]
    ):
        raise MatrixError("fit manifest cligen binary differs from candidate build")
    if source["corpus_config"] != {
        "path": repo_relative(CORPUS_CONFIG),
        "sha256": config_sha,
    } or source["a5a_source_manifest"] != {
        "path": repo_relative(A5A_SOURCE_MANIFEST),
        "sha256": a5a_source_sha,
    }:
        raise MatrixError("fit source manifest differs from the frozen A5a inputs")
    if [row.get("station_id") for row in source["stations"]] != station_ids:
        raise MatrixError("fit source manifest station order differs from A5a")
    if [row.get("station_id") for row in manifest["stations"]] != station_ids:
        raise MatrixError("fit manifest station order differs from A5a")
    if manifest["output_contract"] != {
        "station_schema_version": 2,
        "station_document_role": "a5b_interannual_candidate_bundle_v1",
        "bundle_schema_path": repo_relative(STATION_SCHEMA),
        "bundle_schema_sha256": sha256_path(STATION_SCHEMA),
        "station_count": 17,
        "candidate_order": [row[0] for row in CANDIDATES],
    }:
        raise MatrixError("fit output contract differs from the frozen station bundle")
    if golden["source_manifest_sha256"] != sha256_path(source_path):
        raise MatrixError("fit golden source manifest hash differs")
    if golden["fit_manifest_sha256"] != sha256_path(manifest_path):
        raise MatrixError("fit golden manifest hash differs")

    diagnostics_relative = PurePosixPath(manifest["diagnostics"]["path"])
    if (
        diagnostics_relative != PurePosixPath("diagnostics/fit-diagnostics-v1.json")
        or diagnostics_relative.is_absolute()
        or ".." in diagnostics_relative.parts
    ):
        raise MatrixError("fit diagnostics path differs or is unsafe")
    diagnostics_path = (fit_directory / Path(*diagnostics_relative.parts)).resolve(strict=True)
    if not diagnostics_path.is_relative_to(fit_directory.resolve(strict=True)):
        raise MatrixError("fit diagnostics escape the fit directory")
    if (
        sha256_path(diagnostics_path) != manifest["diagnostics"]["sha256"]
        or diagnostics_path.stat().st_size != manifest["diagnostics"]["bytes"]
        or golden["diagnostics_sha256"] != manifest["diagnostics"]["sha256"]
    ):
        raise MatrixError("fit diagnostics identity differs")

    fit_station_by_id = {row["station_id"]: row for row in manifest["stations"]}
    if len(fit_station_by_id) != 17:
        raise MatrixError("fit manifest station IDs are duplicate or incomplete")
    bundle_validator = fitter_module.bundle_validator()
    result: list[StationInput] = []
    par_items: list[tuple[str, bytes]] = []
    bundle_items: list[tuple[str, bytes]] = []
    for station in stations_value:
        station_id = station.get("station_id")
        regime = station.get("regime")
        if not isinstance(station_id, str) or regime not in ("arid", "monsoonal", "humid", "cold", "fixture"):
            raise MatrixError(f"invalid A5a station identity/regime: {station_id!r}/{regime!r}")
        par_source = cache / f"{station_id}.par"
        if not par_source.is_file() or sha256_path(par_source) != station["par_sha256"]:
            raise MatrixError(f"{station_id}: cache station parameter identity differs")
        par_items.append((station_id, par_source.read_bytes()))
        fit_station = fit_station_by_id.get(station_id)
        if fit_station is None or fit_station["base_par_sha256"] != station["par_sha256"]:
            raise MatrixError(f"{station_id}: fit/base parameter identity differs")
        bundle_relative = PurePosixPath(fit_station["station_bundle"])
        if bundle_relative.is_absolute() or ".." in bundle_relative.parts:
            raise MatrixError(f"{station_id}: unsafe fit bundle path")
        bundle_source = (fit_directory / Path(*bundle_relative.parts)).resolve(strict=True)
        if not bundle_source.is_relative_to(fit_directory.resolve(strict=True)):
            raise MatrixError(f"{station_id}: fit bundle escapes fit directory")
        if (
            sha256_path(bundle_source) != fit_station["station_bundle_sha256"]
            or bundle_source.stat().st_size != fit_station["station_bundle_bytes"]
            or golden["bundle_sha256"].get(station_id) != fit_station["station_bundle_sha256"]
        ):
            raise MatrixError(f"{station_id}: fit bundle identity differs")
        bundle_items.append((station_id, bundle_source.read_bytes()))
        bundle_value = require_object(strict_json(bundle_source), f"{station_id} bundle")
        fitter_module.validate_bundle_semantics(bundle_value, station["par_sha256"], fitter_sha)
        fitter_module.validate_bundle_schema(bundle_value, bundle_validator)
        extensions = {row["candidate_id"]: row for row in bundle_value["extensions"]}
        if tuple(extensions) != tuple(row[0] for row in CANDIDATES):
            raise MatrixError(f"{station_id}: bundle candidate order differs")

        par_snapshot = snapshot / "stations" / par_source.name
        bundle_snapshot = snapshot / "fit" / FIT_BUNDLE_DIRECTORY / bundle_source.name
        copy_file_exact(par_source, par_snapshot)
        copy_file_exact(bundle_source, bundle_snapshot)
        result.append(
            StationInput(
                station_id,
                regime,
                par_snapshot,
                station["par_sha256"],
                bundle_source,
                bundle_snapshot,
                fit_station["station_bundle_sha256"],
                bundle_value,
                extensions,
            )
        )

    par_aggregate = fitter_module.aggregate_bundle_sha256(par_items)
    bundle_aggregate = fitter_module.aggregate_bundle_sha256(bundle_items)
    if par_aggregate != manifest["inputs"]["station_par_aggregate_sha256"]:
        raise MatrixError("fit station-parameter aggregate identity differs")
    if (
        manifest["repeatability"]
        != {
            "passes": 2,
            "byte_identical": True,
            "bundle_aggregate_sha256": bundle_aggregate,
        }
        or golden["bundle_aggregate_sha256"] != bundle_aggregate
    ):
        raise MatrixError("fit bundle repeatability aggregate differs")

    fit_snapshot = snapshot / "fit"
    for source_artifact in fit_directory.rglob("*"):
        if not source_artifact.is_file() or source_artifact.parent.name == FIT_BUNDLE_DIRECTORY:
            continue
        relative = source_artifact.relative_to(fit_directory)
        copy_file_exact(source_artifact, fit_snapshot / relative)
    fit_section = {
        "source_manifest": artifact_for_path(source_path),
        "fit_manifest": artifact_for_path(manifest_path),
        "bundles": [artifact_for_path(station.bundle) for station in result],
    }
    if observed_sha != "4d0987bb172aef76f3f3a48704bf9df78a375d9d562a145f435800042b5b5660":
        raise MatrixError("observed target corpus identity differs from accepted A5a")
    return result, fit_section


def build_jobs(stations: Sequence[StationInput | dict[str, Any]]) -> list[Job]:
    result: list[Job] = []
    for candidate_id, station_model, profile in CANDIDATES:
        for station in stations:
            station_id = station.station_id if isinstance(station, StationInput) else station["station_id"]
            regime = station.regime if isinstance(station, StationInput) else station["regime"]
            for horizon in HORIZONS:
                for replicate, burn, seed in REPLICATES:
                    result.append(
                        Job(
                            station_id,
                            regime,
                            candidate_id,
                            station_model,
                            profile,
                            horizon,
                            replicate,
                            burn,
                            seed,
                        )
                    )
    assert_job_matrix(result, [station.station_id if isinstance(station, StationInput) else station["station_id"] for station in stations])
    return result


def build_base_jobs(stations: Sequence[StationInput | dict[str, Any]]) -> list[BaseJob]:
    result: list[BaseJob] = []
    for station in stations:
        station_id = station.station_id if isinstance(station, StationInput) else station["station_id"]
        regime = station.regime if isinstance(station, StationInput) else station["regime"]
        for horizon in HORIZONS:
            for replicate, burn, _ in REPLICATES:
                result.append(BaseJob(station_id, regime, horizon, replicate, burn))
    keys = [base_key(job) for job in result]
    expected = set(itertools.product(
        [station.station_id if isinstance(station, StationInput) else station["station_id"] for station in stations],
        HORIZONS,
        range(8),
    ))
    if len(keys) != 272 or len(set(keys)) != 272 or set(keys) != expected:
        raise MatrixError("faithful base matrix is not the frozen 272-key Cartesian product")
    return result


def job_key(job: Job) -> tuple[str, str, int, int]:
    return (job.candidate_id, job.station_id, job.horizon_years, job.replicate)


def base_key(job: Job | BaseJob) -> tuple[str, int, int]:
    return (job.station_id, job.horizon_years, job.replicate)


def expected_job_keys(station_ids: Sequence[str]) -> set[tuple[str, str, int, int]]:
    return set(itertools.product((row[0] for row in CANDIDATES), station_ids, HORIZONS, range(8)))


def assert_job_matrix(jobs: Sequence[Job], station_ids: Sequence[str]) -> None:
    keys = [job_key(job) for job in jobs]
    if len(keys) != EXPECTED_RUNS or len(set(keys)) != EXPECTED_RUNS:
        raise MatrixError("candidate job matrix is not 1,904 unique keys")
    if set(keys) != expected_job_keys(station_ids):
        raise MatrixError("candidate job keys differ from the frozen Cartesian product")
    for job in jobs:
        replicate, burn, seed = REPLICATE_BY_INDEX[job.replicate]
        candidate = CANDIDATE_BY_ID[job.candidate_id]
        if (
            replicate != job.replicate
            or burn != job.legacy_burn
            or seed != job.extension_seed
            or candidate[1] != job.station_model
            or candidate[2] != job.generation_profile
        ):
            raise MatrixError("candidate job mapping differs from frozen identities")


def run_stem(job: Job) -> str:
    return (
        f"{job.station_id}-{job.candidate_id}-{job.horizon_years}yr-"
        f"rep{job.replicate}-burn{job.legacy_burn}"
    )


def base_stem(job: Job | BaseJob) -> str:
    return (
        f"{job.station_id}-{job.horizon_years}yr-rep{job.replicate}-"
        f"burn{job.legacy_burn}"
    )


def base_runspec_member_name(job: Job | BaseJob) -> str:
    return f"runspecs/{base_stem(job)}.yaml"


def base_provenance_member_name(job: Job | BaseJob) -> str:
    return f"provenance/{base_stem(job)}.provenance.json"


def plan_member_name(job: Job) -> str:
    return (
        f"plans/{job.station_id}-{job.candidate_id}-rep{job.replicate}-"
        f"burn{job.legacy_burn}.plan.json"
    )


def quality_member_name(job: Job) -> str:
    return f"quality-reports/{run_stem(job)}.quality.json"


def diagnostics_member_name(job: Job) -> str:
    return f"overlay-diagnostics/{run_stem(job)}.diagnostics.json"


def run_record_member_name(job: Job) -> str:
    return f"run-records/{run_stem(job)}.run.json"


def candidate_cli_path(target: Path, job: Job) -> Path:
    return target / CLI_DIRECTORY_NAME / job.candidate_id / f"{run_stem(job)}.cli"


def runspec_bytes(job: BaseJob, par: Path, base_cli: Path) -> bytes:
    text = "\n".join(
        [
            "cligen_runspec: 1",
            "station:",
            f"  par: {json.dumps(str(par))}",
            "mode: continuous",
            "simulation:",
            "  begin_year: 1",
            f"  years: {job.horizon_years}",
            "  interpolation: none",
            "rng:",
            f"  burn: {job.legacy_burn}",
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
    return text.encode("utf-8")


def days_in_horizon(years: int) -> int:
    leap = sum(year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) for year in range(1, years + 1))
    return years * 365 + leap


def subprocess_bytes(command: Sequence[str], label: str) -> bytes:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise MatrixError(f"{label} failed ({completed.returncode}): {stderr}")
    if completed.stderr:
        raise MatrixError(f"{label} wrote unexpected stderr: {completed.stderr.decode(errors='replace').strip()}")
    return completed.stdout


def write_new(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
    except FileExistsError as error:
        raise MatrixError(f"refusing to overwrite artifact: {path}") from error
    except OSError as error:
        raise MatrixError(f"cannot publish artifact {path}: {error}") from error


def publish_new_file(source: Path, destination: Path) -> None:
    """Atomically publish one staged file without an overwrite race."""

    if not source.is_file() or source.stat().st_size < 1:
        raise MatrixError(f"publication source is missing or empty: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except FileExistsError as error:
        raise MatrixError(f"refusing to overwrite published artifact: {destination}") from error
    except OSError as error:
        raise MatrixError(f"cannot atomically publish {destination}: {error}") from error
    try:
        if (
            destination.stat().st_size != source.stat().st_size
            or sha256_path(destination) != sha256_path(source)
        ):
            raise MatrixError(f"published artifact differs from staging: {destination}")
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    try:
        source.unlink()
    except OSError as error:
        destination.unlink(missing_ok=True)
        raise MatrixError(
            f"cannot retire staging link after publishing {destination}: {error}"
        ) from error


def extension_domain_sha256(job: Job) -> str:
    seed = int(job.extension_seed[2:], 16).to_bytes(8, "big")
    material = (
        b"cligen-a5b-extension-v1\0"
        + job.station_id.encode("ascii")
        + b"\0"
        + job.generation_profile.encode("ascii")
        + b"\0"
        + seed
    )
    return sha256_bytes(material)


def validate_plan_for_job(
    plan: dict[str, Any],
    plan_raw: bytes,
    job: Job,
    extension: dict[str, Any],
    plan_module: Any,
) -> None:
    plan_module.validate_plan(plan)
    validate_schema(plan, PLAN_SCHEMA, "A5b overlay plan")
    expected = {
        "station_id": job.station_id,
        "station_model": job.station_model,
        "candidate_profile": job.generation_profile,
        "extension_seed": job.extension_seed,
        "coefficient_payload_sha256": extension["diagnostics"]["payload_sha256"],
    }
    if any(plan.get(name) != value for name, value in expected.items()):
        raise MatrixError(f"{run_stem(job)}: plan identity differs")
    if not plan_raw.endswith(b"\n") or strict_json_bytes(plan_raw, "generated plan") != plan:
        raise MatrixError(f"{run_stem(job)}: plan bytes are not strict deterministic JSON+LF")


def generate_plans(
    stations: Sequence[StationInput],
    staging: Path,
) -> dict[tuple[str, str, int], PlanInput]:
    plan_module = load_module("a5b_plan_generator_matrix_v1", PLAN_GENERATOR)
    result: dict[tuple[str, str, int], PlanInput] = {}
    for candidate_id, station_model, profile in CANDIDATES:
        candidate_root = staging / candidate_id
        for station in stations:
            extension = station.extensions[candidate_id]
            for replicate, burn, seed in REPLICATES:
                job = Job(
                    station.station_id,
                    station.regime,
                    candidate_id,
                    station_model,
                    profile,
                    30,
                    replicate,
                    burn,
                    seed,
                )
                value = plan_module.generate_plan(station.bundle_value, candidate_id, seed)
                raw = plan_module.plan_json_bytes(value)
                member = plan_member_name(job)
                path = candidate_root / Path(*PurePosixPath(member).parts)
                write_new(path, raw)
                validate_plan_for_job(value, raw, job, extension, plan_module)
                result[(candidate_id, station.station_id, replicate)] = PlanInput(
                    path, member_for_path(member, path), value
                )
    if len(result) != 7 * 17 * 8:
        raise MatrixError("plan generation did not produce exactly 952 plans")
    return result


def preflight_real_plans(fit_directory: Path) -> dict[str, Any]:
    """Generate and validate all frozen plans without creating campaign output."""

    if fit_directory.resolve(strict=False) != EXPECTED_FIT_DIRECTORY.resolve(strict=False):
        raise MatrixError(f"fit directory must be {EXPECTED_FIT_DIRECTORY}")
    manifest_path = fit_directory / FIT_MANIFEST_NAME
    manifest = require_object(strict_json(manifest_path), "fit manifest plan preflight")
    fitter_module = load_module("a5b_fit_models_plan_preflight_v1", FITTER)
    fitter_module.validate_fit_manifest_shape(manifest)
    config = require_object(strict_json(CORPUS_CONFIG), "A5a corpus config plan preflight")
    station_ids = [row.get("station_id") for row in config.get("stations", [])]
    fit_rows = manifest.get("stations")
    if (
        len(station_ids) != 17
        or not isinstance(fit_rows, list)
        or [row.get("station_id") for row in fit_rows] != station_ids
    ):
        raise MatrixError("plan preflight fit station order differs from A5a")
    plan_module = load_module("a5b_plan_generator_preflight_v1", PLAN_GENERATOR)
    items: list[tuple[str, bytes]] = []
    bundles: dict[str, dict[str, Any]] = {}
    for row in fit_rows:
        station_id = row["station_id"]
        expected_member = f"{FIT_BUNDLE_DIRECTORY}/{station_id}.a5b.station.json"
        if row["station_bundle"] != expected_member:
            raise MatrixError(f"{station_id}: plan preflight bundle path differs")
        bundle_path = fit_directory / Path(*PurePosixPath(expected_member).parts)
        if (
            not bundle_path.is_file()
            or bundle_path.stat().st_size != row["station_bundle_bytes"]
            or sha256_path(bundle_path) != row["station_bundle_sha256"]
        ):
            raise MatrixError(f"{station_id}: plan preflight bundle identity differs")
        bundle = require_object(strict_json(bundle_path), f"{station_id} plan preflight bundle")
        validate_schema(bundle, STATION_SCHEMA, f"{station_id} plan preflight bundle")
        plan_module.validate_bundle(bundle)
        bundles[station_id] = bundle

    for candidate_id, station_model, profile in CANDIDATES:
        for station_id in station_ids:
            bundle = bundles[station_id]
            extensions = {
                extension["candidate_id"]: extension for extension in bundle["extensions"]
            }
            extension = extensions[candidate_id]
            for replicate, burn, seed in REPLICATES:
                job = Job(
                    station_id,
                    "preflight",
                    candidate_id,
                    station_model,
                    profile,
                    30,
                    replicate,
                    burn,
                    seed,
                )
                plan = plan_module.generate_plan(bundle, candidate_id, seed)
                raw = plan_module.plan_json_bytes(plan)
                validate_plan_for_job(plan, raw, job, extension, plan_module)
                items.append((plan_member_name(job), raw))
    if len(items) != 7 * 17 * 8 or len({name for name, _ in items}) != len(items):
        raise MatrixError("plan preflight did not cover 952 unique plans")
    return {
        "plans": len(items),
        "aggregate_sha256": aggregate_named_bytes(items),
    }


def validate_base_provenance(
    provenance: dict[str, Any],
    job: BaseJob,
    station: StationInput,
    base_cli_sha256: str,
) -> str:
    validate_schema(provenance, PROVENANCE_SCHEMA, "base provenance")
    if (
        provenance["origin"] != "generated"
        or provenance["station"]["input_sha256"] != station.par_sha256
        or provenance["station"]["legacy_source_sha256"] != station.par_sha256
        or provenance["generation"]
        != {
            "profile": "faithful_5_32_3",
            "qc_policy": "off",
            "mode": "continuous",
            "interpolation": "none",
            "rng_scheme": "cligen_randn_5_32_3",
            "burn_per_stream": job.legacy_burn,
        }
        or provenance["effective_runspec"]["begin_year"] != 1
        or provenance["effective_runspec"]["years"] != job.horizon_years
        or provenance["effective_runspec"]["output"]["quality"] is not False
        or provenance["effective_runspec"]["output"]["command_echo"]
        != f"{NEUTRAL_BASE_COMMAND_ECHO} --qc-filter off"
        or provenance["artifact"]["content_sha256"] != base_cli_sha256
        or provenance["actual"]["emitted_day_count"] != days_in_horizon(job.horizon_years)
    ):
        raise MatrixError(f"{base_stem(job)}: base provenance semantics differ")
    return require_sha256(provenance["effective_runspec_sha256"], "base run ID")


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


def validate_overlay_diagnostics(
    diagnostics: dict[str, Any],
    job: Job,
    plan: PlanInput,
    runspec_sha256: str,
    base_cli_sha256: str,
    candidate_cli_sha256: str,
) -> None:
    require_exact_keys(diagnostics, DIAGNOSTIC_KEYS, "overlay diagnostics")
    expected = {
        "diagnostics_schema_version": 1,
        "station_id": job.station_id,
        "station_model": job.station_model,
        "candidate_profile": job.generation_profile,
        "extension_seed": job.extension_seed,
        "coefficient_payload_sha256": plan.value["coefficient_payload_sha256"],
        "state_table_sha256": plan.value["state_table_sha256"],
        "input_runspec_sha256": runspec_sha256,
        "plan_sha256": plan.member["sha256"],
        "faithful_cli_sha256": base_cli_sha256,
        "output_cli_sha256": candidate_cli_sha256,
        "row_count": days_in_horizon(job.horizon_years),
        "plan_state_years": 128,
        "consumed_prefix_years": job.horizon_years,
        "counterfactual_applied": job.candidate_id == "precip_counterfactual",
    }
    if any(diagnostics.get(name) != value for name, value in expected.items()):
        raise MatrixError(f"{run_stem(job)}: overlay diagnostic identity differs")
    integer_fields = (
        "wet_days_before",
        "wet_days_after",
        "temperature_order_repairs",
        "dewpoint_caps",
        "counterfactual_months",
        "relocated_wet_days",
        "reassigned_storm_tuples",
        "precipitation_render_limit_adjustments",
    )
    if any(
        isinstance(diagnostics[field], bool)
        or not isinstance(diagnostics[field], int)
        or diagnostics[field] < 0
        for field in integer_fields
    ):
        raise MatrixError(f"{run_stem(job)}: overlay diagnostic count is invalid")
    if diagnostics["wet_days_before"] != diagnostics["wet_days_after"]:
        raise MatrixError(f"{run_stem(job)}: overlay changed wet-day count")
    expected_months = job.horizon_years * 12 if job.candidate_id == "precip_counterfactual" else 0
    if diagnostics["counterfactual_months"] != expected_months:
        raise MatrixError(f"{run_stem(job)}: counterfactual month count differs")
    final_state = diagnostics["counterfactual_rng_final_state"]
    if job.candidate_id == "precip_counterfactual":
        if not isinstance(final_state, str) or re.fullmatch(r"0x[0-9a-f]{16}", final_state) is None:
            raise MatrixError(f"{run_stem(job)}: counterfactual final RNG state is invalid")
    elif final_state is not None:
        raise MatrixError(f"{run_stem(job)}: non-counterfactual has an RNG final state")
    adjustments = diagnostics["precipitation_factor_adjustments"]
    if not isinstance(adjustments, list) or len(adjustments) != job.horizon_years * 12:
        raise MatrixError(f"{run_stem(job)}: precipitation adjustment table differs")
    adjusted_count = 0
    for index, adjustment_value in enumerate(adjustments):
        adjustment = require_object(
            adjustment_value, f"{run_stem(job)} precipitation adjustment {index}"
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
            f"{run_stem(job)} precipitation adjustment {index}",
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
            or requested != plan.value["annual_states"][year - 1]["precip_factor"][month - 1]
            or requested <= 0.0
            or effective <= 0.0
            or base_max < 0.0
            or render_limit != MAX_RENDERABLE_PRECIP_MM
        ):
            raise MatrixError(
                f"{run_stem(job)}: precipitation adjustment identity differs at "
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
            raise MatrixError(
                f"{run_stem(job)}: precipitation adjustment arithmetic differs at "
                f"year {year} month {month}"
            )
        adjusted_count += int(expected_adjusted)
    if adjusted_count != diagnostics["precipitation_render_limit_adjustments"]:
        raise MatrixError(
            f"{run_stem(job)}: precipitation render-limit adjustment count differs"
        )


def validate_quality_report(
    report: dict[str, Any],
    job: Job,
    station: StationInput,
    candidate_cli_sha256: str,
    parameter_set_sha256: str,
    schema_validation: bool = True,
) -> None:
    if schema_validation:
        validate_schema(report, QUALITY_SCHEMA, "candidate quality report")
    identity = require_object(report.get("identity"), "quality identity")
    content = require_object(identity.get("content"), "quality content identity")
    if (
        report.get("quality_report_schema_version") != 2
        or report.get("metrics_version") != 3
        or identity.get("provenance") is not None
        or report.get("process") is not None
        or content.get("station_model") != "fixed_monthly_5_32_3"
        or content.get("station_source_sha256") != station.par_sha256
        or content.get("station_parameter_set_sha256") != parameter_set_sha256
        or content.get("cli_sha256") != candidate_cli_sha256
        or content.get("days") != days_in_horizon(job.horizon_years)
        or content.get("years") != job.horizon_years
        or content.get("span") != [1, job.horizon_years]
    ):
        raise MatrixError(f"{run_stem(job)}: post-hoc quality identity differs")


def run_record_contracts(contracts: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return {name: contracts[name] for name in RUN_RECORD_CONTRACT_KEYS}


def execute_base(
    job: BaseJob,
    station: StationInput,
    cligen: Path,
    work_root: Path,
    shared_root: Path,
) -> tuple[tuple[str, int, int], BaseInput]:
    stem = base_stem(job)
    work = work_root / "faithful-bases" / stem
    work.mkdir(parents=True, exist_ok=False)
    base_cli = work / "base.cli"
    runspec = work / "base-runspec.yaml"
    runspec_raw = runspec_bytes(job, station.par, base_cli)
    write_new(runspec, runspec_raw)
    runspec_sha = sha256_bytes(runspec_raw)
    shared_runspec = shared_root / base_runspec_member_name(job)
    write_new(shared_runspec, runspec_raw)
    subprocess_bytes([str(cligen), "run", str(runspec)], f"{stem}: faithful base run")
    base_provenance_path = Path(str(base_cli) + ".provenance.json")
    if not base_cli.is_file() or not base_provenance_path.is_file():
        raise MatrixError(f"{stem}: faithful base outputs are incomplete")
    base_cli_sha = sha256_path(base_cli)
    base_provenance_raw = base_provenance_path.read_bytes()
    base_provenance = require_object(
        strict_json_bytes(base_provenance_raw, "base provenance"), "base provenance"
    )
    shared_provenance = shared_root / base_provenance_member_name(job)
    write_new(shared_provenance, base_provenance_raw)
    base_run_id = validate_base_provenance(base_provenance, job, station, base_cli_sha)
    result = BaseInput(
        runspec,
        runspec_sha,
        member_for_path(base_runspec_member_name(job), shared_runspec),
        base_provenance_path,
        sha256_bytes(base_provenance_raw),
        member_for_path(base_provenance_member_name(job), shared_provenance),
        base_cli,
        base_cli_sha,
        base_run_id,
        require_sha256(
            base_provenance["station"]["parameter_set_sha256"],
            "base station parameter-set identity",
        ),
    )
    return base_key(job), result


def assert_base_identities(bases: dict[tuple[str, int, int], BaseInput], phase: str) -> None:
    if len(bases) != 272:
        raise MatrixError(f"{phase}: faithful base matrix count differs")
    for key, base in bases.items():
        if (
            not base.runspec.is_file()
            or sha256_path(base.runspec) != base.runspec_sha256
            or not base.provenance.is_file()
            or sha256_path(base.provenance) != base.provenance_sha256
            or base.runspec_member["sha256"] != base.runspec_sha256
            or base.provenance_member["sha256"] != base.provenance_sha256
            or not base.cli.is_file()
            or sha256_path(base.cli) != base.cli_sha256
        ):
            raise MatrixError(f"{phase}: faithful base identity changed: {key}")


def execute_one(
    job: Job,
    station: StationInput,
    plan: PlanInput,
    base: BaseInput,
    cligen: Path,
    cligen_member: dict[str, Any],
    overlay: Path,
    overlay_member: dict[str, Any],
    target: Path,
    staging: Path,
    contracts: dict[str, dict[str, str]],
    implementation_commit: str,
    corpus_sha256: str,
) -> dict[str, Any]:
    started = time.monotonic_ns()
    stem = run_stem(job)

    candidate_cli = candidate_cli_path(target, job)
    candidate_cli.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_member = diagnostics_member_name(job)
    diagnostics_path = staging / job.candidate_id / Path(*PurePosixPath(diagnostics_member).parts)
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess_bytes(
        [
            str(overlay),
            "--input",
            str(base.runspec),
            "--plan",
            str(plan.path),
            "--output",
            str(candidate_cli),
            "--diagnostics",
            str(diagnostics_path),
        ],
        f"{stem}: A5b overlay",
    )
    candidate_cli_sha = sha256_path(candidate_cli)
    diagnostics = require_object(strict_json(diagnostics_path), "overlay diagnostics")
    validate_overlay_diagnostics(
        diagnostics,
        job,
        plan,
        base.runspec_sha256,
        base.cli_sha256,
        candidate_cli_sha,
    )

    quality_raw = subprocess_bytes(
        [str(cligen), "quality", str(candidate_cli), "--par", str(station.par)],
        f"{stem}: post-hoc quality",
    )
    quality = require_object(strict_json_bytes(quality_raw, "post-hoc quality"), "post-hoc quality")
    validate_quality_report(
        quality,
        job,
        station,
        candidate_cli_sha,
        base.parameter_set_sha256,
    )
    quality_member = quality_member_name(job)
    quality_path = staging / job.candidate_id / Path(*PurePosixPath(quality_member).parts)
    write_new(quality_path, quality_raw)

    elapsed_ms = (time.monotonic_ns() - started) // 1_000_000
    extension = station.extensions[job.candidate_id]
    run_record = {
        "run_record_schema_version": 1,
        "matrix": {
            "station_id": job.station_id,
            "regime": job.regime,
            "candidate_id": job.candidate_id,
            "station_model": job.station_model,
            "generation_profile": job.generation_profile,
            "horizon_years": job.horizon_years,
            "replicate": job.replicate,
            "legacy_burn": job.legacy_burn,
            "extension_seed": job.extension_seed,
        },
        "contracts": run_record_contracts(contracts),
        "inputs": {
            "corpus_schema_version": 1,
            "corpus_content_sha256": corpus_sha256,
            "legacy_par": external_member_with_sha256(station.par, station.par_sha256),
            "augmented_station": external_member_with_sha256(
                station.bundle, station.bundle_sha256
            ),
            "coefficient_payload_sha256": extension["diagnostics"]["payload_sha256"],
            "fit_identity_sha256": extension["fit_identity_sha256"],
            "plan": plan.member,
            "base_runspec_sha256": base.runspec_sha256,
            "base_provenance_sha256": base.provenance_sha256,
            "base_cli_sha256": base.cli_sha256,
            "base_run_id": base.run_id,
        },
        "runtime": {
            "base_generation_profile": "faithful_5_32_3",
            "base_qc_filter": "off",
            "extension_prng": "splitmix64_box_muller_v1",
            "extension_domain_sha256": extension_domain_sha256(job),
            "cligen_binary": cligen_member,
            "overlay_binary": overlay_member,
            "implementation_commit": implementation_commit,
        },
        "outputs": {
            "candidate_cli": external_member_with_sha256(
                candidate_cli, candidate_cli_sha
            ),
            "quality_report": member_for_path(quality_member, quality_path),
            "overlay_diagnostics": member_for_path(diagnostics_member, diagnostics_path),
        },
        "execution": {
            "host_os": platform.system(),
            "host_arch": platform.machine(),
            "wall_time_ms": elapsed_ms,
            "precipitation_clip_count": plan.value["normalization"]["precipitation_clip_count"],
            "precipitation_render_limit_adjustment_count": diagnostics[
                "precipitation_render_limit_adjustments"
            ],
            "temperature_order_repair_count": diagnostics["temperature_order_repairs"],
            "dewpoint_cap_count": diagnostics["dewpoint_caps"],
            "counterfactual_month_count": diagnostics["counterfactual_months"],
            "sealed": True,
        },
    }
    validate_schema(run_record, RUN_RECORD_SCHEMA, "A5b run record")
    record_member = run_record_member_name(job)
    record_path = staging / job.candidate_id / Path(*PurePosixPath(record_member).parts)
    write_new(record_path, canonical_json_bytes(run_record))

    index = {
        "station_id": job.station_id,
        "regime": job.regime,
        "candidate_id": job.candidate_id,
        "horizon_years": job.horizon_years,
        "replicate": job.replicate,
        "legacy_burn": job.legacy_burn,
        "extension_seed": job.extension_seed,
        "archive_candidate_id": job.candidate_id,
        "run_record": member_for_path(record_member, record_path),
        "quality_report": member_for_path(quality_member, quality_path),
        "overlay_diagnostics": member_for_path(diagnostics_member, diagnostics_path),
        "plan": plan.member,
        "candidate_cli_sha256": candidate_cli_sha,
        "candidate_cli_bytes": candidate_cli.stat().st_size,
    }
    return index


def canonical_archive_identity() -> dict[str, Any]:
    return {
        "implementation": "Python stdlib gzip.GzipFile + tarfile",
        "python_version": platform.python_version(),
        "zlib_compile_version": zlib.ZLIB_VERSION,
        "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        "gzip_compresslevel": GZIP_COMPRESSLEVEL,
        "gzip_mtime": FIXED_ARCHIVE_MTIME,
        "tar_format": "ustar",
        "tar_member_mtime": FIXED_ARCHIVE_MTIME,
        "tar_member_uid": 0,
        "tar_member_gid": 0,
        "tar_member_mode": "0644",
        "member_order": "lexicographic",
    }


def validate_archive(
    archive_path: Path,
    sources: Sequence[tuple[str, Path]],
) -> None:
    expected = {name: path for name, path in sources}
    names: list[str] = []
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            safe_member_name(member.name)
            if not member.isfile():
                raise MatrixError(f"canonical archive contains non-file member: {member.name}")
            if member.name in names:
                raise MatrixError(f"canonical archive contains duplicate member: {member.name}")
            if (
                member.mtime != FIXED_ARCHIVE_MTIME
                or member.mode != FIXED_ARCHIVE_MODE
                or member.uid != 0
                or member.gid != 0
                or member.uname != ""
                or member.gname != ""
            ):
                raise MatrixError(f"canonical archive metadata differs: {member.name}")
            source = expected.get(member.name)
            if source is None or member.size != source.stat().st_size:
                raise MatrixError(f"canonical archive has unexpected member/size: {member.name}")
            handle = archive.extractfile(member)
            if handle is None:
                raise MatrixError(f"cannot extract canonical archive member: {member.name}")
            if sha256_bytes(handle.read()) != sha256_path(source):
                raise MatrixError(f"canonical archive member hash differs: {member.name}")
            names.append(member.name)
    if names != sorted(expected) or len(names) != len(expected):
        raise MatrixError("canonical archive member order or closure differs")


def write_canonical_archive(
    destination: Path,
    sources: Sequence[tuple[str, Path]],
    *,
    require_repo_relative: bool = True,
    identity_path: Path | None = None,
) -> dict[str, Any]:
    if destination.exists():
        raise MatrixError(f"refusing to overwrite candidate archive: {destination}")
    names = [name for name, _ in sources]
    for name in names:
        safe_member_name(name)
    if len(names) != len(set(names)):
        raise MatrixError("candidate archive source names are not unique")
    ordered = sorted(sources, key=lambda row: row[0])
    for name, source in ordered:
        if not source.is_file() or source.stat().st_size < 1:
            raise MatrixError(f"candidate archive source is missing/empty: {name}: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                compresslevel=GZIP_COMPRESSLEVEL,
                fileobj=raw,
                mtime=FIXED_ARCHIVE_MTIME,
            ) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                    for name, source in ordered:
                        info = tarfile.TarInfo(name)
                        info.size = source.stat().st_size
                        info.mtime = FIXED_ARCHIVE_MTIME
                        info.mode = FIXED_ARCHIVE_MODE
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        with source.open("rb") as handle:
                            archive.addfile(info, handle)
        validate_archive(temporary, ordered)
        if destination.exists():
            raise MatrixError(f"candidate archive appeared during publication: {destination}")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    identity = {
        "path": (
            repo_relative(identity_path or destination)
            if require_repo_relative
            else (identity_path or destination).name
        ),
        "sha256": sha256_path(destination),
        "bytes": destination.stat().st_size,
    }
    return identity


def archive_sources(staging: Path, candidate_id: str) -> list[tuple[str, Path]]:
    root = staging / candidate_id
    sources = [
        (path.relative_to(root).as_posix(), path)
        for path in root.rglob("*")
        if path.is_file()
    ]
    sources.sort(key=lambda row: row[0])
    if len(sources) != MEMBERS_PER_CANDIDATE:
        raise MatrixError(
            f"{candidate_id}: archive staging contains {len(sources)} members, "
            f"expected {MEMBERS_PER_CANDIDATE}"
        )
    return sources


def shared_base_sources(staging: Path) -> list[tuple[str, Path]]:
    root = staging / "shared-bases"
    sources = [
        (path.relative_to(root).as_posix(), path)
        for path in root.rglob("*")
        if path.is_file()
    ]
    sources.sort(key=lambda row: row[0])
    if len(sources) != SHARED_BASE_MEMBER_COUNT:
        raise MatrixError(
            f"shared-base staging contains {len(sources)} members, "
            f"expected {SHARED_BASE_MEMBER_COUNT}"
        )
    return sources


def shared_base_records(
    bases: dict[tuple[str, int, int], BaseInput],
    station_ids: Sequence[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for station_id in station_ids:
        for horizon in HORIZONS:
            for replicate, burn, _ in REPLICATES:
                base = bases[(station_id, horizon, replicate)]
                records.append(
                    {
                        "station_id": station_id,
                        "horizon_years": horizon,
                        "replicate": replicate,
                        "legacy_burn": burn,
                        "runspec": base.runspec_member,
                        "provenance": base.provenance_member,
                        "base_cli_sha256": base.cli_sha256,
                        "base_run_id": base.run_id,
                        "parameter_set_sha256": base.parameter_set_sha256,
                    }
                )
    if len(records) != SHARED_BASE_COUNT:
        raise MatrixError("shared-base index does not contain exactly 272 records")
    return records


def archive_path(candidate_id: str) -> Path:
    return CLIMATE_DIR / f"candidate-evidence-{candidate_id}-v1.tar.gz"


def shared_base_archive_path() -> Path:
    return CLIMATE_DIR / "shared-base-evidence-v1.tar.gz"


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def validate_manifest_semantics(
    manifest: dict[str, Any],
    station_regimes: dict[str, str],
    candidate_cli_root: Path | None,
) -> None:
    require_exact_keys(manifest["contracts"], set(CONTRACT_PATHS), "manifest contracts")
    for name, path in CONTRACT_PATHS.items():
        if manifest["contracts"][name]["path"] != repo_relative(path):
            raise MatrixError(f"manifest contract path differs: {name}")
    if (
        manifest["matrix"]["horizons"] != list(HORIZONS)
        or manifest["matrix"]["expected_runs"] != EXPECTED_RUNS
    ):
        raise MatrixError("manifest horizon/run-count contract differs")
    if [row["candidate_id"] for row in manifest["matrix"]["candidates"]] != [row[0] for row in CANDIDATES]:
        raise MatrixError("manifest candidate order differs")
    if manifest["matrix"]["candidates"] != [
        {"candidate_id": row[0], "station_model": row[1], "generation_profile": row[2]}
        for row in CANDIDATES
    ]:
        raise MatrixError("manifest candidate model/profile mapping differs")
    if manifest["matrix"]["replicates"] != [
        {"replicate": row[0], "legacy_burn": row[1], "extension_seed": row[2]}
        for row in REPLICATES
    ]:
        raise MatrixError("manifest replicate mapping differs")
    station_ids = manifest["corpus"]["station_ids"]
    if station_ids != list(station_regimes) or len(station_ids) != 17:
        raise MatrixError("manifest station order/set differs")
    archives = manifest["archives"]
    if [row["candidate_id"] for row in archives] != [row[0] for row in CANDIDATES] or any(
        row["member_count"] != MEMBERS_PER_CANDIDATE for row in archives
    ):
        raise MatrixError("manifest candidate archive order/count differs")
    for row in archives:
        if row["format"] != "tar+gzip-canonical-v1" or row["artifact"]["path"] != repo_relative(
            archive_path(row["candidate_id"])
        ):
            raise MatrixError(f"manifest archive path/format differs: {row['candidate_id']}")

    shared = manifest["shared_bases"]
    if (
        shared["format"] != "tar+gzip-canonical-v1"
        or shared["artifact"]["path"] != repo_relative(shared_base_archive_path())
        or shared["base_count"] != SHARED_BASE_COUNT
        or shared["member_count"] != SHARED_BASE_MEMBER_COUNT
    ):
        raise MatrixError("manifest shared-base archive identity/count differs")
    expected_base_keys = [
        (station_id, horizon, replicate)
        for station_id in manifest["corpus"]["station_ids"]
        for horizon in HORIZONS
        for replicate in range(8)
    ]
    base_records = shared["records"]
    actual_base_keys = [
        (row["station_id"], row["horizon_years"], row["replicate"])
        for row in base_records
    ]
    if actual_base_keys != expected_base_keys:
        raise MatrixError("manifest shared-base record order/closure differs")
    shared_members: set[str] = set()
    for row in base_records:
        _, burn, _ = REPLICATE_BY_INDEX[row["replicate"]]
        base_job = BaseJob(
            row["station_id"],
            station_regimes[row["station_id"]],
            row["horizon_years"],
            row["replicate"],
            burn,
        )
        if (
            row["legacy_burn"] != burn
            or row["runspec"]["member"] != base_runspec_member_name(base_job)
            or row["provenance"]["member"] != base_provenance_member_name(base_job)
        ):
            raise MatrixError("manifest shared-base member mapping differs")
        shared_members.add(row["runspec"]["member"])
        shared_members.add(row["provenance"]["member"])
    if len(shared_members) != SHARED_BASE_MEMBER_COUNT:
        raise MatrixError("manifest shared-base members are not 544 unique identities")

    expected_fit_paths = [
        repo_relative(EXPECTED_FIT_DIRECTORY / FIT_BUNDLE_DIRECTORY / f"{station_id}.a5b.station.json")
        for station_id in station_ids
    ]
    if (
        manifest["fit"]["source_manifest"]["path"]
        != repo_relative(EXPECTED_FIT_DIRECTORY / FIT_SOURCE_NAME)
        or manifest["fit"]["fit_manifest"]["path"]
        != repo_relative(EXPECTED_FIT_DIRECTORY / FIT_MANIFEST_NAME)
        or [row["path"] for row in manifest["fit"]["bundles"]] != expected_fit_paths
    ):
        raise MatrixError("manifest fit artifact paths differ")
    snapshot_binary_root = EXPECTED_TARGET / SNAPSHOT_NAME / "binaries"
    if (
        manifest["build"]["cligen_binary"]["path"]
        != repo_relative(snapshot_binary_root / "cligen")
        or manifest["build"]["overlay_binary"]["path"]
        != repo_relative(snapshot_binary_root / "cligen-a5b-overlay")
    ):
        raise MatrixError("manifest binary artifact paths differ")
    plan_preflight = manifest["build"]["plan_preflight"]
    if (
        plan_preflight["plans"] != 7 * 17 * 8
        or re.fullmatch(r"[0-9a-f]{64}", plan_preflight["aggregate_sha256"])
        is None
    ):
        raise MatrixError("manifest plan preflight identity differs")

    runs = manifest["runs"]
    keys = [
        (row["candidate_id"], row["station_id"], row["horizon_years"], row["replicate"])
        for row in runs
    ]
    expected_order = [
        (candidate[0], station_id, horizon, replicate)
        for candidate in CANDIDATES
        for station_id in station_ids
        for horizon in HORIZONS
        for replicate in range(8)
    ]
    if (
        len(keys) != EXPECTED_RUNS
        or len(set(keys)) != EXPECTED_RUNS
        or set(keys) != expected_job_keys(station_ids)
        or keys != expected_order
    ):
        raise MatrixError("manifest run matrix closure differs")
    shared_plans: dict[tuple[str, str, int], tuple[str, str, int]] = {}
    record_members: set[tuple[str, str]] = set()
    quality_members: set[tuple[str, str]] = set()
    diagnostic_members: set[tuple[str, str]] = set()
    for row in runs:
        candidate = CANDIDATE_BY_ID[row["candidate_id"]]
        replicate, burn, seed = REPLICATE_BY_INDEX[row["replicate"]]
        job = Job(
            row["station_id"],
            station_regimes[row["station_id"]],
            candidate[0],
            candidate[1],
            candidate[2],
            row["horizon_years"],
            replicate,
            burn,
            seed,
        )
        if (
            row["regime"] != job.regime
            or row["legacy_burn"] != burn
            or row["extension_seed"] != seed
            or row["archive_candidate_id"] != candidate[0]
            or row["plan"]["member"] != plan_member_name(job)
            or row["quality_report"]["member"] != quality_member_name(job)
            or row["overlay_diagnostics"]["member"] != diagnostics_member_name(job)
            or row["run_record"]["member"] != run_record_member_name(job)
        ):
            raise MatrixError("manifest run/member mapping differs")
        plan_key = (candidate[0], row["station_id"], row["replicate"])
        plan_identity = (
            row["plan"]["member"],
            row["plan"]["sha256"],
            row["plan"]["bytes"],
        )
        prior_plan = shared_plans.setdefault(plan_key, plan_identity)
        if prior_plan != plan_identity:
            raise MatrixError(f"manifest horizon plans differ: {plan_key}")
        record_members.add((candidate[0], row["run_record"]["member"]))
        quality_members.add((candidate[0], row["quality_report"]["member"]))
        diagnostic_members.add((candidate[0], row["overlay_diagnostics"]["member"]))
        if candidate_cli_root is not None:
            cli = candidate_cli_root / candidate[0] / f"{run_stem(job)}.cli"
            if (
                not cli.is_file()
                or cli.stat().st_size != row["candidate_cli_bytes"]
                or sha256_path(cli) != row["candidate_cli_sha256"]
            ):
                raise MatrixError(f"candidate CLI identity differs: {cli}")
    if (
        len(shared_plans) != 7 * PLANS_PER_CANDIDATE
        or len(record_members) != EXPECTED_RUNS
        or len(quality_members) != EXPECTED_RUNS
        or len(diagnostic_members) != EXPECTED_RUNS
    ):
        raise MatrixError("manifest member uniqueness/plan sharing differs")
    removed = manifest["execution"]["candidate_cli_bytes_removed_after_wepp"]
    if removed is False and candidate_cli_root is None:
        raise MatrixError("unremoved candidate CLI bytes require a CLI root for validation")
    if manifest["execution"]["workers"] > MAX_WORKERS or manifest["execution"]["failures"] != []:
        raise MatrixError("manifest execution worker/failure contract differs")
    for section in (
        manifest["contracts"].values(),
        (manifest["fit"]["source_manifest"], manifest["fit"]["fit_manifest"]),
        manifest["fit"]["bundles"],
        (manifest["build"]["cligen_binary"], manifest["build"]["overlay_binary"]),
        (manifest["shared_bases"],),
        manifest["archives"],
    ):
        for value in section:
            artifact = value["artifact"] if "artifact" in value else value
            if "path" in artifact:
                resolve_repo_path(artifact["path"], "manifest artifact", require_file=False)


def build_manifest(
    contracts: dict[str, dict[str, str]],
    stations: Sequence[StationInput],
    fit_section: dict[str, Any],
    build_section: dict[str, Any],
    shared_bases: dict[str, Any],
    archives: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    workers: int,
    started_utc: datetime,
    completed_utc: datetime,
    wall_time_seconds: float,
) -> dict[str, Any]:
    return {
        "candidate_evidence_manifest_version": 1,
        "status": "sealed",
        "contracts": contracts,
        "corpus": {
            "schema_version": 1,
            "content_sha256": sha256_path(OBSERVED_CORPUS),
            "station_ids": [station.station_id for station in stations],
        },
        "matrix": {
            "horizons": list(HORIZONS),
            "replicates": [
                {"replicate": row[0], "legacy_burn": row[1], "extension_seed": row[2]}
                for row in REPLICATES
            ],
            "candidates": [
                {"candidate_id": row[0], "station_model": row[1], "generation_profile": row[2]}
                for row in CANDIDATES
            ],
            "expected_runs": EXPECTED_RUNS,
        },
        "fit": fit_section,
        "build": build_section,
        "shared_bases": shared_bases,
        "archives": archives,
        "runs": runs,
        "execution": {
            "workers": workers,
            "started_utc": iso_utc(started_utc),
            "completed_utc": iso_utc(completed_utc),
            "wall_time_seconds": wall_time_seconds,
            "failures": [],
            "candidate_cli_bytes_removed_after_wepp": False,
        },
    }


def assert_static_identities(
    expected_contracts: dict[str, dict[str, str]],
    stations: Sequence[StationInput],
    cligen: Path,
    cligen_sha256: str,
    overlay: Path,
    overlay_sha256: str,
    phase: str,
) -> None:
    if contract_identities() != expected_contracts:
        raise MatrixError(f"{phase}: frozen contract identity changed during execution")
    for station in stations:
        if (
            sha256_path(station.par) != station.par_sha256
            or sha256_path(station.bundle) != station.bundle_sha256
            or sha256_path(station.bundle_snapshot) != station.bundle_sha256
        ):
            raise MatrixError(f"{phase}: station snapshot changed: {station.station_id}")
    if expected_contracts["fitter"]["sha256"] != sha256_path(FITTER):
        raise MatrixError(f"{phase}: fitter changed during execution")
    for path, expected_sha256 in (
        (cligen, cligen_sha256),
        (overlay, overlay_sha256),
    ):
        if not path.is_file() or sha256_path(path) != expected_sha256:
            raise MatrixError(f"{phase}: binary snapshot identity changed: {path}")


def preflight_production(target: Path) -> None:
    if target.resolve(strict=False) != EXPECTED_TARGET.resolve(strict=False):
        raise MatrixError(f"target directory must be {EXPECTED_TARGET}")
    temporary_manifest = MANIFEST_PATH.with_name(f".{MANIFEST_PATH.name}.unverified")
    forbidden = [
        target,
        MANIFEST_PATH,
        temporary_manifest,
        shared_base_archive_path(),
        *(archive_path(row[0]) for row in CANDIDATES),
    ]
    existing = [path for path in forbidden if path.exists()]
    if existing:
        raise MatrixError(f"candidate output already exists; refusing stale/overwrite state: {existing}")


def _execute_matrix(
    args: argparse.Namespace, ownership: ExecutionOwnership
) -> None:
    target = Path(args.target_directory).resolve()
    preflight_production(target)
    cache = Path(args.cache).resolve(strict=True)
    if not cache.is_dir():
        raise MatrixError("US-2015 cache argument is not a directory")
    cligen_requested = Path(args.cligen).resolve()
    overlay_requested = Path(args.overlay).resolve()
    fit_directory = Path(args.fit_directory).resolve()
    contracts = contract_identities()
    validate_pre_candidate_freeze(contracts)
    implementation_commit = current_commit()
    build_details = build_binaries(cligen_requested, overlay_requested)
    plan_preflight = preflight_real_plans(fit_directory)

    started_utc = datetime.now(timezone.utc)
    started_monotonic = time.monotonic()
    target.mkdir(parents=True, exist_ok=False)
    rollback_marker = target / ROLLBACK_MARKER_NAME
    write_new(rollback_marker, ownership.token)
    ownership.target_created = True
    snapshot = target / SNAPSHOT_NAME
    staging = target / STAGING_NAME
    work_root = target / WORK_NAME
    publication_staging = staging / PUBLICATION_STAGING_NAME
    shared_root = staging / "shared-bases"
    snapshot.mkdir()
    staging.mkdir()
    work_root.mkdir()
    cligen = snapshot / "binaries/cligen"
    overlay = snapshot / "binaries/cligen-a5b-overlay"
    copy_file_exact(cligen_requested, cligen)
    copy_file_exact(overlay_requested, overlay)
    cligen_sha = sha256_path(cligen)
    overlay_sha = sha256_path(overlay)
    stations, fit_section = load_fit_inputs(
        cache,
        fit_directory,
        snapshot,
        cligen_sha,
        implementation_commit,
    )
    jobs = build_jobs(stations)
    base_jobs = build_base_jobs(stations)
    station_by_id = {station.station_id: station for station in stations}
    plans = generate_plans(stations, staging)
    assert_static_identities(
        contracts,
        stations,
        cligen,
        cligen_sha,
        overlay,
        overlay_sha,
        "before faithful bases",
    )

    bases: dict[tuple[str, int, int], BaseInput] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        base_futures = {
            executor.submit(
                execute_base,
                job,
                station_by_id[job.station_id],
                cligen,
                work_root,
                shared_root,
            ): job
            for job in base_jobs
        }
        try:
            for completed, future in enumerate(
                concurrent.futures.as_completed(base_futures), 1
            ):
                key, value = future.result()
                if key in bases:
                    raise MatrixError(f"duplicate faithful base result: {key}")
                bases[key] = value
                if completed % 32 == 0 or completed == len(base_futures):
                    print(
                        f"completed faithful bases {completed}/{len(base_futures)}",
                        flush=True,
                    )
        except BaseException:
            for future in base_futures:
                future.cancel()
            raise
    assert_base_identities(bases, "after faithful bases")
    assert_static_identities(
        contracts,
        stations,
        cligen,
        cligen_sha,
        overlay,
        overlay_sha,
        "after faithful bases",
    )
    cligen_member = external_member_with_sha256(cligen, cligen_sha)
    overlay_member = external_member_with_sha256(overlay, overlay_sha)

    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                execute_one,
                job,
                station_by_id[job.station_id],
                plans[(job.candidate_id, job.station_id, job.replicate)],
                bases[base_key(job)],
                cligen,
                cligen_member,
                overlay,
                overlay_member,
                target,
                staging,
                contracts,
                implementation_commit,
                sha256_path(OBSERVED_CORPUS),
            ): job
            for job in jobs
        }
        try:
            for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
                records.append(future.result())
                if completed % 32 == 0 or completed == len(futures):
                    print(f"completed {completed}/{len(futures)}", flush=True)
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    assert_base_identities(bases, "after matrix")
    assert_static_identities(
        contracts,
        stations,
        cligen,
        cligen_sha,
        overlay,
        overlay_sha,
        "after matrix",
    )
    records.sort(
        key=lambda row: (
            CANDIDATE_ORDER[row["candidate_id"]],
            [station.station_id for station in stations].index(row["station_id"]),
            row["horizon_years"],
            row["replicate"],
        )
    )

    archive_rows = []
    for candidate_id, _, _ in CANDIDATES:
        sources = archive_sources(staging, candidate_id)
        final_path = archive_path(candidate_id)
        artifact = write_canonical_archive(
            publication_staging / final_path.name,
            sources,
            identity_path=final_path,
        )
        archive_rows.append(
            {
                "candidate_id": candidate_id,
                "format": "tar+gzip-canonical-v1",
                "artifact": artifact,
                "member_count": len(sources),
            }
        )
    shared_sources = shared_base_sources(staging)
    shared_final_path = shared_base_archive_path()
    shared_artifact = write_canonical_archive(
        publication_staging / shared_final_path.name,
        shared_sources,
        identity_path=shared_final_path,
    )
    shared_section = {
        "format": "tar+gzip-canonical-v1",
        "artifact": shared_artifact,
        "base_count": SHARED_BASE_COUNT,
        "member_count": len(shared_sources),
        "records": shared_base_records(
            bases, [station.station_id for station in stations]
        ),
    }
    assert_base_identities(bases, "after archives")
    assert_static_identities(
        contracts,
        stations,
        cligen,
        cligen_sha,
        overlay,
        overlay_sha,
        "after archives",
    )
    completed_utc = datetime.now(timezone.utc)
    build_section = {
        "implementation_commit": implementation_commit,
        "cligen_binary": artifact_for_path(cligen),
        "overlay_binary": artifact_for_path(overlay),
        "cargo_lock_sha256": sha256_path(ROOT / "Cargo.lock"),
        "rustc_version": build_details["rustc_version"],
        "plan_preflight": plan_preflight,
    }
    manifest = build_manifest(
        contracts,
        stations,
        fit_section,
        build_section,
        shared_section,
        archive_rows,
        records,
        args.workers,
        started_utc,
        completed_utc,
        time.monotonic() - started_monotonic,
    )
    validate_schema(manifest, EVIDENCE_SCHEMA, "A5b candidate evidence manifest")
    validate_manifest_semantics(
        manifest,
        {station.station_id: station.regime for station in stations},
        target / CLI_DIRECTORY_NAME,
    )
    manifest_raw = canonical_json_bytes(manifest)
    CLIMATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary_manifest = MANIFEST_PATH.with_name(f".{MANIFEST_PATH.name}.unverified")
    write_new(temporary_manifest, manifest_raw)
    ownership.temporary_manifest_created = True
    try:
        subprocess_bytes(
            [
                sys.executable,
                str(EVIDENCE_VERIFIER),
                str(temporary_manifest),
                "--candidate-cli-dir",
                str(target / CLI_DIRECTORY_NAME),
                "--archive-dir",
                str(publication_staging),
            ],
            "independent A5b evidence verification",
        )
        for final_path in (
            shared_base_archive_path(),
            *(archive_path(row[0]) for row in CANDIDATES),
        ):
            publish_new_file(publication_staging / final_path.name, final_path)
            ownership.public_paths.append(final_path)
        publish_new_file(temporary_manifest, MANIFEST_PATH)
        ownership.temporary_manifest_created = False
        ownership.manifest_published = True
    finally:
        if ownership.temporary_manifest_created:
            temporary_manifest.unlink(missing_ok=True)
            ownership.temporary_manifest_created = False
    shutil.rmtree(staging)
    shutil.rmtree(work_root)
    rollback_marker.unlink()
    print(f"manifest {sha256_path(MANIFEST_PATH)} {MANIFEST_PATH}")
    print(
        f"shared-bases {shared_artifact['sha256']} {shared_artifact['path']}"
    )
    for row in archive_rows:
        print(f"archive {row['candidate_id']} {row['artifact']['sha256']} {row['artifact']['path']}")


def execute_matrix(args: argparse.Namespace) -> None:
    """Execute the campaign with rollback while the seal is unpublished."""

    target = Path(args.target_directory).resolve()
    temporary_manifest = MANIFEST_PATH.with_name(f".{MANIFEST_PATH.name}.unverified")
    ownership = ExecutionOwnership(os.urandom(32).hex().encode("ascii"))
    target_preexisted = target.exists()
    manifest_preexisted = MANIFEST_PATH.exists()
    temporary_manifest_preexisted = temporary_manifest.exists()
    public_preexisted = {
        path: path.exists()
        for path in (
            shared_base_archive_path(),
            *(archive_path(row[0]) for row in CANDIDATES),
        )
    }
    try:
        _execute_matrix(args, ownership)
    except BaseException as error:
        clean_start = (
            not target_preexisted
            and not manifest_preexisted
            and not temporary_manifest_preexisted
            and not any(public_preexisted.values())
        )
        if clean_start and not ownership.manifest_published:
            cleanup_errors: list[str] = []
            for path in reversed(ownership.public_paths):
                try:
                    path.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    cleanup_errors.append(f"{path}: {cleanup_error}")
            if ownership.temporary_manifest_created:
                try:
                    temporary_manifest.unlink(missing_ok=True)
                    ownership.temporary_manifest_created = False
                except OSError as cleanup_error:
                    cleanup_errors.append(f"{temporary_manifest}: {cleanup_error}")
            rollback_marker = target / ROLLBACK_MARKER_NAME
            if ownership.target_created:
                try:
                    marker_matches = (
                        rollback_marker.is_file()
                        and rollback_marker.read_bytes() == ownership.token
                    )
                    if marker_matches:
                        shutil.rmtree(target)
                except OSError as cleanup_error:
                    cleanup_errors.append(f"{target}: {cleanup_error}")
            if cleanup_errors:
                raise MatrixError(
                    "candidate campaign failed and rollback was incomplete: "
                    + "; ".join(cleanup_errors)
                ) from error
        raise


def synthetic_contracts() -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": repo_relative(path),
            "sha256": hashlib.sha256(name.encode()).hexdigest(),
        }
        for name, path in CONTRACT_PATHS.items()
    }


def synthetic_station_rows() -> list[dict[str, str]]:
    regimes = ("arid", "monsoonal", "humid", "cold")
    result = [
        {"station_id": f"zz{index:06d}", "regime": regimes[index % len(regimes)]}
        for index in range(16)
    ]
    result.append({"station_id": "zz999999", "regime": "fixture"})
    return result


def synthetic_member(member: str, marker: str = "member") -> dict[str, Any]:
    raw = marker.encode("ascii")
    return {"member": member, "sha256": sha256_bytes(raw), "bytes": len(raw)}


def synthetic_artifact(path: str, marker: str = "artifact") -> dict[str, Any]:
    raw = marker.encode("ascii")
    return {"path": path, "sha256": sha256_bytes(raw), "bytes": len(raw)}


def synthetic_run_record(contracts: dict[str, dict[str, str]]) -> dict[str, Any]:
    job = Job(
        "zz999999",
        "fixture",
        CANDIDATES[0][0],
        CANDIDATES[0][1],
        CANDIDATES[0][2],
        30,
        REPLICATES[0][0],
        REPLICATES[0][1],
        REPLICATES[0][2],
    )
    artifact = synthetic_member("synthetic/input.dat")
    return {
        "run_record_schema_version": 1,
        "matrix": {
            "station_id": job.station_id,
            "regime": job.regime,
            "candidate_id": job.candidate_id,
            "station_model": job.station_model,
            "generation_profile": job.generation_profile,
            "horizon_years": job.horizon_years,
            "replicate": job.replicate,
            "legacy_burn": job.legacy_burn,
            "extension_seed": job.extension_seed,
        },
        "contracts": run_record_contracts(contracts),
        "inputs": {
            "corpus_schema_version": 1,
            "corpus_content_sha256": "1" * 64,
            "legacy_par": artifact,
            "augmented_station": artifact,
            "coefficient_payload_sha256": "2" * 64,
            "fit_identity_sha256": "3" * 64,
            "plan": synthetic_member(plan_member_name(job)),
            "base_runspec_sha256": "4" * 64,
            "base_provenance_sha256": "d" * 64,
            "base_cli_sha256": "5" * 64,
            "base_run_id": "6" * 64,
        },
        "runtime": {
            "base_generation_profile": "faithful_5_32_3",
            "base_qc_filter": "off",
            "extension_prng": "splitmix64_box_muller_v1",
            "extension_domain_sha256": extension_domain_sha256(job),
            "cligen_binary": artifact,
            "overlay_binary": artifact,
            "implementation_commit": "7" * 40,
        },
        "outputs": {
            "candidate_cli": artifact,
            "quality_report": synthetic_member(quality_member_name(job)),
            "overlay_diagnostics": synthetic_member(diagnostics_member_name(job)),
        },
        "execution": {
            "host_os": "synthetic",
            "host_arch": "synthetic",
            "wall_time_ms": 1,
            "precipitation_clip_count": 0,
            "precipitation_render_limit_adjustment_count": 0,
            "temperature_order_repair_count": 0,
            "dewpoint_cap_count": 0,
            "counterfactual_month_count": 0,
            "sealed": True,
        },
    }


def synthetic_manifest() -> tuple[dict[str, Any], dict[str, str]]:
    stations = synthetic_station_rows()
    station_regimes = {row["station_id"]: row["regime"] for row in stations}
    jobs = build_jobs(stations)
    runs = []
    for job in jobs:
        runs.append(
            {
                "station_id": job.station_id,
                "regime": job.regime,
                "candidate_id": job.candidate_id,
                "horizon_years": job.horizon_years,
                "replicate": job.replicate,
                "legacy_burn": job.legacy_burn,
                "extension_seed": job.extension_seed,
                "archive_candidate_id": job.candidate_id,
                "run_record": synthetic_member(run_record_member_name(job), "run"),
                "quality_report": synthetic_member(quality_member_name(job), "quality"),
                "overlay_diagnostics": synthetic_member(diagnostics_member_name(job), "diagnostics"),
                "plan": synthetic_member(plan_member_name(job), "plan"),
                "candidate_cli_sha256": "8" * 64,
                "candidate_cli_bytes": 1,
            }
        )
    contracts = synthetic_contracts()
    manifest = {
        "candidate_evidence_manifest_version": 1,
        "status": "sealed",
        "contracts": contracts,
        "corpus": {
            "schema_version": 1,
            "content_sha256": "9" * 64,
            "station_ids": list(station_regimes),
        },
        "matrix": {
            "horizons": [30, 100],
            "replicates": [
                {"replicate": row[0], "legacy_burn": row[1], "extension_seed": row[2]}
                for row in REPLICATES
            ],
            "candidates": [
                {"candidate_id": row[0], "station_model": row[1], "generation_profile": row[2]}
                for row in CANDIDATES
            ],
            "expected_runs": EXPECTED_RUNS,
        },
        "fit": {
            "source_manifest": synthetic_artifact(
                repo_relative(EXPECTED_FIT_DIRECTORY / FIT_SOURCE_NAME)
            ),
            "fit_manifest": synthetic_artifact(
                repo_relative(EXPECTED_FIT_DIRECTORY / FIT_MANIFEST_NAME)
            ),
            "bundles": [
                synthetic_artifact(
                    repo_relative(
                        EXPECTED_FIT_DIRECTORY
                        / FIT_BUNDLE_DIRECTORY
                        / f"{station_id}.a5b.station.json"
                    )
                )
                for station_id in station_regimes
            ],
        },
        "build": {
            "implementation_commit": "a" * 40,
            "cligen_binary": synthetic_artifact(
                repo_relative(EXPECTED_TARGET / SNAPSHOT_NAME / "binaries/cligen")
            ),
            "overlay_binary": synthetic_artifact(
                repo_relative(
                    EXPECTED_TARGET
                    / SNAPSHOT_NAME
                    / "binaries/cligen-a5b-overlay"
                )
            ),
            "cargo_lock_sha256": "b" * 64,
            "rustc_version": "synthetic rustc",
            "plan_preflight": {
                "plans": 952,
                "aggregate_sha256": "c" * 64,
            },
        },
        "shared_bases": {
            "format": "tar+gzip-canonical-v1",
            "artifact": synthetic_artifact(repo_relative(shared_base_archive_path())),
            "base_count": SHARED_BASE_COUNT,
            "member_count": SHARED_BASE_MEMBER_COUNT,
            "records": [
                {
                    "station_id": station_id,
                    "horizon_years": horizon,
                    "replicate": replicate,
                    "legacy_burn": burn,
                    "runspec": synthetic_member(
                        base_runspec_member_name(
                            BaseJob(station_id, station_regimes[station_id], horizon, replicate, burn)
                        ),
                        "runspec",
                    ),
                    "provenance": synthetic_member(
                        base_provenance_member_name(
                            BaseJob(station_id, station_regimes[station_id], horizon, replicate, burn)
                        ),
                        "provenance",
                    ),
                    "base_cli_sha256": "d" * 64,
                    "base_run_id": "e" * 64,
                    "parameter_set_sha256": "f" * 64,
                }
                for station_id in station_regimes
                for horizon in HORIZONS
                for replicate, burn, _ in REPLICATES
            ],
        },
        "archives": [
            {
                "candidate_id": row[0],
                "format": "tar+gzip-canonical-v1",
                "artifact": synthetic_artifact(repo_relative(archive_path(row[0]))),
                "member_count": MEMBERS_PER_CANDIDATE,
            }
            for row in CANDIDATES
        ],
        "runs": runs,
        "execution": {
            "workers": 4,
            "started_utc": "2026-07-13T00:00:00.000000Z",
            "completed_utc": "2026-07-13T00:01:00.000000Z",
            "wall_time_seconds": 60.0,
            "failures": [],
            "candidate_cli_bytes_removed_after_wepp": True,
        },
    }
    return manifest, station_regimes


def expect_matrix_error(action: Callable[[], Any], label: str) -> None:
    try:
        action()
    except MatrixError:
        return
    raise MatrixError(f"self-test mutation was accepted: {label}")


def run_self_test() -> None:
    expect_matrix_error(lambda: strict_json_bytes(b'{"x":1,"x":2}', "duplicate"), "duplicate JSON key")
    expect_matrix_error(lambda: strict_json_bytes(b'{"x":NaN}', "NaN"), "NaN token")
    expect_matrix_error(lambda: strict_json_bytes(b'{"x":1e999}', "overflow"), "overflowing JSON number")

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        station_errors = list(
            schema_validator(str(STATION_SCHEMA.resolve(strict=True))).iter_errors(
                {"base_station": {}}
            )
        )
    if not station_errors:
        raise MatrixError("self-test local station-schema registry did not validate")
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        quality_errors = list(
            schema_validator(str(QUALITY_SCHEMA.resolve(strict=True))).iter_errors(
                {"identity": {"provenance": None}}
            )
        )
    if not quality_errors:
        raise MatrixError("self-test local quality-schema registry did not validate")

    contracts = synthetic_contracts()
    run_record = synthetic_run_record(contracts)
    validate_schema(run_record, RUN_RECORD_SCHEMA, "synthetic run record")
    manifest, station_regimes = synthetic_manifest()
    if len(build_base_jobs(synthetic_station_rows())) != 272:
        raise MatrixError("self-test faithful base matrix count differs")
    validate_schema(manifest, EVIDENCE_SCHEMA, "synthetic candidate manifest")
    validate_manifest_semantics(manifest, station_regimes, None)
    manifest_sha = sha256_bytes(canonical_json_bytes(manifest))
    if manifest_sha != SELF_TEST_MANIFEST_SHA256:
        raise MatrixError(f"self-test manifest golden differs: {manifest_sha}")

    mutation = json.loads(json.dumps(manifest))
    mutation["runs"][1] = dict(mutation["runs"][0])
    expect_matrix_error(lambda: validate_manifest_semantics(mutation, station_regimes, None), "duplicate matrix key")
    mutation = json.loads(json.dumps(manifest))
    mutation["runs"][0]["legacy_burn"] = 17
    expect_matrix_error(lambda: validate_manifest_semantics(mutation, station_regimes, None), "replicate/burn mismatch")
    mutation = json.loads(json.dumps(manifest))
    mutation["contracts"].pop("fitter")
    expect_matrix_error(lambda: validate_manifest_semantics(mutation, station_regimes, None), "missing contract")
    mutation = json.loads(json.dumps(manifest))
    mutation["archives"][0]["member_count"] = MEMBERS_PER_CANDIDATE - 1
    expect_matrix_error(lambda: validate_manifest_semantics(mutation, station_regimes, None), "archive member count")

    mutation = json.loads(json.dumps(manifest))
    mutation["runs"][0], mutation["runs"][1] = mutation["runs"][1], mutation["runs"][0]
    expect_matrix_error(
        lambda: validate_manifest_semantics(mutation, station_regimes, None),
        "noncanonical run order",
    )
    mutation = json.loads(json.dumps(manifest))
    mutation["runs"][8]["plan"]["sha256"] = "f" * 64
    expect_matrix_error(
        lambda: validate_manifest_semantics(mutation, station_regimes, None),
        "horizon plan identity mismatch",
    )

    job = build_jobs(synthetic_station_rows())[0]
    base_job = BaseJob(
        job.station_id,
        job.regime,
        job.horizon_years,
        job.replicate,
        job.legacy_burn,
    )
    text = runspec_bytes(
        base_job, Path("/synthetic/station.par"), Path("/synthetic/base.cli")
    )
    if (
        b"generation_profile: faithful_5_32_3" not in text
        or b"qc_filter: off" not in text
        or b"quality: false" not in text
        or f"command_echo: {json.dumps(NEUTRAL_BASE_COMMAND_ECHO)}".encode()
        not in text
        or b"--a5b-profile" in text
    ):
        raise MatrixError("self-test runspec does not bind the neutral faithful base")

    diagnostic = {
        "diagnostics_schema_version": 1,
        "station_id": job.station_id,
        "station_model": job.station_model,
        "candidate_profile": job.generation_profile,
        "extension_seed": job.extension_seed,
        "coefficient_payload_sha256": "1" * 64,
        "state_table_sha256": "2" * 64,
        "input_runspec_sha256": "3" * 64,
        "plan_sha256": "4" * 64,
        "faithful_cli_sha256": "5" * 64,
        "output_cli_sha256": "6" * 64,
        "row_count": days_in_horizon(job.horizon_years),
        "plan_state_years": 128,
        "consumed_prefix_years": job.horizon_years,
        "wet_days_before": 10,
        "wet_days_after": 10,
        "temperature_order_repairs": 0,
        "dewpoint_caps": 0,
        "counterfactual_applied": False,
        "counterfactual_months": 0,
        "relocated_wet_days": 0,
        "reassigned_storm_tuples": 0,
        "counterfactual_rng_final_state": None,
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
            for year in range(1, job.horizon_years + 1)
            for month in range(1, 13)
        ],
    }
    plan = PlanInput(
        Path("synthetic-plan"),
        {"member": plan_member_name(job), "sha256": "4" * 64, "bytes": 1},
        {
            "coefficient_payload_sha256": "1" * 64,
            "state_table_sha256": "2" * 64,
            "normalization": {"precipitation_clip_count": 0},
            "annual_states": [
                {"precip_factor": [1.0] * 12} for _ in range(128)
            ],
        },
    )
    validate_overlay_diagnostics(diagnostic, job, plan, "3" * 64, "5" * 64, "6" * 64)
    mutation = dict(diagnostic)
    mutation["wet_days_after"] = 9
    expect_matrix_error(
        lambda: validate_overlay_diagnostics(mutation, job, plan, "3" * 64, "5" * 64, "6" * 64),
        "wet-day preservation",
    )

    quality = {
        "quality_report_schema_version": 2,
        "metrics_version": 3,
        "identity": {
            "content": {
                "station_model": "fixed_monthly_5_32_3",
                "station_source_sha256": "7" * 64,
                "station_parameter_set_sha256": "8" * 64,
                "cli_sha256": "9" * 64,
                "days": days_in_horizon(job.horizon_years),
                "years": job.horizon_years,
                "span": [1, job.horizon_years],
            },
            "provenance": None,
        },
        "process": None,
    }
    station = StationInput(
        job.station_id,
        job.regime,
        Path("par"),
        "7" * 64,
        Path("bundle"),
        Path("bundle-snapshot"),
        "a" * 64,
        {},
        {},
    )
    validate_quality_report(quality, job, station, "9" * 64, "8" * 64, schema_validation=False)
    quality_mutation = json.loads(json.dumps(quality))
    quality_mutation["identity"]["provenance"] = {}
    expect_matrix_error(
        lambda: validate_quality_report(quality_mutation, job, station, "9" * 64, "8" * 64, schema_validation=False),
        "trusted post-hoc provenance",
    )

    with tempfile.TemporaryDirectory(prefix="a5b-matrix-self-test-") as temporary_name:
        temporary = Path(temporary_name)
        sources = []
        for name, raw in (("b/report.json", b"second\n"), ("a/plan.json", b"first\n"), ("c/run.json", b"third\n")):
            source = temporary / "sources" / Path(*PurePosixPath(name).parts)
            write_new(source, raw)
            sources.append((name, source))
        first_archive = temporary / "first.tar.gz"
        second_archive = temporary / "second.tar.gz"
        write_canonical_archive(
            first_archive, list(reversed(sources)), require_repo_relative=False
        )
        write_canonical_archive(
            second_archive, sources, require_repo_relative=False
        )
        if first_archive.read_bytes() != second_archive.read_bytes():
            raise MatrixError("self-test canonical archive is not byte-repeatable")
        archive_sha = sha256_path(first_archive)
        if archive_sha != SELF_TEST_ARCHIVE_SHA256:
            raise MatrixError(f"self-test archive golden differs: {archive_sha}")
        expect_matrix_error(
            lambda: write_canonical_archive(
                first_archive, sources, require_repo_relative=False
            ),
            "archive overwrite",
        )
        expect_matrix_error(
            lambda: write_canonical_archive(
                temporary / "duplicate.tar.gz",
                [sources[0], sources[0]],
                require_repo_relative=False,
            ),
            "duplicate archive member",
        )
        publication_source = temporary / "publication/source.bin"
        publication_destination = temporary / "publication/destination.bin"
        write_new(publication_source, b"atomic-publication\n")
        publish_new_file(publication_source, publication_destination)
        if publication_source.exists() or publication_destination.read_bytes() != b"atomic-publication\n":
            raise MatrixError("self-test atomic publication identity differs")
        second_source = temporary / "publication/second.bin"
        write_new(second_source, b"must-not-overwrite\n")
        expect_matrix_error(
            lambda: publish_new_file(second_source, publication_destination),
            "atomic publication overwrite",
        )
    print(
        json.dumps(
            {
                "self_test": "ok",
                "archive_sha256": SELF_TEST_ARCHIVE_SHA256,
                "manifest_sha256": SELF_TEST_MANIFEST_SHA256,
                "matrix_runs": EXPECTED_RUNS,
                "plans": 7 * PLANS_PER_CANDIDATE,
                "mutations_rejected": 14,
            },
            sort_keys=True,
        )
    )


def workers_type(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("workers must be an integer") from error
    if not 1 <= parsed <= MAX_WORKERS:
        raise argparse.ArgumentTypeError(f"workers must be in [1, {MAX_WORKERS}]")
    return parsed


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cligen", nargs="?")
    parser.add_argument("overlay", nargs="?")
    parser.add_argument("cache", nargs="?")
    parser.add_argument("fit_directory", nargs="?")
    parser.add_argument("target_directory", nargs="?")
    parser.add_argument("--workers", type=workers_type, default=min(MAX_WORKERS, max(1, os.cpu_count() or 1)))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    positional = (args.cligen, args.overlay, args.cache, args.fit_directory, args.target_directory)
    if args.self_test:
        if any(value is not None for value in positional):
            parser.error("--self-test does not accept positional arguments")
    elif any(value is None for value in positional):
        parser.error("cligen, overlay, cache, fit_directory, and target_directory are required")
    return args


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    try:
        if args.self_test:
            run_self_test()
        else:
            execute_matrix(args)
        return 0
    except (MatrixError, OSError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f"run-a5b-matrix: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
