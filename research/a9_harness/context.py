"""Typed daily precipitation context and declared mock consumers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .errors import require


@dataclass(frozen=True)
class DailyContext:
    wet0: bool
    r1mm: bool
    occurrence_state: str
    wet_amount_mm: float
    amount_quantile: float | None
    event_duration_minutes: float | None
    time_to_peak_fraction: float | None
    peak_ratio: float | None
    seasonal_state: str
    latent_state: str | None
    fit_id: str
    candidate_class: str


@dataclass(frozen=True)
class Consumer:
    name: str
    declared_fields: tuple[str, ...]
    function: Callable[[DailyContext], float]

    def evaluate(self, context: DailyContext, requested_fields: tuple[str, ...]) -> dict[str, object]:
        require(set(requested_fields) <= set(self.declared_fields), "UNDECLARED_CONTEXT_FIELD", self.name)
        return {
            "consumer": self.name,
            "value": self.function(context),
            "used_fields": list(requested_fields),
        }


def mock_consumers() -> dict[str, Consumer]:
    return {
        "temperature": Consumer("temperature", ("wet0", "seasonal_state"), lambda c: 15.0 - (2.0 if c.wet0 else 0.0)),
        "humidity": Consumer("humidity", ("wet0", "wet_amount_mm"), lambda c: 40.0 + (20.0 if c.wet0 else 0.0) + min(c.wet_amount_mm, 20.0) / 2.0),
        "radiation": Consumer("radiation", ("wet0",), lambda c: 18.0 - (5.0 if c.wet0 else 0.0)),
        "wind": Consumer("wind", ("event_duration_minutes",), lambda c: 2.0 + (0.01 * (c.event_duration_minutes or 0.0))),
    }

