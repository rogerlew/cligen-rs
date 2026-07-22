#!/usr/bin/env python3
"""A10M5R15R2 matched external-normal conditioning candidates."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import climate_core as climate
import inherited_continuous_core as inherited
import inherited_r15_distribution_core as r14
import portfolio_core as portfolio
import residual_core as residuals


CANDIDATES = (
    "centered_location_ou_smooth_climatology",
    "normal_conditioned_smooth_climatology",
    "descriptor_anchored_residual",
    "normal_anchored_residual",
)
CAPACITY = "K2"
LOCATION_HEAD_INDICES = (0, 1, 3, 5)
NONLOCATION_HEAD_INDICES = tuple(index for index in range(15) if index not in LOCATION_HEAD_INDICES)
NORMAL_FIELD_COUNT = 36
FULL_STATIC_WIDTH = 4 + NORMAL_FIELD_COUNT
DESCRIPTOR_COLUMNS = tuple(
    seasonal * FULL_STATIC_WIDTH + descriptor
    for seasonal in range(5)
    for descriptor in range(4)
)
EXPECTED_COUNTS = {
    CANDIDATES[0]: 1820,
    CANDIDATES[1]: 2540,
    CANDIDATES[2]: 2040,
    CANDIDATES[3]: 2760,
}
_NORMALS: dict[str, np.ndarray] = {}
_CONDITIONING_IDENTITY: dict[str, Any] = {}
_NORMAL_LOOKUPS = 0
_GENERATION_POINT: str | None = None
_combined_blocks = r14._inherited._combined_blocks


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_conditioning(root: Path) -> None:
    global _CONDITIONING_IDENTITY, _NORMALS
    receipt_path = root / "normal-conditioning-receipt.json"
    index_path = root / "normal-conditioning-index.json"
    archive_path = root / "normal-conditioning.f32le"
    normalizer_path = root / "normalizer.f64le"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not (
        receipt.get("valid") is True
        and receipt.get("candidate_fit_count") == 1200
        and receipt.get("fit_validation_count") == 240
        and receipt.get("temporal_site_count") == 6
        and receipt.get("field_count") == NORMAL_FIELD_COUNT
        and all(receipt.get("gates", {}).values())
        and digest(index_path) == receipt.get("index_sha256")
        and digest(archive_path) == receipt.get("archive_sha256")
        and digest(normalizer_path) == receipt.get("normalizer_payload_sha256")
    ):
        raise RuntimeError("normal-conditioning identity drift")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    point_ids = index.get("point_ids", [])
    roles = index.get("roles", [])
    values = np.fromfile(archive_path, dtype="<f4")
    if len(point_ids) != 1446 or len(roles) != 1446 or values.size != 1446 * NORMAL_FIELD_COUNT:
        raise RuntimeError("normal-conditioning shape drift")
    matrix = values.reshape(1446, NORMAL_FIELD_COUNT)
    if not np.isfinite(matrix).all() or len(set(point_ids)) != 1446:
        raise RuntimeError("normal-conditioning values or roster invalid")
    if CounterLike(roles) != {"candidate_fit": 1200, "fit_validation": 240, "temporal_site": 6}:
        raise RuntimeError("normal-conditioning role roster drift")
    _NORMALS = {point_id: row.copy() for point_id, row in zip(point_ids, matrix)}
    _CONDITIONING_IDENTITY = {
        "archive_sha256": receipt["archive_sha256"],
        "bundle_id": receipt.get("bundle_id", "prism-norm91m-monthly-ppt-tmax-tmin"),
        "field_count": NORMAL_FIELD_COUNT,
        "index_sha256": receipt["index_sha256"],
        "normalizer_sha256": receipt["normalizer_payload_sha256"],
        "receipt_sha256": digest(receipt_path),
        "window_limitation": (
            "PRISM Norm91m 1991-2020 monthly normals are fixed climatological "
            "conditioning covariates and do not represent conditions outside that window."
        ),
    }


def CounterLike(values: list[str]) -> dict[str, int]:
    output: dict[str, int] = {}
    for value in values:
        output[value] = output.get(value, 0) + 1
    return output


def set_generation_point(point_id: str | None) -> None:
    global _GENERATION_POINT
    _GENERATION_POINT = None if point_id is None else f"temporal/{point_id}"


def _augment_generation(features: torch.Tensor) -> torch.Tensor:
    global _NORMAL_LOOKUPS
    if features.shape[-1] == 6:
        if _GENERATION_POINT is None or _GENERATION_POINT not in _NORMALS:
            raise RuntimeError("temporal normal conditioning was not selected")
        _NORMAL_LOOKUPS += 1
        normal = torch.from_numpy(_NORMALS[_GENERATION_POINT]).to(
            device=features.device, dtype=torch.float32
        )
        expanded = normal.view(1, 1, -1).expand(features.shape[0], features.shape[1], -1)
        return torch.cat((features, expanded), dim=-1)
    if features.shape[-1] != 6 + NORMAL_FIELD_COUNT:
        raise RuntimeError("conditioned feature width drift")
    return features


def condition_generation_features(features: torch.Tensor) -> torch.Tensor:
    """Materialize immutable site normals before a warm-generation timer."""
    return _augment_generation(features)


def _conditioned_batch(original, records, selections, device, validation_index):
    global _NORMAL_LOOKUPS
    values = list(original(records, selections, device, validation_index))
    physics = values[8]
    if physics.shape[-1] == 6 + NORMAL_FIELD_COUNT:
        return tuple(values)
    if physics.shape[-1] != 6:
        raise RuntimeError("portfolio conditioning width drift")
    normals = []
    for record_index, _ in selections:
        point_id = records[record_index].record.point_id
        if point_id not in _NORMALS:
            raise RuntimeError(f"normal conditioning missing for {point_id}")
        _NORMAL_LOOKUPS += 1
        normals.append(_NORMALS[point_id])
    tensor = torch.from_numpy(np.stack(normals)).to(device=device, dtype=torch.float32)
    tensor = tensor.unsqueeze(1).expand(-1, physics.shape[1], -1)
    values[8] = torch.cat((physics, tensor), dim=-1)
    return tuple(values)


def _projection(indices: tuple[int, ...]) -> torch.Tensor:
    value = torch.zeros((len(indices), 15))
    for row, column in enumerate(indices):
        value[row, column] = 1.0
    return value


def _seasonal(features: torch.Tensor) -> torch.Tensor:
    sine, cosine = features[..., 0].float(), features[..., 1].float()
    return torch.stack(
        (
            torch.ones_like(sine),
            sine,
            cosine,
            2.0 * sine * cosine,
            cosine.square() - sine.square(),
        ),
        dim=-1,
    )


def descriptor_basis(features: torch.Tensor) -> torch.Tensor:
    if features.shape[-1] not in (6, 6 + NORMAL_FIELD_COUNT):
        raise RuntimeError("descriptor feature width drift")
    geographic = torch.stack(
        (
            torch.ones_like(features[..., 0]),
            features[..., 3].float(),
            features[..., 4].float(),
            features[..., 5].float(),
        ),
        dim=-1,
    )
    return (_seasonal(features).unsqueeze(-1) * geographic.unsqueeze(-2)).flatten(-2)


def normal_only_basis(features: torch.Tensor) -> torch.Tensor:
    features = _augment_generation(features)
    return (
        _seasonal(features).unsqueeze(-1) * features[..., 6:].float().unsqueeze(-2)
    ).flatten(-2)


def full_conditioned_basis(features: torch.Tensor) -> torch.Tensor:
    features = _augment_generation(features)
    static = torch.cat(
        (
            torch.ones_like(features[..., :1]),
            features[..., 3:6].float(),
            features[..., 6:].float(),
        ),
        dim=-1,
    )
    return (_seasonal(features).unsqueeze(-1) * static.unsqueeze(-2)).flatten(-2)


class AdapterPair(r14.DistributionHeadFactorial):
    uses_p2 = True

    def __init__(self, candidate: str, days: int, contract: dict[str, Any]) -> None:
        super().__init__(
            r14.CANDIDATES[1] if candidate == CANDIDATES[0] else r14.CANDIDATES[0],
            days,
            contract,
        )
        self.candidate = candidate
        self.uses_normals = candidate == CANDIDATES[1]
        if self.uses_normals:
            self.climatology_heads = nn.Linear(200, len(LOCATION_HEAD_INDICES), bias=False)
            nn.init.zeros_(self.climatology_heads.weight)
            self.register_buffer("climatology_projection", _projection(LOCATION_HEAD_INDICES))

    def member_heads(self, base_heads, features, regimes, months, years, innovations):
        if self.uses_normals:
            conditioned = _augment_generation(features)
        else:
            if features.shape[-1] != 6:
                raise RuntimeError("E0 must receive descriptor-only features")
            conditioned = features
        heads, diagnostics = super().member_heads(
            base_heads, conditioned[..., :6], regimes, months, years, innovations
        )
        if self.uses_normals:
            climatology = self.climatology_heads(full_conditioned_basis(conditioned))
            heads = heads + climatology.unsqueeze(0) @ self.climatology_projection
            diagnostics["normal_climatology_offsets"] = climatology
            diagnostics["climatology_offsets"] = climatology
        else:
            diagnostics["normal_climatology_offsets"] = heads.sum() * 0.0
        return heads, diagnostics


class ReplacementPair(inherited.ContinuousLatentProcess):
    uses_p2 = False

    def __init__(self, candidate: str, days: int, contract: dict[str, Any]) -> None:
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
        self.candidate = candidate
        self.uses_normals = candidate == CANDIDATES[3]
        common = nn.Linear(20, 15, bias=False)
        if not self.uses_normals:
            self.descriptor_baseline = common
        else:
            self.nonlocation_baseline = nn.Linear(20, len(NONLOCATION_HEAD_INDICES), bias=False)
            self.location_baseline = nn.Linear(200, len(LOCATION_HEAD_INDICES), bias=False)
            with torch.no_grad():
                self.nonlocation_baseline.weight.copy_(common.weight[list(NONLOCATION_HEAD_INDICES)])
                self.location_baseline.weight.zero_()
                self.location_baseline.weight[:, list(DESCRIPTOR_COLUMNS)].copy_(
                    common.weight[list(LOCATION_HEAD_INDICES)]
                )
            self.register_buffer("nonlocation_projection", _projection(NONLOCATION_HEAD_INDICES))
            self.register_buffer("location_projection", _projection(LOCATION_HEAD_INDICES))

    def member_heads(self, base_heads, features, regimes, months, years, innovations):
        del base_heads
        if self.uses_normals:
            conditioned = _augment_generation(features)
        else:
            if features.shape[-1] != 6:
                raise RuntimeError("E2C must receive descriptor-only features")
            conditioned = features
        zeros = torch.zeros((*conditioned.shape[:-1], 15), device=conditioned.device)
        residual, diagnostics = super().member_heads(
            zeros, conditioned[..., :6], regimes, months, years, innovations
        )
        descriptor = descriptor_basis(conditioned)
        if self.uses_normals:
            baseline = self.nonlocation_baseline(descriptor) @ self.nonlocation_projection
            baseline = baseline + self.location_baseline(full_conditioned_basis(conditioned)) @ self.location_projection
        else:
            baseline = self.descriptor_baseline(descriptor)
        heads = baseline.unsqueeze(0) + residual
        location = diagnostics.pop("combined_offsets")
        zero = location.sum() * 0.0
        diagnostics.update(
            {
                "climatology_offsets": baseline,
                "location_ou_offsets": location,
                "normal_climatology_offsets": zero,
                "scale_ou_offsets": zero,
            }
        )
        return heads, diagnostics


class PortableCandidateExport(nn.Module):
    """Portable CPU inference surface for one fitted rev-2 candidate."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(
        self,
        base_heads: torch.Tensor,
        features: torch.Tensor,
        medium_daily: torch.Tensor,
        slow_daily: torch.Tensor,
    ) -> torch.Tensor:
        indices = torch.zeros(
            (features.shape[0], features.shape[1]),
            dtype=torch.long,
            device=features.device,
        )
        heads, _ = self.model.member_heads(
            base_heads,
            features,
            indices[:, 0],
            indices,
            indices,
            {"medium_daily": medium_daily, "slow_daily": slow_daily},
        )
        return heads


def portable_stationary_ou_states(
    innovations: torch.Tensor,
    raw_time_scales: torch.Tensor,
    lower_days: float,
    upper_days: float,
    steps: int,
    fft_size: int,
) -> torch.Tensor:
    """Trace-safe prefix-stable OU transform for one frozen horizon."""
    del fft_size
    time_scales = inherited.bounded_time_scales(
        raw_time_scales, lower_days, upper_days
    )
    rho = torch.exp(-1.0 / time_scales)
    innovation_scale = torch.sqrt((1.0 - rho.square()).clamp_min(1e-7))
    states = torch.cat(
        (innovations[:, :, :1], innovations[:, :, 1:] * innovation_scale), dim=2
    )
    offset = 1
    while offset < steps:
        states = torch.cat(
            (
                states[:, :, :offset],
                states[:, :, offset:] + states[:, :, :-offset] * rho.pow(offset),
            ),
            dim=2,
        )
        offset *= 2
    return states


def build_candidate(
    contract: dict[str, Any],
    candidate: str,
    days: int | None = None,
    *,
    generation: bool = False,
):
    if candidate not in CANDIDATES:
        raise RuntimeError("unknown A10M5R15 candidate")
    window_days = int(days or contract["calendar"]["representative_window"]["axis_rows"])
    if (not generation and window_days != 5844) or (generation and window_days <= 0):
        raise RuntimeError("A10M5R15 requires a 16-year daily window")
    model = (
        AdapterPair(candidate, window_days, contract)
        if candidate in CANDIDATES[:2]
        else ReplacementPair(candidate, window_days, contract)
    )
    count = sum(parameter.numel() for parameter in model.parameters())
    if count != EXPECTED_COUNTS[candidate]:
        raise RuntimeError(f"A10M5R15 parameter-count drift: {candidate}/{count}")
    return model


def training_objective(*args, **kwargs):
    return r14.training_objective(*args, **kwargs)


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
    support, points = True, []
    model.eval()
    if control is not None:
        control.eval()
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            active_batch = portfolio.portfolio_batch
            values = (
                _conditioned_batch(active_batch, records, subset, device, 1200)
                if model.uses_normals
                else active_batch(records, subset, device, 1200)
            )
            features, precipitation, targets, observed, station, regimes, month_t, year_t, physics, months, years, valid = values
            base = portfolio.forward_control(control, features, station, hidden_size) if model.uses_p2 else None
            innovations = candidate_innovations(model, members, len(subset), innovation_seed_base + offset, device)
            heads, _ = model.member_heads(base, physics, regimes, month_t, year_t, innovations)
            uniforms = climate.member_uniforms(members, len(subset), heads.shape[2], output_seed_base + offset, device)
            generated, wet = residuals.sample_member_weather(heads, uniforms, None)
            wet = (generated[..., 0] >= 1.0).to(generated.dtype)
            daily = portfolio.member_daily_nll(heads, precipitation, targets, valid)
            _, components = _combined_blocks(generated, wet, observed, months, years, valid, gradient_surrogate=False)
            weight = len(subset)
            count += weight
            daily_total += float(daily.cpu()) * weight
            metric_total += statistics.fmean(float(value.cpu()) for value in components.values()) * weight
            for name, value in components.items():
                totals[name] = totals.get(name, 0.0) + float(value.cpu()) * weight
            support = support and bool(torch.isfinite(generated).all() and (generated[..., 0] >= 0).all() and (generated[..., 1] >= generated[..., 2]).all())
            if include_points:
                for local, (record_index, window_index) in enumerate(subset):
                    _, point_components = _combined_blocks(
                        generated[:, local : local + 1], wet[:, local : local + 1],
                        observed[local : local + 1], [months[local]], [years[local]],
                        [valid[local]], gradient_surrogate=False,
                    )
                    points.append(
                        {
                            "block_scores": {name: float(value.cpu()) for name, value in point_components.items()},
                            "daily_proper_nll": float(portfolio.member_daily_nll(heads[:, local : local + 1], precipitation[local : local + 1], targets[local : local + 1], [valid[local]]).cpu()),
                            "point_id": records[record_index].record.point_id,
                            "window_first_year": records[record_index].windows[window_index].first_year,
                        }
                    )
    result = {
        "block_scores": {name: value / count for name, value in sorted(totals.items())},
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
    uses_normals = candidate in (CANDIDATES[1], CANDIDATES[3])
    if uses_normals and not _NORMALS:
        raise RuntimeError("normal conditioning must be authenticated before training")
    original_build = inherited.build_candidate
    original_objective = portfolio.training_objective
    original_score = inherited.score_candidate
    original_batch = portfolio.portfolio_batch
    original_forward = portfolio.forward_control
    replacement = candidate in CANDIDATES[2:]
    inherited.build_candidate = lambda local_contract, local_candidate: build_candidate(local_contract, local_candidate)
    portfolio.training_objective = training_objective
    inherited.score_candidate = score_candidate
    if uses_normals:
        portfolio.portfolio_batch = lambda records, selections, device, validation_index: _conditioned_batch(original_batch, records, selections, device, validation_index)
    if replacement:
        portfolio.forward_control = lambda control, features, station, hidden_size: None
    try:
        model, result = inherited.train_candidate(contract, candidate, *args, **kwargs)
        model_count = sum(parameter.numel() for parameter in model.parameters())
        result["candidate_adapter_parameter_count"] = model_count
        result["parameter_count"] = model_count
        result["total_parameter_count"] = model_count + (276927 if model.uses_p2 else 0)
        result["parameter_accounting_interface"] = "adapter-only-parameter_count-plus-explicit-total"
        return model, result
    finally:
        inherited.build_candidate = original_build
        portfolio.training_objective = original_objective
        inherited.score_candidate = original_score
        portfolio.portfolio_batch = original_batch
        portfolio.forward_control = original_forward


candidate_innovations = inherited.candidate_innovations


def self_test(device: torch.device) -> None:
    contract = {
        "calendar": {"representative_window": {"axis_rows": 5844}},
        "capacity_shapes": {"K2": {"continuous_context_width": 32, "continuous_medium_state_dim": 8, "continuous_slow_state_dim": 4}},
    }
    global _GENERATION_POINT
    global _NORMAL_LOOKUPS
    models = []
    for candidate in CANDIDATES:
        torch.manual_seed(15021)
        models.append(build_candidate(contract, candidate).to(device))
    e0, e1, e2c, e2 = models
    features = torch.zeros((1, 5844, 6), device=device)
    before_controls = _NORMAL_LOOKUPS
    descriptor_basis(features)
    if _NORMAL_LOOKUPS != before_controls:
        raise RuntimeError("descriptor-only basis requested normals")
    if _NORMALS:
        _GENERATION_POINT = next(iter(_NORMALS))
        augmented = _augment_generation(features)
    else:
        augmented = torch.zeros((1, 5844, 6 + NORMAL_FIELD_COUNT), device=device)
    for control in (e0, e2c):
        try:
            control.member_heads(None, augmented, None, None, None, None)
        except RuntimeError as error:
            if "descriptor-only features" not in str(error):
                raise
        else:
            raise RuntimeError("descriptor-only control accepted conditioned tensors")
    if augmented.shape[-1] != 42 or descriptor_basis(augmented).shape[-1] != 20 or full_conditioned_basis(augmented).shape[-1] != 200:
        raise RuntimeError("conditioning basis shape drift")
    perturbed = augmented.clone()
    perturbed[..., 6:] += 7.0
    if not torch.equal(descriptor_basis(augmented), descriptor_basis(perturbed)):
        raise RuntimeError("E0/E2C descriptor basis consumed normals")
    if torch.equal(normal_only_basis(augmented), normal_only_basis(perturbed)):
        raise RuntimeError("E1/E2 normal basis did not consume normals")
    if not torch.equal(e0.climatology_heads.weight, e1.climatology_heads.weight[:, list(DESCRIPTOR_COLUMNS)]) or torch.count_nonzero(e1.climatology_heads.weight):
        raise RuntimeError("E0/E1 matched initialization drift")
    if not torch.equal(e2c.descriptor_baseline.weight[list(NONLOCATION_HEAD_INDICES)], e2.nonlocation_baseline.weight):
        raise RuntimeError("E2C/E2 non-location initialization drift")
    normal_columns = [index for index in range(200) if index not in DESCRIPTOR_COLUMNS]
    if not torch.equal(e2c.descriptor_baseline.weight[list(LOCATION_HEAD_INDICES)], e2.location_baseline.weight[:, list(DESCRIPTOR_COLUMNS)]) or torch.count_nonzero(e2.location_baseline.weight[:, normal_columns]):
        raise RuntimeError("E2C/E2 location initialization drift")
    if [sum(parameter.numel() for parameter in model.parameters()) for model in models] != [1820, 2540, 2040, 2760]:
        raise RuntimeError("candidate parameter counts drift")
    _GENERATION_POINT = None
    print("A10M5R15R2-CONTINUOUS-CORE-SELF-TEST-PASS")
