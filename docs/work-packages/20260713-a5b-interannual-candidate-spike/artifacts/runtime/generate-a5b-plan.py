#!/usr/bin/env python3
"""Generate one deterministic A5b 128-year annual-state overlay plan.

Usage:
  generate-a5b-plan.py <station-bundle.json> <candidate-id> \
      <0x-extension-seed> <output-plan.json>
  generate-a5b-plan.py --self-test

The generator is deliberately separate from the faithful CLIGEN RNG.  It
validates the complete seven-extension station bundle before selecting one
payload, derives a model/station-specific SplitMix64 state through SHA-256,
and refuses to replace an existing plan.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Callable

import numpy as np


sys.dont_write_bytecode = True

FIXED_YEARS = 128
VAR_WARMUP_YEARS = 256
MASK64 = (1 << 64) - 1
PRECIP_FACTOR_MIN = 0.05
PRECIP_FACTOR_MAX = 20.0
PRECIP_FACTOR_TARGET_SUM = float(FIXED_YEARS)
MAIN_DOMAIN = b"cligen-a5b-extension-v1\0"
COUNTERFACTUAL_DOMAIN = b"cligen-a5b-counterfactual-v1\0"

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
FEATURE_ORDER = tuple(
    [f"prcp_log1p_total_mm_{month}" for month in MONTH_NAMES]
    + [f"tmax_mean_deg_c_{month}" for month in MONTH_NAMES]
    + [f"tmin_mean_deg_c_{month}" for month in MONTH_NAMES]
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
    (
        "fourier_eof",
        "interannual_fourier_eof_v1",
        "a5b_fourier_eof_v1",
    ),
    (
        "vector_ar",
        "interannual_fourier_eof_var1_v1",
        "a5b_vector_ar_v1",
    ),
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
CANDIDATE_INDEX = {candidate[0]: index for index, candidate in enumerate(CANDIDATES)}

ROOT_KEYS = {
    "station_schema_version",
    "station_document_role",
    "station_id",
    "base_station",
    "source_lineage",
    "fit_contract",
    "extensions",
}
SOURCE_KEYS = {
    "source_snapshot_id",
    "product",
    "product_version",
    "doi",
    "retrieval_date",
    "archive_path",
    "archive_sha256",
    "decompressed_sha256",
    "requested_location",
    "returned_grid",
    "header",
    "variables",
    "fit_period",
    "heldout_excluded_after",
    "calendar_transform",
}
FIT_KEYS = {
    "coefficient_payload_schema",
    "fit_recipe_id",
    "implementation_base_commit",
    "fitter_sha256",
    "python_version",
    "numpy_version",
    "scipy_version",
    "feature_order",
    "precipitation_transform",
    "temperature_transform",
    "detrending",
    "usable_years",
    "fit_seed",
}
EXTENSION_KEYS = {
    "candidate_id",
    "station_model",
    "generation_profile",
    "coefficient_payload_schema_version",
    "fit_recipe_id",
    "fit_identity_sha256",
    "runtime_parameter_count",
    "payload",
    "diagnostics",
}
DIAGNOSTIC_REQUIRED_KEYS = {
    "fit_status",
    "warnings",
    "interventions",
    "serialized_numeric_count",
    "payload_sha256",
}
DIAGNOSTIC_OPTIONAL_KEYS = {
    "retained_rank",
    "explained_variance_fraction",
    "reconstruction_rmse",
    "minimum_eigenvalue",
    "maximum_eigenvalue",
    "em_iterations",
    "em_log_likelihood",
    "em_penalized_objective",
}

# These hashes pin the complete 128-state arrays produced from the synthetic
# bundle in _synthetic_bundle(), not merely a few PRNG draws.
SELF_TEST_STATE_HASHES = {
    "rank_one_monthly_sd": "714392d1b4cbc8387db1dc1ec94cf5b44f86a2edc86f693d02ed5857daaf5aed",
    "full_monthly_covariance": "4dd36df72d80c733ca43079a26889512fa1e1ea87cb6ce0fe56123cb6e47bad8",
    "fourier_eof": "b45f9803a467459cabedff383b2e9bdfef03cd69e3c288f1dc4e7937f6108f89",
    "vector_ar": "7970a5ede946c5bdd69dc646ca7eb1c88abc76d30dfa241baf1926c266774be2",
    "gaussian_hmm": "7a7f6044b77c9b718cc29a405b0beadc82ca5b8c4d57279c02dadaf971ee29ce",
    "spectral_random_phase": "e83a7de2c9ce3cdbb174b2ddf7c946f9e9ca51457410217fcdee62a2cdfff9e4",
    "precip_counterfactual": "16ded36979cf22627d6d891a497c001bbe662a1290ed8f6d52e4384f0ccfe422",
}
SELF_TEST_COUNTERFACTUAL_RNG_STATE = "0x5e80f89a9a5053ff"


class PlanError(RuntimeError):
    """A fail-closed station-bundle, sampler, or output violation."""


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PlanError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def reject_constant(token: str) -> None:
    raise PlanError(f"nonfinite JSON token is forbidden: {token}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise PlanError(f"nonfinite JSON number is forbidden: {token}")
    return value


def load_json_strict_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_constant,
            parse_float=parse_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PlanError(f"cannot parse {label}: {error}") from error


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PlanError(f"{label} must be an object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise PlanError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def require_integer(value: Any, label: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlanError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise PlanError(f"{label} must be at least {minimum}")
    return value


def require_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PlanError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise PlanError(f"{label} must be finite")
    return result


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PlanError(f"{label} must be a nonempty string")
    return value


def require_sha256(value: Any, label: str) -> str:
    text = require_string(value, label)
    if re.fullmatch(r"[0-9a-f]{64}", text) is None:
        raise PlanError(f"{label} must be 64 lowercase hexadecimal digits")
    return text


def require_git_commit(value: Any, label: str) -> str:
    text = require_string(value, label)
    if re.fullmatch(r"[0-9a-f]{40}", text) is None:
        raise PlanError(f"{label} must be 40 lowercase hexadecimal digits")
    return text


def require_vector(
    value: Any,
    length: int,
    label: str,
    predicate: Callable[[float], bool] | None = None,
) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise PlanError(f"{label} must contain exactly {length} numbers")
    result = [require_number(item, f"{label}[{index}]") for index, item in enumerate(value)]
    if predicate is not None:
        for index, item in enumerate(result):
            if not predicate(item):
                raise PlanError(f"{label}[{index}] is outside its semantic domain")
    return result


def require_matrix(
    value: Any,
    rows: int,
    columns: int,
    label: str,
    predicate: Callable[[float], bool] | None = None,
) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise PlanError(f"{label} must contain exactly {rows} rows")
    return [
        require_vector(row, columns, f"{label}[{index}]", predicate)
        for index, row in enumerate(value)
    ]


def require_compact_lower(value: Any, size: int, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != size:
        raise PlanError(f"{label} must contain exactly {size} compact lower rows")
    result: list[list[float]] = []
    for row_index, row in enumerate(value):
        parsed = require_vector(row, row_index + 1, f"{label}[{row_index}]")
        if parsed[-1] <= 0.0:
            raise PlanError(f"{label}[{row_index}] diagonal must be positive")
        result.append(parsed)
    return result


def numeric_count(value: Any) -> int:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return 0
    if isinstance(value, (int, float)):
        require_number(value, "numeric inventory value")
        return 1
    if isinstance(value, list):
        return sum(numeric_count(item) for item in value)
    if isinstance(value, dict):
        return sum(numeric_count(item) for item in value.values())
    raise PlanError(f"cannot inventory numeric type {type(value).__name__}")


def payload_json_bytes(value: Any) -> bytes:
    """Match the fitter's revision-1 payload identity encoding."""
    try:
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
    except (TypeError, ValueError) as error:
        raise PlanError(f"cannot canonicalize coefficient payload: {error}") from error


def canonical_state_bytes(annual_states: list[dict[str, Any]]) -> bytes:
    try:
        return json.dumps(
            annual_states,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PlanError(f"cannot canonicalize annual state table: {error}") from error


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_base_station(value: Any) -> None:
    station = require_dict(value, "base_station")
    require_exact_keys(
        station,
        {"station_schema_version", "station_model", "units", "lineage", "parameters"},
        "base_station",
    )
    if station["station_schema_version"] != 1:
        raise PlanError("base_station.station_schema_version must equal 1")
    if station["station_model"] != "fixed_monthly_5_32_3":
        raise PlanError("base_station.station_model must be fixed_monthly_5_32_3")
    validate_base_units(station["units"])
    lineage = require_dict(station["lineage"], "base_station.lineage")
    require_exact_keys(
        lineage,
        {"source_format", "source_sha256", "adapter", "adapter_version"},
        "base_station.lineage",
    )
    if (
        lineage["source_format"] != "cligen_par_5_32_3"
        or lineage["adapter"] != "cligen_rs_legacy_par_to_fixed_monthly"
        or lineage["adapter_version"] != 1
    ):
        raise PlanError("base_station.lineage identity differs from revision 1")
    require_sha256(lineage["source_sha256"], "base_station.lineage.source_sha256")
    validate_base_parameters(station["parameters"])


def validate_base_units(value: Any) -> None:
    expected = {
        "latitude": "degree_north",
        "longitude": "degree_east",
        "elevation": "foot",
        "record_length": "year",
        "precipitation_depth": "inch",
        "precipitation_intensity": "inch_per_hour",
        "temperature": "degree_fahrenheit",
        "solar_radiation": "langley_per_day",
        "wind_speed": "meter_per_second",
        "frequency": "percent",
        "probability": "fraction",
        "interpolation_weight": "dimensionless",
        "skew": "dimensionless",
    }
    units = require_dict(value, "base_station.units")
    require_exact_keys(units, set(expected), "base_station.units")
    if units != expected:
        raise PlanError("base_station.units differs from station-document revision 1")


def validate_base_parameters(value: Any) -> None:
    parameters = require_dict(value, "base_station.parameters")
    require_exact_keys(
        parameters,
        {"identity", "location", "storm", "precipitation", "temperature", "solar_radiation", "wind"},
        "base_station.parameters",
    )
    identity = require_dict(parameters["identity"], "base_station.parameters.identity")
    require_exact_keys(
        identity,
        {"station_name_raw", "state_code", "station_code", "wind_et_flag"},
        "base_station.parameters.identity",
    )
    if not isinstance(identity["station_name_raw"], str) or len(identity["station_name_raw"]) != 41:
        raise PlanError("base station_name_raw must contain exactly 41 characters")
    for key in ("state_code", "station_code", "wind_et_flag"):
        require_integer(identity[key], f"base_station.parameters.identity.{key}")

    location = require_dict(parameters["location"], "base_station.parameters.location")
    require_exact_keys(
        location,
        {"latitude", "longitude", "elevation", "record_years"},
        "base_station.parameters.location",
    )
    require_number(location["latitude"], "base station latitude")
    require_number(location["longitude"], "base station longitude")
    require_integer(location["elevation"], "base station elevation")
    require_integer(location["record_years"], "base station record_years")

    storm = require_dict(parameters["storm"], "base_station.parameters.storm")
    require_exact_keys(
        storm,
        {"single_storm_type", "max_six_hour_precipitation", "time_to_peak_cdf"},
        "base_station.parameters.storm",
    )
    if require_integer(storm["single_storm_type"], "single_storm_type") not in (1, 2, 3, 4):
        raise PlanError("single_storm_type must be in 1..4")
    require_number(storm["max_six_hour_precipitation"], "max_six_hour_precipitation")
    require_vector(storm["time_to_peak_cdf"], 12, "time_to_peak_cdf")

    monthly_groups = {
        "precipitation": (
            "mean_daily",
            "standard_deviation_daily",
            "skew",
            "probability_wet_given_wet",
            "probability_wet_given_dry",
            "max_half_hour_intensity",
        ),
        "temperature": (
            "maximum_mean",
            "minimum_mean",
            "maximum_standard_deviation",
            "minimum_standard_deviation",
            "dew_point_mean",
        ),
        "solar_radiation": ("mean_daily", "standard_deviation_daily"),
    }
    for group_name, keys in monthly_groups.items():
        group = require_dict(parameters[group_name], f"base_station.parameters.{group_name}")
        require_exact_keys(group, set(keys), f"base_station.parameters.{group_name}")
        for key in keys:
            require_vector(group[key], 12, f"base_station.parameters.{group_name}.{key}")

    wind = require_dict(parameters["wind"], "base_station.parameters.wind")
    require_exact_keys(wind, {"directions", "calm_frequency", "interpolation_stations"}, "base_station.parameters.wind")
    require_vector(wind["calm_frequency"], 12, "base_station.parameters.wind.calm_frequency")
    directions = wind["directions"]
    if not isinstance(directions, list) or len(directions) != 16:
        raise PlanError("base_station wind directions must contain exactly 16 entries")
    direction_keys = {"frequency", "mean_speed", "standard_deviation_speed", "skew"}
    for index, direction_value in enumerate(directions):
        direction = require_dict(direction_value, f"wind.directions[{index}]")
        require_exact_keys(direction, direction_keys, f"wind.directions[{index}]")
        for key in sorted(direction_keys):
            require_vector(direction[key], 12, f"wind.directions[{index}].{key}")
    interpolation = wind["interpolation_stations"]
    if not isinstance(interpolation, list) or len(interpolation) != 3:
        raise PlanError("wind interpolation_stations must contain exactly three entries")
    for index, interpolation_value in enumerate(interpolation):
        item = require_dict(interpolation_value, f"wind.interpolation_stations[{index}]")
        require_exact_keys(item, {"station_name_raw", "weight"}, f"wind.interpolation_stations[{index}]")
        if not isinstance(item["station_name_raw"], str) or len(item["station_name_raw"]) != 19:
            raise PlanError("wind interpolation station name must contain 19 characters")
        require_number(item["weight"], f"wind.interpolation_stations[{index}].weight")


def validate_source_lineage(value: Any) -> None:
    lineage = require_dict(value, "source_lineage")
    require_exact_keys(lineage, SOURCE_KEYS, "source_lineage")
    constants = {
        "source_snapshot_id": "daymet_v4r1_a5a17_fit1980_2009_noleap_v1",
        "product": "Daymet V4 R1 daily",
        "product_version": "4.1",
        "doi": "10.3334/ORNLDAAC/2129",
        "heldout_excluded_after": 2009,
        "calendar_transform": "noleap_365_v1",
    }
    for key, expected in constants.items():
        if lineage[key] != expected:
            raise PlanError(f"source_lineage.{key} differs from the frozen identity")
    if lineage["variables"] != ["prcp_mm_day", "tmax_deg_c", "tmin_deg_c"]:
        raise PlanError("source_lineage.variables differs from the frozen order")
    if lineage["fit_period"] != [1980, 2009]:
        raise PlanError("source_lineage.fit_period must equal [1980, 2009]")
    require_string(lineage["retrieval_date"], "source_lineage.retrieval_date")
    require_string(lineage["archive_path"], "source_lineage.archive_path")
    require_sha256(lineage["archive_sha256"], "source_lineage.archive_sha256")
    require_sha256(lineage["decompressed_sha256"], "source_lineage.decompressed_sha256")
    requested = require_dict(lineage["requested_location"], "source_lineage.requested_location")
    require_exact_keys(requested, {"latitude_deg", "longitude_deg", "station_elevation_ft"}, "source_lineage.requested_location")
    for key in requested:
        require_number(requested[key], f"source_lineage.requested_location.{key}")
    grid = require_dict(lineage["returned_grid"], "source_lineage.returned_grid")
    require_exact_keys(grid, {"latitude_deg", "longitude_deg", "x_m", "y_m", "tile", "elevation_m"}, "source_lineage.returned_grid")
    for key in ("latitude_deg", "longitude_deg", "x_m", "y_m"):
        require_number(grid[key], f"source_lineage.returned_grid.{key}")
    require_integer(grid["tile"], "source_lineage.returned_grid.tile", 1)
    require_integer(grid["elevation_m"], "source_lineage.returned_grid.elevation_m")
    header = require_dict(lineage["header"], "source_lineage.header")
    require_exact_keys(header, {"software_version", "selection", "citation"}, "source_lineage.header")
    if header["software_version"] != "4.0" or header["selection"] != "All years; all variables":
        raise PlanError("source_lineage.header version/selection differs from Daymet snapshot")
    require_string(header["citation"], "source_lineage.header.citation")


def validate_fit_contract(value: Any) -> None:
    contract = require_dict(value, "fit_contract")
    require_exact_keys(contract, FIT_KEYS, "fit_contract")
    constants = {
        "coefficient_payload_schema": "a5b_interannual_coefficients_v1",
        "fit_recipe_id": "a5b_monthly_state_fit_v1",
        "precipitation_transform": "monthly_log1p_total_mm_centered_v1",
        "temperature_transform": "monthly_mean_deg_c_centered_v1",
        "detrending": "center_only_raw_v1",
        "usable_years": 30,
        "fit_seed": "none_deterministic_v1",
    }
    for key, expected in constants.items():
        if contract[key] != expected:
            raise PlanError(f"fit_contract.{key} differs from the frozen identity")
    if tuple(contract["feature_order"]) != FEATURE_ORDER:
        raise PlanError("fit_contract.feature_order differs from the frozen 36-vector")
    require_git_commit(contract["implementation_base_commit"], "fit_contract.implementation_base_commit")
    require_sha256(contract["fitter_sha256"], "fit_contract.fitter_sha256")
    for key in ("python_version", "numpy_version", "scipy_version"):
        require_string(contract[key], f"fit_contract.{key}")


def validate_diagnostics(value: Any, payload: dict[str, Any], label: str) -> dict[str, Any]:
    diagnostics = require_dict(value, f"{label}.diagnostics")
    actual = set(diagnostics)
    allowed = DIAGNOSTIC_REQUIRED_KEYS | DIAGNOSTIC_OPTIONAL_KEYS
    if not DIAGNOSTIC_REQUIRED_KEYS <= actual or not actual <= allowed:
        raise PlanError(
            f"{label}.diagnostics keys differ: "
            f"missing={sorted(DIAGNOSTIC_REQUIRED_KEYS - actual)}, "
            f"unknown={sorted(actual - allowed)}"
        )
    if diagnostics["fit_status"] != "ok":
        raise PlanError(f"{label}.diagnostics.fit_status must equal ok")
    for key in ("warnings", "interventions"):
        if not isinstance(diagnostics[key], list) or not all(isinstance(item, str) for item in diagnostics[key]):
            raise PlanError(f"{label}.diagnostics.{key} must be an array of strings")
    serialized_count = require_integer(
        diagnostics["serialized_numeric_count"],
        f"{label}.diagnostics.serialized_numeric_count",
        1,
    )
    if serialized_count != numeric_count(payload):
        raise PlanError(f"{label} serialized_numeric_count does not match payload")
    expected_hash = sha256_bytes(payload_json_bytes(payload))
    recorded_hash = require_sha256(diagnostics["payload_sha256"], f"{label}.diagnostics.payload_sha256")
    if recorded_hash != expected_hash:
        raise PlanError(f"{label} coefficient payload hash mismatch")
    integer_optional = {"retained_rank", "em_iterations"}
    for key in actual & DIAGNOSTIC_OPTIONAL_KEYS:
        if key in integer_optional:
            require_integer(diagnostics[key], f"{label}.diagnostics.{key}", 1)
        else:
            require_number(diagnostics[key], f"{label}.diagnostics.{key}")
    return diagnostics


def validate_extension(value: Any, expected: tuple[str, str, str], label: str) -> dict[str, Any]:
    extension = require_dict(value, label)
    require_exact_keys(extension, EXTENSION_KEYS, label)
    candidate_id, station_model, generation_profile = expected
    if extension["candidate_id"] != candidate_id:
        raise PlanError(f"{label}.candidate_id differs from fixed candidate order")
    if extension["station_model"] != station_model:
        raise PlanError(f"{label}.station_model does not match candidate_id")
    if extension["generation_profile"] != generation_profile:
        raise PlanError(f"{label}.generation_profile does not match candidate_id")
    if extension["coefficient_payload_schema_version"] != 1:
        raise PlanError(f"{label}.coefficient_payload_schema_version must equal 1")
    if extension["fit_recipe_id"] != "a5b_monthly_state_fit_v1":
        raise PlanError(f"{label}.fit_recipe_id differs from the bundle contract")
    require_sha256(extension["fit_identity_sha256"], f"{label}.fit_identity_sha256")
    payload = require_dict(extension["payload"], f"{label}.payload")
    runtime_count = require_integer(extension["runtime_parameter_count"], f"{label}.runtime_parameter_count", 1)
    expected_count, rank = validate_candidate_payload(candidate_id, payload, label)
    if runtime_count != expected_count:
        raise PlanError(f"{label}.runtime_parameter_count must equal {expected_count}")
    diagnostics = validate_diagnostics(extension["diagnostics"], payload, label)
    if rank is not None and "retained_rank" in diagnostics and diagnostics["retained_rank"] != rank:
        raise PlanError(f"{label}.diagnostics.retained_rank differs from payload rank")
    return extension


def validate_candidate_payload(candidate_id: str, payload: dict[str, Any], label: str) -> tuple[int, int | None]:
    if candidate_id == "rank_one_monthly_sd":
        require_exact_keys(payload, {"standard_deviations"}, f"{label}.payload")
        require_vector(payload["standard_deviations"], 36, f"{label}.payload.standard_deviations", lambda x: x >= 0.0)
        return 36, None
    if candidate_id == "full_monthly_covariance":
        require_exact_keys(payload, {"cholesky_lower"}, f"{label}.payload")
        require_compact_lower(payload["cholesky_lower"], 36, f"{label}.payload.cholesky_lower")
        return 666, None

    rank = require_integer(payload.get("rank"), f"{label}.payload.rank")
    if not 3 <= rank <= 10:
        raise PlanError(f"{label}.payload.rank must be in [3, 10]")
    reconstruction = payload.get("reconstruction")
    require_matrix(reconstruction, 36, rank, f"{label}.payload.reconstruction")

    if candidate_id == "fourier_eof":
        require_exact_keys(payload, {"rank", "reconstruction"}, f"{label}.payload")
        return 36 * rank, rank
    if candidate_id == "vector_ar":
        require_exact_keys(
            payload,
            {"rank", "reconstruction", "transition", "innovation_cholesky_lower", "warmup_years"},
            f"{label}.payload",
        )
        require_matrix(payload["transition"], rank, rank, f"{label}.payload.transition")
        require_compact_lower(payload["innovation_cholesky_lower"], rank, f"{label}.payload.innovation_cholesky_lower")
        if payload["warmup_years"] != VAR_WARMUP_YEARS:
            raise PlanError(f"{label}.payload.warmup_years must equal {VAR_WARMUP_YEARS}")
        return 36 * rank + rank * rank + rank * (rank + 1) // 2, rank
    if candidate_id == "gaussian_hmm":
        require_exact_keys(
            payload,
            {"rank", "reconstruction", "transition", "stationary", "emission_means", "emission_standard_deviations"},
            f"{label}.payload",
        )
        transition = require_matrix(payload["transition"], 2, 2, f"{label}.payload.transition", lambda x: 0.0 < x < 1.0)
        stationary = require_vector(payload["stationary"], 2, f"{label}.payload.stationary", lambda x: 0.0 < x < 1.0)
        means = require_matrix(payload["emission_means"], 2, rank, f"{label}.payload.emission_means")
        deviations = require_matrix(payload["emission_standard_deviations"], 2, rank, f"{label}.payload.emission_standard_deviations", lambda x: x >= 0.001)
        _ = means, deviations
        for row_index, row in enumerate(transition):
            if not math.isclose(math.fsum(row), 1.0, rel_tol=0.0, abs_tol=1e-12):
                raise PlanError(f"{label}.payload.transition row {row_index} does not sum to one")
        if not math.isclose(math.fsum(stationary), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise PlanError(f"{label}.payload.stationary does not sum to one")
        evolved = [stationary[0] * transition[0][column] + stationary[1] * transition[1][column] for column in range(2)]
        if any(not math.isclose(evolved[index], stationary[index], rel_tol=0.0, abs_tol=1e-10) for index in range(2)):
            raise PlanError(f"{label}.payload.stationary is not stationary for transition")
        return 36 * rank + 2 + 4 * rank, rank
    if candidate_id == "spectral_random_phase":
        require_exact_keys(payload, {"rank", "reconstruction", "non_dc_amplitudes"}, f"{label}.payload")
        amplitudes = require_matrix(payload["non_dc_amplitudes"], rank, 15, f"{label}.payload.non_dc_amplitudes", lambda x: x >= 0.0)
        for mode, row in enumerate(amplitudes):
            if spectral_training_sd(row) <= 0.0:
                raise PlanError(f"{label}.payload spectral mode {mode} has zero training SD")
        return 36 * rank + 15 * rank, rank
    if candidate_id == "precip_counterfactual":
        require_exact_keys(
            payload,
            {"rank", "reconstruction", "second_order_wet_probabilities", "amount_rank_rho"},
            f"{label}.payload",
        )
        require_matrix(payload["second_order_wet_probabilities"], 12, 4, f"{label}.payload.second_order_wet_probabilities", lambda x: 0.0 < x < 1.0)
        require_vector(payload["amount_rank_rho"], 12, f"{label}.payload.amount_rank_rho", lambda x: -0.95 <= x <= 0.95)
        return 36 * rank + 60, rank
    raise PlanError(f"unsupported candidate_id: {candidate_id}")


def validate_bundle(value: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    bundle = require_dict(value, "station bundle")
    require_exact_keys(bundle, ROOT_KEYS, "station bundle")
    if bundle["station_schema_version"] != 2:
        raise PlanError("station_schema_version must equal 2")
    if bundle["station_document_role"] != "a5b_interannual_candidate_bundle_v1":
        raise PlanError("station_document_role differs from A5b revision 1")
    station_id = require_string(bundle["station_id"], "station_id")
    if re.fullmatch(r"[a-z]{2}[0-9]{6}", station_id) is None:
        raise PlanError("station_id must contain two lowercase letters and six digits")
    validate_base_station(bundle["base_station"])
    validate_source_lineage(bundle["source_lineage"])
    validate_fit_contract(bundle["fit_contract"])
    extensions_value = bundle["extensions"]
    if not isinstance(extensions_value, list) or len(extensions_value) != len(CANDIDATES):
        raise PlanError("extensions must contain the seven candidates exactly once in fixed order")
    extensions = [
        validate_extension(extension, expected, f"extensions[{index}]")
        for index, (extension, expected) in enumerate(zip(extensions_value, CANDIDATES))
    ]
    return bundle, extensions


class SplitMix64BoxMullerV1:
    """Pinned SplitMix64 with one cosine Box-Muller normal per two draws."""

    def __init__(self, state: int):
        if not 0 <= state <= MASK64:
            raise PlanError("SplitMix64 state is outside unsigned 64-bit range")
        self.state = state

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
        return (value ^ (value >> 31)) & MASK64

    def open_unit(self) -> float:
        return ((self.next_u64() >> 11) + 0.5) * (1.0 / float(1 << 53))

    def standard_normal(self) -> float:
        first = self.open_unit()
        second = self.open_unit()
        return math.sqrt(-2.0 * math.log(first)) * math.cos(math.tau * second)


def parse_extension_seed(value: str) -> bytes:
    if re.fullmatch(r"0x[0-9a-f]{16}", value) is None:
        raise PlanError("extension seed must be 0x followed by 16 lowercase hex digits")
    return int(value[2:], 16).to_bytes(8, "big")


def domain_state(domain: bytes, station_id: str, profile: str, seed_bytes: bytes) -> int:
    try:
        suffix = station_id.encode("ascii") + b"\0" + profile.encode("ascii") + b"\0" + seed_bytes
    except UnicodeEncodeError as error:
        raise PlanError("station/profile domain labels must be ASCII") from error
    return int.from_bytes(hashlib.sha256(domain + suffix).digest()[:8], "big")


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    if any(len(row) != len(vector) for row in matrix):
        raise PlanError("matrix/vector shape mismatch during candidate sampling")
    return [math.fsum(coefficient * item for coefficient, item in zip(row, vector)) for row in matrix]


def compact_lower_matvec(lower: list[list[float]], vector: list[float]) -> list[float]:
    if len(lower) != len(vector):
        raise PlanError("lower-factor/vector shape mismatch during candidate sampling")
    return [
        math.fsum(coefficient * vector[column] for column, coefficient in enumerate(row))
        for row in lower
    ]


def add_vectors(left: list[float], right: list[float]) -> list[float]:
    if len(left) != len(right):
        raise PlanError("vector shape mismatch during candidate sampling")
    return [a + b for a, b in zip(left, right)]


def sample_raw_states(candidate_id: str, payload: dict[str, Any], rng: SplitMix64BoxMullerV1) -> list[list[float]]:
    if candidate_id == "rank_one_monthly_sd":
        deviations = [float(value) for value in payload["standard_deviations"]]
        result = []
        for _ in range(FIXED_YEARS):
            draws = [rng.standard_normal() for _ in range(3)]
            result.append(
                [draws[variable] * deviations[variable * 12 + month] for variable in range(3) for month in range(12)]
            )
        return result
    if candidate_id == "full_monthly_covariance":
        lower = [[float(item) for item in row] for row in payload["cholesky_lower"]]
        return [compact_lower_matvec(lower, [rng.standard_normal() for _ in range(36)]) for _ in range(FIXED_YEARS)]

    rank = int(payload["rank"])
    reconstruction = [[float(item) for item in row] for row in payload["reconstruction"]]
    if candidate_id in ("fourier_eof", "precip_counterfactual"):
        return [matvec(reconstruction, [rng.standard_normal() for _ in range(rank)]) for _ in range(FIXED_YEARS)]
    if candidate_id == "vector_ar":
        transition = [[float(item) for item in row] for row in payload["transition"]]
        lower = [[float(item) for item in row] for row in payload["innovation_cholesky_lower"]]
        score = [0.0] * rank
        for _ in range(VAR_WARMUP_YEARS):
            innovation = compact_lower_matvec(lower, [rng.standard_normal() for _ in range(rank)])
            score = add_vectors(matvec(transition, score), innovation)
        result = []
        for _ in range(FIXED_YEARS):
            innovation = compact_lower_matvec(lower, [rng.standard_normal() for _ in range(rank)])
            score = add_vectors(matvec(transition, score), innovation)
            result.append(matvec(reconstruction, score))
        return result
    if candidate_id == "gaussian_hmm":
        transition = [[float(item) for item in row] for row in payload["transition"]]
        stationary = [float(item) for item in payload["stationary"]]
        means = [[float(item) for item in row] for row in payload["emission_means"]]
        deviations = [[float(item) for item in row] for row in payload["emission_standard_deviations"]]
        state = 0 if rng.open_unit() < stationary[0] else 1
        result = []
        for year in range(FIXED_YEARS):
            score = [means[state][mode] + deviations[state][mode] * rng.standard_normal() for mode in range(rank)]
            result.append(matvec(reconstruction, score))
            if year + 1 < FIXED_YEARS:
                state = 0 if rng.open_unit() < transition[state][0] else 1
        return result
    if candidate_id == "spectral_random_phase":
        amplitudes = [[float(item) for item in row] for row in payload["non_dc_amplitudes"]]
        score_series = [spectral_score_series(row, rng) for row in amplitudes]
        return [matvec(reconstruction, [score_series[mode][year] for mode in range(rank)]) for year in range(FIXED_YEARS)]
    raise PlanError(f"unsupported candidate sampler: {candidate_id}")


def spectral_training_sd(amplitudes: list[float]) -> float:
    if len(amplitudes) != 15:
        raise PlanError("spectral amplitude vector must contain 15 non-DC bins")
    weighted_energy = 2.0 * math.fsum(value * value for value in amplitudes[:-1]) + amplitudes[-1] * amplitudes[-1]
    result = math.sqrt(weighted_energy / (30.0 * 29.0))
    if not math.isfinite(result):
        raise PlanError("spectral training sample SD is nonfinite")
    return result


def interpolated_amplitude(training: list[float], target_bin: int) -> float:
    position = (30.0 * target_bin) / FIXED_YEARS
    lower = int(math.floor(position))
    if lower >= 15:
        return training[14]
    lower_value = 0.0 if lower == 0 else training[lower - 1]
    upper_value = training[lower]
    fraction = position - lower
    return lower_value + fraction * (upper_value - lower_value)


def spectral_score_series(training: list[float], rng: SplitMix64BoxMullerV1) -> list[float]:
    target_sd = spectral_training_sd(training)
    positive_real = [0.0] * 65
    positive_imaginary = [0.0] * 65
    for frequency in range(1, 64):
        amplitude = interpolated_amplitude(training, frequency)
        phase = math.tau * rng.open_unit()
        positive_real[frequency] = amplitude * math.cos(phase)
        positive_imaginary[frequency] = amplitude * math.sin(phase)
    positive_real[64] = training[-1] * (-1.0 if rng.open_unit() < 0.5 else 1.0)
    result = []
    for year in range(FIXED_YEARS):
        total = positive_real[64] * (-1.0 if year % 2 else 1.0)
        total += 2.0 * math.fsum(
            positive_real[frequency] * math.cos(math.tau * frequency * year / FIXED_YEARS)
            - positive_imaginary[frequency] * math.sin(math.tau * frequency * year / FIXED_YEARS)
            for frequency in range(1, 64)
        )
        result.append(total / FIXED_YEARS)
    mean = math.fsum(result) / FIXED_YEARS
    centered = [value - mean for value in result]
    generated_sd = math.sqrt(math.fsum(value * value for value in centered) / (FIXED_YEARS - 1))
    if not math.isfinite(generated_sd) or generated_sd <= 0.0:
        raise PlanError("spectral realization has zero or nonfinite sample SD")
    return [value * target_sd / generated_sd for value in centered]


def exact_sum_residual(values: list[float], adjustable: list[int]) -> list[float]:
    """Force the rounded ``math.fsum`` to the frozen integer target.

    The proportional projection is already within a few ulps of the target.
    Revision 1 assigns that residual to the lowest-index interior value.  If
    subtraction rounds to an adjacent float, deterministic ``nextafter``
    steps select the closest value whose correctly rounded sum is exact.
    """

    for index in adjustable:
        others = math.fsum(value for position, value in enumerate(values) if position != index)
        candidate = PRECIP_FACTOR_TARGET_SUM - others
        if not PRECIP_FACTOR_MIN < candidate < PRECIP_FACTOR_MAX:
            continue
        original = values[index]
        values[index] = candidate
        if math.fsum(values) == PRECIP_FACTOR_TARGET_SUM:
            return values
        direction = math.inf if math.fsum(values) < PRECIP_FACTOR_TARGET_SUM else -math.inf
        for _ in range(8):
            candidate = math.nextafter(candidate, direction)
            if not PRECIP_FACTOR_MIN < candidate < PRECIP_FACTOR_MAX:
                break
            values[index] = candidate
            total = math.fsum(values)
            if total == PRECIP_FACTOR_TARGET_SUM:
                return values
            if (direction > 0.0 and total > PRECIP_FACTOR_TARGET_SUM) or (
                direction < 0.0 and total < PRECIP_FACTOR_TARGET_SUM
            ):
                break
        values[index] = original
    raise PlanError("bounded precipitation projection cannot assign its exact residual")


def project_precipitation_factors(exponents: list[float]) -> tuple[list[float], int]:
    """Project positive factors onto the proportional mean-one box.

    The event sweep identifies the unique active interval of
    ``sum(clamp(scale * factor, 0.05, 20))``.  Within that interval the scale
    is solved from the active-set equation, then the specified residual rule
    makes the correctly rounded 128-value sum exactly 128.
    """

    if len(exponents) != FIXED_YEARS:
        raise PlanError("precipitation projection requires exactly 128 exponents")
    try:
        factors = [math.exp(value) for value in exponents]
    except OverflowError as error:
        raise PlanError("precipitation exponent overflow") from error
    if any(not math.isfinite(value) or value <= 0.0 for value in factors):
        raise PlanError("precipitation exponent is nonfinite or nonpositive")

    events = sorted(
        [
            (bound / factor, kind, index)
            for index, factor in enumerate(factors)
            for kind, bound in ((0, PRECIP_FACTOR_MIN), (1, PRECIP_FACTOR_MAX))
        ],
        key=lambda event: (event[0], event[1], event[2]),
    )
    low = set(range(FIXED_YEARS))
    active: set[int] = set()
    high: set[int] = set()
    position = 0
    scale: float | None = None
    while position < len(events):
        breakpoint = events[position][0]
        total_at_breakpoint = math.fsum(
            [PRECIP_FACTOR_MIN] * len(low)
            + [breakpoint * factors[index] for index in sorted(active)]
            + [PRECIP_FACTOR_MAX] * len(high)
        )
        if active and total_at_breakpoint >= PRECIP_FACTOR_TARGET_SUM:
            active_sum = math.fsum(factors[index] for index in sorted(active))
            scale = (
                PRECIP_FACTOR_TARGET_SUM
                - PRECIP_FACTOR_MIN * len(low)
                - PRECIP_FACTOR_MAX * len(high)
            ) / active_sum
            break
        stop = position + 1
        while stop < len(events) and events[stop][0] == breakpoint:
            stop += 1
        for _, kind, index in events[position:stop]:
            if kind == 0:
                low.remove(index)
                active.add(index)
            else:
                active.remove(index)
                high.add(index)
        position = stop
    if scale is None:
        raise PlanError("bounded precipitation projection did not bracket mean one")

    projected = [
        min(PRECIP_FACTOR_MAX, max(PRECIP_FACTOR_MIN, scale * factor))
        for factor in factors
    ]
    interior = [
        index
        for index, value in enumerate(projected)
        if PRECIP_FACTOR_MIN < value < PRECIP_FACTOR_MAX
    ]
    projected = exact_sum_residual(projected, interior)
    if any(
        not math.isfinite(value)
        or not PRECIP_FACTOR_MIN <= value <= PRECIP_FACTOR_MAX
        for value in projected
    ):
        raise PlanError("bounded precipitation projection left its frozen box")
    if math.fsum(projected) != PRECIP_FACTOR_TARGET_SUM:
        raise PlanError("bounded precipitation projection does not have exact mean one")
    bound_count = sum(
        value == PRECIP_FACTOR_MIN or value == PRECIP_FACTOR_MAX
        for value in projected
    )
    return projected, bound_count


def normalize_states(raw: list[list[float]]) -> tuple[list[dict[str, Any]], int]:
    if len(raw) != FIXED_YEARS or any(len(row) != 36 for row in raw):
        raise PlanError("candidate sampler did not produce a 128 x 36 state table")
    if any(not math.isfinite(value) for row in raw for value in row):
        raise PlanError("candidate sampler produced a nonfinite feature")

    temperature = [[row[column] for row in raw] for column in range(12, 36)]
    temperature_means = [math.fsum(column) / FIXED_YEARS for column in temperature]
    temperature_centered = [
        [row[column] - temperature_means[column - 12] for column in range(12, 36)]
        for row in raw
    ]

    precipitation_columns: list[list[float]] = []
    bound_count = 0
    for month in range(12):
        final, month_bound_count = project_precipitation_factors(
            [row[month] for row in raw]
        )
        bound_count += month_bound_count
        precipitation_columns.append(final)

    states = []
    for year in range(FIXED_YEARS):
        tmax = temperature_centered[year][:12]
        tmin = temperature_centered[year][12:]
        if any(not -30.0 <= value <= 30.0 for value in tmax + tmin):
            raise PlanError(f"temperature delta leaves schema bounds in simulation year {year + 1}")
        states.append(
            {
                "simulation_year": year + 1,
                "precip_factor": [precipitation_columns[month][year] for month in range(12)],
                "tmax_delta_c": tmax,
                "tmin_delta_c": tmin,
            }
        )
    validate_normalized_states(states)
    return states, bound_count


def validate_normalized_states(states: list[dict[str, Any]]) -> None:
    for month in range(12):
        precipitation_mean = math.fsum(state["precip_factor"][month] for state in states) / FIXED_YEARS
        tmax_mean = math.fsum(state["tmax_delta_c"][month] for state in states) / FIXED_YEARS
        tmin_mean = math.fsum(state["tmin_delta_c"][month] for state in states) / FIXED_YEARS
        if precipitation_mean != 1.0:
            raise PlanError(f"normalized precipitation month {month + 1} does not have mean one")
        if not math.isclose(tmax_mean, 0.0, rel_tol=0.0, abs_tol=2e-15):
            raise PlanError(f"centered Tmax month {month + 1} does not have mean zero")
        if not math.isclose(tmin_mean, 0.0, rel_tol=0.0, abs_tol=2e-15):
            raise PlanError(f"centered Tmin month {month + 1} does not have mean zero")


def generate_plan(bundle_value: Any, candidate_id: str, extension_seed: str) -> dict[str, Any]:
    bundle, extensions = validate_bundle(bundle_value)
    if candidate_id not in CANDIDATE_INDEX:
        raise PlanError(f"unsupported candidate_id {candidate_id!r}")
    seed_bytes = parse_extension_seed(extension_seed)
    index = CANDIDATE_INDEX[candidate_id]
    extension = extensions[index]
    _, station_model, profile = CANDIDATES[index]
    main_state = domain_state(MAIN_DOMAIN, bundle["station_id"], profile, seed_bytes)
    raw = sample_raw_states(candidate_id, extension["payload"], SplitMix64BoxMullerV1(main_state))
    annual_states, clip_count = normalize_states(raw)
    state_hash = sha256_bytes(canonical_state_bytes(annual_states))
    plan: dict[str, Any] = {
        "plan_schema_version": 1,
        "station_id": bundle["station_id"],
        "station_model": station_model,
        "candidate_profile": profile,
        "extension_seed": extension_seed,
        "coefficient_payload_sha256": extension["diagnostics"]["payload_sha256"],
        "state_table_sha256": state_hash,
        "normalization": {
            "fixed_years": FIXED_YEARS,
            "precipitation_clip_count": clip_count,
            "temperature_centered": True,
        },
        "annual_states": annual_states,
    }
    if candidate_id == "precip_counterfactual":
        payload = extension["payload"]
        counterfactual_state = domain_state(
            COUNTERFACTUAL_DOMAIN,
            bundle["station_id"],
            profile,
            seed_bytes,
        )
        plan["counterfactual"] = {
            "second_order_prob": copy.deepcopy(payload["second_order_wet_probabilities"]),
            "amount_rank_rho": copy.deepcopy(payload["amount_rank_rho"]),
            "rng_state": f"0x{counterfactual_state:016x}",
        }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    expected_keys = {
        "plan_schema_version",
        "station_id",
        "station_model",
        "candidate_profile",
        "extension_seed",
        "coefficient_payload_sha256",
        "state_table_sha256",
        "normalization",
        "annual_states",
    }
    counterfactual_profile = "a5b_fourier_eof_precip_counterfactual_v1"
    if plan["candidate_profile"] == counterfactual_profile:
        expected_keys.add("counterfactual")
    require_exact_keys(plan, expected_keys, "overlay plan")
    if plan["plan_schema_version"] != 1:
        raise PlanError("plan_schema_version must equal 1")
    pair = next((row for row in CANDIDATES if row[2] == plan["candidate_profile"]), None)
    if pair is None or pair[1] != plan["station_model"]:
        raise PlanError("plan station_model/candidate_profile pair is invalid")
    parse_extension_seed(plan["extension_seed"])
    require_sha256(plan["coefficient_payload_sha256"], "plan coefficient_payload_sha256")
    recorded_hash = require_sha256(plan["state_table_sha256"], "plan state_table_sha256")
    states = plan["annual_states"]
    if not isinstance(states, list) or len(states) != FIXED_YEARS:
        raise PlanError("plan annual_states must contain exactly 128 entries")
    for index, state_value in enumerate(states):
        state = require_dict(state_value, f"annual_states[{index}]")
        require_exact_keys(state, {"simulation_year", "precip_factor", "tmax_delta_c", "tmin_delta_c"}, f"annual_states[{index}]")
        if state["simulation_year"] != index + 1:
            raise PlanError("annual state simulation_year values must be contiguous 1..128")
        require_vector(state["precip_factor"], 12, f"annual_states[{index}].precip_factor", lambda x: 0.05 <= x <= 20.0)
        require_vector(state["tmax_delta_c"], 12, f"annual_states[{index}].tmax_delta_c", lambda x: -30.0 <= x <= 30.0)
        require_vector(state["tmin_delta_c"], 12, f"annual_states[{index}].tmin_delta_c", lambda x: -30.0 <= x <= 30.0)
    if recorded_hash != sha256_bytes(canonical_state_bytes(states)):
        raise PlanError("plan state_table_sha256 does not match annual_states")
    normalization = require_dict(plan["normalization"], "plan normalization")
    require_exact_keys(normalization, {"fixed_years", "precipitation_clip_count", "temperature_centered"}, "plan normalization")
    if normalization["fixed_years"] != FIXED_YEARS or normalization["temperature_centered"] is not True:
        raise PlanError("plan normalization identity differs from revision 1")
    require_integer(normalization["precipitation_clip_count"], "plan precipitation_clip_count", 0)
    if "counterfactual" in plan:
        counterfactual = require_dict(plan["counterfactual"], "plan counterfactual")
        require_exact_keys(counterfactual, {"second_order_prob", "amount_rank_rho", "rng_state"}, "plan counterfactual")
        require_matrix(counterfactual["second_order_prob"], 12, 4, "plan counterfactual.second_order_prob", lambda x: 0.0 < x < 1.0)
        require_vector(counterfactual["amount_rank_rho"], 12, "plan counterfactual.amount_rank_rho", lambda x: -0.95 <= x <= 0.95)
        parse_extension_seed(counterfactual["rng_state"])


def plan_json_bytes(plan: dict[str, Any]) -> bytes:
    try:
        return (
            json.dumps(plan, allow_nan=False, ensure_ascii=True, indent=2)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PlanError(f"cannot serialize overlay plan: {error}") from error


def write_new(path: Path, raw: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
    except FileExistsError as error:
        raise PlanError(f"output plan already exists: {path}") from error
    except OSError as error:
        raise PlanError(f"cannot create output plan {path}: {error}") from error


def synthetic_base_station() -> dict[str, Any]:
    months = [0.25] * 12
    monthly = lambda keys: {key: months.copy() for key in keys}
    return {
        "station_schema_version": 1,
        "station_model": "fixed_monthly_5_32_3",
        "units": {
            "latitude": "degree_north",
            "longitude": "degree_east",
            "elevation": "foot",
            "record_length": "year",
            "precipitation_depth": "inch",
            "precipitation_intensity": "inch_per_hour",
            "temperature": "degree_fahrenheit",
            "solar_radiation": "langley_per_day",
            "wind_speed": "meter_per_second",
            "frequency": "percent",
            "probability": "fraction",
            "interpolation_weight": "dimensionless",
            "skew": "dimensionless",
        },
        "lineage": {
            "source_format": "cligen_par_5_32_3",
            "source_sha256": "1" * 64,
            "adapter": "cligen_rs_legacy_par_to_fixed_monthly",
            "adapter_version": 1,
        },
        "parameters": {
            "identity": {
                "station_name_raw": "SYNTHETIC".ljust(41),
                "state_code": 10,
                "station_code": 6388,
                "wind_et_flag": 0,
            },
            "location": {"latitude": 43.0, "longitude": -116.0, "elevation": 2500, "record_years": 30},
            "storm": {"single_storm_type": 1, "max_six_hour_precipitation": 1.0, "time_to_peak_cdf": months.copy()},
            "precipitation": monthly(("mean_daily", "standard_deviation_daily", "skew", "probability_wet_given_wet", "probability_wet_given_dry", "max_half_hour_intensity")),
            "temperature": monthly(("maximum_mean", "minimum_mean", "maximum_standard_deviation", "minimum_standard_deviation", "dew_point_mean")),
            "solar_radiation": monthly(("mean_daily", "standard_deviation_daily")),
            "wind": {
                "directions": [monthly(("frequency", "mean_speed", "standard_deviation_speed", "skew")) for _ in range(16)],
                "calm_frequency": months.copy(),
                "interpolation_stations": [
                    {"station_name_raw": f"SYNTHETIC {index}".ljust(19), "weight": 1.0 / 3.0}
                    for index in range(3)
                ],
            },
        },
    }


def synthetic_extension(candidate: tuple[str, str, str]) -> dict[str, Any]:
    candidate_id, station_model, profile = candidate
    rank = 3
    reconstruction = [
        [0.02 * ((row + mode) % 5 - 2) for mode in range(rank)]
        for row in range(36)
    ]
    if candidate_id == "rank_one_monthly_sd":
        payload: dict[str, Any] = {"standard_deviations": [0.03 + 0.001 * index for index in range(36)]}
        count = 36
    elif candidate_id == "full_monthly_covariance":
        payload = {
            "cholesky_lower": [
                [0.0] * row + [0.04 + row * 0.0005]
                for row in range(36)
            ]
        }
        count = 666
    elif candidate_id == "fourier_eof":
        payload = {"rank": rank, "reconstruction": reconstruction}
        count = 36 * rank
    elif candidate_id == "vector_ar":
        payload = {
            "rank": rank,
            "reconstruction": reconstruction,
            "transition": [[0.45 if row == column else 0.03 for column in range(rank)] for row in range(rank)],
            "innovation_cholesky_lower": [[0.0] * row + [0.35 - 0.02 * row] for row in range(rank)],
            "warmup_years": VAR_WARMUP_YEARS,
        }
        count = 36 * rank + rank * rank + rank * (rank + 1) // 2
    elif candidate_id == "gaussian_hmm":
        payload = {
            "rank": rank,
            "reconstruction": reconstruction,
            "transition": [[0.8, 0.2], [0.3, 0.7]],
            "stationary": [0.6, 0.4],
            "emission_means": [[-0.3, 0.1, -0.2], [0.45, -0.15, 0.3]],
            "emission_standard_deviations": [[0.5, 0.4, 0.3], [0.35, 0.45, 0.55]],
        }
        count = 36 * rank + 2 + 4 * rank
    elif candidate_id == "spectral_random_phase":
        payload = {
            "rank": rank,
            "reconstruction": reconstruction,
            "non_dc_amplitudes": [
                [0.5 + 0.03 * mode + 0.01 * frequency for frequency in range(15)]
                for mode in range(rank)
            ],
        }
        count = 36 * rank + 15 * rank
    else:
        payload = {
            "rank": rank,
            "reconstruction": reconstruction,
            "second_order_wet_probabilities": [
                [0.1 + 0.02 * condition + 0.001 * month for condition in range(4)]
                for month in range(12)
            ],
            "amount_rank_rho": [-0.3 + 0.05 * month for month in range(12)],
        }
        count = 36 * rank + 60
    diagnostics: dict[str, Any] = {
        "fit_status": "ok",
        "warnings": [],
        "interventions": [],
        "serialized_numeric_count": numeric_count(payload),
        "payload_sha256": sha256_bytes(payload_json_bytes(payload)),
    }
    if "rank" in payload:
        diagnostics["retained_rank"] = rank
    return {
        "candidate_id": candidate_id,
        "station_model": station_model,
        "generation_profile": profile,
        "coefficient_payload_schema_version": 1,
        "fit_recipe_id": "a5b_monthly_state_fit_v1",
        "fit_identity_sha256": hashlib.sha256(candidate_id.encode("ascii")).hexdigest(),
        "runtime_parameter_count": count,
        "payload": payload,
        "diagnostics": diagnostics,
    }


def synthetic_bundle() -> dict[str, Any]:
    return {
        "station_schema_version": 2,
        "station_document_role": "a5b_interannual_candidate_bundle_v1",
        "station_id": "id106388",
        "base_station": synthetic_base_station(),
        "source_lineage": {
            "source_snapshot_id": "daymet_v4r1_a5a17_fit1980_2009_noleap_v1",
            "product": "Daymet V4 R1 daily",
            "product_version": "4.1",
            "doi": "10.3334/ORNLDAAC/2129",
            "retrieval_date": "2026-07-12",
            "archive_path": "references/observed/a5a-v1/daymet/id106388.csv.gz",
            "archive_sha256": "2" * 64,
            "decompressed_sha256": "3" * 64,
            "requested_location": {"latitude_deg": 43.0, "longitude_deg": -116.0, "station_elevation_ft": 2500.0},
            "returned_grid": {"latitude_deg": 43.0, "longitude_deg": -116.0, "x_m": 1.0, "y_m": 2.0, "tile": 1, "elevation_m": 762},
            "header": {"software_version": "4.0", "selection": "All years; all variables", "citation": "synthetic self-test"},
            "variables": ["prcp_mm_day", "tmax_deg_c", "tmin_deg_c"],
            "fit_period": [1980, 2009],
            "heldout_excluded_after": 2009,
            "calendar_transform": "noleap_365_v1",
        },
        "fit_contract": {
            "coefficient_payload_schema": "a5b_interannual_coefficients_v1",
            "fit_recipe_id": "a5b_monthly_state_fit_v1",
            "implementation_base_commit": "4" * 40,
            "fitter_sha256": "5" * 64,
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
            "scipy_version": "self-test",
            "feature_order": list(FEATURE_ORDER),
            "precipitation_transform": "monthly_log1p_total_mm_centered_v1",
            "temperature_transform": "monthly_mean_deg_c_centered_v1",
            "detrending": "center_only_raw_v1",
            "usable_years": 30,
            "fit_seed": "none_deterministic_v1",
        },
        "extensions": [synthetic_extension(candidate) for candidate in CANDIDATES],
    }


def expect_plan_error(action: Callable[[], Any], label: str) -> None:
    try:
        action()
    except PlanError:
        return
    raise PlanError(f"self-test mutation was accepted: {label}")


def run_self_test() -> None:
    expect_plan_error(lambda: load_json_strict_bytes(b'{"a":1,"a":2}', "duplicate mutation"), "duplicate key")
    expect_plan_error(lambda: load_json_strict_bytes(b'{"a":NaN}', "NaN mutation"), "NaN")
    expect_plan_error(lambda: load_json_strict_bytes(b'{"a":1e999}', "overflow mutation"), "overflowing number")

    bundle = synthetic_bundle()
    validate_bundle(bundle)
    seed = "0x0c8862ed55f21e2e"
    for candidate_id, _, _ in CANDIDATES:
        first = generate_plan(bundle, candidate_id, seed)
        second = generate_plan(copy.deepcopy(bundle), candidate_id, seed)
        first_bytes = plan_json_bytes(first)
        if first_bytes != plan_json_bytes(second):
            raise PlanError(f"self-test {candidate_id} plan is not byte-repeatable")
        if first["state_table_sha256"] != SELF_TEST_STATE_HASHES[candidate_id]:
            raise PlanError(
                f"self-test {candidate_id} state hash differs: "
                f"{first['state_table_sha256']}"
            )
        if not first_bytes.endswith(b"\n") or b"NaN" in first_bytes or b"Infinity" in first_bytes:
            raise PlanError(f"self-test {candidate_id} serialization is not strict JSON+LF")
    counterfactual = generate_plan(bundle, "precip_counterfactual", seed)
    if counterfactual["counterfactual"]["rng_state"] != SELF_TEST_COUNTERFACTUAL_RNG_STATE:
        raise PlanError(
            "self-test counterfactual rng_state differs: "
            f"{counterfactual['counterfactual']['rng_state']}"
        )

    projected, bound_count = project_precipitation_factors(
        [-12.0] * 16 + [0.0] * 111 + [12.0]
    )
    if (
        math.fsum(projected) != PRECIP_FACTOR_TARGET_SUM
        or min(projected) != PRECIP_FACTOR_MIN
        or max(projected) != PRECIP_FACTOR_MAX
        or bound_count != 17
    ):
        raise PlanError("self-test bounded proportional projection differs")

    mutation = copy.deepcopy(bundle)
    mutation["extensions"][2]["diagnostics"]["payload_sha256"] = "0" * 64
    expect_plan_error(lambda: validate_bundle(mutation), "payload hash")
    mutation = copy.deepcopy(bundle)
    mutation["extensions"][0]["station_model"] = CANDIDATES[1][1]
    expect_plan_error(lambda: validate_bundle(mutation), "model/profile mapping")
    mutation = copy.deepcopy(bundle)
    mutation["extensions"][5]["payload"]["non_dc_amplitudes"][0].pop()
    expect_plan_error(lambda: validate_bundle(mutation), "spectral payload shape")
    mutation = copy.deepcopy(bundle)
    mutation["extensions"][0]["unknown"] = 1
    expect_plan_error(lambda: validate_bundle(mutation), "unknown extension field")
    expect_plan_error(lambda: generate_plan(bundle, "unknown", seed), "unknown candidate")
    expect_plan_error(lambda: generate_plan(bundle, "fourier_eof", "0xABC"), "malformed seed")

    with tempfile.TemporaryDirectory(prefix="a5b-plan-self-test-") as temporary:
        destination = Path(temporary) / "plan.json"
        raw = plan_json_bytes(generate_plan(bundle, "fourier_eof", seed))
        write_new(destination, raw)
        if destination.read_bytes() != raw:
            raise PlanError("self-test output bytes differ after publication")
        expect_plan_error(lambda: write_new(destination, raw), "output overwrite")
    print("generate-a5b-plan self-test: PASS")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", nargs="?")
    parser.add_argument("candidate_id", nargs="?")
    parser.add_argument("extension_seed", nargs="?")
    parser.add_argument("output_plan", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    positional = (args.bundle, args.candidate_id, args.extension_seed, args.output_plan)
    if args.self_test:
        if any(item is not None for item in positional):
            parser.error("--self-test does not accept positional arguments")
    elif any(item is None for item in positional):
        parser.error("bundle, candidate_id, extension_seed, and output_plan are required")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.self_test:
            run_self_test()
            return 0
        bundle_path = Path(args.bundle)
        output_path = Path(args.output_plan)
        if output_path.exists():
            raise PlanError(f"output plan already exists: {output_path}")
        try:
            raw = bundle_path.read_bytes()
        except OSError as error:
            raise PlanError(f"cannot read station bundle {bundle_path}: {error}") from error
        bundle = load_json_strict_bytes(raw, str(bundle_path))
        plan = generate_plan(bundle, args.candidate_id, args.extension_seed)
        write_new(output_path, plan_json_bytes(plan))
        return 0
    except PlanError as error:
        print(f"generate-a5b-plan: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
