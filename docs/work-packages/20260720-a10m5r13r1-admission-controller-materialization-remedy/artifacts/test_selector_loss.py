#!/usr/bin/env python3
"""Test exact selector scaling, family membership, masks, and gradients."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent / "jobs"))
import selector_loss as annual  # noqa: E402

dates = [dt.date(1980, 1, 1) + dt.timedelta(days=index) for index in range(5844)]
years = np.asarray([date.year - 1980 for date in dates], dtype=np.int64)
valid = np.asarray([
    not (date.month == 12 and date.day == 31 and date.year % 4 == 0)
    for date in dates
])
observed = torch.ones((1, 5844, 3), dtype=torch.float32)
generated = observed.unsqueeze(0).repeat(2, 1, 1, 1).clone().requires_grad_(True)
loss, components = annual.selector_aligned_annual_loss(
    generated, observed, [years], [valid]
)
if set(components) != set(annual.FAMILY_KEYS) or float(loss) != 0.0:
    raise RuntimeError("identity loss or exact family registry failed")

precip_scale = annual._scaled(torch.tensor(1.0), torch.tensor(0.0), "precipitation", False)
expected = abs(np.log(1.1) - np.log(0.1)) / 0.25
if not np.isclose(float(precip_scale), expected, rtol=1e-6):
    raise RuntimeError("precipitation +0.1/log/0.25 selector scale drift")
if float(annual._scaled(torch.tensor(2.0), torch.tensor(1.0), "temperature_location", False)) != 1.0:
    raise RuntimeError("temperature location must remain raw degrees C")
if float(annual._scaled(torch.tensor(1.0), torch.tensor(0.5), "temperature_dispersion", False)) != 1.0:
    raise RuntimeError("temperature dispersion /0.5 scale drift")
if not np.isclose(float(annual._scaled(torch.tensor(0.2), torch.tensor(0.1), "dependence", False)), 1.0):
    raise RuntimeError("correlation /0.1 scale drift")

constant_left = torch.ones(16, requires_grad=True)
constant_right = torch.ones(16)
constant_correlation = annual.correlation(constant_left, constant_right)
constant_correlation.backward()
if constant_left.grad is None or not bool(torch.isfinite(constant_left.grad).all()):
    raise RuntimeError("constant-series correlation gradient is not finite")

perturbed = generated.detach().clone()
perturbed[:, :, :365, 0] *= 3.0
changed = annual.selector_aligned_annual_components(
    perturbed, observed, [years], [valid], squared=False
)
if float(changed["annual_location"]) <= 0.0:
    raise RuntimeError("annual precipitation q95/location family is inactive")

train = generated.clone()
train[:, :, :365, 0] *= 1.01
train_loss, _ = annual.selector_aligned_annual_loss(train, observed, [years], [valid])
train_loss.backward()
if generated.grad is None or not bool(torch.isfinite(generated.grad).all()):
    raise RuntimeError("selector-aligned annual objective lost its gradient")

broken = valid.copy()
broken[0] = False
try:
    annual.annual_series(observed[0], years, broken)
except RuntimeError:
    pass
else:
    raise RuntimeError("364-observation year passed eligibility")

# Each of the six order/dependence component paths is independently active.
axis = torch.arange(16, dtype=torch.float32)
target_annual = torch.stack(
    (axis.square() + 1.0, torch.sin(axis / 2.0) * 8.0 + axis, torch.cos(axis / 3.0) * 5.0 - axis / 3.0),
    dim=-1,
)
candidate_annual = target_annual.unsqueeze(0).repeat(2, 1, 1)
expected_lag = ("annual_lag.precipitation", "annual_lag.tmax", "annual_lag.tmin")
for field, name in enumerate(expected_lag):
    changed = candidate_annual.clone()
    changed[:, :, field] = changed[:, torch.tensor([0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 15]), field]
    paths = annual.lag_component_paths(changed, target_annual, squared=False)
    if float(paths[name]) <= 0.0:
        raise RuntimeError(f"inactive lag component: {name}")
    if any(float(paths[other]) != 0.0 for other in expected_lag if other != name):
        raise RuntimeError(f"lag perturbation leaked into unmodified fields: {name}")

expected_pairs = (
    "annual_cross_field_dependence.precipitation_tmax",
    "annual_cross_field_dependence.precipitation_tmin",
    "annual_cross_field_dependence.tmax_tmin",
)
for pair_index, name in enumerate(expected_pairs):
    changed = candidate_annual.clone()
    left, right = annual.PAIRS[pair_index]
    changed[:, :, right] = torch.roll(changed[:, :, right], shifts=3 + pair_index, dims=1)
    paths = annual.cross_field_component_paths(changed, target_annual, squared=False)
    if float(paths[name]) <= 0.0:
        raise RuntimeError(f"inactive annual cross-field component: {name}")

# Reject pooled-member scoring: within-member correlations are both -1 while
# the large between-member shift makes the flattened correlation positive.
x = torch.stack((axis, axis + 100.0))
y = torch.stack((15.0 - axis, 115.0 - axis))
memberwise = annual.correlation(x, y).mean()
pooled = annual.correlation(x.flatten(), y.flatten())
if not (float(memberwise) < -0.99 and float(pooled) > 0.9):
    raise RuntimeError("member-wise-vs-pooled correlation fixture failed")
print("A10M5R13-SELECTOR-LOSS-TEST-PASS")
