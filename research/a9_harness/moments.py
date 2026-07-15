"""Analytic monthly budgets and frozen deterministic quadrature."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping

from .errors import require

QUADRATURE_ID = "composite_simpson_4096_v1"
QUADRATURE_ORDER = 4096
QUADRATURE_TOLERANCE = 1.0e-10


@dataclass(frozen=True)
class MonthlyMoments:
    days: int
    daily_mean: float
    daily_variance: float
    occurrence_amount_variance: float
    covariance_contribution: float
    total_mean: float
    total_variance: float


def bernoulli_gamma_daily(p_wet: float, shape: float, scale: float) -> tuple[float, float]:
    require(0.0 <= p_wet <= 1.0, "PROBABILITY_SUPPORT", str(p_wet))
    require(shape > 0.0 and scale > 0.0, "GAMMA_SUPPORT", f"{shape},{scale}")
    amount_mean = shape * scale
    amount_variance = shape * scale * scale
    second = amount_variance + amount_mean * amount_mean
    daily_mean = p_wet * amount_mean
    daily_variance = p_wet * second - daily_mean * daily_mean
    return daily_mean, daily_variance


def monthly_moments(
    days: int,
    daily_mean: float,
    daily_variance: float,
    autocovariance_by_lag: Mapping[int, float],
) -> MonthlyMoments:
    require(days in {28, 29, 30, 31}, "MONTH_LENGTH", str(days))
    require(math.isfinite(daily_mean) and daily_mean >= 0.0, "DAILY_MEAN_SUPPORT", str(daily_mean))
    require(math.isfinite(daily_variance) and daily_variance >= 0.0, "DAILY_VARIANCE_SUPPORT", str(daily_variance))
    covariance = 0.0
    for lag, value in autocovariance_by_lag.items():
        require(1 <= lag < days and math.isfinite(value), "AUTOCOVARIANCE_SUPPORT", f"{lag}:{value}")
        covariance += 2.0 * (days - lag) * value
    independent = days * daily_variance
    total_variance = independent + covariance
    require(total_variance >= -QUADRATURE_TOLERANCE, "MONTHLY_VARIANCE_NEGATIVE", str(total_variance))
    return MonthlyMoments(
        days=days,
        daily_mean=daily_mean,
        daily_variance=daily_variance,
        occurrence_amount_variance=independent,
        covariance_contribution=covariance,
        total_mean=days * daily_mean,
        total_variance=max(0.0, total_variance),
    )


def reconcile_moments(moment: MonthlyMoments, claimed_mean: float, claimed_variance: float, tolerance: float = QUADRATURE_TOLERANCE) -> None:
    require(abs(moment.total_mean - claimed_mean) <= tolerance, "MONTHLY_MEAN_MISMATCH", str(moment.days))
    require(abs(moment.total_variance - claimed_variance) <= tolerance, "MONTHLY_VARIANCE_MISMATCH", str(moment.days))


def deterministic_quadrature(function: Callable[[float], float], lower: float, upper: float) -> float:
    """Composite Simpson integration with a frozen even order."""

    require(math.isfinite(lower) and math.isfinite(upper) and lower < upper, "QUADRATURE_BOUNDS", f"{lower},{upper}")
    step = (upper - lower) / QUADRATURE_ORDER
    total = function(lower) + function(upper)
    for index in range(1, QUADRATURE_ORDER):
        value = function(lower + index * step)
        require(math.isfinite(value), "QUADRATURE_NONFINITE", str(index))
        total += (4.0 if index % 2 else 2.0) * value
    result = total * step / 3.0
    require(math.isfinite(result), "QUADRATURE_NONFINITE", "result")
    return result

