"""USCRN-style five-minute event segmentation and descriptor vectors."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, Mapping, Sequence

from .errors import HarnessError, require


@dataclass(frozen=True)
class FiveMinuteInterval:
    end: datetime
    precipitation_mm: float | None
    air_temperature_c: float | None = None

    def __post_init__(self) -> None:
        if self.precipitation_mm is not None:
            require(math.isfinite(self.precipitation_mm) and self.precipitation_mm >= 0.0, "INTERVAL_PRECIP_INVALID", self.end.isoformat())
        if self.air_temperature_c is not None:
            require(math.isfinite(self.air_temperature_c), "INTERVAL_TEMPERATURE_INVALID", self.end.isoformat())


def _season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def _valid_zero_window(intervals: list[FiveMinuteInterval], start: int, end: int) -> bool:
    return end - start == 72 and all(item.precipitation_mm == 0.0 for item in intervals[start:end])


def segment_events(intervals: Iterable[FiveMinuteInterval]) -> tuple[list[dict[str, object]], int]:
    """Return complete six-hour-separated events and invalidated event count."""

    rows = list(intervals)
    for previous_row, current in zip(rows, rows[1:]):
        require(current.end - previous_row.end == timedelta(minutes=5), "INTERVAL_DISCONTINUITY", current.end.isoformat())
    positives = [index for index, row in enumerate(rows) if row.precipitation_mm is not None and row.precipitation_mm > 0.0]
    if not positives:
        return [], 0

    groups: list[list[int]] = [[positives[0]]]
    invalid_links: set[int] = set()
    for index in positives[1:]:
        previous_index = groups[-1][-1]
        gap = rows[previous_index + 1 : index]
        if len(gap) >= 72 and all(item.precipitation_mm == 0.0 for item in gap):
            groups.append([index])
        elif any(item.precipitation_mm is None for item in gap):
            invalid_links.add(len(groups) - 1)
            groups.append([index])
            invalid_links.add(len(groups) - 1)
        else:
            groups[-1].append(index)

    events: list[dict[str, object]] = []
    invalid = 0
    for group_index, group in enumerate(groups):
        first, last = group[0], group[-1]
        valid_before = first >= 72 and _valid_zero_window(rows, first - 72, first)
        valid_after = last + 73 <= len(rows) and _valid_zero_window(rows, last + 1, last + 73)
        if group_index in invalid_links or not (valid_before and valid_after):
            invalid += 1
            continue
        path = rows[first : last + 1]
        require(all(row.precipitation_mm is not None for row in path), "EVENT_MISSING_PATH", rows[first].end.isoformat())
        depth_values = [row.precipitation_mm for row in path if row.precipitation_mm is not None]
        depth = sum(depth_values)
        duration_minutes = (rows[last].end - rows[first].end).total_seconds() / 60.0 + 5.0
        positive_rates = []
        for index in group:
            precipitation = rows[index].precipitation_mm
            if precipitation is None:
                raise HarnessError("EVENT_POSITIVE_MISSING", rows[index].end.isoformat())
            positive_rates.append(precipitation * 12.0)
        peak_rate = max(positive_rates)
        peak_group_offset = positive_rates.index(peak_rate)
        peak_index = group[peak_group_offset]
        time_to_peak = ((peak_index - first) * 5.0 + 2.5) / duration_minutes
        mean_rate = depth / (duration_minutes / 60.0)
        temperatures = [row.air_temperature_c for row in path if row.air_temperature_c is not None]
        events.append(
            {
                "start": (rows[first].end - timedelta(minutes=5)).isoformat(),
                "end": rows[last].end.isoformat(),
                "depth_mm": depth,
                "duration_minutes": duration_minutes,
                "time_to_peak_fraction": time_to_peak,
                "peak_ratio": peak_rate / mean_rate,
                "season": _season((rows[first].end - timedelta(minutes=5)).month),
                "cold_context": bool(temperatures and min(temperatures) <= 0.0),
            }
        )
    return events, invalid


def descriptor_checks(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    require(bool(events), "EVENTS_REQUIRED", "descriptor checks")
    time_to_peak = [float(event["time_to_peak_fraction"]) for event in events]
    depths = [float(event["depth_mm"]) for event in events]
    ratios = [float(event["peak_ratio"]) for event in events]
    boundary_mass = sum(value <= 0.0 or value >= 1.0 for value in time_to_peak) / len(time_to_peak)
    dependence = _correlation(depths, ratios)
    return {
        "time_to_peak_boundary_mass": boundary_mass,
        "depth_peak_ratio_correlation": dependence,
        "time_to_peak_pass": boundary_mass < 0.25,
        "joint_dependence_available": len(set(depths)) > 1 and len(set(ratios)) > 1,
    }


def _correlation(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    vx = sum((value - mx) ** 2 for value in x)
    vy = sum((value - my) ** 2 for value in y)
    if vx == 0.0 or vy == 0.0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(vx * vy)
