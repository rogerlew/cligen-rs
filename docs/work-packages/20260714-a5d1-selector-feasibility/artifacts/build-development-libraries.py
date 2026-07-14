#!/usr/bin/env python3
"""Regenerate and repeat-check the frozen A5d1 faithful-off libraries."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

from a5d1_common import (
    A5A_ARCHIVE,
    LIBRARY_DIR,
    LIBRARY_MANIFEST,
    ROOT,
    TARGET,
    days_in_year,
    freeze_identity,
    load_json,
    parse_cli,
    relative,
    sha256,
    station_records,
    synthetic_self_test,
    write_json,
)


BINARY = ROOT / "target/release/cligen"
PAR_DIR = TARGET / "station-parameters"
RUNSPEC_DIR = TARGET / "runspecs"


def extract_station_parameters() -> list[dict]:
    PAR_DIR.mkdir(parents=True, exist_ok=True)
    records = station_records()
    with tarfile.open(A5A_ARCHIVE, mode="r:gz") as archive:
        for station in records:
            station_id = station["station_id"]
            member = archive.getmember(f"station-parameters/{station_id}.par")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"cannot extract station parameter: {station_id}")
            destination = PAR_DIR / f"{station_id}.par"
            destination.write_bytes(source.read())
            if sha256(destination) != station["par_sha256"]:
                raise ValueError(f"station parameter hash mismatch: {station_id}")
    return records


def runspec_text(par: Path, cli: Path) -> str:
    return "\n".join(
        [
            "cligen_runspec: 1",
            "station:",
            f"  par: {json.dumps(str(par.resolve()))}",
            "mode: continuous",
            "simulation:",
            "  begin_year: 1",
            "  years: 256",
            "  interpolation: none",
            "rng:",
            "  burn: 0",
            "generation_profile: faithful_5_32_3",
            "qc_filter: off",
            "output:",
            f"  cli: {json.dumps(str(cli.resolve()))}",
            "  overwrite: true",
            "  quality: true",
            "",
        ]
    )


def run_once(station_id: str, repetition: int) -> dict:
    par = PAR_DIR / f"{station_id}.par"
    # The output path is embedded in the CLI header. Both determinism runs must
    # therefore overwrite one canonical pathname for whole-file byte identity.
    run_dir = LIBRARY_DIR / "canonical"
    run_dir.mkdir(parents=True, exist_ok=True)
    RUNSPEC_DIR.mkdir(parents=True, exist_ok=True)
    cli = run_dir / f"{station_id}-256yr.cli"
    runspec = RUNSPEC_DIR / f"{station_id}-repeat-{repetition}.yaml"
    runspec.write_text(runspec_text(par, cli), encoding="utf-8")
    started = time.monotonic()
    process = subprocess.run(
        [str(BINARY), "run", str(runspec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    wall_seconds = time.monotonic() - started
    if process.returncode != 0:
        raise RuntimeError(f"{station_id}: {process.stderr.strip()}")
    quality = cli.with_name(cli.name + ".quality.json")
    provenance = cli.with_name(cli.name + ".provenance.json")
    rows = parse_cli(cli)
    if len(rows) != sum(days_in_year(year) for year in range(1, 257)):
        raise ValueError(f"wrong library day count: {station_id}")
    provenance_value = load_json(provenance)
    quality_value = load_json(quality)
    if not isinstance(provenance_value, dict) or not isinstance(quality_value, dict):
        raise ValueError(f"invalid sidecar: {station_id}")
    if provenance_value["artifact"]["content_sha256"] != sha256(cli):
        raise ValueError(f"provenance content hash mismatch: {station_id}")
    if quality_value["identity"]["provenance"] != provenance_value:
        raise ValueError(f"quality/provenance identity mismatch: {station_id}")
    if provenance_value["generation"]["profile"] != "faithful_5_32_3":
        raise ValueError(f"profile mismatch: {station_id}")
    if provenance_value["generation"]["qc_policy"] != "off":
        raise ValueError(f"QC mismatch: {station_id}")
    return {
        "station_id": station_id,
        "repetition": repetition,
        "wall_seconds": round(wall_seconds, 6),
        "cli": {"path": relative(cli), "bytes": cli.stat().st_size, "sha256": sha256(cli)},
        "quality": {
            "path": relative(quality),
            "bytes": quality.stat().st_size,
            "sha256": sha256(quality),
        },
        "provenance": {
            "path": relative(provenance),
            "bytes": provenance.stat().st_size,
            "sha256": sha256(provenance),
        },
        "runspec": {"path": relative(runspec), "sha256": sha256(runspec)},
        "years": 256,
        "days": len(rows),
    }


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: build-development-libraries.py")
    freeze_sha256 = freeze_identity()
    tests = synthetic_self_test()
    if not all(tests.values()):
        raise RuntimeError(f"synthetic self-test failed: {tests}")
    if not BINARY.is_file():
        raise FileNotFoundError(BINARY)
    if LIBRARY_DIR.exists():
        shutil.rmtree(LIBRARY_DIR)
    if RUNSPEC_DIR.exists():
        shutil.rmtree(RUNSPEC_DIR)
    stations = extract_station_parameters()
    records: list[dict] = []
    for repetition in (1, 2):
        for station in stations:
            records.append(run_once(station["station_id"], repetition))
    indexed = {(row["station_id"], row["repetition"]): row for row in records}
    repeat_checks = []
    for station in stations:
        station_id = station["station_id"]
        first = indexed[(station_id, 1)]
        second = indexed[(station_id, 2)]
        matched = first["cli"]["sha256"] == second["cli"]["sha256"]
        if not matched:
            raise ValueError(f"repeat library mismatch: {station_id}")
        repeat_checks.append({"station_id": station_id, "byte_identical": matched})
    retained = [row for row in records if row["repetition"] == 2]
    manifest = {
        "development_library_manifest_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "binary": {
            "path": relative(BINARY),
            "bytes": BINARY.stat().st_size,
            "sha256": sha256(BINARY),
        },
        "controls": {
            "profile": "faithful_5_32_3",
            "qc_filter": "off",
            "begin_year": 1,
            "years": 256,
            "burn": 0,
            "interpolation": "none",
        },
        "canonical_library_role": "one nested burn-0 trajectory; repeats are determinism checks, not replicates",
        "station_count": len(stations),
        "records": retained,
        "repeat_checks": repeat_checks,
        "repeat_record_identities": [row for row in records if row["repetition"] == 1],
        "synthetic_self_test": tests,
        "total_retained_bytes": sum(row["cli"]["bytes"] for row in retained),
    }
    write_json(LIBRARY_MANIFEST, manifest)
    print(
        f"A5d1 libraries: PASS ({len(stations)} stations; "
        f"{manifest['total_retained_bytes']} retained bytes)"
    )


if __name__ == "__main__":
    main()
