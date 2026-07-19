#!/usr/bin/env python3
"""Execute the frozen A10M5R7 inference-mode and conditional temporal probe."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

import legacy_core as legacy
import screen_core_v2 as core
from temporal_metrics import realized_metrics


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    partial.replace(path)


def date_axis(begin_year: int, years: int) -> list[dt.date]:
    start = dt.date(begin_year, 1, 1)
    end = dt.date(begin_year + years, 1, 1)
    return [start + dt.timedelta(days=index) for index in range((end - start).days)]


def verify_reconstruction(output: Path, expected: dict[str, Any]) -> dict[str, Any]:
    checkpoint_path = output / "checkpoint.pt"
    checkpoint = read_json(output / "checkpoint-record.json")
    export = read_json(output / "export-metadata.json")
    checks = {
        "checkpoint_payload_bytes": checkpoint_path.stat().st_size,
        "checkpoint_payload_sha256": digest(checkpoint_path),
        "checkpoint_epoch": checkpoint["epoch"],
        "checkpoint_global_step": checkpoint["global_step"],
        "training_seed": checkpoint["training_seed"],
        "corpus_cursor_epoch_order_sha256": checkpoint["corpus_cursor"]["epoch_order_sha256"],
        "corpus_cursor_next_batch": checkpoint["corpus_cursor"]["next_batch"],
        "model_record_sha256": digest(output / "model-record.json"),
        "capacity_id": export["capacity_id"],
        "family": export["family"],
        "hidden_size": export["hidden_size"],
        "parameter_count": export["parameter_count"],
        "validation_primary_nll": export["validation_primary_nll"],
        "validation_stability": export["validation_stability"],
        "validation_tail_score": export["validation_tail_score"],
    }
    for label, actual in checks.items():
        if actual != expected[label]:
            raise RuntimeError(f"accepted reconstruction mismatch: {label}")
    if export["row_id"] != expected["row_id"]:
        raise RuntimeError("accepted reconstruction mismatch: row_id")
    return checks


def reconstruct(
    run_root: Path,
    corpus: Path,
    output: Path,
    row_id: str,
    seed: int,
    expected: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    subprocess.run(
        [
            sys.executable,
            str(run_root / "train.py"),
            "--row-id",
            row_id,
            "--family",
            "lognormal_wet_v2",
            "--capacity",
            "P1",
            "--seed",
            str(seed),
            "--corpus",
            str(corpus),
            "--output",
            str(output),
        ],
        check=True,
    )
    identity = verify_reconstruction(output, expected)
    module = torch.jit.load(str(output / "model-export.pt"), map_location="cuda:0").eval()
    return module, identity


def observation_document(corpus: Path, site: dict[str, Any]) -> dict[str, Any]:
    path = corpus / "artifacts" / site["daymet_shard"]
    if digest(path) != site["daymet_shard_sha256"]:
        raise RuntimeError("observation shard identity mismatch")
    with tarfile.open(path, "r:gz") as archive:
        handle = archive.extractfile(f"{site['point_id']}.json")
        if handle is None:
            raise RuntimeError("observation point absent")
        return json.load(handle)


def observed_surface(document: dict[str, Any]) -> tuple[list[dt.date], list[np.ndarray], dict[dt.date, np.ndarray]]:
    fields = legacy.FIELDS
    dates: list[dt.date] = []
    values: list[list[float]] = [[], [], []]
    conditioning: dict[dt.date, np.ndarray] = {}
    for index, text in enumerate(document["dates"]):
        date = dt.date.fromisoformat(text)
        raw = [document["fields"][field][index] for field in fields]
        source_observed = bool(document["source_observed"][index])
        if source_observed and all(value is not None for value in raw):
            conditioning[date] = np.asarray(raw, dtype=np.float32)
        common = [document["fields"][field][index] for field in ("prcp", "tmax", "tmin")]
        if source_observed and all(value is not None for value in common):
            dates.append(date)
            for target, value in zip(values, common):
                target.append(float(value))
    arrays = [np.asarray(value, dtype=np.float64) for value in values]
    if len(dates) != 10950:
        raise RuntimeError("observation row contract mismatch")
    return dates, arrays, conditioning


def uniforms(point_id: str, burn: int, members: list[int], days: int) -> np.ndarray:
    rows = []
    for member in members:
        words = legacy.philox_words(point_id, burn, member, days)
        rows.append((words.astype(np.float64) + 0.5) / 4294967296.0)
    return np.stack(rows)


def sample_heads(heads: torch.Tensor, random: torch.Tensor) -> torch.Tensor:
    """Sample raw seven-field weather from heads and four registered uniforms."""
    probability = torch.sigmoid(heads[..., 0])
    wet = random[..., 0] < probability
    parameters, continuous_start = core.amount_parameters(heads, "lognormal_wet_v2")
    amount = core.amount_quantile(parameters, "lognormal_wet_v2", random[..., 1])
    locations = heads[..., continuous_start::2]
    scales = torch.nn.functional.softplus(heads[..., continuous_start + 1 :: 2]) + 1e-4
    offsets = torch.arange(6, device=heads.device, dtype=heads.dtype) / 7.0
    normals = torch.sqrt(-2.0 * torch.log(random[..., 1:2])) * torch.cos(
        2.0 * math.pi * (random[..., 2:3] + offsets)
    )
    values = locations + scales * normals
    tmean = values[..., 0]
    dtr = torch.exp(values[..., 1])
    return torch.stack(
        (
            wet * amount,
            tmean + dtr / 2.0,
            tmean - dtr / 2.0,
            torch.exp(values[..., 2]),
            torch.exp(values[..., 3]),
            torch.exp(values[..., 4]),
            86400.0 * torch.sigmoid(values[..., 5]),
        ),
        dim=-1,
    )


def supported(values: np.ndarray) -> bool:
    return bool(
        np.isfinite(values).all()
        and np.all(values[..., 0] >= 0.0)
        and np.all(values[..., 1] >= values[..., 2])
        and np.all(values[..., 3:7] >= 0.0)
        and np.all(values[..., 6] <= 86400.0)
    )


def summarize(
    mode: str,
    site: dict[str, Any],
    seed: int,
    members: list[int],
    dates: list[dt.date],
    values: np.ndarray,
) -> list[dict[str, Any]]:
    records = []
    for member_index, member in enumerate(members):
        stream = values[member_index]
        records.append(
            {
                "mode": mode,
                "point_id": site["point_id"],
                "regime": site["regime"],
                "training_seed": seed,
                "member_id": member,
                "row_count": len(stream),
                "stream_sha256": hashlib.sha256(stream.astype("<f4").tobytes()).hexdigest(),
                "support": supported(stream),
                "metrics": realized_metrics(dates, stream[:, 0], stream[:, 1], stream[:, 2]),
            }
        )
    return records


def open_loop(
    module: Any,
    site: dict[str, Any],
    members: list[int],
    years: int,
    burn: int,
) -> tuple[list[dt.date], np.ndarray]:
    dates = date_axis(2001, years)
    days = len(dates)
    random_np = uniforms(site["point_id"], burn, members, days)
    features = torch.from_numpy(
        legacy.generation_features(years, site["latitude"], site["longitude"], site["elevation_m"])
    ).unsqueeze(0).cuda()
    station = torch.tensor([1200], device="cuda:0")
    hidden = torch.zeros((1, 1, 80), device="cuda:0")
    chunks = []
    with torch.inference_mode():
        for start in range(0, days, 365):
            heads, hidden = module(features[:, start : start + 365], station, hidden)
            chunks.append(heads.squeeze(0))
        heads = torch.cat(chunks).double()
        random = torch.from_numpy(random_np).cuda()
        repeated = heads.unsqueeze(0).expand(len(members), -1, -1)
        output = sample_heads(repeated, random).cpu().numpy()
    return dates, output


def observation_conditioned(
    module: Any,
    site: dict[str, Any],
    members: list[int],
    dates: list[dt.date],
    conditioning: dict[dt.date, np.ndarray],
    means: np.ndarray,
    scales: np.ndarray,
    burn: int,
) -> np.ndarray:
    features = np.zeros((len(dates), 13), dtype=np.float32)
    descriptor = np.asarray(
        [site["latitude"] / 90.0, site["longitude"] / 180.0, site["elevation_m"] / 4000.0],
        dtype=np.float32,
    )
    for index, target in enumerate(dates):
        previous = target - dt.timedelta(days=1)
        if previous in conditioning:
            features[index, :7] = (conditioning[previous] - means) / scales
        year_days = 366 if previous.replace(month=12, day=31).timetuple().tm_yday == 366 else 365
        phase = 2.0 * math.pi * (previous.timetuple().tm_yday - 1) / year_days
        features[index, 7:] = (
            math.sin(phase), math.cos(phase), float(year_days == 366), *descriptor,
        )
    random_np = uniforms(site["point_id"], burn + 10000, members, len(dates))
    station = torch.tensor([1200], device="cuda:0")
    hidden = torch.zeros((1, 1, 80), device="cuda:0")
    chunks = []
    with torch.inference_mode():
        tensor = torch.from_numpy(features).unsqueeze(0).cuda()
        for start in range(0, len(dates), 365):
            heads, hidden = module(tensor[:, start : start + 365], station, hidden)
            chunks.append(heads.squeeze(0))
        heads = torch.cat(chunks).double().unsqueeze(0).expand(len(members), -1, -1)
        output = sample_heads(heads, torch.from_numpy(random_np).cuda()).cpu().numpy()
    return output


def generated_feedback(
    module: Any,
    site: dict[str, Any],
    members: list[int],
    years: int,
    means: np.ndarray,
    scales: np.ndarray,
    burn: int,
) -> tuple[list[dt.date], np.ndarray, bool]:
    dates = date_axis(2001, years)
    days = len(dates)
    random_np = uniforms(site["point_id"], burn, members, days)
    exogenous = legacy.generation_features(
        years, site["latitude"], site["longitude"], site["elevation_m"]
    )
    member_count = len(members)
    hidden = torch.zeros((1, member_count, 80), device="cuda:0")
    station = torch.full((member_count,), 1200, dtype=torch.long, device="cuda:0")
    previous = torch.zeros((member_count, 7), dtype=torch.float32, device="cuda:0")
    means_t = torch.from_numpy(means).cuda()
    scales_t = torch.from_numpy(scales).cuda()
    random = torch.from_numpy(random_np).cuda()
    output = np.empty((member_count, days, 7), dtype=np.float64)
    valid = True
    with torch.inference_mode():
        for day in range(days):
            fixed = torch.from_numpy(exogenous[day, 7:]).cuda().expand(member_count, -1)
            features = torch.cat((previous, fixed), dim=1).unsqueeze(1)
            heads, hidden = module(features, station, hidden)
            sampled = sample_heads(heads[:, 0].double(), random[:, day])
            current = sampled.cpu().numpy()
            output[:, day] = current
            if not supported(current):
                valid = False
                break
            previous = ((sampled.float() - means_t) / scales_t)
    return dates, output, valid and supported(output)


def metric_group(key: str) -> str:
    if key.startswith("occurrence."):
        return "occurrence_spells"
    if key.startswith("annual."):
        return "annual_dependence"
    if "tmax" in key or "tmin" in key:
        return "temperature"
    if key.startswith("monthly.") and key.endswith("precipitation_mean"):
        return "monthly_climatology"
    return "precipitation_distribution"


def signed_scale(key: str, generated: float, observed: float) -> float:
    if "precipitation_" in key and any(
        name in key for name in ("mean", "standard_deviation", "q10", "q50", "q90", "q95")
    ):
        return (math.log(generated + 0.1) - math.log(observed + 0.1)) / 0.25
    if "coefficient_of_variation" in key:
        return (generated - observed) / 0.25
    if "skew" in key:
        return (generated - observed) / 0.5
    if key.startswith("occurrence.") or "dry_frequency" in key:
        return (generated - observed) / 0.05
    if "correlation" in key or "lag1" in key:
        return (generated - observed) / 0.1
    if "tmax_mean" in key or "tmin_mean" in key:
        return generated - observed
    if "tmax_standard_deviation" in key or "tmin_standard_deviation" in key:
        return (generated - observed) / 0.5
    raise RuntimeError(f"unregistered metric: {key}")


def mean_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    keys = set(records[0]["metrics"])
    if any(set(record["metrics"]) != keys for record in records):
        raise RuntimeError("metric key mismatch")
    return {
        key: float(np.mean([record["metrics"][key] for record in records]))
        for key in sorted(keys)
    }


def attribution(
    modes: dict[str, list[dict[str, Any]]],
    references: dict[str, dict[str, dict[str, float]]],
    groups: list[str],
) -> dict[str, Any]:
    components = []
    grouped_values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for mode, records in modes.items():
        by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_point[record["point_id"]].append(record)
        for point, rows in sorted(by_point.items()):
            generated = mean_metrics(rows)
            observed = references[mode][point]
            common = sorted(set(generated) & set(observed))
            for key in common:
                residual = signed_scale(key, generated[key], observed[key])
                group = metric_group(key)
                grouped_values[mode][group].append(abs(residual))
                components.append(
                    {
                        "absolute_scaled_error": abs(residual),
                        "generated": generated[key],
                        "group": group,
                        "metric": key,
                        "mode": mode,
                        "observed": observed[key],
                        "point_id": point,
                        "signed_scaled_residual": residual,
                    }
                )
    summary = {}
    for mode in modes:
        group_errors = {
            group: float(np.mean(grouped_values[mode][group])) for group in groups
        }
        summary[mode] = {
            "family_balanced_error": float(np.mean(list(group_errors.values()))),
            "group_errors": group_errors,
        }
    return {"components": components, "summary": summary}


def architecture_decision(attribution_result: dict[str, Any], contract: dict[str, Any], feedback_support: bool) -> dict[str, Any]:
    diagnostic = contract["diagnostic"]
    summary = attribution_result["summary"]
    accepted = summary["accepted_open_loop"]
    feedback = summary["generated_feedback"]
    conditioned = summary["observation_conditioned"]
    improvement = 1.0 - feedback["family_balanced_error"] / accepted["family_balanced_error"]
    guards = {
        group: feedback["group_errors"][group] <= (1.0 + diagnostic["maximum_group_degradation_fraction"]) * accepted["group_errors"][group]
        for group in diagnostic["groups"]
    }
    feedback_advances = bool(
        feedback_support
        and improvement >= diagnostic["generated_feedback_improvement_fraction"]
        and all(guards.values())
    )
    conditioned_improvement = 1.0 - conditioned["family_balanced_error"] / accepted["family_balanced_error"]
    total = sum(accepted["group_errors"].values())
    shares = {group: accepted["group_errors"][group] / total for group in diagnostic["groups"]}
    if not feedback_support:
        selected = "generated_feedback_support_hold"
        terminal = "HOLD-A10-GENERATED-FEEDBACK-SUPPORT"
    elif feedback_advances:
        selected = contract["candidate_identity"]
        terminal = "A10M5R7-GENERATED-FEEDBACK-ADVANCES"
    elif conditioned_improvement >= diagnostic["observation_conditioned_improvement_fraction"]:
        selected = "closed_loop_rollout_trained_ssm_v1"
        terminal = "A10M5R7-ARCHITECTURE-HYPOTHESIS-READY"
    elif shares["monthly_climatology"] >= diagnostic["monthly_dominance_fraction"]:
        selected = "climate_normal_conditioned_ssm_v1"
        terminal = "A10M5R7-ARCHITECTURE-HYPOTHESIS-READY"
    elif shares["occurrence_spells"] >= diagnostic["occurrence_dominance_fraction"]:
        selected = "semi_markov_occurrence_ssm_v1"
        terminal = "A10M5R7-ARCHITECTURE-HYPOTHESIS-READY"
    elif shares["annual_dependence"] >= diagnostic["annual_dominance_fraction"]:
        selected = "two_timescale_stochastic_ssm_v1"
        terminal = "A10M5R7-ARCHITECTURE-HYPOTHESIS-READY"
    else:
        selected = "mixed_hold"
        terminal = "HOLD-A10-ARCHITECTURE-HYPOTHESIS-MIXED"
    return {
        "accepted_group_error_shares": shares,
        "feedback_advances": feedback_advances,
        "feedback_group_guards": guards,
        "feedback_improvement_fraction": improvement,
        "feedback_support": feedback_support,
        "observation_conditioned_improvement_fraction": conditioned_improvement,
        "protected_roles_opened": [],
        "schema_version": 1,
        "selected_architecture": selected,
        "terminal": terminal,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    run_root = options.run_root.resolve()
    output = options.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    contract = read_json(run_root / "diagnostic-contract.json")
    reconstruction = read_json(run_root / "reconstruction-contract.json")
    sites = read_json(run_root / "sites.json")["sites"]
    expected_by_seed = {model["training_seed"]: model for model in reconstruction["models"] if model["capacity_id"] == "P1"}
    members = contract["diagnostic"]["member_ids"]
    seed = contract["diagnostic"]["training_seed"]
    seed_output = output / f"seed-{seed}"
    module, identity = reconstruct(run_root, options.corpus, seed_output, expected_by_seed[seed]["row_id"], seed, expected_by_seed[seed])
    _, _, normalization = legacy.verify_corpus(options.corpus)
    mode_records: dict[str, list[dict[str, Any]]] = {mode: [] for mode in contract["diagnostic"]["modes"]}
    references: dict[str, dict[str, dict[str, float]]] = {mode: {} for mode in contract["diagnostic"]["modes"]}
    feedback_support = True
    for site in sites:
        document = observation_document(options.corpus, site)
        observed_dates, observed_arrays, conditioning = observed_surface(document)
        observed_metrics = realized_metrics(observed_dates, *observed_arrays)
        means, scales = legacy.normalizers(normalization, site["regime"])
        dates, values = open_loop(module, site, members, contract["diagnostic"]["horizon_years"], 101)
        mode_records["accepted_open_loop"].extend(summarize("accepted_open_loop", site, seed, members, dates, values))
        references["accepted_open_loop"][site["point_id"]] = observed_metrics
        conditioned = observation_conditioned(module, site, members, observed_dates, conditioning, means, scales, 101)
        mode_records["observation_conditioned"].extend(summarize("observation_conditioned", site, seed, members, observed_dates, conditioned))
        references["observation_conditioned"][site["point_id"]] = observed_metrics
        feedback_dates, feedback, valid = generated_feedback(
            module, site, members, contract["diagnostic"]["horizon_years"], means, scales, 101
        )
        feedback_support = feedback_support and valid
        if valid:
            mode_records["generated_feedback"].extend(summarize("generated_feedback", site, seed, members, feedback_dates, feedback))
            references["generated_feedback"][site["point_id"]] = observed_metrics
    if feedback_support:
        residual = attribution(mode_records, references, contract["diagnostic"]["groups"])
        decision = architecture_decision(residual, contract, True)
    else:
        residual = attribution(
            {
                "accepted_open_loop": mode_records["accepted_open_loop"],
                "observation_conditioned": mode_records["observation_conditioned"],
            },
            {
                "accepted_open_loop": references["accepted_open_loop"],
                "observation_conditioned": references["observation_conditioned"],
            },
            contract["diagnostic"]["groups"],
        )
        decision = {
            "feedback_advances": False,
            "feedback_support": False,
            "protected_roles_opened": [],
            "schema_version": 1,
            "selected_architecture": "generated_feedback_support_hold",
            "terminal": "HOLD-A10-GENERATED-FEEDBACK-SUPPORT",
        }
    residual.update({"checkpoint_reconstruction": identity, "protected_roles_opened": [], "schema_version": 1})
    atomic_json(output / "probe-streams.json", {"modes": mode_records, "schema_version": 1})
    atomic_json(output / "residual-attribution.json", residual)
    atomic_json(output / "architecture-decision.json", decision)

    candidate_records: list[dict[str, Any]] = []
    candidate_identities = []
    if decision["feedback_advances"]:
        full_members = list(range(contract["full_temporal"]["members_per_seed"]))
        for full_seed in contract["full_temporal"]["training_seeds"]:
            if full_seed == seed:
                full_module, full_identity = module, identity
            else:
                full_output = output / f"seed-{full_seed}"
                expected = expected_by_seed[full_seed]
                full_module, full_identity = reconstruct(
                    run_root, options.corpus, full_output, expected["row_id"], full_seed, expected
                )
            candidate_identities.append({"training_seed": full_seed, "identity": full_identity})
            for site in sites:
                means, scales = legacy.normalizers(normalization, site["regime"])
                dates, values, valid = generated_feedback(
                    full_module,
                    site,
                    full_members,
                    contract["full_temporal"]["horizon_years"],
                    means,
                    scales,
                    101,
                )
                if not valid:
                    raise RuntimeError("full generated-feedback support failure")
                candidate_records.extend(
                    summarize(contract["candidate_identity"], site, full_seed, full_members, dates, values)
                )
    candidate = {
        "candidate_identity": contract["candidate_identity"],
        "checkpoint_reconstructions": candidate_identities,
        "protected_roles_opened": [],
        "schema_version": 1,
        "streams": candidate_records,
        "temporal_candidate_available": bool(candidate_records),
    }
    atomic_json(output / "candidate-streams.json", candidate)
    scientific_gates = {
        "accepted_seed_reconstructed": True,
        "diagnostic_modes_complete": all(mode_records[mode] for mode in ("accepted_open_loop", "observation_conditioned")),
        "generated_feedback_support": feedback_support,
        "protected_roles_sealed": True,
    }
    operational_gates = {
        "architecture_decision_published": True,
        "candidate_surface_honest": bool(candidate_records) == bool(decision["feedback_advances"]),
        "reconstruction_identity_verified": True,
    }
    atomic_json(
        output / "evidence.json.part",
        {
            "classification": "a10m5r7-development-only-structural-architecture-identification",
            "gates": operational_gates,
            "protected_roles_opened": [],
            "scientific_gates": scientific_gates,
            "terminal": decision["terminal"],
        },
    )
    print(decision["terminal"])


if __name__ == "__main__":
    main()
