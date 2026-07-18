#!/usr/bin/env python3
"""Verify the terminal A10M5R1 evidence relationships."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LIMIT = 2_147_483_648


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    r1 = read(ROOT / "raw-r1/results/memory-attribution/evidence.json")
    acceptance = read(ROOT / "toolkit/evidence/results/acceptance/evidence.json")
    benchmark = read(ROOT / "toolkit/evidence/results/acceptance/benchmark.json")
    expected = json.loads((ROOT / "jobs/expected-identities.json").read_text(encoding="utf-8"))
    terminal = read(ROOT / "toolkit/terminal.json")
    cleanup = read(ROOT / "toolkit/cleanup.json")

    inference = [row for row in r1["variants"] if row.get("exact_reference_identity") is True]
    assert inference and all(row["rss_limit_pass"] for row in inference)
    assert max(row["time_v"]["maximum_resident_set_bytes"] for row in inference) < LIMIT
    assert r1["reference"]["export_bytes"] < 262_144_000

    assert acceptance["verdict"] == "PASS"
    assert all(acceptance["gates"].values())
    scientific = acceptance["scientific_gates"]
    assert scientific["candidate_identity_exact"] is True
    assert all(value is True for key, value in scientific.items() if key != "absolute_safeguards")
    assert scientific["absolute_safeguards"] is False
    assert acceptance["cold_start_seconds"] <= 15.0
    assert acceptance["export_bytes"] <= 262_144_000
    assert acceptance["runtime_ratio_max"] < 5.0

    observed = [
        {key: row[key] for key in ("station_id", "horizon_years", "candidate_identity")}
        for row in benchmark["rows"]
    ]
    assert observed == expected
    assert all(row["complete"] and row["runtime_class"] == "PASS" for row in benchmark["rows"])
    assert terminal["terminal"] == "LEMHI-TOOLKIT-RUN-CLOSED"
    assert cleanup["remote_absent"] is True
    assert cleanup["job_local_cleanup"] == "verified_absent"
    print("A10M5R1 verifier: PASS")


if __name__ == "__main__":
    main()
