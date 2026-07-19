#!/usr/bin/env python3
"""Verify the A10 portfolio corpus calendar and core/solar masks."""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import tarfile
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
PROFILE = REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json"
FIELDS = ("prcp", "tmax", "tmin", "srad")


def verify_document(document: dict[str, Any], profile: dict[str, Any]) -> None:
    expected = profile["fit_period_example"]
    window = profile["window_example"]
    dates = [dt.date.fromisoformat(value) for value in document["dates"]]
    start = dt.date.fromisoformat(expected["start_date_inclusive"])
    end = dt.date.fromisoformat(expected["end_date_inclusive"])
    expected_dates = [
        start + dt.timedelta(days=offset)
        for offset in range((end - start).days + 1)
    ]
    if dates != expected_dates:
        raise RuntimeError("normalized date axis is not complete proleptic Gregorian")
    observed = [bool(value) for value in document["source_observed"]]
    missing = [
        date
        for date, keep in zip(document["dates"], observed, strict=True)
        if not keep
    ]
    if len(document["dates"]) != expected["calendar_axis_rows"]:
        raise RuntimeError("calendar-axis row count mismatch")
    if sum(observed) != expected["observed_rows"]:
        raise RuntimeError("observed row count mismatch")
    if missing != expected["unobserved_dates"]:
        raise RuntimeError("unobserved date profile mismatch")
    field_masks: dict[str, list[bool]] = {}
    for field in FIELDS:
        values = document["fields"][field]
        present = [value is not None for value in values]
        field_masks[field] = present
        if present != observed:
            raise RuntimeError(f"{field} mask differs from source_observed")
        if field == "srad" and any(
            value is not None and value <= 0 for value in values
        ):
            raise RuntimeError("solar radiation is nonpositive")
    core = [
        keep and field_masks["prcp"][index] and field_masks["tmax"][index]
        and field_masks["tmin"][index]
        for index, keep in enumerate(observed)
    ]
    physics = [
        keep and field_masks["srad"][index]
        for index, keep in enumerate(core)
    ]
    if core != observed or physics != observed:
        raise RuntimeError("core or physics target mask differs from source_observed")

    leap_days = [
        dt.date(year, 2, 29)
        for year in range(start.year, end.year + 1)
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    ]
    date_index = {date: index for index, date in enumerate(dates)}
    if any(not observed[date_index[date]] for date in leap_days):
        raise RuntimeError("Daymet February 29 must be source-observed")

    window_start = dt.date.fromisoformat(window["start_inclusive"])
    window_end = dt.date.fromisoformat(window["end_exclusive"])
    window_indices = [
        index for index, date in enumerate(dates)
        if window_start <= date < window_end
    ]
    if len(window_indices) != window["calendar_axis_rows"]:
        raise RuntimeError("representative-window axis count mismatch")
    if sum(observed[index] for index in window_indices) != window["observed_rows"]:
        raise RuntimeError("representative-window observed count mismatch")
    window_missing = [
        dates[index].isoformat() for index in window_indices if not observed[index]
    ]
    if window_missing != window["unobserved_dates"]:
        raise RuntimeError("representative-window missing-date profile mismatch")
    if dates[window_indices[-1]] != window_end - dt.timedelta(days=1):
        raise RuntimeError("day before exclusive window end was not included")
    if window_end not in date_index or date_index[window_end] in window_indices:
        raise RuntimeError("exclusive window end was not retained outside the window")

    for mask_name, mask in (("core", core), ("physics", physics)):
        month_counts: dict[tuple[int, int], int] = {}
        for date, keep in zip(dates, mask, strict=True):
            if keep:
                key = (date.year, date.month)
                month_counts[key] = month_counts.get(key, 0) + 1
        if len(month_counts) != 30 * 12 or min(month_counts.values()) < 28:
            raise RuntimeError(f"{mask_name} mask has an ineligible year-month")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-tar", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    roles = {"candidate_fit": 0, "fit_validation": 0}
    solar_missing = {"candidate_fit": 0, "fit_validation": 0}
    with tarfile.open(options.corpus_tar, "r:") as outer:
        for member in outer.getmembers():
            if not member.name.endswith(".tar.gz") or "/daymet-v2/" not in member.name:
                continue
            stream = outer.extractfile(member)
            if stream is None:
                raise RuntimeError("outer corpus member cannot be read")
            with tarfile.open(fileobj=io.BytesIO(stream.read()), mode="r:gz") as inner:
                for item in inner.getmembers():
                    document_stream = inner.extractfile(item)
                    if document_stream is None:
                        continue
                    document = json.load(document_stream)
                    role = document["role"]
                    if role not in roles:
                        continue
                    verify_document(document, profile)
                    roles[role] += 1
                    solar_missing[role] += sum(
                        value is None for value in document["fields"]["srad"]
                    )
    if roles != {"candidate_fit": 1200, "fit_validation": 240}:
        raise RuntimeError(f"Daymet role roster mismatch: {roles}")
    expected_missing = len(profile["fit_period_example"]["unobserved_dates"])
    if solar_missing != {
        "candidate_fit": roles["candidate_fit"] * expected_missing,
        "fit_validation": roles["fit_validation"] * expected_missing,
    }:
        raise RuntimeError(f"solar missing-value count mismatch: {solar_missing}")
    result = {
        "fields": list(FIELDS),
        "full_period": {
            "calendar_axis_rows": profile["fit_period_example"]["calendar_axis_rows"],
            "core_observed_rows": profile["fit_period_example"]["observed_rows"],
            "physics_observed_rows": profile["fit_period_example"]["observed_rows"],
        },
        "profile_id": profile["profile_id"],
        "representative_window": {
            "calendar_axis_rows": profile["window_example"]["calendar_axis_rows"],
            "core_observed_rows": profile["window_example"]["observed_rows"],
            "end_exclusive": profile["window_example"]["end_exclusive"],
            "physics_observed_rows": profile["window_example"]["observed_rows"],
        },
        "roles": roles,
        "solar_missing_values": solar_missing,
        "valid": True,
    }
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if options.output is not None:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = options.output.with_suffix(options.output.suffix + ".part")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(options.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
