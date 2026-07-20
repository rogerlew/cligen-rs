#!/usr/bin/env python3
"""Exercise the 16-year Daymet calendar and boundary contract."""

from __future__ import annotations

import dataclasses
import datetime as dt
import importlib.util
import sys
import types
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class CalendarWindow:
    input_start: int
    days: int
    first_year: int
    month_index: object
    year_index: object
    valid_index: object


@dataclasses.dataclass
class CalendarRecord:
    record: object
    windows: list[CalendarWindow]


stub = types.ModuleType("inherited_climate_core")
stub.CalendarWindow = CalendarWindow
stub.CalendarRecord = CalendarRecord
stub.__all__ = ["CalendarWindow", "CalendarRecord"]
sys.modules["inherited_climate_core"] = stub
path = Path(__file__).parent / "jobs" / "climate_core.py"
spec = importlib.util.spec_from_file_location("r13_climate", path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

start, stop = dt.date(1980, 1, 1), dt.date(2010, 1, 1)
dates = [start + dt.timedelta(days=index) for index in range((stop - start).days)]
observed = [not (date.month == 12 and date.day == 31 and date.year % 4 == 0) for date in dates]
document = {
    "dates": [date.isoformat() for date in dates],
    "source_observed": observed,
    "fields": {
        name: [1.0 if keep else None for keep in observed]
        for name in ("prcp", "tmax", "tmin")
    },
}
windows = module._long_windows(document, 16)
if len(windows) != 13 or [row.first_year for row in windows] != list(range(1981, 1994)):
    raise RuntimeError("expected 13 rolling 16-year origins")
for window in windows:
    if window.days != 5844 or int(window.valid_index.sum()) != 5840:
        raise RuntimeError("5844-axis/5840-observed contract drift")
    for ordinal in range(16):
        if int((window.valid_index & (window.year_index == ordinal)).sum()) != 365:
            raise RuntimeError("annual mask eligibility drift")
first = windows[0]
target_dates = dates[first.input_start + 1 : first.input_start + 1 + first.days]
lookup = {date: index for index, date in enumerate(target_dates)}
if not first.valid_index[lookup[dt.date(1984, 2, 29)]]:
    raise RuntimeError("observed leap-day was masked")
if first.valid_index[lookup[dt.date(1984, 12, 31)]]:
    raise RuntimeError("structural leap-year December 31 was observed")
print("A10M5R13-CALENDAR-TEST-PASS")
