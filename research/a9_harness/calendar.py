"""Frozen civil-calendar rules and nested Gregorian horizons."""

from __future__ import annotations

import calendar as calendar_module
from datetime import date, timedelta
from typing import Iterable

from .errors import HarnessError, require


def daymet_official_date(year: int, ordinal: int) -> date:
    """Map Daymet's 365 ordinals: retain leap day and omit leap Dec 31."""

    require(1 <= ordinal <= 365, "DAYMET_ORDINAL_RANGE", str(ordinal))
    return date(year, 1, 1) + timedelta(days=ordinal - 1)


def daymet_expected_dates(year: int) -> list[date]:
    dates = [daymet_official_date(year, ordinal) for ordinal in range(1, 366)]
    if calendar_module.isleap(year):
        require(dates[-1] == date(year, 12, 30), "DAYMET_CALENDAR_INTERNAL", str(year))
    else:
        require(dates[-1] == date(year, 12, 31), "DAYMET_CALENDAR_INTERNAL", str(year))
    return dates


def completeness(valid_dates: Iterable[date], year: int) -> dict[str, object]:
    expected = daymet_expected_dates(year)
    valid = set(valid_dates)
    unexpected = valid - set(expected)
    require(not unexpected, "DAYMET_UNEXPECTED_DATE", min(unexpected).isoformat() if unexpected else "")
    missing = [day for day in expected if day not in valid]
    longest = 0
    run = 0
    for day in expected:
        if day in valid:
            run = 0
        else:
            run += 1
            longest = max(longest, run)
    fraction = len(valid) / len(expected)
    return {
        "available_fraction": fraction,
        "complete": fraction >= 0.90 and longest <= 3,
        "expected_days": len(expected),
        "missing_days": len(missing),
        "longest_missing_run": longest,
    }


def gregorian_dates(start_year: int, years: int) -> list[date]:
    require(years > 0, "HORIZON_INVALID", str(years))
    start = date(start_year, 1, 1)
    end = date(start_year + years, 1, 1)
    return [start + timedelta(days=offset) for offset in range((end - start).days)]


def nested_prefix(rows_100: list[dict[str, object]], start_year: int) -> list[dict[str, object]]:
    cutoff = date(start_year + 30, 1, 1).isoformat()
    return [row for row in rows_100 if str(row["date"]) < cutoff]


def assert_contiguous_dates(rows: list[dict[str, object]]) -> None:
    try:
        dates = [date.fromisoformat(str(row["date"])) for row in rows]
    except ValueError as error:
        raise HarnessError("INVALID_DATE", str(error)) from error
    for previous, current in zip(dates, dates[1:]):
        require(current == previous + timedelta(days=1), "DATE_DISCONTINUITY", f"{previous}/{current}")

