"""Prospectively frozen A10M5R3 family and capacity selectors."""

from __future__ import annotations

import math
import statistics
from typing import Any, Mapping, Sequence

FAMILIES = (
    "lognormal_wet_v2",
    "gamma_wet_v2",
    "lognormal_body_gpd_excess_v2",
)
SEEDS = (147031, 271828, 314159)
FAMILY_ARCHITECTURE = {"latent_dim": 64, "width": 128, "depth": 2}
CAPACITY_LADDER = {
    "P0": {"latent_dim": 32, "width": 128, "depth": 2, "nominal_parameters": 35_000},
    "P1": {"latent_dim": 80, "width": 160, "depth": 2, "nominal_parameters": 100_000},
    "P2": {"latent_dim": 144, "width": 288, "depth": 2, "nominal_parameters": 300_000},
    "P3": {"latent_dim": 272, "width": 544, "depth": 2, "nominal_parameters": 1_000_000},
    "P4": {"latent_dim": 480, "width": 960, "depth": 2, "nominal_parameters": 3_000_000},
}
SPLICE_THRESHOLD_MM = 20.0
SEED_NLL_SD_MAX = 0.15


class ContractError(ValueError):
    """A row or selection violates the prospective R3 contract."""


def parameter_count(family: str, latent: int, width: int, depth: int) -> int:
    if family not in FAMILIES or latent <= 0 or width <= 0 or depth != 2:
        raise ContractError("illegal family or architecture")
    head_outputs = 18 if family == "lognormal_body_gpd_excess_v2" else 15
    encoder = 14 * width + (depth - 1) * (width * width + width)
    gru = 3 * latent * width + 3 * latent * latent + 6 * latent
    head = (latent + 1) * head_outputs
    return encoder + gru + head


def _valid(row: Mapping[str, Any]) -> bool:
    gates = row.get("gates")
    return row.get("valid") is True and isinstance(gates, Mapping) and bool(gates) and all(gates.values())


def _finite(row: Mapping[str, Any], key: str) -> float:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"{key} must be finite")
    return float(value)


def select_family(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = {(family, seed) for family in FAMILIES for seed in SEEDS}
    actual = {(row.get("amount_family"), row.get("training_seed")) for row in rows}
    if len(rows) != 9 or actual != expected:
        raise ContractError("family matrix identity mismatch")
    ranking = []
    for family in FAMILIES:
        group = [row for row in rows if row["amount_family"] == family]
        if not all(_valid(row) for row in group):
            continue
        primary = [_finite(row, "validation_primary_nll") for row in group]
        ranking.append({
            "amount_family": family,
            "mean_primary_nll": statistics.fmean(primary),
            "mean_tail_score": statistics.fmean(_finite(row, "validation_tail_score") for row in group),
            "mean_stability": statistics.fmean(_finite(row, "validation_stability") for row in group),
            "primary_nll_population_sd": statistics.pstdev(primary),
        })
    ranking.sort(key=lambda row: (row["mean_primary_nll"], row["mean_tail_score"], row["mean_stability"], row["primary_nll_population_sd"], row["amount_family"]))
    if not ranking:
        raise ContractError("no calibrated family")
    return {"schema_version": 1, "winner": ranking[0]["amount_family"], "diagnostic_runner_up": ranking[1]["amount_family"] if len(ranking) > 1 else None, "ranking": ranking}


def _dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    keys = ("validation_primary_nll", "runtime_ratio_max", "peak_rss_bytes", "export_bytes", "gpu_fit_wall_seconds", "parameter_count")
    values = [(_finite(left, key), _finite(right, key)) for key in keys]
    return all(a <= b for a, b in values) and any(a < b for a, b in values)


def select_capacity(rows: Sequence[Mapping[str, Any]], family: str) -> dict[str, Any]:
    expected = set(CAPACITY_LADDER)
    actual = {row.get("capacity_id") for row in rows}
    if len(rows) != 5 or actual != expected or any(row.get("amount_family") != family or row.get("training_seed") != SEEDS[0] for row in rows):
        raise ContractError("capacity matrix identity mismatch")
    passing = [row for row in rows if _valid(row)]
    frontier = [row for row in passing if not any(_dominates(other, row) for other in passing if other is not row)]
    frontier.sort(key=lambda row: (_finite(row, "parameter_count"), str(row["capacity_id"])))
    if len(frontier) < 2:
        raise ContractError("fewer than two passing frontier points")
    if len(frontier) == 2:
        knee_index = 0
        distances = [0.0]
    else:
        xs = [math.log(_finite(row, "parameter_count")) for row in frontier]
        ys = [_finite(row, "validation_primary_nll") for row in frontier]
        x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
        xspan, yspan = max(x1 - x0, 1e-12), max(max(ys) - min(ys), 1e-12)
        xn = [(x - x0) / xspan for x in xs]
        yn = [(y - min(ys)) / yspan for y in ys]
        denominator = math.hypot(yn[-1] - yn[0], xn[-1] - xn[0]) or 1.0
        distances = [abs((yn[-1] - yn[0]) * xn[i] - (xn[-1] - xn[0]) * yn[i] + xn[-1] * yn[0] - yn[-1] * xn[0]) / denominator for i in range(len(frontier) - 1)]
        knee_index = min(range(len(frontier) - 1), key=lambda i: (-distances[i], _finite(frontier[i], "validation_primary_nll"), _finite(frontier[i], "parameter_count")))
    pair = [str(frontier[knee_index]["capacity_id"]), str(frontier[knee_index + 1]["capacity_id"])]
    return {"schema_version": 1, "amount_family": family, "frontier": [str(row["capacity_id"]) for row in frontier], "curvature_distances": distances, "knee": pair[0], "larger_neighbor": pair[1], "pair": pair}


def validate_pair(rows: Sequence[Mapping[str, Any]], family: str, pair: Sequence[str]) -> dict[str, Any]:
    expected = {(capacity, seed) for capacity in pair for seed in SEEDS}
    actual = {(row.get("capacity_id"), row.get("training_seed")) for row in rows}
    if len(pair) != 2 or len(rows) != 6 or actual != expected or any(row.get("amount_family") != family for row in rows):
        raise ContractError("frontier pair matrix identity mismatch")
    summaries = []
    for capacity in pair:
        group = [row for row in rows if row["capacity_id"] == capacity]
        values = [_finite(row, "validation_primary_nll") for row in group]
        sd = statistics.pstdev(values)
        summaries.append({"capacity_id": capacity, "primary_nll_mean": statistics.fmean(values), "primary_nll_population_sd": sd, "all_gates_pass": all(_valid(row) for row in group), "stable": sd <= SEED_NLL_SD_MAX})
    ready = all(row["all_gates_pass"] and row["stable"] for row in summaries)
    return {"schema_version": 1, "amount_family": family, "pair": list(pair), "summaries": summaries, "ready": ready, "disposition": "A10M5R3-CAPACITY-PAIR-READY" if ready else "HOLD-A10-NO-CAPACITY-PAIR"}
