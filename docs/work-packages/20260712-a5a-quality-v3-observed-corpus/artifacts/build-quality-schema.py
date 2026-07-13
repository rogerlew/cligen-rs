#!/usr/bin/env python3
"""Build the envelope-2/metrics-3 quality schema from frozen v2.

The historical envelope-2/metrics-2 resource is an input, never rewritten.
This generator asserts its A1 SHA-256 before replacing only metric-vector
definitions and the top-level metrics constant/identity.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SPECS = ROOT / "docs" / "specifications"
SOURCE = SPECS / "quality-report-v2.schema.json"
DESTINATION = SPECS / "quality-report-s2-m3.schema.json"
RUNTIME_SCHEMA_DIR = ROOT / "crates" / "cligen" / "schemas"
RUNTIME_QUALITY = RUNTIME_SCHEMA_DIR / DESTINATION.name
PUBLIC_PROVENANCE = SPECS / "provenance-v1.schema.json"
RUNTIME_PROVENANCE = RUNTIME_SCHEMA_DIR / PUBLIC_PROVENANCE.name
SOURCE_SHA256 = "3b8234ecfd9fa544c27bd203ce162e009662f390302872ca2b4a6f47c13f4db9"
PROVENANCE_SHA256 = "c1f2ef184547f6a6e11b1a62472dd40d860443cb69287e5c29b6c102aecdc941"
MONTHS = [
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
]


def ref(name: str) -> dict:
    return {"$ref": f"#/$defs/{name}"}


def object_schema(properties: dict) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def add_count_states(
    schema: dict, count_field: str, states: list[tuple[dict, dict]]
) -> dict:
    """Add Draft-2020-12 count-conditioned property constraints."""
    schema["allOf"] = [
        {
            "if": {
                "required": [count_field],
                "properties": {count_field: count_constraint},
            },
            "then": {"properties": property_constraints},
        }
        for count_constraint, property_constraints in states
    ]
    return schema


def null_properties(names: list[str]) -> dict:
    return {name: {"type": "null"} for name in names}


def number_properties(names: list[str], definition: str) -> dict:
    return {name: ref(definition) for name in names}


def months(definition: str) -> dict:
    return object_schema({month: ref(definition) for month in MONTHS})


def fixed_array(item: dict, size: int = 12) -> dict:
    return {"type": "array", "minItems": size, "maxItems": size, "items": item}


def fixed_matrix(item: dict) -> dict:
    return fixed_array(fixed_array(item))


def nullable_number(minimum=None, maximum=None) -> dict:
    number = {"type": "number"}
    if minimum is not None:
        number["minimum"] = minimum
    if maximum is not None:
        number["maximum"] = maximum
    return {"anyOf": [number, {"type": "null"}]}


def define_interannual(defs: dict) -> None:
    defs["nullable_nonnegative_number"] = nullable_number(0)
    defs["nullable_fraction"] = nullable_number(0, 1)
    defs["nullable_correlation"] = nullable_number(-1, 1)
    dispersion = object_schema(
        {
            "mean": ref("nullable_nonnegative_number"),
            "sd": ref("nullable_nonnegative_number"),
            "cv": ref("nullable_nonnegative_number"),
            "n_years": ref("nonnegative_integer"),
        }
    )
    defs["dispersion"] = add_count_states(
        dispersion,
        "n_years",
        [
            ({"const": 0}, null_properties(["mean", "sd", "cv"])),
            (
                {"const": 1},
                {
                    "mean": {"type": "number", "minimum": 0},
                    "sd": {"type": "null"},
                    "cv": {"type": "null"},
                },
            ),
            (
                {"minimum": 2},
                {
                    "mean": {"type": "number", "minimum": 0},
                    "sd": {"type": "number", "minimum": 0},
                },
            ),
        ],
    )
    location_dispersion = object_schema(
        {
            "mean": ref("nullable_number"),
            "sd": ref("nullable_nonnegative_number"),
            "n_years": ref("nonnegative_integer"),
        }
    )
    defs["location_dispersion"] = add_count_states(
        location_dispersion,
        "n_years",
        [
            ({"const": 0}, null_properties(["mean", "sd"])),
            (
                {"const": 1},
                {"mean": {"type": "number"}, "sd": {"type": "null"}},
            ),
            (
                {"minimum": 2},
                {
                    "mean": {"type": "number"},
                    "sd": {"type": "number", "minimum": 0},
                },
            ),
        ],
    )
    defs["annual_stats"] = object_schema(
        {
            "precip_total_mm": ref("dispersion"),
            "trace_wet_day_count": ref("dispersion"),
            "r1mm_wet_day_count": ref("dispersion"),
            "max_daily_precip_mm": ref("dispersion"),
            "tmax_mean_c": ref("location_dispersion"),
            "tmin_mean_c": ref("location_dispersion"),
        }
    )
    defs["monthly_climate"] = object_schema(
        {
            "precip_total_mm": ref("dispersion"),
            "trace_wet_day_count": ref("dispersion"),
            "r1mm_wet_day_count": ref("dispersion"),
            "trace_wet_day_mean_amount_mm": ref("dispersion"),
            "r1mm_wet_day_mean_amount_mm": ref("dispersion"),
            "tmax_mean_c": ref("location_dispersion"),
            "tmin_mean_c": ref("location_dispersion"),
        }
    )
    defs["months_monthly_climate"] = months("monthly_climate")
    defs["month_dependence_matrix"] = object_schema(
        {
            "covariance": fixed_matrix(ref("nullable_number")),
            "pearson_correlation": fixed_matrix(ref("nullable_correlation")),
            "n_pairs": fixed_matrix(ref("nonnegative_integer")),
        }
    )
    defs["climate_anomaly_correlations"] = object_schema(
        {
            "precip_tmax": ref("corr_pair"),
            "precip_tmin": ref("corr_pair"),
            "tmax_tmin": ref("corr_pair"),
        }
    )
    defs["months_climate_anomaly_correlations"] = months("climate_anomaly_correlations")
    defs["series_dependence"] = object_schema(
        {
            "lag_one": ref("corr_pair"),
            "period_ge_4y_power_fraction": ref("nullable_fraction"),
            "n_years": ref("nonnegative_integer"),
        }
    )
    defs["annual_dependence"] = object_schema(
        {
            "precip_total_mm": ref("series_dependence"),
            "tmax_mean_c": ref("series_dependence"),
            "tmin_mean_c": ref("series_dependence"),
        }
    )
    defs["interannual_dependence"] = object_schema(
        {
            "precip_cross_month": ref("month_dependence_matrix"),
            "tmax_cross_month": ref("month_dependence_matrix"),
            "tmin_cross_month": ref("month_dependence_matrix"),
            "cross_variable_by_month": ref("months_climate_anomaly_correlations"),
            "annual": ref("annual_dependence"),
        }
    )
    defs["interannual"] = object_schema(
        {
            "annual": ref("annual_stats"),
            "monthly": ref("months_monthly_climate"),
            "dependence": ref("interannual_dependence"),
            "by_decade": {"type": "array", "items": ref("interannual_decade")},
        }
    )
    defs["interannual_decade"] = object_schema(
        {
            "decade": ref("nonnegative_integer"),
            "start_year": {"type": "integer"},
            "n_years": ref("nonnegative_integer"),
            "annual": ref("annual_stats"),
            "monthly": ref("months_monthly_climate"),
        }
    )


def define_covariation(defs: dict) -> None:
    corr_pair = object_schema(
        {
            "pearson": ref("nullable_correlation"),
            "spearman": ref("nullable_correlation"),
            "n": ref("nonnegative_integer"),
        }
    )
    defs["corr_pair"] = add_count_states(
        corr_pair,
        "n",
        [
            (
                {"maximum": 1},
                null_properties(["pearson", "spearman"]),
            )
        ],
    )
    defs["corr_set"] = object_schema(
        {
            "amount_duration": ref("corr_pair"),
            "amount_peak_intensity_ratio": ref("corr_pair"),
            "duration_radiation": ref("corr_pair"),
        }
    )
    freezing_fraction = object_schema(
        {
            "fraction": ref("nullable_fraction"),
            "precipitation_on_freezing_air_days_mm": ref("nullable_nonnegative_number"),
            "total_precipitation_mm": ref("nullable_nonnegative_number"),
            "freezing_air_day_count": ref("nonnegative_integer"),
            "n_days": ref("nonnegative_integer"),
        }
    )
    defs["freezing_precipitation_fraction"] = add_count_states(
        freezing_fraction,
        "n_days",
        [
            (
                {"const": 0},
                null_properties(
                    [
                        "fraction",
                        "precipitation_on_freezing_air_days_mm",
                        "total_precipitation_mm",
                    ]
                ),
            ),
            (
                {"minimum": 1},
                {
                    "precipitation_on_freezing_air_days_mm": {
                        "type": "number",
                        "minimum": 0,
                    },
                    "total_precipitation_mm": {"type": "number", "minimum": 0},
                },
            ),
        ],
    )
    defs["months_freezing_precipitation_fraction"] = months(
        "freezing_precipitation_fraction"
    )
    defs["year_winter_air_temperature_proxy"] = object_schema(
        {
            "year": {"type": "integer"},
            "n_days": ref("nonnegative_integer"),
            "complete_year": {"type": "boolean"},
            "precipitation_on_freezing_air_days": ref(
                "freezing_precipitation_fraction"
            ),
            "freeze_thaw_air_temperature_proxy_cycles": ref("nonnegative_integer"),
        }
    )
    defs["winter_air_temperature_proxies"] = object_schema(
        {
            "precipitation_on_freezing_air_days": ref(
                "freezing_precipitation_fraction"
            ),
            "by_month": ref("months_freezing_precipitation_fraction"),
            "djf_r1mm_precip_mean_air_temperature": ref("corr_pair"),
            "freeze_thaw_air_temperature_proxy_cycles": ref("dispersion"),
            "per_year": {
                "type": "array",
                "items": ref("year_winter_air_temperature_proxy"),
            },
        }
    )
    defs["covariation"] = object_schema(
        {
            "whole_run": ref("corr_set"),
            "months": ref("months_corr_set"),
            "radiation_wet_dry_contrast": ref("months_contrast"),
            "daily_range_mean_c": ref("daily_range_mean"),
            "winter_air_temperature_proxies": ref("winter_air_temperature_proxies"),
            "by_decade": {"type": "array", "items": ref("covariation_decade")},
        }
    )


def define_tails(defs: dict) -> None:
    statistics = ["mean", "sd", "p50", "p90", "p95", "p99", "max"]

    def distribution_schema(value_definition: str) -> dict:
        schema = object_schema(
            {
                "n": ref("nonnegative_integer"),
                **number_properties(statistics, value_definition),
            }
        )
        return add_count_states(
            schema,
            "n",
            [
                ({"const": 0}, null_properties(statistics)),
                (
                    {"const": 1},
                    {
                        **{
                            name: {
                                "type": "number",
                                "minimum": 0,
                                **(
                                    {"maximum": 1}
                                    if value_definition == "nullable_fraction"
                                    else {}
                                ),
                            }
                            for name in statistics
                            if name != "sd"
                        },
                        "sd": {"type": "null"},
                    },
                ),
                (
                    {"minimum": 2},
                    {
                        name: {
                            "type": "number",
                            "minimum": 0,
                            **(
                                {"maximum": 1}
                                if value_definition == "nullable_fraction"
                                else {}
                            ),
                        }
                        for name in statistics
                    },
                ),
            ],
        )

    defs["scalar_distribution"] = distribution_schema("nullable_nonnegative_number")
    defs["fraction_distribution"] = distribution_schema("nullable_fraction")
    defs["months_scalar_distribution"] = months("scalar_distribution")
    defs["spell_distribution"] = object_schema(
        {
            "whole_run": ref("scalar_distribution"),
            "by_start_month": ref("months_scalar_distribution"),
        }
    )
    defs["threshold_precipitation_structure"] = object_schema(
        {
            "wet_spells_days": ref("spell_distribution"),
            "dry_spells_days": ref("spell_distribution"),
            "wet_day_amount_mm": ref("scalar_distribution"),
            "adjacent_wet_day_amount": ref("corr_pair"),
            "annual_max_1_day_mm": ref("scalar_distribution"),
            "annual_max_3_day_mm": ref("scalar_distribution"),
            "annual_max_5_day_mm": ref("scalar_distribution"),
        }
    )
    defs["precipitation_structure"] = object_schema(
        {
            "trace_positive": ref("threshold_precipitation_structure"),
            "r1mm": ref("threshold_precipitation_structure"),
        }
    )
    defs["storm_descriptor_distributions"] = object_schema(
        {
            "depth_mm": ref("scalar_distribution"),
            "duration_h": ref("scalar_distribution"),
            "time_to_peak_fraction": ref("fraction_distribution"),
            "peak_intensity_ratio": ref("scalar_distribution"),
        }
    )
    defs["storm_descriptor_dependence"] = object_schema(
        {
            "depth_duration": ref("corr_pair"),
            "depth_time_to_peak": ref("corr_pair"),
            "depth_peak_intensity_ratio": ref("corr_pair"),
            "duration_time_to_peak": ref("corr_pair"),
            "duration_peak_intensity_ratio": ref("corr_pair"),
            "time_to_peak_peak_intensity_ratio": ref("corr_pair"),
        }
    )
    defs["storm_descriptors"] = object_schema(
        {
            "wet_event_days": ref("nonnegative_integer"),
            "included_event_days": ref("nonnegative_integer"),
            "excluded_event_days": ref("nonnegative_integer"),
            "distributions": ref("storm_descriptor_distributions"),
            "dependence": ref("storm_descriptor_dependence"),
        }
    )
    defs["year_tails"] = object_schema(
        {
            "year": {"type": "integer"},
            "n_days": ref("nonnegative_integer"),
            "complete_year": {"type": "boolean"},
            "max_1_day_precip_mm": ref("nullable_nonnegative_number"),
            "max_3_day_precip_mm": ref("nullable_nonnegative_number"),
            "max_5_day_precip_mm": ref("nullable_nonnegative_number"),
            "wet_event_day_count": ref("nonnegative_integer"),
            "max_peak_intensity_ratio": ref("nullable_number"),
            "longest_wet_spell_days": ref("nonnegative_integer"),
            "longest_dry_spell_days": ref("nonnegative_integer"),
        }
    )
    defs["top_event"] = object_schema(
        {
            "rank": {"type": "integer", "minimum": 1, "maximum": 5},
            "year": {"type": "integer"},
            "month": {"type": "integer", "minimum": 1, "maximum": 12},
            "day": {"type": "integer", "minimum": 1, "maximum": 31},
            "row_index": {"type": "integer", "minimum": 1},
            "precip_mm": {"type": "number", "exclusiveMinimum": 0},
            # These are raw finite fields from depth-ranked wet rows.
            # Descriptor validity bounds apply only to storm_descriptors,
            # which reports included and excluded event counts.
            "duration_h": {"type": "number"},
            "time_to_peak_fraction": {"type": "number"},
            "peak_intensity_ratio": {"type": "number"},
        }
    )
    defs["tails"] = object_schema(
        {
            "per_year": {"type": "array", "minItems": 1, "items": ref("year_tails")},
            "top_events": {"type": "array", "maxItems": 5, "items": ref("top_event")},
            "precipitation_structure": ref("precipitation_structure"),
            "storm_descriptors": ref("storm_descriptors"),
        }
    )


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != SOURCE_SHA256:
        raise SystemExit(f"frozen v2 schema hash mismatch: {actual}")
    schema = json.loads(source_bytes)
    schema["$id"] = (
        "https://raw.githubusercontent.com/rogerlew/cligen-rs/main/"
        "docs/specifications/quality-report-s2-m3.schema.json"
    )
    schema["title"] = "cligen-rs quality report envelope 2, metrics version 3"
    schema["description"] = (
        "SPEC-QUALITY-REPORT revision-8 combination schema. Report-envelope "
        "and metric-vector versions are independent."
    )
    schema["properties"]["metrics_version"] = {"const": 3}
    defs = schema["$defs"]
    define_interannual(defs)
    define_covariation(defs)
    define_tails(defs)
    defs.pop("monthly_sd_cell", None)
    defs.pop("months_monthly_sd", None)
    rendered = json.dumps(schema, indent=2) + "\n"
    DESTINATION.write_text(rendered, encoding="utf-8")
    RUNTIME_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_QUALITY.write_text(rendered, encoding="utf-8")
    provenance = PUBLIC_PROVENANCE.read_bytes()
    actual_provenance_sha = hashlib.sha256(provenance).hexdigest()
    if actual_provenance_sha != PROVENANCE_SHA256:
        raise ValueError(
            "frozen provenance schema changed: "
            f"{actual_provenance_sha} != {PROVENANCE_SHA256}"
        )
    RUNTIME_PROVENANCE.write_bytes(provenance)
    print(hashlib.sha256(DESTINATION.read_bytes()).hexdigest(), DESTINATION)


if __name__ == "__main__":
    main()
