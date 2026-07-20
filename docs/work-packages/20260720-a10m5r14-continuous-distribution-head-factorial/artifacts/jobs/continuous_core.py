#!/usr/bin/env python3
"""R14 continuous distribution-head factorial candidates."""

from __future__ import annotations

import math
import statistics
from typing import Any

import torch
from torch import nn

import aligned_objective as aligned
import climate_core as climate
import inherited_continuous_core as inherited
import portfolio_core as portfolio
import residual_core as residuals

CANDIDATES = (
    "centered_location_ou",
    "centered_location_ou_smooth_climatology",
    "centered_location_and_scale_ou",
    "centered_location_and_scale_ou_smooth_climatology",
)
CAPACITY = "K2"
LOCATION_HEAD_INDICES = (0, 1, 3, 5)
SCALE_HEAD_INDICES = (2, 4, 6)


def _projection(indices: tuple[int, ...]) -> torch.Tensor:
    value = torch.zeros((len(indices), 15))
    for row, column in enumerate(indices):
        value[row, column] = 1.0
    return value


def smooth_climatology_basis(features: torch.Tensor) -> torch.Tensor:
    """Exact 5-seasonal by 4-geographic outer-product basis (20 terms)."""
    sine = features[..., 0].float()
    cosine = features[..., 1].float()
    seasonal = torch.stack(
        (
            torch.ones_like(sine), sine, cosine, 2.0 * sine * cosine,
            cosine.square() - sine.square(),
        ),
        dim=-1,
    )
    geographic = torch.stack(
        (
            torch.ones_like(sine), features[..., 3].float(),
            features[..., 4].float(), features[..., 5].float(),
        ),
        dim=-1,
    )
    return (seasonal.unsqueeze(-1) * geographic.unsqueeze(-2)).flatten(-2)


def straight_through_weather(
    member_heads: torch.Tensor,
    generated: torch.Tensor,
    soft_wet: torch.Tensor,
    uniforms: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Use exact Bernoulli forward values and relaxed wet gradients."""
    if soft_wet.shape != member_heads.shape[:-1]:
        raise RuntimeError("relaxed wet field shape drift")
    uniform = uniforms[..., 0].clamp(1.0e-7, 1.0 - 1.0e-7)
    hard_wet = (uniforms[..., 0] < torch.sigmoid(member_heads[..., 0])).to(
        generated.dtype
    )
    logistic_threshold = torch.log(uniform) - torch.log1p(-uniform)
    relaxed_wet = torch.sigmoid(
        (member_heads[..., 0] - logistic_threshold) / 0.5
    )
    wet = relaxed_wet + (hard_wet - relaxed_wet).detach()
    amount_scale = nn.functional.softplus(member_heads[..., 2]) + 1.0e-4
    amount_normal = math.sqrt(2.0) * torch.erfinv(2.0 * uniforms[..., 1] - 1.0)
    amount = torch.exp(member_heads[..., 1] + amount_scale * amount_normal)
    weather = torch.stack(
        (wet * amount, generated[..., 1], generated[..., 2]), dim=-1
    )
    soft_metric_wet = torch.sigmoid((weather[..., 0] - 1.0) / 0.1)
    hard_metric_wet = (weather[..., 0] >= 1.0).to(weather.dtype)
    metric_wet = soft_metric_wet + (hard_metric_wet - soft_metric_wet).detach()
    return weather, metric_wet


class DistributionHeadFactorial(inherited.ContinuousLatentProcess):
    def __init__(self, architecture: str, days: int, contract: dict[str, Any]) -> None:
        if architecture not in CANDIDATES:
            raise RuntimeError("unknown A10M5R14 architecture")
        shape = contract["capacity_shapes"][CAPACITY]
        super().__init__(
            inherited.CANDIDATES[1],
            days,
            int(shape["continuous_medium_state_dim"]),
            int(shape["continuous_slow_state_dim"]),
            int(shape["continuous_context_width"]),
            (14.0, 180.0),
            (180.0, 1460.0),
        )
        self.architecture = architecture
        self.smooth_climatology = architecture in (CANDIDATES[1], CANDIDATES[3])
        self.scale_ou = architecture in (CANDIDATES[2], CANDIDATES[3])
        if self.smooth_climatology:
            self.climatology_heads = nn.Linear(
                20, len(LOCATION_HEAD_INDICES), bias=False
            )
            nn.init.zeros_(self.climatology_heads.weight)
            self.register_buffer("climatology_projection", _projection(LOCATION_HEAD_INDICES))
        if self.scale_ou:
            width = int(shape["continuous_context_width"])
            self.medium_scale_loadings = nn.Linear(
                width, self.medium_dim * len(SCALE_HEAD_INDICES), bias=False
            )
            self.slow_scale_loadings = nn.Linear(
                width, self.slow_dim * len(SCALE_HEAD_INDICES), bias=False
            )
            nn.init.zeros_(self.medium_scale_loadings.weight)
            nn.init.zeros_(self.slow_scale_loadings.weight)
            self.register_buffer("scale_head_projection", _projection(SCALE_HEAD_INDICES))

    def member_heads(self, base_heads, features, regimes, months, years, innovations):
        heads, diagnostics = super().member_heads(
            base_heads, features, regimes, months, years, innovations
        )
        location_offsets = diagnostics.pop("combined_offsets")
        diagnostics["location_ou_offsets"] = location_offsets
        zero = location_offsets.sum() * 0.0
        diagnostics["scale_ou_offsets"] = zero
        diagnostics["climatology_offsets"] = zero
        context = self.context_basis(features[..., (0, 1, 3, 4, 5)].float())
        if self.smooth_climatology:
            basis = smooth_climatology_basis(features)
            climatology = self.climatology_heads(basis)
            heads = heads + climatology.unsqueeze(0) @ self.climatology_projection
            diagnostics["uncentered_smooth_climatology"] = climatology
            diagnostics["climatology_offsets"] = climatology
        if self.scale_ou:
            medium = diagnostics["medium_daily_states"]
            slow = diagnostics["slow_daily_states"]
            medium_loadings = self.medium_scale_loadings(context).view(
                features.shape[0], features.shape[1], self.medium_dim,
                len(SCALE_HEAD_INDICES),
            )
            slow_loadings = self.slow_scale_loadings(context).view(
                features.shape[0], features.shape[1], self.slow_dim,
                len(SCALE_HEAD_INDICES),
            )
            scale = torch.einsum("mbtl,btlo->mbto", medium, medium_loadings)
            scale = scale + torch.einsum("mbtl,btlo->mbto", slow, slow_loadings)
            scale = scale - scale.mean(dim=0, keepdim=True)
            heads = heads + scale @ self.scale_head_projection
            diagnostics["centered_scale_head_offsets"] = scale
            diagnostics["scale_ou_offsets"] = scale
        return heads, diagnostics


def build_candidate(contract: dict[str, Any], candidate: str, days: int | None = None):
    window_days = int(days or contract["calendar"]["representative_window"]["axis_rows"])
    if window_days != 5844:
        raise RuntimeError("A10M5R14 candidate requires a 16-year daily window")
    return DistributionHeadFactorial(candidate, window_days, contract)


def _combined_blocks(
    generated, wet, observed, months, years, valid, *, gradient_surrogate
):
    components = aligned.aligned_components(
        generated, wet, observed, months, years, valid,
        gradient_surrogate=gradient_surrogate,
    )
    groups: dict[str, list[torch.Tensor]] = {}
    for key, value in components.items():
        groups.setdefault(aligned.family_name(key), []).append(value)
    return {
        name: torch.stack(values).mean()
        for name, values in sorted(groups.items())
    }, components


def factorial_regularization(diagnostics: dict[str, torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    """Fixed registry: shared OU states once; absent factorial terms exact zero."""
    expected = {
        "medium_daily_states", "slow_daily_states", "location_ou_offsets",
        "scale_ou_offsets", "climatology_offsets",
    }
    if not expected <= diagnostics.keys():
        raise RuntimeError("factorial regularization registry incomplete")
    stability = (
        diagnostics["medium_daily_states"].square().mean()
        + diagnostics["slow_daily_states"].square().mean()
    )
    size = sum(
        diagnostics[name].square().mean()
        for name in ("location_ou_offsets", "scale_ou_offsets", "climatology_offsets")
    )
    return stability, size


def training_objective(
    member_heads,
    diagnostics,
    generated,
    wet,
    precipitation,
    targets,
    observed,
    months,
    years,
    valid,
    uniforms,
    contract,
    physics,
):
    if physics:
        raise RuntimeError("A10M5R14 keeps solar sealed")
    generated, wet = straight_through_weather(
        member_heads, generated, wet, uniforms
    )
    blocks, components = _combined_blocks(
        generated, wet, observed, months, years, valid,
        gradient_surrogate=True,
    )
    if len(components) != 188 or set(components) != set(aligned.metric_keys()):
        raise RuntimeError("full selector-aligned objective registry drift")
    climate_loss = torch.stack(tuple(components.values())).mean()
    daily = portfolio.member_daily_nll(member_heads, precipitation, targets, valid)
    stability, size = factorial_regularization(diagnostics)
    objective = contract["objective"]
    total = (
        climate_loss
        + float(objective["daily_proper_nll_weight"]) * daily
        + float(objective["latent_stability_weight"]) * stability
        + float(objective["residual_size_and_centering_weight"]) * size
    )
    row = {
        "climate": float(climate_loss.detach().cpu()),
        "daily_proper_nll": float(daily.detach().cpu()),
        "latent_stability": float(stability.detach().cpu()),
        "residual_size": float(size.detach().cpu()),
        "solar_nll": 0.0,
    }
    row["aligned_metric_count"] = 188.0
    row.update({f"aligned_{name}": float(value.detach().cpu()) for name, value in blocks.items()})
    return total, row


def score_candidate(
    model,
    control,
    hidden_size,
    records,
    selections,
    members,
    device,
    output_seed_base,
    innovation_seed_base,
    include_points,
):
    totals: dict[str, float] = {}
    daily_total, metric_total, count = 0.0, 0.0, 0
    support = True
    points = []
    model.eval()
    control.eval()
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            values = portfolio.portfolio_batch(records, subset, device, 1200)
            (
                features, precipitation, targets, observed, station, regimes,
                month_t, year_t, physics, months, years, valid,
            ) = values
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
            wet = (generated[..., 0] >= 1.0).to(generated.dtype)
            daily = portfolio.member_daily_nll(heads, precipitation, targets, valid)
            _, components = _combined_blocks(
                generated, wet, observed, months, years, valid,
                gradient_surrogate=False,
            )
            blocks = {
                name: float(value.detach().cpu())
                for name, value in components.items()
            }
            weight = len(subset)
            count += weight
            daily_total += float(daily.cpu()) * weight
            metric_total += statistics.fmean(
                float(value.detach().cpu()) for value in components.values()
            ) * weight
            for name, value in blocks.items():
                totals[name] = totals.get(name, 0.0) + value * weight
            support = support and bool(
                torch.isfinite(generated).all()
                and (generated[..., 0] >= 0.0).all()
                and (generated[..., 1] >= generated[..., 2]).all()
            )
            if include_points:
                for local, (record_index, window_index) in enumerate(subset):
                    _, point_components = _combined_blocks(
                        generated[:, local : local + 1],
                        wet[:, local : local + 1],
                        observed[local : local + 1],
                        [months[local]], [years[local]], [valid[local]],
                        gradient_surrogate=False,
                    )
                    point_blocks = {
                        name: float(value.detach().cpu())
                        for name, value in point_components.items()
                    }
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
    block_scores = {name: value / count for name, value in sorted(totals.items())}
    result = {
        "block_scores": block_scores,
        "daily_proper_nll": daily_total / count,
        "family_balanced_climate_score": metric_total / count,
        "point_count": count,
        "stochastic_members": members,
        "support": support,
    }
    if include_points:
        result["points"] = points
    return result


def train_candidate(contract, candidate, *args, **kwargs):
    if float(contract["objective"]["daily_proper_nll_weight"]) != 0.0:
        raise RuntimeError("daily NLL must remain diagnostic")
    if float(contract["objective"]["paired_daily_pattern_weight"]) != 0.0:
        raise RuntimeError("paired daily pattern loss must remain zero")
    original_build = inherited.build_candidate
    original_objective = portfolio.training_objective
    original_score = inherited.score_candidate
    inherited.build_candidate = lambda local_contract, local_candidate: build_candidate(
        local_contract, local_candidate
    )
    portfolio.training_objective = training_objective
    inherited.score_candidate = score_candidate
    try:
        model, result = inherited.train_candidate(
            contract, candidate, *args, **kwargs
        )
        adapter_count = sum(parameter.numel() for parameter in model.parameters())
        result["candidate_adapter_parameter_count"] = adapter_count
        result["parameter_count"] = 276927 + adapter_count
        expected = {
            CANDIDATES[0]: 278667,
            CANDIDATES[1]: 278747,
            CANDIDATES[2]: 279819,
            CANDIDATES[3]: 279899,
        }[candidate]
        if result["parameter_count"] != expected:
            raise RuntimeError("trained factorial parameter-count drift")
        return model, result
    finally:
        inherited.build_candidate = original_build
        portfolio.training_objective = original_objective
        inherited.score_candidate = original_score


candidate_innovations = inherited.candidate_innovations


def self_test(device: torch.device) -> None:
    aligned.require_registry(aligned.metric_keys())
    inherited.self_test(device)
    contract = {
        "calendar": {"representative_window": {"axis_rows": 5844}},
        "capacity_shapes": {
            "K2": {
                "continuous_context_width": 32,
                "continuous_medium_state_dim": 8,
                "continuous_slow_state_dim": 4,
            }
        },
    }
    torch.manual_seed(13001)
    models = []
    for candidate in CANDIDATES:
        torch.manual_seed(13001)
        models.append(build_candidate(contract, candidate).to(device))
    base, climatology, scale, both = models
    common = set(base.state_dict())
    for model in models[1:]:
        for name in common:
            if not torch.equal(base.state_dict()[name], model.state_dict()[name]):
                raise RuntimeError("matched common hierarchy initialization drift")
    left = candidate_innovations(base, 2, 3, 13002, device)
    right = candidate_innovations(both, 2, 3, 13002, device)
    if left["slow_daily"].shape != (2, 3, 5844, 4):
        raise RuntimeError("slow innovation shape drift")
    if any(not torch.equal(left[name], right[name]) for name in left):
        raise RuntimeError("candidate innovation fields are not common")
    base_heads = torch.zeros((3, 5844, 15), device=device)
    features = torch.zeros((3, 5844, 6), device=device)
    indices = torch.zeros((3, 5844), dtype=torch.long, device=device)
    outputs = [
        model.member_heads(base_heads, features, indices[:, 0], indices, indices, left)
        for model in models
    ]
    if any(not torch.equal(outputs[0][0], value[0]) for value in outputs[1:]):
        raise RuntimeError("zero-output matched initialization failed")
    if any(model.slow_dim != 4 or model.medium_dim != 8 for model in models):
        raise RuntimeError("factorial arm changed inherited OU dimensions")
    if not (hasattr(climatology, "climatology_heads") and hasattr(scale, "medium_scale_loadings") and hasattr(both, "climatology_heads") and hasattr(both, "medium_scale_loadings")):
        raise RuntimeError("2x2 factorial mechanism registry drift")
    regularizers = [factorial_regularization(value[1]) for value in outputs]
    if any(not torch.equal(regularizers[0][0], value[0]) for value in regularizers[1:]):
        raise RuntimeError("shared OU states were not counted exactly once")
    if any(not torch.equal(regularizers[0][1], value[1]) for value in regularizers[1:]):
        raise RuntimeError("zero initialized factorial penalties are not matched")
    frozen_p2_parameter_count = 276927
    counts = [
        frozen_p2_parameter_count
        + sum(parameter.numel() for parameter in model.parameters())
        for model in models
    ]
    if counts != [278667, 278747, 279819, 279899]:
        raise RuntimeError(f"factorial parameter-count freeze drift: {counts}")
    basis_features = torch.tensor(
        [[[0.6, 0.8, 0.0, 2.0, 3.0, 4.0]]], device=device
    )
    basis = smooth_climatology_basis(basis_features).view(5, 4)
    expected_basis = torch.tensor(
        (1.0, 0.6, 0.8, 0.96, 0.28), device=device
    ).unsqueeze(1) * torch.tensor((1.0, 2.0, 3.0, 4.0), device=device)
    if not torch.allclose(basis, expected_basis):
        raise RuntimeError("literal sin/cos harmonic outer-product basis drift")
    sample_heads = torch.zeros((2, 1, 8, 15), device=device, requires_grad=True)
    sample_weather = torch.ones((2, 1, 8, 3), device=device)
    sample_wet = torch.sigmoid(sample_heads[..., 0])
    sample_uniforms = torch.linspace(0.1, 0.9, 16, device=device).view(2, 1, 8, 1).repeat(1, 1, 1, 3)
    hard_weather, straight_wet = straight_through_weather(
        sample_heads, sample_weather, sample_wet, sample_uniforms
    )
    expected_wet = (hard_weather[..., 0] >= 1.0).to(straight_wet.dtype)
    if not torch.equal(straight_wet, expected_wet):
        raise RuntimeError("wet forward path is not exact realized >=1mm threshold")
    (hard_weather[..., 0].sum() + straight_wet.sum()).backward()
    if sample_heads.grad is None or not bool(torch.isfinite(sample_heads.grad).all()):
        raise RuntimeError("straight-through wet backward path failed")
    print("A10M5R14-CONTINUOUS-CORE-SELF-TEST-PASS")
