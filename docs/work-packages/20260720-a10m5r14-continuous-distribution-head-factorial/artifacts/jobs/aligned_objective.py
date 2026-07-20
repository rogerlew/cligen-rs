#!/usr/bin/env python3
"""Differentiable counterparts for all 188 frozen temporal-selector metrics."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import torch

MONTHLY_PRECIPITATION = (
    "mean", "standard_deviation", "coefficient_of_variation", "skew",
    "dry_frequency", "q10", "q50", "q90", "q95",
)
MONTHLY_TEMPERATURE = (
    "tmax_mean", "tmax_standard_deviation", "tmin_mean",
    "tmin_standard_deviation", "tmax_tmin_correlation",
)
ANNUAL = (
    "precipitation_mean", "precipitation_standard_deviation",
    "precipitation_q95", "tmax_mean", "tmax_standard_deviation",
    "tmin_mean", "tmin_standard_deviation", "precipitation_lag1",
    "tmax_lag1", "tmin_lag1", "precipitation_tmax_correlation",
    "precipitation_tmin_correlation", "tmax_tmin_correlation",
)
OCCURRENCE = (
    "p_wet_given_wet", "p_wet_given_dry", "wet_spell_survival_3",
    "wet_spell_survival_7", "dry_spell_survival_3",
    "dry_spell_survival_7", "seasonal_wet_frequency_range",
)


def metric_keys() -> tuple[str, ...]:
    rows = [
        f"monthly.{month:02d}.precipitation_{name}"
        for month in range(1, 13)
        for name in MONTHLY_PRECIPITATION
    ]
    rows.extend(
        f"monthly.{month:02d}.{name}"
        for month in range(1, 13)
        for name in MONTHLY_TEMPERATURE
    )
    rows.extend(f"annual.{name}" for name in ANNUAL)
    rows.extend(f"occurrence.{name}" for name in OCCURRENCE)
    if len(rows) != 188 or len(set(rows)) != 188:
        raise RuntimeError("frozen selector metric registry is not exactly 188")
    return tuple(rows)


def _std(values: torch.Tensor) -> torch.Tensor:
    return values.std(dim=-1, correction=1)


def _correlation(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    left = left - left.mean(dim=-1, keepdim=True)
    right = right - right.mean(dim=-1, keepdim=True)
    denominator = torch.sqrt(
        left.square().mean(dim=-1) * right.square().mean(dim=-1)
    ).clamp_min(1.0e-6)
    return (left * right).mean(dim=-1) / denominator


def _skew(values: torch.Tensor) -> torch.Tensor:
    centered = values - values.mean(dim=-1, keepdim=True)
    scale = centered.square().mean(dim=-1, keepdim=True).sqrt().clamp_min(1.0e-6)
    return (centered / scale).pow(3).mean(dim=-1)


def _spell_survival(wet: torch.Tensor, valid: torch.Tensor, length: int) -> torch.Tensor:
    """Smooth run-survival ratio; exact for binary wet indicators."""
    previous_wet = torch.cat((torch.zeros_like(wet[..., :1]), wet[..., :-1]), dim=-1)
    previous_valid = torch.cat((torch.zeros_like(valid[:1]), valid[:-1]))
    starts = wet * valid.to(wet.dtype) * (
        1.0 - previous_wet * previous_valid.to(wet.dtype)
    )
    candidates = starts[..., : wet.shape[-1] - length + 1]
    supported = valid[: valid.shape[0] - length + 1].clone()
    survival = torch.ones_like(candidates)
    for offset in range(length):
        supported &= valid[offset : offset + supported.shape[0]]
        survival = survival * wet[..., offset : offset + survival.shape[-1]]
    numerator = (candidates * survival * supported.to(wet.dtype)).sum(dim=-1)
    denominator = starts.sum(dim=-1).clamp_min(1.0e-6)
    return numerator / denominator


def _occurrence(
    wet: torch.Tensor, months: torch.Tensor, valid: torch.Tensor
) -> dict[str, torch.Tensor]:
    left_valid = valid[:-1] & valid[1:]
    previous = wet[..., :-1]
    current = wet[..., 1:]
    mask = left_valid.to(wet.dtype)
    pww = (previous * current * mask).sum(-1) / (previous * mask).sum(-1).clamp_min(1.0e-6)
    dry_previous = 1.0 - previous
    pwd = (dry_previous * current * mask).sum(-1) / (dry_previous * mask).sum(-1).clamp_min(1.0e-6)
    rows = {
        "occurrence.p_wet_given_wet": pww,
        "occurrence.p_wet_given_dry": pwd,
        "occurrence.wet_spell_survival_3": _spell_survival(wet, valid, 3),
        "occurrence.wet_spell_survival_7": _spell_survival(wet, valid, 7),
        "occurrence.dry_spell_survival_3": _spell_survival(1.0 - wet, valid, 3),
        "occurrence.dry_spell_survival_7": _spell_survival(1.0 - wet, valid, 7),
    }
    frequencies = []
    for season in ((11, 0, 1), (2, 3, 4), (5, 6, 7), (8, 9, 10)):
        axis = valid & torch.isin(months, torch.tensor(season, device=months.device))
        frequencies.append(wet[..., axis].mean(dim=-1))
    values = torch.stack(frequencies, dim=-1)
    rows["occurrence.seasonal_wet_frequency_range"] = values.max(-1).values - values.min(-1).values
    return rows


def _realized(
    weather: torch.Tensor,
    wet: torch.Tensor,
    month_index: np.ndarray,
    year_index: np.ndarray,
    valid_index: np.ndarray,
    *,
    relaxed_dry_frequency: bool,
) -> dict[str, torch.Tensor]:
    """Return metric tensors with arbitrary leading dimensions."""
    device = weather.device
    months = torch.as_tensor(month_index, dtype=torch.long, device=device)
    years = torch.as_tensor(year_index, dtype=torch.long, device=device)
    valid = torch.as_tensor(valid_index, dtype=torch.bool, device=device)
    if len(months) != 5844 or int(valid.sum()) != 5840:
        raise RuntimeError("aligned objective requires the frozen 16-year mask")
    output: dict[str, torch.Tensor] = {}
    month_cells: dict[int, tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = {}
    for month in range(12):
        p_cells, tx_cells, tn_cells = [], [], []
        for year in range(16):
            axis = valid & (months == month) & (years == year)
            if int(axis.sum()) < 28:
                raise RuntimeError("mask-ineligible month entered aligned objective")
            p_cells.append(weather[..., axis, 0].sum(-1))
            tx_cells.append(weather[..., axis, 1].mean(-1))
            tn_cells.append(weather[..., axis, 2].mean(-1))
        precipitation = torch.stack(p_cells, dim=-1)
        tmax = torch.stack(tx_cells, dim=-1)
        tmin = torch.stack(tn_cells, dim=-1)
        month_cells[month] = (precipitation, tmax, tmin)
        prefix = f"monthly.{month + 1:02d}"
        pmean, pstd = precipitation.mean(-1), _std(precipitation)
        output[f"{prefix}.precipitation_mean"] = pmean
        output[f"{prefix}.precipitation_standard_deviation"] = pstd
        output[f"{prefix}.precipitation_coefficient_of_variation"] = pstd / pmean.clamp_min(1.0e-6)
        output[f"{prefix}.precipitation_skew"] = _skew(precipitation)
        if relaxed_dry_frequency:
            soft_dry = torch.sigmoid((1.0 - precipitation) / 0.1)
            hard_dry = (precipitation < 1.0).to(weather.dtype)
            straight_dry = soft_dry + (hard_dry - soft_dry).detach()
            output[f"{prefix}.precipitation_dry_frequency"] = straight_dry.mean(-1)
        else:
            output[f"{prefix}.precipitation_dry_frequency"] = (precipitation < 1.0).to(weather.dtype).mean(-1)
        for label, probability in (("q10", 0.10), ("q50", 0.50), ("q90", 0.90), ("q95", 0.95)):
            output[f"{prefix}.precipitation_{label}"] = torch.quantile(precipitation, probability, dim=-1)
        output[f"{prefix}.tmax_mean"] = tmax.mean(-1)
        output[f"{prefix}.tmax_standard_deviation"] = _std(tmax)
        output[f"{prefix}.tmin_mean"] = tmin.mean(-1)
        output[f"{prefix}.tmin_standard_deviation"] = _std(tmin)
        output[f"{prefix}.tmax_tmin_correlation"] = _correlation(tmax, tmin)

    annual_cells: list[list[torch.Tensor]] = [[], [], []]
    for year in range(16):
        axis = valid & (years == year)
        if int(axis.sum()) != 365:
            raise RuntimeError("mask-ineligible year entered aligned objective")
        annual_cells[0].append(weather[..., axis, 0].sum(-1))
        annual_cells[1].append(weather[..., axis, 1].mean(-1))
        annual_cells[2].append(weather[..., axis, 2].mean(-1))
    annual = [torch.stack(values, dim=-1) for values in annual_cells]
    precipitation, tmax, tmin = annual
    output.update({
        "annual.precipitation_mean": precipitation.mean(-1),
        "annual.precipitation_standard_deviation": _std(precipitation),
        "annual.precipitation_q95": torch.quantile(precipitation, 0.95, dim=-1),
        "annual.tmax_mean": tmax.mean(-1),
        "annual.tmax_standard_deviation": _std(tmax),
        "annual.tmin_mean": tmin.mean(-1),
        "annual.tmin_standard_deviation": _std(tmin),
        "annual.precipitation_lag1": _correlation(precipitation[..., :-1], precipitation[..., 1:]),
        "annual.tmax_lag1": _correlation(tmax[..., :-1], tmax[..., 1:]),
        "annual.tmin_lag1": _correlation(tmin[..., :-1], tmin[..., 1:]),
        "annual.precipitation_tmax_correlation": _correlation(precipitation, tmax),
        "annual.precipitation_tmin_correlation": _correlation(precipitation, tmin),
        "annual.tmax_tmin_correlation": _correlation(tmax, tmin),
    })
    output.update(_occurrence(wet, months, valid))
    if set(output) != set(metric_keys()):
        raise RuntimeError("aligned objective metric coverage drift")
    return output


def scale_kind(key: str) -> str:
    if "precipitation_" in key and any(
        name in key for name in ("mean", "standard_deviation", "q10", "q50", "q90", "q95")
    ):
        return "log_precipitation"
    if "coefficient_of_variation" in key:
        return "coefficient_of_variation"
    if "skew" in key:
        return "skew"
    if key.startswith("occurrence.") or "dry_frequency" in key:
        return "probability"
    if "correlation" in key or "lag1" in key:
        return "correlation"
    if "tmax_mean" in key or "tmin_mean" in key:
        return "temperature_mean_c"
    if "tmax_standard_deviation" in key or "tmin_standard_deviation" in key:
        return "temperature_standard_deviation_c"
    raise RuntimeError(f"unregistered aligned-objective scale: {key}")


def _scaled(candidate: torch.Tensor, target: torch.Tensor, key: str) -> torch.Tensor:
    kind = scale_kind(key)
    if kind == "log_precipitation":
        return (torch.log(candidate.clamp_min(0.0) + 0.1) - torch.log(target.clamp_min(0.0) + 0.1)) / 0.25
    divisor = {
        "coefficient_of_variation": 0.25,
        "skew": 0.5,
        "probability": 0.05,
        "correlation": 0.1,
        "temperature_mean_c": 1.0,
        "temperature_standard_deviation_c": 0.5,
    }[kind]
    return (candidate - target) / divisor


def aligned_components(
    generated: torch.Tensor,
    generated_wet: torch.Tensor,
    observed: torch.Tensor,
    month_indices: list[np.ndarray],
    year_indices: list[np.ndarray],
    valid_indices: list[np.ndarray],
    *,
    gradient_surrogate: bool,
) -> dict[str, torch.Tensor]:
    if generated.ndim != 4 or observed.ndim != 3 or generated.shape[1:] != observed.shape:
        raise RuntimeError("aligned objective weather shapes differ")
    rows: dict[str, list[torch.Tensor]] = {key: [] for key in metric_keys()}
    for batch in range(generated.shape[1]):
        candidate = _realized(
            generated[:, batch], generated_wet[:, batch], month_indices[batch],
            year_indices[batch], valid_indices[batch],
            relaxed_dry_frequency=gradient_surrogate,
        )
        target_weather = observed[batch]
        target_wet = (target_weather[:, 0] >= 1.0).to(target_weather.dtype)
        target = _realized(
            target_weather, target_wet, month_indices[batch], year_indices[batch],
            valid_indices[batch], relaxed_dry_frequency=False,
        )
        for key in metric_keys():
            residual = _scaled(candidate[key].mean(), target[key], key)
            rows[key].append(residual.abs())
    return {key: torch.stack(values).mean() for key, values in rows.items()}


def aligned_loss(*args, **kwargs) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    components = aligned_components(*args, gradient_surrogate=True, **kwargs)
    return torch.stack(tuple(components.values())).mean(), components


def family_name(key: str) -> str:
    if key.startswith("monthly."):
        return "monthly_precipitation" if ".precipitation_" in key else "monthly_temperature"
    return key.split(".", 1)[0]


def require_registry(keys: Iterable[str]) -> None:
    if tuple(keys) != metric_keys():
        raise RuntimeError("aligned objective registry order drift")


if __name__ == "__main__":
    require_registry(metric_keys())
    print("A10M5R14-ALIGNED-OBJECTIVE-REGISTRY-PASS")
