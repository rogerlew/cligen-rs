#!/usr/bin/env python3
"""Verify A9a traceability, research schemas, and prospective boundaries."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DISPATCH_COMMIT = "5c7f5d271b93e953986b88f7987044c5270d6c61"
PACKAGE = ROOT / "docs/work-packages/20260715-a9a-successor-family-foundation"
SPEC = ROOT / "docs/specifications/SPEC-A9-RESEARCH-FOUNDATION.md"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def run(*args: str) -> bytes:
    try:
        return subprocess.check_output(args, cwd=ROOT, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        fail(f"command failed ({' '.join(args)}): {error.output.decode().strip()}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def verify_identity(record: dict[str, Any]) -> None:
    path = ROOT / record["path"]
    if not path.is_file():
        fail(f"identity path missing: {record['path']}")
    data = path.read_bytes()
    if len(data) != record["bytes"] or sha256(data) != record["sha256"]:
        fail(f"identity mismatch: {record['path']}")


def verify_authority() -> None:
    manifest = load(HERE / "authority-manifest-v1.json")
    if manifest["dispatch_commit"] != DISPATCH_COMMIT:
        fail("authority dispatch commit changed")
    if manifest["predecessor_terminal"] != "A8C-ROUTED-DAILY-RUNTIME-RETIRED":
        fail("wrong predecessor terminal")
    if len(manifest["files"]) != 25:
        fail("authority manifest must contain 25 exact files")
    for record in manifest["files"]:
        verify_identity(record)
    run("git", "cat-file", "-e", f"{DISPATCH_COMMIT}^{{commit}}")
    run("git", "merge-base", "--is-ancestor", DISPATCH_COMMIT, "HEAD")
    predecessor = (
        ROOT
        / "docs/work-packages/20260715-a8c1-routed-daily-retirement/package.md"
    ).read_text(encoding="utf-8")
    if "A8C-ROUTED-DAILY-RUNTIME-RETIRED" not in predecessor:
        fail("A8c1 terminal is absent")


def verify_exposure() -> set[str]:
    manifest = load(HERE / "exposure-manifest-v1.json")
    expected = {
        "exposed_model_ids": 14,
        "exposed_source_records": 10,
        "exposed_station_ids": 37,
    }
    if manifest["summary"] != expected:
        fail("exposure summary changed")
    if manifest["a9a_confirmation_target_accessed"]:
        fail("A9a claims confirmation target access")
    if not manifest["candidate_outputs_and_thresholds_are_development_only"]:
        fail("prior candidate outcomes are not development-only")
    for record in manifest["source_records"]:
        verify_identity(record)
    station_ids = [record["station_id"] for record in manifest["stations"]]
    if len(station_ids) != 37 or len(set(station_ids)) != 37:
        fail("exposed station set is not exactly 37 unique IDs")
    if len(set(manifest["exposed_model_ids"])) != 14:
        fail("exposed model IDs are incomplete or duplicated")
    return set(station_ids)


def distance_km(left: dict[str, Any], right: dict[str, Any]) -> float:
    lat1 = math.radians(left["latitude"])
    lat2 = math.radians(right["latitude"])
    delta_lat = lat2 - lat1
    delta_lon = math.radians(right["longitude"] - left["longitude"])
    term = math.sin(delta_lat / 2.0) ** 2
    term += math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2.0) ** 2
    return 2.0 * 6371.0088 * math.asin(math.sqrt(term))


def verify_confirmation(exposed: set[str]) -> None:
    roster = load(HERE / "confirmation-metadata-selection-v1.json")
    boundary = roster["access_boundary"]
    if boundary["confirmation_target_series_accessed"]:
        fail("confirmation target access barrier is false")
    if len(boundary["metadata_accessed"]) != 4:
        fail("NOAA metadata source inventory is incomplete")
    expected_hashes = {
        "a34e22a2356200602d9a1e67b0a160456d46b860d13610789e5da64b2b271f71",
        "0a973b423f503a6c48557b21f14f648149d4d8f4f209b9bad34dbc52f7748e2c",
        "a86a32c6d8a0d1f5d3e2724e8e98b237cc714a64858da9a8822da900e9f4f5f3",
        "cf1525e5a98d071d736c32e799ff80657c1f6a599f3f55433efce7e698c86938",
    }
    if {record["content_sha256"] for record in boundary["metadata_accessed"]} != expected_hashes:
        fail("NOAA metadata hashes changed")

    stations = roster["stations"]
    if len(stations) != 18 or len({station["station_id"] for station in stations}) != 18:
        fail("confirmation roster must contain 18 unique sites")
    if {station["station_id"] for station in stations} & exposed:
        fail("confirmation station ID overlaps prior exposed ID")
    counts = Counter(station["primary_stratum"] for station in stations)
    if dict(sorted(counts.items())) != roster["stratum_counts"]:
        fail("confirmation stratum counts do not match roster")
    if set(counts.values()) != {3} or len(counts) != 6:
        fail("confirmation roster must have three sites in six strata")
    for station in stations:
        if station["network"] != "CRN" or station["closed_at"] is not None:
            fail(f"confirmation site is not active CRN: {station['station_id']}")
        if station["operational_at"] > "2008-12-31T23:59:59Z":
            fail(f"confirmation site started too late: {station['station_id']}")
        if station["nearest_exposed_distance_km"] < 75.0:
            fail(f"confirmation site violates exposed-distance guard: {station['station_id']}")
    for stratum in counts:
        members = [s for s in stations if s["primary_stratum"] == stratum]
        minimum = min(
            distance_km(left, right)
            for index, left in enumerate(members)
            for right in members[index + 1 :]
        )
        if minimum < 150.0:
            fail(f"confirmation stratum lacks geographic separation: {stratum}")
    if roster["fit_period"]["start"] != "1980-01-01" or roster["fit_period"]["end"] != "2009-12-31":
        fail("confirmation fit period changed")
    if roster["target_period"]["start"] != "2010-01-01" or roster["target_period"]["end"] != "2025-12-31":
        fail("confirmation target period changed")


def verify_schemas_and_registry() -> None:
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "docs/specifications").glob("a9-*.schema.json")):
        schema = load(path)
        Draft202012Validator.check_schema(schema)
        schemas[path.name] = schema
    expected = {
        "a9-data-role-manifest-v1.schema.json",
        "a9-fit-artifact-v1.schema.json",
        "a9-objective-registry-v1.schema.json",
    }
    if set(schemas) != expected:
        fail("A9 schema set changed")

    path = HERE / "objective-registry-v1.json"
    registry = load(path)
    Draft202012Validator(
        schemas["a9-objective-registry-v1.schema.json"],
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    ).validate(registry)
    if path.read_bytes() != canonical(registry):
        fail("objective registry is not canonical JSON")
    if len(registry["objectives"]) != 31:
        fail("objective registry must contain 31 objectives")
    ids = [entry["id"] for entry in registry["objectives"]]
    if len(ids) != len(set(ids)):
        fail("objective IDs are duplicated")
    required_ids = {
        "occ_monthly_wet_frequency",
        "occ_wet_spell_survival",
        "amt_monthly_wet_mean",
        "amt_adjacent_wet_dependence",
        "amt_upper_tail",
        "agg_zero_month_frequency",
        "agg_monthly_total_mean",
        "agg_monthly_total_cv",
        "agg_annual_total_cv",
        "ext_annual_1_3_5_day_maxima",
        "storm_duration",
        "storm_time_to_peak",
        "storm_peak_ratio",
        "storm_joint_dependence",
        "ctx_wet_dry_temperature",
        "ctx_wet_event_wind_speed",
        "winter_cold_wet_fraction",
        "winter_freeze_transition_count",
        "winter_precip_temperature_dependence",
    }
    if not required_ids.issubset(ids):
        fail("objective registry is missing a required metric")
    for entry in registry["objectives"]:
        if entry["baseline_zero"] == "absolute_floor" and "absolute_floor" not in entry:
            fail(f"absolute-floor objective lacks floor: {entry['id']}")
    if registry["null_calibration"] != {
        "baseline_zero_rule": "Use the objective's absolute floor or its separate zero-mass and positive-scale distances; division by a zero baseline is prohibited.",
        "candidate_access_prohibited": True,
        "familywise_alpha": 0.05,
        "method": "paired_max_statistic_quantile",
        "replicates": 500,
    }:
        fail("null-calibration contract changed")


def verify_contract_content() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    required_spec = (
        "alternating_renewal_marked_v1",
        "latent_regime_marked_v1",
        "Philox4x32-10",
        "a9_uscrn_event_6h_v1",
        "The first A9 family has no runtime fallback",
        "one shot",
        "30-year evaluation",
        "100-year",
        "does not add a station-document revision",
    )
    for text in required_spec:
        if text not in spec:
            fail(f"foundation spec lacks required text: {text}")

    ledger = (HERE / "evidence-to-requirements-ledger.md").read_text(encoding="utf-8")
    for index in range(1, 17):
        if f"E{index:02d}" not in ledger:
            fail(f"evidence ledger missing E{index:02d}")
    for index in range(1, 10):
        if f"D{index:02d}" not in ledger:
            fail(f"evidence ledger missing D{index:02d}")
    if len(set(re.findall(r"RQ-[A-Z]+-\d{3}", ledger))) < 20:
        fail("evidence ledger has too few traced requirements")

    fixtures = (HERE / "fixture-plan.md").read_text(encoding="utf-8")
    for index in range(1, 21):
        if f"FX-{index:03d}" not in fixtures:
            fail(f"fixture plan missing FX-{index:03d}")
    handoff = (HERE / "a9b-handoff.md").read_text(encoding="utf-8")
    if "A9b remains unscaffolded and unauthorized" not in handoff:
        fail("A9b authorization boundary is missing")
    if "HARNESS-READY-A9C" not in handoff:
        fail("A9b continuation terminal is missing")


def verify_links() -> None:
    paths = list(PACKAGE.rglob("*.md")) + [SPEC, ROOT / "docs/specifications/README.md"]
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in paths:
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            target = target.strip().strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                fail(f"broken local link in {path.relative_to(ROOT)}: {target}")


def verify_no_runtime_change() -> None:
    changed = run(
        "git",
        "diff",
        "--name-only",
        DISPATCH_COMMIT,
        "--",
        "crates",
        "reference/cligen532",
    ).decode().splitlines()
    if changed:
        fail(f"A9a changed production/reference files: {changed}")
    runtime_roots = (ROOT / "crates",)
    forbidden = ("alternating_renewal_marked_v1", "latent_regime_marked_v1", "a9_joint_daily_event_family_v1")
    for root in runtime_roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for token in forbidden:
                if token in text:
                    fail(f"research ID entered runtime: {path.relative_to(ROOT)}")
    forbidden_suffixes = {".cli", ".parquet", ".par"}
    for path in PACKAGE.rglob("*"):
        if path.is_file() and path.suffix in forbidden_suffixes:
            fail(f"A9a contains generated/candidate data: {path.relative_to(ROOT)}")


def verify_closure_records() -> None:
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    if "Status: `EXECUTED-COMPLETE`" not in package:
        fail("package is not executed-complete")
    if "Terminal: `FOUNDATION-READY-A9B`" not in package:
        fail("package terminal is missing")
    review = (HERE / "review.md").read_text(encoding="utf-8")
    for text in ("Verdict: `ACCEPT`", "Open P1 findings: 0", "Open P2 findings: 0"):
        if text not in review:
            fail(f"review gate missing: {text}")
    catalog = (ROOT / "docs/work-packages/README.md").read_text(encoding="utf-8")
    expected_catalog = (
        "[20260715-a9a-successor-family-foundation]"
        "(20260715-a9a-successor-family-foundation/package.md) | EXECUTED-COMPLETE"
    )
    if expected_catalog not in catalog:
        fail("work-package catalog is not closed")
    roadmap = (ROOT / "docs/ROADMAP.md").read_text(encoding="utf-8")
    if "A9a completed on 2026-07-15 with" not in roadmap:
        fail("roadmap does not record A9a completion")
    if "A9b — calibration-harness implementation" not in roadmap:
        fail("roadmap lacks the next eligible A9b boundary")
    registry = (ROOT / "docs/specifications/README.md").read_text(encoding="utf-8")
    if "research-only (rev 1; A9a; no accepted runtime identifier)" not in registry:
        fail("specification registry does not preserve the research-only boundary")


def verify_canonical_manifests() -> None:
    for name in (
        "authority-manifest-v1.json",
        "exposure-manifest-v1.json",
        "confirmation-metadata-selection-v1.json",
    ):
        path = HERE / name
        if path.read_bytes() != canonical(load(path)):
            fail(f"manifest is not canonical JSON: {name}")


def main() -> None:
    verify_authority()
    exposed = verify_exposure()
    verify_confirmation(exposed)
    verify_schemas_and_registry()
    verify_contract_content()
    verify_links()
    verify_no_runtime_change()
    verify_closure_records()
    verify_canonical_manifests()
    print(
        "PASS: 25 authorities and 10 exposure sources verified; 37 exposed "
        "stations isolated; 18-site metadata-only roster, 31 objectives, 20 fixture "
        "groups, and zero runtime changes verified"
    )


if __name__ == "__main__":
    main()
