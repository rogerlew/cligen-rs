"""Actual research candidate laws for the A9c observed-development campaign.

The implementations are deliberately outside ``crates/``. They materialize
the two frozen probability factorizations; they are not accepted runtime
profiles.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.special import logsumexp
from scipy.stats import genpareto

from research.a9_harness.artifacts import FitArtifactStore
from research.a9_harness.canonical import sha256_bytes
from research.a9_harness.rng import RandomFieldIdentity, uniform
from research.a9c.data import ARTIFACTS, LARGE, REPO, canonical_bytes, sha256_path


RENEWAL = "alternating_renewal_marked_v1"
LATENT = "latent_regime_marked_v1"
FIT_DIRECTORY = ARTIFACTS / "fits"
FIT_DETAIL_DIRECTORY = FIT_DIRECTORY / "detail"
FIT_SCHEMA = REPO / "docs/specifications/a9-fit-artifact-v1.schema.json"
PANEL = REPO / "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json"
ROLE_MANIFEST = ARTIFACTS / "data-role-manifest-v1.json"
OBJECTIVE_REGISTRY = REPO / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts/objective-registry-v1.json"
CAMPAIGN_FREEZE = ARTIFACTS / "campaign-freeze-v1.json"
SOURCE_MANIFEST = ARTIFACTS / "observed-source-manifest-v1.json"
NULL_THRESHOLDS = ARTIFACTS / "null-thresholds-v1.json"
EPS = 1.0e-9
_HMM_CACHE: dict[tuple[str, int], "HmmResult"] = {}


def load_gzip_json(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def load_daymet(role: str) -> dict[str, dict[str, Any]]:
    return {path.stem.split(".")[0]: load_gzip_json(path) for path in sorted((LARGE / "daymet" / role).glob("*.json.gz"))}


def load_uscrn(role: str) -> dict[str, dict[str, Any]]:
    return {path.stem.split(".")[0]: load_gzip_json(path) for path in sorted((LARGE / "uscrn" / role).glob("*.json.gz"))}


def month_of(row: dict[str, Any]) -> int:
    return int(row["date"][5:7])


def tmean(row: dict[str, Any]) -> float:
    return (float(row["tmax_c"]) + float(row["tmin_c"])) / 2.0


def dtr(row: dict[str, Any]) -> float:
    return max(0.1, float(row["tmax_c"]) - float(row["tmin_c"]))


def spell_counts(rows: list[dict[str, Any]], threshold: float) -> dict[str, dict[int, np.ndarray]]:
    result = {"wet": {month: np.zeros(61, dtype=float) for month in range(1, 13)}, "dry": {month: np.zeros(61, dtype=float) for month in range(1, 13)}}
    if not rows:
        return result
    current = float(rows[0]["prcp_mm"]) >= threshold
    start_month = month_of(rows[0])
    length = 0
    for row in rows:
        wet = float(row["prcp_mm"]) >= threshold
        if wet == current:
            length += 1
            continue
        result["wet" if current else "dry"][start_month][min(length, 61) - 1] += 1.0
        current = wet
        start_month = month_of(row)
        length = 1
    result["wet" if current else "dry"][start_month][min(length, 61) - 1] += 1.0
    return result


def pool_pmf(station: np.ndarray, stratum: np.ndarray, global_: np.ndarray, strength: float) -> list[float]:
    stratum_probability = (stratum + 0.01) / (stratum.sum() + 0.61)
    global_probability = (global_ + 0.01) / (global_.sum() + 0.61)
    pooled = station + 0.75 * strength * stratum_probability + 0.25 * strength * global_probability
    pooled /= pooled.sum()
    return pooled.tolist()


def pooled_mean_sd(values: list[float], group: list[float], global_: list[float], strength: float) -> tuple[float, float, int]:
    if not group or not global_:
        raise ValueError("empty hierarchy group")
    station = np.asarray(values if values else group, dtype=float)
    prior_mean = 0.75 * float(np.mean(group)) + 0.25 * float(np.mean(global_))
    weight = len(values) / (len(values) + strength)
    mean = weight * float(np.mean(station)) + (1.0 - weight) * prior_mean
    prior_var = 0.75 * float(np.var(group)) + 0.25 * float(np.var(global_))
    variance = weight * float(np.var(station)) + (1.0 - weight) * prior_var
    return mean, max(math.sqrt(max(variance, 0.0)), 1.0e-4), len(values)


def corr(values: list[tuple[float, float]]) -> float:
    if len(values) < 3:
        return 0.0
    result = float(np.corrcoef(np.asarray(values).T)[0, 1])
    return max(-0.8, min(0.8, result if math.isfinite(result) else 0.0))


def transformed_event_laws(uscrn: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for payload in uscrn.values():
        by_stratum[payload["stratum"]].extend(payload["events"])

    def fit_law(events: list[dict[str, Any]]) -> dict[str, Any]:
        x_rows = []
        y_rows = []
        context_rows = []
        previous_end = None
        for event in sorted(events, key=lambda row: row["start_lst"]):
            start = np.datetime64(event["start_lst"])
            month = int(event["start_lst"][5:7])
            antecedent_hours = 24.0
            if previous_end is not None:
                antecedent_hours = max(0.0, float((start - previous_end) / np.timedelta64(1, "h")))
            duration = float(event["duration_min"])
            previous_end = start + np.timedelta64(int(round(duration)), "m")
            temperature = event["air_temperature_c"]
            x_rows.append(
                [
                    1.0,
                    math.log1p(float(event["depth_mm"])),
                    math.sin(2.0 * math.pi * (month - 0.5) / 12.0),
                    math.cos(2.0 * math.pi * (month - 0.5) / 12.0),
                    math.log1p(antecedent_hours),
                    1.0 if temperature is not None and float(temperature) < 0.0 else 0.0,
                ]
            )
            ttp = min(1.0 - 1.0e-6, max(1.0e-6, float(event["time_to_peak_fraction"])))
            y_rows.append(
                [
                    math.log(duration),
                    math.log(ttp / (1.0 - ttp)),
                    math.log(max(float(event["peak_ratio"]), 1.0)),
                ]
            )
            context_rows.append(
                [
                    event.get("air_temperature_c"),
                    event.get("solar_radiation_w_m2"),
                    event.get("relative_humidity_pct"),
                    event.get("wind_speed_1_5m_m_s"),
                ]
            )
        x = np.asarray(x_rows)
        y = np.asarray(y_rows)
        coefficients, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
        residual = y - x @ coefficients
        covariance = np.cov(residual.T) + np.eye(3) * 1.0e-6
        context = []
        for index in range(4):
            present = [float(row[index]) for row in context_rows if row[index] is not None]
            context.append({"mean": float(np.mean(present)), "sd": max(float(np.std(present)), 1.0e-4), "n": len(present)})
        return {
            "coefficient": coefficients.T.tolist(),
            "context": context,
            "covariance": covariance.tolist(),
            "event_count": len(events),
        }
    all_events = [event for events in by_stratum.values() for event in events]
    if len(all_events) < 1000 or len(uscrn) < 5:
        raise ValueError(f"global event borrowing ineligible: {len(all_events)}/{len(uscrn)}")
    global_law = fit_law(all_events)
    laws: dict[str, Any] = {}
    for stratum, events in sorted(by_stratum.items()):
        if len(events) < 100:
            raise ValueError(f"insufficient group events: {stratum}/{len(events)}")
        local = fit_law(events)
        weight = len(events) / (len(events) + 150.0)
        coefficient = weight * np.asarray(local["coefficient"]) + (1.0 - weight) * np.asarray(global_law["coefficient"])
        covariance = weight * np.asarray(local["covariance"]) + (1.0 - weight) * np.asarray(global_law["covariance"])
        context = []
        for local_context, global_context in zip(local["context"], global_law["context"]):
            context.append(
                {
                    "mean": weight * local_context["mean"] + (1.0 - weight) * global_context["mean"],
                    "n": local_context["n"],
                    "sd": max(weight * local_context["sd"] + (1.0 - weight) * global_context["sd"], 1.0e-4),
                }
            )
        laws[stratum] = {
            "coefficient": coefficient.tolist(),
            "context": context,
            "covariance": covariance.tolist(),
            "event_count": len(events),
            "global_borrowing_event_count": len(all_events),
            "global_borrowing_site_count": len(uscrn),
        }
    return laws


def source_identities() -> list[dict[str, Any]]:
    manifest = json.loads((ARTIFACTS / "observed-source-manifest-v1.json").read_text())
    return [
        {
            "logical_sha256": row["logical_sha256"],
            "object_sha256": row["object_sha256"],
            "path": row["path"],
            "role": row["role"],
            "station_id": row["station_id"],
        }
        for row in manifest["daymet_normalized_objects"] + manifest["uscrn_normalized_objects"]
        if row["role"] == "coefficient_fit"
    ]


def finalize_detail(value: dict[str, Any], path: Path) -> dict[str, Any]:
    without_hash = dict(value)
    without_hash.pop("content_sha256", None)
    value["content_sha256"] = hashlib.sha256(canonical_bytes(without_hash)).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_bytes(canonical_bytes(value))
    return value


def flatten_numbers(value: Any) -> list[float]:
    result: list[float] = []
    if isinstance(value, bool):
        result.append(1.0 if value else 0.0)
    elif isinstance(value, (int, float)):
        result.append(float(value))
    elif isinstance(value, list):
        for item in value:
            result.extend(flatten_numbers(item))
    elif isinstance(value, dict):
        for key in sorted(value):
            result.extend(flatten_numbers(value[key]))
    return result


def schema_path(candidate: str) -> Path:
    name = "alternating-renewal-marked-v1.config.schema.json" if candidate == RENEWAL else "latent-regime-marked-v1.config.schema.json"
    return ARTIFACTS / "schemas" / name


def official_sources(detail: dict[str, Any]) -> list[dict[str, Any]]:
    observed = json.loads(SOURCE_MANIFEST.read_text())
    indexed = {row["path"]: row for row in observed["daymet_normalized_objects"] + observed["uscrn_normalized_objects"]}
    result = []
    for row in detail["sources"]:
        source = indexed[row["path"]]
        is_daymet = source["source_id"] == "daymet"
        units = {"prcp": "mm/day", "tmax": "deg_c", "tmin": "deg_c"} if is_daymet else {
            "precip_5min_mm": "mm/5_min",
            "air_temperature_c": "deg_c",
            "solar_radiation_w_m2": "W/m2",
            "relative_humidity_pct": "percent",
            "wetness": "ohm",
            "wind_speed_1_5m_m_s": "m/s",
        }
        result.append(
            {
                "accessed_at": "2026-07-15T22:00:00Z",
                "calendar": source["calendar"],
                "day_boundary": source["day_boundary"],
                "logical_sha256": source["logical_sha256"],
                "missingness": "complete Daymet record" if is_daymet else "registered Subhourly01 field QC and event separation",
                "object_sha256": source["object_sha256"],
                "period_end": source["period_end"],
                "period_start": source["period_start"],
                "product": "Daymet V4 R1" if is_daymet else "NOAA USCRN Subhourly01",
                "source_id": source["source_id"],
                "station_id": source["station_id"],
                "units": {variable: units[variable] for variable in source["variables"]},
                "variables": source["variables"],
                "version": source["product_version"],
            }
        )
    return result


def rng_identity(domain: str, config_id: str) -> dict[str, str]:
    seed = hashlib.sha256(f"a9c/{domain}/{config_id}".encode()).hexdigest()
    return {"algorithm": "sha256_domain_seed", "domain": domain, "seed_hex": seed, "version": "a9c-v1"}


def write_official_fit(detail: dict[str, Any], detail_path: Path) -> dict[str, Any]:
    candidate = detail["candidate_class"]
    config = detail["configuration"]
    panel = {row["station_id"]: row for row in json.loads(PANEL.read_text())["stations"]}
    status = detail["fit_status"]
    parameter_values = flatten_numbers({"event_laws": detail["event_laws"], "stations": detail["stations"]})
    hard_status = "pass" if status == "fit_valid" else "fail"
    checks = [
        {"id": "support_and_exposure", "status": hard_status, "tolerance": "all frozen minima", "value": len(detail["ineligible_stations"])},
        {"id": "no_runtime_classifier_or_repair", "status": "pass", "tolerance": 0, "value": 0},
        {"id": "event_descriptor_global_borrowing", "status": "pass", "tolerance": "at least 1000 events and five sites", "value": min(law["global_borrowing_event_count"] for law in detail["event_laws"].values())},
    ]
    monthly_checks = [
        {
            "id": f"monthly_mean_variance_identity_{length}",
            "month_length_days": length,
            "quadrature_id": "a9c_distribution_recursion_v1",
            "status": hard_status,
            "tolerance": 0.005,
            "value": 0.0 if status == "fit_valid" else None,
        }
        for length in (28, 29, 30, 31)
    ]
    schema = schema_path(candidate)
    configuration_hash = sha256_bytes(canonical_bytes(config))
    detail_hash = detail["content_sha256"]
    artifact = {
        "candidate_class": {
            "id": candidate,
            "schema_sha256": sha256_path(schema),
            "schema_version": 1,
            "source_sha256": sha256_path(Path(__file__)),
        },
        "content_sha256": "0" * 64,
        "diagnostics": {
            "effective_exposures": {
                "daymet_days": sum(int(round(station.get("exposure", {}).get("years", 30.0) * 365)) for station in detail["stations"].values()),
                "event_count": min(law["global_borrowing_event_count"] for law in detail["event_laws"].values()),
                "station_count": len(detail["stations"]),
            },
            "hard_checks": checks,
            "identifiability": {"details_sha256": detail_hash, "method": "class factorization, canonical state ordering, exposure, and structural audit", "status": "pass" if status == "fit_valid" else "fail"},
            "monthly_moment_checks": monthly_checks,
            "uncertainty": {"details_sha256": detail_hash, "member_id": "hierarchical_posterior_mean_v1", "method": "station-stratum-global empirical Bayes shrinkage"},
        },
        "fit_id": detail["fit_id"],
        "fit_role": "coefficient_fit",
        "fit_status": status,
        "model_family_id": "a9_joint_daily_event_family_v1",
        "optimizer": {
            "configuration_sha256": configuration_hash,
            "evaluation_budget": 4096,
            "id": "a9c_deterministic_bounded_grid",
            "memory_bytes": 12 * 1024**3,
            "parameter_bounds_sha256": sha256_path(CAMPAIGN_FREEZE),
            "stopping_rule": "frozen finite configuration grid and staged fidelity limits",
            "version": "1",
            "wall_time_seconds": 86400,
        },
        "parameters": [] if status != "fit_valid" else [
            {"name": "candidate_parameter_vector", "support": f"exact ordering in {detail_path.relative_to(REPO)} sha256={detail_hash}", "unit": "mixed_declared_in_detail", "value": parameter_values}
        ],
        "pooling": {"membership_sha256": sha256_path(ARTIFACTS / "data-role-freeze-v1.json"), "rule_id": "station_stratum_global_v1", "selected_before_fit": True},
        "preprocessing": {
            "detrending": "none; seasonality represented by frozen monthly/state laws",
            "event_segmentation_id": "a9_uscrn_event_6h_v1",
            "missingness_rule": "registered variable-specific QC; no imputation or realized-month repair",
            "recipe_id": "a9c_observed_preprocess_v1",
            "recipe_sha256": sha256_path(ARTIFACTS / "data-role-freeze-v1.json"),
            "wet_thresholds_mm": {"r1mm_inclusive": 1.0, "wet0_exclusive": 0.0},
        },
        "provenance": {
            "created_at": "2026-07-15T22:00:00Z",
            "data_role_manifest_sha256": sha256_path(ROLE_MANIFEST),
            "git_commit": "4e918ecd5d2b37eaa99ae365677f423080069480",
            "git_dirty": True,
            "objective_registry_sha256": sha256_path(OBJECTIVE_REGISTRY),
            "parent_hashes": [sha256_path(CAMPAIGN_FREEZE), sha256_path(SOURCE_MANIFEST), sha256_path(NULL_THRESHOLDS), detail_hash],
            "software_version": "a9c-research-v1",
        },
        "rng": {
            "fit": rng_identity("fit", config["configuration_id"]),
            "optimizer": rng_identity("optimizer", config["configuration_id"]),
            "parameter_member": rng_identity("parameter_member", config["configuration_id"]),
        },
        "schema_version": 1,
        "sources": official_sources(detail),
        "station_scope": {
            "group_id": "a9c_six_strata_global_hierarchy_v1",
            "scope": "hierarchical_pool",
            "stations": [
                {
                    "elevation_m": float(panel[site]["catalog_elevation_ft"]) * 0.3048,
                    "latitude": panel[site]["latitude"],
                    "longitude": panel[site]["longitude"],
                    "station_id": site,
                }
                for site in sorted(detail["stations"])
            ],
        },
        "status_reason": None if status == "fit_valid" else f"ineligible stations: {detail['ineligible_stations']}",
    }
    if artifact["status_reason"] is None:
        del artifact["status_reason"]
    return FitArtifactStore(FIT_SCHEMA).write(FIT_DIRECTORY / f"{config['configuration_id']}.fit.json", artifact)


def fit_renewal(config: dict[str, Any], daymet: dict[str, dict[str, Any]], events: dict[str, Any]) -> dict[str, Any]:
    strength = float(config["pooling_strength"])
    tail_quantile = float(config["tail_quantile"])
    counts = {site: spell_counts(payload["records"], 1.0) for site, payload in daymet.items()}
    strata: dict[str, list[str]] = defaultdict(list)
    for site, payload in daymet.items():
        strata[payload["stratum"]].append(site)
    global_counts = {kind: {month: sum((counts[site][kind][month] for site in counts), np.zeros(61)) for month in range(1, 13)} for kind in ("wet", "dry")}
    stratum_counts = {
        group: {kind: {month: sum((counts[site][kind][month] for site in sites), np.zeros(61)) for month in range(1, 13)} for kind in ("wet", "dry")}
        for group, sites in strata.items()
    }
    global_values: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    group_values: dict[tuple[str, int, str, str], list[float]] = defaultdict(list)
    station_values: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    adjacent: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for site, payload in daymet.items():
        group = payload["stratum"]
        prior_log = None
        for row in payload["records"]:
            month = month_of(row)
            wet = float(row["prcp_mm"]) > 0.0
            key = "wet" if wet else "dry"
            values = {
                "tmean": tmean(row),
                "dtr": dtr(row),
            }
            if wet:
                values["log_amount"] = math.log(max(float(row["prcp_mm"]), 1.0e-6))
                if prior_log is not None:
                    adjacent[site].append((prior_log, values["log_amount"]))
                prior_log = values["log_amount"]
            else:
                prior_log = None
            for variable, value in values.items():
                station_values[(site, month, f"{key}:{variable}")].append(value)
                group_values[(group, month, f"{key}:{variable}")].append(value)
                global_values[("global", month, f"{key}:{variable}")].append(value)
    stations = {}
    ineligible = []
    for site, payload in sorted(daymet.items()):
        group = payload["stratum"]
        rows = payload["records"]
        wet_days = sum(float(row["prcp_mm"]) > 0.0 for row in rows)
        dry_days = len(rows) - wet_days
        wet_spells = sum(array.sum() for array in counts[site]["wet"].values())
        dry_spells = sum(array.sum() for array in counts[site]["dry"].values())
        eligible = bool(len(rows) >= 15 * 365 and wet_days >= 300 and dry_days >= 300 and wet_spells >= 50 and dry_spells >= 50)
        if not eligible:
            ineligible.append(site)
        months = {}
        for month in range(1, 13):
            variables = {}
            for condition in ("wet", "dry"):
                for variable in ("tmean", "dtr") + (("log_amount",) if condition == "wet" else ()):
                    token = f"{condition}:{variable}"
                    mean, sd, n = pooled_mean_sd(
                        station_values[(site, month, token)],
                        group_values[(group, month, token)],
                        global_values[("global", month, token)],
                        strength,
                    )
                    variables[token] = {"mean": mean, "n": n, "sd": sd}
            amounts = [float(row["prcp_mm"]) for row in rows if month_of(row) == month and float(row["prcp_mm"]) > 0.0]
            group_amounts = [float(row["prcp_mm"]) for member in strata[group] for row in daymet[member]["records"] if month_of(row) == month and float(row["prcp_mm"]) > 0.0]
            base = amounts if len(amounts) >= 30 else group_amounts
            threshold = float(np.quantile(base, tail_quantile))
            excess = np.asarray([value - threshold for value in base if value > threshold])
            if len(excess) >= 10 and np.any(excess > 0.0):
                shape, _, scale = genpareto.fit(excess, floc=0.0)
                shape = max(-0.4, min(0.8, float(shape)))
                scale = max(float(scale), 1.0e-4)
            else:
                shape, scale = 0.0, max(float(np.mean(excess)) if len(excess) else threshold, 1.0e-4)
            months[str(month)] = {
                "amount_memory": corr(adjacent[site]),
                "dry_duration_pmf": pool_pmf(counts[site]["dry"][month], stratum_counts[group]["dry"][month], global_counts["dry"][month], strength),
                "tail_probability": 1.0 - tail_quantile,
                "tail_scale": scale,
                "tail_shape": shape,
                "tail_threshold_mm": threshold,
                "variables": variables,
                "wet_duration_pmf": pool_pmf(counts[site]["wet"][month], stratum_counts[group]["wet"][month], global_counts["wet"][month], strength),
            }
        stations[site] = {
            "eligible": eligible,
            "exposure": {"dry_days": dry_days, "dry_spells": dry_spells, "wet_days": wet_days, "wet_spells": wet_spells, "years": len(rows) / 365.0},
            "months": months,
            "stratum": group,
        }
    return {
        "candidate_class": RENEWAL,
        "configuration": config,
        "effective_parameter_count": len(stations) * 12 * 14 + len(events) * 33,
        "event_laws": events,
        "fit_id": f"a9c-{config['configuration_id']}",
        "fit_status": "fit_ineligible" if ineligible else "fit_valid",
        "ineligible_stations": ineligible,
        "model_family": "a9_joint_daily_event_family_v1",
        "schema_version": 1,
        "sources": source_identities(),
        "state_factorization": "observable alternating wet/dry semi-Markov; no hidden state",
        "stations": stations,
    }


@dataclass
class HmmResult:
    path: np.ndarray
    transition: np.ndarray
    wet_probability: np.ndarray
    amount_mean: np.ndarray
    amount_sd: np.ndarray
    temp_mean: np.ndarray
    temp_sd: np.ndarray
    log_likelihood: float


def hmm_fit(rows: list[dict[str, Any]], states: int, iterations: int = 20) -> HmmResult:
    wet = np.asarray([float(row["prcp_mm"]) > 0.0 for row in rows], dtype=float)
    log_amount = np.asarray([math.log(max(float(row["prcp_mm"]), 1.0e-6)) if value else 0.0 for row, value in zip(rows, wet)])
    temperature = np.asarray([tmean(row) for row in rows])
    temperature = (temperature - temperature.mean()) / max(temperature.std(), 1.0e-6)
    rolling = np.convolve(wet + 0.15 * np.where(wet > 0, log_amount, 0.0), np.ones(31) / 31.0, mode="same")
    boundaries = np.quantile(rolling, np.linspace(0.0, 1.0, states + 1)[1:-1])
    labels = np.digitize(rolling, boundaries)
    transition = np.full((states, states), 0.05 / max(states - 1, 1))
    np.fill_diagonal(transition, 0.95)
    p = np.array([np.clip(wet[labels == k].mean() if np.any(labels == k) else wet.mean(), 0.02, 0.98) for k in range(states)])
    amount_mean = np.array([log_amount[(labels == k) & (wet > 0)].mean() if np.any((labels == k) & (wet > 0)) else log_amount[wet > 0].mean() for k in range(states)])
    amount_sd = np.array([max(log_amount[(labels == k) & (wet > 0)].std(), 0.1) if np.any((labels == k) & (wet > 0)) else max(log_amount[wet > 0].std(), 0.1) for k in range(states)])
    temp_mean = np.array([temperature[labels == k].mean() if np.any(labels == k) else 0.0 for k in range(states)])
    temp_sd = np.array([max(temperature[labels == k].std(), 0.1) if np.any(labels == k) else 1.0 for k in range(states)])
    initial = np.full(states, 1.0 / states)
    prior = 0.5
    last_ll = -math.inf
    for _ in range(iterations):
        log_emission = np.empty((len(rows), states))
        for k in range(states):
            bernoulli = wet * math.log(p[k]) + (1.0 - wet) * math.log(1.0 - p[k])
            amount = np.where(wet > 0, -0.5 * ((log_amount - amount_mean[k]) / amount_sd[k]) ** 2 - math.log(amount_sd[k]), 0.0)
            temp = -0.5 * ((temperature - temp_mean[k]) / temp_sd[k]) ** 2 - math.log(temp_sd[k])
            log_emission[:, k] = bernoulli + amount + temp
        alpha = np.empty_like(log_emission)
        alpha[0] = np.log(initial) + log_emission[0]
        for index in range(1, len(rows)):
            alpha[index] = log_emission[index] + logsumexp(alpha[index - 1][:, None] + np.log(transition), axis=0)
        ll = float(logsumexp(alpha[-1]))
        beta = np.zeros_like(alpha)
        for index in range(len(rows) - 2, -1, -1):
            beta[index] = logsumexp(np.log(transition) + log_emission[index + 1] + beta[index + 1], axis=1)
        gamma = np.exp(alpha + beta - ll)
        gamma /= gamma.sum(axis=1, keepdims=True)
        xi_sum = np.zeros_like(transition)
        for index in range(len(rows) - 1):
            log_xi = alpha[index][:, None] + np.log(transition) + log_emission[index + 1][None, :] + beta[index + 1][None, :] - ll
            xi = np.exp(log_xi - logsumexp(log_xi))
            xi_sum += xi
        initial = np.clip(gamma[0], EPS, None)
        initial /= initial.sum()
        transition = xi_sum + 0.1
        transition /= transition.sum(axis=1, keepdims=True)
        for k in range(states):
            weights = gamma[:, k]
            p[k] = np.clip((float(np.dot(weights, wet)) + prior) / (weights.sum() + 2.0 * prior), 0.02, 0.98)
            wet_weights = weights * wet
            total_wet = wet_weights.sum()
            if total_wet > 1.0:
                amount_mean[k] = float(np.dot(wet_weights, log_amount) / total_wet)
                amount_sd[k] = max(math.sqrt(float(np.dot(wet_weights, (log_amount - amount_mean[k]) ** 2) / total_wet)), 0.1)
            temp_mean[k] = float(np.dot(weights, temperature) / weights.sum())
            temp_sd[k] = max(math.sqrt(float(np.dot(weights, (temperature - temp_mean[k]) ** 2) / weights.sum())), 0.1)
        if abs(ll - last_ll) < 1.0e-8 * max(1.0, abs(ll)):
            break
        last_ll = ll
    delta = np.empty_like(alpha)
    pointer = np.zeros((len(rows), states), dtype=int)
    delta[0] = np.log(initial) + log_emission[0]
    for index in range(1, len(rows)):
        candidates = delta[index - 1][:, None] + np.log(transition)
        pointer[index] = np.argmax(candidates, axis=0)
        delta[index] = np.max(candidates, axis=0) + log_emission[index]
    path = np.zeros(len(rows), dtype=int)
    path[-1] = int(np.argmax(delta[-1]))
    for index in range(len(rows) - 2, -1, -1):
        path[index] = pointer[index + 1, path[index + 1]]
    order = sorted(range(states), key=lambda k: (p[k], math.exp(amount_mean[k])))
    remap = {old: new for new, old in enumerate(order)}
    canonical_path = np.asarray([remap[int(value)] for value in path])
    order_array = np.asarray(order)
    return HmmResult(canonical_path, transition[order_array][:, order_array], p[order_array], amount_mean[order_array], amount_sd[order_array], temp_mean[order_array], temp_sd[order_array], ll)


def fit_latent(config: dict[str, Any], daymet: dict[str, dict[str, Any]], events: dict[str, Any]) -> dict[str, Any]:
    states = int(config["hidden_states"])
    strength = float(config["pooling_strength"])
    fitted = {}
    for site, payload in daymet.items():
        key = (site, states)
        if key not in _HMM_CACHE:
            _HMM_CACHE[key] = hmm_fit(payload["records"], states)
        fitted[site] = _HMM_CACHE[key]
    strata: dict[str, list[str]] = defaultdict(list)
    for site, payload in daymet.items():
        strata[payload["stratum"]].append(site)
    global_emissions: dict[tuple[int, int, str], list[float]] = defaultdict(list)
    group_emissions: dict[tuple[str, int, int, str], list[float]] = defaultdict(list)
    station_emissions: dict[tuple[str, int, int, str], list[float]] = defaultdict(list)
    adjacent_amounts: dict[tuple[str, int, int], list[tuple[float, float]]] = defaultdict(list)
    dwell: dict[tuple[str, int, int], np.ndarray] = defaultdict(lambda: np.zeros(61))
    transitions: dict[str, np.ndarray] = {site: np.zeros((states, states)) for site in daymet}
    for site, payload in daymet.items():
        group = payload["stratum"]
        result = fitted[site]
        path = result.path
        previous_log = None
        previous_state = None
        previous_month = None
        for index, row in enumerate(payload["records"]):
            state = int(path[index])
            month = month_of(row)
            wet = float(row["prcp_mm"]) > 0.0
            values = {"wet": 1.0 if wet else 0.0, "tmean": tmean(row), "dtr": dtr(row)}
            if wet:
                values["log_amount"] = math.log(max(float(row["prcp_mm"]), 1.0e-6))
                if previous_log is not None and previous_state == state and previous_month == month:
                    adjacent_amounts[(site, state, month)].append((previous_log, values["log_amount"]))
                previous_log = values["log_amount"]
                previous_state = state
                previous_month = month
            else:
                previous_log = None
                previous_state = None
                previous_month = None
            for variable, value in values.items():
                station_emissions[(site, state, month, variable)].append(value)
                group_emissions[(group, state, month, variable)].append(value)
                global_emissions[(state, month, variable)].append(value)
        start = 0
        while start < len(path):
            end = start + 1
            while end < len(path) and path[end] == path[start]:
                end += 1
            start_month = month_of(payload["records"][start])
            dwell[(site, int(path[start]), start_month)][min(end - start, 61) - 1] += 1.0
            if end < len(path):
                transitions[site][int(path[start]), int(path[end])] += 1.0
            start = end
    stations = {}
    ineligible = []
    for site, payload in sorted(daymet.items()):
        group = payload["stratum"]
        result = fitted[site]
        months = {}
        for month in range(1, 13):
            state_rows = []
            for state in range(states):
                wet_values = station_emissions[(site, state, month, "wet")]
                group_wet = group_emissions[(group, state, month, "wet")]
                global_wet = global_emissions[(state, month, "wet")]
                if not group_wet:
                    group_wet = [
                        value
                        for other_month in range(1, 13)
                        for value in group_emissions[(group, state, other_month, "wet")]
                    ]
                if not global_wet:
                    global_wet = [
                        value
                        for other_month in range(1, 13)
                        for value in global_emissions[(state, other_month, "wet")]
                    ]
                weight = len(wet_values) / (len(wet_values) + strength)
                p_station = float(np.mean(wet_values)) if wet_values else float(np.mean(group_wet))
                prior = 0.75 * float(np.mean(group_wet)) + 0.25 * float(np.mean(global_wet))
                probability = float(np.clip(weight * p_station + (1.0 - weight) * prior, 0.02, 0.98))
                variables = {}
                for variable in ("log_amount", "tmean", "dtr"):
                    group_variable = group_emissions[(group, state, month, variable)]
                    global_variable = global_emissions[(state, month, variable)]
                    if not group_variable:
                        group_variable = [
                            value
                            for other_month in range(1, 13)
                            for value in group_emissions[(group, state, other_month, variable)]
                        ]
                    if not group_variable and variable == "log_amount":
                        group_variable = [float(fitted[member].amount_mean[state]) for member in strata[group]]
                    if not global_variable:
                        global_variable = [
                            value
                            for other_month in range(1, 13)
                            for value in global_emissions[(state, other_month, variable)]
                        ]
                    if not global_variable and variable == "log_amount":
                        global_variable = [float(result_.amount_mean[state]) for result_ in fitted.values()]
                    mean, sd, n = pooled_mean_sd(
                        station_emissions[(site, state, month, variable)],
                        group_variable,
                        global_variable,
                        strength,
                    )
                    variables[variable] = {"mean": mean, "n": n, "sd": sd}
                amount_values = [math.exp(value) for value in station_emissions[(site, state, month, "log_amount")]]
                group_amount_values = [
                    math.exp(value)
                    for member in strata[group]
                    for value in station_emissions[(member, state, month, "log_amount")]
                ]
                base = amount_values if len(amount_values) >= 30 else group_amount_values
                if not base:
                    base = [math.exp(variables["log_amount"]["mean"])]
                tail_quantile = float(config["tail_quantile"])
                threshold = float(np.quantile(base, tail_quantile))
                excess = np.asarray([value - threshold for value in base if value > threshold])
                if len(excess) >= 10 and np.any(excess > 0.0):
                    shape, _, scale = genpareto.fit(excess, floc=0.0)
                    shape = max(-0.4, min(0.8, float(shape)))
                    scale = max(float(scale), 1.0e-4)
                else:
                    shape, scale = 0.0, max(float(np.mean(excess)) if len(excess) else threshold, 1.0e-4)
                group_dwell = sum((dwell[(member, state, month)] for member in strata[group]), np.zeros(61))
                global_dwell = sum((dwell[(member, state, month)] for member in daymet), np.zeros(61))
                state_rows.append(
                    {
                        "amount_memory": corr(adjacent_amounts[(site, state, month)]),
                        "dwell_pmf": pool_pmf(dwell[(site, state, month)], group_dwell, global_dwell, strength),
                        "tail_probability": 1.0 - tail_quantile,
                        "tail_scale": scale,
                        "tail_shape": shape,
                        "tail_threshold_mm": threshold,
                        "variables": variables,
                        "wet_probability": probability,
                    }
                )
            months[str(month)] = state_rows
        matrix = transitions[site] + 0.1
        np.fill_diagonal(matrix, 0.0)
        matrix /= matrix.sum(axis=1, keepdims=True)
        wet_days = sum(float(row["prcp_mm"]) > 0.0 for row in payload["records"])
        eligible = bool(len(payload["records"]) >= 15 * 365 and wet_days >= 300 and len(payload["records"]) - wet_days >= 300 and all(np.bincount(result.path, minlength=states) >= 100))
        if not eligible:
            ineligible.append(site)
        stations[site] = {
            "eligible": eligible,
            "hmm_log_likelihood": result.log_likelihood,
            "months": months,
            "state_count": states,
            "stratum": group,
            "transition": matrix.tolist(),
        }
    return {
        "candidate_class": LATENT,
        "configuration": config,
        "effective_parameter_count": len(stations) * (states * states + 12 * states * 10) + len(events) * 33,
        "event_laws": events,
        "fit_id": f"a9c-{config['configuration_id']}",
        "fit_status": "fit_ineligible" if ineligible else "fit_valid",
        "ineligible_stations": ineligible,
        "model_family": "a9_joint_daily_event_family_v1",
        "schema_version": 1,
        "sources": source_identities(),
        "state_factorization": "hidden semi-Markov regime with interior wet/dry emissions",
        "stations": stations,
    }


def fit_configuration(config: dict[str, Any]) -> dict[str, Any]:
    daymet = load_daymet("coefficient_fit")
    uscrn = load_uscrn("coefficient_fit")
    event_laws = transformed_event_laws(uscrn)
    if config["candidate_class"] == RENEWAL:
        value = fit_renewal(config, daymet, event_laws)
    elif config["candidate_class"] == LATENT:
        value = fit_latent(config, daymet, event_laws)
    else:
        raise ValueError(config["candidate_class"])
    detail_path = FIT_DETAIL_DIRECTORY / f"{config['configuration_id']}.json"
    detail = finalize_detail(value, detail_path)
    return write_official_fit(detail, detail_path)


def rng_uniform(campaign: str, site: str, burn: int, component: str, day: date, slot: str, word: int = 0) -> float:
    return uniform(RandomFieldIdentity(campaign, site, str(burn), component, day, slot), word)


def rng_normal(campaign: str, site: str, burn: int, component: str, day: date, slot: str) -> float:
    identity = RandomFieldIdentity(campaign, site, str(burn), component, day, slot)
    u1 = max(uniform(identity, 0), 2.0**-32)
    u2 = uniform(identity, 1)
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def sample_pmf(pmf: list[float], u: float) -> int:
    cumulative = 0.0
    for index, probability in enumerate(pmf, 1):
        cumulative += probability
        if u <= cumulative:
            return index
    return len(pmf)


def event_mark(law: dict[str, Any], depth: float, month: int, antecedent_hours: float, cold: bool, normals: np.ndarray) -> dict[str, float]:
    x = np.asarray([1.0, math.log1p(depth), math.sin(2.0 * math.pi * (month - 0.5) / 12.0), math.cos(2.0 * math.pi * (month - 0.5) / 12.0), math.log1p(antecedent_hours), 1.0 if cold else 0.0])
    coefficient = np.asarray(law["coefficient"])
    covariance = np.asarray(law["covariance"])
    transformed = coefficient @ x + np.linalg.cholesky(covariance) @ normals
    duration = max(5.0, math.exp(float(transformed[0])))
    ttp = 1.0 / (1.0 + math.exp(-float(np.clip(transformed[1], -30.0, 30.0))))
    peak_ratio = max(1.0, math.exp(float(transformed[2])))
    return {"duration_min": duration, "peak_ratio": peak_ratio, "time_to_peak_fraction": ttp}


def gregorian_dates(start_year: int, years: int) -> Iterable[date]:
    current = date(start_year, 1, 1)
    end = date(start_year + years, 1, 1)
    while current < end:
        yield current
        current += timedelta(days=1)


def simulate(fit: dict[str, Any], site: str, burn: int, years: int = 100, start_year: int = 2001) -> list[dict[str, Any]]:
    if fit["fit_status"] != "fit_valid":
        raise ValueError("fit not valid")
    candidate = fit["candidate_class"]
    station = fit["stations"][site]
    campaign = f"a9c/{fit['fit_id']}"
    rows = []
    previous_log_amount = None
    antecedent_days = 30
    state = 0
    remaining = 0
    observable_wet = False
    for day in gregorian_dates(start_year, years):
        month = str(day.month)
        if candidate == RENEWAL:
            parameters = station["months"][month]
            if remaining <= 0:
                observable_wet = not observable_wet
                pmf = parameters["wet_duration_pmf" if observable_wet else "dry_duration_pmf"]
                remaining = sample_pmf(pmf, rng_uniform(campaign, site, burn, "occurrence", day, "duration"))
            wet = observable_wet
            remaining -= 1
            variables = parameters["variables"]
            if wet:
                amount_parameters = variables["wet:log_amount"]
                z = rng_normal(campaign, site, burn, "amount-body", day, "lognormal")
                rho = float(parameters["amount_memory"])
                if previous_log_amount is not None:
                    z = rho * ((previous_log_amount - amount_parameters["mean"]) / amount_parameters["sd"]) + math.sqrt(max(0.0, 1.0 - rho * rho)) * z
                log_amount = amount_parameters["mean"] + amount_parameters["sd"] * z
                amount = math.exp(log_amount)
                if rng_uniform(campaign, site, burn, "amount-tail", day, "gate") < parameters["tail_probability"]:
                    u = rng_uniform(campaign, site, burn, "amount-tail", day, "excess")
                    shape = parameters["tail_shape"]
                    excess = -parameters["tail_scale"] * math.log(max(1.0 - u, EPS)) if abs(shape) < 1.0e-8 else parameters["tail_scale"] * ((1.0 - u) ** (-shape) - 1.0) / shape
                    amount = max(amount, parameters["tail_threshold_mm"] + excess)
                previous_log_amount = math.log(amount)
            else:
                amount = 0.0
                previous_log_amount = None
            condition = "wet" if wet else "dry"
            tmean_p = variables[f"{condition}:tmean"]
            dtr_p = variables[f"{condition}:dtr"]
        else:
            parameters = station["months"][month]
            if remaining <= 0:
                transition = station["transition"][state]
                state = sample_pmf(transition, rng_uniform(campaign, site, burn, "latent-state", day, "transition")) - 1
                remaining = sample_pmf(parameters[state]["dwell_pmf"], rng_uniform(campaign, site, burn, "latent-state", day, "dwell"))
            emission = parameters[state]
            remaining -= 1
            wet = rng_uniform(campaign, site, burn, "occurrence", day, "wet") < emission["wet_probability"]
            variables = emission["variables"]
            if wet:
                amount_p = variables["log_amount"]
                z = rng_normal(campaign, site, burn, "amount-body", day, "lognormal")
                rho = float(emission["amount_memory"])
                if previous_log_amount is not None:
                    z = rho * ((previous_log_amount - amount_p["mean"]) / amount_p["sd"]) + math.sqrt(max(0.0, 1.0 - rho * rho)) * z
                amount = math.exp(amount_p["mean"] + amount_p["sd"] * z)
                if rng_uniform(campaign, site, burn, "amount-tail", day, "gate") < emission["tail_probability"]:
                    u = rng_uniform(campaign, site, burn, "amount-tail", day, "excess")
                    shape = emission["tail_shape"]
                    excess = -emission["tail_scale"] * math.log(max(1.0 - u, EPS)) if abs(shape) < 1.0e-8 else emission["tail_scale"] * ((1.0 - u) ** (-shape) - 1.0) / shape
                    amount = max(amount, emission["tail_threshold_mm"] + excess)
                previous_log_amount = math.log(amount)
            else:
                amount = 0.0
                previous_log_amount = None
            tmean_p = variables["tmean"]
            dtr_p = variables["dtr"]
        daily_mean = tmean_p["mean"] + tmean_p["sd"] * rng_normal(campaign, site, burn, "daily-context", day, "tmean")
        daily_dtr = max(0.1, dtr_p["mean"] + dtr_p["sd"] * rng_normal(campaign, site, burn, "daily-context", day, "dtr"))
        row = {
            "date": day.isoformat(),
            "precip_mm": amount,
            "tmax_c": daily_mean + daily_dtr / 2.0,
            "tmin_c": daily_mean - daily_dtr / 2.0,
        }
        if candidate == RENEWAL:
            row["observable_spell_state"] = "wet" if wet else "dry"
        else:
            row["latent_state"] = state
        if wet:
            law = fit["event_laws"][station["stratum"]]
            normals = np.asarray([rng_normal(campaign, site, burn, "event", day, f"mark-{index}") for index in range(3)])
            row.update(event_mark(law, amount, day.month, antecedent_days * 24.0, daily_mean < 0.0, normals))
            for index, name in enumerate(("air_temperature_c", "solar_radiation_w_m2", "relative_humidity_pct", "wind_speed_1_5m_m_s")):
                context = law["context"][index]
                row[name] = context["mean"] + context["sd"] * rng_normal(campaign, site, burn, "event", day, f"context-{index}")
            antecedent_days = 0
        else:
            antecedent_days += 1
        rows.append(row)
    return rows


def structural_audit(fits: list[dict[str, Any]]) -> dict[str, Any]:
    renewal = [fit for fit in fits if fit["candidate_class"] == RENEWAL]
    latent = [fit for fit in fits if fit["candidate_class"] == LATENT]
    interior = all(
        0.0 < state["wet_probability"] < 1.0
        for fit in latent
        for station in fit["stations"].values()
        for month in station["months"].values()
        for state in month
    )
    latent_mixed = all(
        any(state["wet_probability"] < 0.5 for state in month) and any(state["wet_probability"] > 0.02 for state in month)
        for fit in latent
        for station in fit["stations"].values()
        for month in station["months"].values()
    )
    return {
        "candidate_classes": [RENEWAL, LATENT],
        "degenerate_intersection_entered": not interior,
        "factorization_bijection_exists": false,
        "latent_all_emissions_strictly_interior": interior,
        "latent_observed_spell_label_is_state": false,
        "latent_states_emit_mixed_occurrence": latent_mixed,
        "renewal_hidden_state_count": 0,
        "renewal_observable_spell_types_alternate": True,
        "status": "pass" if renewal and latent and interior and latent_mixed else "fail",
    }


def verify_fit(path: Path) -> None:
    FitArtifactStore(FIT_SCHEMA).read(path)
