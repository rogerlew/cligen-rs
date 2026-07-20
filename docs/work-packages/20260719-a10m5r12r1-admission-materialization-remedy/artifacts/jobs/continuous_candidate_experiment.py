#!/usr/bin/env python3
"""Train one continuous latent process and publish realized temporal streams."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import math
import os
import statistics
from pathlib import Path
from typing import Any

import torch
import numpy as np

import climate_core as climate
import continuous_core as continuous
import legacy_core as legacy
import portfolio_core as portfolio
import residual_core as residuals
from temporal_metrics import realized_metrics

RETAINED = {(candidate, continuous.CAPACITY) for candidate in continuous.CANDIDATES}


def date_axis(years: int) -> list[dt.date]:
    start = dt.date(2001, 1, 1)
    return [start + dt.timedelta(days=index) for index in range(legacy.days_for_years(years))]


def generation_tensors(
    years: int, latitude: float, longitude: float, elevation_m: float,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, list[dt.date]]:
    dates = date_axis(years)
    features = torch.from_numpy(
        legacy.generation_features(years, latitude, longitude, elevation_m)
    ).unsqueeze(0).to(device=device, dtype=torch.float32)
    months = torch.tensor(
        [[value.month - 1 for value in dates]], dtype=torch.long, device=device
    )
    year_indices = torch.tensor(
        [[value.year - 2001 for value in dates]], dtype=torch.long, device=device
    )
    return features, months, year_indices, dates


def generation_innovations(
    model: continuous.ContinuousLatentProcess, members: int, days: int, seed: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    output = {}
    for offset, (name, (_, latent)) in enumerate(sorted(model.innovation_shapes().items())):
        output[name] = residuals.member_innovations(
            members, 1, days, latent, seed + 1009 * (offset + 1), device
        )
    return output


def stream_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(values.astype("<f4", copy=False).tobytes()).hexdigest()


def generate_site_streams(
    model: continuous.ContinuousLatentProcess,
    control: torch.jit.ScriptModule,
    hidden_size: int,
    site: dict[str, Any],
    seed: int,
    generation: dict[str, Any],
    device: torch.device,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    years = int(generation["horizon_years"])
    members = len(generation["member_ids"])
    features, months, year_indices, dates = generation_tensors(
        years, float(site["latitude"]), float(site["longitude"]),
        float(site["elevation_m"]), device,
    )
    station = torch.tensor([1200], dtype=torch.long, device=device)
    with torch.inference_mode():
        base = portfolio.forward_control(control, features, station, hidden_size)
        innovations = generation_innovations(
            model, members, len(dates), seed + int(site["site_index"]) * 100_003, device
        )
        regimes = torch.zeros(1, dtype=torch.long, device=device)
        heads, _ = model.member_heads(
            base, features[..., 7:13], regimes, months, year_indices, innovations
        )
        uniforms = climate.member_uniforms(
            members, 1, len(dates), seed + int(site["site_index"]) * 100_003 + 900_000,
            device,
        )
        weather, _ = residuals.sample_member_weather(heads, uniforms, None)
        values = weather[:, 0].detach().cpu().numpy().astype("<f4")
    records = []
    for member_index, member_id in enumerate(generation["member_ids"]):
        member_values = values[member_index]
        support = bool(
            np.isfinite(member_values).all()
            and np.all(member_values[:, 0] >= 0.0)
            and np.all(member_values[:, 1] >= member_values[:, 2])
        )
        if not support:
            raise RuntimeError("generated temporal stream support failure")
        metrics = realized_metrics(
            dates, member_values[:, 0], member_values[:, 1], member_values[:, 2]
        )
        if not all(math.isfinite(value) for value in metrics.values()):
            raise RuntimeError("generated temporal metric is non-finite")
        records.append({
            "member_id": int(member_id),
            "metrics": metrics,
            "point_id": site["point_id"],
            "regime": site["regime"],
            "row_count": len(member_values),
            "stream_sha256": stream_sha256(member_values),
            "support": support,
            "training_seed": seed,
        })
    return records, values


def find_control(
    summary: dict[str, Any], capacity: str, seed: int
) -> dict[str, Any]:
    matches = [
        row for row in summary["models"]
        if row["capacity_id"] == capacity and int(row["training_seed"]) == seed
    ]
    if len(matches) != 1:
        raise RuntimeError(f"matched control identity is not unique: {capacity}/{seed}")
    return matches[0]


def median_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    block_names = sorted(rows[0]["candidate"]["block_scores"])
    result = {
        "block_scores": {
            name: statistics.median(row["candidate"]["block_scores"][name] for row in rows)
            for name in block_names
        },
        "daily_proper_nll": statistics.median(
            row["candidate"]["daily_proper_nll"] for row in rows
        ),
        "family_balanced_climate_score": statistics.median(
            row["candidate"]["family_balanced_climate_score"] for row in rows
        ),
    }
    if all("solar" in row["candidate"] for row in rows):
        solar_names = sorted(rows[0]["candidate"]["solar"]["block_scores"])
        result["solar"] = {
            "block_scores": {
                name: statistics.median(
                    row["candidate"]["solar"]["block_scores"][name] for row in rows
                )
                for name in solar_names
            },
            "family_score": statistics.median(
                row["candidate"]["solar"]["family_score"] for row in rows
            ),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--controls", type=Path, required=True)
    parser.add_argument("--candidate", choices=continuous.CANDIDATES, required=True)
    parser.add_argument("--capacity", choices=(continuous.CAPACITY,), required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    device = portfolio.require_l40()
    continuous.self_test(device)
    options.output.mkdir(parents=True, exist_ok=True)
    contract_path = options.run_root / "portfolio-contract.json"
    profile_path = options.run_root / "a10-daymet-calendar-profile-v1.json"
    contract = portfolio.read_json(contract_path)
    temporal_contract_path = options.run_root / "temporal-contract.json"
    temporal_contract = portfolio.read_json(temporal_contract_path)
    sites = portfolio.read_json(options.run_root / "sites.json")["sites"]
    for index, site in enumerate(sites):
        site["site_index"] = index
    profile = portfolio.read_json(profile_path)
    seeds = tuple(int(value) for value in contract["controls"]["seeds"])
    if seeds != portfolio.SEEDS:
        raise RuntimeError("frozen seed roster mismatch")
    architecture = contract["architectures"][options.candidate]
    if (options.candidate, options.capacity) not in RETAINED:
        raise RuntimeError("configuration is not in the continuous temporal matrix")
    role_matches = [
        row for row in temporal_contract["roles"]
        if row["architecture"] == options.candidate and row["capacity"] == options.capacity
    ]
    if len(role_matches) != 1 or tuple(role_matches[0]["seeds"]) != portfolio.SEEDS:
        raise RuntimeError("candidate role contract mismatch")
    role_id = role_matches[0]["role_id"]
    if options.output.name != role_id:
        raise RuntimeError(f"output directory must equal frozen role id: {role_id}")

    control_summary_path = options.controls / "control-summary.json"
    control_identity_path = options.controls / "control-identity.json"
    control_calendar_path = options.controls / "calendar-preflight.json"
    control_summary = portfolio.read_json(control_summary_path)
    control_identity = portfolio.read_json(control_identity_path)
    calendar_record = portfolio.read_json(control_calendar_path)
    if not control_identity["all_exact"] or not calendar_record["valid"]:
        raise RuntimeError("control predecessor did not pass")
    if control_summary["contract_sha256"] != portfolio.digest(contract_path):
        raise RuntimeError("control predecessor contract identity mismatch")

    transfer, normalized, normalization = legacy.verify_corpus(options.corpus)
    preflight = portfolio.calendar_preflight(options.corpus, normalized, profile)
    if preflight != calendar_record:
        raise RuntimeError("candidate calendar preflight differs from control predecessor")
    portfolio.atomic_json(options.output / "calendar-preflight.json", preflight)
    fit, validation, role_counts = legacy.load_daymet(
        options.corpus, normalized, normalization
    )
    fit_calendar, validation_calendar = climate.attach_calendars(
        options.corpus,
        normalized,
        fit,
        validation,
        int(contract["stochastic"]["window_calendar_years"]),
    )
    if len(fit_calendar) != 1200 or len(validation_calendar) != 240:
        raise RuntimeError("candidate calendar surface incomplete")
    selections = [(index, 0) for index in range(len(validation_calendar))]
    backbone = portfolio.backbone_capacity(contract, options.capacity)
    hidden_size = int(contract["controls"]["capacities"][options.capacity]["hidden_size"])
    parameter_ceiling = int(
        contract["controls"]["capacities"][options.capacity]["candidate_parameter_ceiling"]
    )
    seed_rows, training_rows, identity_rows, stream_rows, stream_values = [], [], [], [], []
    for seed in seeds:
        control_row = find_control(control_summary, backbone, seed)
        model_root = options.controls / control_row["model_directory"]
        export_path = model_root / "model-export.pt"
        if portfolio.digest(export_path) != control_row["export_sha256"]:
            raise RuntimeError("shared control export identity changed")
        control = torch.jit.load(str(export_path), map_location=device).eval()
        export_before = portfolio.digest(export_path)
        seed_work = options.output / "seed-work" / str(seed)
        model, training = continuous.train_candidate(
            contract,
            options.candidate,
            seed,
            control,
            hidden_size,
            fit_calendar,
            validation_calendar,
            device,
            seed_work,
        )
        candidate_parameters = int(training["parameter_count"])
        total_parameters = candidate_parameters + int(control_row["parameter_count"])
        if total_parameters > parameter_ceiling:
            raise RuntimeError(
                f"candidate parameter ceiling exceeded: {total_parameters}>{parameter_ceiling}"
            )
        candidate_score = continuous.score_candidate(
            model,
            control,
            hidden_size,
            validation_calendar,
            selections,
            int(contract["stochastic"]["evaluation_members"]),
            device,
            910000,
            920000,
            True,
        )
        if candidate_score["point_count"] != int(
            contract["checkpoint"]["final_fit_validation_points"]
        ):
            raise RuntimeError("all-240 final score incomplete")
        if not candidate_score["support"]:
            raise RuntimeError("candidate final score failed physical support")
        if portfolio.digest(export_path) != export_before:
            raise RuntimeError("frozen control export changed during candidate training")
        for site in sites:
            site_rows, site_values = generate_site_streams(
                model, control, hidden_size, site, seed,
                temporal_contract["generation"], device,
            )
            stream_rows.extend(site_rows)
            stream_values.append(site_values)
        seed_record = {
            "architecture": options.candidate,
            "backbone_capacity": backbone,
            "calendar_preflight_sha256": portfolio.digest(
                options.output / "calendar-preflight.json"
            ),
            "candidate": candidate_score,
            "candidate_parameter_count": candidate_parameters,
            "capacity": options.capacity,
            "configuration_id": f"{options.candidate}-{options.capacity.lower()}",
            "contract_sha256": portfolio.digest(contract_path),
            "control": control_row["score"],
            "control_export_sha256": export_before,
            "control_summary_sha256": portfolio.digest(control_summary_path),
            "fit_validation_gradient": False,
            "protected_roles_opened": [],
            "schema_version": 1,
            "role_id": role_id,
            "seed": seed,
            "solar_control": None,
            "total_parameter_count": total_parameters,
            "training": {
                "best_epoch": training["best_epoch"],
                "checkpoint_bytes": training["checkpoint_bytes"],
                "checkpoint_sha256": training["checkpoint_sha256"],
                "epochs_completed": training["epochs_completed"],
                "model_state_sha256": training["model_state_sha256"],
                "wall_seconds": training["wall_seconds"],
            },
        }
        if not all(
            math.isfinite(float(value))
            for value in (
                candidate_score["family_balanced_climate_score"],
                candidate_score["daily_proper_nll"],
                *candidate_score["block_scores"].values(),
            )
        ):
            raise RuntimeError("non-finite final candidate score")
        portfolio.atomic_json(options.output / "seeds" / f"{seed}.json", seed_record)
        seed_rows.append(seed_record)
        training_rows.append({"seed": seed, **training})
        identity_rows.append({
            "backbone_capacity": backbone,
            "control_checkpoint_sha256": control_row["checkpoint_sha256"],
            "control_export_sha256": export_before,
            "row_id": control_row["row_id"],
            "seed": seed,
        })
        del model, control
        torch.cuda.empty_cache()

    total_counts = {row["total_parameter_count"] for row in seed_rows}
    if len(total_counts) != 1:
        raise RuntimeError("parameter count changed across seeds")
    summary = {
        "architecture": options.candidate,
        "backbone_capacity": backbone,
        "calendar_preflight_sha256": portfolio.digest(options.output / "calendar-preflight.json"),
        "capacity": options.capacity,
        "configuration_id": f"{options.candidate}-{options.capacity.lower()}",
        "contract_sha256": portfolio.digest(contract_path),
        "corpus": {
            "aggregate_bytes": transfer["aggregate_bytes"],
            "normalization_role": normalization["fit_role_only"],
            "object_count": len(transfer["objects"]),
            "role_counts": role_counts,
        },
        "median_candidate_metrics": median_metrics(seed_rows),
        "protected_roles_opened": [],
        "role_id": role_id,
        "schema_version": 1,
        "seed_files": [f"seeds/{seed}.json" for seed in seeds],
        "seeds": list(seeds),
        "total_parameter_count": next(iter(total_counts)),
        "training_wall_seconds": sum(row["training"]["wall_seconds"] for row in seed_rows),
    }
    portfolio.atomic_json(options.output / "candidate-summary.json", summary)
    portfolio.atomic_json(options.output / "training.json", {
        "architecture": options.candidate,
        "capacity": options.capacity,
        "schema_version": 1,
        "seeds": training_rows,
    })
    portfolio.atomic_json(options.output / "control-identity.json", {
        "control_identity_sha256": portfolio.digest(control_identity_path),
        "control_summary_sha256": portfolio.digest(control_summary_path),
        "controls": identity_rows,
        "exact": True,
        "schema_version": 1,
    })
    expected_streams = int(
        temporal_contract["generation"]["expected_streams_per_configuration"]
    )
    if len(stream_rows) != expected_streams:
        raise RuntimeError(f"temporal stream matrix incomplete: {len(stream_rows)}")
    weather = np.concatenate(stream_values, axis=0)
    if weather.shape != (expected_streams, len(date_axis(int(temporal_contract["generation"]["horizon_years"]))), 3):
        raise RuntimeError("retained temporal stream archive shape mismatch")
    archive_path = options.output / "streams.npz"
    archive_partial = options.output / "streams.npz.part"
    with archive_partial.open("wb") as stream:
        np.savez_compressed(
            stream,
            member_id=np.asarray([row["member_id"] for row in stream_rows], dtype=np.int16),
            site_index=np.asarray(
                [next(index for index, site in enumerate(sites) if site["point_id"] == row["point_id"]) for row in stream_rows],
                dtype=np.int16,
            ),
            training_seed=np.asarray([row["training_seed"] for row in stream_rows], dtype=np.int64),
            weather=weather,
        )
    os.replace(archive_partial, archive_path)
    archive_identity = {
        "bytes": archive_path.stat().st_size,
        "sha256": portfolio.digest(archive_path),
    }
    portfolio.atomic_json(options.output / "streams.json", {
        "architecture": options.candidate,
        "capacity": options.capacity,
        "configuration_id": f"{options.candidate}-{options.capacity.lower()}",
        "protected_roles_opened": [],
        "role_id": role_id,
        "schema_version": 1,
        "stream_count": len(stream_rows),
        "stream_archive": archive_identity,
        "streams": stream_rows,
        "temporal_contract_sha256": portfolio.digest(temporal_contract_path),
    })
    evidence = {
        "classification": f"a10m5r12-development-only-{role_id}",
        "gates": {
            "all_seed_results_published": len(seed_rows) == 3,
            "calendar_preflight": preflight["valid"],
            "calendar_surface_complete": len(fit_calendar) == 1200 and len(validation_calendar) == 240,
            "candidate_parameter_ceiling": next(iter(total_counts)) <= parameter_ceiling,
            "common_evaluation_field": True,
            "controls_reconstructed_exactly": control_identity["all_exact"],
            "fit_validation_gradient_free": True,
            "physical_support": all(row["candidate"]["support"] for row in seed_rows),
            "temporal_stream_matrix_complete": len(stream_rows) == expected_streams,
            "temporal_stream_archive_published": archive_path.stat().st_size > 0,
            "temporal_stream_support": all(row["support"] for row in stream_rows),
            "protected_roles_sealed": True,
        },
        "protected_roles_opened": [],
        "role_id": role_id,
        "schema_version": 1,
    }
    portfolio.atomic_json(options.output / "evidence.json.part", evidence)
    print(f"A10M5R12-CONTINUOUS-CANDIDATE-COMPLETE {role_id}")


if __name__ == "__main__":
    main()
