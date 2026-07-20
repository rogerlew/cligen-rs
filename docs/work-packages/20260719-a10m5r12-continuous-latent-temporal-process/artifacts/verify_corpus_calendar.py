#!/usr/bin/env python3
"""Publish the revision-2 A10 calendar/missingness consumer preflight."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PROFILE = REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json"
PARENT = (
    REPO
    / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio"
    / "artifacts/verify_corpus_calendar.py"
)
FIELDS = ("prcp", "tmax", "tmin", "srad")
FIXTURE_DATES = (
    "1984-02-28",
    "1984-02-29",
    "1984-03-01",
    "1984-12-30",
    "1984-12-31",
    "1985-01-01",
    "1987-12-31",
    "1988-01-01",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def parent_verifier() -> Any:
    spec = importlib.util.spec_from_file_location("a10_calendar_parent", PARENT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load parent calendar verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(document: dict[str, Any]) -> dict[str, Any]:
    indices = {value: index for index, value in enumerate(document["dates"])}
    rows = []
    for date in FIXTURE_DATES:
        index = indices[date]
        observed = bool(document["source_observed"][index])
        present = {
            field: document["fields"][field][index] is not None for field in FIELDS
        }
        if any(value != observed for value in present.values()):
            raise RuntimeError("fixture required-field mask differs from source mask")
        rows.append(
            {
                "date": date,
                "required_fields_present": present,
                "source_observed": observed,
            }
        )
    if not (
        rows[1]["source_observed"]
        and not rows[4]["source_observed"]
        and rows[-2]["source_observed"]
        and rows[-1]["source_observed"]
    ):
        raise RuntimeError("calendar boundary fixture semantics failed")
    return {
        "point_id": document["point_id"],
        "rows": rows,
        "spans_absent_leap_december_31": True,
        "spans_observed_february_29": True,
        "spans_window_end_exclusive": ["1987-12-31", "1988-01-01"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-tar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    parent = parent_verifier()
    roles = {"candidate_fit": 0, "fit_validation": 0}
    minimum_counts = {"core": 10**9, "physics": 10**9}
    fixture_record = None
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
                    parent.verify_document(document, profile)
                    roles[role] += 1
                    observed = [bool(value) for value in document["source_observed"]]
                    dates = [dt.date.fromisoformat(value) for value in document["dates"]]
                    for name, fields in (
                        ("core", ("prcp", "tmax", "tmin")),
                        ("physics", FIELDS),
                    ):
                        counts: dict[tuple[int, int], int] = {}
                        for index, date in enumerate(dates):
                            keep = observed[index] and all(
                                document["fields"][field][index] is not None
                                for field in fields
                            )
                            if keep:
                                key = (date.year, date.month)
                                counts[key] = counts.get(key, 0) + 1
                        if len(counts) != 360:
                            raise RuntimeError("year-month eligibility cell count drift")
                        minimum_counts[name] = min(minimum_counts[name], min(counts.values()))
                    if fixture_record is None and role == "candidate_fit":
                        fixture_record = fixture(document)
    if roles != {"candidate_fit": 1200, "fit_validation": 240}:
        raise RuntimeError(f"Daymet role roster mismatch: {roles}")
    if fixture_record is None or min(minimum_counts.values()) < 28:
        raise RuntimeError("calendar consumer preflight incomplete")
    expected = profile["fit_period_example"]
    window = profile["window_example"]
    result = {
        "corpus": {
            "bytes": options.corpus_tar.stat().st_size,
            "sha256": digest(options.corpus_tar),
        },
        "counts": {
            "calendar_axis_rows_per_point": expected["calendar_axis_rows"],
            "core_observed_rows_per_point": expected["observed_rows"],
            "physics_observed_rows_per_point": expected["observed_rows"],
            "roles": roles,
        },
        "fixture": fixture_record,
        "mask_composition": {
            "core": "source_observed and prcp present and tmax present and tmin present",
            "physics": "core and srad present",
        },
        "month_year_eligibility": {
            "core_minimum_observed_rows": minimum_counts["core"],
            "eligible": True,
            "physics_minimum_observed_rows": minimum_counts["physics"],
            "required_minimum_observed_rows": 28,
            "year_month_cells_per_point": 360,
        },
        "normalized_calendar_axis": profile["normalized_axis"],
        "profile_id": profile["profile_id"],
        "schema_version": 2,
        "source_bounds": {
            "end_inclusive": expected["end_date_inclusive"],
            "start_inclusive": expected["start_date_inclusive"],
        },
        "source_transform_id": profile["profile_id"],
        "unobserved_dates": expected["unobserved_dates"],
        "valid": True,
        "window": {
            "calendar_axis_rows": window["calendar_axis_rows"],
            "core_observed_rows": window["observed_rows"],
            "end_exclusive": window["end_exclusive"],
            "end_semantics": "exclusive",
            "physics_observed_rows": window["observed_rows"],
            "start_inclusive": window["start_inclusive"],
        },
    }
    options.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("A10M5R12-CALENDAR-PREFLIGHT-PASS")


if __name__ == "__main__":
    main()
