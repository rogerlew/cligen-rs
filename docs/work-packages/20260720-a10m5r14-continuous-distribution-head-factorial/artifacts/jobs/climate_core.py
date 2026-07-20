#!/usr/bin/env python3
"""R12 climate core with prospectively frozen 16-year calendar windows."""

from __future__ import annotations

import datetime as dt
import json
import tarfile
from typing import Any

import numpy as np

from inherited_climate_core import *  # noqa: F403
from inherited_climate_core import CalendarRecord, CalendarWindow


def _long_windows(document: dict[str, Any], years: int) -> list[CalendarWindow]:
    if years != 16:
        raise RuntimeError("A10M5R13 requires exactly 16 calendar years")
    dates = [dt.date.fromisoformat(text) for text in document["dates"]]
    positions = {date: index for index, date in enumerate(dates)}
    complete = np.asarray(document["source_observed"], dtype=bool)
    for field in ("prcp", "tmax", "tmin"):
        complete &= np.asarray(
            [value is not None for value in document["fields"][field]]
        )
    windows = []
    for first_year in range(dates[0].year, dates[-1].year - years + 2):
        start, stop = dt.date(first_year, 1, 1), dt.date(first_year + years, 1, 1)
        previous = start - dt.timedelta(days=1)
        if previous not in positions or stop not in positions:
            continue
        input_start, end = positions[previous], positions[stop]
        targets = dates[positions[start] : end]
        month = np.asarray([date.month - 1 for date in targets], dtype=np.int64)
        year = np.asarray([date.year - first_year for date in targets], dtype=np.int64)
        valid = complete[positions[start] : end].copy()
        if len(targets) != 5844 or set(year.tolist()) != set(range(16)):
            raise RuntimeError("16-year Gregorian axis mismatch")
        if int(valid.sum()) != 5840:
            raise RuntimeError("16-year Daymet core support must be exactly 5840")
        for ordinal in range(16):
            axis = year == ordinal
            if int(valid[axis].sum()) != 365:
                raise RuntimeError("each Daymet year must provide exactly 365 core rows")
            missing = [date for date, keep in zip(np.asarray(targets)[axis], valid[axis]) if not keep]
            if int(axis.sum()) == 366 and missing != [dt.date(first_year + ordinal, 12, 31)]:
                raise RuntimeError("leap-year Daymet null must be December 31")
            if int(axis.sum()) == 365 and missing:
                raise RuntimeError("common-year Daymet support is incomplete")
        support = [
            int((valid & (year == y) & (month == m)).sum())
            for y in range(16)
            for m in range(12)
        ]
        if min(support) >= 28:
            windows.append(
                CalendarWindow(input_start, len(targets), first_year, month, year, valid)
            )
    return windows


def attach_calendars(
    corpus, normalized, fit, validation, years
) -> tuple[list[CalendarRecord], list[CalendarRecord]]:
    lookup = {(record.role, record.point_id): record for record in (*fit, *validation)}
    attached = {}
    for shard in normalized["daymet_shards"]:
        with tarfile.open(corpus / shard["path"], "r:gz") as archive:
            for member in archive.getmembers():
                stream = archive.extractfile(member)
                if stream is None:
                    continue
                document = json.load(stream)
                key = (document["role"], document["point_id"])
                if key in lookup:
                    windows = _long_windows(document, years)
                    if len(windows) != 13:
                        raise RuntimeError("16-year Daymet roster must expose 13 origins")
                    if windows:
                        attached[key] = CalendarRecord(lookup[key], windows)
    fit_rows = [attached[(r.role, r.point_id)] for r in fit if (r.role, r.point_id) in attached]
    validation_rows = [attached[(r.role, r.point_id)] for r in validation if (r.role, r.point_id) in attached]
    if len(fit_rows) != len(fit) or len(validation_rows) != len(validation):
        raise RuntimeError("16-year calendar eligibility incomplete")
    return fit_rows, validation_rows
