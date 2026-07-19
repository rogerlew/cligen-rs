#!/usr/bin/env python3
"""A10M5R8 calendar-climate objective and deterministic evaluation core."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import statistics
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import legacy_core as legacy
import screen_core_v2 as accepted


@dataclass(frozen=True)
class CalendarWindow:
    input_start: int
    days: int
    first_year: int
    month_index: np.ndarray
    year_index: np.ndarray


@dataclass
class CalendarRecord:
    record: Any
    windows: list[CalendarWindow]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    partial.replace(path)


def _document_windows(document: dict[str, Any], years: int) -> list[CalendarWindow]:
    dates = [dt.date.fromisoformat(text) for text in document["dates"]]
    positions = {date: index for index, date in enumerate(dates)}
    complete = np.asarray(document["source_observed"], dtype=bool)
    for field in legacy.FIELDS:
        complete &= np.asarray([value is not None for value in document["fields"][field]])
    windows = []
    for first_year in range(dates[0].year, dates[-1].year - years + 2):
        target_start = dt.date(first_year, 1, 1)
        target_end = dt.date(first_year + years, 1, 1)
        previous = target_start - dt.timedelta(days=1)
        if previous not in positions or target_end not in positions:
            continue
        input_start = positions[previous]
        end = positions[target_end]
        days = end - positions[target_start]
        if days <= 0 or end - input_start != days + 1:
            continue
        if not bool(complete[input_start : end + 1].all()):
            continue
        targets = dates[input_start + 1 : end + 1]
        month_index = np.asarray([date.month - 1 for date in targets], dtype=np.int64)
        year_index = np.asarray([date.year - first_year for date in targets], dtype=np.int64)
        if len(month_index) != days or set(year_index.tolist()) != set(range(years)):
            raise RuntimeError("calendar window construction mismatch")
        windows.append(CalendarWindow(input_start, days, first_year, month_index, year_index))
    return windows


def attach_calendars(
    corpus: Path,
    normalized: dict[str, Any],
    fit: list[Any],
    validation: list[Any],
    years: int,
) -> tuple[list[CalendarRecord], list[CalendarRecord]]:
    lookup: dict[tuple[str, str], Any] = {}
    for record in (*fit, *validation):
        key = (record.role, record.point_id)
        if key in lookup:
            raise RuntimeError("duplicate Daymet role/point identity")
        lookup[key] = record
    attached: dict[tuple[str, str], CalendarRecord] = {}
    for shard in normalized["daymet_shards"]:
        with tarfile.open(corpus / shard["path"], "r:gz") as archive:
            for member in archive.getmembers():
                stream = archive.extractfile(member)
                if stream is None:
                    continue
                document = json.load(stream)
                key = (document["role"], document["point_id"])
                if key not in lookup:
                    continue
                windows = _document_windows(document, years)
                if windows:
                    attached[key] = CalendarRecord(lookup[key], windows)
    fit_calendar = [attached[(record.role, record.point_id)] for record in fit if (record.role, record.point_id) in attached]
    validation_calendar = [attached[(record.role, record.point_id)] for record in validation if (record.role, record.point_id) in attached]
    if len(fit_calendar) != len(fit) or len(validation_calendar) != len(validation):
        raise RuntimeError(
            f"eight-year eligibility incomplete: fit={len(fit_calendar)}/{len(fit)} "
            f"validation={len(validation_calendar)}/{len(validation)}"
        )
    lengths = {window.days for item in (*fit_calendar, *validation_calendar) for window in item.windows}
    if lengths != {2922}:
        raise RuntimeError(f"unexpected eight-year day counts: {sorted(lengths)}")
    return fit_calendar, validation_calendar


def raw_temperature(targets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = targets[:, 0]
    range_value = np.exp(targets[:, 1])
    return mean + range_value / 2.0, mean - range_value / 2.0


def climate_batch(
    records: list[CalendarRecord],
    selections: list[tuple[int, int]],
    device: torch.device,
    validation_index: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, list[np.ndarray], list[np.ndarray]]:
    feature_rows, precipitation_rows, target_rows, weather_rows, stations = [], [], [], [], []
    months, years = [], []
    for record_index, window_index in selections:
        item = records[record_index]
        window = item.windows[window_index]
        record = item.record
        start = window.input_start
        stop = start + window.days
        features = record.features[start:stop].copy()
        features[:, :7] = 0.0
        precipitation = record.precipitation[start + 1 : stop + 1]
        transformed = record.targets[start + 1 : stop + 1]
        tmax, tmin = raw_temperature(transformed)
        feature_rows.append(features)
        precipitation_rows.append(precipitation)
        target_rows.append(transformed)
        weather_rows.append(np.column_stack((precipitation, tmax, tmin)).astype(np.float32))
        stations.append(record.fit_index if record.fit_index >= 0 else validation_index)
        months.append(window.month_index)
        years.append(window.year_index)
    return (
        torch.from_numpy(np.stack(feature_rows)).to(device),
        torch.from_numpy(np.stack(precipitation_rows)).to(device),
        torch.from_numpy(np.stack(target_rows)).to(device),
        torch.from_numpy(np.stack(weather_rows)).to(device),
        torch.tensor(stations, dtype=torch.long, device=device),
        months,
        years,
    )


def member_uniforms(
    members: int,
    batch: int,
    days: int,
    seed: int,
    device: torch.device,
) -> torch.Tensor:
    generator = np.random.Generator(np.random.Philox(seed))
    values = generator.random((members, batch, days, 3), dtype=np.float64)
    values = np.clip(values, 1e-7, 1.0 - 1e-7)
    return torch.from_numpy(values).to(device=device, dtype=torch.float32)


def sample_weather(
    heads: torch.Tensor,
    uniforms: torch.Tensor,
    relaxed_temperature: float | None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    expanded = heads.float().unsqueeze(0).expand(uniforms.shape[0], -1, -1, -1)
    logit = expanded[..., 0]
    if relaxed_temperature is None:
        wet = (uniforms[..., 0] < torch.sigmoid(logit)).float()
    else:
        logistic = torch.log(uniforms[..., 0]) - torch.log1p(-uniforms[..., 0])
        wet = torch.sigmoid((logit + logistic) / relaxed_temperature)
    scale = nn.functional.softplus(expanded[..., 2]) + 1e-4
    normal_amount = math.sqrt(2.0) * torch.erfinv(2.0 * uniforms[..., 1] - 1.0)
    amount = torch.exp(expanded[..., 1] + scale * normal_amount)
    locations = expanded[..., 3::2]
    scales = nn.functional.softplus(expanded[..., 4::2]) + 1e-4
    offsets = torch.arange(6, device=heads.device, dtype=torch.float32) / 7.0
    normals = torch.sqrt(-2.0 * torch.log(uniforms[..., 1:2])) * torch.cos(
        2.0 * math.pi * (uniforms[..., 2:3] + offsets)
    )
    continuous = locations + scales * normals
    tmean = continuous[..., 0]
    dtr = torch.exp(continuous[..., 1])
    weather = torch.stack((wet * amount, tmean + dtr / 2.0, tmean - dtr / 2.0), dim=-1)
    return weather, wet, amount


def _standard_deviation(values: torch.Tensor, dim: int) -> torch.Tensor:
    return values.std(dim=dim, correction=0)


def _correlation(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = torch.sqrt(left_centered.square().mean() * right_centered.square().mean()).clamp_min(1e-6)
    return (left_centered * right_centered).mean() / denominator


def _residual(predicted: torch.Tensor, observed: torch.Tensor, kind: str) -> torch.Tensor:
    if kind == "precipitation":
        return (torch.log1p(predicted.clamp_min(0.0)) - torch.log1p(observed.clamp_min(0.0))) / 0.25
    if kind == "temperature_location":
        return (predicted - observed) / 2.0
    if kind == "temperature_dispersion":
        return (predicted - observed) / 0.5
    if kind == "frequency":
        return (predicted - observed) / 0.05
    if kind == "dependence":
        return (predicted - observed) / 0.1
    raise RuntimeError(f"unknown residual kind: {kind}")


def climate_components(
    generated: torch.Tensor,
    generated_wet: torch.Tensor,
    observed: torch.Tensor,
    month_indices: list[np.ndarray],
    year_indices: list[np.ndarray],
    squared: bool,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    blocks: dict[str, list[torch.Tensor]] = {
        "monthly_location": [],
        "monthly_interannual_dispersion": [],
        "within_month_daily_dispersion": [],
        "annual_location": [],
        "annual_interannual_dispersion": [],
        "wet_occurrence_and_amount": [],
        "precipitation_temperature_dependence": [],
    }
    member_count, batch_count = generated.shape[:2]
    for batch_index in range(batch_count):
        months = torch.from_numpy(month_indices[batch_index]).to(generated.device)
        years = torch.from_numpy(year_indices[batch_index]).to(generated.device)
        year_count = int(years.max().item()) + 1
        generated_month_cells: list[list[torch.Tensor]] = [[], [], []]
        observed_month_cells: list[list[torch.Tensor]] = [[], [], []]
        generated_wet_cells, observed_wet_cells = [], []
        generated_amount_cells, observed_amount_cells = [], []
        generated_within: list[list[torch.Tensor]] = [[], [], []]
        observed_within: list[list[torch.Tensor]] = [[], [], []]
        for month in range(12):
            month_generated: list[list[torch.Tensor]] = [[], [], []]
            month_observed: list[list[torch.Tensor]] = [[], [], []]
            month_wet_generated, month_wet_observed = [], []
            month_amount_generated, month_amount_observed = [], []
            for year in range(year_count):
                mask = (months == month) & (years == year)
                if int(mask.sum()) < 28:
                    raise RuntimeError("incomplete calendar month")
                generated_slice = generated[:, batch_index, mask]
                observed_slice = observed[batch_index, mask]
                wet_slice = generated_wet[:, batch_index, mask]
                observed_wet = (observed_slice[:, 0] >= 1.0).float()
                for field in range(3):
                    generated_aggregate = generated_slice[..., field].sum(1) if field == 0 else generated_slice[..., field].mean(1)
                    observed_aggregate = observed_slice[:, field].sum() if field == 0 else observed_slice[:, field].mean()
                    month_generated[field].append(generated_aggregate)
                    month_observed[field].append(observed_aggregate)
                    generated_within[field].append(_standard_deviation(generated_slice[..., field], dim=1))
                    observed_within[field].append(_standard_deviation(observed_slice[:, field], dim=0))
                generated_frequency = wet_slice.mean(1)
                observed_frequency = observed_wet.mean()
                month_wet_generated.append(generated_frequency)
                month_wet_observed.append(observed_frequency)
                generated_amount = generated_slice[..., 0].sum(1) / wet_slice.sum(1).clamp_min(0.25)
                observed_amount = observed_slice[:, 0].sum() / observed_wet.sum().clamp_min(1.0)
                month_amount_generated.append(generated_amount)
                month_amount_observed.append(observed_amount)
            for field in range(3):
                generated_values = torch.stack(month_generated[field], dim=1)
                observed_values = torch.stack(month_observed[field])
                generated_month_cells[field].append(generated_values)
                observed_month_cells[field].append(observed_values)
                kind = "precipitation" if field == 0 else "temperature_location"
                blocks["monthly_location"].append(_residual(generated_values.mean(), observed_values.mean(), kind))
                dispersion_kind = "precipitation" if field == 0 else "temperature_dispersion"
                blocks["monthly_interannual_dispersion"].append(
                    _residual(_standard_deviation(generated_values.flatten(), 0), _standard_deviation(observed_values, 0), dispersion_kind)
                )
                generated_daily = torch.cat(generated_within[field][-year_count:]).mean()
                observed_daily = torch.stack(observed_within[field][-year_count:]).mean()
                blocks["within_month_daily_dispersion"].append(
                    _residual(generated_daily, observed_daily, dispersion_kind)
                )
            generated_frequency_values = torch.stack(month_wet_generated, dim=1)
            observed_frequency_values = torch.stack(month_wet_observed)
            blocks["wet_occurrence_and_amount"].extend(
                (
                    _residual(generated_frequency_values.mean(), observed_frequency_values.mean(), "frequency"),
                    _residual(
                        _standard_deviation(generated_frequency_values.flatten(), 0),
                        _standard_deviation(observed_frequency_values, 0),
                        "frequency",
                    ),
                    _residual(torch.stack(month_amount_generated).mean(), torch.stack(month_amount_observed).mean(), "precipitation"),
                )
            )
            generated_wet_cells.append(generated_frequency_values)
            observed_wet_cells.append(observed_frequency_values)
            generated_amount_cells.append(torch.stack(month_amount_generated, dim=1))
            observed_amount_cells.append(torch.stack(month_amount_observed))

        generated_annual: list[list[torch.Tensor]] = [[], [], []]
        observed_annual: list[list[torch.Tensor]] = [[], [], []]
        for year in range(year_count):
            mask = years == year
            for field in range(3):
                generated_values = generated[:, batch_index, mask, field]
                observed_values = observed[batch_index, mask, field]
                generated_annual[field].append(generated_values.sum(1) if field == 0 else generated_values.mean(1))
                observed_annual[field].append(observed_values.sum() if field == 0 else observed_values.mean())
        for field in range(3):
            generated_values = torch.stack(generated_annual[field], dim=1)
            observed_values = torch.stack(observed_annual[field])
            location_kind = "precipitation" if field == 0 else "temperature_location"
            dispersion_kind = "precipitation" if field == 0 else "temperature_dispersion"
            blocks["annual_location"].append(_residual(generated_values.mean(), observed_values.mean(), location_kind))
            blocks["annual_interannual_dispersion"].append(
                _residual(_standard_deviation(generated_values.flatten(), 0), _standard_deviation(observed_values, 0), dispersion_kind)
            )

        generated_precip = torch.cat([value.flatten() for value in generated_month_cells[0]])
        observed_precip = torch.cat(observed_month_cells[0])
        for field in (1, 2):
            generated_temperature = torch.cat([value.flatten() for value in generated_month_cells[field]])
            observed_temperature = torch.cat(observed_month_cells[field])
            blocks["precipitation_temperature_dependence"].append(
                _residual(_correlation(generated_precip, generated_temperature), _correlation(observed_precip, observed_temperature), "dependence")
            )
        generated_dtr = torch.cat([value.flatten() for value in generated_month_cells[1]]) - torch.cat(
            [value.flatten() for value in generated_month_cells[2]]
        )
        observed_dtr = torch.cat(observed_month_cells[1]) - torch.cat(observed_month_cells[2])
        blocks["precipitation_temperature_dependence"].append(
            _residual(_correlation(generated_precip, generated_dtr), _correlation(observed_precip, observed_dtr), "dependence")
        )

    reduced = {}
    for name, residuals in blocks.items():
        values = torch.stack(residuals)
        reduced[name] = values.square().mean() if squared else values.abs().mean()
    return torch.stack(list(reduced.values())).mean(), reduced


def _forward(model: Any, features: torch.Tensor, station: torch.Tensor, hidden_size: int) -> tuple[torch.Tensor, torch.Tensor]:
    if isinstance(model, accepted.StateSpace):
        return model(features, station)
    hidden = torch.zeros((1, len(features), hidden_size), device=features.device)
    head_chunks, state_chunks = [], []
    for start in range(0, features.shape[1], 365):
        heads, hidden = model(features[:, start : start + 365], station, hidden)
        head_chunks.append(heads)
        state_chunks.append(hidden.transpose(0, 1))
    return torch.cat(head_chunks, dim=1), torch.cat(state_chunks, dim=1)


def score_model(
    model: Any,
    records: list[CalendarRecord],
    selections: list[tuple[int, int]],
    members: int,
    device: torch.device,
    validation_index: int,
    seed_base: int,
    hidden_size: int = 80,
) -> dict[str, Any]:
    totals: dict[str, float] = {}
    daily_total = 0.0
    count = 0
    support = True
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            features, precipitation, targets, weather, station, months, years = climate_batch(
                records, subset, device, validation_index
            )
            heads, _ = _forward(model, features, station, hidden_size)
            uniforms = member_uniforms(members, len(subset), heads.shape[1], seed_base + offset, device)
            generated, wet, _ = sample_weather(heads, uniforms, None)
            score, blocks = climate_components(generated, wet, weather, months, years, squared=False)
            primary, _ = accepted.mixed_nll(heads, precipitation, targets, "lognormal_wet_v2")
            weight = len(subset)
            count += weight
            daily_total += float(primary.cpu()) * weight
            for name, value in blocks.items():
                totals[name] = totals.get(name, 0.0) + float(value.cpu()) * weight
            support = support and bool(
                torch.isfinite(generated).all()
                and (generated[..., 0] >= 0.0).all()
                and (generated[..., 1] >= generated[..., 2]).all()
                and torch.isfinite(score)
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


def checkpoint_subset(records: list[CalendarRecord], regimes: tuple[str, ...], per_regime: int) -> list[tuple[int, int]]:
    selections = []
    for regime in regimes:
        eligible = sorted(
            ((item.record.point_id, index) for index, item in enumerate(records) if item.record.regime == regime),
            key=lambda row: row[0],
        )
        if len(eligible) < per_regime:
            raise RuntimeError(f"checkpoint regime incomplete: {regime}")
        selections.extend((index, 0) for _, index in eligible[:per_regime])
    return selections


def train_treatment(
    contract: dict[str, Any],
    fit: list[CalendarRecord],
    validation: list[CalendarRecord],
    device: torch.device,
    output: Path,
) -> tuple[accepted.StateSpace, dict[str, Any]]:
    definition = contract["architecture"]
    training = contract["training"]
    checkpoint = contract["checkpoint"]
    stochastic = contract["stochastic"]
    legacy.configure(definition["training_seed"])
    model = accepted.StateSpace(
        definition["latent_dim"], definition["width"], definition["depth"],
        definition["amount_family"], len(fit),
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=training["learning_rate"], weight_decay=training["weight_decay"]
    )
    sampler = np.random.Generator(np.random.Philox(definition["training_seed"]))
    by_regime = {
        regime: [index for index, item in enumerate(fit) if item.record.regime == regime]
        for regime in legacy.REGIMES
    }
    if any(len(rows) != 200 for rows in by_regime.values()):
        raise RuntimeError("candidate-fit regime roster mismatch")
    subset = checkpoint_subset(validation, legacy.REGIMES, checkpoint["points_per_regime"])
    best_score, best_epoch, best_payload, patience = math.inf, -1, None, 0
    trace = []
    started = time.monotonic()
    for epoch in range(checkpoint["maximum_epochs"]):
        model.train()
        train_rows = []
        for batch_index in range(training["batches_per_epoch"]):
            regime = legacy.REGIMES[batch_index % len(legacy.REGIMES)]
            selections = []
            for _ in range(training["records_per_batch"]):
                record_index = int(sampler.choice(by_regime[regime]))
                window_index = int(sampler.integers(len(fit[record_index].windows)))
                selections.append((record_index, window_index))
            features, precipitation, targets, weather, station, months, years = climate_batch(
                fit, selections, device, model.validation_index
            )
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                heads, states = model(features, station)
            uniforms = member_uniforms(
                stochastic["training_members"], len(selections), heads.shape[1],
                definition["training_seed"] + epoch * 1009 + batch_index, device,
            )
            generated, wet, _ = sample_weather(heads, uniforms, stochastic["relaxed_wet_temperature"])
            climate_loss, block_losses = climate_components(generated, wet, weather, months, years, squared=True)
            daily_nll, _ = accepted.mixed_nll(heads, precipitation, targets, definition["amount_family"])
            stability = states.float().square().mean()
            objective = (
                contract["objective"]["climate_block_weight"] * climate_loss
                + contract["objective"]["daily_proper_nll_weight"] * daily_nll
                + contract["objective"]["latent_stability_weight"] * stability
            )
            objective.backward()
            if not math.isfinite(float(objective)) or not all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
                for parameter in model.parameters()
            ):
                raise RuntimeError("non-finite treatment training state")
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_rows.append(
                {
                    "climate_loss": float(climate_loss.detach().cpu()),
                    "daily_proper_nll": float(daily_nll.detach().cpu()),
                    "objective": float(objective.detach().cpu()),
                    "block_losses": {name: float(value.detach().cpu()) for name, value in block_losses.items()},
                }
            )
        model.eval()
        validation_score = score_model(
            model, validation, subset, stochastic["evaluation_members"], device,
            model.validation_index, 910000 + epoch * 100,
        )
        score = validation_score["family_balanced_climate_score"]
        improved = score < best_score - checkpoint["tie_tolerance"]
        if improved:
            best_score, best_epoch, patience = score, epoch + 1, 0
            best_payload = copy.deepcopy(model.state_dict())
        else:
            patience += 1
        trace.append(
            {
                "epoch": epoch + 1,
                "improved": improved,
                "train_climate_loss": statistics.fmean(row["climate_loss"] for row in train_rows),
                "train_daily_proper_nll": statistics.fmean(row["daily_proper_nll"] for row in train_rows),
                "train_objective": statistics.fmean(row["objective"] for row in train_rows),
                "validation": validation_score,
            }
        )
        if epoch + 1 >= checkpoint["minimum_epochs"] and patience >= checkpoint["early_stop_patience"]:
            break
    if best_payload is None:
        raise RuntimeError("no treatment checkpoint")
    model.load_state_dict(best_payload)
    model.eval()
    checkpoint_path = output / "treatment-checkpoint.pt"
    torch.save({"model": best_payload, "epoch": best_epoch, "training_seed": definition["training_seed"]}, checkpoint_path)
    result = {
        "best_epoch": best_epoch,
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": digest(checkpoint_path),
        "epochs_completed": len(trace),
        "fit_points": len(fit),
        "fit_validation_gradient": False,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "trace": trace,
        "wall_seconds": time.monotonic() - started,
    }
    atomic_json(output / "treatment-training.json", result)
    return model, result


def decision(control: dict[str, Any], treatment: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    thresholds = contract["decision"]
    improvement = 1.0 - treatment["family_balanced_climate_score"] / control["family_balanced_climate_score"]
    block_guards = {
        name: treatment["block_scores"][name]
        <= (1.0 + thresholds["maximum_block_degradation_fraction"]) * control["block_scores"][name]
        for name in control["block_scores"]
    }
    nll_guard = treatment["daily_proper_nll"] <= (
        1.0 + thresholds["maximum_daily_nll_degradation_fraction"]
    ) * control["daily_proper_nll"]
    advances = bool(
        control["support"]
        and treatment["support"]
        and improvement >= thresholds["minimum_climate_score_improvement_fraction"]
        and all(block_guards.values())
        and nll_guard
    )
    return {
        "advances": advances,
        "block_non_degradation": block_guards,
        "climate_score_improvement_fraction": improvement,
        "daily_proper_nll_guard": nll_guard,
        "selected_arm": "climate_statistics_treatment" if advances else "none",
        "terminal": "A10M5R8-CORE-OBJECTIVE-READY" if advances else "HOLD-A10M5R8-CORE-OBJECTIVE-NOT-SUPPORTED",
    }


def self_test() -> None:
    days = 2922
    dates = [dt.date(2001, 1, 1) + dt.timedelta(days=index) for index in range(days)]
    months = [np.asarray([date.month - 1 for date in dates], dtype=np.int64)]
    years = [np.asarray([date.year - 2001 for date in dates], dtype=np.int64)]
    phase = torch.linspace(0.0, 16.0 * math.pi, days)
    observed = torch.stack(
        (2.0 + torch.sin(phase).clamp_min(0.0), 20.0 + 8.0 * torch.sin(phase), 8.0 + 6.0 * torch.sin(phase)), dim=1
    ).unsqueeze(0)
    generated = observed.unsqueeze(0).repeat(4, 1, 1, 1)
    wet = (generated[..., 0] >= 1.0).float()
    exact, exact_blocks = climate_components(generated, wet, observed, months, years, squared=False)
    perturbed = generated.clone()
    annual_scale = torch.tensor([0.5, 0.8, 1.2, 1.5]).view(4, 1, 1, 1)
    perturbed[..., :1] *= annual_scale
    changed, changed_blocks = climate_components(perturbed, wet, observed, months, years, squared=False)
    if float(exact) > 1e-5:
        raise RuntimeError("identical climate self-test did not score zero")
    if float(changed_blocks["monthly_interannual_dispersion"]) <= float(exact_blocks["monthly_interannual_dispersion"]):
        raise RuntimeError("monthly dispersion self-test is insensitive")
    if float(changed_blocks["annual_interannual_dispersion"]) <= float(exact_blocks["annual_interannual_dispersion"]):
        raise RuntimeError("annual dispersion self-test is insensitive")
    shifted = torch.roll(generated, 17, dims=2)
    shifted_score, _ = climate_components(shifted, torch.roll(wet, 17, dims=2), observed, months, years, squared=False)
    if not math.isfinite(float(shifted_score)):
        raise RuntimeError("aggregate-only shifted self-test is non-finite")
    print("A10M5R8-CLIMATE-CORE-SELF-TEST-PASS")


if __name__ == "__main__":
    self_test()
