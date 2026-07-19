#!/usr/bin/env python3
"""Verify the normative A10 Daymet calendar profile and spec bindings."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
SPECIFICATIONS = REPO / "docs/specifications"
PROFILE = SPECIFICATIONS / "a10-daymet-calendar-profile-v1.json"


def dates_between(start: dt.date, end: dt.date) -> list[dt.date]:
    return [start + dt.timedelta(days=index) for index in range((end - start).days + 1)]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    require(profile["profile_id"] == "daymet_official_365_v1", "profile identity drift")
    require(profile["source_calendar"]["leap_year_february_29"] == "observed", "February 29 drift")
    require(profile["source_calendar"]["leap_year_december_31"] == "absent", "December 31 drift")

    fit = profile["fit_period_example"]
    fit_dates = dates_between(dt.date.fromisoformat(fit["start_date_inclusive"]), dt.date.fromisoformat(fit["end_date_inclusive"]))
    expected_missing = [dt.date(year, 12, 31) for year in range(1980, 2010) if dt.date(year, 12, 31).timetuple().tm_yday == 366]
    require(len(fit_dates) == fit["calendar_axis_rows"] == 10958, "fit calendar count drift")
    require([date.isoformat() for date in expected_missing] == fit["unobserved_dates"], "fit missing-date drift")
    require(len(fit_dates) - len(expected_missing) == fit["observed_rows"] == 10950, "fit observed count drift")
    require(all(dt.date(year, 2, 29) in fit_dates for year in (1980, 1984, 1988, 1992, 1996, 2000, 2004, 2008)), "fit February 29 missing")

    window = profile["window_example"]
    window_start = dt.date.fromisoformat(window["start_inclusive"])
    window_end = dt.date.fromisoformat(window["end_exclusive"])
    window_dates = dates_between(window_start, window_end - dt.timedelta(days=1))
    window_missing = [date for date in expected_missing if window_start <= date < window_end]
    require(len(window_dates) == window["calendar_axis_rows"] == 2922, "window calendar count drift")
    require([date.isoformat() for date in window_missing] == window["unobserved_dates"], "window missing-date drift")
    require(len(window_dates) - len(window_missing) == window["observed_rows"] == 2920, "window observed count drift")

    corpus_spec = (SPECIFICATIONS / "SPEC-A10-CORPUS.md").read_text(encoding="utf-8")
    climate_spec = (SPECIFICATIONS / "SPEC-A10-CLIMATE-STATISTICS-TRAINING.md").read_text(encoding="utf-8")
    for required in ("February 29 is present", "December 31 is absent", "all-calendar-row-observed"):
        require(required in corpus_spec, f"corpus spec omits {required!r}")
    for required in ("February 29 is observed", "leap-year December 31", "2,920 observed target rows"):
        require(required in climate_spec, f"climate spec omits {required!r}")
    print("A10-DAYMET-CALENDAR-PROFILE-VERIFIED")


if __name__ == "__main__":
    main()
