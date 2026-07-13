#!/usr/bin/env python3
"""Build the strict public A5a observed-target Draft 2020-12 schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from corpus_common import write_canonical_json

MONTHS = (
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
STATION_IDS = (
    "ca042319",
    "az029654",
    "ut429382",
    "ca042257",
    "az022664",
    "az028619",
    "nm294426",
    "tx412797",
    "al015478",
    "ms227840",
    "fl086997",
    "fl083909",
    "co051660",
    "wy485345",
    "mn214026",
    "ak505769",
    "id106388",
)
FIXED_PERIODS = {
    "evaluation": [2010, 2025],
    "fit": [1980, 2009],
    "full": [1980, 2025],
}


def ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


def obj(properties: dict[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def nullable_number(
    minimum: float | None = None, maximum: float | None = None
) -> dict[str, object]:
    number: dict[str, object] = {"type": "number"}
    if minimum is not None:
        number["minimum"] = minimum
    if maximum is not None:
        number["maximum"] = maximum
    return {"anyOf": [number, {"type": "null"}]}


def months(definition: str) -> dict[str, object]:
    return obj({month: ref(definition) for month in MONTHS})


def fixed_array(items: dict[str, object], size: int = 12) -> dict[str, object]:
    return {
        "type": "array",
        "minItems": size,
        "maxItems": size,
        "items": items,
    }


def fixed_matrix(items: dict[str, object]) -> dict[str, object]:
    return fixed_array(fixed_array(items))


def period_variant(start: int, end: int) -> dict[str, object]:
    return {
        "allOf": [
            ref("target_period"),
            {
                "properties": {
                    "period": {
                        "const": {
                            "end_year": end,
                            "start_year": start,
                        }
                    }
                }
            },
        ]
    }


def source_identity(calendar: str, source_id_pattern: str) -> dict[str, object]:
    return obj(
        {
            "archive_sha256": ref("sha256"),
            "calendar": {"const": calendar},
            "fixed_window_logical_records_sha256": ref("sha256"),
            "source_id": {"type": "string", "pattern": source_id_pattern},
            "source_sha256": ref("sha256"),
        }
    )


def available_source(calendar: str, source_id_pattern: str) -> dict[str, object]:
    return obj(
        {
            "availability": {"const": "available"},
            "periods": ref("target_periods"),
            "source_identity": source_identity(calendar, source_id_pattern),
        }
    )


def build_schema() -> dict[str, object]:
    defs: dict[str, object] = {}
    defs["sha256"] = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    defs["nonnegative_integer"] = {"type": "integer", "minimum": 0}
    defs["nullable_number"] = nullable_number()
    defs["nullable_nonnegative_number"] = nullable_number(0)
    defs["nullable_correlation"] = nullable_number(-1, 1)
    defs["nullable_fraction"] = nullable_number(0, 1)

    defs["corr_pair"] = obj(
        {
            "n": ref("nonnegative_integer"),
            "pearson": ref("nullable_correlation"),
            "spearman": ref("nullable_correlation"),
        }
    )
    defs["precip_dispersion"] = obj(
        {
            "cv": ref("nullable_nonnegative_number"),
            "detrended_sd": ref("nullable_nonnegative_number"),
            "mean": ref("nullable_nonnegative_number"),
            "n_years": ref("nonnegative_integer"),
            "sd": ref("nullable_nonnegative_number"),
        }
    )
    defs["temperature_dispersion"] = obj(
        {
            "cv": {"type": "null"},
            "detrended_sd": ref("nullable_nonnegative_number"),
            "mean": ref("nullable_number"),
            "n_years": ref("nonnegative_integer"),
            "sd": ref("nullable_nonnegative_number"),
        }
    )
    defs["annual_targets"] = obj(
        {
            "max_daily_precip_mm": ref("precip_dispersion"),
            "precip_total_mm": ref("precip_dispersion"),
            "r1mm_wet_day_count": ref("precip_dispersion"),
            "tmax_mean_c": ref("temperature_dispersion"),
            "tmin_mean_c": ref("temperature_dispersion"),
        }
    )
    defs["monthly_targets"] = obj(
        {
            "precip_total_mm": ref("precip_dispersion"),
            "r1mm_wet_day_count": ref("precip_dispersion"),
            "r1mm_wet_day_mean_amount_mm": ref("precip_dispersion"),
            "tmax_mean_c": ref("temperature_dispersion"),
            "tmin_mean_c": ref("temperature_dispersion"),
        }
    )
    defs["months_monthly_targets"] = months("monthly_targets")

    defs["month_dependence_matrix"] = obj(
        {
            "covariance": fixed_matrix(ref("nullable_number")),
            "n_pairs": fixed_matrix(ref("nonnegative_integer")),
            "pearson_correlation": fixed_matrix(ref("nullable_correlation")),
        }
    )
    defs["climate_anomaly_correlations"] = obj(
        {
            "precip_tmax": ref("corr_pair"),
            "precip_tmin": ref("corr_pair"),
            "tmax_tmin": ref("corr_pair"),
        }
    )
    defs["months_climate_anomaly_correlations"] = months("climate_anomaly_correlations")
    defs["series_dependence"] = obj(
        {
            "lag_one": ref("corr_pair"),
            "n_years": ref("nonnegative_integer"),
            "period_ge_4y_power_fraction": ref("nullable_fraction"),
        }
    )
    defs["annual_dependence"] = obj(
        {
            "precip_total_mm": ref("series_dependence"),
            "tmax_mean_c": ref("series_dependence"),
            "tmin_mean_c": ref("series_dependence"),
        }
    )
    defs["dependence_variant"] = obj(
        {
            "annual": ref("annual_dependence"),
            "cross_variable_by_month": ref("months_climate_anomaly_correlations"),
            "precip_cross_month": ref("month_dependence_matrix"),
            "tmax_cross_month": ref("month_dependence_matrix"),
            "tmin_cross_month": ref("month_dependence_matrix"),
        }
    )
    defs["dependence"] = obj(
        {
            "detrended": ref("dependence_variant"),
            "raw": ref("dependence_variant"),
        }
    )

    defs["scalar_distribution"] = obj(
        {
            "max": ref("nullable_nonnegative_number"),
            "mean": ref("nullable_nonnegative_number"),
            "n": ref("nonnegative_integer"),
            "p50": ref("nullable_nonnegative_number"),
            "p90": ref("nullable_nonnegative_number"),
            "p95": ref("nullable_nonnegative_number"),
            "p99": ref("nullable_nonnegative_number"),
            "sd": ref("nullable_nonnegative_number"),
        }
    )
    defs["months_scalar_distribution"] = months("scalar_distribution")
    defs["spell_distribution"] = obj(
        {
            "by_start_month": ref("months_scalar_distribution"),
            "whole_run": ref("scalar_distribution"),
        }
    )
    defs["rolling_maximum"] = obj(
        {
            "max_1_day_mm": {"type": "number", "minimum": 0},
            "max_3_day_mm": {"type": "number", "minimum": 0},
            "max_5_day_mm": {"type": "number", "minimum": 0},
            "year": {"type": "integer", "minimum": 1980, "maximum": 2025},
        }
    )
    defs["precipitation_coverage"] = obj(
        {
            "expected_days": ref("nonnegative_integer"),
            "missing_days": ref("nonnegative_integer"),
            "missing_gap_runs": ref("nonnegative_integer"),
            "observed_precip_days": ref("nonnegative_integer"),
        }
    )
    defs["precipitation_structure"] = obj(
        {
            "adjacent_wet_day_amount": ref("corr_pair"),
            "annual_max_1_day_mm": ref("scalar_distribution"),
            "annual_max_3_day_mm": ref("scalar_distribution"),
            "annual_max_5_day_mm": ref("scalar_distribution"),
            "annual_rolling_maxima": {
                "type": "array",
                "maxItems": 46,
                "items": ref("rolling_maximum"),
            },
            "coverage": ref("precipitation_coverage"),
            "dry_spells_days": ref("spell_distribution"),
            "threshold_mm": {"const": 1.0},
            "wet_day_amount_mm": ref("scalar_distribution"),
            "wet_spells_days": ref("spell_distribution"),
        }
    )
    defs["storm_descriptors_unavailable"] = obj(
        {
            "availability": {"const": "unavailable"},
            "reason": {
                "const": "daily Daymet/GHCN sources do not contain duration, time-to-peak fraction, or peak-intensity ratio"
            },
        }
    )

    defs["freezing_precipitation_fraction"] = obj(
        {
            "fraction": ref("nullable_fraction"),
            "freezing_air_day_count": ref("nonnegative_integer"),
            "n_days": ref("nonnegative_integer"),
            "precipitation_on_freezing_air_days_mm": ref("nullable_nonnegative_number"),
            "total_precipitation_mm": ref("nullable_nonnegative_number"),
        }
    )
    defs["months_freezing_precipitation_fraction"] = months(
        "freezing_precipitation_fraction"
    )
    defs["count_dispersion"] = obj(
        {
            "cv": ref("nullable_nonnegative_number"),
            "mean": ref("nullable_nonnegative_number"),
            "n_years": ref("nonnegative_integer"),
            "sd": ref("nullable_nonnegative_number"),
        }
    )
    defs["year_winter_air_temperature_proxy"] = obj(
        {
            "complete_year": {"type": "boolean"},
            "freeze_thaw_air_temperature_proxy_cycles": ref("nonnegative_integer"),
            "n_days": ref("nonnegative_integer"),
            "precipitation_on_freezing_air_days": ref(
                "freezing_precipitation_fraction"
            ),
            "year": {"type": "integer", "minimum": 1980, "maximum": 2025},
        }
    )
    defs["winter_air_temperature_proxies"] = obj(
        {
            "by_month": ref("months_freezing_precipitation_fraction"),
            "djf_r1mm_precip_mean_air_temperature": ref("corr_pair"),
            "freeze_thaw_air_temperature_proxy_cycles": ref("count_dispersion"),
            "per_year": {
                "type": "array",
                "minItems": 16,
                "maxItems": 46,
                "items": ref("year_winter_air_temperature_proxy"),
            },
            "precipitation_on_freezing_air_days": ref(
                "freezing_precipitation_fraction"
            ),
        }
    )

    defs["period_bounds"] = obj(
        {
            "end_year": {"type": "integer", "minimum": 1980, "maximum": 2025},
            "start_year": {
                "type": "integer",
                "minimum": 1980,
                "maximum": 2025,
            },
        }
    )
    defs["target_period"] = obj(
        {
            "annual": ref("annual_targets"),
            "dependence": ref("dependence"),
            "monthly": ref("months_monthly_targets"),
            "period": ref("period_bounds"),
            "precipitation_structure": ref("precipitation_structure"),
            "storm_descriptors": ref("storm_descriptors_unavailable"),
            "winter_air_temperature_proxies": ref("winter_air_temperature_proxies"),
        }
    )
    defs["target_periods"] = obj(
        {
            "evaluation": period_variant(2010, 2025),
            "fit": period_variant(1980, 2009),
            "full": period_variant(1980, 2025),
        }
    )

    defs["unavailable_source"] = obj(
        {
            "availability": {"const": "unavailable"},
            "reason": {
                "const": "Q3 station mapping absent or failed the completeness screen"
            },
        }
    )
    defs["daymet_source"] = available_source(
        "noleap_365", "^daymet-v4r1-[a-z]{2}[0-9]{6}$"
    )
    defs["ghcn_source"] = available_source(
        "proleptic_gregorian", "^ghcn-daily-USC[0-9]{8}-20260712$"
    )
    defs["station_parameter"] = obj(
        {
            "collection": {"const": "us-2015"},
            "collection_version": {"const": "2026.07"},
            "legacy_par_sha256": ref("sha256"),
            "model": {"const": "fixed_monthly_5_32_3"},
        }
    )
    defs["station"] = obj(
        {
            "catalog_elevation_ft": {"type": "number"},
            "latitude": {"type": "number", "minimum": -90, "maximum": 90},
            "longitude": {
                "type": "number",
                "minimum": -180,
                "maximum": 180,
            },
            "name": {"type": "string", "minLength": 1},
            "regime": {"enum": ["arid", "monsoonal", "humid", "cold", "fixture"]},
            "sources": obj(
                {
                    "daymet": ref("daymet_source"),
                    "ghcn": {"oneOf": [ref("ghcn_source"), ref("unavailable_source")]},
                }
            ),
            "station_id": {"enum": list(STATION_IDS)},
            "station_parameter": ref("station_parameter"),
        }
    )
    defs["station_collection"] = obj(
        {
            "archive_sha256": ref("sha256"),
            "catalog_sha256": ref("sha256"),
            "name": {"const": "us-2015"},
            "version": {"const": "2026.07"},
        }
    )

    properties = {
        "conventions": {
            "const": {
                "air_freezing_threshold_c": 0.0,
                "detrending": "OLS linear residual by integer year",
                "low_frequency": "centered DFT positive-frequency power fraction with period >= 4 years; contiguous annual series required",
                "precipitation_wet_day_threshold_mm": 1.0,
                "quantile": "empirical inverse-CDF nearest rank: sorted[ceil(p*n)-1]",
                "rolling_maxima": "consecutive source-calendar windows attributed to end year; distributions retain complete precipitation years",
            }
        },
        "corpus_id": {"const": "cligen-a5a-observed-v1"},
        "fixed_periods": {"const": FIXED_PERIODS},
        "metrics_version": {"const": 3},
        "observed_target_corpus_schema_version": {"const": 1},
        "source_manifest_sha256": ref("sha256"),
        "station_collection": ref("station_collection"),
        "stations": {
            "type": "array",
            "minItems": 17,
            "maxItems": 17,
            "uniqueItems": True,
            "items": ref("station"),
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://raw.githubusercontent.com/rogerlew/cligen-rs/main/docs/specifications/observed-target-corpus-v1.schema.json",
        "title": "CLIGEN A5 observed-target corpus revision 1",
        **obj(properties),
        "$defs": defs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    script = Path(__file__).resolve()
    repo = script.parents[5]
    output = (
        args.output
        or repo / "docs/specifications/observed-target-corpus-v1.schema.json"
    )
    write_canonical_json(output, build_schema())
    print(output)


if __name__ == "__main__":
    main()
