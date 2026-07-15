#!/usr/bin/env python3
"""Deterministic dry-regime applicability analysis for A8a."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import tarfile
from pathlib import Path
from typing import Any

import numpy as np

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
SEASONS = ("DJF", "MAM", "JJA", "SON")
INTEGRATED = "integrated_daily"
FALLBACK = "legacy_daily_fallback"
MASK64 = (1 << 64) - 1


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
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


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def checked_input(contract: dict[str, Any], name: str) -> Path:
    entry = contract["inputs"][name]
    path = REPO / entry["path"]
    actual = sha256(path.read_bytes())
    if actual != entry["sha256"]:
        raise ValueError(f"input identity mismatch for {name}: {actual}")
    return path


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_freeze(contract: dict[str, Any]) -> None:
    freeze = load_json(ARTIFACTS / "pre-analysis-freeze-v2.json")
    if freeze["status"] != "FROZEN-BEFORE-NEW-DAILY-DATA":
        raise ValueError("A8a pre-analysis freeze is not active")
    for relative, expected in freeze["frozen_files_sha256"].items():
        if sha256((REPO / relative).read_bytes()) != expected:
            raise ValueError(f"frozen file changed: {relative}")
    if freeze["source_commit"] != contract["source_commit"]:
        raise ValueError("freeze source commit mismatch")


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_json(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def parameter_members(path: Path, station_ids: set[str], a7b: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    with tarfile.open(path, mode="r:gz") as archive:
        for station_id in sorted(station_ids):
            member = archive.getmember(f"station-parameters/{station_id}.par")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"missing parameter file: {station_id}")
            raw = stream.read()
            lines = raw.decode("ascii").splitlines()
            mean_mm = [value * 25.4 for value in a7b.parse_parameter_row(lines[3])]
            sd_mm = [value * 25.4 for value in a7b.parse_parameter_row(lines[4])]
            pww = a7b.parse_parameter_row(lines[6])
            pwd = a7b.parse_parameter_row(lines[7])
            result[station_id] = {
                "parameter_sha256": sha256(raw),
                "pwd": pwd,
                "pww": pww,
                "wet_mean_mm": mean_mm,
                "wet_sd_mm": sd_mm,
            }
    return result


def series_from_records(
    records: dict[tuple[int, int, int], dict[str, float]],
    start_year: int,
    end_year: int,
    threshold: float,
    a7b: Any,
) -> Any:
    dates = tuple(
        date for date in sorted(records) if start_year <= date[0] <= end_year
    )
    amounts = np.asarray([records[date]["prcp"] for date in dates], dtype=float)
    return a7b.DailySeries(dates, amounts, amounts >= threshold)


def slice_series(series: Any, start_year: int, end_year: int, a7b: Any) -> Any:
    indices = [
        index
        for index, date in enumerate(series.dates)
        if start_year <= date[0] <= end_year
    ]
    dates = tuple(series.dates[index] for index in indices)
    amounts = series.amounts[indices]
    return a7b.DailySeries(dates, amounts, series.wet[indices])


def splitmix64(value: int) -> tuple[int, int]:
    state = (value + 0x9E3779B97F4A7C15) & MASK64
    mixed = state
    mixed = ((mixed ^ (mixed >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    mixed = ((mixed ^ (mixed >> 27)) * 0x94D049BB133111EB) & MASK64
    return state, (mixed ^ (mixed >> 31)) & MASK64


def annual_support(
    series: Any,
    contract: dict[str, Any],
    a7b_contract: dict[str, Any],
    a7b: Any,
) -> dict[int, dict[str, Any]]:
    threshold = contract["sources"]["wet_day_threshold_mm"]
    result: dict[int, dict[str, Any]] = {}
    years = sorted({date[0] for date in series.dates})
    for year in years:
        indices = [index for index, date in enumerate(series.dates) if date[0] == year]
        first = indices[0]
        values = {
            season: {"adjacent_wet_pairs": 0, "occurrence_exposures": [0, 0, 0, 0], "wet_amounts": 0}
            for season in SEASONS
        }
        for index in indices:
            season = a7b.season_for_month(a7b_contract, series.dates[index][1])
            wet = bool(series.amounts[index] >= threshold)
            values[season]["wet_amounts"] += int(wet)
            if index > first and series.wet[index - 1] and wet:
                values[season]["adjacent_wet_pairs"] += 1
            if index >= first + 2:
                state = 2 * int(series.wet[index - 2]) + int(series.wet[index - 1])
                values[season]["occurrence_exposures"][state] += 1
        result[year] = values
    return result


def bootstrap_support(
    station_id: str,
    series: Any,
    amount_fits: dict[str, dict[str, Any]],
    occurrence_fits: dict[str, dict[str, Any]],
    contract: dict[str, Any],
    a7b_contract: dict[str, Any],
    a7b: Any,
) -> dict[str, Any]:
    contributions = annual_support(series, contract, a7b_contract, a7b)
    years = sorted(contributions)
    replicates = contract["bootstrap"]["replicates"]
    state = contract["bootstrap"]["seed_u64"] ^ int(
        hashlib.sha256(station_id.encode("ascii")).hexdigest()[:16], 16
    )
    sampled = {
        season: {"adjacent_wet_pairs": [], "occurrence_exposures": [[], [], [], []], "wet_amounts": []}
        for season in SEASONS
    }
    for _ in range(replicates):
        totals = {
            season: {"adjacent_wet_pairs": 0, "occurrence_exposures": [0, 0, 0, 0], "wet_amounts": 0}
            for season in SEASONS
        }
        for _draw in years:
            state, value = splitmix64(state)
            contribution = contributions[years[value % len(years)]]
            for season in SEASONS:
                totals[season]["adjacent_wet_pairs"] += contribution[season]["adjacent_wet_pairs"]
                totals[season]["wet_amounts"] += contribution[season]["wet_amounts"]
                for index in range(4):
                    totals[season]["occurrence_exposures"][index] += contribution[season]["occurrence_exposures"][index]
        for season in SEASONS:
            sampled[season]["adjacent_wet_pairs"].append(totals[season]["adjacent_wet_pairs"])
            sampled[season]["wet_amounts"].append(totals[season]["wet_amounts"])
            for index in range(4):
                sampled[season]["occurrence_exposures"][index].append(totals[season]["occurrence_exposures"][index])
    rank = max(0, math.ceil(contract["bootstrap"]["lower_quantile"] * replicates) - 1)
    rules = a7b_contract["fit_rules"]
    seasons: dict[str, Any] = {}
    for season in SEASONS:
        lower = {
            "adjacent_wet_pairs": sorted(sampled[season]["adjacent_wet_pairs"])[rank],
            "occurrence_exposures": [
                sorted(sampled[season]["occurrence_exposures"][index])[rank]
                for index in range(4)
            ],
            "wet_amounts": sorted(sampled[season]["wet_amounts"])[rank],
        }
        lower_pass = bool(
            lower["adjacent_wet_pairs"] >= rules["minimum_adjacent_wet_pairs_per_station_season"]
            and lower["wet_amounts"] >= rules["minimum_wet_amounts_per_station_season"]
            and min(lower["occurrence_exposures"])
            >= rules["minimum_occurrence_exposure_per_state_and_station_season"]
        )
        point_pass = bool(
            amount_fits[season]["identifiable"] and occurrence_fits[season]["identifiable"]
        )
        seasons[season] = {
            "bootstrap_lower": lower,
            "bootstrap_lower_pass": lower_pass,
            "point_fit_pass": point_pass,
        }
    return {
        "all_seasons_pass": all(
            entry["bootstrap_lower_pass"] and entry["point_fit_pass"]
            for entry in seasons.values()
        ),
        "lower_quantile": contract["bootstrap"]["lower_quantile"],
        "replicates": replicates,
        "seasons": seasons,
    }


def fit_station(
    series: Any,
    legacy: dict[str, Any],
    contract: dict[str, Any],
    a7b_contract: dict[str, Any],
    a7b: Any,
) -> dict[str, Any]:
    candidate_id = contract["mechanism"]["candidate_id"]
    amount_fits: dict[str, dict[str, Any]] = {}
    occurrence_fits: dict[str, dict[str, Any]] = {}
    for season in SEASONS:
        amount_fits[season] = a7b.seasonal_amount_fit(series, season, a7b_contract)
        occurrence_fits[season] = a7b.seasonal_occurrence_fit(
            series, season, candidate_id, a7b_contract
        )
    cells: list[dict[str, Any]] = []
    for month, days in enumerate(a7b_contract["comparison"]["month_lengths"], 1):
        season = a7b.season_for_month(a7b_contract, month)
        amount_fit = amount_fits[season]
        occurrence_fit = occurrence_fits[season]
        mean_mm = legacy["wet_mean_mm"][month - 1]
        sd_mm = legacy["wet_sd_mm"][month - 1]
        pww = legacy["pww"][month - 1]
        pwd = legacy["pwd"][month - 1]
        reasons = list(amount_fit["infeasibility_reasons"])
        reasons.extend(occurrence_fit["infeasibility_reasons"])
        denominator = 1.0 - pww + pwd
        target_mu = pwd / denominator if denominator > 0.0 else None
        cell: dict[str, Any] = {
            "days": days,
            "legacy": {
                "pwd": pwd,
                "pww": pww,
                "stationary_wet_fraction": target_mu,
                "wet_mean_mm": mean_mm,
                "wet_sd_mm": sd_mm,
            },
            "month": month,
            "season": season,
        }
        if target_mu is None or not 0.0 < target_mu < 1.0 or mean_mm <= 0.0:
            reasons.append("legacy_degenerate_wet_month")
        else:
            recentered = a7b.recenter_kernel(
                candidate_id,
                np.asarray(occurrence_fit["probabilities"]),
                target_mu,
                a7b_contract,
            )
            reasons.extend(recentered["infeasibility_reasons"])
            cell["kernel"] = {
                "logit_shift": recentered["logit_shift"],
                "probabilities": [float(value) for value in recentered["probabilities"]],
                "stationary_distribution": [float(value) for value in recentered["stationary"]],
                "stationary_wet_fraction": recentered["stationary_wet_fraction"],
                "transition_matrix": [
                    [float(value) for value in row] for row in recentered["transition"]
                ],
            }
            if amount_fit["identifiable"] and occurrence_fit["identifiable"] and not recentered["infeasibility_reasons"]:
                occurrence = a7b.occurrence_moments(
                    recentered["transition"],
                    recentered["stationary"],
                    a7b.wet_mask(candidate_id),
                    days,
                )
                baseline = a7b.baseline_occurrence(pww, pwd, days)
                shape = a7b.AmountShape(amount_fit, a7b_contract)
                budget = a7b.certify_amount_budget(
                    shape,
                    occurrence,
                    baseline,
                    days,
                    mean_mm,
                    sd_mm,
                    a7b_contract,
                )
                reasons.extend(budget["infeasibility_reasons"])
                cell["budget"] = budget
                cell["occurrence_moments"] = {
                    "candidate_wet_count_variance": occurrence["wet_count_variance"],
                    "legacy_wet_count_variance": baseline["wet_count_variance"],
                }
        cell["infeasibility_reasons"] = sorted(set(reasons))
        cell["feasible"] = not cell["infeasibility_reasons"]
        cells.append(clean_json(cell))
    return {
        "amount_fits": {season: clean_json(fit) for season, fit in amount_fits.items()},
        "analytic_pass": all(cell["feasible"] for cell in cells),
        "cells": cells,
        "feasible_cell_count": sum(cell["feasible"] for cell in cells),
        "occurrence_fits": {season: clean_json(fit) for season, fit in occurrence_fits.items()},
        "raw_amount_fits": amount_fits,
        "raw_occurrence_fits": occurrence_fits,
    }


def support_point_pass(fit: dict[str, Any]) -> bool:
    return all(
        fit["amount_fits"][season]["identifiable"]
        and fit["occurrence_fits"][season]["identifiable"]
        for season in SEASONS
    )


def ghcn_support(
    records: dict[tuple[int, int, int], dict[str, float]],
    contract: dict[str, Any],
    a7b_contract: dict[str, Any],
    common: Any,
) -> dict[str, Any]:
    start_year, end_year = contract["sources"]["period"]
    dates = [
        date
        for date in sorted(records)
        if start_year <= date[0] <= end_year and "prcp" in records[date]
    ]
    threshold = contract["sources"]["wet_day_threshold_mm"]
    values = [records[date]["prcp"] for date in dates]
    wet = [value >= threshold for value in values]
    rules = a7b_contract["fit_rules"]
    seasons: dict[str, Any] = {}
    for season in SEASONS:
        months = set(a7b_contract["comparison"]["seasons"][season])
        wet_values = [value for date, value in zip(dates, values) if date[1] in months and value >= threshold]
        adjacent = 0
        exposures = [0, 0, 0, 0]
        for index, date in enumerate(dates):
            if date[1] not in months:
                continue
            if index >= 1 and common.next_date("proleptic_gregorian", dates[index - 1]) == date:
                adjacent += int(wet[index - 1] and wet[index])
            if (
                index >= 2
                and common.next_date("proleptic_gregorian", dates[index - 2]) == dates[index - 1]
                and common.next_date("proleptic_gregorian", dates[index - 1]) == date
            ):
                state = 2 * int(wet[index - 2]) + int(wet[index - 1])
                exposures[state] += 1
        identifiable = bool(
            len(wet_values) >= rules["minimum_wet_amounts_per_station_season"]
            and len(set(wet_values)) >= rules["minimum_distinct_wet_amounts_per_station_season"]
            and adjacent >= rules["minimum_adjacent_wet_pairs_per_station_season"]
            and min(exposures)
            >= rules["minimum_occurrence_exposure_per_state_and_station_season"]
        )
        seasons[season] = {
            "adjacent_wet_pairs": adjacent,
            "distinct_wet_amounts": len(set(wet_values)),
            "identifiable": identifiable,
            "occurrence_exposures": exposures,
            "wet_amounts": len(wet_values),
        }
    return {"all_seasons_point_support_pass": all(x["identifiable"] for x in seasons.values()), "seasons": seasons}


def load_sources(contract: dict[str, Any], panel: dict[str, Any], common: Any, a7b: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, str], dict[str, Any]]:
    threshold = contract["sources"]["wet_day_threshold_mm"]
    start_year, end_year = contract["sources"]["period"]
    confirmation_ids = {station["station_id"] for station in panel["stations"]}
    confirmation_parameters = parameter_members(
        checked_input(contract, "selected_parameters"), confirmation_ids, a7b
    )
    manifest = load_json(ARTIFACTS / "source-manifest-v1.json")
    if manifest["analysis_contract_sha256"] != sha256(
        (ARTIFACTS / "analysis-contract-v1.json").read_bytes()
    ):
        raise ValueError("source manifest contract mismatch")
    manifest_index = {entry["station_id"]: entry for entry in manifest["stations"]}
    series: dict[str, Any] = {}
    ghcn_records: dict[str, Any] = {}
    strata = {station["station_id"]: station["stratum"] for station in panel["stations"]}
    for station in panel["stations"]:
        station_id = station["station_id"]
        source = manifest_index[station_id]["sources"]["daymet"]
        path = REPO / source["archive_path"]
        if sha256(path.read_bytes()) != source["archive_sha256"]:
            raise ValueError(f"Daymet archive mismatch: {station_id}")
        records, metadata = common.archive_records(path, "daymet", station)
        if metadata["source_sha256"] != source["source_sha256"]:
            raise ValueError(f"Daymet source mismatch: {station_id}")
        series[station_id] = series_from_records(
            records, start_year, end_year, threshold, a7b
        )
        ghcn = manifest_index[station_id]["sources"]["ghcn"]
        if ghcn["availability"] == "available" and ghcn["sensitivity_eligible"]:
            path = REPO / ghcn["archive_path"]
            if sha256(path.read_bytes()) != ghcn["archive_sha256"]:
                raise ValueError(f"GHCN archive mismatch: {station_id}")
            records, _metadata = common.archive_records(
                path, "ghcn", {"ghcn_station_id": ghcn["station_identifier"]}
            )
            ghcn_records[station_id] = records
    a5a_config = load_json(checked_input(contract, "a5a_corpus_config"))
    a5a_manifest = load_json(checked_input(contract, "a5a_source_manifest"))
    config_index = {entry["station_id"]: entry for entry in a5a_config["stations"]}
    source_index = {entry["station_id"]: entry for entry in a5a_manifest["stations"]}
    development_ids = set(contract["decision"]["expected_development_classes"])
    development_parameters = parameter_members(
        checked_input(contract, "a5a_baseline_archive"), development_ids, a7b
    )
    for station_id in sorted(development_ids):
        station = config_index[station_id]
        source = source_index[station_id]["sources"]["daymet"]
        records, _metadata = common.archive_records(
            REPO / source["archive_path"], "daymet", station
        )
        series[station_id] = series_from_records(
            records, start_year, end_year, threshold, a7b
        )
        strata[station_id] = f"development_{station['regime']}"
    parameters = {**confirmation_parameters, **development_parameters}
    return series, parameters, strata, ghcn_records


def analyze(contract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    for name in contract["inputs"]:
        checked_input(contract, name)
    a7b_path = checked_input(contract, "a7b_analyzer")
    a7b = load_module(a7b_path, "a8a_a7b_analyzer")
    a7b_contract = load_json(checked_input(contract, "a7b_contract"))
    common = load_module(checked_input(contract, "corpus_common"), "a8a_corpus_common")
    panel = load_json(checked_input(contract, "panel"))
    series, parameters, strata, ghcn_records = load_sources(
        contract, panel, common, a7b
    )
    confirmation_ids = {station["station_id"] for station in panel["stations"]}
    development_ids = set(contract["decision"]["expected_development_classes"])
    station_results: list[dict[str, Any]] = []
    for station_id in sorted(series):
        full = fit_station(
            series[station_id], parameters[station_id], contract, a7b_contract, a7b
        )
        bootstrap = bootstrap_support(
            station_id,
            series[station_id],
            full["raw_amount_fits"],
            full["raw_occurrence_fits"],
            contract,
            a7b_contract,
            a7b,
        )
        classification = (
            INTEGRATED if full["analytic_pass"] and bootstrap["all_seasons_pass"] else FALLBACK
        )
        windows = []
        if station_id in confirmation_ids:
            for start_year, end_year in contract["shortened_windows"]:
                window_fit = fit_station(
                    slice_series(series[station_id], start_year, end_year, a7b),
                    parameters[station_id],
                    contract,
                    a7b_contract,
                    a7b,
                )
                window_class = (
                    INTEGRATED
                    if window_fit["analytic_pass"] and support_point_pass(window_fit)
                    else FALLBACK
                )
                windows.append(
                    {
                        "analytic_pass": window_fit["analytic_pass"],
                        "classification": window_class,
                        "feasible_cell_count": window_fit["feasible_cell_count"],
                        "period": [start_year, end_year],
                        "point_support_pass": support_point_pass(window_fit),
                    }
                )
        sensitivity = None
        if station_id in ghcn_records:
            sensitivity = ghcn_support(
                ghcn_records[station_id], contract, a7b_contract, common
            )
            sensitivity["daymet_point_support_pass"] = support_point_pass(full)
            sensitivity["support_agrees"] = (
                sensitivity["all_seasons_point_support_pass"]
                == sensitivity["daymet_point_support_pass"]
            )
        station_results.append(
            {
                "bootstrap_support": bootstrap,
                "classification": classification,
                "confirmation": station_id in confirmation_ids,
                "full_record": {
                    "amount_fits": full["amount_fits"],
                    "analytic_pass": full["analytic_pass"],
                    "cells": full["cells"],
                    "feasible_cell_count": full["feasible_cell_count"],
                    "occurrence_fits": full["occurrence_fits"],
                    "point_support_pass": support_point_pass(full),
                },
                "ghcn_sensitivity": sensitivity,
                "parameter_sha256": parameters[station_id]["parameter_sha256"],
                "shortened_windows": windows,
                "station_id": station_id,
                "stratum": strata[station_id],
            }
        )
        print(f"analyzed {station_id}", file=sys.stderr, flush=True)
    confirmation = [entry for entry in station_results if entry["confirmation"]]
    development = [entry for entry in station_results if not entry["confirmation"]]
    dry = [entry for entry in confirmation if entry["stratum"] != "negative_control"]
    controls = [entry for entry in confirmation if entry["stratum"] == "negative_control"]
    comparisons = [
        entry["classification"] == window["classification"]
        for entry in confirmation
        for window in entry["shortened_windows"]
    ]
    monsoon = [entry for entry in confirmation if entry["stratum"] == "monsoonal_transition"]
    other_dry = [
        entry
        for entry in confirmation
        if entry["stratum"] in contract["stability"]["other_dry_groups"]
    ]

    def instability(entries: list[dict[str, Any]]) -> float:
        values = [
            entry["classification"] != window["classification"]
            for entry in entries
            for window in entry["shortened_windows"]
        ]
        return sum(values) / len(values)

    development_actual = {entry["station_id"]: entry["classification"] for entry in development}
    expected = contract["decision"]["expected_development_classes"]
    stratum_counts = {
        stratum: {
            INTEGRATED: sum(
                entry["stratum"] == stratum and entry["classification"] == INTEGRATED
                for entry in confirmation
            ),
            FALLBACK: sum(
                entry["stratum"] == stratum and entry["classification"] == FALLBACK
                for entry in confirmation
            ),
        }
        for stratum in sorted({entry["stratum"] for entry in confirmation})
    }
    shortened_agreement = sum(comparisons) / len(comparisons)
    monsoon_instability = instability(monsoon)
    other_dry_instability = instability(other_dry)
    guards = {
        "confirmation_cardinality": len(confirmation)
        == contract["decision"]["confirmation_station_count"],
        "development_reproduced": development_actual == expected,
        "dry_fallback_breadth": sum(entry["classification"] == FALLBACK for entry in dry)
        >= contract["decision"]["dry_fallback_min"],
        "dry_integrated_breadth": sum(entry["classification"] == INTEGRATED for entry in dry)
        >= contract["decision"]["dry_integrated_min"],
        "integrated_analytic_pass": all(
            entry["full_record"]["analytic_pass"]
            for entry in confirmation
            if entry["classification"] == INTEGRATED
        ),
        "monsoonal_shared_boundary": (
            monsoon_instability - other_dry_instability
            <= contract["decision"]["monsoonal_instability_excess_max"]
        ),
        "negative_controls_integrated": sum(
            entry["classification"] == INTEGRATED for entry in controls
        )
        == contract["decision"]["negative_control_integrated_required"],
        "shortened_window_agreement": shortened_agreement
        >= contract["decision"]["shortened_window_agreement_min"],
    }
    terminal = (
        contract["decision"]["pass_terminal"]
        if all(guards.values())
        else contract["decision"]["stop_terminal"]
    )
    ghcn_entries = [
        entry["ghcn_sensitivity"]
        for entry in confirmation
        if entry["ghcn_sensitivity"] is not None
    ]
    decision = {
        "analysis_id": contract["analysis_id"],
        "classification_counts": {
            INTEGRATED: sum(entry["classification"] == INTEGRATED for entry in confirmation),
            FALLBACK: sum(entry["classification"] == FALLBACK for entry in confirmation),
        },
        "development_actual_classes": development_actual,
        "ghcn_support_agreement": {
            "agreement_fraction": (
                sum(entry["support_agrees"] for entry in ghcn_entries) / len(ghcn_entries)
                if ghcn_entries
                else None
            ),
            "eligible_station_count": len(ghcn_entries),
            "terminal_gate": False,
        },
        "guards": guards,
        "monsoonal_instability_rate": monsoon_instability,
        "monsoonal_separate_study_justified": not guards["monsoonal_shared_boundary"],
        "other_dry_instability_rate": other_dry_instability,
        "schema_version": 1,
        "shortened_window_agreement": shortened_agreement,
        "stratum_counts": stratum_counts,
        "terminal": terminal,
    }
    analysis = {
        "analysis_id": contract["analysis_id"],
        "analysis_contract_sha256": sha256((ARTIFACTS / "analysis-contract-v1.json").read_bytes()),
        "execution_counts": {
            "confirmation_stations": len(confirmation),
            "development_stations": len(development),
            "full_record_cells": 12 * len(station_results),
            "shortened_station_windows": len(comparisons),
        },
        "pre_analysis_freeze_sha256": sha256(
            (ARTIFACTS / "pre-analysis-freeze-v2.json").read_bytes()
        ),
        "schema_version": 1,
        "source_manifest_sha256": sha256((ARTIFACTS / "source-manifest-v1.json").read_bytes()),
        "station_results": station_results,
        "terminal": terminal,
    }
    return clean_json(analysis), clean_json(decision)


def findings(decision: dict[str, Any]) -> str:
    lines = [
        "# A8a findings",
        "",
        f"Terminal: `{decision['terminal']}`",
        "",
        "A8a selected stations before new daily-data access and generated no candidate climate.",
        "",
        "| Stratum | Integrated daily | Legacy daily fallback |",
        "|---|---:|---:|",
    ]
    for stratum, counts in decision["stratum_counts"].items():
        lines.append(f"| {stratum} | {counts[INTEGRATED]} | {counts[FALLBACK]} |")
    lines.extend(
        [
            "",
            f"Shortened-window agreement: {decision['shortened_window_agreement']:.3f}",
            f"Monsoonal instability: {decision['monsoonal_instability_rate']:.3f}",
            f"Other-dry instability: {decision['other_dry_instability_rate']:.3f}",
            "",
            "The classification is a compiler-time evidence disposition, not a runtime aridity inference or output-selected fallback.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ARTIFACTS / "a8a-analysis-v1.json")
    parser.add_argument("--decision", type=Path, default=ARTIFACTS / "a8a-decision-v1.json")
    parser.add_argument("--findings", type=Path, default=ARTIFACTS / "findings.md")
    args = parser.parse_args()
    contract = load_json(ARTIFACTS / "analysis-contract-v1.json")
    check_freeze(contract)
    a7b = load_module(checked_input(contract, "a7b_analyzer"), "a8a_boundary_check")
    a7b.check_source_boundary(REPO, contract["source_commit"])
    analysis, decision = analyze(contract)
    args.output.write_bytes(canonical_json_bytes(analysis))
    args.decision.write_bytes(canonical_json_bytes(decision))
    args.findings.write_text(findings(decision), encoding="utf-8")
    print(decision["terminal"])


if __name__ == "__main__":
    main()
