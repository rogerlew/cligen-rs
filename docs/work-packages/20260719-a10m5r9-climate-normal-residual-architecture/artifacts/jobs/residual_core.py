#!/usr/bin/env python3
"""A10M5R9 climate-normal baseline and monthly stochastic residual core."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import climate_core as climate
import legacy_core as legacy

REGIMES = legacy.REGIMES
CORE_HEAD_INDICES = (0, 1, 3, 5)
DISPERSION_BLOCKS = ("monthly_interannual_dispersion", "annual_interannual_dispersion")


class ClimateNormalBaseline(nn.Module):
    """Transferable regime/month distribution baseline with a shared site correction."""

    def __init__(self, width: int, depth: int) -> None:
        super().__init__()
        self.table = nn.Parameter(torch.zeros((len(REGIMES), 12, 15)))
        layers: list[nn.Module] = []
        size = 3
        for _ in range(depth):
            layers.extend((nn.Linear(size, width), nn.ReLU()))
            size = width
        layers.append(nn.Linear(size, 15))
        self.site_correction = nn.Sequential(*layers)
        nn.init.zeros_(self.site_correction[-1].weight)
        nn.init.zeros_(self.site_correction[-1].bias)

    def forward(
        self,
        features: torch.Tensor,
        regime_indices: torch.Tensor,
        month_indices: torch.Tensor,
    ) -> torch.Tensor:
        site = features[:, 0, 10:13].float()
        correction = self.site_correction(site).unsqueeze(1)
        regime = regime_indices.unsqueeze(1).expand_as(month_indices)
        return self.table[regime, month_indices] + correction


class MonthlyResidual(nn.Module):
    """Small persistent stochastic state decoded into core location heads only."""

    def __init__(self, latent_dim: int, maximum_persistence: float) -> None:
        super().__init__()
        initial = torch.tensor((0.20, 0.40, 0.60, 0.80, 0.92, 0.98))
        if latent_dim != len(initial):
            raise RuntimeError("frozen latent initialization requires dimension six")
        ratio = (initial / maximum_persistence).clamp(1e-5, 1.0 - 1e-5)
        self.raw_persistence = nn.Parameter(torch.logit(ratio))
        self.decoder = nn.Linear(latent_dim, len(CORE_HEAD_INDICES), bias=False)
        nn.init.normal_(self.decoder.weight, mean=0.0, std=0.02)
        projection = torch.zeros((len(CORE_HEAD_INDICES), 15))
        for row, column in enumerate(CORE_HEAD_INDICES):
            projection[row, column] = 1.0
        self.register_buffer("projection", projection)
        self.maximum_persistence = maximum_persistence

    def persistence(self) -> torch.Tensor:
        return self.maximum_persistence * torch.sigmoid(self.raw_persistence)

    def states(self, innovations: torch.Tensor) -> torch.Tensor:
        persistence = self.persistence().view(1, 1, -1)
        innovation_scale = torch.sqrt((1.0 - persistence.square()).clamp_min(1e-6))
        state = torch.zeros_like(innovations[:, :, 0])
        values = []
        for index in range(innovations.shape[2]):
            state = persistence * state + innovation_scale * innovations[:, :, index]
            values.append(state)
        return torch.stack(values, dim=2)

    def member_heads(
        self,
        baseline_heads: torch.Tensor,
        month_indices: torch.Tensor,
        year_indices: torch.Tensor,
        innovations: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        states = self.states(innovations)
        cell_indices = year_indices * 12 + month_indices
        members, batch, _, latent = states.shape
        gather = cell_indices.unsqueeze(0).unsqueeze(-1).expand(members, batch, -1, latent)
        daily_states = states.gather(2, gather)
        decoded = self.decoder(daily_states)
        decoded = decoded - decoded.mean(dim=0, keepdim=True)
        adjustment = decoded @ self.projection
        return baseline_heads.float().unsqueeze(0) + adjustment, decoded


def model_state_sha256(model: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def regime_tensor(
    records: list[climate.CalendarRecord],
    selections: list[tuple[int, int]],
    device: torch.device,
) -> torch.Tensor:
    lookup = {name: index for index, name in enumerate(REGIMES)}
    return torch.tensor(
        [lookup[records[index].record.regime] for index, _ in selections],
        dtype=torch.long,
        device=device,
    )


def index_tensors(
    months: list[np.ndarray],
    years: list[np.ndarray],
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    return (
        torch.from_numpy(np.stack(months)).to(device=device, dtype=torch.long),
        torch.from_numpy(np.stack(years)).to(device=device, dtype=torch.long),
    )


def member_innovations(
    members: int,
    batch: int,
    cells: int,
    latent: int,
    seed: int,
    device: torch.device,
) -> torch.Tensor:
    if members < 2 or members % 2:
        raise RuntimeError("centered innovation field requires a positive even member count")
    generator = np.random.Generator(np.random.Philox(seed))
    half = generator.standard_normal((members // 2, batch, cells, latent), dtype=np.float32)
    values = np.concatenate((half, -half), axis=0)
    return torch.from_numpy(values).to(device)


def sample_member_weather(
    heads: torch.Tensor,
    uniforms: torch.Tensor,
    relaxed_temperature: float | None,
) -> tuple[torch.Tensor, torch.Tensor]:
    logit = heads[..., 0]
    if relaxed_temperature is None:
        wet = (uniforms[..., 0] < torch.sigmoid(logit)).float()
    else:
        logistic = torch.log(uniforms[..., 0]) - torch.log1p(-uniforms[..., 0])
        wet = torch.sigmoid((logit + logistic) / relaxed_temperature)
    amount_scale = nn.functional.softplus(heads[..., 2]) + 1e-4
    amount_normal = math.sqrt(2.0) * torch.erfinv(2.0 * uniforms[..., 1] - 1.0)
    amount = torch.exp(heads[..., 1] + amount_scale * amount_normal)
    locations = heads[..., 3::2]
    scales = nn.functional.softplus(heads[..., 4::2]) + 1e-4
    offsets = torch.arange(6, device=heads.device, dtype=torch.float32) / 7.0
    normals = torch.sqrt(-2.0 * torch.log(uniforms[..., 1:2])) * torch.cos(
        2.0 * math.pi * (uniforms[..., 2:3] + offsets)
    )
    continuous = locations + scales * normals
    tmean = continuous[..., 0]
    dtr = torch.exp(continuous[..., 1])
    weather = torch.stack((wet * amount, tmean + dtr / 2.0, tmean - dtr / 2.0), dim=-1)
    return weather, wet


def member_daily_nll(
    heads: torch.Tensor,
    precipitation: torch.Tensor,
    targets: torch.Tensor,
    valid: list[np.ndarray],
) -> torch.Tensor:
    return torch.stack(
        [climate.core_daily_nll(member, precipitation, targets, valid) for member in heads]
    ).mean()


def _batch(
    records: list[climate.CalendarRecord],
    selections: list[tuple[int, int]],
    device: torch.device,
) -> tuple[Any, ...]:
    values = climate.climate_batch(records, selections, device, len(records))
    features, precipitation, targets, weather, station, months, years, valid = values
    del station
    month_tensor, year_tensor = index_tensors(months, years, device)
    regimes = regime_tensor(records, selections, device)
    return (
        features,
        precipitation,
        targets,
        weather,
        regimes,
        month_tensor,
        year_tensor,
        months,
        years,
        valid,
    )


def _accumulate_score(
    totals: dict[str, float],
    blocks: dict[str, torch.Tensor],
    weight: int,
) -> None:
    for name, value in blocks.items():
        totals[name] = totals.get(name, 0.0) + float(value.detach().cpu()) * weight


def score_baseline(
    baseline: ClimateNormalBaseline,
    records: list[climate.CalendarRecord],
    selections: list[tuple[int, int]],
    members: int,
    device: torch.device,
    seed_base: int,
) -> dict[str, Any]:
    totals: dict[str, float] = {}
    daily_total = 0.0
    count = 0
    support = True
    baseline.eval()
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            features, precipitation, targets, weather, regimes, month_t, _, months, years, valid = _batch(
                records, subset, device
            )
            heads = baseline(features, regimes, month_t)
            uniforms = climate.member_uniforms(members, len(subset), heads.shape[1], seed_base + offset, device)
            generated, wet, _ = climate.sample_weather(heads, uniforms, None)
            _, blocks = climate.climate_components(generated, wet, weather, months, years, valid, squared=False)
            daily = climate.core_daily_nll(heads, precipitation, targets, valid)
            weight = len(subset)
            count += weight
            daily_total += float(daily.cpu()) * weight
            _accumulate_score(totals, blocks, weight)
            support = support and bool(
                torch.isfinite(generated).all()
                and (generated[..., 0] >= 0.0).all()
                and (generated[..., 1] >= generated[..., 2]).all()
            )
    block_scores = {name: value / count for name, value in sorted(totals.items())}
    return {
        "block_scores": block_scores,
        "daily_proper_nll": daily_total / count,
        "family_balanced_climate_score": statistics.fmean(block_scores.values()),
        "point_count": count,
        "stochastic_members": members,
        "support": support,
    }


def score_residual(
    baseline: ClimateNormalBaseline,
    residual: MonthlyResidual,
    records: list[climate.CalendarRecord],
    selections: list[tuple[int, int]],
    members: int,
    device: torch.device,
    output_seed_base: int,
    innovation_seed_base: int,
) -> dict[str, Any]:
    totals: dict[str, float] = {}
    daily_total = 0.0
    count = 0
    support = True
    baseline.eval()
    residual.eval()
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            features, precipitation, targets, weather, regimes, month_t, year_t, months, years, valid = _batch(
                records, subset, device
            )
            base_heads = baseline(features, regimes, month_t)
            innovations = member_innovations(
                members, len(subset), 96, residual.raw_persistence.numel(),
                innovation_seed_base + offset, device,
            )
            heads, _ = residual.member_heads(base_heads, month_t, year_t, innovations)
            uniforms = climate.member_uniforms(members, len(subset), heads.shape[2], output_seed_base + offset, device)
            generated, wet = sample_member_weather(heads, uniforms, None)
            _, blocks = climate.climate_components(generated, wet, weather, months, years, valid, squared=False)
            daily = member_daily_nll(heads, precipitation, targets, valid)
            weight = len(subset)
            count += weight
            daily_total += float(daily.cpu()) * weight
            _accumulate_score(totals, blocks, weight)
            support = support and bool(
                torch.isfinite(generated).all()
                and (generated[..., 0] >= 0.0).all()
                and (generated[..., 1] >= generated[..., 2]).all()
            )
    block_scores = {name: value / count for name, value in sorted(totals.items())}
    return {
        "block_scores": block_scores,
        "daily_proper_nll": daily_total / count,
        "family_balanced_climate_score": statistics.fmean(block_scores.values()),
        "point_count": count,
        "stochastic_members": members,
        "support": support,
    }


def _sampler(records: list[climate.CalendarRecord], seed: int) -> tuple[np.random.Generator, dict[str, list[int]]]:
    by_regime = {
        regime: [index for index, item in enumerate(records) if item.record.regime == regime]
        for regime in REGIMES
    }
    if any(len(rows) != 200 for rows in by_regime.values()):
        raise RuntimeError("candidate-fit regime roster mismatch")
    return np.random.Generator(np.random.Philox(seed)), by_regime


def _draw(
    generator: np.random.Generator,
    by_regime: dict[str, list[int]],
    fit: list[climate.CalendarRecord],
    regime: str,
    count: int,
) -> list[tuple[int, int]]:
    selections = []
    for _ in range(count):
        record_index = int(generator.choice(by_regime[regime]))
        window_index = int(generator.integers(len(fit[record_index].windows)))
        selections.append((record_index, window_index))
    return selections


def baseline_checkpoint_value(score: dict[str, Any], contract: dict[str, Any]) -> float:
    blocks = score["block_scores"]
    objective = contract["objective"]
    return (
        objective["baseline_daily_proper_nll_weight"] * score["daily_proper_nll"]
        + objective["baseline_location_weight"]
        * statistics.fmean((blocks["monthly_location"], blocks["annual_location"]))
        + objective["baseline_wet_weight"] * blocks["wet_occurrence_and_amount"]
    )


def train_baseline(
    contract: dict[str, Any],
    fit: list[climate.CalendarRecord],
    validation: list[climate.CalendarRecord],
    device: torch.device,
    output: Path,
) -> tuple[ClimateNormalBaseline, dict[str, Any]]:
    definition = contract["architecture"]["baseline"]
    training = contract["training"]
    checkpoint = contract["checkpoint"]
    stochastic = contract["stochastic"]
    seed = contract["architecture"]["training_seed"]
    legacy.configure(seed)
    model = ClimateNormalBaseline(definition["width"], definition["depth"]).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=training["baseline_learning_rate"], weight_decay=training["weight_decay"]
    )
    generator, by_regime = _sampler(fit, seed)
    subset = climate.checkpoint_subset(validation, REGIMES, checkpoint["points_per_regime"])
    best_value, best_epoch, best_payload, patience = math.inf, -1, None, 0
    trace = []
    started = time.monotonic()
    for epoch in range(checkpoint["baseline_maximum_epochs"]):
        model.train()
        train_rows = []
        for batch_index in range(training["batches_per_epoch"]):
            regime = REGIMES[batch_index % len(REGIMES)]
            selections = _draw(generator, by_regime, fit, regime, training["records_per_batch"])
            features, precipitation, targets, weather, regimes, month_t, _, months, years, valid = _batch(
                fit, selections, device
            )
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                heads = model(features, regimes, month_t)
            uniforms = climate.member_uniforms(
                stochastic["training_members"], len(selections), heads.shape[1],
                seed + epoch * 1009 + batch_index, device,
            )
            generated, wet, _ = climate.sample_weather(
                heads, uniforms, stochastic["relaxed_wet_temperature"]
            )
            _, blocks = climate.climate_components(generated, wet, weather, months, years, valid, squared=True)
            daily = climate.core_daily_nll(heads, precipitation, targets, valid)
            objective = (
                contract["objective"]["baseline_daily_proper_nll_weight"] * daily
                + contract["objective"]["baseline_location_weight"]
                * (blocks["monthly_location"] + blocks["annual_location"]) / 2.0
                + contract["objective"]["baseline_wet_weight"] * blocks["wet_occurrence_and_amount"]
            )
            objective.backward()
            if not math.isfinite(float(objective)) or not all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
                for parameter in model.parameters()
            ):
                raise RuntimeError("non-finite baseline training state")
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_rows.append((float(objective.detach().cpu()), float(daily.detach().cpu())))
        validation_score = score_baseline(
            model, validation, subset, stochastic["evaluation_members"], device, 610000 + epoch * 100
        )
        value = baseline_checkpoint_value(validation_score, contract)
        improved = value < best_value - checkpoint["tie_tolerance"]
        if improved:
            best_value, best_epoch, patience = value, epoch + 1, 0
            best_payload = copy.deepcopy(model.state_dict())
        else:
            patience += 1
        trace.append({
            "checkpoint_value": value,
            "epoch": epoch + 1,
            "improved": improved,
            "train_daily_proper_nll": statistics.fmean(row[1] for row in train_rows),
            "train_objective": statistics.fmean(row[0] for row in train_rows),
            "validation": validation_score,
        })
        if epoch + 1 >= checkpoint["baseline_minimum_epochs"] and patience >= checkpoint["early_stop_patience"]:
            break
    if best_payload is None:
        raise RuntimeError("no baseline checkpoint")
    model.load_state_dict(best_payload)
    model.eval()
    checkpoint_path = output / "baseline-checkpoint.pt"
    torch.save({"epoch": best_epoch, "model": best_payload, "training_seed": seed}, checkpoint_path)
    result = {
        "best_epoch": best_epoch,
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": climate.digest(checkpoint_path),
        "epochs_completed": len(trace),
        "fit_points": len(fit),
        "fit_validation_gradient": False,
        "model_state_sha256": model_state_sha256(model),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "trace": trace,
        "wall_seconds": time.monotonic() - started,
    }
    climate.atomic_json(output / "baseline-training.json", result)
    return model, result


def residual_checkpoint_value(
    score: dict[str, Any],
    baseline_score: dict[str, Any],
    contract: dict[str, Any],
) -> float:
    threshold = contract["decision"]["maximum_block_degradation_fraction"]
    nll_threshold = contract["decision"]["maximum_daily_nll_degradation_fraction"]
    penalty = max(0.0, score["daily_proper_nll"] / baseline_score["daily_proper_nll"] - (1.0 + nll_threshold))
    for name, value in score["block_scores"].items():
        penalty += max(0.0, value / baseline_score["block_scores"][name] - (1.0 + threshold))
    return score["family_balanced_climate_score"] + 10.0 * penalty


def train_residual(
    contract: dict[str, Any],
    baseline: ClimateNormalBaseline,
    fit: list[climate.CalendarRecord],
    validation: list[climate.CalendarRecord],
    device: torch.device,
    output: Path,
) -> tuple[MonthlyResidual, dict[str, Any]]:
    definition = contract["architecture"]["residual"]
    training = contract["training"]
    checkpoint = contract["checkpoint"]
    stochastic = contract["stochastic"]
    seed = contract["architecture"]["training_seed"]
    baseline.eval()
    for parameter in baseline.parameters():
        parameter.requires_grad_(False)
    baseline_before = model_state_sha256(baseline)
    model = MonthlyResidual(definition["latent_dim"], definition["maximum_persistence"]).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=training["residual_learning_rate"], weight_decay=training["weight_decay"]
    )
    generator, by_regime = _sampler(fit, seed + 1)
    subset = climate.checkpoint_subset(validation, REGIMES, checkpoint["points_per_regime"])
    baseline_subset = score_baseline(
        baseline, validation, subset, stochastic["evaluation_members"], device, 710000
    )
    best_value, best_epoch, best_payload, patience = math.inf, -1, None, 0
    trace = []
    started = time.monotonic()
    for epoch in range(checkpoint["residual_maximum_epochs"]):
        model.train()
        train_rows = []
        for batch_index in range(training["batches_per_epoch"]):
            regime = REGIMES[batch_index % len(REGIMES)]
            selections = _draw(generator, by_regime, fit, regime, training["records_per_batch"])
            features, precipitation, targets, weather, regimes, month_t, year_t, months, years, valid = _batch(
                fit, selections, device
            )
            with torch.no_grad():
                base_heads = baseline(features, regimes, month_t)
            innovations = member_innovations(
                stochastic["training_members"], len(selections), 96, definition["latent_dim"],
                seed + 200000 + epoch * 1009 + batch_index, device,
            )
            optimizer.zero_grad(set_to_none=True)
            member_heads, offsets = model.member_heads(base_heads, month_t, year_t, innovations)
            uniforms = climate.member_uniforms(
                stochastic["training_members"], len(selections), base_heads.shape[1],
                seed + 300000 + epoch * 1009 + batch_index, device,
            )
            generated, wet = sample_member_weather(
                member_heads, uniforms, stochastic["relaxed_wet_temperature"]
            )
            climate_loss, _ = climate.climate_components(
                generated, wet, weather, months, years, valid, squared=True
            )
            daily = member_daily_nll(member_heads, precipitation, targets, valid)
            size = offsets.square().mean()
            objective = (
                contract["objective"]["residual_climate_weight"] * climate_loss
                + contract["objective"]["residual_daily_proper_nll_weight"] * daily
                + contract["objective"]["residual_size_weight"] * size
            )
            objective.backward()
            if not math.isfinite(float(objective)) or not all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
                for parameter in model.parameters()
            ):
                raise RuntimeError("non-finite residual training state")
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_rows.append((float(objective.detach().cpu()), float(climate_loss.detach().cpu()), float(daily.detach().cpu())))
        validation_score = score_residual(
            baseline, model, validation, subset, stochastic["evaluation_members"], device,
            710000 + epoch * 100, 810000 + epoch * 100,
        )
        value = residual_checkpoint_value(validation_score, baseline_subset, contract)
        improved = value < best_value - checkpoint["tie_tolerance"]
        if improved:
            best_value, best_epoch, patience = value, epoch + 1, 0
            best_payload = copy.deepcopy(model.state_dict())
        else:
            patience += 1
        trace.append({
            "checkpoint_value": value,
            "epoch": epoch + 1,
            "improved": improved,
            "train_climate_loss": statistics.fmean(row[1] for row in train_rows),
            "train_daily_proper_nll": statistics.fmean(row[2] for row in train_rows),
            "train_objective": statistics.fmean(row[0] for row in train_rows),
            "validation": validation_score,
        })
        if epoch + 1 >= checkpoint["residual_minimum_epochs"] and patience >= checkpoint["early_stop_patience"]:
            break
    if best_payload is None:
        raise RuntimeError("no residual checkpoint")
    model.load_state_dict(best_payload)
    model.eval()
    baseline_after = model_state_sha256(baseline)
    if baseline_after != baseline_before:
        raise RuntimeError("frozen baseline changed during residual training")
    checkpoint_path = output / "residual-checkpoint.pt"
    torch.save({"epoch": best_epoch, "model": best_payload, "training_seed": seed}, checkpoint_path)
    result = {
        "baseline_state_sha256_after": baseline_after,
        "baseline_state_sha256_before": baseline_before,
        "best_epoch": best_epoch,
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": climate.digest(checkpoint_path),
        "epochs_completed": len(trace),
        "fit_points": len(fit),
        "fit_validation_gradient": False,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "persistence": [float(value) for value in model.persistence().detach().cpu()],
        "trace": trace,
        "wall_seconds": time.monotonic() - started,
    }
    climate.atomic_json(output / "residual-training.json", result)
    return model, result


def decision(
    p1: dict[str, Any],
    baseline: dict[str, Any],
    residual: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    limits = contract["decision"]
    baseline_dispersion = statistics.fmean(baseline["block_scores"][name] for name in DISPERSION_BLOCKS)
    residual_dispersion = statistics.fmean(residual["block_scores"][name] for name in DISPERSION_BLOCKS)
    dispersion_improvement = 1.0 - residual_dispersion / baseline_dispersion
    climate_improvement = 1.0 - residual["family_balanced_climate_score"] / baseline["family_balanced_climate_score"]
    blocks = {
        name: residual["block_scores"][name]
        <= (1.0 + limits["maximum_block_degradation_fraction"]) * baseline["block_scores"][name]
        for name in baseline["block_scores"]
    }
    baseline_nll = residual["daily_proper_nll"] <= (
        1.0 + limits["maximum_daily_nll_degradation_fraction"]
    ) * baseline["daily_proper_nll"]
    p1_climate = residual["family_balanced_climate_score"] <= (
        1.0 + limits["p1_maximum_climate_score_degradation_fraction"]
    ) * p1["family_balanced_climate_score"]
    p1_nll = residual["daily_proper_nll"] <= (
        1.0 + limits["p1_maximum_daily_nll_degradation_fraction"]
    ) * p1["daily_proper_nll"]
    advances = bool(
        p1["support"] and baseline["support"] and residual["support"]
        and dispersion_improvement >= limits["minimum_dispersion_improvement_fraction"]
        and climate_improvement >= limits["minimum_climate_score_improvement_fraction"]
        and all(blocks.values()) and baseline_nll and p1_climate and p1_nll
    )
    return {
        "advances": advances,
        "baseline_block_non_degradation": blocks,
        "baseline_daily_proper_nll_guard": baseline_nll,
        "climate_score_improvement_fraction": climate_improvement,
        "dispersion_improvement_fraction": dispersion_improvement,
        "p1_climate_score_guard": p1_climate,
        "p1_daily_proper_nll_guard": p1_nll,
        "selected_arm": "climate_normal_plus_residual" if advances else "none",
        "terminal": "A10M5R9-CORE-ARCHITECTURE-READY" if advances else "HOLD-A10M5R9-RESIDUAL-ARCHITECTURE-NOT-SUPPORTED",
    }


def self_test() -> None:
    torch.manual_seed(190719)
    baseline = ClimateNormalBaseline(16, 1)
    residual = MonthlyResidual(6, 0.995)
    features = torch.zeros((2, 12, 13))
    features[:, :, 10:13] = torch.tensor((0.5, -0.6, 0.2))
    regimes = torch.tensor((0, 5))
    months = torch.tensor([list(range(12)), list(range(12))])
    years = torch.zeros_like(months)
    base = baseline(features, regimes, months)
    innovations = member_innovations(4, 2, 96, 6, 91, torch.device("cpu"))
    heads, offsets = residual.member_heads(base, months, years, innovations)
    repeated, repeated_offsets = residual.member_heads(
        base, months, years, member_innovations(4, 2, 96, 6, 91, torch.device("cpu"))
    )
    if heads.shape != (4, 2, 12, 15) or not torch.equal(heads, repeated):
        raise RuntimeError("residual deterministic shape self-test failed")
    if not torch.allclose(offsets.mean(0), torch.zeros_like(offsets.mean(0)), atol=1e-7):
        raise RuntimeError("member-centered residual self-test failed")
    if not torch.equal(offsets, repeated_offsets):
        raise RuntimeError("residual innovation replay failed")
    if any(index not in CORE_HEAD_INDICES and not torch.equal(heads[..., index], base[..., index].expand_as(heads[..., index])) for index in range(15)):
        raise RuntimeError("residual changed a prohibited head")

    dates = [dt.date(1979, 12, 31) + dt.timedelta(days=index) for index in range(2924)]
    valid = [not (date.month == 12 and date.day == 31 and date.year in (1980, 1984)) for date in dates]
    document = {
        "dates": [date.isoformat() for date in dates],
        "source_observed": valid,
        "fields": {field: [1.0 if keep else None for keep in valid] for field in ("prcp", "tmax", "tmin")},
    }
    windows = climate._document_windows(document, 8)
    window = next((value for value in windows if value.first_year == 1980), None)
    if window is None or window.days != 2922 or int(window.valid_index.sum()) != 2920:
        raise RuntimeError("Daymet calendar profile self-test failed")
    target_dates = dates[1:2923]
    february_29 = target_dates.index(dt.date(1980, 2, 29))
    december_31 = target_dates.index(dt.date(1980, 12, 31))
    if not window.valid_index[february_29] or window.valid_index[december_31]:
        raise RuntimeError("Daymet leap-year mask semantics failed")

    blocks = {
        "annual_interannual_dispersion": 1.0,
        "annual_location": 1.0,
        "monthly_interannual_dispersion": 1.0,
        "monthly_location": 1.0,
        "precipitation_temperature_dependence": 1.0,
        "wet_occurrence_and_amount": 1.0,
        "within_month_daily_dispersion": 1.0,
    }
    p1 = {"block_scores": blocks, "daily_proper_nll": 1.0, "family_balanced_climate_score": 1.0, "support": True}
    base_score = {"block_scores": blocks, "daily_proper_nll": 1.0, "family_balanced_climate_score": 1.0, "support": True}
    residual_blocks = {name: (0.8 if name in DISPERSION_BLOCKS else 0.95) for name in blocks}
    residual_score = {"block_scores": residual_blocks, "daily_proper_nll": 1.05, "family_balanced_climate_score": statistics.fmean(residual_blocks.values()), "support": True}
    local_contract = Path(__file__).resolve().parent / "architecture-contract.json"
    if not local_contract.is_file():
        local_contract = Path(__file__).resolve().parents[1] / "architecture-contract.json"
    contract = json.loads(local_contract.read_text(encoding="utf-8"))
    if not decision(p1, base_score, residual_score, contract)["advances"]:
        raise RuntimeError("passing decision self-test failed")
    print("A10M5R9-RESIDUAL-CORE-SELF-TEST-PASS")


if __name__ == "__main__":
    self_test()
