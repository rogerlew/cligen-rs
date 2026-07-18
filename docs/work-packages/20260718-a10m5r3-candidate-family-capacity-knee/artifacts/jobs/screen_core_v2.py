#!/usr/bin/env python3
"""A10M5R3 family-correct training and deterministic generation core."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import math
import os
import random
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import legacy_core as legacy

FAMILIES = ("lognormal_wet_v2", "gamma_wet_v2", "lognormal_body_gpd_excess_v2")
THRESHOLD = 20.0
SEEDS = (147031, 271828, 314159)
CAPACITIES = {
    "P0": (32, 128, 2), "P1": (80, 160, 2), "P2": (144, 288, 2),
    "P3": (272, 544, 2), "P4": (480, 960, 2),
}
STATIONS = legacy.STATIONS
REGIMES = legacy.REGIMES


class StateSpace(nn.Module):
    def __init__(self, latent: int, width: int, depth: int, family: str, fit_count: int) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        size = 13
        for _ in range(depth):
            layers.extend((nn.Linear(size, width), nn.ReLU()))
            size = width
        self.encoder = nn.Sequential(*layers)
        self.embedding = None
        self.validation_index = fit_count
        self.transition = nn.GRU(width, latent, batch_first=True)
        self.head = nn.Linear(latent, 18 if family == FAMILIES[2] else 15)

    def forward(self, features: torch.Tensor, station: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        del station
        encoded = self.encoder(features)
        if features.device.type == "cuda":
            with torch.autocast(device_type="cuda", enabled=False):
                states, _ = self.transition(encoded.float())
        else:
            states, _ = self.transition(encoded.float())
        return self.head(states), states


StreamingExport = legacy.StreamingExport


def amount_parameters(heads: torch.Tensor, family: str) -> tuple[dict[str, torch.Tensor], int]:
    if family == FAMILIES[0]:
        return {"location": heads[..., 1], "scale": nn.functional.softplus(heads[..., 2]) + 1e-4}, 3
    if family == FAMILIES[1]:
        return {"shape": nn.functional.softplus(heads[..., 1]) + 0.05, "scale": nn.functional.softplus(heads[..., 2]) + 1e-4}, 3
    if family == FAMILIES[2]:
        return {
            "location": heads[..., 1], "body_scale": nn.functional.softplus(heads[..., 2]) + 1e-4,
            "tail_mass": torch.sigmoid(heads[..., 3]), "tail_shape": 0.25 * torch.sigmoid(heads[..., 4]),
            "tail_scale": nn.functional.softplus(heads[..., 5]) + 1e-4,
        }, 6
    raise RuntimeError("unknown amount family")


def normal_cdf(value: torch.Tensor) -> torch.Tensor:
    return 0.5 * (1.0 + torch.erf(value / math.sqrt(2.0)))


def amount_expectation(parameters: dict[str, torch.Tensor], family: str) -> torch.Tensor:
    if family == FAMILIES[0]:
        return torch.exp(parameters["location"] + 0.5 * parameters["scale"].square())
    if family == FAMILIES[1]:
        return parameters["shape"] * parameters["scale"]
    location, scale = parameters["location"], parameters["body_scale"]
    z = (math.log(THRESHOLD) - location) / scale
    body = torch.exp(location + 0.5 * scale.square()) * normal_cdf(z - scale) / normal_cdf(z).clamp_min(1e-8)
    tail = THRESHOLD + parameters["tail_scale"] / (1.0 - parameters["tail_shape"])
    return (1.0 - parameters["tail_mass"]) * body + parameters["tail_mass"] * tail


def gamma_quantile(shape: torch.Tensor, scale: torch.Tensor, probability: torch.Tensor) -> torch.Tensor:
    low = torch.zeros_like(shape)
    high = torch.maximum(shape * scale + 12.0 * torch.sqrt(shape) * scale, torch.full_like(shape, 10.0))
    probability = probability.clamp(1e-7, 1.0 - 1e-7)
    for _ in range(36):
        middle = 0.5 * (low + high)
        cdf = torch.special.gammainc(shape, middle / scale)
        low = torch.where(cdf < probability, middle, low)
        high = torch.where(cdf >= probability, middle, high)
    return 0.5 * (low + high)


def amount_quantile(parameters: dict[str, torch.Tensor], family: str, probability: torch.Tensor) -> torch.Tensor:
    probability = torch.broadcast_to(probability, next(iter(parameters.values())).shape).clamp(1e-7, 1.0 - 1e-7)
    if family == FAMILIES[0]:
        normal = math.sqrt(2.0) * torch.erfinv(2.0 * probability - 1.0)
        return torch.exp(parameters["location"] + parameters["scale"] * normal)
    if family == FAMILIES[1]:
        return gamma_quantile(parameters["shape"], parameters["scale"], probability)
    mass = parameters["tail_mass"]
    body_probability = (probability / (1.0 - mass).clamp_min(1e-7)).clamp(1e-7, 1.0 - 1e-7)
    z_threshold = (math.log(THRESHOLD) - parameters["location"]) / parameters["body_scale"]
    truncated_probability = (body_probability * normal_cdf(z_threshold)).clamp(1e-7, 1.0 - 1e-7)
    body_normal = math.sqrt(2.0) * torch.erfinv(2.0 * truncated_probability - 1.0)
    body = torch.exp(parameters["location"] + parameters["body_scale"] * body_normal)
    tail_probability = ((probability - (1.0 - mass)) / mass.clamp_min(1e-7)).clamp(0.0, 1.0 - 1e-7)
    shape, scale = parameters["tail_shape"], parameters["tail_scale"]
    excess = scale * (torch.pow(1.0 - tail_probability, -shape) - 1.0) / shape
    return torch.where(probability <= 1.0 - mass, body, THRESHOLD + excess)


def mixed_nll(heads: torch.Tensor, precipitation: torch.Tensor, targets: torch.Tensor, family: str) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    heads, precipitation, targets = heads[:, 60:].float(), precipitation[:, 60:].float(), targets[:, 60:].float()
    wet = (precipitation >= 1.0).float()
    occurrence = nn.functional.binary_cross_entropy_with_logits(heads[..., 0], wet)
    positive = wet.bool()
    parameters, continuous_start = amount_parameters(heads, family)
    if positive.any():
        values = precipitation[positive]
        selected = {key: value[positive] for key, value in parameters.items()}
        if family == FAMILIES[0]:
            logged = torch.log(values)
            amount = (torch.log(selected["scale"]) + 0.5 * ((logged - selected["location"]) / selected["scale"]).square() + logged).mean()
        elif family == FAMILIES[1]:
            shape, scale = selected["shape"], selected["scale"]
            amount = (torch.lgamma(shape) + shape * torch.log(scale) - (shape - 1.0) * torch.log(values) + values / scale).mean()
        else:
            body = values <= THRESHOLD
            location, scale = selected["location"], selected["body_scale"]
            lognormal = torch.log(scale) + 0.5 * ((torch.log(values) - location) / scale).square() + torch.log(values)
            logcdf = torch.log(normal_cdf((math.log(THRESHOLD) - location) / scale).clamp_min(1e-8))
            body_nll = -torch.log1p(-selected["tail_mass"].clamp(max=1.0 - 1e-7)) + lognormal + logcdf
            excess = (values - THRESHOLD).clamp_min(0.0)
            tail_nll = -torch.log(selected["tail_mass"].clamp_min(1e-7)) + torch.log(selected["tail_scale"]) + (1.0 / selected["tail_shape"] + 1.0) * torch.log1p(selected["tail_shape"] * excess / selected["tail_scale"])
            amount = torch.where(body, body_nll, tail_nll).mean()
    else:
        amount = occurrence * 0.0
    locations = heads[..., continuous_start::2]
    scales = nn.functional.softplus(heads[..., continuous_start + 1::2]) + 1e-4
    continuous = (torch.log(scales) + 0.5 * ((targets - locations) / scales).square()).mean()
    primary = occurrence + amount + continuous
    return primary, {"occurrence": occurrence, "amount": amount, "continuous": continuous}


def auxiliary_loss(heads: torch.Tensor, states: torch.Tensor, precipitation: torch.Tensor, targets: torch.Tensor, model: StateSpace, family: str) -> tuple[torch.Tensor, dict[str, float]]:
    del model
    heads, states = heads[:, 60:].float(), states[:, 60:].float()
    precipitation, targets = precipitation[:, 60:].float(), targets[:, 60:].float()
    wet = (precipitation >= 1.0).float()
    probability = torch.sigmoid(heads[..., 0])
    parameters, continuous_start = amount_parameters(heads, family)
    expected = probability * amount_expectation(parameters, family)
    transition = nn.functional.mse_loss(probability[:, 1:] - probability[:, :-1], wet[:, 1:] - wet[:, :-1])
    monthly = (torch.log1p(expected.mean(dim=1)) - torch.log1p(precipitation.mean(dim=1))).square().mean()
    half = precipitation.shape[1] // 2
    annual = (torch.asinh(expected[:, :half].sum(1) - expected[:, half:2*half].sum(1)) - torch.asinh(precipitation[:, :half].sum(1) - precipitation[:, half:2*half].sum(1))).square().mean()
    predicted_context = ((probability - probability.mean(1, keepdim=True)) * (heads[..., continuous_start] - heads[..., continuous_start].mean(1, keepdim=True))).mean(1)
    observed_context = ((wet - wet.mean(1, keepdim=True)) * (targets[..., 0] - targets[..., 0].mean(1, keepdim=True))).mean(1)
    context = (predicted_context - observed_context).square().mean()
    stability = states.square().mean()
    terms = {"wet_dry_spell_survival": transition, "monthly_expected_precipitation": monthly, "annual_aggregate_dispersion": annual, "precipitation_context_dependence": context, "latent_state_stability": stability}
    total = 0.05 * transition + 0.05 * monthly + 0.04 * annual + 0.04 * context + 0.02 * stability
    return total, {key: float(value.detach().cpu()) for key, value in terms.items()}


def validation_metrics(model: StateSpace, records: list[Any], family: str, device: torch.device) -> tuple[float, float, float, dict[str, float]]:
    by_regime: dict[str, list[tuple[float, float, float]]] = {regime: [] for regime in REGIMES}
    selections: list[tuple[int, int]] = []
    with torch.no_grad():
        for record_index, record in enumerate(records):
            for start_index in range(len(record.starts)):
                selections.append((record_index, start_index))
                if len(selections) == 64:
                    evaluate_batch(model, records, selections, family, device, by_regime); selections.clear()
        if selections:
            evaluate_batch(model, records, selections, family, device, by_regime)
    if any(not rows for rows in by_regime.values()):
        raise RuntimeError("validation regime has no eligible windows")
    regime_primary = {regime: statistics.fmean(row[0] for row in rows) for regime, rows in by_regime.items()}
    return statistics.fmean(regime_primary.values()), statistics.fmean(statistics.fmean(row[1] for row in rows) for rows in by_regime.values()), statistics.fmean(statistics.fmean(row[2] for row in rows) for rows in by_regime.values()), regime_primary


def evaluate_batch(model: StateSpace, records: list[Any], selections: list[tuple[int, int]], family: str, device: torch.device, output: dict[str, list[tuple[float, float, float]]]) -> None:
    features, precipitation, targets, station = legacy.batch(records, selections, device, model.validation_index)
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        heads, states = model(features, station)
    for regime in REGIMES:
        indices = [i for i, (record_index, _) in enumerate(selections) if records[record_index].regime == regime]
        if not indices:
            continue
        subset = torch.tensor(indices, dtype=torch.long, device=device)
        rh, rp, rt = heads.index_select(0, subset), precipitation.index_select(0, subset), targets.index_select(0, subset)
        primary, _ = mixed_nll(rh, rp, rt, family)
        wet_values = rp[:, 60:][rp[:, 60:] >= 1.0]
        empirical = torch.quantile(wet_values.float(), 0.95) if wet_values.numel() else torch.tensor(0.0, device=device)
        parameters, _ = amount_parameters(rh[:, 60:].float(), family)
        predicted = amount_quantile(parameters, family, torch.tensor(0.95, device=device)).median()
        tail = float(torch.abs(torch.log1p(predicted) - torch.log1p(empirical)).cpu())
        stable = float(states.index_select(0, subset)[:, 60:].float().square().mean().sqrt().cpu())
        output[regime].extend([(float(primary.cpu()), tail, stable)] * len(indices))


def family_calibration(family: str) -> dict[str, Any]:
    torch.manual_seed(80817)
    head_count = 18 if family == FAMILIES[2] else 15
    heads = torch.zeros((4096, head_count), dtype=torch.float64, requires_grad=True)
    parameters, _ = amount_parameters(heads, family)
    probabilities = (torch.arange(4096, dtype=torch.float64) + 0.5) / 4096.0
    samples = amount_quantile(parameters, family, probabilities)
    expected = amount_expectation(parameters, family)
    empirical_mean = samples.mean()
    quantile = amount_quantile(parameters, family, torch.full((4096,), 0.95, dtype=torch.float64))[0]
    empirical_cdf = (samples <= quantile).double().mean()
    loss = samples.log1p().mean() + expected.mean() + quantile
    loss.backward()
    gates = {
        "positive_support": bool(torch.isfinite(samples).all() and (samples > 0).all()),
        "expectation_relative_error": bool(abs(float(empirical_mean / expected.mean() - 1.0)) <= 0.035),
        "quantile_empirical_error": bool(abs(float(empirical_cdf) - 0.95) <= 0.01),
        "finite_gradients": bool(heads.grad is not None and torch.isfinite(heads.grad).all()),
        "finite_analytic_values": bool(torch.isfinite(expected).all() and torch.isfinite(quantile)),
    }
    return {"family": family, "sample_count": 4096, "analytic_expectation": float(expected.mean()), "empirical_expectation": float(empirical_mean), "predicted_q95": float(quantile), "empirical_cdf_at_q95": float(empirical_cdf), "gates": gates, "valid": all(gates.values())}


def training(options: Any, definition: dict[str, Any], output: Path) -> tuple[StateSpace, dict[str, Any], dict[str, Any]]:
    started = time.monotonic()
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or "L40" not in torch.cuda.get_device_name(0):
        raise RuntimeError("exactly one typed L40 is required")
    transfer, normalized, normalization = legacy.verify_corpus(options.corpus)
    fit, validation, role_counts = legacy.load_daymet(options.corpus, normalized, normalization)
    by_regime = {regime: [i for i, record in enumerate(fit) if record.regime == regime] for regime in REGIMES}
    if any(len(rows) != 200 for rows in by_regime.values()):
        raise RuntimeError("candidate-fit regime roster mismatch")
    device = torch.device("cuda:0")
    model = StateSpace(definition["latent_dim"], definition["width"], definition["depth"], definition["amount_family"], len(fit)).to(device)
    count = sum(parameter.numel() for parameter in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0003, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    generator = np.random.Generator(np.random.Philox(options.seed))
    best_primary, best_epoch, patience, best_payload = math.inf, -1, 0, None
    trace, global_step = [], 0
    checkpoint_dir = output / "rolling"; checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for epoch in range(100):
        model.train(); losses, auxiliary, order_words = [], {}, []
        for batch_index in range(12):
            regime = REGIMES[batch_index % 6]; selections = []
            for _ in range(64):
                record_index = int(generator.choice(by_regime[regime])); start_index = int(generator.integers(len(fit[record_index].starts)))
                selections.append((record_index, start_index)); order_words.append(f"{record_index}:{start_index}")
            features, precipitation, targets, station = legacy.batch(fit, selections, device, model.validation_index)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16): heads, states = model(features, station)
            primary, _ = mixed_nll(heads, precipitation, targets, definition["amount_family"])
            aux, auxiliary = auxiliary_loss(heads, states, precipitation, targets, model, definition["amount_family"])
            loss = primary + aux; loss.backward()
            if not math.isfinite(float(loss)) or not all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters()): raise RuntimeError("non-finite training state")
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step(); global_step += 1; losses.append(float(loss.detach().cpu()))
        scheduler.step(); model.eval()
        primary_value, tail_value, stability_value, regime_primary = validation_metrics(model, validation, definition["amount_family"], device)
        improved = primary_value < best_primary - 1e-4
        if improved: best_primary, best_epoch, patience = primary_value, epoch + 1, 0
        else: patience += 1
        payload = {"model": model.state_dict(), "optimizer": optimizer.state_dict(), "scheduler": scheduler.state_dict(), "scaler": scaler.state_dict(), "rng": legacy.rng_state(), "sampler": generator.bit_generator.state, "corpus_cursor": {"epoch_order_sha256": hashlib.sha256("\n".join(order_words).encode()).hexdigest(), "next_batch": 0}, "epoch": epoch + 1, "global_step": global_step}
        rolling = checkpoint_dir / f"epoch-{epoch+1:03d}.pt"; legacy.atomic_torch(rolling, payload)
        for stale in sorted(checkpoint_dir.glob("epoch-*.pt"))[:-2]: stale.unlink()
        if improved: best_payload = copy.deepcopy(payload)
        trace.append({"epoch": epoch + 1, "global_step": global_step, "train_loss": statistics.fmean(losses), "validation_primary_nll": primary_value, "validation_tail_score": tail_value, "validation_stability": stability_value, "regime_primary_nll": regime_primary, "improved": improved, "auxiliary_last_batch": auxiliary})
        if epoch + 1 >= 20 and patience >= 10: break
    if best_payload is None: raise RuntimeError("no finite best checkpoint")
    final_checkpoint = output / "checkpoint.pt"; legacy.atomic_torch(final_checkpoint, best_payload); model.load_state_dict(best_payload["model"]); model.eval()
    checkpoint = {"schema_version": 1, "checkpoint_id": f"a10m5r3-{options.row_id}", "model_id": f"a10m5r3-{options.row_id}", "epoch": best_epoch, "global_step": int(best_payload["global_step"]), "training_seed": options.seed, "payload_sha256": legacy.sha256(final_checkpoint), "payload_bytes": final_checkpoint.stat().st_size, "state": {key: True for key in ("model", "optimizer", "scheduler", "scaler", "rng", "sampler")}, "corpus_cursor": best_payload["corpus_cursor"], "created_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    legacy.atomic_json(output / "checkpoint-record.json", checkpoint)
    final = trace[best_epoch - 1]
    result = {"aggregate_bytes": transfer["aggregate_bytes"], "object_count": len(transfer["objects"]), "role_counts": role_counts, "fit_role": "candidate_fit", "validation_role": "fit_validation", "validation_used_for_gradient": False, "normalization_role": normalization["fit_role_only"], "epochs_completed": len(trace), "best_epoch": best_epoch, "global_step": global_step, "parameter_count": count, "validation_primary_nll": final["validation_primary_nll"], "validation_tail_score": final["validation_tail_score"], "validation_stability": final["validation_stability"], "gpu_peak_bytes": int(torch.cuda.max_memory_allocated()), "wall_seconds": time.monotonic() - started, "trace": trace}
    legacy.atomic_json(output / "training.json", result)
    return model, result, checkpoint


def candidate_stream(model: Any, family: str, station: tuple[str, str, float, float, float], years: int) -> tuple[str, bytes, bool]:
    _, station_id, latitude, longitude, elevation = station
    days = legacy.days_for_years(years); words = legacy.philox_words(station_id, 101, 0, days)
    uniforms = (words.astype(np.float64) + 0.5) / 4294967296.0
    features = torch.from_numpy(legacy.generation_features(years, latitude, longitude, elevation)).unsqueeze(0)
    index = torch.tensor([model.validation_index]); hidden = torch.zeros((1, 1, model.transition.hidden_size)); chunks = []
    with torch.inference_mode():
        for start in range(0, days, 365):
            heads, hidden = model(features[:, start:start+365], index, hidden); chunks.append(heads.squeeze(0))
    heads_t = torch.cat(chunks).double(); probability = torch.sigmoid(heads_t[:, 0]).numpy(); wet = uniforms[:, 0] < probability
    parameters, continuous_start = amount_parameters(heads_t, family)
    amount = amount_quantile(parameters, family, torch.from_numpy(uniforms[:, 1])).numpy()
    heads = heads_t.numpy(); locations = heads[:, continuous_start::2]; scales = np.log1p(np.exp(heads[:, continuous_start+1::2])) + 1e-4
    normals = np.sqrt(-2.0 * np.log(uniforms[:, [1]])) * np.cos(2.0 * np.pi * (uniforms[:, [2]] + np.arange(6) / 7.0))
    values = locations + scales * normals; tmean, dtr = values[:, 0], np.exp(values[:, 1])
    output = np.column_stack((wet * amount, tmean + dtr/2, tmean-dtr/2, np.exp(values[:, 2]), np.exp(values[:, 3]), np.exp(values[:, 4]), 86400.0/(1.0+np.exp(-values[:, 5])), uniforms[:, 3])).astype("<f4")
    support = bool(np.isfinite(output).all() and np.all(output[:, 0] >= 0) and np.all(output[:, 1] >= output[:, 2]) and np.all(output[:, 3:7] >= 0) and np.all(output[:, 6] <= 86400))
    payload = output.tobytes(); return hashlib.sha256(payload).hexdigest(), payload, support


legacy.candidate_stream = candidate_stream
benchmark = legacy.benchmark
sha256 = legacy.sha256
atomic_json = legacy.atomic_json
configure = legacy.configure
days_for_years = legacy.days_for_years
