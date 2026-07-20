#!/usr/bin/env python3
"""Exercise all 188 differentiable selector counterparts and gradients."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

package = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(package / "artifacts/jobs"))
import aligned_objective as aligned  # noqa: E402

dates = np.arange(np.datetime64("1980-01-01"), np.datetime64("1996-01-01"))
years_absolute = dates.astype("datetime64[Y]").astype(int) + 1970
years = years_absolute - 1980
months = dates.astype("datetime64[M]").astype(int) % 12
text = dates.astype(str)
valid = np.asarray([
    not value.endswith("-12-31") or int(value[:4]) % 4 != 0
    for value in text
], dtype=bool)
if (len(dates), int(valid.sum())) != (5844, 5840):
    raise RuntimeError("test calendar drift")

phase = torch.linspace(0.0, 32.0 * torch.pi, 5844)
observed = torch.stack((
    2.0 + 1.5 * torch.sin(phase).square(),
    18.0 + 8.0 * torch.sin(phase),
    8.0 + 6.0 * torch.sin(phase),
), dim=-1).unsqueeze(0)
generated = observed.unsqueeze(0).repeat(2, 1, 1, 1).clone().requires_grad_(True)
soft_wet = torch.sigmoid((generated[..., 0] - 1.0) / 0.1)
hard_wet = (generated[..., 0] >= 1.0).to(generated.dtype)
wet = soft_wet + (hard_wet - soft_wet).detach()
components = aligned.aligned_components(
    generated, wet, observed, [months], [years], [valid],
    gradient_surrogate=True,
)
if tuple(components) != aligned.metric_keys() or len(components) != 188:
    raise RuntimeError("aligned objective did not cover exact selector registry")
loss = torch.stack(tuple(components.values())).mean()
loss.backward()
if generated.grad is None or not bool(torch.isfinite(generated.grad).all()):
    raise RuntimeError("aligned 188-metric objective lost its gradient")
perturbed = generated.detach().clone()
perturbed[..., 0] *= 1.1
perturbed_soft_wet = torch.sigmoid((perturbed[..., 0] - 1.0) / 0.1)
perturbed_hard_wet = (perturbed[..., 0] >= 1.0).to(perturbed.dtype)
perturbed_wet = perturbed_soft_wet + (
    perturbed_hard_wet - perturbed_soft_wet
).detach()
train_components = aligned.aligned_components(
    perturbed, perturbed_hard_wet, observed, [months], [years], [valid],
    gradient_surrogate=True,
)
checkpoint_components = aligned.aligned_components(
    perturbed, perturbed_wet, observed, [months], [years], [valid],
    gradient_surrogate=False,
)
if any(
    not torch.equal(train_components[key], checkpoint_components[key])
    for key in aligned.metric_keys()
):
    raise RuntimeError("training/checkpoint 188-component absolute loss drift")
if set(aligned.scale_kind(key) for key in components) != {
    "log_precipitation", "coefficient_of_variation", "skew", "probability",
    "correlation", "temperature_mean_c", "temperature_standard_deviation_c",
}:
    raise RuntimeError("aligned selector scale registry incomplete")
print("A10M5R14-ALIGNED-OBJECTIVE-TEST-PASS")
