#!/usr/bin/env python3
"""Execute the frozen A8c routed-daily generation matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
CONTRACT_PATH = ARTIFACTS / "pilot-contract-v1.json"
FREEZE_PATH = ARTIFACTS / "pre-execution-freeze-v1.json"
MATRIX_PATH = ARTIFACTS / "runspecs/runspec-matrix-v1.json"
DEFAULT_WORK = ROOT / "target/a8c-routed-daily-pilot"
DEFAULT_OUTPUT = ARTIFACTS / "execution-evidence-v1.json"
BINARY = ROOT / "target/release/cligen"
BUILD = ["cargo", "build", "--locked", "--offline", "--release", "--bin", "cligen"]


def reject_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON token: {token}")


def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(
            stream,
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicates,
        )
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_hashes(entries: dict[str, Any]) -> dict[str, str]:
    checked = {}
    for name, entry in entries.items():
        path = ROOT / entry["path"]
        actual = sha256(path)
        if actual != entry["sha256"]:
            raise ValueError(f"input identity mismatch: {name}: {actual}")
        checked[name] = actual
    return checked


def check_freeze() -> dict[str, Any]:
    freeze = load_json(FREEZE_PATH)
    if freeze["status"] != "FROZEN-BEFORE-CANDIDATE-GENERATION":
        raise ValueError("A8c freeze is not active")
    for relative, expected in freeze["frozen_files_sha256"].items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise ValueError(f"frozen file changed: {relative}: {actual}")
    return freeze


def runspec_text(
    station_kind: str,
    station_path: Path,
    output: Path,
    years: int,
    burn: int,
    profile: str,
) -> str:
    return "\n".join(
        [
            "cligen_runspec: 1",
            "station:",
            f"  {station_kind}: {json.dumps(str(station_path))}",
            "mode: continuous",
            "simulation:",
            "  begin_year: 1",
            f"  years: {years}",
            "  interpolation: none",
            "rng:",
            f"  burn: {burn}",
            f"generation_profile: {profile}",
            "qc_filter: faithful",
            "output:",
            f"  cli: {json.dumps(str(output))}",
            "  overwrite: true",
            "  quality: false",
            "",
        ]
    )


def provenance_path(cli: Path) -> Path:
    return Path(str(cli) + ".provenance.json")


def quality_path(cli: Path) -> Path:
    return Path(str(cli) + ".quality.json")


def run_once(runspec: Path) -> None:
    result = subprocess.run(
        [str(BINARY), "run", str(runspec)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{runspec.name}: {result.stderr.strip()}")


def daily_rows(path: Path) -> list[list[str]]:
    result: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 13:
            continue
        try:
            int(fields[0])
            int(fields[1])
            int(fields[2])
        except ValueError:
            continue
        values = [float(token) for token in fields[3:]]
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"non-finite daily row: {path}")
        result.append(fields)
    if not result:
        raise ValueError(f"no daily rows: {path}")
    return result


def row_hash(rows: list[list[str]]) -> str:
    return sha256_bytes(("\n".join(" ".join(row) for row in rows) + "\n").encode("ascii"))


def expected_days(years: int) -> int:
    return sum(366 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 365 for year in range(1, years + 1))


def validate_provenance(
    path: Path, station: dict[str, Any], station_document: Path
) -> dict[str, Any]:
    value = load_json(path)
    generation = value["generation"]
    station_value = value["station"]
    if generation["profile"] != "a8c_routed_daily_v1":
        raise ValueError(f"{station['station_id']}: wrong generation profile")
    if generation["rng_scheme"] != "cligen_randn_5_32_3_plus_splitmix64_daily_v1":
        raise ValueError(f"{station['station_id']}: wrong RNG scheme")
    if station_value["input_schema"] != {
        "id": "org.openwepp.cligen.station",
        "version": "2",
    }:
        raise ValueError(f"{station['station_id']}: wrong station schema")
    expected_model = (
        "a8c_integrated_daily_v1"
        if station["route"] == "integrated_daily"
        else "fixed_monthly_5_32_3"
    )
    expected_fit = (
        "a8a_o2_logqspline_gaussian_copula_v1"
        if station["route"] == "integrated_daily"
        else "legacy_daily_only_v1"
    )
    if station_value["model"] != expected_model:
        raise ValueError(f"{station['station_id']}: wrong station model")
    if station_value["fit"] != {"status": "reported", "id": expected_fit}:
        raise ValueError(f"{station['station_id']}: wrong fit identity")
    if station_value["input_sha256"] != sha256(station_document):
        raise ValueError(f"{station['station_id']}: wrong document identity")
    return {
        "fit_id": expected_fit,
        "input_schema_version": 2,
        "model": expected_model,
        "profile": generation["profile"],
        "rng_scheme": generation["rng_scheme"],
    }


def extract_parameters(archive_path: Path, stations: list[dict[str, Any]], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    result = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        for station in stations:
            station_id = station["station_id"]
            member = archive.getmember(f"station-parameters/{station_id}.par")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"missing parameter file: {station_id}")
            raw = stream.read()
            if sha256_bytes(raw) != station["parameter_sha256"]:
                raise ValueError(f"parameter identity mismatch: {station_id}")
            path = output / f"{station_id}.par"
            path.write_bytes(raw)
            result[station_id] = path
    return result


def execute_cell(
    station: dict[str, Any],
    burn: int,
    parameter: Path,
    work: Path,
) -> dict[str, Any]:
    station_id = station["station_id"]
    document = ARTIFACTS / "stations" / f"{station_id}.station.json"
    stem = f"{station_id}-burn{burn}"
    candidate = work / "streams" / f"{stem}-candidate-100.cli"
    candidate_30 = work / "scratch" / f"{stem}-candidate-30.cli"
    faithful = work / "streams" / f"{stem}-faithful-100.cli"
    cases = [
        ("candidate-100", "document", document, candidate, 100, "a8c_routed_daily_v1"),
        ("candidate-30", "document", document, candidate_30, 30, "a8c_routed_daily_v1"),
        ("faithful-100", "par", parameter, faithful, 100, "faithful_5_32_3"),
    ]
    runspecs = {}
    for name, kind, source, cli, years, profile in cases:
        runspec = work / "runspecs" / f"{stem}-{name}.yaml"
        runspec.write_text(
            runspec_text(kind, source, cli, years, burn, profile), encoding="utf-8"
        )
        runspecs[name] = sha256(runspec)
        run_once(runspec)

    first_cli = candidate.read_bytes()
    first_provenance = provenance_path(candidate).read_bytes()
    run_once(work / "runspecs" / f"{stem}-candidate-100.yaml")
    replay_cli = candidate.read_bytes()
    replay_provenance = provenance_path(candidate).read_bytes()
    replay_ok = first_cli == replay_cli and first_provenance == replay_provenance

    candidate_rows = daily_rows(candidate)
    short_rows = daily_rows(candidate_30)
    faithful_rows = daily_rows(faithful)
    if len(candidate_rows) != expected_days(100) or len(faithful_rows) != expected_days(100):
        raise ValueError(f"{stem}: 100-year row count mismatch")
    if len(short_rows) != expected_days(30):
        raise ValueError(f"{stem}: 30-year row count mismatch")
    prefix_ok = short_rows == candidate_rows[: len(short_rows)]
    fallback_identity = None
    cross_variable_identity = None
    if station["route"] == "legacy_daily_fallback":
        fallback_identity = candidate_rows == faithful_rows
    else:
        cross_variable_identity = all(
            candidate_row[7:13] == faithful_row[7:13]
            for candidate_row, faithful_row in zip(candidate_rows, faithful_rows)
        )
    provenance = validate_provenance(provenance_path(candidate), station, document)
    if quality_path(candidate).exists() or quality_path(faithful).exists():
        raise ValueError(f"{stem}: quality=false emitted a quality report")

    for path in (
        candidate_30,
        provenance_path(candidate_30),
        quality_path(candidate_30),
    ):
        path.unlink(missing_ok=True)
    return {
        "burn": burn,
        "candidate": {
            "cli_path": str(candidate.relative_to(ROOT)),
            "cli_sha256": sha256(candidate),
            "provenance_path": str(provenance_path(candidate).relative_to(ROOT)),
            "provenance_sha256": sha256(provenance_path(candidate)),
            "row_count": len(candidate_rows),
            "row_sha256": row_hash(candidate_rows),
        },
        "candidate_byte_replay": replay_ok,
        "candidate_30_year_row_prefix": prefix_ok,
        "cross_variable_exact": cross_variable_identity,
        "faithful": {
            "cli_path": str(faithful.relative_to(ROOT)),
            "cli_sha256": sha256(faithful),
            "provenance_path": str(provenance_path(faithful).relative_to(ROOT)),
            "provenance_sha256": sha256(provenance_path(faithful)),
            "row_count": len(faithful_rows),
            "row_sha256": row_hash(faithful_rows),
        },
        "fallback_typed_row_identity": fallback_identity,
        "provenance": provenance,
        "route": station["route"],
        "runspec_sha256": runspecs,
        "station_id": station_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    work = args.work.resolve()
    output = args.output.resolve()

    contract = load_json(CONTRACT_PATH)
    matrix = load_json(MATRIX_PATH)
    freeze = check_freeze()
    input_hashes = check_hashes(contract["inputs"])
    if matrix["station_ids"] != [row["station_id"] for row in contract["stations"]]:
        raise ValueError("runspec matrix station order differs from contract")
    if matrix["burns"] != contract["execution"]["burns"]:
        raise ValueError("runspec matrix burns differ from contract")

    shutil.rmtree(work, ignore_errors=True)
    for directory in ("parameters", "runspecs", "scratch", "streams"):
        (work / directory).mkdir(parents=True, exist_ok=True)
    subprocess.run(BUILD, cwd=ROOT, check=True)
    binary_sha256 = sha256(BINARY)
    parameters = extract_parameters(
        ROOT / contract["inputs"]["a8a_selected_parameters"]["path"],
        contract["stations"],
        work / "parameters",
    )

    cells = []
    for station in contract["stations"]:
        for burn in contract["execution"]["burns"]:
            cells.append(execute_cell(station, burn, parameters[station["station_id"]], work))
    cells.sort(key=lambda row: (row["station_id"], row["burn"]))
    result = {
        "analysis_id": contract["analysis_id"],
        "binary_sha256": binary_sha256,
        "cells": cells,
        "contract_sha256": sha256(CONTRACT_PATH),
        "execution_counts": {
            "cells": len(cells),
            "processes": len(cells) * 4,
            "retained_streams": len(cells) * 2,
        },
        "freeze_sha256": sha256(FREEZE_PATH),
        "input_hashes": input_hashes,
        "matrix_sha256": sha256(MATRIX_PATH),
        "schema_version": 1,
        "source_commit": freeze["source_commit"],
    }
    if result["execution_counts"]["processes"] != matrix["expected_process_count"]:
        raise ValueError("unexpected process count")
    write_json(output, result)
    print(f"wrote {output.relative_to(ROOT)} ({len(cells)} station/burn cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
