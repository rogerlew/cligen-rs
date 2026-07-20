#!/usr/bin/env python3
"""Selector-aligned long-horizon continuous hierarchy candidates."""

from __future__ import annotations

import statistics
from typing import Any

import torch
from torch import nn

import climate_core as climate
import inherited_continuous_core as inherited
import portfolio_core as portfolio
import residual_core as residuals
import selector_loss as selector
from selector_loss import (
    FAMILY_KEYS,
    component_scalars,
    selector_aligned_annual_components,
    selector_aligned_annual_loss,
)

CANDIDATES = (
    "selector_aligned_continuous_hierarchy",
    "selector_aligned_shared_slow_climate_state",
)
CAPACITY = "K2"


class SelectorAlignedHierarchy(inherited.ContinuousLatentProcess):
    def __init__(self, architecture: str, days: int, contract: dict[str, Any]) -> None:
        if architecture not in CANDIDATES:
            raise RuntimeError("unknown A10M5R13 architecture")
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
        self.explicit_shared = architecture == CANDIDATES[1]
        # Both arms start with factor zero silent, so their initial outputs and
        # all common parameters match. The base may learn four flexible head
        # loadings. The shared arm uses only row zero as a scalar loading and
        # the four-element field vector below: a rank-one decoding, not a
        # fifth stochastic state.
        with torch.no_grad():
            self.slow_loadings.weight[: len(inherited.CORE_HEAD_INDICES)].zero_()
        if self.explicit_shared:
            self.shared_field_vector = nn.Parameter(
                torch.ones(len(inherited.CORE_HEAD_INDICES))
            )

    def member_heads(self, base_heads, features, regimes, months, years, innovations):
        heads, diagnostics = super().member_heads(
            base_heads, features, regimes, months, years, innovations
        )
        if not self.explicit_shared:
            return heads, diagnostics
        slow = diagnostics["slow_daily_states"]
        context = self.context_basis(features[..., (0, 1, 3, 4, 5)].float())
        all_loadings = self.slow_loadings(context).view(
            features.shape[0],
            features.shape[1],
            self.slow_dim,
            len(inherited.CORE_HEAD_INDICES),
        )
        original = (
            slow[..., :1].unsqueeze(-1)
            * all_loadings[:, :, :1, :].unsqueeze(0)
        )
        original = original.sum(dim=-2)
        scalar_loading = all_loadings[:, :, 0, 0]
        shared = (
            slow[..., 0].unsqueeze(-1)
            * scalar_loading.unsqueeze(0).unsqueeze(-1)
            * self.shared_field_vector
        )
        original = original - original.mean(dim=0, keepdim=True)
        shared = shared - shared.mean(dim=0, keepdim=True)
        heads = heads + (shared - original) @ self.head_projection
        diagnostics["combined_offsets"] = (
            diagnostics["combined_offsets"] + shared - original
        )
        diagnostics["explicit_shared_slow_climate_state"] = slow[..., 0]
        diagnostics["explicit_shared_slow_adjustment"] = shared
        diagnostics["flexible_slow_daily_state"] = slow[..., 1:]
        return heads, diagnostics


def build_candidate(contract: dict[str, Any], candidate: str, days: int | None = None):
    window_days = int(days or contract["calendar"]["representative_window"]["axis_rows"])
    if window_days != 5844:
        raise RuntimeError("A10M5R13 candidate requires a 16-year daily window")
    return SelectorAlignedHierarchy(candidate, window_days, contract)


def _combined_blocks(generated, wet, observed, months, years, valid, *, squared):
    _, inherited_blocks = climate.climate_components(
        generated, wet, observed, months, years, valid, squared=squared
    )
    # Replace rather than duplicate the inherited annual location/dispersion.
    inherited_blocks.pop("annual_location")
    inherited_blocks.pop("annual_interannual_dispersion")
    inherited_blocks.update(
        selector_aligned_annual_components(
            generated, observed, years, valid, squared=squared
        )
    )
    return inherited_blocks


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
        raise RuntimeError("A10M5R13 keeps solar sealed")
    blocks = _combined_blocks(
        generated, wet, observed, months, years, valid, squared=True
    )
    weights = contract["objective"]["climate_blocks"]
    if set(weights) != set(blocks) or any(float(weights[name]) != 1.0 for name in FAMILY_KEYS):
        raise RuntimeError("selector-aligned climate block registry drift")
    denominator = sum(float(value) for value in weights.values())
    climate_loss = sum(
        float(weights[name]) * value for name, value in blocks.items()
    ) / denominator
    daily = portfolio.member_daily_nll(member_heads, precipitation, targets, valid)
    stability, size = portfolio.regularization(diagnostics)
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
    row.update(component_scalars({name: blocks[name] for name in FAMILY_KEYS}))
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
    daily_total, count = 0.0, 0
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
            daily = portfolio.member_daily_nll(heads, precipitation, targets, valid)
            blocks = {
                name: float(value.detach().cpu())
                for name, value in _combined_blocks(
                    generated, wet, observed, months, years, valid, squared=False
                ).items()
            }
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
                    point_blocks = {
                        name: float(value.detach().cpu())
                        for name, value in _combined_blocks(
                            generated[:, local : local + 1],
                            wet[:, local : local + 1],
                            observed[local : local + 1],
                            [months[local]], [years[local]], [valid[local]],
                            squared=False,
                        ).items()
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
        "family_balanced_climate_score": statistics.fmean(block_scores.values()),
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
        return inherited.train_candidate(contract, candidate, *args, **kwargs)
    finally:
        inherited.build_candidate = original_build
        portfolio.training_objective = original_objective
        inherited.score_candidate = original_score


candidate_innovations = inherited.candidate_innovations


def self_test(device: torch.device) -> None:
    selector.self_test()
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
    base = build_candidate(contract, CANDIDATES[0]).to(device)
    torch.manual_seed(13001)
    shared = build_candidate(contract, CANDIDATES[1]).to(device)
    for name, value in base.state_dict().items():
        if not torch.equal(value, shared.state_dict()[name]):
            raise RuntimeError("matched common hierarchy initialization drift")
    if sum(p.numel() for p in shared.parameters()) - sum(p.numel() for p in base.parameters()) != 4:
        raise RuntimeError("shared arm must add only its four-element field vector")
    left = candidate_innovations(base, 2, 3, 13002, device)
    right = candidate_innovations(shared, 2, 3, 13002, device)
    if left["slow_daily"].shape != (2, 3, 5844, 4):
        raise RuntimeError("slow innovation shape drift")
    if any(not torch.equal(left[name], right[name]) for name in left):
        raise RuntimeError("candidate innovation fields are not common")
    base_heads = torch.zeros((3, 5844, 15), device=device)
    features = torch.zeros((3, 5844, 6), device=device)
    indices = torch.zeros((3, 5844), dtype=torch.long, device=device)
    base_output, base_diagnostics = base.member_heads(base_heads, features, indices[:, 0], indices, indices, left)
    shared_output, shared_diagnostics = shared.member_heads(base_heads, features, indices[:, 0], indices + 1, indices + 9, right)
    if not torch.equal(base_output, shared_output):
        raise RuntimeError("zero-output matched initialization failed")
    if base.slow_dim != shared.slow_dim or shared.slow_dim != 4:
        raise RuntimeError("shared arm changed the inherited slow state count")
    base_regularizers = portfolio.regularization(base_diagnostics)
    shared_regularizers = portfolio.regularization(shared_diagnostics)
    if any(not torch.equal(left_value, right_value) for left_value, right_value in zip(base_regularizers, shared_regularizers)):
        raise RuntimeError("zero-output matched regularization failed")
    print("A10M5R13-CONTINUOUS-CORE-SELF-TEST-PASS")
