#!/usr/bin/env python3
"""Execute, archive, and summarize the preregistered A5a 544-run baseline.

The raw `.cli` streams are hashed and removed. Reports, provenance sidecars,
and exact station parameters are committed in a deterministic evidence
archive; ephemeral target-directory copies are removed after verification.

Usage:
  run-baseline-matrix.py target/release/cligen <us-2015-cache> <target-directory>
"""

from __future__ import annotations

import concurrent.futures
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import zlib

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
CORPUS_CONFIG = PACKAGE / "corpus" / "corpus-config-v1.json"
OBSERVED_TARGET = PACKAGE / "corpus" / "observed-target-corpus-v1.json"
PREREGISTRATION = PACKAGE / "a5b-pre-registration.md"
EVALUATION_SPEC = ROOT / "docs" / "specifications" / "SPEC-A5-EVALUATION.md"
GATE_METRICS = ROOT / "docs" / "specifications" / "a5-climate-gate-metrics-v1.json"
GATE_METRICS_SCHEMA = (
    ROOT / "docs" / "specifications" / "a5-climate-gate-metrics-v1.schema.json"
)
GATE_METRICS_VERIFIER = PACKAGE / "verify-a5-climate-gate-metrics-v1.py"
OBSERVED_BOOTSTRAP = PACKAGE / "observed-bootstrap-v1.py"
OBSERVED_BOOTSTRAP_GOLDEN = PACKAGE / "observed-bootstrap-v1-golden.json"
WEPP_RESPONSE_SCHEMA = (
    ROOT / "docs" / "specifications" / "a5-wepp-response-v1.schema.json"
)
WEPP_RESPONSE_VERIFIER = PACKAGE / "verify-wepp-response-schema.py"
WEPP_RESPONSE_PROTOCOL = PACKAGE / "wepp-response-protocol.md"
MANIFEST = PACKAGE / "baseline-run-manifest-v1.json"
ANALYSIS = PACKAGE / "baseline-analysis-v1.json"
MANIFEST_SCHEMA = PACKAGE / "baseline-run-manifest-v1.schema.json"
ANALYSIS_SCHEMA = PACKAGE / "baseline-analysis-v1.schema.json"
EVIDENCE_ARCHIVE = PACKAGE / "baseline-evidence-v1.tar.gz"
VERIFIER = PACKAGE / "verify-baseline-evidence.py"
QUALITY_SCHEMA = ROOT / "docs" / "specifications" / "quality-report-s2-m3.schema.json"
PROVENANCE_SCHEMA = ROOT / "docs" / "specifications" / "provenance-v1.schema.json"
BUILD_COMMAND = [
    "cargo",
    "build",
    "--locked",
    "--offline",
    "--release",
    "--bin",
    "cligen",
]
BUILD_PROFILE = "release"
EXPECTED_BINARY = ROOT / "target" / BUILD_PROFILE / "cligen"
EXPECTED_EVIDENCE_TARGET = ROOT / "target" / "a5a-baseline-v1"
ARCHIVE_FORMAT = "tar+gzip"
ARCHIVE_QUALITY_PREFIX = "quality-reports"
ARCHIVE_PROVENANCE_PREFIX = "provenance"
ARCHIVE_PAR_PREFIX = "station-parameters"
SNAPSHOT_DIRNAME = ".a5a-input-snapshot"
SNAPSHOT_STATION_DIRNAME = "stations"
GZIP_COMPRESSLEVEL = 9
FIXED_ARCHIVE_MTIME = 0
FIXED_ARCHIVE_MODE = 0o644
HORIZONS = [30, 100]
BURNS = [0, 17, 101, 503, 1009, 5003, 10007, 50021]
QC_POLICIES = ["faithful", "off"]
WORKERS = min(4, max(1, os.cpu_count() or 1))
SAFE_CARGO_RUST_ENV = {
    "CARGO_NET_OFFLINE",
    "RUST_BACKTRACE",
    "RUST_LIB_BACKTRACE",
    "RUST_LOG",
}
SAFE_CARGO_RUST_ENV_PREFIXES = ("CARGO_TERM_",)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def implementation_identity() -> dict[str, object]:
    paths = {
        ROOT / "Cargo.lock",
        ROOT / "Cargo.toml",
        ROOT / "rust-toolchain.toml",
    }
    paths.update(ROOT.glob(".cargo/**/*"))
    paths.update(ROOT.glob("crates/**/Cargo.toml"))
    paths.update(ROOT.glob("crates/**/*.rs"))
    paths.update(ROOT.glob("crates/**/src/**/*.json"))
    paths.update(ROOT.glob("crates/**/schemas/**/*.json"))
    files = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in sorted(paths)
        if path.is_file()
    }
    return {"sha256": canonical_sha256(files), "files": files}


def command_version(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.rstrip("\n")


def cargo_rust_environment_audit() -> dict[str, str]:
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
        raise ValueError(
            "compiler-affecting Cargo/Rust environment must be unset for the "
            f"pinned evidence build: {unsafe}"
        )
    return relevant


def cargo_configuration_audit() -> dict[str, object]:
    cargo_home = Path.home() / ".cargo"
    candidates = set()
    for directory in (ROOT, *ROOT.parents):
        candidates.add(directory / ".cargo" / "config")
        candidates.add(directory / ".cargo" / "config.toml")
    candidates.add(cargo_home / "config")
    candidates.add(cargo_home / "config.toml")
    searched = sorted(str(path) for path in candidates)
    active = sorted(str(path) for path in candidates if path.is_file())
    if active:
        raise ValueError(
            "Cargo configuration is forbidden for the pinned evidence build; "
            f"unset or remove these effective config files: {active}"
        )
    return {
        "workspace_root": str(ROOT),
        "cargo_home": str(cargo_home),
        "searched_config_paths": searched,
        "active_config_files": active,
    }


def build_binary(binary: Path) -> dict[str, object]:
    if binary != EXPECTED_BINARY.resolve():
        raise ValueError(
            f"binary must be {EXPECTED_BINARY} for the pinned {BUILD_PROFILE} build"
        )
    cargo_rust_environment = cargo_rust_environment_audit()
    cargo_configuration = cargo_configuration_audit()
    rustflags = os.environ.get("RUSTFLAGS") or None
    encoded_rustflags = os.environ.get("CARGO_ENCODED_RUSTFLAGS") or None
    rustc_wrapper = os.environ.get("RUSTC_WRAPPER") or None
    rustc_workspace_wrapper = os.environ.get("RUSTC_WORKSPACE_WRAPPER") or None
    cargo_target_dir = os.environ.get("CARGO_TARGET_DIR") or None
    cargo_build_target = os.environ.get("CARGO_BUILD_TARGET") or None
    if rustflags or encoded_rustflags:
        raise ValueError("RUSTFLAGS must be unset for the pinned evidence build")
    if rustc_wrapper or rustc_workspace_wrapper:
        raise ValueError(
            "RUSTC_WRAPPER and RUSTC_WORKSPACE_WRAPPER must be unset for the "
            "pinned evidence build"
        )
    if cargo_target_dir or cargo_build_target:
        raise ValueError(
            "CARGO_TARGET_DIR and CARGO_BUILD_TARGET must be unset for the pinned build"
        )
    cargo_executable = shutil.which("cargo")
    rustc_command = os.environ.get("RUSTC", "rustc")
    rustc_executable = shutil.which(rustc_command)
    if cargo_executable is None or rustc_executable is None:
        raise FileNotFoundError("cargo and rustc must resolve to executable files")
    subprocess.run(
        [cargo_executable, *BUILD_COMMAND[1:]],
        cwd=ROOT,
        check=True,
    )
    if cargo_configuration_audit() != cargo_configuration:
        raise RuntimeError("effective Cargo configuration changed during the build")
    if cargo_rust_environment_audit() != cargo_rust_environment:
        raise RuntimeError("Cargo/Rust environment changed during the build")
    if not binary.is_file():
        raise FileNotFoundError(binary)
    return {
        "command": BUILD_COMMAND,
        "profile": BUILD_PROFILE,
        "binary_path": str(binary.relative_to(ROOT)),
        "cargo_executable": cargo_executable,
        "rustc_executable": rustc_executable,
        "rustc_version_verbose": command_version(
            [rustc_executable, "--version", "--verbose"]
        ),
        "cargo_version_verbose": command_version(
            [cargo_executable, "--version", "--verbose"]
        ),
        "cargo_configuration": cargo_configuration,
        "cargo_rust_environment": cargo_rust_environment,
        "build_environment": {
            "RUSTC": os.environ.get("RUSTC"),
            "RUSTC_WRAPPER": rustc_wrapper,
            "RUSTC_WORKSPACE_WRAPPER": rustc_workspace_wrapper,
            "RUSTFLAGS": rustflags,
            "CARGO_ENCODED_RUSTFLAGS": encoded_rustflags,
            "CARGO_TARGET_DIR": cargo_target_dir,
            "CARGO_BUILD_TARGET": cargo_build_target,
        },
    }


def reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON token: {token}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"JSON number overflows binary64: {token}")
    return value


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(
            handle,
            parse_constant=reject_nonfinite,
            parse_float=parse_finite_float,
            object_pairs_hook=reject_duplicate_keys,
        )


def load_report(path: Path) -> dict:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"quality/provenance document is not an object: {path}")
    return value


def validate_instance(value: object, schema_path: Path) -> None:
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        raise ValueError(f"schema document is not an object: {schema_path}")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)


def days_in_horizon(years: int) -> int:
    leap_years = sum(
        year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        for year in range(1, years + 1)
    )
    return years * 365 + leap_years


def assert_matrix(matrix: object, name: str) -> None:
    if not isinstance(matrix, list) or len(matrix) != 12:
        raise ValueError(f"{name}: outer dimension is not 12")
    if any(not isinstance(row, list) or len(row) != 12 for row in matrix):
        raise ValueError(f"{name}: inner dimension is not 12")


def validate_report(report: dict, years: int, qc: str) -> None:
    if report["quality_report_schema_version"] != 2:
        raise ValueError("unexpected quality-report schema version")
    if report["metrics_version"] != 3:
        raise ValueError("unexpected metrics version")
    if report["identity"]["content"]["days"] != days_in_horizon(years):
        raise ValueError("generated day count does not match Gregorian horizon")
    if report["identity"]["content"]["years"] != years:
        raise ValueError("generated year count does not match horizon")
    if report["identity"]["content"]["span"] != [1, years]:
        raise ValueError("generated span does not match horizon")
    for group in ("par_convergence", "interannual", "covariation", "process"):
        if report[group] is None:
            raise ValueError(f"required generated group is null: {group}")
    process = report["process"]
    if process["qc_filter"] != qc:
        raise ValueError("process QC identity mismatch")
    if (qc == "off") != (process["counterfactual"] is not None):
        raise ValueError("counterfactual surface does not match QC policy")
    interannual = report["interannual"]
    if interannual["annual"]["precip_total_mm"]["n_years"] != years:
        raise ValueError("complete-year precipitation count mismatch")
    for variable in ("precip", "tmax", "tmin"):
        block = interannual["dependence"][f"{variable}_cross_month"]
        for field in ("covariance", "pearson_correlation", "n_pairs"):
            assert_matrix(block[field], f"{variable}.{field}")
    if len(report["tails"]["per_year"]) != years:
        raise ValueError("per-year tail count mismatch")
    if not all(year["complete_year"] for year in report["tails"]["per_year"]):
        raise ValueError("generated horizon contains an incomplete year")
    descriptors = report["tails"]["storm_descriptors"]
    if (
        descriptors["included_event_days"] + descriptors["excluded_event_days"]
        != descriptors["wet_event_days"]
    ):
        raise ValueError("storm descriptor count identity failed")


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def month_values(block: dict, path: list[str]) -> list[float]:
    values = []
    for month in (
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
    ):
        value = block[month]
        for component in path:
            value = value[component]
        if value is not None:
            values.append(value)
    return values


def par_relative_errors(group: dict) -> list[float]:
    values = []
    for parameter, months in group.items():
        if parameter == "observed_passthrough":
            continue
        for month in (
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
        ):
            value = months[month]["rel_err"]
            if value is not None:
                values.append(value)
    return values


def sum_months(months: dict) -> int:
    return sum(
        months[month]
        for month in (
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
    )


def metric_summary(report: dict) -> dict[str, float | int | None]:
    group_a = report["par_convergence"]
    interannual = report["interannual"]
    winter = report["covariation"]["winter_air_temperature_proxies"]
    structure = report["tails"]["precipitation_structure"]["r1mm"]
    descriptors = report["tails"]["storm_descriptors"]
    process = report["process"]
    rejected = sum(
        sum_months(parameter["rejected_attempts"]) for parameter in process["retries"]
    )
    accepted = sum(
        sum_months(parameter["accepted_batches"]) for parameter in process["retries"]
    )
    counterfactual = process["counterfactual"]
    return {
        "group_a_median_relative_error": median(par_relative_errors(group_a)),
        "group_b_annual_precipitation_sd_mm": interannual["annual"]["precip_total_mm"][
            "sd"
        ],
        "group_b_monthly_precipitation_sd_median_mm": median(
            month_values(interannual["monthly"], ["precip_total_mm", "sd"])
        ),
        "group_b_monthly_r1mm_count_sd_median": median(
            month_values(interannual["monthly"], ["r1mm_wet_day_count", "sd"])
        ),
        "group_b_monthly_tmax_sd_median_c": median(
            month_values(interannual["monthly"], ["tmax_mean_c", "sd"])
        ),
        "group_b_monthly_tmin_sd_median_c": median(
            month_values(interannual["monthly"], ["tmin_mean_c", "sd"])
        ),
        "group_b_annual_precipitation_low_frequency_fraction": interannual[
            "dependence"
        ]["annual"]["precip_total_mm"]["period_ge_4y_power_fraction"],
        "group_c_freezing_air_precipitation_fraction": winter[
            "precipitation_on_freezing_air_days"
        ]["fraction"],
        "group_c_freeze_thaw_proxy_cycles_mean": winter[
            "freeze_thaw_air_temperature_proxy_cycles"
        ]["mean"],
        "group_c_djf_r1mm_temperature_pearson": winter[
            "djf_r1mm_precip_mean_air_temperature"
        ]["pearson"],
        "group_d_r1mm_wet_spell_p95_days": structure["wet_spells_days"]["whole_run"][
            "p95"
        ],
        "group_d_r1mm_dry_spell_p95_days": structure["dry_spells_days"]["whole_run"][
            "p95"
        ],
        "group_d_r1mm_adjacent_amount_pearson": structure["adjacent_wet_day_amount"][
            "pearson"
        ],
        "group_d_annual_max_1_day_p95_mm": structure["annual_max_1_day_mm"]["p95"],
        "group_d_annual_max_3_day_p95_mm": structure["annual_max_3_day_mm"]["p95"],
        "group_d_annual_max_5_day_p95_mm": structure["annual_max_5_day_mm"]["p95"],
        "group_d_time_to_peak_mean_fraction": descriptors["distributions"][
            "time_to_peak_fraction"
        ]["mean"],
        "group_d_peak_intensity_ratio_mean": descriptors["distributions"][
            "peak_intensity_ratio"
        ]["mean"],
        "group_d_depth_duration_pearson": descriptors["dependence"]["depth_duration"][
            "pearson"
        ],
        "group_p_rejected_to_accepted_batch_ratio": (
            rejected / accepted if accepted else None
        ),
        "group_p_counterfactual_rejection_fraction": (
            counterfactual["would_reject"] / counterfactual["batches"]
            if counterfactual is not None and counterfactual["batches"]
            else None
        ),
    }


def numeric_inventory(value: object) -> dict[str, int]:
    counts = {"numeric_values": 0, "null_values": 0}

    def visit(node: object) -> None:
        if node is None:
            counts["null_values"] += 1
        elif isinstance(node, bool):
            return
        elif isinstance(node, (int, float)):
            counts["numeric_values"] += 1
        elif isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            for item in node.values():
                visit(item)

    visit(value)
    return counts


def runspec_text(par: Path, cli: Path, years: int, burn: int, qc: str) -> str:
    return "\n".join(
        [
            "cligen_runspec: 1",
            "station:",
            f"  par: {json.dumps(str(par))}",
            "mode: continuous",
            "simulation:",
            "  begin_year: 1",
            f"  years: {years}",
            "  interpolation: none",
            "rng:",
            f"  burn: {burn}",
            "generation_profile: faithful_5_32_3",
            f"qc_filter: {qc}",
            "output:",
            f"  cli: {json.dumps(str(cli))}",
            "  overwrite: true",
            "  quality: true",
            "",
        ]
    )


def execute_one(binary: Path, target: Path, job: dict) -> dict:
    stem = f"{job['station']}-{job['years']}yr-burn{job['burn']}-qc-{job['qc']}"
    cli = target / f"{stem}.cli"
    report_path = target / f"{stem}.cli.quality.json"
    provenance_path = target / f"{stem}.cli.provenance.json"
    runspec = target / f"{stem}.yaml"
    runspec.write_text(
        runspec_text(job["par"], cli, job["years"], job["burn"], job["qc"]),
        encoding="utf-8",
    )
    started = time.monotonic()
    result = subprocess.run(
        [str(binary), "run", str(runspec)],
        capture_output=True,
        text=True,
        check=False,
    )
    wall_seconds = time.monotonic() - started
    if result.returncode != 0:
        raise RuntimeError(f"{stem}: {result.stderr.strip()}")
    report = load_report(report_path)
    validate_report(report, job["years"], job["qc"])
    provenance = load_report(provenance_path)
    if report["identity"]["provenance"] != provenance:
        raise ValueError(f"{stem}: quality report provenance differs from sidecar")
    cli_sha256 = sha256(cli)
    if provenance["artifact"]["content_sha256"] != cli_sha256:
        raise ValueError(f"{stem}: provenance artifact hash differs from CLI")
    record = {
        "station": job["station"],
        "years": job["years"],
        "burn": job["burn"],
        "qc_filter": job["qc"],
        "wall_seconds": round(wall_seconds, 6),
        "cli_sha256": cli_sha256,
        "cli_bytes": cli.stat().st_size,
        "quality_report": f"{ARCHIVE_QUALITY_PREFIX}/{report_path.name}",
        "quality_report_sha256": sha256(report_path),
        "quality_report_bytes": report_path.stat().st_size,
        "provenance": f"{ARCHIVE_PROVENANCE_PREFIX}/{provenance_path.name}",
        "provenance_sha256": sha256(provenance_path),
        "provenance_bytes": provenance_path.stat().st_size,
        "metric_summary": metric_summary(report),
        "metric_inventory": {
            name: numeric_inventory(report[name])
            for name in (
                "par_convergence",
                "interannual",
                "covariation",
                "tails",
                "process",
            )
        },
    }
    cli.unlink()
    runspec.unlink()
    return record


def compression_identity() -> dict[str, object]:
    return {
        "implementation": "Python stdlib gzip.GzipFile + tarfile",
        "python_version": platform.python_version(),
        "zlib_compile_version": zlib.ZLIB_VERSION,
        "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        "gzip_compresslevel": GZIP_COMPRESSLEVEL,
        "gzip_mtime": FIXED_ARCHIVE_MTIME,
        "gzip_header_flags": 0,
        "gzip_header_extra_flags": 2,
        "gzip_header_os": 255,
        "tar_format": "ustar",
        "tar_member_mtime": FIXED_ARCHIVE_MTIME,
        "tar_member_uid": 0,
        "tar_member_gid": 0,
        "tar_member_mode": "0644",
        "member_order": "lexicographic",
    }


def evaluation_contract_identity() -> dict[str, object]:
    artifacts = {
        "evaluation_spec": EVALUATION_SPEC,
        "metric_manifest": GATE_METRICS,
        "metric_manifest_schema": GATE_METRICS_SCHEMA,
        "metric_manifest_verifier": GATE_METRICS_VERIFIER,
        "observed_bootstrap_reference": OBSERVED_BOOTSTRAP,
        "observed_bootstrap_golden": OBSERVED_BOOTSTRAP_GOLDEN,
        "wepp_response_schema": WEPP_RESPONSE_SCHEMA,
        "wepp_response_verifier": WEPP_RESPONSE_VERIFIER,
        "wepp_response_protocol": WEPP_RESPONSE_PROTOCOL,
    }
    return {
        name: {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }
        for name, path in artifacts.items()
    }


def static_evidence_identity() -> dict[str, object]:
    """Capture every mutable contract/input identity before execution."""

    return {
        "runner_sha256": sha256(Path(__file__)),
        "verifier_sha256": sha256(VERIFIER),
        "manifest_schema_sha256": sha256(MANIFEST_SCHEMA),
        "analysis_schema_sha256": sha256(ANALYSIS_SCHEMA),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "compression": compression_identity(),
        "implementation": implementation_identity(),
        "schemas": {
            "quality_report": {
                "path": str(QUALITY_SCHEMA.relative_to(ROOT)),
                "sha256": sha256(QUALITY_SCHEMA),
            },
            "provenance": {
                "path": str(PROVENANCE_SCHEMA.relative_to(ROOT)),
                "sha256": sha256(PROVENANCE_SCHEMA),
            },
        },
        "inputs": {
            "corpus_config_sha256": sha256(CORPUS_CONFIG),
            "observed_target_corpus_sha256": sha256(OBSERVED_TARGET),
            "preregistration_sha256": sha256(PREREGISTRATION),
            "evaluation_contract": evaluation_contract_identity(),
        },
    }


def assert_static_evidence_identity(expected: dict[str, object], phase: str) -> None:
    actual = static_evidence_identity()
    if actual == expected:
        return
    changed = sorted(
        key
        for key in expected.keys() | actual.keys()
        if expected.get(key) != actual.get(key)
    )
    raise RuntimeError(
        f"{phase}: static evidence identity changed during execution: {changed}"
    )


def assert_file_sha256(path: Path, expected: str, phase: str, label: str) -> None:
    if not path.is_file() or sha256(path) != expected:
        raise RuntimeError(f"{phase}: {label} changed during execution: {path}")


def assert_station_snapshots(
    station_records: list[dict], station_sources: dict[str, Path], phase: str
) -> None:
    for record in station_records:
        assert_file_sha256(
            station_sources[record["station"]],
            record["par_sha256"],
            phase,
            f"station snapshot {record['station']}",
        )


def evidence_sources(
    target: Path, records: list[dict], station_sources: dict[str, Path]
) -> list[tuple[str, Path]]:
    sources = []
    for record in records:
        sources.append(
            (record["quality_report"], target / Path(record["quality_report"]).name)
        )
        sources.append((record["provenance"], target / Path(record["provenance"]).name))
    for station, source in station_sources.items():
        sources.append((f"{ARCHIVE_PAR_PREFIX}/{station}.par", source))
    sources.sort(key=lambda item: item[0])
    names = [name for name, _ in sources]
    if len(names) != len(set(names)):
        raise ValueError("evidence archive member names are not unique")
    for name, source in sources:
        if not source.is_file():
            raise FileNotFoundError(
                f"archive member source is missing: {name}: {source}"
            )
    return sources


def write_evidence_archive(sources: list[tuple[str, Path]]) -> dict[str, object]:
    temporary = EVIDENCE_ARCHIVE.with_suffix(EVIDENCE_ARCHIVE.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                compresslevel=GZIP_COMPRESSLEVEL,
                fileobj=raw,
                mtime=FIXED_ARCHIVE_MTIME,
            ) as compressed:
                with tarfile.open(
                    fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT
                ) as archive:
                    for name, source in sources:
                        info = tarfile.TarInfo(name=name)
                        info.size = source.stat().st_size
                        info.mtime = FIXED_ARCHIVE_MTIME
                        info.mode = FIXED_ARCHIVE_MODE
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        with source.open("rb") as handle:
                            archive.addfile(info, handle)
        os.replace(temporary, EVIDENCE_ARCHIVE)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "path": EVIDENCE_ARCHIVE.name,
        "format": ARCHIVE_FORMAT,
        "sha256": sha256(EVIDENCE_ARCHIVE),
        "bytes": EVIDENCE_ARCHIVE.stat().st_size,
        "member_counts": {
            "quality_reports": 544,
            "provenance_documents": 544,
            "station_parameters": 17,
            "total": len(sources),
        },
    }


def remove_ephemeral_evidence_sources(
    target: Path, records: list[dict], snapshot: Path
) -> None:
    for record in records:
        (target / Path(record["quality_report"]).name).unlink()
        (target / Path(record["provenance"]).name).unlink()
    shutil.rmtree(snapshot)
    remaining = list(target.iterdir())
    if remaining:
        raise RuntimeError(
            "successful evidence publication left unexpected target files: "
            f"{remaining}"
        )


def nearest_rank(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(probability * len(ordered)) - 1)]


def empirical_summary(
    values: list[float], expected: int
) -> dict[str, float | int | None]:
    if not values:
        return {
            "n_available": 0,
            "n_expected": expected,
            "median": None,
            "p05": None,
            "p95": None,
            "minimum": None,
            "maximum": None,
        }
    return {
        "n_available": len(values),
        "n_expected": expected,
        "median": median(values),
        "p05": nearest_rank(values, 0.05),
        "p95": nearest_rank(values, 0.95),
        "minimum": min(values),
        "maximum": max(values),
    }


def build_analysis(records: list[dict]) -> dict:
    groups: dict[tuple[str, int, str], dict[str, list[float]]] = {}
    for record in records:
        key = (record["station"], record["years"], record["qc_filter"])
        metrics = groups.setdefault(key, {})
        for name, value in record["metric_summary"].items():
            if value is not None:
                metrics.setdefault(name, []).append(value)
    summaries = []
    metric_names = sorted(records[0]["metric_summary"])
    for (station, years, qc), metrics in sorted(groups.items()):
        summaries.append(
            {
                "station": station,
                "years": years,
                "qc_filter": qc,
                "metrics": {
                    name: empirical_summary(metrics.get(name, []), len(BURNS))
                    for name in metric_names
                },
            }
        )
    comparison = []
    indexed = {
        (row["station"], row["years"], row["qc_filter"]): row for row in summaries
    }
    stations = sorted({record["station"] for record in records})
    for station in stations:
        for years in HORIZONS:
            faithful = indexed[(station, years, "faithful")]
            off = indexed[(station, years, "off")]
            metric = "group_b_annual_precipitation_sd_mm"
            faithful_median = faithful["metrics"][metric]["median"]
            off_median = off["metrics"][metric]["median"]
            comparison.append(
                {
                    "station": station,
                    "years": years,
                    "faithful_to_off_median_sd_ratio": (
                        faithful_median / off_median if off_median else None
                    ),
                }
            )
    return {
        "baseline_analysis_schema_version": 1,
        "interpretation": (
            "Burns are deterministic trajectory offsets. Median is the conventional "
            "sample median (the arithmetic mean of the two center values for even n); "
            "p05/p95 are nearest-rank empirical across-burn spread, not confidence "
            "intervals."
        ),
        "run_count": len(records),
        "expected_run_count": 544,
        "matrix_complete": len(records) == 544,
        "metric_across_burns": summaries,
        "qc_context": comparison,
        "metric_inventory_totals": {
            group: {
                field: sum(
                    record["metric_inventory"][group][field] for record in records
                )
                for field in ("numeric_values", "null_values")
            }
            for group in (
                "par_convergence",
                "interannual",
                "covariation",
                "tails",
                "process",
            )
        },
    }


def main(binary_arg: str, cache_arg: str, target_arg: str) -> None:
    binary = Path(binary_arg).resolve()
    cache = Path(cache_arg).resolve(strict=True)
    target = Path(target_arg).resolve()
    if target != EXPECTED_EVIDENCE_TARGET.resolve():
        raise ValueError(
            "target directory must be the pinned A5a evidence directory: "
            f"{EXPECTED_EVIDENCE_TARGET}"
        )
    if target.exists() and any(target.iterdir()):
        raise ValueError(
            f"target directory must be empty to prevent stale evidence: {target}"
        )
    static_identity = static_evidence_identity()
    build = build_binary(binary)
    assert_static_evidence_identity(static_identity, "after pinned binary build")
    binary_sha256 = sha256(binary)
    target.mkdir(parents=True, exist_ok=True)
    snapshot = target / SNAPSHOT_DIRNAME
    snapshot_pars = snapshot / SNAPSHOT_STATION_DIRNAME
    snapshot_pars.mkdir(parents=True)
    snapshot_binary = snapshot / "cligen"
    shutil.copy2(binary, snapshot_binary)
    assert_file_sha256(
        snapshot_binary, binary_sha256, "before matrix", "immutable binary snapshot"
    )
    config = load_json(CORPUS_CONFIG)
    if not isinstance(config, dict):
        raise ValueError(f"corpus config is not an object: {CORPUS_CONFIG}")
    stations = config["stations"]
    jobs = []
    station_records = []
    station_sources = {}
    for station in stations:
        par = cache / f"{station['station_id']}.par"
        if not par.is_file():
            raise FileNotFoundError(par)
        actual_par_sha = sha256(par)
        if actual_par_sha != station["par_sha256"]:
            raise ValueError(f"{station['station_id']}: station .par hash mismatch")
        snapshot_par = snapshot_pars / par.name
        shutil.copy2(par, snapshot_par)
        assert_file_sha256(
            snapshot_par,
            actual_par_sha,
            "before matrix",
            f"station snapshot {station['station_id']}",
        )
        station_records.append(
            {
                "station": station["station_id"],
                "par_file": f"{ARCHIVE_PAR_PREFIX}/{station['station_id']}.par",
                "par_sha256": actual_par_sha,
                "par_bytes": snapshot_par.stat().st_size,
            }
        )
        station_sources[station["station_id"]] = snapshot_par
        for years in HORIZONS:
            for burn in BURNS:
                for qc in QC_POLICIES:
                    jobs.append(
                        {
                            "station": station["station_id"],
                            "par": snapshot_par,
                            "years": years,
                            "burn": burn,
                            "qc": qc,
                        }
                    )
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [
            executor.submit(execute_one, snapshot_binary, target, job) for job in jobs
        ]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            records.append(future.result())
            if completed % 16 == 0 or completed == len(jobs):
                print(f"completed {completed}/{len(jobs)}", flush=True)
    assert_static_evidence_identity(static_identity, "after matrix")
    assert_file_sha256(binary, binary_sha256, "after matrix", "built binary")
    assert_file_sha256(
        snapshot_binary,
        binary_sha256,
        "after matrix",
        "immutable binary snapshot",
    )
    assert_station_snapshots(station_records, station_sources, "after matrix")
    records.sort(
        key=lambda row: (
            row["station"],
            row["years"],
            row["burn"],
            row["qc_filter"],
        )
    )
    station_records.sort(key=lambda row: row["station"])
    sources = evidence_sources(target, records, station_sources)
    archive = write_evidence_archive(sources)
    assert_static_evidence_identity(static_identity, "after archive creation")
    assert_file_sha256(binary, binary_sha256, "after archive creation", "built binary")
    assert_file_sha256(
        snapshot_binary,
        binary_sha256,
        "after archive creation",
        "immutable binary snapshot",
    )
    assert_station_snapshots(station_records, station_sources, "after archive creation")
    manifest = {
        "baseline_run_manifest_schema_version": 1,
        "matrix": {
            "stations": len(stations),
            "horizons_years": HORIZONS,
            "burn_offsets": BURNS,
            "qc_filters": QC_POLICIES,
            "expected_runs": 544,
            "actual_runs": len(records),
        },
        "execution": {
            "parallel_workers": WORKERS,
            "binary_sha256": binary_sha256,
            "runner_sha256": static_identity["runner_sha256"],
            "verifier_sha256": static_identity["verifier_sha256"],
            "manifest_schema_sha256": static_identity["manifest_schema_sha256"],
            "analysis_schema_sha256": static_identity["analysis_schema_sha256"],
            "python_version": static_identity["python_version"],
            "platform": static_identity["platform"],
            "build": build,
            "compression": static_identity["compression"],
            "implementation": static_identity["implementation"],
        },
        "schemas": static_identity["schemas"],
        "inputs": {
            **static_identity["inputs"],
            "station_parameters": station_records,
        },
        "raw_output_policy": (
            "CLI streams are removed after hashing and are not archived. All 544 "
            "quality reports, all 544 provenance sidecars, and all 17 exact station "
            ".par files are committed in the deterministic evidence archive; "
            "ephemeral target-directory report and provenance copies are removed "
            "after archive verification."
        ),
        "archive": archive,
        "runs": records,
    }
    validate_instance(manifest, MANIFEST_SCHEMA)
    MANIFEST.write_text(
        json.dumps(manifest, allow_nan=False, indent=2) + "\n", encoding="utf-8"
    )
    analysis = build_analysis(records)
    analysis["baseline_run_manifest_sha256"] = sha256(MANIFEST)
    validate_instance(analysis, ANALYSIS_SCHEMA)
    ANALYSIS.write_text(
        json.dumps(analysis, allow_nan=False, indent=2) + "\n", encoding="utf-8"
    )
    assert_static_evidence_identity(static_identity, "before independent verification")
    subprocess.run([sys.executable, str(VERIFIER)], cwd=ROOT, check=True)
    assert_static_evidence_identity(static_identity, "after independent verification")
    assert_file_sha256(
        snapshot_binary,
        binary_sha256,
        "after independent verification",
        "immutable binary snapshot",
    )
    assert_station_snapshots(
        station_records, station_sources, "after independent verification"
    )
    remove_ephemeral_evidence_sources(target, records, snapshot)
    print(f"manifest {sha256(MANIFEST)} {MANIFEST}")
    print(f"analysis {sha256(ANALYSIS)} {ANALYSIS}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
