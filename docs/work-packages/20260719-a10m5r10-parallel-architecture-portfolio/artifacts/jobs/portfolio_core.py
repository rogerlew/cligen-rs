#!/usr/bin/env python3
"""Shared science engine for the A10M5R10 architecture portfolio."""

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
import residual_core as residuals

CANDIDATES = (
    "monthly_residual_adapter",
    "annual_monthly_residual_adapter",
    "hierarchical_joint_factor_adapter",
    "climate_normal_hierarchical_state_space",
    "physics_conditioned_hierarchical_adapter",
)
CAPACITIES = ("K1", "K2")
SEEDS = (147031, 271828, 314159)
CORE_HEAD_INDICES = (0, 1, 3, 5)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, allow_nan=False, indent=2, sort_keys=True)
        stream.write("\n")
    partial.replace(path)
    if path.stat().st_size >= 10_000_000:
        raise RuntimeError(f"JSON publication exceeds 10 MB: {path}")


def require_l40() -> torch.device:
    if (
        not torch.cuda.is_available()
        or torch.cuda.device_count() != 1
        or "L40" not in torch.cuda.get_device_name(0)
    ):
        raise RuntimeError("exactly one typed L40 is required")
    return torch.device("cuda:0")


def model_state_sha256(model: nn.Module) -> str:
    value = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        value.update(name.encode("utf-8"))
        value.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return value.hexdigest()


def projection(indices: tuple[int, ...]) -> torch.Tensor:
    value = torch.zeros((len(indices), 15))
    for row, column in enumerate(indices):
        value[row, column] = 1.0
    return value


def stationary_ar_states(
    innovations: torch.Tensor,
    raw_persistence: torch.Tensor,
    maximum_persistence: float,
) -> torch.Tensor:
    """Return stationary unit-variance AR(1) states without a zero-state warmup."""
    if innovations.ndim != 4 or innovations.shape[2] < 1:
        raise RuntimeError("AR innovations must have shape [members,batch,cells,latent]")
    persistence = maximum_persistence * torch.sigmoid(raw_persistence)
    persistence = persistence.view(1, 1, -1)
    innovation_scale = torch.sqrt((1.0 - persistence.square()).clamp_min(1e-6))
    state = innovations[:, :, 0]
    values = [state]
    for index in range(1, innovations.shape[2]):
        state = persistence * state + innovation_scale * innovations[:, :, index]
        values.append(state)
    return torch.stack(values, dim=2)


def annual_conditioned_monthly_states(
    innovations: torch.Tensor,
    raw_monthly_persistence: torch.Tensor,
    maximum_persistence: float,
    annual_states: torch.Tensor,
    conditioner: nn.Module,
) -> torch.Tensor:
    """AR(1) monthly states whose transition mean is set by the annual state."""
    if innovations.shape[2] != 12 * annual_states.shape[2]:
        raise RuntimeError("annual/monthly state grids do not align")
    persistence = maximum_persistence * torch.sigmoid(raw_monthly_persistence)
    persistence = persistence.view(1, 1, -1)
    innovation_scale = torch.sqrt((1.0 - persistence.square()).clamp_min(1e-6))
    annual_daily = annual_states.repeat_interleave(12, dim=2)
    condition = conditioner(annual_daily)
    state = innovations[:, :, 0] + condition[:, :, 0]
    values = [state]
    for index in range(1, innovations.shape[2]):
        state = (
            persistence * state
            + innovation_scale * innovations[:, :, index]
            + (1.0 - persistence) * condition[:, :, index]
        )
        values.append(state)
    return torch.stack(values, dim=2)


def raw_persistence(latent_dim: int, maximum_persistence: float) -> nn.Parameter:
    values = torch.linspace(0.25, 0.95, latent_dim)
    ratio = (values / maximum_persistence).clamp(1e-5, 1.0 - 1e-5)
    return nn.Parameter(torch.logit(ratio))


def centered(values: torch.Tensor) -> torch.Tensor:
    return values - values.mean(dim=0, keepdim=True)


def gather_cells(states: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
    members, batch, _, latent = states.shape
    gather = indices.unsqueeze(0).unsqueeze(-1).expand(members, batch, -1, latent)
    return states.gather(2, gather)


class PortfolioCandidate(nn.Module):
    """Common member-head interface for all portfolio candidates."""

    uses_control = True

    def member_heads(
        self,
        base_heads: torch.Tensor | None,
        features: torch.Tensor,
        regimes: torch.Tensor,
        months: torch.Tensor,
        years: torch.Tensor,
        innovations: dict[str, torch.Tensor],
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        raise NotImplementedError

    def innovation_shapes(self) -> dict[str, tuple[int, int]]:
        raise NotImplementedError

    def persistence_values(self) -> dict[str, list[float]]:
        return {}


class MonthlyResidualAdapter(PortfolioCandidate):
    def __init__(self, latent_dim: int, maximum_persistence: float) -> None:
        super().__init__()
        self.raw_monthly_persistence = raw_persistence(latent_dim, maximum_persistence)
        self.decoder = nn.Linear(latent_dim, len(CORE_HEAD_INDICES), bias=False)
        nn.init.normal_(self.decoder.weight, mean=0.0, std=0.02)
        self.register_buffer("head_projection", projection(CORE_HEAD_INDICES))
        self.latent_dim = latent_dim
        self.maximum_persistence = maximum_persistence

    def innovation_shapes(self) -> dict[str, tuple[int, int]]:
        return {"monthly": (96, self.latent_dim)}

    def member_heads(self, base_heads: torch.Tensor | None, features: torch.Tensor,
                     regimes: torch.Tensor, months: torch.Tensor, years: torch.Tensor,
                     innovations: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        del features, regimes
        if base_heads is None:
            raise RuntimeError("monthly adapter requires a frozen control")
        states = stationary_ar_states(
            innovations["monthly"], self.raw_monthly_persistence, self.maximum_persistence
        )
        decoded = centered(self.decoder(gather_cells(states, years * 12 + months)))
        heads = base_heads.float().unsqueeze(0) + decoded @ self.head_projection
        return heads, {"monthly_offsets": decoded, "monthly_states": states}

    def persistence_values(self) -> dict[str, list[float]]:
        values = self.maximum_persistence * torch.sigmoid(self.raw_monthly_persistence)
        return {"monthly": [float(value) for value in values.detach().cpu()]}


class AnnualMonthlyResidualAdapter(PortfolioCandidate):
    def __init__(self, annual_dim: int, monthly_dim: int, maximum_persistence: float) -> None:
        super().__init__()
        self.raw_annual_persistence = raw_persistence(annual_dim, maximum_persistence)
        self.raw_monthly_persistence = raw_persistence(monthly_dim, maximum_persistence)
        self.annual_decoder = nn.Linear(annual_dim, len(CORE_HEAD_INDICES), bias=False)
        self.annual_conditioner = nn.Linear(annual_dim, monthly_dim, bias=False)
        self.monthly_decoder = nn.Linear(
            annual_dim + monthly_dim, len(CORE_HEAD_INDICES), bias=False
        )
        nn.init.normal_(self.annual_decoder.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.annual_conditioner.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.monthly_decoder.weight, mean=0.0, std=0.02)
        self.register_buffer("head_projection", projection(CORE_HEAD_INDICES))
        self.annual_dim = annual_dim
        self.monthly_dim = monthly_dim
        self.maximum_persistence = maximum_persistence

    def innovation_shapes(self) -> dict[str, tuple[int, int]]:
        return {"annual": (8, self.annual_dim), "monthly": (96, self.monthly_dim)}

    def decoded_offsets(
        self, months: torch.Tensor, years: torch.Tensor, innovations: dict[str, torch.Tensor]
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        annual_states = stationary_ar_states(
            innovations["annual"], self.raw_annual_persistence, self.maximum_persistence
        )
        monthly_states = annual_conditioned_monthly_states(
            innovations["monthly"], self.raw_monthly_persistence,
            self.maximum_persistence, annual_states, self.annual_conditioner,
        )
        annual_features = gather_cells(annual_states, years)
        monthly_features = gather_cells(monthly_states, years * 12 + months)
        annual = self.annual_decoder(annual_features)
        monthly = self.monthly_decoder(torch.cat((annual_features, monthly_features), dim=-1))
        decoded = centered(annual + monthly)
        return decoded, {
            "annual_offsets": centered(annual),
            "annual_states": annual_states,
            "monthly_offsets": centered(monthly),
            "monthly_states": monthly_states,
        }

    def member_heads(self, base_heads: torch.Tensor | None, features: torch.Tensor,
                     regimes: torch.Tensor, months: torch.Tensor, years: torch.Tensor,
                     innovations: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        del features, regimes
        if base_heads is None:
            raise RuntimeError("hierarchical adapter requires a frozen control")
        decoded, diagnostics = self.decoded_offsets(months, years, innovations)
        heads = base_heads.float().unsqueeze(0) + decoded @ self.head_projection
        diagnostics["combined_offsets"] = decoded
        return heads, diagnostics

    def persistence_values(self) -> dict[str, list[float]]:
        annual = self.maximum_persistence * torch.sigmoid(self.raw_annual_persistence)
        monthly = self.maximum_persistence * torch.sigmoid(self.raw_monthly_persistence)
        return {
            "annual": [float(value) for value in annual.detach().cpu()],
            "monthly": [float(value) for value in monthly.detach().cpu()],
        }


class HierarchicalJointFactorAdapter(PortfolioCandidate):
    """Annual context plus shared and field-specific monthly factors."""

    def __init__(self, annual_dim: int, shared_dim: int, field_dim: int,
                 decoder_width: int, maximum_persistence: float) -> None:
        super().__init__()
        self.annual_dim = annual_dim
        self.shared_dim = shared_dim
        self.field_dim = field_dim
        self.maximum_persistence = maximum_persistence
        self.raw_annual_persistence = raw_persistence(annual_dim, maximum_persistence)
        self.raw_shared_persistence = raw_persistence(shared_dim, maximum_persistence)
        self.raw_precip_persistence = raw_persistence(field_dim, maximum_persistence)
        self.raw_temperature_persistence = raw_persistence(field_dim, maximum_persistence)
        self.shared_conditioner = nn.Linear(annual_dim, shared_dim, bias=False)
        self.precip_conditioner = nn.Linear(annual_dim, field_dim, bias=False)
        self.temperature_conditioner = nn.Linear(annual_dim, field_dim, bias=False)
        total = annual_dim + shared_dim + 2 * field_dim
        self.decoder = nn.Sequential(
            nn.Linear(total, decoder_width), nn.Tanh(), nn.Linear(decoder_width, len(CORE_HEAD_INDICES))
        )
        nn.init.zeros_(self.decoder[-1].bias)
        nn.init.normal_(self.decoder[-1].weight, mean=0.0, std=0.01)
        self.register_buffer("head_projection", projection(CORE_HEAD_INDICES))

    def innovation_shapes(self) -> dict[str, tuple[int, int]]:
        return {
            "annual": (8, self.annual_dim),
            "shared_monthly": (96, self.shared_dim),
            "precip_monthly": (96, self.field_dim),
            "temperature_monthly": (96, self.field_dim),
        }

    def member_heads(self, base_heads: torch.Tensor | None, features: torch.Tensor,
                     regimes: torch.Tensor, months: torch.Tensor, years: torch.Tensor,
                     innovations: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        del features, regimes
        if base_heads is None:
            raise RuntimeError("joint factor adapter requires a frozen control")
        annual_states = stationary_ar_states(
            innovations["annual"], self.raw_annual_persistence, self.maximum_persistence
        )
        gathered = [gather_cells(annual_states, years)]
        diagnostics = {"annual_states": annual_states}
        definitions = (
            ("shared_monthly", self.raw_shared_persistence, self.shared_conditioner),
            ("precip_monthly", self.raw_precip_persistence, self.precip_conditioner),
            ("temperature_monthly", self.raw_temperature_persistence, self.temperature_conditioner),
        )
        for name, persistence, conditioner in definitions:
            states = annual_conditioned_monthly_states(
                innovations[name], persistence, self.maximum_persistence,
                annual_states, conditioner,
            )
            gathered.append(gather_cells(states, years * 12 + months))
            diagnostics[f"{name}_states"] = states
        decoded = centered(self.decoder(torch.cat(gathered, dim=-1)))
        heads = base_heads.float().unsqueeze(0) + decoded @ self.head_projection
        diagnostics["combined_offsets"] = decoded
        return heads, diagnostics

    def persistence_values(self) -> dict[str, list[float]]:
        output = {}
        for name in ("annual", "shared", "precip", "temperature"):
            raw = getattr(self, f"raw_{name}_persistence")
            values = self.maximum_persistence * torch.sigmoid(raw)
            output[name] = [float(value) for value in values.detach().cpu()]
        return output


class ClimateNormalHierarchical(AnnualMonthlyResidualAdapter):
    uses_control = False

    def __init__(self, width: int, depth: int, annual_dim: int, monthly_dim: int,
                 maximum_persistence: float) -> None:
        super().__init__(annual_dim, monthly_dim, maximum_persistence)
        self.baseline = residuals.ClimateNormalBaseline(width, depth)

    def member_heads(self, base_heads: torch.Tensor | None, features: torch.Tensor,
                     regimes: torch.Tensor, months: torch.Tensor, years: torch.Tensor,
                     innovations: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        del base_heads
        baseline_features = torch.zeros(
            (*features.shape[:-1], 13), dtype=features.dtype, device=features.device
        )
        baseline_features[..., 10:13] = features[..., 3:6]
        baseline = self.baseline(baseline_features, regimes, months)
        decoded, diagnostics = self.decoded_offsets(months, years, innovations)
        heads = baseline.float().unsqueeze(0) + decoded @ self.head_projection
        diagnostics["combined_offsets"] = decoded
        return heads, diagnostics


def astronomical_envelope(features: torch.Tensor) -> torch.Tensor:
    """Dimensionless top-of-atmosphere daily radiation from lat and target DOY."""
    if features.shape[-1] != 6:
        raise RuntimeError("physics covariates must be sin/cos/leap/lat/lon/elevation")
    phase = torch.atan2(features[..., 0], features[..., 1])
    phase = torch.remainder(phase, 2.0 * math.pi)
    latitude = (features[..., 3] * 90.0).clamp(-89.9, 89.9) * (math.pi / 180.0)
    declination = 0.409 * torch.sin(phase - 1.39)
    sunset = torch.acos((-torch.tan(latitude) * torch.tan(declination)).clamp(-1.0, 1.0))
    inverse_distance = 1.0 + 0.033 * torch.cos(phase)
    radiation = inverse_distance * (
        sunset * torch.sin(latitude) * torch.sin(declination)
        + torch.cos(latitude) * torch.cos(declination) * torch.sin(sunset)
    )
    return radiation.clamp_min(0.0)


class PhysicsConditionedHierarchical(HierarchicalJointFactorAdapter):
    def __init__(self, annual_dim: int, shared_dim: int, field_dim: int,
                 decoder_width: int, physics_width: int,
                 maximum_persistence: float) -> None:
        super().__init__(
            annual_dim, shared_dim, field_dim, decoder_width, maximum_persistence
        )
        self.physics = nn.Sequential(
            nn.Linear(5, physics_width), nn.Tanh(), nn.Linear(physics_width, 5)
        )
        nn.init.zeros_(self.physics[-1].bias)
        nn.init.normal_(self.physics[-1].weight, mean=0.0, std=0.01)
        self.register_buffer("physics_projection", projection((0, 1, 3, 5, 7)))

    def member_heads(self, base_heads: torch.Tensor | None, features: torch.Tensor,
                     regimes: torch.Tensor, months: torch.Tensor, years: torch.Tensor,
                     innovations: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        if base_heads is None:
            raise RuntimeError("physics adapter requires a frozen control")
        core_heads, diagnostics = super().member_heads(
            base_heads, features, regimes, months, years, innovations
        )
        core = diagnostics["combined_offsets"]
        envelope = astronomical_envelope(features)
        physics_input = torch.stack(
            (
                torch.log1p(envelope), features[..., 0], features[..., 1],
                features[..., 3], features[..., 5],
            ),
            dim=-1,
        )
        deterministic = self.physics(physics_input).unsqueeze(0)
        # Shared monthly stochastic state scales the clear-sky-conditioned daily signal.
        cloud = torch.tanh(core[..., :1])
        physics = centered(deterministic * (1.0 + 0.25 * cloud))
        adjustment = physics @ self.physics_projection
        heads = core_heads + adjustment
        diagnostics.update({
            "combined_offsets": heads - base_heads.float().unsqueeze(0),
            "solar_envelope": envelope,
        })
        return heads, diagnostics


def _capacity_definition(contract: dict[str, Any], candidate: str, capacity: str) -> dict[str, Any]:
    if candidate not in CANDIDATES or capacity not in CAPACITIES:
        raise RuntimeError("unknown portfolio candidate/capacity")
    return {
        **contract["capacity_shapes"][capacity],
        **contract["architectures"][candidate],
    }


def backbone_capacity(contract: dict[str, Any], capacity: str) -> str:
    value = contract["controls"]["capacities"][capacity]["accepted_capacity_id"]
    if value not in ("P1", "P2"):
        raise RuntimeError("K1/K2 must map to P1/P2")
    return value


def build_candidate(contract: dict[str, Any], candidate: str, capacity: str) -> PortfolioCandidate:
    definition = _capacity_definition(contract, candidate, capacity)
    maximum = float(definition.get("maximum_persistence", 0.995))
    if candidate == "monthly_residual_adapter":
        return MonthlyResidualAdapter(int(definition["monthly_state_dim"]), maximum)
    annual = int(definition["annual_state_dim"])
    monthly = int(definition["monthly_state_dim"])
    if candidate == "annual_monthly_residual_adapter":
        return AnnualMonthlyResidualAdapter(annual, monthly, maximum)
    if candidate == "hierarchical_joint_factor_adapter":
        return HierarchicalJointFactorAdapter(
            annual, int(definition["shared_factor_dim"]), int(definition["field_factor_dim"]),
            int(definition["decoder_width"]), maximum,
        )
    if candidate == "climate_normal_hierarchical_state_space":
        return ClimateNormalHierarchical(
            int(definition["normal_width"]), int(definition.get("normal_depth", 2)),
            annual, monthly, maximum,
        )
    if candidate == "physics_conditioned_hierarchical_adapter":
        return PhysicsConditionedHierarchical(
            annual, int(definition["shared_factor_dim"]),
            int(definition["field_factor_dim"]), int(definition["decoder_width"]),
            int(definition["physics_width"]), maximum,
        )
    raise AssertionError(candidate)


def candidate_innovations(
    model: PortfolioCandidate,
    members: int,
    batch: int,
    seed: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    semantic_offsets = {
        "annual": 0,
        "monthly": 1,
        "shared_monthly": 1,
        "precip_monthly": 2,
        "temperature_monthly": 3,
    }
    output = {}
    for name, (cells, latent) in model.innovation_shapes().items():
        if name not in semantic_offsets:
            raise RuntimeError(f"unregistered stochastic field: {name}")
        output[name] = residuals.member_innovations(
            members, batch, cells, latent,
            seed + 100003 * semantic_offsets[name], device,
        )
    return output


def portfolio_batch(
    records: list[climate.CalendarRecord],
    selections: list[tuple[int, int]],
    device: torch.device,
    validation_index: int,
) -> tuple[Any, ...]:
    values = climate.climate_batch(records, selections, device, validation_index)
    features, precipitation, targets, weather, station, months, years, valid = values
    target_covariates = []
    regimes = []
    regime_lookup = {name: index for index, name in enumerate(legacy.REGIMES)}
    for record_index, window_index in selections:
        item = records[record_index]
        window = item.windows[window_index]
        start = window.input_start + 1
        stop = start + window.days
        # Only calendar and static descriptors are exposed to physics.
        target_covariates.append(item.record.features[start:stop, 7:13])
        regimes.append(regime_lookup[item.record.regime])
    return (
        features, precipitation, targets, weather, station,
        torch.tensor(regimes, dtype=torch.long, device=device),
        torch.from_numpy(np.stack(months)).to(device=device, dtype=torch.long),
        torch.from_numpy(np.stack(years)).to(device=device, dtype=torch.long),
        torch.from_numpy(np.stack(target_covariates)).to(device=device, dtype=torch.float32),
        months, years, valid,
    )


def forward_control(
    control: torch.jit.ScriptModule,
    features: torch.Tensor,
    station: torch.Tensor,
    hidden_size: int,
) -> torch.Tensor:
    hidden = torch.zeros((1, len(features), hidden_size), device=features.device)
    chunks = []
    for start in range(0, features.shape[1], 365):
        heads, hidden = control(features[:, start : start + 365], station, hidden)
        chunks.append(heads)
    return torch.cat(chunks, dim=1)


def weighted_climate_loss(blocks: dict[str, torch.Tensor], contract: dict[str, Any]) -> torch.Tensor:
    weights = contract["objective"]["climate_blocks"]
    if set(weights) != set(blocks):
        raise RuntimeError("climate objective block set mismatch")
    if float(weights["monthly_interannual_dispersion"]) <= 0.0 or float(
        weights["annual_interannual_dispersion"]
    ) <= 0.0:
        raise RuntimeError("monthly and annual dispersion must carry objective weight")
    denominator = sum(float(value) for value in weights.values())
    if denominator <= 0.0:
        raise RuntimeError("climate block weights must sum positive")
    return sum(float(weights[name]) * value for name, value in blocks.items()) / denominator


def member_daily_nll(
    heads: torch.Tensor,
    precipitation: torch.Tensor,
    targets: torch.Tensor,
    valid: list[np.ndarray],
) -> torch.Tensor:
    return torch.stack(
        [climate.core_daily_nll(member, precipitation, targets, valid) for member in heads]
    ).mean()


def solar_nll(
    heads: torch.Tensor,
    targets: torch.Tensor,
    valid: list[np.ndarray],
) -> torch.Tensor:
    mask = torch.from_numpy(np.stack(valid)).to(heads.device)
    observed = targets.float()[..., 2][mask]
    values = []
    for member in heads:
        selected = member.float()[mask]
        scale = nn.functional.softplus(selected[:, 8]) + 1e-4
        values.append((torch.log(scale) + 0.5 * ((observed - selected[:, 7]) / scale).square()).mean())
    return torch.stack(values).mean()


def sample_solar(heads: torch.Tensor, uniforms: torch.Tensor) -> torch.Tensor:
    scale = nn.functional.softplus(heads[..., 8]) + 1e-4
    normal = torch.sqrt(-2.0 * torch.log(uniforms[..., 1])) * torch.cos(
        2.0 * math.pi * (uniforms[..., 2] + 6.0 / 7.0)
    )
    return torch.exp(heads[..., 7] + scale * normal)


def _solar_residual(predicted: torch.Tensor, observed: torch.Tensor, kind: str) -> torch.Tensor:
    if kind in ("location", "dispersion", "contrast"):
        return (torch.log1p(predicted.clamp_min(0.0)) - torch.log1p(observed.clamp_min(0.0))) / 0.25
    if kind == "dependence":
        return (predicted - observed) / 0.1
    raise RuntimeError(f"unknown solar residual kind: {kind}")


def solar_components(
    generated: torch.Tensor,
    generated_wet: torch.Tensor,
    generated_solar: torch.Tensor,
    observed: torch.Tensor,
    observed_solar: torch.Tensor,
    month_indices: list[np.ndarray],
    year_indices: list[np.ndarray],
    valid_indices: list[np.ndarray],
    squared: bool,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    blocks: dict[str, list[torch.Tensor]] = {
        "annual_interannual_dispersion": [],
        "annual_location": [],
        "monthly_interannual_dispersion": [],
        "monthly_location": [],
        "precipitation_temperature_association": [],
        "wet_dry_contrast": [],
        "within_month_daily_dispersion": [],
    }
    for batch_index in range(generated.shape[1]):
        months = torch.from_numpy(month_indices[batch_index]).to(generated.device)
        years = torch.from_numpy(year_indices[batch_index]).to(generated.device)
        valid = torch.from_numpy(valid_indices[batch_index]).to(generated.device)
        year_count = int(years.max()) + 1
        generated_months, observed_months = [], []
        generated_annual, observed_annual = [], []
        for month in range(12):
            generated_years, observed_years = [], []
            for year in range(year_count):
                mask = valid & (months == month) & (years == year)
                if int(mask.sum()) < 28:
                    raise RuntimeError("incomplete solar calendar month")
                generated_values = generated_solar[:, batch_index, mask]
                observed_values = observed_solar[batch_index, mask]
                generated_years.append(generated_values.mean(1))
                observed_years.append(observed_values.mean())
                blocks["within_month_daily_dispersion"].append(
                    _solar_residual(
                        generated_values.std(1, correction=0).mean(),
                        observed_values.std(0, correction=0),
                        "dispersion",
                    )
                )
            generated_cells = torch.stack(generated_years, dim=1)
            observed_cells = torch.stack(observed_years)
            generated_months.append(generated_cells)
            observed_months.append(observed_cells)
            blocks["monthly_location"].append(
                _solar_residual(generated_cells.mean(), observed_cells.mean(), "location")
            )
            blocks["monthly_interannual_dispersion"].append(
                _solar_residual(
                    generated_cells.flatten().std(0, correction=0),
                    observed_cells.std(0, correction=0),
                    "dispersion",
                )
            )
        for year in range(year_count):
            mask = valid & (years == year)
            generated_annual.append(generated_solar[:, batch_index, mask].mean(1))
            observed_annual.append(observed_solar[batch_index, mask].mean())
        generated_years = torch.stack(generated_annual, dim=1)
        observed_years = torch.stack(observed_annual)
        blocks["annual_location"].append(
            _solar_residual(generated_years.mean(), observed_years.mean(), "location")
        )
        blocks["annual_interannual_dispersion"].append(
            _solar_residual(
                generated_years.flatten().std(0, correction=0),
                observed_years.std(0, correction=0),
                "dispersion",
            )
        )
        generated_solar_valid = generated_solar[:, batch_index, valid]
        generated_wet_valid = generated_wet[:, batch_index, valid]
        observed_valid = observed[batch_index, valid]
        observed_solar_valid = observed_solar[batch_index, valid]
        observed_wet = observed_valid[:, 0] >= 1.0
        generated_contrast = (
            (generated_solar_valid * (1.0 - generated_wet_valid)).sum()
            / (1.0 - generated_wet_valid).sum().clamp_min(1.0)
            - (generated_solar_valid * generated_wet_valid).sum()
            / generated_wet_valid.sum().clamp_min(1.0)
        )
        observed_contrast = (
            observed_solar_valid[~observed_wet].mean()
            - observed_solar_valid[observed_wet].mean()
        )
        blocks["wet_dry_contrast"].append(
            _solar_residual(generated_contrast, observed_contrast, "contrast")
        )
        generated_month_solar = torch.cat(
            [value.transpose(0, 1).reshape(-1) for value in generated_months]
        )
        observed_month_solar = torch.cat(observed_months)
        for field in (0, 1, 2):
            generated_month_weather, observed_month_weather = [], []
            for month in range(12):
                for year in range(year_count):
                    mask = valid & (months == month) & (years == year)
                    generated_values = generated[:, batch_index, mask, field]
                    observed_values = observed[batch_index, mask, field]
                    generated_month_weather.append(
                        generated_values.sum(1) if field == 0 else generated_values.mean(1)
                    )
                    observed_month_weather.append(
                        observed_values.sum() if field == 0 else observed_values.mean()
                    )
            blocks["precipitation_temperature_association"].append(
                _solar_residual(
                    climate._correlation(generated_month_solar, torch.stack(generated_month_weather).flatten()),
                    climate._correlation(observed_month_solar, torch.stack(observed_month_weather)),
                    "dependence",
                )
            )
    reduced = {}
    for name, residuals in blocks.items():
        values = torch.stack(residuals)
        reduced[name] = values.square().mean() if squared else values.abs().mean()
    return torch.stack(list(reduced.values())).mean(), reduced


def fit_clearness_climatology(
    records: list[climate.CalendarRecord], device: torch.device
) -> tuple[torch.Tensor, torch.Tensor]:
    values: list[list[list[np.ndarray]]] = [
        [[] for _ in range(12)] for _ in legacy.REGIMES
    ]
    regime_lookup = {name: index for index, name in enumerate(legacy.REGIMES)}
    for item in records:
        window = item.windows[0]
        start = window.input_start + 1
        stop = start + window.days
        covariates = torch.from_numpy(item.record.features[start:stop, 7:13]).float()
        envelope = astronomical_envelope(covariates).numpy()
        log_solar = item.record.targets[start:stop, 2]
        clearness = log_solar - np.log1p(envelope)
        regime = regime_lookup[item.record.regime]
        for month in range(12):
            mask = window.valid_index & (window.month_index == month)
            values[regime][month].append(clearness[mask])
    locations = np.empty((len(legacy.REGIMES), 12), dtype=np.float32)
    scales = np.empty_like(locations)
    for regime in range(len(legacy.REGIMES)):
        for month in range(12):
            cell = np.concatenate(values[regime][month])
            if len(cell) < 100 or not np.isfinite(cell).all():
                raise RuntimeError("candidate-fit clearness climatology cell incomplete")
            locations[regime, month] = float(cell.mean())
            scales[regime, month] = max(float(cell.std()), 1e-4)
    return torch.from_numpy(locations).to(device), torch.from_numpy(scales).to(device)


def regularization(diagnostics: dict[str, torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    states = [value.square().mean() for key, value in diagnostics.items() if key.endswith("_states")]
    offsets = [value.square().mean() for key, value in diagnostics.items() if key.endswith("offsets")]
    reference = next(iter(diagnostics.values()))
    zero = reference.float().sum() * 0.0
    return (torch.stack(states).mean() if states else zero, torch.stack(offsets).mean() if offsets else zero)


def training_objective(
    member_heads: torch.Tensor,
    diagnostics: dict[str, torch.Tensor],
    generated: torch.Tensor,
    wet: torch.Tensor,
    precipitation: torch.Tensor,
    targets: torch.Tensor,
    observed: torch.Tensor,
    months: list[np.ndarray],
    years: list[np.ndarray],
    valid: list[np.ndarray],
    uniforms: torch.Tensor,
    contract: dict[str, Any],
    physics: bool,
) -> tuple[torch.Tensor, dict[str, float]]:
    _, blocks = climate.climate_components(
        generated, wet, observed, months, years, valid, squared=True
    )
    climate_loss = weighted_climate_loss(blocks, contract)
    daily = member_daily_nll(member_heads, precipitation, targets, valid)
    stability, size = regularization(diagnostics)
    objective = contract["objective"]
    total = (
        climate_loss
        + float(objective["daily_proper_nll_weight"]) * daily
        + float(objective["latent_stability_weight"]) * stability
        + float(objective["residual_size_and_centering_weight"]) * size
    )
    solar = total * 0.0
    if physics:
        generated_solar = sample_solar(member_heads, uniforms)
        observed_solar = torch.exp(targets.float()[..., 2])
        solar, _ = solar_components(
            generated, wet, generated_solar, observed, observed_solar,
            months, years, valid, squared=True,
        )
        total = total + float(objective["physics_solar_family_weight"]) * solar
    return total, {
        "climate": float(climate_loss.detach().cpu()),
        "daily_proper_nll": float(daily.detach().cpu()),
        "latent_stability": float(stability.detach().cpu()),
        "residual_size": float(size.detach().cpu()),
        "solar_nll": float(solar.detach().cpu()),
    }


def sampler(records: list[climate.CalendarRecord], seed: int) -> tuple[np.random.Generator, dict[str, list[int]]]:
    by_regime = {
        regime: [index for index, item in enumerate(records) if item.record.regime == regime]
        for regime in legacy.REGIMES
    }
    if any(len(rows) != 200 for rows in by_regime.values()):
        raise RuntimeError("candidate-fit regime roster mismatch")
    return np.random.Generator(np.random.Philox(seed)), by_regime


def draw(
    generator: np.random.Generator,
    by_regime: dict[str, list[int]],
    records: list[climate.CalendarRecord],
    regime: str,
    count: int,
) -> list[tuple[int, int]]:
    output = []
    for _ in range(count):
        record_index = int(generator.choice(by_regime[regime]))
        window_index = int(generator.integers(len(records[record_index].windows)))
        output.append((record_index, window_index))
    return output


def _score_blocks(
    generated: torch.Tensor,
    wet: torch.Tensor,
    observed: torch.Tensor,
    months: list[np.ndarray],
    years: list[np.ndarray],
    valid: list[np.ndarray],
) -> dict[str, float]:
    _, blocks = climate.climate_components(
        generated, wet, observed, months, years, valid, squared=False
    )
    return {name: float(value.detach().cpu()) for name, value in blocks.items()}


def score_candidate(
    model: PortfolioCandidate,
    control: torch.jit.ScriptModule | None,
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
    if control is not None:
        control.eval()
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            values = portfolio_batch(records, subset, device, 1200)
            features, precipitation, targets, observed, station, regimes, month_t, year_t, physics, months, years, valid = values
            base = None if control is None else forward_control(control, features, station, hidden_size)
            innovations = candidate_innovations(
                model, members, len(subset), innovation_seed_base + offset, device
            )
            heads, _ = model.member_heads(base, physics, regimes, month_t, year_t, innovations)
            uniforms = climate.member_uniforms(
                members, len(subset), heads.shape[2], output_seed_base + offset, device
            )
            generated, wet = residuals.sample_member_weather(heads, uniforms, None)
            daily = member_daily_nll(heads, precipitation, targets, valid)
            blocks = _score_blocks(generated, wet, observed, months, years, valid)
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
            if isinstance(model, PhysicsConditionedHierarchical):
                generated_solar = sample_solar(heads, uniforms)
                observed_solar = torch.exp(targets.float()[..., 2])
                _, solar_blocks = solar_components(
                    generated, wet, generated_solar, observed, observed_solar,
                    months, years, valid, squared=False,
                )
                for name, value in solar_blocks.items():
                    key = f"solar::{name}"
                    totals[key] = totals.get(key, 0.0) + float(value.cpu()) * weight
            if include_points:
                for local, (record_index, window_index) in enumerate(subset):
                    point_blocks = _score_blocks(
                        generated[:, local : local + 1], wet[:, local : local + 1],
                        observed[local : local + 1], [months[local]], [years[local]], [valid[local]],
                    )
                    point_nll = member_daily_nll(
                        heads[:, local : local + 1], precipitation[local : local + 1],
                        targets[local : local + 1], [valid[local]],
                    )
                    points.append({
                        "block_scores": point_blocks,
                        "daily_proper_nll": float(point_nll.cpu()),
                        "point_id": records[record_index].record.point_id,
                        "window_first_year": records[record_index].windows[window_index].first_year,
                    })
    solar_scores = {
        name.removeprefix("solar::"): value / count
        for name, value in sorted(totals.items())
        if name.startswith("solar::")
    }
    block_scores = {
        name: value / count
        for name, value in sorted(totals.items())
        if not name.startswith("solar::")
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
    if solar_scores:
        result["solar"] = {
            "block_scores": solar_scores,
            "family_score": statistics.fmean(solar_scores.values()),
        }
    return result


def score_clearness_climatology(
    control: torch.jit.ScriptModule,
    hidden_size: int,
    climatology: tuple[torch.Tensor, torch.Tensor],
    records: list[climate.CalendarRecord],
    selections: list[tuple[int, int]],
    members: int,
    device: torch.device,
    output_seed_base: int,
) -> dict[str, Any]:
    totals: dict[str, float] = {}
    count = 0
    locations, scales = climatology
    with torch.no_grad():
        for offset in range(0, len(selections), 6):
            subset = selections[offset : offset + 6]
            values = portfolio_batch(records, subset, device, 1200)
            features, _, targets, observed, station, regimes, month_t, _, physics, months, years, valid = values
            heads = forward_control(control, features, station, hidden_size)
            uniforms = climate.member_uniforms(
                members, len(subset), heads.shape[1], output_seed_base + offset, device
            )
            generated, wet, _ = climate.sample_weather(heads, uniforms, None)
            envelope = astronomical_envelope(physics)
            regime = regimes.unsqueeze(1).expand_as(month_t)
            location = torch.log1p(envelope) + locations[regime, month_t]
            scale = scales[regime, month_t]
            normal = torch.sqrt(-2.0 * torch.log(uniforms[..., 1])) * torch.cos(
                2.0 * math.pi * (uniforms[..., 2] + 6.0 / 7.0)
            )
            generated_solar = torch.exp(location.unsqueeze(0) + scale.unsqueeze(0) * normal)
            observed_solar = torch.exp(targets.float()[..., 2])
            _, blocks = solar_components(
                generated, wet, generated_solar, observed, observed_solar,
                months, years, valid, squared=False,
            )
            weight = len(subset)
            count += weight
            for name, value in blocks.items():
                totals[name] = totals.get(name, 0.0) + float(value.cpu()) * weight
    block_scores = {name: value / count for name, value in sorted(totals.items())}
    return {
        "block_scores": block_scores,
        "family_score": statistics.fmean(block_scores.values()),
        "point_count": count,
        "stochastic_members": members,
    }


def checkpoint_value(score: dict[str, Any], contract: dict[str, Any]) -> float:
    selection = contract["checkpoint"]["selection_scalar"]
    if (
        float(selection["daily_proper_nll_weight"])
        != float(contract["objective"]["daily_proper_nll_weight"])
        or float(selection["physics_solar_family_weight"])
        != float(contract["objective"]["physics_solar_family_weight"])
        or selection["training_regularizers_excluded"]
        != ["latent_stability", "residual_size_and_centering"]
    ):
        raise RuntimeError("checkpoint selection scalar disagrees with frozen objective")
    objective = float(selection["core_family_balanced_climate_weight"]) * weighted_score(
        score, contract
    )
    objective += float(selection["daily_proper_nll_weight"]) * score["daily_proper_nll"]
    if "solar" in score:
        if not selection["physics_solar_term_applies_only_to_physics_candidate"]:
            raise RuntimeError("physics-only checkpoint selection flag drifted")
        objective += float(selection["physics_solar_family_weight"]) * score["solar"][
            "family_score"
        ]
    return objective


def weighted_score(score: dict[str, Any], contract: dict[str, Any]) -> float:
    weights = contract["objective"]["climate_blocks"]
    denominator = sum(float(value) for value in weights.values())
    return sum(float(weights[name]) * score["block_scores"][name] for name in weights) / denominator


def train_candidate(
    contract: dict[str, Any],
    candidate: str,
    capacity: str,
    seed: int,
    control: torch.jit.ScriptModule | None,
    hidden_size: int,
    fit: list[climate.CalendarRecord],
    validation: list[climate.CalendarRecord],
    device: torch.device,
    output: Path,
) -> tuple[PortfolioCandidate, dict[str, Any]]:
    if float(contract["objective"]["paired_daily_pattern_weight"]) != 0.0:
        raise RuntimeError("paired daily pattern loss must remain zero")
    legacy.configure(seed)
    model = build_candidate(contract, candidate, capacity).to(device)
    learning_rate_key = (
        "climate_normal_learning_rate"
        if candidate == "climate_normal_hierarchical_state_space"
        else "adapter_learning_rate"
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(contract["training"][learning_rate_key]),
        weight_decay=float(contract["training"]["weight_decay"]),
    )
    generator, by_regime = sampler(fit, seed)
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
            selections = draw(
                generator, by_regime, fit, regime,
                int(contract["training"]["records_per_batch"]),
            )
            values = portfolio_batch(fit, selections, device, len(fit))
            features, precipitation, targets, observed, station, regimes, month_t, year_t, physics, months, years, valid = values
            with torch.no_grad():
                base = None if control is None else forward_control(control, features, station, hidden_size)
            innovations = candidate_innovations(
                model, int(stochastic["training_members"]), len(selections),
                seed + 200000 + epoch * 1009 + batch_index, device,
            )
            optimizer.zero_grad(set_to_none=True)
            heads, diagnostics = model.member_heads(base, physics, regimes, month_t, year_t, innovations)
            uniforms = climate.member_uniforms(
                int(stochastic["training_members"]), len(selections), heads.shape[2],
                seed + 300000 + epoch * 1009 + batch_index, device,
            )
            generated, wet = residuals.sample_member_weather(
                heads, uniforms, float(contract["training"]["relaxed_wet_temperature"])
            )
            objective, row = training_objective(
                heads, diagnostics, generated, wet, precipitation, targets, observed,
                months, years, valid, uniforms, contract,
                candidate == "physics_conditioned_hierarchical_adapter",
            )
            objective.backward()
            if not math.isfinite(float(objective)) or not all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
                for parameter in model.parameters()
            ):
                raise RuntimeError("non-finite candidate training state")
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
        value = checkpoint_value(validation_score, contract)
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
            "validation": {key: value for key, value in validation_score.items() if key != "points"},
        })
        if (
            epoch + 1 >= int(checkpoint["minimum_epochs"])
            and patience >= int(checkpoint["early_stop_patience"])
        ):
            break
    if best_payload is None:
        raise RuntimeError("candidate produced no checkpoint")
    model.load_state_dict(best_payload)
    model.eval()
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "checkpoint.pt"
    torch.save({
        "candidate": candidate, "capacity": capacity, "epoch": best_epoch,
        "model": best_payload, "training_seed": seed,
    }, checkpoint_path)
    result = {
        "best_epoch": best_epoch,
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "checkpoint_sha256": digest(checkpoint_path),
        "epochs_completed": len(trace),
        "fit_points": len(fit),
        "fit_validation_gradient": False,
        "model_state_sha256": model_state_sha256(model),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "persistence": model.persistence_values(),
        "trace": trace,
        "wall_seconds": time.monotonic() - started,
    }
    return model, result


def calendar_preflight(corpus: Path, normalized: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    # Importing M5R9 experiment would execute an application-level dependency;
    # keep the canonical check local to the shared science engine.
    import tarfile

    expected = profile["fit_period_example"]
    role_counts = {"candidate_fit": 0, "fit_validation": 0}
    for shard in normalized["daymet_shards"]:
        with tarfile.open(corpus / shard["path"], "r:gz") as archive:
            for member in archive.getmembers():
                stream = archive.extractfile(member)
                if stream is None:
                    continue
                document = json.load(stream)
                role = document["role"]
                if role not in role_counts:
                    continue
                observed = [bool(value) for value in document["source_observed"]]
                missing = [
                    date for date, keep in zip(document["dates"], observed, strict=True) if not keep
                ]
                if len(document["dates"]) != expected["calendar_axis_rows"]:
                    raise RuntimeError("Daymet calendar-axis count mismatch")
                if sum(observed) != expected["observed_rows"]:
                    raise RuntimeError("Daymet observed-row count mismatch")
                if missing != expected["unobserved_dates"]:
                    raise RuntimeError("Daymet missing-date profile mismatch")
                for field in ("prcp", "tmax", "tmin"):
                    if [value is not None for value in document["fields"][field]] != observed:
                        raise RuntimeError(f"Daymet {field} mask mismatch")
                solar_values = document["fields"]["srad"]
                if [value is not None for value in solar_values] != observed:
                    raise RuntimeError("Daymet srad mask mismatch")
                if any(
                    not math.isfinite(float(value)) or float(value) <= 0.0
                    for value, keep in zip(solar_values, observed, strict=True)
                    if keep
                ):
                    raise RuntimeError("Daymet observed srad support mismatch")
                role_counts[role] += 1
    if role_counts != {"candidate_fit": 1200, "fit_validation": 240}:
        raise RuntimeError(f"calendar role mismatch: {role_counts}")
    return {
        "calendar_axis_rows_per_point": expected["calendar_axis_rows"],
        "observed_rows_per_point": expected["observed_rows"],
        "physics_observed_rows_per_point": expected["observed_rows"],
        "profile_id": profile["profile_id"],
        "role_counts": role_counts,
        "schema_version": 1,
        "unobserved_dates": expected["unobserved_dates"],
        "valid": True,
        "window_axis_rows": profile["window_example"]["calendar_axis_rows"],
        "window_observed_rows": profile["window_example"]["observed_rows"],
        "window_physics_observed_rows": profile["window_example"]["observed_rows"],
    }


def self_test() -> None:
    torch.manual_seed(190710)
    device = torch.device("cpu")
    members, batch, days = 8, 2, 24
    months = torch.tensor([list(range(12)) * 2] * batch)
    years = torch.tensor([[0] * 12 + [1] * 12] * batch)
    features = torch.zeros((batch, days, 6))
    features[..., 1] = 1.0
    features[..., 3] = torch.tensor((0.5, -0.5)).unsqueeze(1)
    base = torch.zeros((batch, days, 15))
    regimes = torch.tensor((0, 1))
    contract = {
        "controls": {"capacities": {
            "K1": {"accepted_capacity_id": "P1"},
            "K2": {"accepted_capacity_id": "P2"},
        }},
        "architectures": {candidate: {} for candidate in CANDIDATES},
        "capacity_shapes": {
            "K1": {
                "monthly_state_dim": 6, "annual_state_dim": 4,
                "shared_factor_dim": 4, "field_factor_dim": 2, "decoder_width": 16,
                "normal_width": 16, "normal_depth": 2, "physics_width": 8,
                "maximum_persistence": 0.995,
            },
            "K2": {
                "monthly_state_dim": 12, "annual_state_dim": 8,
                "shared_factor_dim": 8, "field_factor_dim": 4, "decoder_width": 32,
                "normal_width": 24, "normal_depth": 2, "physics_width": 16,
                "maximum_persistence": 0.995,
            },
        }
    }
    for candidate in CANDIDATES:
        model = build_candidate(contract, candidate, "K1")
        innovations = candidate_innovations(model, members, batch, 91, device)
        control = None if not model.uses_control else base
        heads, diagnostics = model.member_heads(
            control, features, regimes, months, years, innovations
        )
        repeated, _ = model.member_heads(
            control, features, regimes, months, years,
            candidate_innovations(model, members, batch, 91, device),
        )
        if heads.shape != (members, batch, days, 15) or not torch.equal(heads, repeated):
            raise RuntimeError(f"candidate deterministic shape/replay failed: {candidate}")
        offsets = heads - (base.unsqueeze(0) if control is not None else heads.mean(0, keepdim=True))
        if not torch.allclose(offsets.mean(0), torch.zeros_like(offsets.mean(0)), atol=2e-6):
            raise RuntimeError(f"candidate centering failed: {candidate}")
        if any(key.endswith("_states") and not torch.isfinite(value).all() for key, value in diagnostics.items()):
            raise RuntimeError(f"candidate state support failed: {candidate}")
    monthly_only = MonthlyResidualAdapter(6, 0.995)
    hierarchical = AnnualMonthlyResidualAdapter(3, 6, 0.995)
    monthly_field = candidate_innovations(monthly_only, members, batch, 149, device)[
        "monthly"
    ]
    hierarchical_field = candidate_innovations(
        hierarchical, members, batch, 149, device
    )["monthly"]
    if not torch.equal(monthly_field, hierarchical_field):
        raise RuntimeError("semantic common random field self-test failed")
    model = AnnualMonthlyResidualAdapter(4, 6, 0.995)
    innovations = candidate_innovations(model, 2048, 1, 171, device)
    monthly = stationary_ar_states(
        innovations["monthly"], model.raw_monthly_persistence, model.maximum_persistence
    )
    if not 0.85 <= float(monthly[:, :, 0].std(correction=0)) <= 1.15:
        raise RuntimeError("stationary initial-state variance failed")
    _, diagnostics = model.member_heads(base[:1], features[:1], regimes[:1], months[:1], years[:1], {
        name: value[:, :1] for name, value in candidate_innovations(model, members, batch, 271, device).items()
    })
    annual = diagnostics["annual_offsets"]
    if not torch.equal(annual[:, :, 0], annual[:, :, 11]) or torch.equal(annual[:, :, 11], annual[:, :, 12]):
        raise RuntimeError("annual hierarchy mapping failed")
    fixed = {
        name: value[:, :1]
        for name, value in candidate_innovations(model, members, batch, 372, device).items()
    }
    changed = {name: value.clone() for name, value in fixed.items()}
    changed["annual"] = changed["annual"] + 1.0
    _, first_diagnostics = model.member_heads(
        base[:1], features[:1], regimes[:1], months[:1], years[:1], fixed
    )
    _, changed_diagnostics = model.member_heads(
        base[:1], features[:1], regimes[:1], months[:1], years[:1], changed
    )
    if torch.equal(
        first_diagnostics["monthly_states"], changed_diagnostics["monthly_states"]
    ):
        raise RuntimeError("annual state does not condition the monthly transition")
    physics_model = build_candidate(contract, "physics_conditioned_hierarchical_adapter", "K1")
    if not isinstance(physics_model, HierarchicalJointFactorAdapter) or (
        physics_model.shared_dim != contract["capacity_shapes"]["K1"]["shared_factor_dim"]
        or physics_model.field_dim != contract["capacity_shapes"]["K1"]["field_factor_dim"]
    ):
        raise RuntimeError("physics shared/field factor shape freeze failed")
    envelope = astronomical_envelope(features)
    rejected_extra_input = False
    try:
        astronomical_envelope(torch.cat((features, torch.ones((*features.shape[:-1], 1))), dim=-1))
    except RuntimeError:
        rejected_extra_input = True
    if not rejected_extra_input or not torch.isfinite(envelope).all():
        raise RuntimeError("physics envelope/leakage self-test failed")
    simple_blocks = {
        "annual_interannual_dispersion": torch.tensor(2.0, requires_grad=True),
        "annual_location": torch.tensor(1.0, requires_grad=True),
        "monthly_interannual_dispersion": torch.tensor(3.0, requires_grad=True),
        "monthly_location": torch.tensor(1.0, requires_grad=True),
        "precipitation_temperature_dependence": torch.tensor(1.0, requires_grad=True),
        "wet_occurrence_and_amount": torch.tensor(1.0, requires_grad=True),
        "within_month_daily_dispersion": torch.tensor(1.0, requires_grad=True),
    }
    objective_contract = {"objective": {"climate_blocks": {name: 1.0 for name in simple_blocks}}}
    value = weighted_climate_loss(simple_blocks, objective_contract)
    value.backward()
    if simple_blocks["annual_interannual_dispersion"].grad is None or simple_blocks[
        "monthly_interannual_dispersion"
    ].grad is None:
        raise RuntimeError("dispersion objective gradient self-test failed")
    print("A10M5R10-PORTFOLIO-CORE-SELF-TEST-PASS")


if __name__ == "__main__":
    self_test()
