#!/usr/bin/env python3
"""Continuous latent-process candidates for A10M5R12."""

from __future__ import annotations

import copy
import math
import statistics
import time
from pathlib import Path
from typing import Any

import torch
from torch import nn

import climate_core as climate
import legacy_core as legacy
import portfolio_core as portfolio
import residual_core as residuals

CANDIDATES = (
    "continuous_medium_latent_process",
    "continuous_hierarchical_latent_process",
)
CAPACITY = "K2"
CORE_HEAD_INDICES = (0, 1, 3, 5)


def projection() -> torch.Tensor:
    value = torch.zeros((len(CORE_HEAD_INDICES), 15))
    for row, column in enumerate(CORE_HEAD_INDICES):
        value[row, column] = 1.0
    return value


def bounded_time_scales(
    raw: torch.Tensor, lower_days: float, upper_days: float
) -> torch.Tensor:
    return lower_days + (upper_days - lower_days) * torch.sigmoid(raw)


def initial_raw_time_scales(latent_dim: int) -> nn.Parameter:
    fractions = torch.linspace(0.15, 0.85, latent_dim)
    return nn.Parameter(torch.logit(fractions))


def stationary_ou_states(
    innovations: torch.Tensor,
    raw_time_scales: torch.Tensor,
    lower_days: float,
    upper_days: float,
) -> torch.Tensor:
    """Exact daily discretization of a stationary continuous-time OU process."""
    if innovations.ndim != 4 or innovations.shape[2] < 2:
        raise RuntimeError("OU innovations require [members,batch,days,latent]")
    if innovations.shape[3] != raw_time_scales.numel():
        raise RuntimeError("OU innovation and time-scale dimensions differ")
    time_scales = bounded_time_scales(
        raw_time_scales, lower_days, upper_days
    )
    rho = torch.exp(-1.0 / time_scales)
    innovation_scale = torch.sqrt((1.0 - rho.square()).clamp_min(1e-7))
    adjusted = torch.cat(
        (innovations[:, :, :1], innovations[:, :, 1:] * innovation_scale),
        dim=2,
    )
    steps = innovations.shape[2]
    powers = torch.arange(steps, dtype=innovations.dtype, device=innovations.device)
    kernel = rho.unsqueeze(1).pow(powers.unsqueeze(0))
    fft_size = 1 << (2 * steps - 2).bit_length()
    source = adjusted.permute(0, 1, 3, 2)
    source_fft = torch.fft.rfft(source, n=fft_size, dim=-1)
    kernel_fft = torch.fft.rfft(kernel, n=fft_size, dim=-1)
    states = torch.fft.irfft(
        source_fft * kernel_fft.unsqueeze(0).unsqueeze(0),
        n=fft_size,
        dim=-1,
    )[..., :steps]
    return states.permute(0, 1, 3, 2)


class ContinuousLatentProcess(portfolio.PortfolioCandidate):
    """Seasonally loaded OU factors with no calendar-month or year resets."""

    def __init__(
        self,
        candidate: str,
        days: int,
        medium_dim: int,
        slow_dim: int,
        context_width: int,
        medium_bounds: tuple[float, float],
        slow_bounds: tuple[float, float] | None,
    ) -> None:
        super().__init__()
        if candidate not in CANDIDATES:
            raise RuntimeError("unknown continuous candidate")
        if (slow_bounds is None) != (candidate == CANDIDATES[0]):
            raise RuntimeError("slow-process ablation identity mismatch")
        self.candidate = candidate
        self.days = days
        self.medium_dim = medium_dim
        self.slow_dim = 0 if slow_bounds is None else slow_dim
        self.medium_bounds = medium_bounds
        self.slow_bounds = slow_bounds
        self.raw_medium_time_scales = initial_raw_time_scales(medium_dim)
        if slow_bounds is not None:
            self.raw_slow_time_scales = initial_raw_time_scales(slow_dim)
        self.context_basis = nn.Sequential(
            nn.Linear(5, context_width),
            nn.Tanh(),
        )
        self.medium_loadings = nn.Linear(
            context_width,
            medium_dim * len(CORE_HEAD_INDICES),
            bias=False,
        )
        nn.init.normal_(self.medium_loadings.weight, mean=0.0, std=0.01)
        if slow_bounds is not None:
            self.slow_loadings = nn.Linear(
                context_width,
                slow_dim * len(CORE_HEAD_INDICES),
                bias=False,
            )
            nn.init.normal_(self.slow_loadings.weight, mean=0.0, std=0.01)
        self.register_buffer("head_projection", projection())

    def innovation_shapes(self) -> dict[str, tuple[int, int]]:
        output = {"medium_daily": (self.days, self.medium_dim)}
        if self.slow_bounds is not None:
            output["slow_daily"] = (self.days, self.slow_dim)
        return output

    def member_heads(
        self,
        base_heads: torch.Tensor | None,
        features: torch.Tensor,
        regimes: torch.Tensor,
        months: torch.Tensor,
        years: torch.Tensor,
        innovations: dict[str, torch.Tensor],
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        del regimes, months, years
        if base_heads is None:
            raise RuntimeError("continuous process requires a frozen control")
        if features.shape[-1] != 6 or features.shape[1] != base_heads.shape[1]:
            raise RuntimeError("continuous context must be daily calendar/static features")
        medium = stationary_ou_states(
            innovations["medium_daily"],
            self.raw_medium_time_scales,
            *self.medium_bounds,
        )
        states = [medium]
        diagnostics = {"medium_daily_states": medium}
        if self.slow_bounds is not None:
            slow = stationary_ou_states(
                innovations["slow_daily"],
                self.raw_slow_time_scales,
                *self.slow_bounds,
            )
            states.append(slow)
            diagnostics["slow_daily_states"] = slow
        joint = torch.cat(states, dim=-1)
        # The inherited feature at index 2 is a binary leap-year flag. It is
        # deliberately excluded from the new continuous loading surface.
        context = self.context_basis(features[..., (0, 1, 3, 4, 5)].float())
        loading_parts = [
            self.medium_loadings(context).view(
                features.shape[0],
                features.shape[1],
                self.medium_dim,
                len(CORE_HEAD_INDICES),
            )
        ]
        if self.slow_bounds is not None:
            loading_parts.append(
                self.slow_loadings(context).view(
                    features.shape[0],
                    features.shape[1],
                    self.slow_dim,
                    len(CORE_HEAD_INDICES),
                )
            )
        loadings = torch.cat(loading_parts, dim=2)
        decoded = torch.einsum("mbtl,btlo->mbto", joint, loadings)
        decoded = decoded - decoded.mean(dim=0, keepdim=True)
        heads = base_heads.float().unsqueeze(0) + decoded @ self.head_projection
        diagnostics["combined_offsets"] = decoded
        return heads, diagnostics

    def persistence_values(self) -> dict[str, list[float]]:
        medium = bounded_time_scales(
            self.raw_medium_time_scales, *self.medium_bounds
        )
        output = {
            "medium_time_scale_days": [
                float(value) for value in medium.detach().cpu()
            ]
        }
        if self.slow_bounds is not None:
            slow = bounded_time_scales(
                self.raw_slow_time_scales, *self.slow_bounds
            )
            output["slow_time_scale_days"] = [
                float(value) for value in slow.detach().cpu()
            ]
        return output


def build_candidate(
    contract: dict[str, Any], candidate: str, days: int | None = None
) -> ContinuousLatentProcess:
    if candidate not in CANDIDATES:
        raise RuntimeError("unknown continuous candidate")
    shape = contract["capacity_shapes"][CAPACITY]
    definition = contract["architectures"][candidate]
    window_days = (
        int(days)
        if days is not None
        else int(contract["calendar"]["representative_window"]["axis_rows"])
    )
    slow_bounds = (
        tuple(float(value) for value in definition["slow_time_scale_days"])
        if definition["slow_state"]
        else None
    )
    return ContinuousLatentProcess(
        candidate,
        window_days,
        int(shape["continuous_medium_state_dim"]),
        int(shape["continuous_slow_state_dim"]),
        int(shape["continuous_context_width"]),
        tuple(float(value) for value in definition["medium_time_scale_days"]),
        slow_bounds,
    )


def candidate_innovations(
    model: ContinuousLatentProcess,
    members: int,
    batch: int,
    seed: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    offsets = {"medium_daily": 1, "slow_daily": 2}
    return {
        name: residuals.member_innovations(
            members, batch, days, latent, seed + 100003 * offsets[name], device
        )
        for name, (days, latent) in model.innovation_shapes().items()
    }


def score_candidate(
    model: ContinuousLatentProcess,
    control: torch.jit.ScriptModule,
    hidden_size: int,
    records: list[climate.CalendarRecord],
    selections: list[tuple[int, int]],
    members: int,
    device: torch.device,
    output_seed_base: int,
    innovation_seed_base: int,
    include_points: bool,
) -> dict[str, Any]:
    totals: dict[str, float] = {}
    daily_total, count = 0.0, 0
    support = True
    points = []
    model.eval()
    control.eval()
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            values = portfolio.portfolio_batch(records, subset, device, 1200)
            features, precipitation, targets, observed, station, regimes, month_t, year_t, physics, months, years, valid = values
            base = portfolio.forward_control(control, features, station, hidden_size)
            innovations = candidate_innovations(
                model, members, len(subset), innovation_seed_base + offset, device
            )
            heads, _ = model.member_heads(
                base, physics, regimes, month_t, year_t, innovations
            )
            uniforms = climate.member_uniforms(
                members, len(subset), heads.shape[2], output_seed_base + offset, device
            )
            generated, wet = residuals.sample_member_weather(heads, uniforms, None)
            daily = portfolio.member_daily_nll(heads, precipitation, targets, valid)
            blocks = portfolio._score_blocks(
                generated, wet, observed, months, years, valid
            )
            weight = len(subset)
            count += weight
            daily_total += float(daily.cpu()) * weight
            for name, value in blocks.items():
                totals[name] = totals.get(name, 0.0) + value * weight
            support = support and bool(
                torch.isfinite(generated).all()
                and (generated[..., 0] >= 0.0).all()
                and (generated[..., 1] >= generated[..., 2]).all()
            )
            if include_points:
                for local, (record_index, window_index) in enumerate(subset):
                    point_blocks = portfolio._score_blocks(
                        generated[:, local : local + 1],
                        wet[:, local : local + 1],
                        observed[local : local + 1],
                        [months[local]], [years[local]], [valid[local]],
                    )
                    point_nll = portfolio.member_daily_nll(
                        heads[:, local : local + 1],
                        precipitation[local : local + 1],
                        targets[local : local + 1],
                        [valid[local]],
                    )
                    points.append({
                        "block_scores": point_blocks,
                        "daily_proper_nll": float(point_nll.cpu()),
                        "point_id": records[record_index].record.point_id,
                        "window_first_year": records[record_index].windows[window_index].first_year,
                    })
    block_scores = {
        name: value / count for name, value in sorted(totals.items())
    }
    result = {
        "block_scores": block_scores,
        "daily_proper_nll": daily_total / count,
        "family_balanced_climate_score": statistics.fmean(block_scores.values()),
        "point_count": count,
        "stochastic_members": members,
        "support": support,
    }
    if include_points:
        result["points"] = points
    return result


def train_candidate(
    contract: dict[str, Any],
    candidate: str,
    seed: int,
    control: torch.jit.ScriptModule,
    hidden_size: int,
    fit: list[climate.CalendarRecord],
    validation: list[climate.CalendarRecord],
    device: torch.device,
    output: Path,
) -> tuple[ContinuousLatentProcess, dict[str, Any]]:
    if float(contract["objective"]["paired_daily_pattern_weight"]) != 0.0:
        raise RuntimeError("paired daily pattern loss must remain zero")
    if (
        float(contract["objective"]["daily_proper_nll_weight"]) != 0.0
        or float(
            contract["checkpoint"]["selection_scalar"][
                "daily_proper_nll_weight"
            ]
        )
        != 0.0
    ):
        raise RuntimeError("conditional-member daily NLL must remain diagnostic only")
    legacy.configure(seed)
    model = build_candidate(contract, candidate).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(contract["training"]["continuous_learning_rate"]),
        weight_decay=float(contract["training"]["weight_decay"]),
    )
    generator, by_regime = portfolio.sampler(fit, seed)
    checkpoint = contract["checkpoint"]
    subset = climate.checkpoint_subset(
        validation, legacy.REGIMES, int(checkpoint["points_per_regime"])
    )
    stochastic = contract["stochastic"]
    best_value, best_epoch, best_payload, patience = math.inf, -1, None, 0
    trace = []
    started = time.monotonic()
    for epoch in range(int(checkpoint["maximum_epochs"])):
        model.train()
        epoch_rows = []
        for batch_index in range(int(contract["training"]["batches_per_epoch"])):
            regime = legacy.REGIMES[batch_index % len(legacy.REGIMES)]
            selections = portfolio.draw(
                generator, by_regime, fit, regime,
                int(contract["training"]["records_per_batch"]),
            )
            values = portfolio.portfolio_batch(fit, selections, device, len(fit))
            features, precipitation, targets, observed, station, regimes, month_t, year_t, physics, months, years, valid = values
            with torch.no_grad():
                base = portfolio.forward_control(control, features, station, hidden_size)
            innovations = candidate_innovations(
                model, int(stochastic["training_members"]), len(selections),
                seed + 200000 + epoch * 1009 + batch_index, device,
            )
            optimizer.zero_grad(set_to_none=True)
            heads, diagnostics = model.member_heads(
                base, physics, regimes, month_t, year_t, innovations
            )
            uniforms = climate.member_uniforms(
                int(stochastic["training_members"]), len(selections), heads.shape[2],
                seed + 300000 + epoch * 1009 + batch_index, device,
            )
            generated, wet = residuals.sample_member_weather(
                heads, uniforms, float(contract["training"]["relaxed_wet_temperature"])
            )
            objective, row = portfolio.training_objective(
                heads, diagnostics, generated, wet, precipitation, targets, observed,
                months, years, valid, uniforms, contract, False,
            )
            objective.backward()
            if not math.isfinite(float(objective)) or not all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
                for parameter in model.parameters()
            ):
                raise RuntimeError("non-finite continuous candidate training state")
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), float(contract["training"]["gradient_clip_norm"])
            )
            optimizer.step()
            row["objective"] = float(objective.detach().cpu())
            epoch_rows.append(row)
        validation_score = score_candidate(
            model, control, hidden_size, validation, subset,
            int(stochastic["evaluation_members"]), device,
            610000, 710000, False,
        )
        value = portfolio.checkpoint_value(validation_score, contract)
        improved = value < best_value - float(checkpoint["tie_tolerance"])
        if improved:
            best_value, best_epoch, patience = value, epoch + 1, 0
            best_payload = copy.deepcopy(model.state_dict())
        else:
            patience += 1
        trace.append({
            "checkpoint_value": value,
            "epoch": epoch + 1,
            "improved": improved,
            "train": {
                name: statistics.fmean(row[name] for row in epoch_rows)
                for name in epoch_rows[0]
            },
            "validation": validation_score,
        })
        if (
            epoch + 1 >= int(checkpoint["minimum_epochs"])
            and patience >= int(checkpoint["early_stop_patience"])
        ):
            break
    if best_payload is None:
        raise RuntimeError("continuous candidate produced no checkpoint")
    model.load_state_dict(best_payload)
    model.eval()
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "checkpoint.pt"
    torch.save({
        "candidate": candidate,
        "capacity": CAPACITY,
        "epoch": best_epoch,
        "model": best_payload,
        "training_seed": seed,
    }, checkpoint_path)
    result = {
        "best_epoch": best_epoch,
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": portfolio.digest(checkpoint_path),
        "epochs_completed": len(trace),
        "fit_points": len(fit),
        "fit_validation_gradient": False,
        "model_state_sha256": portfolio.model_state_sha256(model),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "time_scales_days": model.persistence_values(),
        "trace": trace,
        "wall_seconds": time.monotonic() - started,
    }
    return model, result


def self_test(device: torch.device) -> None:
    raw = torch.tensor([0.0], device=device)
    innovations = torch.zeros((2, 1, 64, 1), device=device)
    innovations[:, :, 0] = torch.tensor([1.0, -1.0], device=device).view(2, 1, 1)
    states = stationary_ou_states(innovations, raw, 30.0, 30.0)
    rho = math.exp(-1.0 / 30.0)
    expected = torch.tensor([rho ** index for index in range(64)], device=device)
    if not torch.allclose(states[0, 0, :, 0], expected, atol=2e-5, rtol=2e-5):
        raise RuntimeError("FFT OU state does not match exact recurrence")
    if not torch.allclose(states[1, 0, :, 0], -expected, atol=2e-5, rtol=2e-5):
        raise RuntimeError("OU sign symmetry failed")
    torch.manual_seed(190720)
    random_innovations = torch.randn((2, 1, 2922, 2), device=device)
    random_raw = torch.tensor((-1.25, 1.25), device=device)
    fft_states = stationary_ou_states(
        random_innovations, random_raw, 14.0, 180.0
    )
    time_scales = bounded_time_scales(random_raw, 14.0, 180.0)
    random_rho = torch.exp(-1.0 / time_scales)
    random_scale = torch.sqrt(1.0 - random_rho.square())
    with torch.no_grad():
        current = random_innovations[:, :, 0]
        recurrence = [current]
        for index in range(1, random_innovations.shape[2]):
            current = (
                random_rho * current
                + random_scale * random_innovations[:, :, index]
            )
            recurrence.append(current)
        scalar_states = torch.stack(recurrence, dim=2)
    if not torch.allclose(fft_states, scalar_states, atol=2e-4, rtol=2e-4):
        raise RuntimeError("training-length FFT OU differs from scalar recurrence")
    long_innovations = torch.zeros((2, 1, 36524, 1), device=device)
    long_innovations[:, :, 0] = torch.tensor(
        (1.0, -1.0), device=device
    ).view(2, 1, 1)
    long_raw = torch.tensor((10.0,), device=device)
    long_states = stationary_ou_states(
        long_innovations, long_raw, 180.0, 1460.0
    )
    long_tau = bounded_time_scales(long_raw, 180.0, 1460.0)[0]
    long_rho = torch.exp(-1.0 / long_tau)
    long_expected = long_rho.pow(
        torch.arange(36524, dtype=long_rho.dtype, device=device)
    )
    if not torch.allclose(
        long_states[0, 0, :, 0], long_expected, atol=2e-4, rtol=2e-4
    ):
        raise RuntimeError("generation-length slow OU recurrence drift")
    torch.manual_seed(190721)
    stationary_innovations = torch.randn((256, 1, 2048, 1), device=device)
    stationary_raw = torch.tensor((0.0,), device=device)
    stationary = stationary_ou_states(
        stationary_innovations, stationary_raw, 30.0, 30.0
    )[:, 0, :, 0]
    variance = stationary.var(correction=0)
    covariance = (stationary[:, 1:] * stationary[:, :-1]).mean()
    if not (
        abs(float(variance) - 1.0) < 0.06
        and abs(float(covariance) - math.exp(-1.0 / 30.0)) < 0.06
    ):
        raise RuntimeError("stationary OU variance/autocovariance drift")
    gradient_raw = torch.tensor((0.25,), device=device, requires_grad=True)
    gradient_state = stationary_ou_states(
        torch.randn((2, 1, 128, 1), device=device),
        gradient_raw,
        14.0,
        1460.0,
    )
    gradient_state.square().mean().backward()
    if gradient_raw.grad is None or not bool(torch.isfinite(gradient_raw.grad).all()):
        raise RuntimeError("OU time-scale gradient failed")
    torch.manual_seed(190719)
    medium = ContinuousLatentProcess(
        CANDIDATES[0], 64, 8, 4, 32, (14.0, 180.0), None
    )
    torch.manual_seed(190719)
    hierarchy = ContinuousLatentProcess(
        CANDIDATES[1], 64, 8, 4, 32, (14.0, 180.0), (180.0, 1460.0)
    )
    shared_parameters = (
        (medium.raw_medium_time_scales, hierarchy.raw_medium_time_scales),
        (medium.context_basis[0].weight, hierarchy.context_basis[0].weight),
        (medium.context_basis[0].bias, hierarchy.context_basis[0].bias),
        (medium.medium_loadings.weight, hierarchy.medium_loadings.weight),
    )
    if not all(torch.equal(left, right) for left, right in shared_parameters):
        raise RuntimeError("matched medium-process initialization drift")
    medium = medium.to(device).eval()
    hierarchy = hierarchy.to(device).eval()
    features = torch.randn((1, 64, 6), device=device)
    base = torch.randn((1, 64, 15), device=device)
    regimes = torch.zeros(1, dtype=torch.long, device=device)
    months = torch.arange(64, device=device).remainder(12).view(1, 64)
    years = torch.arange(64, device=device).div(16, rounding_mode="floor").view(1, 64)
    shared = candidate_innovations(medium, 2, 1, 190722, device)
    medium_heads, _ = medium.member_heads(
        base, features, regimes, months, years, shared
    )
    perturbed_heads, _ = medium.member_heads(
        base, features, regimes, months.roll(7, dims=1), years.flip(1), shared
    )
    hierarchy_innovations = {
        "medium_daily": shared["medium_daily"],
        "slow_daily": torch.zeros((2, 1, 64, 4), device=device),
    }
    hierarchy_heads, _ = hierarchy.member_heads(
        base, features, regimes, months, years, hierarchy_innovations
    )
    if not torch.equal(medium_heads, perturbed_heads):
        raise RuntimeError("calendar-bin tensors changed continuous outputs")
    if not torch.allclose(medium_heads, hierarchy_heads, atol=1e-6, rtol=1e-6):
        raise RuntimeError("common medium random field/output ablation drift")
    print("A10M5R12-CONTINUOUS-CORE-SELF-TEST-PASS")
