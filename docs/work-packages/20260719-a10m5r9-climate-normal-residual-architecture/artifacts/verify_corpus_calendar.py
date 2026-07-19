#!/usr/bin/env python3
"""Verify the immutable A10 corpus tar against the canonical Daymet calendar profile."""

from __future__ import annotations

import argparse
import io
import json
import tarfile
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
PROFILE = REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json"


def verify_document(document: dict[str, Any], profile: dict[str, Any]) -> None:
    expected = profile["fit_period_example"]
    observed = document["source_observed"]
    missing = [date for date, keep in zip(document["dates"], observed, strict=True) if not keep]
    if len(document["dates"]) != expected["calendar_axis_rows"]:
        raise RuntimeError("calendar-axis row count mismatch")
    if sum(bool(value) for value in observed) != expected["observed_rows"]:
        raise RuntimeError("observed row count mismatch")
    if missing != expected["unobserved_dates"]:
        raise RuntimeError("unobserved date profile mismatch")
    for field in ("prcp", "tmax", "tmin"):
        present = [value is not None for value in document["fields"][field]]
        if present != observed:
            raise RuntimeError(f"{field} mask differs from source_observed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-tar", type=Path, required=True)
    options = parser.parse_args()
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    roles = {"candidate_fit": 0, "fit_validation": 0}
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
    if roles != {"candidate_fit": 1200, "fit_validation": 240}:
        raise RuntimeError(f"Daymet role roster mismatch: {roles}")
    print(json.dumps({"profile_id": profile["profile_id"], "roles": roles, "valid": True}, sort_keys=True))


if __name__ == "__main__":
    main()
