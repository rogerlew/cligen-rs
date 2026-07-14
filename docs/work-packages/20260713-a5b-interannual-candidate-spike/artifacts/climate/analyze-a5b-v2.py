#!/usr/bin/env python3
"""Analyze the frozen A5b climate matrix without changing its denominators.

Usage:
  analyze-a5b-v2.py CANDIDATE_MANIFEST CANDIDATE_ARCHIVE_DIR \
      BASELINE_MANIFEST BASELINE_ARCHIVE OBSERVED_TARGET OUTPUT
  analyze-a5b-v2.py --self-test

The candidate evidence verifier is the authority for archive/schema closure.
This program repeats the identities it consumes, compresses each quality
report to the prospectively registered scalar surface, fixes eligibility from
the accepted faithful-off baseline, and then evaluates the seven climate
gates.  Observed-target bootstrap intervals are report-only.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import hashlib
import importlib.util
import itertools
import json
import math
import multiprocessing
import os
from pathlib import Path
import re
import sys
import tarfile
from typing import Any, Iterable, Sequence

from jsonschema import Draft202012Validator
import numpy as np


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = ROOT / "docs/work-packages/20260713-a5b-interannual-candidate-spike"
A5A = ROOT / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"
METRIC_MANIFEST = ROOT / "docs/specifications/a5-climate-gate-metrics-v1.json"
METRIC_SCHEMA = ROOT / "docs/specifications/a5-climate-gate-metrics-v1.schema.json"
METRIC_VERIFIER = A5A / "artifacts/verify-a5-climate-gate-metrics-v1.py"
BOOTSTRAP_REFERENCE = A5A / "artifacts/observed-bootstrap-v1.py"
BOOTSTRAP_GOLDEN = A5A / "artifacts/observed-bootstrap-v1-golden.json"
BUILD_TARGETS = A5A / "artifacts/corpus/build_targets.py"
CORPUS_COMMON = A5A / "artifacts/corpus/corpus_common.py"
CORPUS_CONFIG = A5A / "artifacts/corpus/corpus-config-v1.json"
CANDIDATE_SCHEMA = ROOT / "docs/specifications/a5b-candidate-evidence-v1.schema.json"
BASELINE_SCHEMA = A5A / "artifacts/baseline-run-manifest-v1.schema.json"
PRE_CANDIDATE_FREEZE = PACKAGE / "artifacts/freeze/pre-candidate-freeze-v1.json"
ACCEPTED_BASELINE_MANIFEST = A5A / "artifacts/baseline-run-manifest-v1.json"
ACCEPTED_BASELINE_ARCHIVE = A5A / "artifacts/baseline-evidence-v1.tar.gz"
RELEASE_METRICS_HELPER = ROOT / "target/release/cligen-quality-estimator"
ANALYZER_SOURCE = Path(__file__).resolve()
ORIGINAL_ANALYZER = ANALYZER_SOURCE.with_name("analyze-a5b.py")
POST_CLIMATE_WEPP_FREEZE = (
    PACKAGE / "artifacts/freeze/post-climate-wepp-freeze-v3.json"
)
V7_WEPP_ANALYZER = PACKAGE / "artifacts/wepp/analyze-wepp-v7.py"
V8_WEPP_ANALYZER = PACKAGE / "artifacts/wepp/analyze-wepp-v8.py"
POST_OUTPUT_ANALYSIS_AMENDMENT = (
    PACKAGE / "artifacts/freeze/post-output-analysis-amendment-v1.md"
)
POST_OUTPUT_ANALYSIS_FREEZE = (
    PACKAGE / "artifacts/freeze/post-output-analysis-freeze-v1.json"
)
ANALYSIS_HELPER_SOURCE_PATHS = (
    "Cargo.lock",
    "Cargo.toml",
    "rust-toolchain.toml",
    "crates/cligen/Cargo.toml",
    "crates/cligen/src/lib.rs",
    "crates/cligen/src/bin/cligen-quality-estimator.rs",
    "crates/cligen/src/quality/estimators.rs",
    "crates/cligen/src/quality/mod.rs",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/build_targets.py",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/corpus_common.py",
    "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/corpus-config-v1.json",
)
RELEASE_METRICS_HELPER_COMMAND = (
    "cargo",
    "build",
    "--locked",
    "--offline",
    "--release",
    "--bin",
    "cligen-quality-estimator",
)
FORBIDDEN_METRICS_HELPER_BUILD_ENV = (
    "RUSTFLAGS",
    "CARGO_ENCODED_RUSTFLAGS",
    "RUSTC_WRAPPER",
    "RUSTC_WORKSPACE_WRAPPER",
    "CARGO_TARGET_DIR",
    "CARGO_BUILD_TARGET",
)

CANDIDATES = (
    "rank_one_monthly_sd",
    "full_monthly_covariance",
    "fourier_eof",
    "vector_ar",
    "gaussian_hmm",
    "spectral_random_phase",
    "precip_counterfactual",
)
BASELINE_ID = "faithful_off_baseline"
HORIZONS = (30, 100)
REPLICATES = tuple(range(8))
REGIMES = ("arid", "monsoonal", "humid", "cold", "fixture")
COLD_STATIONS = ("co051660", "wy485345", "mn214026", "ak505769", "id106388")
BOOTSTRAP_GATES = (1, 4, 6)
BOOTSTRAP_REPLICATES = 2000
RUN_RECORD_CONTRACT_KEYS = frozenset(
    {
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
    }
)
EVIDENCE_ONLY_CONTRACT_KEYS = frozenset(
    {
        "evidence_schema",
        "evidence_verifier",
        "matrix_runner",
        "plan_generator",
        "overlay_source",
        "fitter",
        "pre_candidate_freeze",
        "pre_output_amendments",
    }
)
EVIDENCE_CONTRACT_KEYS = RUN_RECORD_CONTRACT_KEYS | EVIDENCE_ONLY_CONTRACT_KEYS


class AnalysisError(RuntimeError):
    """A frozen input, evidence, or analysis-contract violation."""


MISSING = object()


def reject_constant(token: str) -> None:
    raise AnalysisError(f"nonfinite JSON token is forbidden: {token}")


def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AnalysisError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise AnalysisError(f"JSON float overflows finite range: {token}")
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
        raise AnalysisError(f"cannot parse {label}: {error}") from error


def strict_json(path: Path) -> Any:
    return strict_json_bytes(path.read_bytes(), str(path))


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AnalysisError(f"cannot import frozen helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_helpers() -> tuple[Any, Any, Any, Any]:
    metric = load_module("a5_metric_manifest_v1", METRIC_VERIFIER)
    bootstrap = load_module("a5_observed_bootstrap_v1", BOOTSTRAP_REFERENCE)
    corpus = load_module("corpus_common", CORPUS_COMMON)
    corpus_dir = str(CORPUS_COMMON.parent)
    if corpus_dir not in sys.path:
        sys.path.insert(0, corpus_dir)
    targets = load_module("a5_build_targets_v1", BUILD_TARGETS)
    return metric, bootstrap, corpus, targets


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    schema = strict_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(value) for value in first.absolute_path)
        raise AnalysisError(f"{label} schema failure at /{location}: {first.message}")


def finite_number(value: Any) -> float | object:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return MISSING
    result = float(value)
    return result if math.isfinite(result) else MISSING


def conventional_median(values: Sequence[float]) -> float:
    if len(values) == 0:
        raise AnalysisError("median input is empty")
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def nearest_rank(values: Sequence[float], numerator: int, denominator: int) -> float:
    if len(values) == 0 or not 0 < numerator <= denominator:
        raise AnalysisError("invalid nearest-rank request")
    ordered = sorted(float(value) for value in values)
    rank = (numerator * len(ordered) + denominator - 1) // denominator
    return ordered[rank - 1]


def summary(values: Sequence[float]) -> dict[str, Any]:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return {
            "n_available": 0,
            "n_expected": len(values),
            "median": None,
            "p05": None,
            "p95": None,
            "minimum": None,
            "maximum": None,
        }
    return {
        "n_available": len(finite),
        "n_expected": len(values),
        "median": conventional_median(finite),
        "p05": nearest_rank(finite, 1, 20),
        "p95": nearest_rank(finite, 19, 20),
        "minimum": min(finite),
        "maximum": max(finite),
    }


def bootstrap_interval(values: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {"n_available": 0, "p2_5": None, "p97_5": None}
    ordered = np.sort(finite)
    low = (1 * ordered.size + 40 - 1) // 40 - 1
    high = (39 * ordered.size + 40 - 1) // 40 - 1
    return {
        "n_available": int(ordered.size),
        "p2_5": float(ordered[low]),
        "p97_5": float(ordered[high]),
    }


_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_INDEX = re.compile(r"0|[1-9][0-9]*")
_SELECTOR = re.compile(r"@station_id=([a-z]{2}[0-9]{6})")


def compile_json_path(path: str) -> tuple[tuple[str, Any], ...]:
    if not path.startswith("$"):
        raise AnalysisError(f"JSON path does not start with $: {path}")
    tokens: list[tuple[str, Any]] = []
    offset = 1
    while offset < len(path):
        if path[offset] == ".":
            match = _NAME.match(path, offset + 1)
            if match is None:
                raise AnalysisError(f"invalid JSON path member at {path[offset:]}")
            tokens.append(("member", match.group(0)))
            offset = match.end()
            continue
        if path[offset] == "[":
            end = path.find("]", offset)
            if end < 0:
                raise AnalysisError(f"unterminated JSON path index: {path}")
            body = path[offset + 1 : end]
            if _INDEX.fullmatch(body):
                tokens.append(("index", int(body)))
            else:
                match = _SELECTOR.fullmatch(body)
                if match is None:
                    raise AnalysisError(f"unsupported JSON path selector: [{body}]")
                tokens.append(("station", match.group(1)))
            offset = end + 1
            continue
        raise AnalysisError(f"unexpected JSON path character at {path[offset:]}")
    return tuple(tokens)


def resolve_tokens(
    root: Any, tokens: Sequence[tuple[str, Any]], missing_ok: bool
) -> Any:
    value = root
    for kind, token in tokens:
        if kind == "member":
            if not isinstance(value, dict) or token not in value:
                if missing_ok:
                    return MISSING
                raise AnalysisError(f"JSON path member is missing: {token}")
            value = value[token]
        elif kind == "index":
            if not isinstance(value, list) or token >= len(value):
                if missing_ok:
                    return MISSING
                raise AnalysisError(f"JSON path array index is missing: {token}")
            value = value[token]
        else:
            if not isinstance(value, list):
                if missing_ok:
                    return MISSING
                raise AnalysisError("station selector did not address an array")
            matches = [
                item
                for item in value
                if isinstance(item, dict) and item.get("station_id") == token
            ]
            if len(matches) != 1:
                if missing_ok and not matches:
                    return MISSING
                raise AnalysisError(
                    f"station selector requires exactly one match: {token}/{len(matches)}"
                )
            value = matches[0]
    return value


def resolve_path(root: Any, path: str, missing_ok: bool = False) -> Any:
    return resolve_tokens(root, compile_json_path(path), missing_ok)


@dataclass(frozen=True)
class Binding:
    index: int
    report_index: int
    gate_id: int
    template_id: str
    dimensions: tuple[tuple[str, Any], ...]
    family: str
    variable: str
    statistic: str
    distance: str
    surface_id: str
    generated_path: str
    generated_count_path: str
    target_path: str
    target_count_path: str
    target_scale_path: str | None
    cell_key: str


def binding_key(
    gate_id: int,
    template_id: str,
    dimensions: dict[str, Any],
    surface_id: str,
) -> str:
    encoded = json.dumps(
        dimensions, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    return f"gate={gate_id}|template={template_id}|dimensions={encoded}|surface={surface_id}"


def expand_bindings(metric_helper: Any) -> tuple[dict[str, Any], list[Binding]]:
    manifest = strict_json(METRIC_MANIFEST)
    schema = strict_json(METRIC_SCHEMA)
    result = metric_helper.validate_manifest(manifest, schema)
    if result["expanded_cell_bindings"] != 1211:
        raise AnalysisError("frozen metric manifest did not expand to 1,211 bindings")
    surfaces = {row["surface_id"]: row for row in manifest["target_surfaces"]}
    bindings: list[Binding] = []
    for template in manifest["metric_templates"]:
        rows = metric_helper.substitutions(template["dimensions"])
        for gate in template["gate_bindings"]:
            surface_id = gate["target_surface"]
            prefix = surfaces[surface_id]["path_prefix"]
            for dimensions in rows:
                target_values = {"target_prefix": prefix} | dimensions
                generated = metric_helper.substitute(
                    template["generated_path_template"], dimensions
                )
                generated_count = metric_helper.substitute(
                    template["completeness"]["generated_count_path_template"],
                    dimensions,
                )
                target = metric_helper.substitute(
                    template["target_path_template"], target_values
                )
                target_count = metric_helper.substitute(
                    template["completeness"]["target_count_path_template"],
                    target_values,
                )
                normalization = template.get("normalization")
                target_scale = (
                    metric_helper.substitute(
                        normalization["target_scale_path_template"], dimensions
                    )
                    if normalization is not None
                    else None
                )
                index = len(bindings)
                bindings.append(
                    Binding(
                        index=index,
                        report_index=index,
                        gate_id=int(gate["gate_id"]),
                        template_id=template["template_id"],
                        dimensions=tuple(dimensions.items()),
                        family=template["family"],
                        variable=metric_helper.variable_for(template, dimensions),
                        statistic=metric_helper.statistic_for(template, dimensions),
                        distance=template["distance"],
                        surface_id=surface_id,
                        generated_path=generated,
                        generated_count_path=generated_count,
                        target_path=target,
                        target_count_path=target_count,
                        target_scale_path=target_scale,
                        cell_key=binding_key(
                            int(gate["gate_id"]),
                            template["template_id"],
                            dimensions,
                            surface_id,
                        ),
                    )
                )
    if len(bindings) != 1211 or len({row.cell_key for row in bindings}) != 1211:
        raise AnalysisError(
            "expanded metric binding identity is not exactly 1,211 unique rows"
        )
    return manifest, bindings


def projected_bindings(
    manifest: dict[str, Any], bindings: list[Binding]
) -> dict[str, list[Binding]]:
    surfaces = {row["surface_id"]: row for row in manifest["target_surfaces"]}
    primary = [row for row in bindings if row.gate_id == 1]
    result: dict[str, list[Binding]] = {}
    dispersion = {
        "b_annual_nonnegative_dispersion",
        "b_annual_temperature_dispersion",
        "b_monthly_nonnegative_dispersion",
        "b_monthly_temperature_dispersion",
    }
    dependence = {
        "b_cross_month_dependence",
        "b_cross_variable_dependence",
        "b_annual_lag_one_dependence",
        "b_annual_low_frequency_fraction",
    }
    old_prefix = surfaces["daymet_evaluation_raw"]["path_prefix"]
    for projection in manifest["sensitivity_projections"]:
        projection_id = projection["projection_id"]
        surface_id = projection["target_surface"]
        new_prefix = surfaces[surface_id]["path_prefix"]
        rows: list[Binding] = []
        detrended = projection_id.endswith("detrended")
        for source in primary:
            if detrended and not (
                (source.template_id in dispersion and source.statistic == "sd")
                or source.template_id in dependence
            ):
                continue
            target = source.target_path.replace(old_prefix, new_prefix, 1)
            target_count = source.target_count_path.replace(old_prefix, new_prefix, 1)
            if detrended:
                if source.template_id in dispersion:
                    if not target.endswith(".sd"):
                        raise AnalysisError("detrended dispersion target is not an SD")
                    target = target[:-3] + ".detrended_sd"
                else:
                    target = target.replace(
                        ".dependence.raw.", ".dependence.detrended."
                    )
            dimensions = dict(source.dimensions)
            rows.append(
                Binding(
                    index=-1,
                    report_index=source.report_index,
                    gate_id=1,
                    template_id=source.template_id,
                    dimensions=source.dimensions,
                    family=source.family,
                    variable=source.variable,
                    statistic=source.statistic,
                    distance=source.distance,
                    surface_id=surface_id,
                    generated_path=source.generated_path,
                    generated_count_path=source.generated_count_path,
                    target_path=target,
                    target_count_path=target_count,
                    target_scale_path=None,
                    cell_key=binding_key(1, source.template_id, dimensions, surface_id),
                )
            )
        expected = 344 if detrended else 422
        if len(rows) != expected:
            raise AnalysisError(
                f"sensitivity {projection_id} expanded to {len(rows)}, expected {expected}"
            )
        result[projection_id] = rows
    return result


def sufficient_count(binding: Binding, value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    if binding.statistic in ("pearson", "spearman", "pearson_correlation"):
        return value >= 2
    if binding.statistic in ("sd", "cv"):
        return value >= 2
    return value >= 1


@dataclass
class ReportVector:
    values: np.ndarray
    counts: list[Any]
    targets: np.ndarray
    target_counts: list[Any]
    scales: np.ndarray
    parameter_sha256: str


def compress_report(report: dict[str, Any], bindings: list[Binding]) -> ReportVector:
    if (
        report.get("quality_report_schema_version") != 2
        or report.get("metrics_version") != 3
    ):
        raise AnalysisError("quality report is not envelope 2 / metrics 3")
    identity = report.get("identity")
    if not isinstance(identity, dict) or not isinstance(identity.get("content"), dict):
        raise AnalysisError("quality report content identity is missing")
    parameter_sha = identity["content"].get("station_parameter_set_sha256")
    if not isinstance(parameter_sha, str) or not re.fullmatch(
        r"[0-9a-f]{64}", parameter_sha
    ):
        raise AnalysisError("quality report station-parameter identity is invalid")
    values = np.full(len(bindings), np.nan, dtype=np.float64)
    targets = np.full(len(bindings), np.nan, dtype=np.float64)
    scales = np.full(len(bindings), np.nan, dtype=np.float64)
    counts: list[Any] = [MISSING] * len(bindings)
    target_counts: list[Any] = [MISSING] * len(bindings)
    for binding in bindings:
        generated = finite_number(resolve_path(report, binding.generated_path))
        if generated is not MISSING:
            values[binding.index] = generated
        counts[binding.index] = resolve_path(report, binding.generated_count_path)
        if binding.surface_id == "report_embedded_station_parameter":
            target = finite_number(resolve_path(report, binding.target_path))
            if target is not MISSING:
                targets[binding.index] = target
            target_counts[binding.index] = resolve_path(
                report, binding.target_count_path
            )
            if binding.target_scale_path is not None:
                scale = finite_number(resolve_path(report, binding.target_scale_path))
                if scale is not MISSING:
                    scales[binding.index] = scale
    return ReportVector(values, counts, targets, target_counts, scales, parameter_sha)


def safe_tar_name(name: str) -> None:
    pure = Path(name)
    if not name or name.startswith("/") or "\\" in name or ".." in pure.parts:
        raise AnalysisError(f"unsafe evidence member name: {name!r}")


def read_wanted_members(
    archive: Path,
    wanted: dict[str, tuple[str, int]],
    expected_member_count: int | None = None,
) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    seen: set[str] = set()
    try:
        with tarfile.open(archive, "r:gz") as stream:
            for member in stream:
                safe_tar_name(member.name)
                if member.name in seen:
                    raise AnalysisError(f"duplicate tar member: {member.name}")
                seen.add(member.name)
                if not member.isfile():
                    raise AnalysisError(
                        f"non-regular tar member is forbidden: {member.name}"
                    )
                if member.name not in wanted:
                    continue
                handle = stream.extractfile(member)
                if handle is None:
                    raise AnalysisError(
                        f"cannot extract evidence member: {member.name}"
                    )
                raw = handle.read()
                expected_sha, expected_bytes = wanted[member.name]
                if len(raw) != expected_bytes or sha256_bytes(raw) != expected_sha:
                    raise AnalysisError(
                        f"evidence member identity mismatch: {member.name}"
                    )
                result[member.name] = raw
    except (tarfile.TarError, OSError) as error:
        raise AnalysisError(
            f"cannot read evidence archive {archive}: {error}"
        ) from error
    missing = set(wanted) - set(result)
    if missing:
        raise AnalysisError(f"evidence archive omits {len(missing)} referenced members")
    if expected_member_count is not None and len(seen) != expected_member_count:
        raise AnalysisError(
            f"evidence archive has {len(seen)} members, expected {expected_member_count}"
        )
    return result


def verify_artifact(path: Path, artifact: dict[str, Any], label: str) -> Path:
    if not path.is_file():
        raise AnalysisError(f"{label} is missing: {path}")
    if (
        path.stat().st_size != artifact["bytes"]
        or sha256_path(path) != artifact["sha256"]
    ):
        raise AnalysisError(f"{label} identity differs: {path}")
    return path


def resolve_archive_artifact(base: Path, artifact: dict[str, Any]) -> Path:
    lexical = Path(artifact["path"])
    if lexical.is_absolute():
        raise AnalysisError("candidate archive paths must be repository-root-relative")
    repository = ROOT.resolve(strict=True)
    archive_root = base.resolve(strict=True)
    if not archive_root.is_relative_to(repository):
        raise AnalysisError("candidate archive directory is outside the repository")
    path = (repository / lexical).resolve(strict=False)
    if not path.is_relative_to(repository):
        raise AnalysisError(f"candidate archive path escapes the repository: {lexical}")
    if not path.is_relative_to(archive_root):
        raise AnalysisError(
            f"candidate archive is outside the supplied archive directory: {lexical}"
        )
    return verify_artifact(path, artifact, "candidate archive")


def resolve_repo_artifact(artifact: dict[str, Any]) -> Path:
    lexical = Path(artifact["path"])
    if lexical.is_absolute():
        raise AnalysisError(
            "repository artifact paths must be repository-root-relative"
        )
    root = ROOT.resolve(strict=True)
    path = (root / lexical).resolve(strict=False)
    if not path.is_relative_to(root):
        raise AnalysisError(f"artifact path escapes the repository: {lexical}")
    return verify_artifact(path, artifact, "repository artifact")


def resolve_repo_identity(identity: dict[str, Any]) -> Path:
    lexical = Path(identity["path"])
    if lexical.is_absolute():
        raise AnalysisError("contract paths must be repository-root-relative")
    root = ROOT.resolve(strict=True)
    path = (root / lexical).resolve(strict=False)
    if not path.is_relative_to(root) or not path.is_file():
        raise AnalysisError(
            f"contract path is missing or escapes the repository: {lexical}"
        )
    if sha256_path(path) != identity["sha256"]:
        raise AnalysisError(f"contract identity differs: {lexical}")
    return path


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AnalysisError(f"{label} must be an object")
    return value


def require_exact_keys(
    value: dict[str, Any], expected: set[str], label: str
) -> None:
    actual = set(value)
    if actual != expected:
        raise AnalysisError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def canonical_repository_path(relative: str, label: str) -> Path:
    lexical = Path(relative)
    if lexical.is_absolute() or ".." in lexical.parts:
        raise AnalysisError(f"{label} path is not safe repository-relative: {relative}")
    root = ROOT.resolve(strict=True)
    candidate = root / lexical
    if candidate.is_symlink():
        raise AnalysisError(f"{label} may not be a symlink")
    path = candidate.resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise AnalysisError(f"{label} is missing, a symlink, or outside the repository")
    return path


def locate_metrics_helper(identity: dict[str, Any]) -> Path:
    require_exact_keys(identity, {"path", "sha256", "bytes"}, "metrics helper")
    if identity["path"] != RELEASE_METRICS_HELPER.relative_to(ROOT).as_posix():
        raise AnalysisError("frozen metrics helper is not the release binary")
    if not RELEASE_METRICS_HELPER.is_file() or RELEASE_METRICS_HELPER.is_symlink():
        raise AnalysisError(
            "observed bootstrap requires the frozen release "
            "target/release/cligen-quality-estimator"
        )
    expected_path = RELEASE_METRICS_HELPER.resolve(strict=True)
    if not os.access(expected_path, os.X_OK):
        raise AnalysisError("frozen release metrics helper is not executable")
    return verify_artifact(expected_path, identity, "frozen release metrics helper")


def validate_analysis_helper_sources(
    sources: dict[str, Any], frozen: dict[str, Any] | None = None
) -> None:
    if set(sources) != set(ANALYSIS_HELPER_SOURCE_PATHS):
        raise AnalysisError("release analysis-helper source inventory differs")
    for relative in ANALYSIS_HELPER_SOURCE_PATHS:
        identity = require_dict(sources[relative], f"analysis helper source {relative}")
        require_exact_keys(identity, {"sha256", "bytes"}, f"analysis helper source {relative}")
        path = canonical_repository_path(relative, "analysis helper source")
        if (
            (frozen is not None and identity["sha256"] != frozen.get(relative))
            or identity["sha256"] != sha256_path(path)
            or identity["bytes"] != path.stat().st_size
        ):
            raise AnalysisError(f"release analysis-helper source differs: {relative}")


def validate_analysis_freeze_value(
    freeze: dict[str, Any],
    baseline_manifest_path: Path,
    baseline_archive_path: Path,
    freeze_sha256: str,
) -> dict[str, Any]:
    if (
        freeze.get("pre_candidate_freeze_version") != 1
        or freeze.get("status") != "passed"
        or freeze.get("candidate_output_absent") is not True
    ):
        raise AnalysisError("pre-candidate freeze is not a passing revision-1 freeze")

    a5a = require_dict(freeze.get("a5a_pinned_artifacts"), "freeze A5a inventory")
    baseline_bindings = (
        (baseline_manifest_path, ACCEPTED_BASELINE_MANIFEST, "accepted baseline manifest"),
        (baseline_archive_path, ACCEPTED_BASELINE_ARCHIVE, "accepted baseline archive"),
    )
    for supplied, canonical, label in baseline_bindings:
        canonical_resolved = canonical.resolve(strict=True)
        if supplied.resolve(strict=True) != canonical_resolved:
            raise AnalysisError(f"{label} path differs from the accepted A5a artifact")
        relative = canonical.relative_to(ROOT).as_posix()
        expected_sha256 = a5a.get(relative)
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
            raise AnalysisError(f"pre-candidate freeze omits {label}")
        if sha256_path(canonical_resolved) != expected_sha256:
            raise AnalysisError(f"{label} differs from the pre-candidate freeze")

    frozen = require_dict(
        freeze.get("a5b_frozen_artifacts"), "freeze A5b artifact inventory"
    )
    analyzer_relative = ORIGINAL_ANALYZER.relative_to(ROOT).as_posix()
    required_frozen = (analyzer_relative, *ANALYSIS_HELPER_SOURCE_PATHS)
    for relative in required_frozen:
        expected_sha256 = frozen.get(relative)
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
            raise AnalysisError(f"pre-candidate freeze omits analysis input: {relative}")
        path = canonical_repository_path(relative, "frozen analysis input")
        if sha256_path(path) != expected_sha256:
            raise AnalysisError(f"frozen analysis input differs: {relative}")

    helper = require_dict(
        freeze.get("analysis_helper_release"), "release analysis-helper evidence"
    )
    require_exact_keys(
        helper,
        {"contract_id", "built_before_candidate_output", "build", "sources", "binary"},
        "release analysis-helper evidence",
    )
    if (
        helper["contract_id"] != "a5b-analysis-helper-release-v1"
        or helper["built_before_candidate_output"] is not True
    ):
        raise AnalysisError("release analysis-helper contract identity differs")
    build = require_dict(helper["build"], "release analysis-helper build")
    require_exact_keys(
        build,
        {
            "command",
            "cwd",
            "profile",
            "locked",
            "offline",
            "forbidden_environment_absent",
            "cargo_version_verbose",
            "rustc_version_verbose",
        },
        "release analysis-helper build",
    )
    if (
        build["command"] != list(RELEASE_METRICS_HELPER_COMMAND)
        or build["cwd"] != "."
        or build["profile"] != "release"
        or build["locked"] is not True
        or build["offline"] is not True
        or build["forbidden_environment_absent"]
        != list(FORBIDDEN_METRICS_HELPER_BUILD_ENV)
        or not isinstance(build["cargo_version_verbose"], str)
        or not build["cargo_version_verbose"]
        or not isinstance(build["rustc_version_verbose"], str)
        or not build["rustc_version_verbose"]
    ):
        raise AnalysisError("release analysis-helper build metadata differs")

    sources = require_dict(helper["sources"], "release analysis-helper sources")
    validate_analysis_helper_sources(sources, frozen)

    binary = require_dict(helper["binary"], "release analysis-helper binary")
    locate_metrics_helper(binary)
    return {
        "pre_candidate_freeze_sha256": freeze_sha256,
        "analyzer_sha256": frozen[analyzer_relative],
        "analysis_helper_release": helper,
    }


def validate_post_output_analysis_freeze() -> str:
    freeze = require_dict(
        strict_json(POST_OUTPUT_ANALYSIS_FREEZE), "post-output analysis freeze"
    )
    require_exact_keys(
        freeze,
        {
            "post_output_analysis_freeze_version",
            "status",
            "created_utc",
            "boundary",
            "immutable_anchors",
            "corrected_artifacts",
            "failed_analysis",
        },
        "post-output analysis freeze",
    )
    if (
        freeze["post_output_analysis_freeze_version"] != 1
        or freeze["status"] != "passed"
        or freeze["boundary"]
        != {
            "candidate_climate_output_present": True,
            "candidate_metric_values_inspected": False,
            "wepp_response_output_present": True,
            "analysis_output_absent": True,
        }
    ):
        raise AnalysisError("post-output analysis freeze status/boundary differs")
    inventories = {
        "immutable_anchors": (
            PRE_CANDIDATE_FREEZE,
            ORIGINAL_ANALYZER,
            POST_CLIMATE_WEPP_FREEZE,
            V7_WEPP_ANALYZER,
        ),
        "corrected_artifacts": (
            ANALYZER_SOURCE,
            V8_WEPP_ANALYZER,
            POST_OUTPUT_ANALYSIS_AMENDMENT,
        ),
    }
    for name, paths in inventories.items():
        inventory = require_dict(freeze[name], f"post-output {name}")
        expected = {path.relative_to(ROOT).as_posix() for path in paths}
        if set(inventory) != expected:
            raise AnalysisError(f"post-output {name} paths differ")
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            identity = require_dict(
                inventory[relative], f"post-output artifact {relative}"
            )
            require_exact_keys(
                identity, {"sha256", "bytes"}, f"post-output artifact {relative}"
            )
            if (
                not path.is_file()
                or path.is_symlink()
                or identity["sha256"] != sha256_path(path)
                or identity["bytes"] != path.stat().st_size
            ):
                raise AnalysisError(f"post-output frozen artifact differs: {relative}")
    if freeze["failed_analysis"] != {
        "analyzer_version": 1,
        "status": "failed_closed_before_analysis_output",
        "candidate_metric_values_inspected": False,
        "failure": (
            "The truth value of an array with more than one element is ambiguous. "
            "Use a.any() or a.all()"
        ),
        "cause": "sequence_emptiness_predicate_applied_to_numpy_array",
        "corrected_functions": ["conventional_median", "nearest_rank"],
    }:
        raise AnalysisError("post-output failed-analysis disposition differs")
    return sha256_path(POST_OUTPUT_ANALYSIS_FREEZE)


def validate_analysis_freeze(
    candidate_manifest: dict[str, Any],
    baseline_manifest_path: Path,
    baseline_archive_path: Path,
) -> dict[str, Any]:
    freeze_path = resolve_repo_identity(
        require_dict(
            candidate_manifest["contracts"]["pre_candidate_freeze"],
            "candidate pre-candidate-freeze binding",
        )
    )
    if freeze_path != PRE_CANDIDATE_FREEZE.resolve(strict=True):
        raise AnalysisError("candidate evidence binds an unexpected pre-candidate freeze")
    freeze = require_dict(strict_json(freeze_path), "pre-candidate freeze")
    result = validate_analysis_freeze_value(
        freeze,
        baseline_manifest_path,
        baseline_archive_path,
        sha256_path(freeze_path),
    )
    amendment_sha256 = validate_post_output_analysis_freeze()
    result["pre_candidate_analyzer_sha256"] = result["analyzer_sha256"]
    result["analyzer_sha256"] = sha256_path(ANALYZER_SOURCE)
    result["post_output_analysis_freeze_sha256"] = amendment_sha256
    return result


def assert_exact_matrix(
    keys: Iterable[tuple[Any, ...]], expected: set[tuple[Any, ...]], label: str
) -> None:
    actual_list = list(keys)
    actual = set(actual_list)
    if len(actual) != len(actual_list):
        raise AnalysisError(f"{label} contains duplicate matrix keys")
    if actual != expected:
        raise AnalysisError(
            f"{label} matrix differs: missing={len(expected - actual)}, extra={len(actual - expected)}"
        )


def load_baseline_reports(
    manifest_path: Path,
    archive_path: Path,
    bindings: list[Binding],
    station_ids: Sequence[str],
    burn_by_replicate: dict[int, int],
) -> tuple[dict[tuple[str, int, int], ReportVector], dict[str, Any]]:
    manifest = strict_json(manifest_path)
    validate_schema(manifest, BASELINE_SCHEMA, "accepted A5a baseline manifest")
    if manifest["matrix"]["actual_runs"] != 544:
        raise AnalysisError("accepted baseline matrix is not complete")
    archive_identity = manifest["archive"]
    if (
        archive_path.stat().st_size != archive_identity["bytes"]
        or sha256_path(archive_path) != archive_identity["sha256"]
    ):
        raise AnalysisError("accepted baseline archive identity differs")
    burn_to_replicate = {
        burn: replicate for replicate, burn in burn_by_replicate.items()
    }
    if len(burn_to_replicate) != 8:
        raise AnalysisError("replicate burn offsets are not unique")
    selected = [row for row in manifest["runs"] if row["qc_filter"] == "off"]
    wanted = {
        row["quality_report"]: (
            row["quality_report_sha256"],
            row["quality_report_bytes"],
        )
        for row in selected
    }
    if len(wanted) != 272:
        raise AnalysisError(
            "accepted baseline does not contain 272 distinct off reports"
        )
    members = read_wanted_members(archive_path, wanted)
    reports: dict[tuple[str, int, int], ReportVector] = {}
    for row in selected:
        replicate = burn_to_replicate.get(row["burn"])
        if replicate is None:
            raise AnalysisError("baseline burn is outside the fixed replicate records")
        key = (row["station"], row["years"], replicate)
        report = strict_json_bytes(
            members[row["quality_report"]], row["quality_report"]
        )
        if report["identity"]["content"]["years"] != row["years"]:
            raise AnalysisError("baseline report horizon differs from manifest")
        reports[key] = compress_report(report, bindings)
    expected = set(itertools.product(station_ids, HORIZONS, REPLICATES))
    assert_exact_matrix(reports, expected, "faithful-off baseline")
    return reports, manifest


def load_candidate_reports(
    manifest: dict[str, Any],
    archive_dir: Path,
    bindings: list[Binding],
    station_ids: Sequence[str],
) -> tuple[
    dict[tuple[str, str, int, int], ReportVector],
    dict[str, list[dict[str, int]]],
]:
    runs_by_candidate = {candidate: [] for candidate in CANDIDATES}
    for row in manifest["runs"]:
        runs_by_candidate[row["candidate_id"]].append(row)
    reports: dict[tuple[str, str, int, int], ReportVector] = {}
    runtime: dict[str, list[dict[str, int]]] = {
        candidate: [] for candidate in CANDIDATES
    }
    archive_by_candidate = {row["candidate_id"]: row for row in manifest["archives"]}
    if tuple(archive_by_candidate) != CANDIDATES:
        raise AnalysisError("candidate archive order differs from the frozen order")
    for candidate in CANDIDATES:
        archive_row = archive_by_candidate[candidate]
        archive = resolve_archive_artifact(archive_dir, archive_row["artifact"])
        rows = runs_by_candidate[candidate]
        wanted: dict[str, tuple[str, int]] = {}
        for row in rows:
            if row["archive_candidate_id"] != candidate:
                raise AnalysisError("run index points at the wrong candidate archive")
            for field in (
                "quality_report",
                "run_record",
                "overlay_diagnostics",
                "plan",
            ):
                item = row[field]
                identity = (item["sha256"], item["bytes"])
                prior = wanted.get(item["member"])
                if prior is not None and prior != identity:
                    raise AnalysisError(
                        "one tar member has conflicting declared identities"
                    )
                wanted[item["member"]] = identity
        members = read_wanted_members(
            archive, wanted, expected_member_count=archive_row["member_count"]
        )
        for row in rows:
            quality = strict_json_bytes(
                members[row["quality_report"]["member"]],
                row["quality_report"]["member"],
            )
            if (
                quality.get("process") is not None
                or quality.get("identity", {}).get("provenance") is not None
            ):
                raise AnalysisError(
                    "candidate post-hoc report claims trusted process/provenance"
                )
            if quality["identity"]["content"]["years"] != row["horizon_years"]:
                raise AnalysisError("candidate report horizon differs from run index")
            key = (
                candidate,
                row["station_id"],
                row["horizon_years"],
                row["replicate"],
            )
            reports[key] = compress_report(quality, bindings)
            record = strict_json_bytes(
                members[row["run_record"]["member"]], row["run_record"]["member"]
            )
            if set(record.get("contracts", {})) != RUN_RECORD_CONTRACT_KEYS:
                raise AnalysisError(
                    "run record contract key set differs from the frozen 15"
                )
            expected_contracts = {
                key: manifest["contracts"][key] for key in RUN_RECORD_CONTRACT_KEYS
            }
            if record["contracts"] != expected_contracts:
                raise AnalysisError(
                    "run record contracts differ from the evidence manifest"
                )
            strict_json_bytes(
                members[row["overlay_diagnostics"]["member"]],
                row["overlay_diagnostics"]["member"],
            )
            strict_json_bytes(members[row["plan"]["member"]], row["plan"]["member"])
            matrix = record.get("matrix", {})
            comparisons = {
                "station_id": row["station_id"],
                "candidate_id": candidate,
                "horizon_years": row["horizon_years"],
                "replicate": row["replicate"],
                "legacy_burn": row["legacy_burn"],
                "extension_seed": row["extension_seed"],
            }
            if any(matrix.get(name) != value for name, value in comparisons.items()):
                raise AnalysisError(
                    "candidate run record matrix key differs from index"
                )
            execution = record.get("execution", {})
            if execution.get("sealed") is not True:
                raise AnalysisError("candidate run record is not sealed")
            runtime[candidate].append(
                {
                    name: int(execution[name])
                    for name in (
                        "wall_time_ms",
                        "precipitation_clip_count",
                        "temperature_order_repair_count",
                        "dewpoint_cap_count",
                        "counterfactual_month_count",
                    )
                }
            )
    expected = set(itertools.product(CANDIDATES, station_ids, HORIZONS, REPLICATES))
    assert_exact_matrix(reports, expected, "A5b candidate")
    return reports, runtime


def observed_cell(
    corpus: dict[str, Any], binding: Binding, station_id: str
) -> tuple[Any, Any]:
    target_path = binding.target_path.replace("{station_id}", station_id)
    count_path = binding.target_count_path.replace("{station_id}", station_id)
    return (
        resolve_path(corpus, target_path, missing_ok=True),
        resolve_path(corpus, count_path, missing_ok=True),
    )


def baseline_eligible(
    corpus: dict[str, Any],
    binding: Binding,
    station_id: str,
    baseline_rows: Sequence[ReportVector],
) -> bool:
    if binding.gate_id == 6 and station_id not in COLD_STATIONS:
        return False
    for row in baseline_rows:
        value = row.values[binding.report_index]
        if not math.isfinite(float(value)) or not sufficient_count(
            binding, row.counts[binding.report_index]
        ):
            return False
    if binding.gate_id == 5:
        return True
    if binding.surface_id == "report_embedded_station_parameter":
        for row in baseline_rows:
            target = row.targets[binding.report_index]
            if not math.isfinite(float(target)) or not sufficient_count(
                binding, row.target_counts[binding.report_index]
            ):
                return False
            if binding.distance == "absolute_relative" and target <= 0.0:
                return False
            if binding.target_scale_path is not None:
                scale = row.scales[binding.report_index]
                if not math.isfinite(float(scale)) or scale <= 0.0:
                    return False
        return True
    target, count = observed_cell(corpus, binding, station_id)
    numeric = finite_number(target)
    return (
        numeric is not MISSING
        and sufficient_count(binding, count)
        and (binding.distance != "absolute_relative" or numeric > 0.0)
    )


def candidate_defines(rows: Sequence[ReportVector], binding: Binding) -> bool:
    return all(
        math.isfinite(float(row.values[binding.report_index]))
        and sufficient_count(binding, row.counts[binding.report_index])
        for row in rows
    )


def distance_value(
    generated: float, target: float, binding: Binding, scale: float | None
) -> float:
    if binding.target_scale_path is not None:
        if scale is None or not math.isfinite(scale) or scale <= 0.0:
            raise AnalysisError("temperature-location normalization is unavailable")
        return abs(generated - target) / scale
    if binding.distance == "absolute_relative":
        if not target > 0.0:
            raise AnalysisError("relative-distance target is not strictly positive")
        return abs(generated - target) / target
    if binding.distance == "absolute_difference":
        return abs(generated - target)
    raise AnalysisError(f"unknown distance definition: {binding.distance}")


def distance_rows(
    corpus: dict[str, Any],
    bindings: Sequence[Binding],
    station_id: str,
    generated: Sequence[ReportVector],
    frozen_baseline: Sequence[ReportVector],
) -> np.ndarray:
    result = np.empty((8, len(bindings)), dtype=np.float64)
    for column, binding in enumerate(bindings):
        if binding.surface_id == "report_embedded_station_parameter":
            for replicate, (row, baseline) in enumerate(
                zip(generated, frozen_baseline, strict=True)
            ):
                scale = (
                    float(baseline.scales[binding.report_index])
                    if binding.target_scale_path is not None
                    else None
                )
                result[replicate, column] = distance_value(
                    float(row.values[binding.report_index]),
                    float(baseline.targets[binding.report_index]),
                    binding,
                    scale,
                )
        else:
            target, _count = observed_cell(corpus, binding, station_id)
            numeric = finite_number(target)
            if numeric is MISSING:
                raise AnalysisError("eligible observed target became unavailable")
            for replicate, row in enumerate(generated):
                result[replicate, column] = distance_value(
                    float(row.values[binding.report_index]),
                    float(numeric),
                    binding,
                    None,
                )
    return result


@dataclass
class Aggregates:
    variables: dict[tuple[str, str], np.ndarray]
    families: dict[str, np.ndarray]
    gate: np.ndarray


def aggregate_rows(distances: np.ndarray, bindings: Sequence[Binding]) -> Aggregates:
    if distances.shape != (8, len(bindings)) or not bindings:
        raise AnalysisError("distance matrix has the wrong shape or empty membership")
    variable_indices: dict[tuple[str, str], list[int]] = {}
    for index, binding in enumerate(bindings):
        variable_indices.setdefault((binding.family, binding.variable), []).append(
            index
        )
    variables = {
        key: np.median(distances[:, indices], axis=1)
        for key, indices in variable_indices.items()
    }
    family_variables: dict[str, list[np.ndarray]] = {}
    for (family, _variable), values in variables.items():
        family_variables.setdefault(family, []).append(values)
    families = {
        family: np.median(np.stack(values, axis=1), axis=1)
        for family, values in family_variables.items()
    }
    gate = np.median(np.stack(list(families.values()), axis=1), axis=1)
    return Aggregates(variables, families, gate)


def ratio(candidate: float, baseline: float) -> float | None:
    if baseline == 0.0:
        return 0.0 if candidate == 0.0 else None
    return candidate / baseline


def passes_gate_1(
    candidate: float,
    baseline: float,
    candidate_low_frequency: float,
    baseline_low_frequency: float,
    improved_stations: int,
    regimes: Sequence[tuple[float, float]],
) -> bool:
    return (
        candidate <= 0.90 * baseline
        and candidate_low_frequency <= 0.90 * baseline_low_frequency
        and improved_stations >= 11
        and all(left <= 1.05 * right for left, right in regimes)
    )


def passes_gate_2(candidate: float, baseline: float) -> bool:
    return candidate <= 1.10 * baseline


def passes_gate_3_or_6(
    candidate: float,
    baseline: float,
    stations: Sequence[tuple[float, float]],
) -> bool:
    return candidate <= 1.10 * baseline and all(
        left <= 1.25 * right for left, right in stations
    )


def passes_gate_4(candidate: float, baseline: float) -> bool:
    return candidate <= 1.10 * baseline


def passes_gate_5(candidate: float, low: float, high: float) -> bool:
    return low <= candidate <= high


def passes_gate_7(
    climate_evidence_complete: bool, downstream_wepp_complete: bool
) -> bool:
    return climate_evidence_complete and downstream_wepp_complete


def pair_station_aggregate(
    station_id: str,
    regime: str,
    bindings: list[Binding],
    candidate: Aggregates,
    baseline: Aggregates,
) -> dict[str, Any]:
    return {
        "station_id": station_id,
        "regime": regime,
        "eligible_scalar_cells": len(bindings),
        "candidate_gate": summary(candidate.gate),
        "baseline_gate": summary(baseline.gate),
        "candidate_to_baseline_gate_median_ratio": ratio(
            conventional_median(candidate.gate.tolist()),
            conventional_median(baseline.gate.tolist()),
        ),
        "families": [
            {
                "family": family,
                "candidate": summary(candidate.families[family]),
                "baseline": summary(baseline.families[family]),
            }
            for family in sorted(candidate.families)
        ],
        "variables": [
            {
                "family": family,
                "variable": variable,
                "candidate": summary(candidate.variables[(family, variable)]),
                "baseline": summary(baseline.variables[(family, variable)]),
            }
            for family, variable in sorted(candidate.variables)
        ],
    }


def eligible_cell_inventory(
    corpus: dict[str, Any],
    bindings: Sequence[Binding],
    baseline_reports: dict[tuple[str, int, int], ReportVector],
    stations: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        for station in stations:
            station_id = station["station_id"]
            baseline = [
                baseline_reports[(station_id, horizon, replicate)]
                for replicate in REPLICATES
            ]
            for gate_id in range(1, 7):
                eligible = [
                    binding
                    for binding in bindings
                    if binding.gate_id == gate_id
                    and baseline_eligible(corpus, binding, station_id, baseline)
                ]
                inventory.append(
                    {
                        "station_id": station_id,
                        "regime": station["regime"],
                        "horizon_years": horizon,
                        "gate_id": gate_id,
                        "cell_count": len(eligible),
                        "cell_ids": [
                            f"{binding.cell_key}|station={station_id}|horizon={horizon}"
                            for binding in eligible
                        ],
                    }
                )
    return inventory


def analyze_distance_gate(
    corpus: dict[str, Any],
    all_bindings: Sequence[Binding],
    baseline_reports: dict[tuple[str, int, int], ReportVector],
    candidate_reports: dict[tuple[str, str, int, int], ReportVector],
    candidate_id: str,
    horizon: int,
    gate_id: int,
    stations: Sequence[dict[str, Any]],
    evidence_failures: list[str],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    candidate_by_station: dict[str, Aggregates] = {}
    baseline_by_station: dict[str, Aggregates] = {}
    membership = [row for row in all_bindings if row.gate_id == gate_id]
    for station in stations:
        station_id = station["station_id"]
        if gate_id == 6 and station_id not in COLD_STATIONS:
            continue
        baseline = [baseline_reports[(station_id, horizon, rep)] for rep in REPLICATES]
        candidate = [
            candidate_reports[(candidate_id, station_id, horizon, rep)]
            for rep in REPLICATES
        ]
        eligible = [
            binding
            for binding in membership
            if baseline_eligible(corpus, binding, station_id, baseline)
        ]
        if not eligible:
            continue
        missing = [
            binding.cell_key
            for binding in eligible
            if not candidate_defines(candidate, binding)
        ]
        if missing:
            evidence_failures.append(
                f"{candidate_id}/{station_id}/{horizon}/gate{gate_id}: "
                f"candidate omits {len(missing)} baseline-eligible cells"
            )
            continue
        if gate_id == 3:
            for rep, (candidate_row, baseline_row) in enumerate(
                zip(candidate, baseline, strict=True)
            ):
                if candidate_row.parameter_sha256 != baseline_row.parameter_sha256:
                    evidence_failures.append(
                        f"{candidate_id}/{station_id}/{horizon}/rep{rep}: "
                        "station parameter identity differs"
                    )
                for binding in eligible:
                    index = binding.report_index
                    if (
                        candidate_row.targets[index] != baseline_row.targets[index]
                        or candidate_row.target_counts[index]
                        != baseline_row.target_counts[index]
                        or (
                            binding.target_scale_path is not None
                            and candidate_row.scales[index]
                            != baseline_row.scales[index]
                        )
                    ):
                        evidence_failures.append(
                            f"{candidate_id}/{station_id}/{horizon}/rep{rep}: "
                            f"embedded target differs for {binding.cell_key}"
                        )
        baseline_aggregate = aggregate_rows(
            distance_rows(corpus, eligible, station_id, baseline, baseline), eligible
        )
        candidate_aggregate = aggregate_rows(
            distance_rows(corpus, eligible, station_id, candidate, baseline), eligible
        )
        baseline_by_station[station_id] = baseline_aggregate
        candidate_by_station[station_id] = candidate_aggregate
        rows.append(
            pair_station_aggregate(
                station_id,
                station["regime"],
                eligible,
                candidate_aggregate,
                baseline_aggregate,
            )
        )
    if not rows:
        return {
            "gate_id": gate_id,
            "status": "unavailable",
            "reason": "no baseline-eligible station composite",
            "passed": False,
            "stations": [],
        }
    candidate_station = {
        station_id: conventional_median(value.gate.tolist())
        for station_id, value in candidate_by_station.items()
    }
    baseline_station = {
        station_id: conventional_median(value.gate.tolist())
        for station_id, value in baseline_by_station.items()
    }
    candidate_corpus = conventional_median(list(candidate_station.values()))
    baseline_corpus = conventional_median(list(baseline_station.values()))
    regimes: list[dict[str, Any]] = []
    for regime in REGIMES:
        ids = [
            station["station_id"]
            for station in stations
            if station["regime"] == regime
            and station["station_id"] in candidate_station
        ]
        if ids:
            candidate_value = conventional_median(
                [candidate_station[item] for item in ids]
            )
            baseline_value = conventional_median(
                [baseline_station[item] for item in ids]
            )
            regimes.append(
                {
                    "regime": regime,
                    "station_count": len(ids),
                    "candidate": candidate_value,
                    "baseline": baseline_value,
                    "candidate_to_baseline_ratio": ratio(
                        candidate_value, baseline_value
                    ),
                }
            )
    family_corpus: dict[str, dict[str, Any]] = {}
    families = sorted(
        {
            family
            for aggregate in candidate_by_station.values()
            for family in aggregate.families
        }
    )
    for family in families:
        ids = [
            station_id
            for station_id, aggregate in candidate_by_station.items()
            if family in aggregate.families
        ]
        candidate_value = conventional_median(
            [
                conventional_median(candidate_by_station[item].families[family])
                for item in ids
            ]
        )
        baseline_value = conventional_median(
            [
                conventional_median(baseline_by_station[item].families[family])
                for item in ids
            ]
        )
        family_corpus[family] = {
            "candidate": candidate_value,
            "baseline": baseline_value,
            "candidate_to_baseline_ratio": ratio(candidate_value, baseline_value),
        }
    station_pairs = [
        (candidate_station[station_id], baseline_station[station_id])
        for station_id in candidate_station
    ]
    if gate_id == 1:
        low = family_corpus["interannual_low_frequency"]
        improved = sum(left < right for left, right in station_pairs)
        passed = passes_gate_1(
            candidate_corpus,
            baseline_corpus,
            low["candidate"],
            low["baseline"],
            improved,
            [(row["candidate"], row["baseline"]) for row in regimes],
        )
        decision = {
            "improved_station_count": improved,
            "required_improved_station_count": 11,
            "low_frequency_family": low,
        }
    elif gate_id == 2:
        passed = passes_gate_2(candidate_corpus, baseline_corpus)
        decision = {"available_station_count": len(station_pairs)}
    elif gate_id == 3:
        passed = passes_gate_3_or_6(candidate_corpus, baseline_corpus, station_pairs)
        decision = {}
    elif gate_id == 4:
        passed = passes_gate_4(candidate_corpus, baseline_corpus)
        decision = {}
    elif gate_id == 6:
        passed = passes_gate_3_or_6(candidate_corpus, baseline_corpus, station_pairs)
        decision = {"required_station_ids": list(COLD_STATIONS)}
    else:
        raise AnalysisError(f"distance aggregation requested for gate {gate_id}")
    return {
        "gate_id": gate_id,
        "status": "available",
        "passed": passed,
        "candidate_corpus_distance": candidate_corpus,
        "baseline_corpus_distance": baseline_corpus,
        "candidate_to_baseline_ratio": ratio(candidate_corpus, baseline_corpus),
        "family_corpus_distances": family_corpus,
        "regimes": regimes,
        "stations": rows,
        **decision,
    }


def analyze_descriptor_gate(
    bindings: Sequence[Binding],
    baseline_reports: dict[tuple[str, int, int], ReportVector],
    candidate_reports: dict[tuple[str, str, int, int], ReportVector],
    candidate_id: str,
    horizon: int,
    stations: Sequence[dict[str, Any]],
    evidence_failures: list[str],
) -> dict[str, Any]:
    membership = [row for row in bindings if row.gate_id == 5]
    cells: list[dict[str, Any]] = []
    failures = 0
    for station in stations:
        station_id = station["station_id"]
        baseline = [baseline_reports[(station_id, horizon, rep)] for rep in REPLICATES]
        candidate = [
            candidate_reports[(candidate_id, station_id, horizon, rep)]
            for rep in REPLICATES
        ]
        eligible = [
            binding
            for binding in membership
            if baseline_eligible({}, binding, station_id, baseline)
        ]
        for binding in eligible:
            if not candidate_defines(candidate, binding):
                evidence_failures.append(
                    f"{candidate_id}/{station_id}/{horizon}/gate5: "
                    f"candidate omits {binding.cell_key}"
                )
                failures += 1
                continue
            baseline_values = [
                float(row.values[binding.report_index]) for row in baseline
            ]
            candidate_values = [
                float(row.values[binding.report_index]) for row in candidate
            ]
            low = nearest_rank(baseline_values, 1, 20)
            high = nearest_rank(baseline_values, 19, 20)
            candidate_median = conventional_median(candidate_values)
            passed = passes_gate_5(candidate_median, low, high)
            failures += int(not passed)
            cells.append(
                {
                    "station_id": station_id,
                    "cell_id": binding.cell_key,
                    "candidate_median_raw": candidate_median,
                    "baseline_p05_raw": low,
                    "baseline_p95_raw": high,
                    "passed": passed,
                }
            )
    return {
        "gate_id": 5,
        "status": "available" if cells else "unavailable",
        "passed": bool(cells) and failures == 0,
        "failed_cell_count": failures,
        "evaluated_cell_count": len(cells),
        "cells": cells,
    }


def analyze_sensitivities(
    corpus: dict[str, Any],
    projections: dict[str, list[Binding]],
    baseline_reports: dict[tuple[str, int, int], ReportVector],
    candidate_reports: dict[tuple[str, str, int, int], ReportVector],
    stations: Sequence[dict[str, Any]],
    evidence_failures: list[str],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate_id in CANDIDATES:
        for horizon in HORIZONS:
            for projection_id, membership in projections.items():
                station_rows: list[dict[str, Any]] = []
                for station in stations:
                    station_id = station["station_id"]
                    baseline = [
                        baseline_reports[(station_id, horizon, rep)]
                        for rep in REPLICATES
                    ]
                    candidate = [
                        candidate_reports[(candidate_id, station_id, horizon, rep)]
                        for rep in REPLICATES
                    ]
                    eligible = [
                        binding
                        for binding in membership
                        if baseline_eligible(corpus, binding, station_id, baseline)
                    ]
                    if not eligible:
                        continue
                    missing = [
                        row.cell_key
                        for row in eligible
                        if not candidate_defines(candidate, row)
                    ]
                    if missing:
                        evidence_failures.append(
                            f"{candidate_id}/{station_id}/{horizon}/{projection_id}: "
                            f"candidate omits {len(missing)} cells"
                        )
                        continue
                    baseline_aggregate = aggregate_rows(
                        distance_rows(corpus, eligible, station_id, baseline, baseline),
                        eligible,
                    )
                    candidate_aggregate = aggregate_rows(
                        distance_rows(
                            corpus, eligible, station_id, candidate, baseline
                        ),
                        eligible,
                    )
                    station_rows.append(
                        {
                            "station_id": station_id,
                            "regime": station["regime"],
                            "eligible_scalar_cells": len(eligible),
                            "candidate": conventional_median(candidate_aggregate.gate),
                            "baseline": conventional_median(baseline_aggregate.gate),
                        }
                    )
                if station_rows:
                    candidate_value = conventional_median(
                        [row["candidate"] for row in station_rows]
                    )
                    baseline_value = conventional_median(
                        [row["baseline"] for row in station_rows]
                    )
                    status = "available"
                else:
                    candidate_value = baseline_value = None
                    status = "unavailable"
                output.append(
                    {
                        "candidate_id": candidate_id,
                        "horizon_years": horizon,
                        "projection_id": projection_id,
                        "status": status,
                        "candidate_corpus_distance": candidate_value,
                        "baseline_corpus_distance": baseline_value,
                        "candidate_to_baseline_ratio": (
                            ratio(candidate_value, baseline_value)
                            if candidate_value is not None
                            and baseline_value is not None
                            else None
                        ),
                        "stations": station_rows,
                    }
                )
    return output


def relative_bootstrap_path(
    binding: Binding, station_id: str
) -> tuple[tuple[str, Any], ...]:
    full = binding.target_path.replace("{station_id}", station_id)
    marker = "].sources.daymet.periods.evaluation"
    position = full.find(marker)
    if position < 0:
        raise AnalysisError(
            f"bootstrap binding is not a Daymet evaluation path: {full}"
        )
    return compile_json_path("$" + full[position + len(marker) :])


def relative_bootstrap_count_path(
    binding: Binding, station_id: str
) -> tuple[tuple[str, Any], ...]:
    full = binding.target_count_path.replace("{station_id}", station_id)
    marker = "].sources.daymet.periods.evaluation"
    position = full.find(marker)
    if position < 0:
        raise AnalysisError(f"bootstrap count is not a Daymet evaluation path: {full}")
    return compile_json_path("$" + full[position + len(marker) :])


def bootstrap_target_matrix(
    corpus_sha256: str,
    station: dict[str, Any],
    bindings: Sequence[Binding],
    needed: set[int],
    bootstrap_helper: Any,
    corpus_helper: Any,
    target_helper: Any,
) -> tuple[np.ndarray, dict[str, Any]]:
    station_id = station["station_id"]
    source = station["sources"]["daymet"]["source_identity"]
    archive = ROOT / f"references/observed/a5a-v1/daymet/{station_id}.csv.gz"
    if archive.stat().st_size <= 0 or sha256_path(archive) != source["archive_sha256"]:
        raise AnalysisError(f"{station_id}: raw Daymet archive identity differs")
    config = strict_json(CORPUS_CONFIG)
    config_station = next(
        row for row in config["stations"] if row["station_id"] == station_id
    )
    records, checked = corpus_helper.archive_records(archive, "daymet", config_station)
    if (
        checked["source_sha256"] != source["source_sha256"]
        or checked["calendar"] != "noleap_365"
    ):
        raise AnalysisError(f"{station_id}: raw Daymet source identity differs")
    source_years = list(range(2010, 2026))
    by_year = {
        year: [
            (date[1], date[2], records[date])
            for date in sorted(records)
            if date[0] == year
        ]
        for year in source_years
    }
    if any(len(rows) != 365 for rows in by_year.values()):
        raise AnalysisError(f"{station_id}: held-out Daymet years are not complete")
    digest = bootstrap_helper.seed_digest(
        corpus_sha256, source["source_id"], station_id, "evaluation"
    )
    seed = int.from_bytes(digest[:8], "big", signed=False)
    starts, indices = bootstrap_helper.bootstrap_indices(seed, 16, 5, 2000)
    matrix = np.full((BOOTSTRAP_REPLICATES, len(bindings)), np.nan, dtype=np.float64)
    target_paths = {
        index: relative_bootstrap_path(bindings[index], station_id) for index in needed
    }
    count_paths = {
        index: relative_bootstrap_count_path(bindings[index], station_id)
        for index in needed
    }
    for bootstrap_index, sample in enumerate(indices):
        relabelled: dict[tuple[int, int, int], dict[str, float]] = {}
        for position, source_index in enumerate(sample):
            for month, day, values in by_year[source_years[source_index]]:
                relabelled[(position, month, day)] = values
        target = target_helper.period_targets(relabelled, "noleap_365", (0, 15))
        for index in needed:
            binding = bindings[index]
            value = finite_number(resolve_tokens(target, target_paths[index], True))
            count = resolve_tokens(target, count_paths[index], True)
            if (
                value is not MISSING
                and sufficient_count(binding, count)
                and (binding.distance != "absolute_relative" or value > 0.0)
            ):
                matrix[bootstrap_index, index] = value
    return matrix, {
        "station_id": station_id,
        "source_id": source["source_id"],
        "source_archive_sha256": source["archive_sha256"],
        "seed_sha256": digest.hex(),
        "seed_u64_big_endian": str(seed),
        "first_three_start_indices": starts[:3],
        "sampled_year_indices_sha256": sha256_bytes(
            json.dumps(indices, ensure_ascii=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ),
        "computed_target_cell_count": len(needed),
    }


@dataclass(frozen=True)
class BootstrapTargetWork:
    corpus_sha256: str
    station: dict[str, Any]
    bindings: tuple[Binding, ...]
    needed: frozenset[int]
    metrics_helper_identity: dict[str, Any]
    helper_source_identities: dict[str, Any]


def bootstrap_target_worker(
    work: BootstrapTargetWork,
) -> tuple[np.ndarray, dict[str, Any]]:
    validate_analysis_helper_sources(work.helper_source_identities)
    _metric, bootstrap_helper, corpus_helper, target_helper = load_helpers()
    target_helper.METRICS_HELPER = locate_metrics_helper(work.metrics_helper_identity)
    return bootstrap_target_matrix(
        work.corpus_sha256,
        work.station,
        work.bindings,
        set(work.needed),
        bootstrap_helper,
        corpus_helper,
        target_helper,
    )


def median_propagating_nan(values: np.ndarray, axis: int) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return np.median(values, axis=axis)


def bootstrap_scenario(
    target_matrix: np.ndarray,
    uncertainty_bindings: Sequence[Binding],
    eligible_by_gate: dict[int, list[Binding]],
    reports: Sequence[ReportVector],
    model_id: str,
    station_id: str,
    regime: str,
    horizon: int,
    output: dict[str, list[dict[str, Any]]],
) -> dict[int, np.ndarray]:
    station_gate: dict[int, np.ndarray] = {}
    position = {
        binding.report_index: index
        for index, binding in enumerate(uncertainty_bindings)
    }
    for gate_id in BOOTSTRAP_GATES:
        bindings = eligible_by_gate.get(gate_id, [])
        if not bindings:
            continue
        columns = [position[binding.report_index] for binding in bindings]
        targets = target_matrix[:, columns]
        cube = np.empty((BOOTSTRAP_REPLICATES, 8, len(bindings)), dtype=np.float64)
        for cell, binding in enumerate(bindings):
            target = targets[:, cell]
            for replicate, report in enumerate(reports):
                generated = float(report.values[binding.report_index])
                if binding.distance == "absolute_relative":
                    cube[:, replicate, cell] = np.abs(generated - target) / target
                else:
                    cube[:, replicate, cell] = np.abs(generated - target)
        scalar = median_propagating_nan(cube, axis=1)
        for cell, binding in enumerate(bindings):
            output["scalar_cells"].append(
                {
                    "model_id": model_id,
                    "horizon_years": horizon,
                    "station_id": station_id,
                    "gate_id": gate_id,
                    "cell_id": binding.cell_key,
                    "template_id": binding.template_id,
                    "family": binding.family,
                    "variable": binding.variable,
                    "statistic": binding.statistic,
                    **bootstrap_interval(scalar[:, cell]),
                }
            )
        variable_indices: dict[tuple[str, str], list[int]] = {}
        for index, binding in enumerate(bindings):
            variable_indices.setdefault((binding.family, binding.variable), []).append(
                index
            )
        variable_by_rep = {
            key: median_propagating_nan(cube[:, :, indices], axis=2)
            for key, indices in variable_indices.items()
        }
        for (family, variable), values in variable_by_rep.items():
            output["station_variables"].append(
                {
                    "model_id": model_id,
                    "horizon_years": horizon,
                    "station_id": station_id,
                    "gate_id": gate_id,
                    "family": family,
                    "variable": variable,
                    **bootstrap_interval(median_propagating_nan(values, axis=1)),
                }
            )
        family_variables: dict[str, list[np.ndarray]] = {}
        for (family, _variable), values in variable_by_rep.items():
            family_variables.setdefault(family, []).append(values)
        family_by_rep = {
            family: median_propagating_nan(np.stack(values, axis=2), axis=2)
            for family, values in family_variables.items()
        }
        for family, values in family_by_rep.items():
            output["station_families"].append(
                {
                    "model_id": model_id,
                    "horizon_years": horizon,
                    "station_id": station_id,
                    "gate_id": gate_id,
                    "family": family,
                    **bootstrap_interval(median_propagating_nan(values, axis=1)),
                }
            )
        gate_by_rep = median_propagating_nan(
            np.stack(list(family_by_rep.values()), axis=2), axis=2
        )
        gate = median_propagating_nan(gate_by_rep, axis=1)
        station_gate[gate_id] = gate
        output["station_gates"].append(
            {
                "model_id": model_id,
                "horizon_years": horizon,
                "station_id": station_id,
                "regime": regime,
                "gate_id": gate_id,
                **bootstrap_interval(gate),
            }
        )
    return station_gate


def analyze_bootstrap(
    corpus_sha256: str,
    corpus: dict[str, Any],
    bindings: list[Binding],
    baseline_reports: dict[tuple[str, int, int], ReportVector],
    candidate_reports: dict[tuple[str, str, int, int], ReportVector],
    stations: Sequence[dict[str, Any]],
    bootstrap_helper: Any,
    corpus_helper: Any,
    target_helper: Any,
    analysis_helper_release: dict[str, Any],
) -> dict[str, Any]:
    del bootstrap_helper, corpus_helper, target_helper
    metrics_helper_identity = require_dict(
        analysis_helper_release["binary"], "release analysis-helper binary"
    )
    helper_source_identities = require_dict(
        analysis_helper_release["sources"], "release analysis-helper sources"
    )
    validate_analysis_helper_sources(helper_source_identities)
    metrics_helper = locate_metrics_helper(metrics_helper_identity)
    uncertainty = [row for row in bindings if row.gate_id in BOOTSTRAP_GATES]
    if len(uncertainty) != 645:
        raise AnalysisError(f"bootstrap membership is {len(uncertainty)}, expected 645")
    # Reindexing the compact uncertainty target cache is independent of report indices.
    uncertainty = [
        Binding(
            index=index,
            report_index=row.report_index,
            gate_id=row.gate_id,
            template_id=row.template_id,
            dimensions=row.dimensions,
            family=row.family,
            variable=row.variable,
            statistic=row.statistic,
            distance=row.distance,
            surface_id=row.surface_id,
            generated_path=row.generated_path,
            generated_count_path=row.generated_count_path,
            target_path=row.target_path,
            target_count_path=row.target_count_path,
            target_scale_path=row.target_scale_path,
            cell_key=row.cell_key,
        )
        for index, row in enumerate(uncertainty)
    ]
    by_report_index = {row.report_index: row for row in uncertainty}
    output: dict[str, list[dict[str, Any]]] = {
        "scalar_cells": [],
        "station_variables": [],
        "station_families": [],
        "station_gates": [],
        "regime_gates": [],
        "corpus_gates": [],
    }
    target_audits: list[dict[str, Any]] = []
    gate_series: dict[tuple[str, int, int, str], np.ndarray] = {}
    models = (BASELINE_ID,) + CANDIDATES
    station_work: list[
        tuple[dict[str, Any], dict[int, dict[int, list[Binding]]], BootstrapTargetWork]
    ] = []
    for station in stations:
        station_id = station["station_id"]
        eligible_by_horizon: dict[int, dict[int, list[Binding]]] = {}
        needed: set[int] = set()
        for horizon in HORIZONS:
            baseline = [
                baseline_reports[(station_id, horizon, rep)] for rep in REPLICATES
            ]
            eligible_by_horizon[horizon] = {}
            for gate_id in BOOTSTRAP_GATES:
                rows = [
                    by_report_index[row.report_index]
                    for row in bindings
                    if row.gate_id == gate_id
                    and baseline_eligible(corpus, row, station_id, baseline)
                ]
                eligible_by_horizon[horizon][gate_id] = rows
                needed.update(row.index for row in rows)
        station_work.append(
            (
                station,
                eligible_by_horizon,
                BootstrapTargetWork(
                    corpus_sha256=corpus_sha256,
                    station={
                        "station_id": station_id,
                        "sources": {
                            "daymet": {
                                "source_identity": station["sources"]["daymet"][
                                    "source_identity"
                                ]
                            }
                        },
                    },
                    bindings=tuple(uncertainty),
                    needed=frozenset(needed),
                    metrics_helper_identity=dict(metrics_helper_identity),
                    helper_source_identities=dict(helper_source_identities),
                ),
            )
        )
    workers = min(4, len(station_work))
    context_name = (
        "fork" if "fork" in multiprocessing.get_all_start_methods() else "spawn"
    )
    context = multiprocessing.get_context(context_name)
    with ProcessPoolExecutor(max_workers=workers, mp_context=context) as executor:
        target_results = executor.map(
            bootstrap_target_worker,
            (item[2] for item in station_work),
            chunksize=1,
        )
        for (station, eligible_by_horizon, _work), (target_matrix, audit) in zip(
            station_work, target_results, strict=True
        ):
            station_id = station["station_id"]
            target_audits.append(audit)
            for model_id in models:
                for horizon in HORIZONS:
                    if model_id == BASELINE_ID:
                        reports = [
                            baseline_reports[(station_id, horizon, rep)]
                            for rep in REPLICATES
                        ]
                    else:
                        reports = [
                            candidate_reports[(model_id, station_id, horizon, rep)]
                            for rep in REPLICATES
                        ]
                    station_series = bootstrap_scenario(
                        target_matrix,
                        uncertainty,
                        eligible_by_horizon[horizon],
                        reports,
                        model_id,
                        station_id,
                        station["regime"],
                        horizon,
                        output,
                    )
                    for gate_id, values in station_series.items():
                        gate_series[(model_id, horizon, gate_id, station_id)] = values
    for model_id in models:
        for horizon in HORIZONS:
            for gate_id in BOOTSTRAP_GATES:
                applicable = [
                    row
                    for row in stations
                    if (model_id, horizon, gate_id, row["station_id"]) in gate_series
                ]
                if not applicable:
                    continue
                corpus_values = median_propagating_nan(
                    np.stack(
                        [
                            gate_series[(model_id, horizon, gate_id, row["station_id"])]
                            for row in applicable
                        ],
                        axis=1,
                    ),
                    axis=1,
                )
                output["corpus_gates"].append(
                    {
                        "model_id": model_id,
                        "horizon_years": horizon,
                        "gate_id": gate_id,
                        "station_count": len(applicable),
                        **bootstrap_interval(corpus_values),
                    }
                )
                for regime in REGIMES:
                    selected = [row for row in applicable if row["regime"] == regime]
                    if not selected:
                        continue
                    regime_values = median_propagating_nan(
                        np.stack(
                            [
                                gate_series[
                                    (model_id, horizon, gate_id, row["station_id"])
                                ]
                                for row in selected
                            ],
                            axis=1,
                        ),
                        axis=1,
                    )
                    output["regime_gates"].append(
                        {
                            "model_id": model_id,
                            "horizon_years": horizon,
                            "gate_id": gate_id,
                            "regime": regime,
                            "station_count": len(selected),
                            **bootstrap_interval(regime_values),
                        }
                    )
    return {
        "contract_id": "cligen-a5-observed-circular-moving-block-bootstrap-v1",
        "decision_role": "report_only",
        "replicates": BOOTSTRAP_REPLICATES,
        "block_length_years": 5,
        "target_workers": workers,
        "multiprocessing_start_method": context_name,
        "metrics_helper": {
            "path": metrics_helper.relative_to(ROOT).as_posix(),
            "sha256": sha256_path(metrics_helper),
            "bytes": metrics_helper.stat().st_size,
        },
        "target_cache": target_audits,
        "intervals": output,
    }


def diagnostic_summary(
    manifest: dict[str, Any], runtime: dict[str, list[dict[str, int]]]
) -> dict[str, Any]:
    contract_paths = {
        name: resolve_repo_identity(identity).relative_to(ROOT).as_posix()
        for name, identity in manifest["contracts"].items()
    }
    source_manifest_path = resolve_repo_artifact(manifest["fit"]["source_manifest"])
    source_manifest = strict_json(source_manifest_path)
    if source_manifest.get("source_manifest_version") != 1:
        raise AnalysisError("fit source manifest is not revision 1")
    fit_path = resolve_repo_artifact(manifest["fit"]["fit_manifest"])
    fit = strict_json(fit_path)
    if fit.get("fit_manifest_version") != 1 or len(fit.get("stations", [])) != 17:
        raise AnalysisError("fit manifest shape differs from A5b fit revision 1")
    fit_by_candidate: dict[str, list[dict[str, Any]]] = {row: [] for row in CANDIDATES}
    for station in fit["stations"]:
        candidate_rows = station["candidate_fits"]
        if [row["candidate_id"] for row in candidate_rows] != list(CANDIDATES):
            raise AnalysisError("fit candidate order differs")
        for row in candidate_rows:
            fit_by_candidate[row["candidate_id"]].append(row)
    bundle_interventions: dict[str, list[str]] = {row: [] for row in CANDIDATES}
    bundle_warnings: dict[str, list[str]] = {row: [] for row in CANDIDATES}
    for artifact in manifest["fit"]["bundles"]:
        bundle = strict_json(resolve_repo_artifact(artifact))
        for extension in bundle["extensions"]:
            candidate = extension["candidate_id"]
            bundle_interventions[candidate].extend(
                extension["diagnostics"]["interventions"]
            )
            bundle_warnings[candidate].extend(extension["diagnostics"]["warnings"])
    candidates: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        fits = fit_by_candidate[candidate]
        run_rows = runtime[candidate]
        candidates.append(
            {
                "candidate_id": candidate,
                "fit_status_counts": {
                    status: sum(row["fit_status"] == status for row in fits)
                    for status in sorted({row["fit_status"] for row in fits})
                },
                "runtime_parameter_count": summary(
                    [float(row["runtime_parameter_count"]) for row in fits]
                ),
                "runtime_parameter_count_sum_over_stations": sum(
                    row["runtime_parameter_count"] for row in fits
                ),
                "serialized_numeric_count": summary(
                    [float(row["serialized_numeric_count"]) for row in fits]
                ),
                "fit_interventions": sorted(bundle_interventions[candidate]),
                "fit_warnings": sorted(bundle_warnings[candidate]),
                "run_wall_time_ms": summary(
                    [float(row["wall_time_ms"]) for row in run_rows]
                ),
                "run_intervention_totals": {
                    name: sum(row[name] for row in run_rows)
                    for name in (
                        "precipitation_clip_count",
                        "temperature_order_repair_count",
                        "dewpoint_cap_count",
                        "counterfactual_month_count",
                    )
                },
                "run_count": len(run_rows),
            }
        )
    build_paths = {
        field: resolve_repo_artifact(manifest["build"][field])
        .relative_to(ROOT)
        .as_posix()
        for field in ("cligen_binary", "overlay_binary")
    }
    return {
        "contract_paths": contract_paths,
        "source_manifest_sha256": sha256_path(source_manifest_path),
        "fit_manifest_sha256": sha256_path(fit_path),
        "build_artifact_paths": build_paths,
        "candidate_diagnostics": candidates,
        "execution_failures": manifest["execution"]["failures"],
    }


def synthetic_analysis_freeze() -> dict[str, Any]:
    sources = {
        relative: {
            "sha256": sha256_path(ROOT / relative),
            "bytes": (ROOT / relative).stat().st_size,
        }
        for relative in ANALYSIS_HELPER_SOURCE_PATHS
    }
    frozen = {
        relative: identity["sha256"] for relative, identity in sources.items()
    }
    frozen[ORIGINAL_ANALYZER.relative_to(ROOT).as_posix()] = sha256_path(
        ORIGINAL_ANALYZER
    )
    return {
        "pre_candidate_freeze_version": 1,
        "status": "passed",
        "candidate_output_absent": True,
        "a5a_pinned_artifacts": {
            ACCEPTED_BASELINE_MANIFEST.relative_to(ROOT).as_posix(): sha256_path(
                ACCEPTED_BASELINE_MANIFEST
            ),
            ACCEPTED_BASELINE_ARCHIVE.relative_to(ROOT).as_posix(): sha256_path(
                ACCEPTED_BASELINE_ARCHIVE
            ),
        },
        "a5b_frozen_artifacts": frozen,
        "analysis_helper_release": {
            "contract_id": "a5b-analysis-helper-release-v1",
            "built_before_candidate_output": True,
            "build": {
                "command": list(RELEASE_METRICS_HELPER_COMMAND),
                "cwd": ".",
                "profile": "release",
                "locked": True,
                "offline": True,
                "forbidden_environment_absent": list(
                    FORBIDDEN_METRICS_HELPER_BUILD_ENV
                ),
                "cargo_version_verbose": "synthetic self-test cargo",
                "rustc_version_verbose": "synthetic self-test rustc",
            },
            "sources": sources,
            "binary": {
                "path": RELEASE_METRICS_HELPER.relative_to(ROOT).as_posix(),
                "sha256": sha256_path(RELEASE_METRICS_HELPER),
                "bytes": RELEASE_METRICS_HELPER.stat().st_size,
            },
        },
    }


def self_test() -> dict[str, Any]:
    metric_helper, bootstrap_helper, _corpus_helper, _target_helper = load_helpers()
    if (
        len(RUN_RECORD_CONTRACT_KEYS) != 15
        or len(EVIDENCE_CONTRACT_KEYS) != 23
        or RUN_RECORD_CONTRACT_KEYS & EVIDENCE_ONLY_CONTRACT_KEYS
    ):
        raise AssertionError("frozen contract key sets are inconsistent")
    if REGIMES != ("arid", "monsoonal", "humid", "cold", "fixture"):
        raise AssertionError("frozen regime order differs")
    freeze_fixture = synthetic_analysis_freeze()
    frozen = validate_analysis_freeze_value(
        freeze_fixture,
        ACCEPTED_BASELINE_MANIFEST,
        ACCEPTED_BASELINE_ARCHIVE,
        "f" * 64,
    )
    if frozen["analysis_helper_release"]["binary"]["path"] != (
        "target/release/cligen-quality-estimator"
    ):
        raise AssertionError("release estimator path was not retained")
    mutated = json.loads(json.dumps(freeze_fixture))
    baseline_relative = ACCEPTED_BASELINE_ARCHIVE.relative_to(ROOT).as_posix()
    mutated["a5a_pinned_artifacts"][baseline_relative] = "0" * 64
    try:
        validate_analysis_freeze_value(
            mutated,
            ACCEPTED_BASELINE_MANIFEST,
            ACCEPTED_BASELINE_ARCHIVE,
            "f" * 64,
        )
    except AnalysisError:
        pass
    else:
        raise AssertionError("mutated accepted baseline freeze was accepted")
    mutated = json.loads(json.dumps(freeze_fixture))
    mutated["analysis_helper_release"]["sources"][
        "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/corpus_common.py"
    ]["sha256"] = "0" * 64
    try:
        validate_analysis_freeze_value(
            mutated,
            ACCEPTED_BASELINE_MANIFEST,
            ACCEPTED_BASELINE_ARCHIVE,
            "f" * 64,
        )
    except AnalysisError:
        pass
    else:
        raise AssertionError("mutated analysis helper freeze was accepted")
    manifest, bindings = expand_bindings(metric_helper)
    projections = projected_bindings(manifest, bindings)
    if conventional_median([1.0, 2.0, 3.0, 4.0]) != 2.5:
        raise AssertionError("even conventional median failed")
    if conventional_median(np.array([1.0, 2.0, 3.0])) != 2.0:
        raise AssertionError("NumPy conventional median failed")
    if nearest_rank(np.array([1.0, 2.0, 3.0]), 1, 2) != 2.0:
        raise AssertionError("NumPy nearest rank failed")
    if (
        nearest_rank(list(range(1, 21)), 1, 20) != 1.0
        or nearest_rank(list(range(1, 21)), 19, 20) != 19.0
    ):
        raise AssertionError("nearest-rank endpoint failed")
    # Equal-weight hierarchy differs from flattening: five cells in one
    # variable and one in another become median(median(A), median(B)).
    hierarchy = conventional_median(
        [conventional_median([0, 0, 0, 0, 0]), conventional_median([100])]
    )
    if hierarchy != 50.0 or conventional_median([0, 0, 0, 0, 0, 100]) != 0.0:
        raise AssertionError("equal-weight hierarchy was flattened")
    sample_binding = bindings[0]
    defined = ReportVector(
        np.zeros(len(bindings)),
        [2] * len(bindings),
        np.zeros(len(bindings)),
        [2] * len(bindings),
        np.ones(len(bindings)),
        "0" * 64,
    )
    missing = ReportVector(
        defined.values.copy(),
        list(defined.counts),
        defined.targets.copy(),
        list(defined.target_counts),
        defined.scales.copy(),
        defined.parameter_sha256,
    )
    missing.values[sample_binding.report_index] = np.nan
    if candidate_defines([missing] * 8, sample_binding):
        raise AssertionError("candidate changed the frozen denominator")
    starts, indices = bootstrap_helper.bootstrap_indices(
        0x123456789ABCDEF0, 16, 5, 2000
    )
    if starts[0] != [8, 0, 13, 15] or indices[0] != [
        8,
        9,
        10,
        11,
        12,
        0,
        1,
        2,
        3,
        4,
        13,
        14,
        15,
        0,
        1,
        15,
    ]:
        raise AssertionError("bootstrap block/draw order changed")
    if sum((index + 1) * value for index, value in enumerate(indices[0])) != 1011:
        raise AssertionError("order-sensitive bootstrap statistic changed")
    generator = bootstrap_helper.SplitMix64V1(0)
    if [generator.bounded(10) for _ in range(8)] != [5, 0, 9, 4, 7, 0, 3, 0]:
        raise AssertionError("non-divisor bounded draw changed")
    bootstrap_helper.validate_golden(strict_json(BOOTSTRAP_GOLDEN))
    if not passes_gate_1(0.9, 1.0, 0.9, 1.0, 11, [(1.05, 1.0)]):
        raise AssertionError("gate 1 inclusive boundary failed")
    if passes_gate_1(0.9000001, 1.0, 0.9, 1.0, 11, [(1.05, 1.0)]):
        raise AssertionError("gate 1 upper boundary failed")
    if not passes_gate_2(1.1, 1.0) or passes_gate_2(1.1000001, 1.0):
        raise AssertionError("gate 2 boundary failed")
    if not passes_gate_3_or_6(1.1, 1.0, [(1.25, 1.0)]) or passes_gate_3_or_6(
        1.1, 1.0, [(1.2500001, 1.0)]
    ):
        raise AssertionError("gate 3/6 boundary failed")
    if not passes_gate_4(1.1, 1.0) or passes_gate_4(1.1000001, 1.0):
        raise AssertionError("gate 4 boundary failed")
    if not passes_gate_5(1.0, 1.0, 1.0) or passes_gate_5(1.0000001, 0.0, 1.0):
        raise AssertionError("gate 5 inclusive boundary failed")
    if not passes_gate_7(True, True) or passes_gate_7(True, False):
        raise AssertionError("gate 7 evidence boundary failed")
    selector = {"stations": [{"station_id": "aa000001", "m": [[1, 2], [3, 4]]}]}
    if resolve_path(selector, "$.stations[@station_id=aa000001].m[1][0]") != 3:
        raise AssertionError("station-selector/matrix-index resolver failed")
    fixture = {
        "path": METRIC_SCHEMA.relative_to(ROOT).as_posix(),
        "sha256": sha256_path(METRIC_SCHEMA),
        "bytes": METRIC_SCHEMA.stat().st_size,
    }
    if (
        resolve_repo_artifact(fixture) != METRIC_SCHEMA.resolve()
        or resolve_archive_artifact(ROOT, fixture) != METRIC_SCHEMA.resolve()
    ):
        raise AssertionError("contained artifact identity resolution failed")
    for resolver, base in (
        (resolve_repo_artifact, None),
        (resolve_archive_artifact, ROOT),
    ):
        escaped = {"path": "../outside", "sha256": "0" * 64, "bytes": 1}
        try:
            resolver(escaped) if base is None else resolver(base, escaped)
        except AnalysisError:
            pass
        else:
            raise AssertionError("artifact path traversal was accepted")
    return {
        "status": "pass",
        "expanded_binding_count": len(bindings),
        "projection_counts": {key: len(value) for key, value in projections.items()},
        "checks": [
            "strict_json_and_path_resolver",
            "contained_exact_artifact_resolution",
            "fifteen_and_twenty_three_contract_key_sets",
            "five_regime_order_including_fixture",
            "accepted_baseline_and_release_helper_freeze",
            "baseline_and_helper_freeze_mutations",
            "sequence_and_numpy_conventional_median",
            "sequence_and_numpy_nearest_rank",
            "equal_weight_hierarchy",
            "baseline_denominator_freeze",
            "order_sensitive_bootstrap",
            "non_divisor_bounded_draw",
            "gate_1_through_7_boundaries",
        ],
    }


def execute(
    candidate_manifest_path: Path,
    candidate_archive_dir: Path,
    baseline_manifest_path: Path,
    baseline_archive_path: Path,
    observed_target_path: Path,
    output_path: Path,
) -> None:
    if output_path.exists():
        raise AnalysisError(f"refusing to overwrite analysis output: {output_path}")
    candidate_manifest = strict_json(candidate_manifest_path)
    validate_schema(candidate_manifest, CANDIDATE_SCHEMA, "A5b candidate evidence")
    if candidate_manifest["status"] != "sealed":
        raise AnalysisError("candidate evidence is not sealed")
    if set(candidate_manifest["contracts"]) != EVIDENCE_CONTRACT_KEYS:
        raise AnalysisError(
            "candidate evidence contract key set differs from the frozen 23"
        )
    if [
        row["candidate_id"] for row in candidate_manifest["matrix"]["candidates"]
    ] != list(CANDIDATES):
        raise AnalysisError("candidate matrix order differs from the frozen contract")
    frozen_analysis = validate_analysis_freeze(
        candidate_manifest, baseline_manifest_path, baseline_archive_path
    )
    metric_helper, bootstrap_helper, corpus_helper, target_helper = load_helpers()
    metric_manifest, bindings = expand_bindings(metric_helper)
    projections = projected_bindings(metric_manifest, bindings)
    station_ids = candidate_manifest["corpus"]["station_ids"]
    replicates = candidate_manifest["matrix"]["replicates"]
    if [row["replicate"] for row in replicates] != list(REPLICATES):
        raise AnalysisError("replicate records are not ordered 0 through 7")
    burn_by_replicate = {row["replicate"]: row["legacy_burn"] for row in replicates}
    corpus = strict_json(observed_target_path)
    if corpus.get("observed_target_corpus_schema_version") != 1:
        raise AnalysisError("observed target is not corpus schema version 1")
    corpus_sha = sha256_path(observed_target_path)
    if corpus_sha != candidate_manifest["corpus"]["content_sha256"]:
        raise AnalysisError("candidate evidence binds a different observed corpus")
    stations = corpus["stations"]
    station_by_id = {row["station_id"]: row for row in stations}
    if len(station_by_id) != 17 or set(station_by_id) != set(station_ids):
        raise AnalysisError("observed/candidate station sets differ")
    stations = [station_by_id[station_id] for station_id in station_ids]
    if {row.get("regime") for row in stations} != set(REGIMES):
        raise AnalysisError("observed station regime vocabulary differs from the frozen order")
    baseline_reports, baseline_manifest = load_baseline_reports(
        baseline_manifest_path,
        baseline_archive_path,
        bindings,
        station_ids,
        burn_by_replicate,
    )
    if baseline_manifest["inputs"]["observed_target_corpus_sha256"] != corpus_sha:
        raise AnalysisError("accepted baseline binds a different observed corpus")
    candidate_reports, runtime = load_candidate_reports(
        candidate_manifest, candidate_archive_dir, bindings, station_ids
    )
    eligibility = eligible_cell_inventory(corpus, bindings, baseline_reports, stations)
    evidence_failures: list[str] = []
    deterministic: list[dict[str, Any]] = []
    for candidate_id in CANDIDATES:
        for horizon in HORIZONS:
            gates = [
                analyze_distance_gate(
                    corpus,
                    bindings,
                    baseline_reports,
                    candidate_reports,
                    candidate_id,
                    horizon,
                    gate_id,
                    stations,
                    evidence_failures,
                )
                for gate_id in (1, 2, 3, 4)
            ]
            gates.append(
                analyze_descriptor_gate(
                    bindings,
                    baseline_reports,
                    candidate_reports,
                    candidate_id,
                    horizon,
                    stations,
                    evidence_failures,
                )
            )
            gates.append(
                analyze_distance_gate(
                    corpus,
                    bindings,
                    baseline_reports,
                    candidate_reports,
                    candidate_id,
                    horizon,
                    6,
                    stations,
                    evidence_failures,
                )
            )
            # Gate 7 is finalized conservatively after climate completeness is
            # known; this CLI has no downstream-WEPP input and cannot pass it.
            gates.append({"gate_id": 7, "passed": None, "status": "pending"})
            deterministic.append(
                {
                    "candidate_id": candidate_id,
                    "horizon_years": horizon,
                    "gates": gates,
                }
            )
    sensitivities = analyze_sensitivities(
        corpus,
        projections,
        baseline_reports,
        candidate_reports,
        stations,
        evidence_failures,
    )
    climate_evidence_complete = (
        not evidence_failures and not candidate_manifest["execution"]["failures"]
    )
    for row in deterministic:
        row["gates"][-1] = {
            "gate_id": 7,
            "status": "pending_downstream_wepp",
            "passed": passes_gate_7(climate_evidence_complete, False),
            "climate_evidence_complete": climate_evidence_complete,
            "downstream_wepp_complete": False,
            "climate_failure_count": len(evidence_failures),
            "completion_rule": (
                "the package-level final analysis combines this climate result "
                "with the separately pinned WEPP campaign"
            ),
        }
        row["climate_gates_1_through_6_pass"] = all(
            gate["passed"] is True for gate in row["gates"][:6]
        )
        row["all_seven_package_gates_pass"] = all(
            gate["passed"] is True for gate in row["gates"]
        )
    diagnostics = diagnostic_summary(candidate_manifest, runtime)
    bootstrap = analyze_bootstrap(
        corpus_sha,
        corpus,
        bindings,
        baseline_reports,
        candidate_reports,
        stations,
        bootstrap_helper,
        corpus_helper,
        target_helper,
        frozen_analysis["analysis_helper_release"],
    )
    result = {
        "a5b_climate_analysis_schema_version": 1,
        "status": "complete",
        "decision_scope": "climate_only_no_profile_promotion",
        "inputs": {
            "candidate_manifest_sha256": sha256_path(candidate_manifest_path),
            "baseline_manifest_sha256": sha256_path(baseline_manifest_path),
            "baseline_archive_sha256": sha256_path(baseline_archive_path),
            "observed_target_corpus_sha256": corpus_sha,
            "metric_manifest_sha256": sha256_path(METRIC_MANIFEST),
            "metric_schema_sha256": sha256_path(METRIC_SCHEMA),
            "metric_verifier_sha256": sha256_path(METRIC_VERIFIER),
            "bootstrap_reference_sha256": sha256_path(BOOTSTRAP_REFERENCE),
            "bootstrap_golden_sha256": sha256_path(BOOTSTRAP_GOLDEN),
            "build_targets_sha256": sha256_path(BUILD_TARGETS),
            "corpus_common_sha256": sha256_path(CORPUS_COMMON),
            "pre_candidate_freeze_sha256": frozen_analysis[
                "pre_candidate_freeze_sha256"
            ],
            "pre_candidate_analyzer_sha256": frozen_analysis[
                "pre_candidate_analyzer_sha256"
            ],
            "post_output_analysis_freeze_sha256": frozen_analysis[
                "post_output_analysis_freeze_sha256"
            ],
            "analyzer_sha256": frozen_analysis["analyzer_sha256"],
            "analysis_helper_release": frozen_analysis[
                "analysis_helper_release"
            ],
        },
        "matrix": {
            "candidate_runs": len(candidate_manifest["runs"]),
            "baseline_off_runs": len(baseline_reports),
            "expanded_metric_bindings": len(bindings),
            "candidate_ids": list(CANDIDATES),
            "horizons_years": list(HORIZONS),
            "replicates": list(replicates),
        },
        "aggregation": metric_manifest["aggregation"],
        "baseline_eligible_cell_sets": eligibility,
        "deterministic_gate_results": deterministic,
        "sensitivity_projections": sensitivities,
        "evidence_completeness": {
            "climate_evidence_complete": climate_evidence_complete,
            "downstream_wepp_status": "pending_external_campaign_input",
            "gate_7_passed": passes_gate_7(climate_evidence_complete, False),
            "climate_failures": sorted(set(evidence_failures)),
        },
        "diagnostics": diagnostics,
        "observed_target_uncertainty": bootstrap,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_bytes(result))
    print(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_manifest", type=Path, nargs="?")
    parser.add_argument("candidate_archive_dir", type=Path, nargs="?")
    parser.add_argument("baseline_manifest", type=Path, nargs="?")
    parser.add_argument("baseline_archive", type=Path, nargs="?")
    parser.add_argument("observed_target", type=Path, nargs="?")
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    positional = (
        args.candidate_manifest,
        args.candidate_archive_dir,
        args.baseline_manifest,
        args.baseline_archive,
        args.observed_target,
        args.output,
    )
    if args.self_test:
        if any(value is not None for value in positional):
            parser.error("--self-test does not accept evidence inputs")
        print(json.dumps(self_test(), allow_nan=False, indent=2, sort_keys=True))
        return
    if any(value is None for value in positional):
        parser.error("six evidence/output paths are required")
    execute(
        args.candidate_manifest.resolve(strict=True),
        args.candidate_archive_dir.resolve(strict=True),
        args.baseline_manifest.resolve(strict=True),
        args.baseline_archive.resolve(strict=True),
        args.observed_target.resolve(strict=True),
        args.output.resolve(),
    )


if __name__ == "__main__":
    try:
        main()
    except (AnalysisError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"analyze-a5b: {error}", file=sys.stderr)
        raise SystemExit(1) from error
