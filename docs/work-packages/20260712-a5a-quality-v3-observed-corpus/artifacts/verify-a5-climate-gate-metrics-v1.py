#!/usr/bin/env python3
"""Validate the frozen A5 climate-gate metric-cell manifest."""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = ROOT / "docs/specifications/a5-climate-gate-metrics-v1.json"
DEFAULT_SCHEMA = ROOT / "docs/specifications/a5-climate-gate-metrics-v1.schema.json"

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
CORRELATIONS = ["pearson", "spearman"]
DISTRIBUTION_STATS = ["mean", "sd", "p50", "p90", "p95", "p99", "max"]
EXPECTED_CANONICAL_MANIFEST_SHA256 = (
    "f2ad21f350d7723fc427eb9e8af09950777fdffa68856891410726a179d3c1ae"
)

EXPECTED_SURFACES = {
    "daymet_evaluation_raw": (
        "daymet_v4_r1",
        "evaluation_2010_2025",
        "raw",
        "required",
        "$.stations[@station_id={station_id}].sources.daymet.periods.evaluation",
    ),
    "daymet_evaluation_detrended": (
        "daymet_v4_r1",
        "evaluation_2010_2025",
        "ols_linear_residual_by_integer_year",
        "required",
        "$.stations[@station_id={station_id}].sources.daymet.periods.evaluation",
    ),
    "daymet_full_raw": (
        "daymet_v4_r1",
        "full_1980_2025",
        "raw",
        "required",
        "$.stations[@station_id={station_id}].sources.daymet.periods.full",
    ),
    "daymet_full_detrended": (
        "daymet_v4_r1",
        "full_1980_2025",
        "ols_linear_residual_by_integer_year",
        "required",
        "$.stations[@station_id={station_id}].sources.daymet.periods.full",
    ),
    "ghcn_evaluation_raw": (
        "ghcn_daily_snapshot_20260712",
        "evaluation_2010_2025",
        "raw",
        "explicit_available_only",
        "$.stations[@station_id={station_id}].sources.ghcn.periods.evaluation",
    ),
    "ghcn_evaluation_detrended": (
        "ghcn_daily_snapshot_20260712",
        "evaluation_2010_2025",
        "ols_linear_residual_by_integer_year",
        "explicit_available_only",
        "$.stations[@station_id={station_id}].sources.ghcn.periods.evaluation",
    ),
    "ghcn_full_raw": (
        "ghcn_daily_snapshot_20260712",
        "full_1980_2025",
        "raw",
        "explicit_available_only",
        "$.stations[@station_id={station_id}].sources.ghcn.periods.full",
    ),
    "ghcn_full_detrended": (
        "ghcn_daily_snapshot_20260712",
        "full_1980_2025",
        "ols_linear_residual_by_integer_year",
        "explicit_available_only",
        "$.stations[@station_id={station_id}].sources.ghcn.periods.full",
    ),
    "report_embedded_station_parameter": (
        "quality_report_embedded_station_parameter_target",
        "generated_run",
        "not_applicable",
        "required",
        "$.par_convergence",
    ),
    "faithful_off_baseline": (
        "faithful_5_32_3_qc_filter_off",
        "matched_horizon_and_replicate_matrix",
        "not_applicable",
        "required",
        "$",
    ),
}

# (expanded count, group, family, gate ids, distance, dimensions,
# generated path, target path)
EXPECTED_TEMPLATES: dict[str, tuple[Any, ...]] = {
    "b_annual_nonnegative_dispersion": (
        9,
        "B",
        "interannual_annual_dispersion",
        [1, 2],
        "absolute_relative",
        {
            "statistic": ["mean", "sd", "cv"],
            "variable": [
                "precip_total_mm",
                "r1mm_wet_day_count",
                "max_daily_precip_mm",
            ],
        },
        "$.interannual.annual.{variable}.{statistic}",
        "{target_prefix}.annual.{variable}.{statistic}",
    ),
    "b_annual_temperature_dispersion": (
        2,
        "B",
        "interannual_annual_dispersion",
        [1, 2],
        "absolute_relative",
        {"statistic": ["sd"], "variable": ["tmax_mean_c", "tmin_mean_c"]},
        "$.interannual.annual.{variable}.{statistic}",
        "{target_prefix}.annual.{variable}.{statistic}",
    ),
    "b_monthly_nonnegative_dispersion": (
        108,
        "B",
        "interannual_monthly_dispersion",
        [1, 2],
        "absolute_relative",
        {
            "month": "canonical_sets.months",
            "statistic": ["mean", "sd", "cv"],
            "variable": [
                "precip_total_mm",
                "r1mm_wet_day_count",
                "r1mm_wet_day_mean_amount_mm",
            ],
        },
        "$.interannual.monthly.{month}.{variable}.{statistic}",
        "{target_prefix}.monthly.{month}.{variable}.{statistic}",
    ),
    "b_monthly_temperature_dispersion": (
        24,
        "B",
        "interannual_monthly_dispersion",
        [1, 2],
        "absolute_relative",
        {
            "month": "canonical_sets.months",
            "statistic": ["sd"],
            "variable": ["tmax_mean_c", "tmin_mean_c"],
        },
        "$.interannual.monthly.{month}.{variable}.{statistic}",
        "{target_prefix}.monthly.{month}.{variable}.{statistic}",
    ),
    "b_cross_month_dependence": (
        198,
        "B",
        "interannual_cross_month_dependence",
        [1, 2],
        "absolute_difference",
        {
            "matrix_statistic": ["pearson_correlation"],
            "month_pair": "canonical_sets.upper_off_diagonal_month_pairs",
            "variable": [
                "precip_cross_month",
                "tmax_cross_month",
                "tmin_cross_month",
            ],
        },
        "$.interannual.dependence.{variable}.{matrix_statistic}[{row}][{col}]",
        "{target_prefix}.dependence.raw.{variable}.{matrix_statistic}[{row}][{col}]",
    ),
    "b_cross_variable_dependence": (
        72,
        "B",
        "interannual_cross_variable_dependence",
        [1, 2],
        "absolute_difference",
        {
            "correlation_statistic": "canonical_sets.correlation_statistics",
            "month": "canonical_sets.months",
            "variable": ["precip_tmax", "precip_tmin", "tmax_tmin"],
        },
        "$.interannual.dependence.cross_variable_by_month.{month}.{variable}.{correlation_statistic}",
        "{target_prefix}.dependence.raw.cross_variable_by_month.{month}.{variable}.{correlation_statistic}",
    ),
    "b_annual_lag_one_dependence": (
        6,
        "B",
        "interannual_annual_dependence",
        [1, 2],
        "absolute_difference",
        {
            "correlation_statistic": "canonical_sets.correlation_statistics",
            "variable": ["precip_total_mm", "tmax_mean_c", "tmin_mean_c"],
        },
        "$.interannual.dependence.annual.{variable}.lag_one.{correlation_statistic}",
        "{target_prefix}.dependence.raw.annual.{variable}.lag_one.{correlation_statistic}",
    ),
    "b_annual_low_frequency_fraction": (
        3,
        "B",
        "interannual_low_frequency",
        [1, 2],
        "absolute_difference",
        {"variable": ["precip_total_mm", "tmax_mean_c", "tmin_mean_c"]},
        "$.interannual.dependence.annual.{variable}.period_ge_4y_power_fraction",
        "{target_prefix}.dependence.raw.annual.{variable}.period_ge_4y_power_fraction",
    ),
    "a_monthly_positive_contract": (
        36,
        "A",
        "monthly_station_contract",
        [3],
        "absolute_relative",
        {
            "month": "canonical_sets.months",
            "variable": [
                "precip_wet_mean_mm",
                "precip_wet_sd_mm",
                "precip_wet_skew",
            ],
        },
        "$.par_convergence.{variable}.{month}.generated",
        "$.par_convergence.{variable}.{month}.target",
    ),
    "a_monthly_probability_contract": (
        36,
        "A",
        "monthly_station_contract",
        [3],
        "absolute_difference",
        {
            "month": "canonical_sets.months",
            "variable": ["wet_day_fraction", "p_ww", "p_wd"],
        },
        "$.par_convergence.{variable}.{month}.generated",
        "$.par_convergence.{variable}.{month}.target",
    ),
    "a_monthly_tmax_location_contract": (
        12,
        "A",
        "monthly_station_contract",
        [3],
        "absolute_difference",
        {"month": "canonical_sets.months"},
        "$.par_convergence.tmax_mean_c.{month}.generated",
        "$.par_convergence.tmax_mean_c.{month}.target",
    ),
    "a_monthly_tmin_location_contract": (
        12,
        "A",
        "monthly_station_contract",
        [3],
        "absolute_difference",
        {"month": "canonical_sets.months"},
        "$.par_convergence.tmin_mean_c.{month}.generated",
        "$.par_convergence.tmin_mean_c.{month}.target",
    ),
    "a_monthly_temperature_scale_contract": (
        24,
        "A",
        "monthly_station_contract",
        [3],
        "absolute_relative",
        {
            "month": "canonical_sets.months",
            "variable": ["tmax_sd_c", "tmin_sd_c"],
        },
        "$.par_convergence.{variable}.{month}.generated",
        "$.par_convergence.{variable}.{month}.target",
    ),
    "d_r1mm_spell_whole_run": (
        14,
        "D",
        "precipitation_structure",
        [4],
        "absolute_relative",
        {
            "statistic": "canonical_sets.distribution_statistics",
            "variable": ["wet_spells_days", "dry_spells_days"],
        },
        "$.tails.precipitation_structure.r1mm.{variable}.whole_run.{statistic}",
        "{target_prefix}.precipitation_structure.{variable}.whole_run.{statistic}",
    ),
    "d_r1mm_spell_by_month": (
        168,
        "D",
        "precipitation_structure",
        [4],
        "absolute_relative",
        {
            "month": "canonical_sets.months",
            "statistic": "canonical_sets.distribution_statistics",
            "variable": ["wet_spells_days", "dry_spells_days"],
        },
        "$.tails.precipitation_structure.r1mm.{variable}.by_start_month.{month}.{statistic}",
        "{target_prefix}.precipitation_structure.{variable}.by_start_month.{month}.{statistic}",
    ),
    "d_r1mm_amount_persistence": (
        2,
        "D",
        "precipitation_structure",
        [4],
        "absolute_difference",
        {"correlation_statistic": "canonical_sets.correlation_statistics"},
        "$.tails.precipitation_structure.r1mm.adjacent_wet_day_amount.{correlation_statistic}",
        "{target_prefix}.precipitation_structure.adjacent_wet_day_amount.{correlation_statistic}",
    ),
    "d_r1mm_rolling_extremes": (
        21,
        "D",
        "precipitation_structure",
        [4],
        "absolute_relative",
        {
            "statistic": "canonical_sets.distribution_statistics",
            "variable": [
                "annual_max_1_day_mm",
                "annual_max_3_day_mm",
                "annual_max_5_day_mm",
            ],
        },
        "$.tails.precipitation_structure.r1mm.{variable}.{statistic}",
        "{target_prefix}.precipitation_structure.{variable}.{statistic}",
    ),
    "d_descriptor_time_to_peak_distribution": (
        7,
        "D",
        "descriptor_guard",
        [5],
        "absolute_difference",
        {
            "statistic": "canonical_sets.distribution_statistics",
            "variable": ["time_to_peak_fraction"],
        },
        "$.tails.storm_descriptors.distributions.{variable}.{statistic}",
        "$.tails.storm_descriptors.distributions.{variable}.{statistic}",
    ),
    "d_descriptor_peak_ratio_distribution": (
        7,
        "D",
        "descriptor_guard",
        [5],
        "absolute_relative",
        {
            "statistic": "canonical_sets.distribution_statistics",
            "variable": ["peak_intensity_ratio"],
        },
        "$.tails.storm_descriptors.distributions.{variable}.{statistic}",
        "$.tails.storm_descriptors.distributions.{variable}.{statistic}",
    ),
    "d_descriptor_dependence": (
        10,
        "D",
        "descriptor_guard",
        [5],
        "absolute_difference",
        {
            "correlation_statistic": "canonical_sets.correlation_statistics",
            "variable": [
                "depth_time_to_peak",
                "depth_peak_intensity_ratio",
                "duration_time_to_peak",
                "duration_peak_intensity_ratio",
                "time_to_peak_peak_intensity_ratio",
            ],
        },
        "$.tails.storm_descriptors.dependence.{variable}.{correlation_statistic}",
        "$.tails.storm_descriptors.dependence.{variable}.{correlation_statistic}",
    ),
    "c_winter_freezing_precipitation_fraction": (
        1,
        "C",
        "winter_air_temperature_proxies",
        [6],
        "absolute_difference",
        {},
        "$.covariation.winter_air_temperature_proxies.precipitation_on_freezing_air_days.fraction",
        "{target_prefix}.winter_air_temperature_proxies.precipitation_on_freezing_air_days.fraction",
    ),
    "c_winter_monthly_freezing_precipitation_fraction": (
        12,
        "C",
        "winter_air_temperature_proxies",
        [6],
        "absolute_difference",
        {"month": "canonical_sets.months"},
        "$.covariation.winter_air_temperature_proxies.by_month.{month}.fraction",
        "{target_prefix}.winter_air_temperature_proxies.by_month.{month}.fraction",
    ),
    "c_winter_djf_dependence": (
        2,
        "C",
        "winter_air_temperature_proxies",
        [6],
        "absolute_difference",
        {"correlation_statistic": "canonical_sets.correlation_statistics"},
        "$.covariation.winter_air_temperature_proxies.djf_r1mm_precip_mean_air_temperature.{correlation_statistic}",
        "{target_prefix}.winter_air_temperature_proxies.djf_r1mm_precip_mean_air_temperature.{correlation_statistic}",
    ),
    "c_winter_freeze_thaw_cycle_dispersion": (
        3,
        "C",
        "winter_air_temperature_proxies",
        [6],
        "absolute_relative",
        {"statistic": ["mean", "sd", "cv"]},
        "$.covariation.winter_air_temperature_proxies.freeze_thaw_air_temperature_proxy_cycles.{statistic}",
        "{target_prefix}.winter_air_temperature_proxies.freeze_thaw_air_temperature_proxy_cycles.{statistic}",
    ),
}

EXPECTED_GATE_COUNTS = {1: 422, 2: 422, 3: 120, 4: 205, 5: 24, 6: 18, 7: 0}
EXPECTED_GATE_NAMES = {
    1: ("primary_low_frequency_improvement", "primary_observed_distance"),
    2: ("independent_source_sensitivity", "secondary_observed_distance"),
    3: ("monthly_contract_preservation", "station_parameter_contract_guard"),
    4: ("precipitation_structure_guard", "primary_observed_distance"),
    5: ("descriptor_no_regression", "baseline_envelope_guard"),
    6: ("winter_climate_proxy_guard", "primary_observed_distance"),
    7: ("no_missing_evidence", "evidence_completeness"),
}
EXPECTED_NORMALIZATION_PATHS = {
    "a_monthly_tmax_location_contract": "$.par_convergence.tmax_sd_c.{month}.target",
    "a_monthly_tmin_location_contract": "$.par_convergence.tmin_sd_c.{month}.target",
}


class ValidationError(ValueError):
    """Manifest validation failure."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def strict_json_loads(text: str) -> Any:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise ValidationError(f"non-finite JSON token: {value}")

    def parse_finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValidationError(f"JSON float overflows finite range: {value}")
        return parsed

    return json.loads(
        text,
        object_pairs_hook=pairs_hook,
        parse_constant=reject_constant,
        parse_float=parse_finite_float,
    )


def load_json(path: Path) -> Any:
    return strict_json_loads(path.read_text(encoding="utf-8"))


def canonical_content_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, separators=(",", ":"), sort_keys=True, ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def dimension_values(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    known = {
        "canonical_sets.months": MONTHS,
        "canonical_sets.correlation_statistics": CORRELATIONS,
        "canonical_sets.distribution_statistics": DISTRIBUTION_STATS,
        "canonical_sets.upper_off_diagonal_month_pairs": [
            {"row": row, "col": col} for row in range(12) for col in range(row + 1, 12)
        ],
    }
    require(value in known, f"unknown dimension source: {value}")
    return known[value]


def substitutions(dimensions: dict[str, Any]) -> list[dict[str, Any]]:
    if not dimensions:
        return [{}]
    keys = list(dimensions)
    choices = [dimension_values(dimensions[key]) for key in keys]
    rows: list[dict[str, Any]] = []
    for values in itertools.product(*choices):
        row: dict[str, Any] = {}
        for key, value in zip(keys, values, strict=True):
            if key == "month_pair":
                row.update(value)
            else:
                row[key] = value
        rows.append(row)
    return rows


def substitute(template: str, values: dict[str, Any]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def statistic_for(template: dict[str, Any], values: dict[str, Any]) -> str:
    for key in ("statistic", "matrix_statistic", "correlation_statistic"):
        if key in values:
            return str(values[key])
    return str(template["statistic_selection"])


def variable_for(template: dict[str, Any], values: dict[str, Any]) -> str:
    assignment = template["variable_assignment"]
    return (
        str(values["variable"]) if assignment == "dimensions.variable" else assignment
    )


def validate_manifest(
    manifest: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    Draft202012Validator.check_schema(schema)
    schema_errors = sorted(
        Draft202012Validator(schema).iter_errors(manifest),
        key=lambda error: list(error.path),
    )
    require(
        not schema_errors,
        f"schema: {schema_errors[0].message}" if schema_errors else "",
    )
    require(
        canonical_content_sha256(manifest) == EXPECTED_CANONICAL_MANIFEST_SHA256,
        "normative manifest content differs from frozen version 1",
    )

    require(manifest["canonical_sets"]["months"] == MONTHS, "month order changed")
    require(
        manifest["canonical_sets"]["correlation_statistics"] == CORRELATIONS,
        "correlation statistic set changed",
    )
    require(
        manifest["canonical_sets"]["distribution_statistics"] == DISTRIBUTION_STATS,
        "distribution statistic set changed",
    )
    require(manifest["aggregation"]["cell_weight"] == 1, "cell weight is not one")
    require(
        manifest["aggregation"]["identity"] == "a5-equal-weight-median-v1",
        "aggregation identity changed",
    )
    require(
        manifest["aggregation"]["station_pooling"] == "forbidden",
        "station pooling enabled",
    )
    require(
        manifest["evidence_completeness"]["count_fields_are_distance_cells"] is False,
        "count metadata entered distance vector",
    )
    require(
        manifest["cell_selection"]["denominator_switching"] == "forbidden",
        "denominator switching not forbidden",
    )

    surfaces = {
        surface["surface_id"]: surface for surface in manifest["target_surfaces"]
    }
    require(
        len(surfaces) == len(manifest["target_surfaces"]), "duplicate target surface id"
    )
    require(set(surfaces) == set(EXPECTED_SURFACES), "missing or extra target surface")
    for surface_id, expected in EXPECTED_SURFACES.items():
        surface = surfaces[surface_id]
        actual = tuple(
            surface[key]
            for key in ("source", "period", "detrending", "availability", "path_prefix")
        )
        require(actual == expected, f"source/period/detrending mismatch: {surface_id}")

    templates = manifest["metric_templates"]
    template_ids = [template["template_id"] for template in templates]
    require(len(template_ids) == len(set(template_ids)), "duplicate template id")
    require(
        set(template_ids) == set(EXPECTED_TEMPLATES), "missing or extra metric template"
    )

    cells: list[tuple[Any, ...]] = []
    by_template: dict[str, int] = {}
    for template in templates:
        template_id = template["template_id"]
        expected = EXPECTED_TEMPLATES[template_id]
        (
            count,
            group,
            family,
            gates,
            distance,
            dimensions,
            generated_path,
            target_path,
        ) = expected
        require(template["group"] == group, f"wrong group: {template_id}")
        require(template["family"] == family, f"wrong family: {template_id}")
        require(template["distance"] == distance, f"wrong distance: {template_id}")
        require(
            template["dimensions"] == dimensions,
            f"wrong statistic/dimensions: {template_id}",
        )
        require(
            template["generated_path_template"] == generated_path,
            f"invalid generated path: {template_id}",
        )
        require(
            template["target_path_template"] == target_path,
            f"invalid target path: {template_id}",
        )
        actual_gates = [binding["gate_id"] for binding in template["gate_bindings"]]
        require(actual_gates == gates, f"wrong gate binding: {template_id}")
        require(template["weight"] == 1, f"unequal template weight: {template_id}")
        require(
            template["inclusion_profile"]
            == ("relative" if distance == "absolute_relative" else "difference"),
            f"distance/inclusion mismatch: {template_id}",
        )
        normalization = template.get("normalization")
        if template_id in EXPECTED_NORMALIZATION_PATHS:
            require(normalization is not None, f"missing normalization: {template_id}")
            require(
                normalization["target_scale_path_template"]
                == EXPECTED_NORMALIZATION_PATHS[template_id],
                f"wrong normalization scale: {template_id}",
            )
        else:
            require(normalization is None, f"unexpected normalization: {template_id}")

        rows = substitutions(template["dimensions"])
        require(len(rows) == count, f"wrong expanded count: {template_id}")
        by_template[template_id] = len(rows)
        for binding in template["gate_bindings"]:
            surface_id = binding["target_surface"]
            require(surface_id in surfaces, f"unknown target surface: {template_id}")
            values_base = {"target_prefix": surfaces[surface_id]["path_prefix"]}
            for values in rows:
                generated = substitute(template["generated_path_template"], values)
                target = substitute(
                    template["target_path_template"], values_base | values
                )
                generated_count = substitute(
                    template["completeness"]["generated_count_path_template"], values
                )
                target_count = substitute(
                    template["completeness"]["target_count_path_template"],
                    values_base | values,
                )
                target_scale = (
                    substitute(normalization["target_scale_path_template"], values)
                    if normalization is not None
                    else None
                )
                require(
                    "{" not in generated, f"unexpanded generated path: {template_id}"
                )
                require(
                    "{" not in target.replace("{station_id}", ""),
                    f"unexpanded target path: {template_id}",
                )
                require(
                    generated_count.endswith((".n", ".n_years", ".n_days"))
                    or ".n_pairs[" in generated_count,
                    f"invalid generated count path: {template_id}",
                )
                require(
                    target_count.endswith((".n", ".n_years", ".n_days"))
                    or ".n_pairs[" in target_count,
                    f"invalid target count path: {template_id}",
                )
                cells.append(
                    (
                        binding["gate_id"],
                        template_id,
                        generated,
                        target,
                        family,
                        variable_for(template, values),
                        statistic_for(template, values),
                        distance,
                        surface_id,
                        target_scale,
                    )
                )

    require(len(cells) == len(set(cells)), "duplicate expanded scalar cell")
    gate_counts = {
        gate_id: sum(cell[0] == gate_id for cell in cells) for gate_id in range(1, 8)
    }
    require(
        gate_counts == EXPECTED_GATE_COUNTS, f"wrong gate cell counts: {gate_counts}"
    )

    gates = manifest["gates"]
    gate_ids = [gate["gate_id"] for gate in gates]
    require(
        gate_ids == list(range(1, 8)), "gates must be unique and ordered 1 through 7"
    )
    for gate in gates:
        expected_name, expected_role = EXPECTED_GATE_NAMES[gate["gate_id"]]
        require(gate["name"] == expected_name, f"wrong gate name: {gate['gate_id']}")
        require(gate["role"] == expected_role, f"wrong gate role: {gate['gate_id']}")
    require(
        gates[0]["rule"].count("0.90") == 2
        and "strictly_less_than" in gates[0]["rule"],
        "gate 1 strict improvement/low-frequency subguard missing",
    )
    require("1.10" in gates[1]["rule"], "gate 2 formula missing")
    require("inclusive" in gates[4]["rule"], "gate 5 inclusive spread rule missing")
    require(
        gates[5]["station_ids"]
        == ["co051660", "wy485345", "mn214026", "ak505769", "id106388"],
        "gate 6 station set changed",
    )

    gate1 = {
        (cell[1], cell[2], cell[4], cell[5], cell[6], cell[7])
        for cell in cells
        if cell[0] == 1
    }
    gate2 = {
        (cell[1], cell[2], cell[4], cell[5], cell[6], cell[7])
        for cell in cells
        if cell[0] == 2
    }
    require(gate1 == gate2, "GHCN gate does not exactly mirror gate 1 membership")

    projection_ids = [
        item["projection_id"] for item in manifest["sensitivity_projections"]
    ]
    require(
        projection_ids
        == [
            "daymet_full_raw",
            "ghcn_full_raw",
            "daymet_evaluation_detrended",
            "daymet_full_detrended",
            "ghcn_evaluation_detrended",
            "ghcn_full_detrended",
        ],
        "sensitivity projection set/order changed",
    )
    for projection in manifest["sensitivity_projections"]:
        surface = surfaces[projection["target_surface"]]
        if projection["projection_id"].endswith("detrended"):
            require(
                surface["detrending"] == "ols_linear_residual_by_integer_year",
                "detrended projection uses raw surface",
            )
        else:
            require(
                surface["detrending"] == "raw", "raw projection uses detrended surface"
            )

    uncertainty = manifest["uncertainty_application"]
    require(
        uncertainty["included_gate_ids"] == [1, 4, 6],
        "wrong uncertainty gate membership",
    )
    require(
        uncertainty["excluded_gates"] == [2, 3, 5, 7],
        "wrong uncertainty gate exclusions",
    )
    require(
        uncertainty["target_surface"] == "daymet_evaluation_raw",
        "wrong uncertainty target surface",
    )
    expected_uncertainty_templates = [
        template_id
        for template_id in template_ids
        if any(
            binding["gate_id"] in {1, 4, 6}
            for binding in next(
                template
                for template in templates
                if template["template_id"] == template_id
            )["gate_bindings"]
        )
    ]
    require(
        uncertainty["included_template_ids"] == expected_uncertainty_templates,
        "wrong uncertainty template membership/order",
    )

    return {
        "template_count": len(templates),
        "expanded_cell_bindings": len(cells),
        "gate_counts": gate_counts,
        "template_counts": by_template,
    }


def expect_rejected(
    name: str, manifest: dict[str, Any], schema: dict[str, Any], mutate: Any
) -> str:
    candidate = copy.deepcopy(manifest)
    mutate(candidate)
    try:
        validate_manifest(candidate, schema)
    except (ValidationError, KeyError, TypeError) as error:
        return f"{name}: {error}"
    raise AssertionError(f"negative vector unexpectedly passed: {name}")


def mutation_tests(manifest: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    tests: list[tuple[str, Any]] = [
        ("missing_template", lambda item: item["metric_templates"].pop()),
        (
            "extra_template",
            lambda item: item["metric_templates"].append(
                copy.deepcopy(item["metric_templates"][0])
                | {"template_id": "unexpected_extra"}
            ),
        ),
        (
            "duplicate_template",
            lambda item: item["metric_templates"].append(
                copy.deepcopy(item["metric_templates"][0])
            ),
        ),
        (
            "invalid_generated_path",
            lambda item: item["metric_templates"][0].__setitem__(
                "generated_path_template", "$.interannual.not_real"
            ),
        ),
        (
            "invalid_target_path",
            lambda item: item["metric_templates"][0].__setitem__(
                "target_path_template", "{target_prefix}.not_real"
            ),
        ),
        (
            "source_mismatch",
            lambda item: item["target_surfaces"][0].__setitem__("source", "ghcn"),
        ),
        (
            "detrending_mismatch",
            lambda item: item["target_surfaces"][0].__setitem__(
                "detrending", "ols_linear_residual_by_integer_year"
            ),
        ),
        (
            "wrong_distance",
            lambda item: item["metric_templates"][0].__setitem__(
                "distance", "absolute_difference"
            ),
        ),
        (
            "wrong_statistic",
            lambda item: item["metric_templates"][0]["dimensions"][
                "statistic"
            ].__setitem__(0, "p95"),
        ),
        (
            "wrong_family",
            lambda item: item["metric_templates"][0].__setitem__("family", "other"),
        ),
        (
            "wrong_gate",
            lambda item: item["metric_templates"][0]["gate_bindings"][0].__setitem__(
                "gate_id", 4
            ),
        ),
        (
            "unequal_weight",
            lambda item: item["metric_templates"][0].__setitem__("weight", 2),
        ),
        (
            "count_as_distance",
            lambda item: item["evidence_completeness"].__setitem__(
                "count_fields_are_distance_cells", True
            ),
        ),
        ("missing_root_field", lambda item: item.pop("cell_selection")),
        ("extra_root_field", lambda item: item.__setitem__("analyst_choice", True)),
        (
            "gate_1_threshold",
            lambda item: item["gates"][0].__setitem__("rule", "always_pass"),
        ),
        (
            "gate_2_formula",
            lambda item: item["gates"][1].__setitem__("rule", "direction_optional"),
        ),
        (
            "gate_3_threshold",
            lambda item: item["gates"][2].__setitem__("rule", "arbitrary_regression"),
        ),
        (
            "gate_4_threshold",
            lambda item: item["gates"][3].__setitem__("rule", "always_pass"),
        ),
        (
            "gate_5_spread",
            lambda item: item["gates"][4].__setitem__("rule", "descriptor_optional"),
        ),
        (
            "gate_6_threshold",
            lambda item: item["gates"][5].__setitem__("rule", "always_pass"),
        ),
        (
            "gate_7_evidence_rule",
            lambda item: item["gates"][6]["rules"].__setitem__(0, "reports_optional"),
        ),
        (
            "aggregation_hierarchy",
            lambda item: item["aggregation"]["levels"].reverse(),
        ),
        (
            "median_estimator",
            lambda item: item["aggregation"].__setitem__("median", "lower_middle"),
        ),
        (
            "count_sufficiency",
            lambda item: item["count_sufficiency"].__setitem__(
                "correlation_n_or_n_pairs", "integer_at_least_999999"
            ),
        ),
        (
            "candidate_cell_requirement",
            lambda item: item["cell_selection"].__setitem__(
                "candidate_requirement", "optional"
            ),
        ),
        (
            "common_denominator",
            lambda item: item["cell_selection"].__setitem__(
                "common_denominator", "candidate_selected"
            ),
        ),
        (
            "distance_formula",
            lambda item: item["distance_definitions"]["absolute_relative"].__setitem__(
                "formula", "generated/target"
            ),
        ),
        (
            "inclusion_rule",
            lambda item: item["inclusion_profiles"]["relative"].__setitem__(
                "target", "any_number"
            ),
        ),
        (
            "null_evidence_rule",
            lambda item: item["evidence_completeness"].__setitem__(
                "null_or_nonfinite_action", "ignore"
            ),
        ),
        (
            "gate_3_contract_identity",
            lambda item: item["evidence_completeness"].__setitem__(
                "gate_3_contract_identity", "candidate_selected"
            ),
        ),
        (
            "sensitivity_membership",
            lambda item: item["sensitivity_projections"][0].__setitem__(
                "membership", "analyst_selected"
            ),
        ),
        (
            "binding_target_surface",
            lambda item: item["metric_templates"][0]["gate_bindings"][0].__setitem__(
                "target_surface", "daymet_full_raw"
            ),
        ),
        (
            "count_path",
            lambda item: item["metric_templates"][0]["completeness"].__setitem__(
                "generated_count_path_template", "$.interannual.annual.{variable}.n"
            ),
        ),
        (
            "temperature_location_scale",
            lambda item: next(
                template
                for template in item["metric_templates"]
                if template["template_id"] == "a_monthly_tmax_location_contract"
            )["normalization"].__setitem__(
                "target_scale_path_template",
                "$.par_convergence.tmin_sd_c.{month}.target",
            ),
        ),
        (
            "uncertainty_gate_membership",
            lambda item: item["uncertainty_application"]["included_gate_ids"].pop(),
        ),
        (
            "uncertainty_template_membership",
            lambda item: item["uncertainty_application"]["included_template_ids"].pop(),
        ),
        (
            "uncertainty_target_surface",
            lambda item: item["uncertainty_application"].__setitem__(
                "target_surface", "ghcn_evaluation_raw"
            ),
        ),
        (
            "uncertainty_generated_crossing",
            lambda item: item["uncertainty_application"].__setitem__(
                "crossing", "pair_by_index"
            ),
        ),
        (
            "uncertainty_aggregation_order",
            lambda item: item["uncertainty_application"][
                "aggregation_order_within_bootstrap_replicate"
            ].reverse(),
        ),
        (
            "uncertainty_decision_role",
            lambda item: item["uncertainty_application"].__setitem__(
                "decision_role", "changes_promotion"
            ),
        ),
        (
            "uncertainty_year_relabeling",
            lambda item: item["uncertainty_application"].__setitem__(
                "resampled_year_relabeling", "sort_original_labels"
            ),
        ),
        (
            "uncertainty_sequence_closure",
            lambda item: item["uncertainty_application"].__setitem__(
                "sequence_boundaries", "join_final_to_first"
            ),
        ),
        (
            "uncertainty_invalid_cell",
            lambda item: item["uncertainty_application"].__setitem__(
                "invalid_resample_cell", "drop_and_reweight"
            ),
        ),
        (
            "uncertainty_station_alignment",
            lambda item: item["uncertainty_application"].__setitem__(
                "station_stream_alignment", "pool_station_streams"
            ),
        ),
    ]
    return [expect_rejected(name, manifest, schema, mutate) for name, mutate in tests]


def parser_negative_tests() -> list[str]:
    inputs = {
        "duplicate_key": '{"a":1,"a":2}',
        "nan": '{"a":NaN}',
        "positive_infinity": '{"a":Infinity}',
        "negative_infinity": '{"a":-Infinity}',
        "positive_float_overflow": '{"a":1e400}',
        "negative_float_overflow": '{"a":-1e400}',
    }
    results: list[str] = []
    for name, text in inputs.items():
        try:
            strict_json_loads(text)
        except (ValidationError, ValueError) as error:
            results.append(f"{name}: {error}")
            continue
        raise AssertionError(f"invalid JSON unexpectedly passed: {name}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    manifest_bytes = args.manifest.read_bytes()
    manifest = strict_json_loads(manifest_bytes.decode("utf-8"))
    schema = load_json(args.schema)
    summary = validate_manifest(manifest, schema)
    negatives = mutation_tests(manifest, schema)
    parser_negatives = parser_negative_tests()
    print(
        json.dumps(
            {
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                **summary,
                "negative_vectors": len(negatives) + len(parser_negatives),
                "status": "pass",
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
