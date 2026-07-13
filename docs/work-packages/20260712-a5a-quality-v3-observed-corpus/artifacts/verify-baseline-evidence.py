#!/usr/bin/env python3
"""Verify the committed A5a baseline evidence without extracting the archive.

Usage:
  verify-baseline-evidence.py
  verify-baseline-evidence.py --self-test
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import sys
import tarfile

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
MANIFEST = PACKAGE / "baseline-run-manifest-v1.json"
ANALYSIS = PACKAGE / "baseline-analysis-v1.json"
MANIFEST_SCHEMA = PACKAGE / "baseline-run-manifest-v1.schema.json"
ANALYSIS_SCHEMA = PACKAGE / "baseline-analysis-v1.schema.json"
RUNNER = PACKAGE / "run-baseline-matrix.py"
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
CORPUS_CONFIG = PACKAGE / "corpus" / "corpus-config-v1.json"
OBSERVED_TARGET = PACKAGE / "corpus" / "observed-target-corpus-v1.json"
QUALITY_SCHEMA = ROOT / "docs" / "specifications" / "quality-report-s2-m3.schema.json"
PROVENANCE_SCHEMA = ROOT / "docs" / "specifications" / "provenance-v1.schema.json"
HORIZONS = [30, 100]
BURNS = [0, 17, 101, 503, 1009, 5003, 10007, 50021]
QC_POLICIES = ["faithful", "off"]
EXPECTED_RUNS = 544
EXPECTED_QUALITY_REPORTS = 544
EXPECTED_PROVENANCE_DOCUMENTS = 544
EXPECTED_STATION_PARAMETERS = 17
EXPECTED_MEMBERS = 1105
SNAPSHOT_DIRNAME = ".a5a-input-snapshot"
SNAPSHOT_STATION_DIRNAME = "stations"
SAFE_CARGO_RUST_ENV = {
    "CARGO_NET_OFFLINE",
    "RUST_BACKTRACE",
    "RUST_LIB_BACKTRACE",
    "RUST_LOG",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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


def parse_json(value: bytes | str, label: str) -> object:
    try:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(
            value,
            parse_constant=reject_nonfinite,
            parse_float=parse_finite_float,
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{label}: invalid strict JSON: {error}") from error


def load_json(path: Path) -> object:
    return parse_json(path.read_bytes(), str(path))


def validate_instance(value: object, schema: dict, label: str) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if errors:
        locations = []
        for error in errors[:5]:
            path = "/".join(str(part) for part in error.absolute_path) or "<root>"
            locations.append(f"{path}: {error.message}")
        raise ValueError(f"{label}: schema validation failed: {'; '.join(locations)}")


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


def lexical_normalize(path: Path) -> Path:
    """Normalize `.` and `..` without dereferencing a toolchain proxy symlink."""

    return Path(os.path.normpath(str(path)))


def verify_build_provenance(build: dict) -> None:
    environment = build["cargo_rust_environment"]
    unsafe = sorted(
        name
        for name in environment
        if name not in SAFE_CARGO_RUST_ENV and not name.startswith("CARGO_TERM_")
    )
    if unsafe:
        raise ValueError(
            f"build records compiler-affecting Cargo/Rust environment: {unsafe}"
        )
    configuration = build["cargo_configuration"]
    workspace_root = lexical_normalize(Path(configuration["workspace_root"]))
    cargo_home = lexical_normalize(Path(configuration["cargo_home"]))
    if not workspace_root.is_absolute() or not cargo_home.is_absolute():
        raise ValueError("recorded workspace root and Cargo home must be absolute")
    for field in ("cargo_executable", "rustc_executable"):
        executable = lexical_normalize(Path(build[field]))
        if not executable.is_absolute():
            raise ValueError(f"recorded {field} proxy path must be absolute")
        if executable.parent.parent != cargo_home:
            raise ValueError(
                f"recorded {field} proxy is not linked to recorded Cargo home"
            )
    candidates = set()
    for directory in (workspace_root, *workspace_root.parents):
        candidates.add(directory / ".cargo" / "config")
        candidates.add(directory / ".cargo" / "config.toml")
    candidates.add(cargo_home / "config")
    candidates.add(cargo_home / "config.toml")
    expected_paths = sorted(str(path) for path in candidates)
    if configuration["searched_config_paths"] != expected_paths:
        raise ValueError("Cargo configuration search closure is incomplete")
    if configuration["active_config_files"]:
        raise ValueError("evidence build used an unbound Cargo configuration file")
    if any(value is not None for value in build["build_environment"].values()):
        raise ValueError("evidence build records a forbidden compiler override")


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


def conventional_median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


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
        "median": conventional_median(values),
        "p05": nearest_rank(values, 0.05),
        "p95": nearest_rank(values, 0.95),
        "minimum": min(values),
        "maximum": max(values),
    }


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
        "group_a_median_relative_error": conventional_median(
            par_relative_errors(group_a)
        ),
        "group_b_annual_precipitation_sd_mm": interannual["annual"]["precip_total_mm"][
            "sd"
        ],
        "group_b_monthly_precipitation_sd_median_mm": conventional_median(
            month_values(interannual["monthly"], ["precip_total_mm", "sd"])
        ),
        "group_b_monthly_r1mm_count_sd_median": conventional_median(
            month_values(interannual["monthly"], ["r1mm_wet_day_count", "sd"])
        ),
        "group_b_monthly_tmax_sd_median_c": conventional_median(
            month_values(interannual["monthly"], ["tmax_mean_c", "sd"])
        ),
        "group_b_monthly_tmin_sd_median_c": conventional_median(
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


def expected_run_stem(record: dict) -> str:
    return (
        f"{record['station']}-{record['years']}yr-burn{record['burn']}-"
        f"qc-{record['qc_filter']}"
    )


def expected_run_keys(stations: list[str]) -> set[tuple[str, int, int, str]]:
    return {
        (station, years, burn, qc)
        for station in stations
        for years in HORIZONS
        for burn in BURNS
        for qc in QC_POLICIES
    }


def validate_matrix(manifest: dict) -> tuple[list[str], dict[str, dict]]:
    station_records = manifest["inputs"]["station_parameters"]
    stations = [record["station"] for record in station_records]
    if stations != sorted(stations) or len(stations) != len(set(stations)):
        raise ValueError("station parameter records must be unique and sorted")
    if len(stations) != EXPECTED_STATION_PARAMETERS:
        raise ValueError("station parameter record count mismatch")
    corpus_config = load_json(CORPUS_CONFIG)
    configured = {
        station["station_id"]: station["par_sha256"]
        for station in corpus_config["stations"]
    }
    archived = {record["station"]: record["par_sha256"] for record in station_records}
    if archived != configured:
        raise ValueError(
            "archived station set or .par hashes differ from corpus config"
        )
    expected = expected_run_keys(stations)
    runs = manifest["runs"]
    actual_order = [
        (run["station"], run["years"], run["burn"], run["qc_filter"]) for run in runs
    ]
    if actual_order != sorted(actual_order):
        raise ValueError("baseline runs are not in canonical key order")
    if len(actual_order) != len(set(actual_order)):
        raise ValueError("baseline run key is duplicated")
    if set(actual_order) != expected:
        missing = sorted(expected - set(actual_order))[:3]
        unexpected = sorted(set(actual_order) - expected)[:3]
        raise ValueError(
            f"baseline matrix mismatch; missing={missing}, unexpected={unexpected}"
        )
    matrix = manifest["matrix"]
    if matrix != {
        "stations": 17,
        "horizons_years": HORIZONS,
        "burn_offsets": BURNS,
        "qc_filters": QC_POLICIES,
        "expected_runs": EXPECTED_RUNS,
        "actual_runs": EXPECTED_RUNS,
    }:
        raise ValueError("manifest matrix declaration differs from the frozen matrix")
    return stations, {record["station"]: record for record in station_records}


def validate_safe_member_name(name: str) -> None:
    path = PurePosixPath(name)
    if (
        not name
        or name.startswith("/")
        or "\\" in name
        or any(part in ("", ".", "..") for part in path.parts)
        or str(path) != name
    ):
        raise ValueError(f"unsafe or non-canonical archive member name: {name!r}")


def validate_gzip_header(path: Path) -> None:
    with path.open("rb") as handle:
        header = handle.read(10)
    expected = bytes((0x1F, 0x8B, 8, 0, 0, 0, 0, 0, 2, 255))
    if header != expected:
        raise ValueError(
            f"evidence archive gzip header is not canonical: {header.hex()}"
        )


def expected_archive_bindings(
    manifest: dict, station_by_id: dict[str, dict]
) -> dict[str, tuple[str, str, int, dict | None]]:
    bindings = {}
    for run in manifest["runs"]:
        stem = expected_run_stem(run)
        quality_name = f"quality-reports/{stem}.cli.quality.json"
        provenance_name = f"provenance/{stem}.cli.provenance.json"
        if run["quality_report"] != quality_name:
            raise ValueError(f"{stem}: non-canonical quality report filename")
        if run["provenance"] != provenance_name:
            raise ValueError(f"{stem}: non-canonical provenance filename")
        for name, kind, digest, size in (
            (
                quality_name,
                "quality",
                run["quality_report_sha256"],
                run["quality_report_bytes"],
            ),
            (
                provenance_name,
                "provenance",
                run["provenance_sha256"],
                run["provenance_bytes"],
            ),
        ):
            if name in bindings:
                raise ValueError(f"duplicate manifest archive binding: {name}")
            bindings[name] = (kind, digest, size, run)
    for station, record in station_by_id.items():
        name = f"station-parameters/{station}.par"
        if record["par_file"] != name:
            raise ValueError(f"{station}: non-canonical station parameter filename")
        if name in bindings:
            raise ValueError(f"duplicate manifest archive binding: {name}")
        bindings[name] = (
            "par",
            record["par_sha256"],
            record["par_bytes"],
            None,
        )
    if len(bindings) != EXPECTED_MEMBERS:
        raise ValueError("manifest archive member binding count mismatch")
    return bindings


def quality_validator(quality_schema: dict, provenance_schema: dict):
    if quality_schema.get("$defs", {}).get("provenance") != {
        "$ref": "provenance-v1.schema.json"
    }:
        raise ValueError("quality schema provenance reference changed unexpectedly")
    inlined = copy.deepcopy(quality_schema)
    inlined["$defs"]["provenance"] = provenance_schema
    Draft202012Validator.check_schema(inlined)
    return Draft202012Validator(inlined)


def external_schema_refs(value: object) -> list[str]:
    refs = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str) and not child.startswith("#"):
                refs.append(child)
            else:
                refs.extend(external_schema_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(external_schema_refs(child))
    return refs


def validate_report_document(run: dict, report: dict, station: dict) -> None:
    stem = expected_run_stem(run)
    identity = report["identity"]
    content = identity["content"]
    if content["cli_sha256"] != run["cli_sha256"]:
        raise ValueError(f"{stem}: report CLI hash differs from run manifest")
    if content["station_source_sha256"] != station["par_sha256"]:
        raise ValueError(f"{stem}: report station hash differs from archived .par")
    if content["days"] != days_in_horizon(run["years"]):
        raise ValueError(f"{stem}: report day count differs from Gregorian horizon")
    if content["years"] != run["years"] or content["span"] != [1, run["years"]]:
        raise ValueError(f"{stem}: report year identity differs from run key")
    process = report["process"]
    if process["qc_filter"] != run["qc_filter"]:
        raise ValueError(f"{stem}: report process QC policy differs from run key")
    if (run["qc_filter"] == "off") != (process["counterfactual"] is not None):
        raise ValueError(
            f"{stem}: report counterfactual surface differs from QC policy"
        )
    interannual = report["interannual"]
    if interannual["annual"]["precip_total_mm"]["n_years"] != run["years"]:
        raise ValueError(f"{stem}: complete-year precipitation count mismatch")
    for variable in ("precip", "tmax", "tmin"):
        block = interannual["dependence"][f"{variable}_cross_month"]
        for field in ("covariance", "pearson_correlation", "n_pairs"):
            assert_matrix(block[field], f"{stem}: {variable}.{field}")
    if len(report["tails"]["per_year"]) != run["years"]:
        raise ValueError(f"{stem}: per-year tail count mismatch")
    if not all(year["complete_year"] for year in report["tails"]["per_year"]):
        raise ValueError(f"{stem}: generated horizon contains an incomplete year")
    descriptors = report["tails"]["storm_descriptors"]
    if (
        descriptors["included_event_days"] + descriptors["excluded_event_days"]
        != descriptors["wet_event_days"]
    ):
        raise ValueError(f"{stem}: storm descriptor count identity failed")
    if run["metric_summary"] != metric_summary(report):
        raise ValueError(f"{stem}: metric summary does not recompute from report")
    expected_inventory = {
        group: numeric_inventory(report[group])
        for group in (
            "par_convergence",
            "interannual",
            "covariation",
            "tails",
            "process",
        )
    }
    if run["metric_inventory"] != expected_inventory:
        raise ValueError(f"{stem}: metric inventory does not recompute from report")


def declaration_ordered_compact_sha256(value: object) -> str:
    """Hash the UTF-8 compact JSON order used by the provenance v1 structs."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return bytes_sha256(encoded)


def validate_provenance_document(
    run: dict, provenance: dict, station: dict, workspace_root: Path
) -> None:
    stem = expected_run_stem(run)
    if provenance["artifact"]["content_sha256"] != run["cli_sha256"]:
        raise ValueError(f"{stem}: provenance CLI hash differs from run manifest")
    if provenance["station"]["input_sha256"] != station["par_sha256"]:
        raise ValueError(f"{stem}: provenance station hash differs from archived .par")
    expected_generation = {
        "profile": "faithful_5_32_3",
        "qc_policy": run["qc_filter"],
        "mode": "continuous",
        "interpolation": "none",
        "rng_scheme": "cligen_randn_5_32_3",
        "burn_per_stream": run["burn"],
    }
    if provenance["generation"] != expected_generation:
        raise ValueError(f"{stem}: generation identity differs from frozen baseline")
    runspec = provenance["effective_runspec"]
    cli_path = Path(runspec["output"]["cli_lexical_path"])
    if not cli_path.is_absolute():
        raise ValueError(f"{stem}: output CLI lexical path is not absolute")
    expected_target = workspace_root / "target" / "a5a-baseline-v1"
    if cli_path.parent != expected_target:
        raise ValueError(f"{stem}: output CLI parent is not the pinned evidence target")
    expected_cli_path = expected_target / f"{stem}.cli"
    expected_station_path = (
        expected_target
        / SNAPSHOT_DIRNAME
        / SNAPSHOT_STATION_DIRNAME
        / f"{run['station']}.par"
    )
    expected_runspec = {
        "cligen_runspec": 1,
        "station": {
            "selector": "par",
            "lexical_path": str(expected_station_path),
            "input_sha256": station["par_sha256"],
        },
        "mode": "continuous",
        "begin_year": 1,
        "years": run["years"],
        "interpolation": "none",
        "burn": run["burn"],
        "generation_profile": "faithful_5_32_3",
        "qc_filter": run["qc_filter"],
        "observed": None,
        "storm": None,
        "output": {
            "cli_lexical_path": str(expected_cli_path),
            "parquet_lexical_path": None,
            "quality": True,
            "overwrite": True,
            "command_echo": (
                (f"-r{run['burn']} " if run["burn"] else "")
                + f"-i{expected_station_path} -o{expected_cli_path}"
                + (" --qc-filter off" if run["qc_filter"] == "off" else "")
            ),
        },
    }
    if runspec != expected_runspec:
        raise ValueError(f"{stem}: effective runspec differs from frozen baseline")
    expected_runspec_sha256 = declaration_ordered_compact_sha256(expected_runspec)
    if provenance["effective_runspec_sha256"] != expected_runspec_sha256:
        raise ValueError(f"{stem}: effective runspec SHA-256 does not recompute")
    expected_actual = {
        "emitted_day_count": days_in_horizon(run["years"]),
        "first_date": {"year": 1, "month": 1, "day": 1},
        "last_date": {"year": run["years"], "month": 12, "day": 31},
        "coverage": "complete_run",
    }
    if provenance["actual"] != expected_actual:
        raise ValueError(f"{stem}: actual output span differs from frozen baseline")


def verify_archive(
    manifest: dict,
    station_by_id: dict[str, dict],
    quality_schema: dict,
    provenance_schema: dict,
) -> None:
    workspace_root = lexical_normalize(
        Path(manifest["execution"]["build"]["cargo_configuration"]["workspace_root"])
    )
    archive_record = manifest["archive"]
    archive_path = PACKAGE / archive_record["path"]
    if archive_path.stat().st_size != archive_record["bytes"]:
        raise ValueError("evidence archive byte count mismatch")
    if sha256(archive_path) != archive_record["sha256"]:
        raise ValueError("evidence archive SHA-256 mismatch")
    validate_gzip_header(archive_path)
    bindings = expected_archive_bindings(manifest, station_by_id)
    report_validator = quality_validator(quality_schema, provenance_schema)
    provenance_validator = Draft202012Validator(provenance_schema)
    provenance_pairs: dict[tuple[str, int, int, str], dict[str, dict]] = {}
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            raise ValueError("evidence archive contains duplicate member names")
        if names != sorted(names):
            raise ValueError(
                "evidence archive members are not lexicographically sorted"
            )
        for name in names:
            validate_safe_member_name(name)
        actual = set(names)
        expected = set(bindings)
        if actual != expected:
            missing = sorted(expected - actual)[:3]
            unexpected = sorted(actual - expected)[:3]
            raise ValueError(
                f"evidence archive member mismatch; missing={missing}, "
                f"unexpected={unexpected}"
            )
        for member in members:
            if not member.isfile():
                raise ValueError(f"archive member is not a regular file: {member.name}")
            archive.fileobj.seek(member.offset)
            raw_header = archive.fileobj.read(512)
            if len(raw_header) != 512 or raw_header[257:263] != b"ustar\0":
                raise ValueError(
                    f"archive member is not encoded as ustar: {member.name}"
                )
            if (
                member.mtime != 0
                or member.mode != 0o644
                or member.uid != 0
                or member.gid != 0
                or member.uname != ""
                or member.gname != ""
            ):
                raise ValueError(f"archive metadata is not canonical: {member.name}")
            kind, expected_hash, expected_size, run = bindings[member.name]
            if member.size != expected_size:
                raise ValueError(f"archive member size mismatch: {member.name}")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError(f"archive member cannot be read: {member.name}")
            value = handle.read()
            if len(value) != expected_size or bytes_sha256(value) != expected_hash:
                raise ValueError(f"archive member content mismatch: {member.name}")
            if kind == "par":
                continue
            document = parse_json(value, member.name)
            if not isinstance(document, dict):
                raise ValueError(f"archive JSON member is not an object: {member.name}")
            key = (run["station"], run["years"], run["burn"], run["qc_filter"])
            pair = provenance_pairs.setdefault(key, {})
            if kind == "quality":
                errors = list(report_validator.iter_errors(document))
                if errors:
                    raise ValueError(
                        f"{member.name}: quality schema validation failed: "
                        f"{errors[0].message}"
                    )
                validate_report_document(run, document, station_by_id[run["station"]])
                pair["embedded"] = document["identity"]["provenance"]
            else:
                errors = list(provenance_validator.iter_errors(document))
                if errors:
                    raise ValueError(
                        f"{member.name}: provenance schema validation failed: "
                        f"{errors[0].message}"
                    )
                validate_provenance_document(
                    run,
                    document,
                    station_by_id[run["station"]],
                    workspace_root,
                )
                pair["sidecar"] = document
    if len(provenance_pairs) != EXPECTED_RUNS:
        raise ValueError("archive JSON document pair count mismatch")
    for run in manifest["runs"]:
        key = (run["station"], run["years"], run["burn"], run["qc_filter"])
        pair = provenance_pairs[key]
        if set(pair) != {"embedded", "sidecar"}:
            raise ValueError(
                f"run does not have one report and one provenance sidecar: {key}"
            )
        if pair["embedded"] != pair["sidecar"]:
            raise ValueError(f"report provenance does not equal sidecar: {key}")
    counts = {
        "quality_reports": sum(name.startswith("quality-reports/") for name in names),
        "provenance_documents": sum(name.startswith("provenance/") for name in names),
        "station_parameters": sum(
            name.startswith("station-parameters/") for name in names
        ),
        "total": len(names),
    }
    if counts != archive_record["member_counts"]:
        raise ValueError("archive member counts differ from manifest")


def expected_analysis(manifest: dict) -> dict:
    records = manifest["runs"]
    groups: dict[tuple[str, int, str], dict[str, list[float]]] = {}
    for record in records:
        key = (record["station"], record["years"], record["qc_filter"])
        metrics = groups.setdefault(key, {})
        for name, value in record["metric_summary"].items():
            if value is not None:
                metrics.setdefault(name, []).append(value)
    metric_names = sorted(records[0]["metric_summary"])
    if any(set(record["metric_summary"]) != set(metric_names) for record in records):
        raise ValueError("run metric-summary names are inconsistent")
    summaries = []
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
    indexed = {
        (row["station"], row["years"], row["qc_filter"]): row for row in summaries
    }
    comparison = []
    for station in sorted({record["station"] for record in records}):
        for years in HORIZONS:
            metric = "group_b_annual_precipitation_sd_mm"
            faithful = indexed[(station, years, "faithful")]["metrics"][metric][
                "median"
            ]
            off = indexed[(station, years, "off")]["metrics"][metric]["median"]
            comparison.append(
                {
                    "station": station,
                    "years": years,
                    "faithful_to_off_median_sd_ratio": faithful / off if off else None,
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
        "expected_run_count": EXPECTED_RUNS,
        "matrix_complete": len(records) == EXPECTED_RUNS,
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


def verify_static_bindings(manifest: dict, manifest_schema: dict) -> None:
    execution = manifest["execution"]
    verify_build_provenance(execution["build"])
    expected_hashes = {
        "runner_sha256": sha256(RUNNER),
        "verifier_sha256": sha256(Path(__file__)),
        "manifest_schema_sha256": sha256(MANIFEST_SCHEMA),
        "analysis_schema_sha256": sha256(ANALYSIS_SCHEMA),
    }
    for field, expected in expected_hashes.items():
        if execution[field] != expected:
            raise ValueError(f"execution binding mismatch: {field}")
    if execution["implementation"] != implementation_identity():
        raise ValueError("implementation source identity differs from current checkout")
    if manifest["schemas"] != {
        "quality_report": {
            "path": str(QUALITY_SCHEMA.relative_to(ROOT)),
            "sha256": sha256(QUALITY_SCHEMA),
        },
        "provenance": {
            "path": str(PROVENANCE_SCHEMA.relative_to(ROOT)),
            "sha256": sha256(PROVENANCE_SCHEMA),
        },
    }:
        raise ValueError("public report/provenance schema binding mismatch")
    inputs = manifest["inputs"]
    expected_inputs = {
        "corpus_config_sha256": sha256(CORPUS_CONFIG),
        "observed_target_corpus_sha256": sha256(OBSERVED_TARGET),
        "preregistration_sha256": sha256(PREREGISTRATION),
        "evaluation_contract": evaluation_contract_identity(),
    }
    for field, expected in expected_inputs.items():
        if inputs[field] != expected:
            raise ValueError(f"input binding mismatch: {field}")
    Draft202012Validator.check_schema(manifest_schema)


def verify() -> None:
    manifest_schema = load_json(MANIFEST_SCHEMA)
    analysis_schema = load_json(ANALYSIS_SCHEMA)
    quality_schema = load_json(QUALITY_SCHEMA)
    provenance_schema = load_json(PROVENANCE_SCHEMA)
    for label, schema in (
        ("manifest schema", manifest_schema),
        ("analysis schema", analysis_schema),
        ("quality schema", quality_schema),
        ("provenance schema", provenance_schema),
    ):
        if not isinstance(schema, dict):
            raise ValueError(f"{label} is not a JSON object")
        Draft202012Validator.check_schema(schema)
    manifest = load_json(MANIFEST)
    analysis = load_json(ANALYSIS)
    if not isinstance(manifest, dict) or not isinstance(analysis, dict):
        raise ValueError("manifest and analysis must be JSON objects")
    validate_instance(manifest, manifest_schema, "baseline manifest")
    validate_instance(analysis, analysis_schema, "baseline analysis")
    verify_static_bindings(manifest, manifest_schema)
    _, station_by_id = validate_matrix(manifest)
    verify_archive(manifest, station_by_id, quality_schema, provenance_schema)
    expected = expected_analysis(manifest)
    expected["baseline_run_manifest_sha256"] = sha256(MANIFEST)
    if analysis != expected:
        raise ValueError(
            "baseline analysis does not exactly recompute from the manifest"
        )
    print(
        "A5a baseline evidence: manifest/analysis schemas pass; 544-run matrix is "
        "complete; 1,105 canonical archive members hash, validate, and agree "
        "semantically"
    )


def provenance_semantic_self_test() -> None:
    run = {
        "station": "id106388",
        "years": 30,
        "burn": 17,
        "qc_filter": "off",
        "cli_sha256": "0" * 64,
    }
    station = {"par_sha256": "1" * 64}
    workspace_root = Path("/tmp/cligen-a5a-baseline-self-test")
    target = workspace_root / "target" / "a5a-baseline-v1"
    cli_path = target / f"{expected_run_stem(run)}.cli"
    station_path = target / SNAPSHOT_DIRNAME / SNAPSHOT_STATION_DIRNAME / "id106388.par"
    runspec = {
        "cligen_runspec": 1,
        "station": {
            "selector": "par",
            "lexical_path": str(station_path),
            "input_sha256": station["par_sha256"],
        },
        "mode": "continuous",
        "begin_year": 1,
        "years": 30,
        "interpolation": "none",
        "burn": 17,
        "generation_profile": "faithful_5_32_3",
        "qc_filter": "off",
        "observed": None,
        "storm": None,
        "output": {
            "cli_lexical_path": str(cli_path),
            "parquet_lexical_path": None,
            "quality": True,
            "overwrite": True,
            "command_echo": (f"-r17 -i{station_path} -o{cli_path} --qc-filter off"),
        },
    }
    runspec_sha256 = declaration_ordered_compact_sha256(runspec)
    if (
        runspec_sha256
        != "1b0ca87b5808ceb4139466a14ff5b32d4423fb91914cfd79d3b5a0be5f2affab"
    ):
        raise AssertionError(
            "effective-runspec compact-JSON golden hash drifted: " f"{runspec_sha256}"
        )
    provenance = {
        "artifact": {"content_sha256": run["cli_sha256"]},
        "station": {"input_sha256": station["par_sha256"]},
        "generation": {
            "profile": "faithful_5_32_3",
            "qc_policy": "off",
            "mode": "continuous",
            "interpolation": "none",
            "rng_scheme": "cligen_randn_5_32_3",
            "burn_per_stream": 17,
        },
        "effective_runspec": runspec,
        "effective_runspec_sha256": runspec_sha256,
        "actual": {
            "emitted_day_count": days_in_horizon(30),
            "first_date": {"year": 1, "month": 1, "day": 1},
            "last_date": {"year": 30, "month": 12, "day": 31},
            "coverage": "complete_run",
        },
    }
    validate_provenance_document(run, provenance, station, workspace_root)
    negatives = []
    wrong_runspec = copy.deepcopy(provenance)
    wrong_runspec["effective_runspec"]["begin_year"] = 2
    wrong_runspec["effective_runspec"]["interpolation"] = "linear"
    wrong_runspec["generation"]["interpolation"] = "linear"
    wrong_runspec["effective_runspec_sha256"] = declaration_ordered_compact_sha256(
        wrong_runspec["effective_runspec"]
    )
    negatives.append(("changed begin/interpolation", wrong_runspec))
    stale_hash = copy.deepcopy(provenance)
    stale_hash["effective_runspec_sha256"] = "0" * 64
    negatives.append(("stale effective-runspec hash", stale_hash))
    wrong_actual = copy.deepcopy(provenance)
    wrong_actual["actual"]["coverage"] = "observed_source_end"
    negatives.append(("changed actual coverage", wrong_actual))
    wrong_target = copy.deepcopy(provenance)
    wrong_target["effective_runspec"]["output"]["cli_lexical_path"] = str(
        workspace_root / "other" / f"{expected_run_stem(run)}.cli"
    )
    negatives.append(("unlinked output target", wrong_target))
    wrong_station_path = copy.deepcopy(provenance)
    wrong_station_path["effective_runspec"]["station"]["lexical_path"] = str(
        target / SNAPSHOT_DIRNAME / "station-parameters" / "id106388.par"
    )
    negatives.append(("unlinked station snapshot", wrong_station_path))
    for label, value in negatives:
        try:
            validate_provenance_document(run, value, station, workspace_root)
        except ValueError:
            pass
        else:
            raise AssertionError(f"provenance semantic negative passed: {label}")


def report_semantic_self_test() -> None:
    manifest = load_json(MANIFEST)
    if not isinstance(manifest, dict):
        raise AssertionError("baseline manifest is not an object")
    run = manifest["runs"][0]
    station = next(
        row
        for row in manifest["inputs"]["station_parameters"]
        if row["station"] == run["station"]
    )
    archive_path = PACKAGE / manifest["archive"]["path"]
    with tarfile.open(archive_path, mode="r:gz") as archive:
        member = archive.getmember(run["quality_report"])
        extracted = archive.extractfile(member)
        if extracted is None:
            raise AssertionError("quality-report self-test member is unreadable")
        report = parse_json(extracted.read(), run["quality_report"])
    if not isinstance(report, dict):
        raise AssertionError("quality-report self-test member is not an object")
    validate_report_document(run, report, station)
    incomplete = copy.deepcopy(report)
    incomplete["tails"]["per_year"][0]["complete_year"] = False
    try:
        validate_report_document(run, incomplete, station)
    except ValueError as error:
        if "incomplete year" not in str(error):
            raise AssertionError(
                "report semantic mutation failed at the wrong assertion"
            ) from error
    else:
        raise AssertionError("incomplete generated year passed report verification")


def build_provenance_self_test() -> None:
    workspace_root = Path("/repo")
    cargo_home = Path("/home/evidence/.cargo")
    candidates = set()
    for directory in (workspace_root, *workspace_root.parents):
        candidates.add(directory / ".cargo" / "config")
        candidates.add(directory / ".cargo" / "config.toml")
    candidates.add(cargo_home / "config")
    candidates.add(cargo_home / "config.toml")
    build = {
        "cargo_rust_environment": {"RUST_LOG": "warn"},
        "cargo_executable": str(cargo_home / "bin" / ".." / "bin" / "cargo"),
        "rustc_executable": str(cargo_home / "bin" / "rustc"),
        "cargo_configuration": {
            "workspace_root": str(workspace_root),
            "cargo_home": str(cargo_home),
            "searched_config_paths": sorted(str(path) for path in candidates),
            "active_config_files": [],
        },
        "build_environment": {"RUSTFLAGS": None},
    }
    verify_build_provenance(build)
    negatives = []
    unsafe_environment = copy.deepcopy(build)
    unsafe_environment["cargo_rust_environment"][
        "CARGO_BUILD_RUSTFLAGS"
    ] = "-Cllvm-args=changed"
    negatives.append(("unsafe Cargo environment", unsafe_environment))
    incomplete_search = copy.deepcopy(build)
    incomplete_search["cargo_configuration"]["searched_config_paths"].pop()
    negatives.append(("incomplete Cargo config search", incomplete_search))
    unlinked_proxy = copy.deepcopy(build)
    unlinked_proxy["cargo_executable"] = "/opt/toolchain/bin/cargo"
    negatives.append(("unlinked Cargo proxy", unlinked_proxy))
    for label, value in negatives:
        try:
            verify_build_provenance(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"build-provenance negative passed: {label}")


def self_test() -> None:
    if conventional_median([4.0, 1.0, 3.0, 2.0]) != 2.5:
        raise AssertionError("even-sample conventional median self-test failed")
    if conventional_median([3.0, 1.0, 2.0]) != 2.0:
        raise AssertionError("odd-sample conventional median self-test failed")
    if nearest_rank(list(range(1, 9)), 0.05) != 1:
        raise AssertionError("p05 nearest-rank self-test failed")
    if nearest_rank(list(range(1, 9)), 0.95) != 8:
        raise AssertionError("p95 nearest-rank self-test failed")
    try:
        parse_json('{"a": 1, "a": 2}', "duplicate-key negative vector")
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate JSON object key was accepted")
    for overflowing in ("1e400", "-1e400"):
        try:
            parse_json(overflowing, "binary64-overflow negative vector")
        except ValueError:
            pass
        else:
            raise AssertionError(f"overflowing JSON number was accepted: {overflowing}")
    for unsafe in ("", "/absolute", "../escape", "a/../escape", "a\\b", "./a"):
        try:
            validate_safe_member_name(unsafe)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe archive name was accepted: {unsafe!r}")
    validate_safe_member_name("quality-reports/station.cli.quality.json")
    quality_schema = load_json(QUALITY_SCHEMA)
    provenance_schema = load_json(PROVENANCE_SCHEMA)
    validator = quality_validator(quality_schema, provenance_schema)
    refs = external_schema_refs(validator.schema)
    if refs:
        raise AssertionError(f"quality validator retained external references: {refs}")
    embedded_validator = Draft202012Validator(validator.schema["$defs"]["provenance"])
    if not list(embedded_validator.iter_errors({"provenance_schema_version": 1})):
        raise AssertionError("inlined provenance-schema negative vector was accepted")
    provenance_semantic_self_test()
    report_semantic_self_test()
    build_provenance_self_test()
    print("A5a baseline evidence verifier self-tests pass")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif sys.argv[1:]:
        raise SystemExit(__doc__)
    else:
        verify()
