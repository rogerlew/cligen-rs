#!/usr/bin/env python3
"""Exact differentiable annual families from the frozen R12 selector."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch

FAMILY_KEYS = (
    "annual_location",
    "annual_dispersion",
    "annual_lag",
    "annual_cross_field_dependence",
)
PAIRS = ((0, 1), (0, 2), (1, 2))


def correlation(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    """Correlation along the final axis, preserving member dimensions."""
    left = left - left.mean(dim=-1, keepdim=True)
    right = right - right.mean(dim=-1, keepdim=True)
    denominator = torch.sqrt(
        (
            left.square().mean(dim=-1)
            * right.square().mean(dim=-1)
        ).clamp_min(1.0e-12)
    )
    return (left * right).mean(dim=-1) / denominator


def annual_series(
    values: torch.Tensor, year_index: np.ndarray, valid: np.ndarray
) -> torch.Tensor:
    """Return [..., 16 years, precipitation-total/tmax-mean/tmin-mean]."""
    if len(year_index) != 5844 or len(valid) != 5844:
        raise RuntimeError("annual selector loss requires the 5844-row axis")
    years = sorted(set(int(value) for value in year_index.tolist()))
    if years != list(range(16)):
        raise RuntimeError("annual selector loss requires 16 ordinal years")
    output = []
    for year in years:
        axis = year_index == year
        axis_rows = int(axis.sum())
        observed_rows = int((valid & axis).sum())
        missing_rows = int((~valid & axis).sum())
        if axis_rows not in (365, 366) or observed_rows != 365:
            raise RuntimeError(
                "each normalized Gregorian year must have exactly 365 "
                "source-observed core rows"
            )
        if missing_rows != axis_rows - 365:
            raise RuntimeError("annual source-observed mask shape drift")
        mask = torch.as_tensor(valid & axis, dtype=torch.bool, device=values.device)
        output.append(
            torch.stack(
                (
                    values[..., mask, 0].sum(dim=-1),
                    values[..., mask, 1].mean(dim=-1),
                    values[..., mask, 2].mean(dim=-1),
                ),
                dim=-1,
            )
        )
    return torch.stack(output, dim=-2)


def _scaled(
    generated: torch.Tensor,
    observed: torch.Tensor,
    kind: str,
    squared: bool,
) -> torch.Tensor:
    if kind == "precipitation":
        residual = (
            torch.log(generated.clamp_min(0.0) + 0.1)
            - torch.log(observed.clamp_min(0.0) + 0.1)
        ) / 0.25
    elif kind == "temperature_location":
        residual = generated - observed
    elif kind == "temperature_dispersion":
        residual = (generated - observed) / 0.5
    elif kind == "dependence":
        residual = (generated - observed) / 0.1
    else:
        raise RuntimeError(f"unknown selector scale: {kind}")
    return residual.square() if squared else residual.abs()


def lag_component_paths(
    candidate: torch.Tensor, target: torch.Tensor, *, squared: bool
) -> dict[str, torch.Tensor]:
    output = {}
    for field, name in enumerate(("precipitation", "tmax", "tmin")):
        generated = correlation(candidate[:, 1:, field], candidate[:, :-1, field]).mean()
        observed = correlation(target[1:, field], target[:-1, field])
        output[f"annual_lag.{name}"] = _scaled(
            generated, observed, "dependence", squared
        )
    return output


def cross_field_component_paths(
    candidate: torch.Tensor, target: torch.Tensor, *, squared: bool
) -> dict[str, torch.Tensor]:
    names = ("precipitation_tmax", "precipitation_tmin", "tmax_tmin")
    output = {}
    for (left, right), name in zip(PAIRS, names):
        generated = correlation(candidate[..., left], candidate[..., right]).mean()
        observed = correlation(target[:, left], target[:, right])
        output[f"annual_cross_field_dependence.{name}"] = _scaled(
            generated, observed, "dependence", squared
        )
    return output


def selector_aligned_annual_components(
    generated: torch.Tensor,
    observed: torch.Tensor,
    years: list[np.ndarray],
    valid: list[np.ndarray],
    *,
    squared: bool,
) -> dict[str, torch.Tensor]:
    """Four equal-weight families with exact R12 transforms and scales."""
    if generated.ndim != 4 or observed.ndim != 3:
        raise RuntimeError("annual loss expects [member,batch,day,field]")
    if generated.shape[1:] != observed.shape or generated.shape[-1] != 3:
        raise RuntimeError("generated and observed annual fields differ")
    rows: dict[str, list[torch.Tensor]] = {name: [] for name in FAMILY_KEYS}
    for batch in range(generated.shape[1]):
        candidate = annual_series(generated[:, batch], years[batch], valid[batch])
        target = annual_series(observed[batch], years[batch], valid[batch])

        # Match temporal_select.annual_family_keys exactly: precipitation mean
        # and q95 plus tmax/tmin means are one four-component location family.
        location = [
            _scaled(candidate[..., 0].mean(dim=-1).mean(), target[:, 0].mean(), "precipitation", squared),
            _scaled(
                torch.quantile(candidate[..., 0], 0.95, dim=-1).mean(),
                torch.quantile(target[:, 0], 0.95),
                "precipitation",
                squared,
            ),
            _scaled(candidate[..., 1].mean(dim=-1).mean(), target[:, 1].mean(), "temperature_location", squared),
            _scaled(candidate[..., 2].mean(dim=-1).mean(), target[:, 2].mean(), "temperature_location", squared),
        ]
        rows["annual_location"].append(torch.stack(location).mean())

        dispersion = [
            _scaled(
                candidate[..., 0].std(dim=-1, correction=0).mean(),
                target[:, 0].std(correction=0),
                "precipitation",
                squared,
            ),
            _scaled(
                candidate[..., 1].std(dim=-1, correction=0).mean(),
                target[:, 1].std(correction=0),
                "temperature_dispersion",
                squared,
            ),
            _scaled(
                candidate[..., 2].std(dim=-1, correction=0).mean(),
                target[:, 2].std(correction=0),
                "temperature_dispersion",
                squared,
            ),
        ]
        rows["annual_dispersion"].append(torch.stack(dispersion).mean())

        lag = lag_component_paths(candidate, target, squared=squared)
        rows["annual_lag"].append(torch.stack(tuple(lag.values())).mean())
        dependence = cross_field_component_paths(candidate, target, squared=squared)
        rows["annual_cross_field_dependence"].append(
            torch.stack(tuple(dependence.values())).mean()
        )
    return {name: torch.stack(rows[name]).mean() for name in FAMILY_KEYS}


def selector_aligned_annual_loss(
    generated: torch.Tensor,
    observed: torch.Tensor,
    years: list[np.ndarray],
    valid: list[np.ndarray],
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    components = selector_aligned_annual_components(
        generated, observed, years, valid, squared=True
    )
    return torch.stack(tuple(components.values())).mean(), components


def component_scalars(values: dict[str, torch.Tensor]) -> dict[str, float]:
    return {name: float(value.detach().cpu()) for name, value in values.items()}


def self_test() -> None:
    # 1980--1995 has 5844 axis rows and four Daymet-null leap-year Dec 31s.
    dates = np.arange(np.datetime64("1980-01-01"), np.datetime64("1996-01-01"))
    year_values = dates.astype("datetime64[Y]").astype(int) + 1970
    years = year_values - 1980
    text = dates.astype(str)
    valid = np.asarray([
        not value.endswith("-12-31") or int(value[:4]) % 4 != 0
        for value in text
    ], dtype=bool)
    values = torch.arange(5844, dtype=torch.float32).view(1, 5844, 1).repeat(2, 1, 3)
    observed = values[:1]
    components = selector_aligned_annual_components(
        values.unsqueeze(1), observed, [years], [valid], squared=False
    )
    if set(components) != set(FAMILY_KEYS) or any(float(value) != 0.0 for value in components.values()):
        raise RuntimeError("exact annual selector identity failed")
    broken = valid.copy()
    broken[0] = False
    try:
        annual_series(values[0], years, broken)
    except RuntimeError:
        pass
    else:
        raise RuntimeError("incomplete annual support was accepted")


if __name__ == "__main__":
    self_test()
    print("A10M5R13-SELECTOR-LOSS-SELF-TEST-PASS")
