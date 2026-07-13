#!/usr/bin/env python3
"""Offline identity, schema, and byte-rebuild gate for A5a-v1."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from corpus_common import expected_dates, metric_estimator_identity, sha256


def verify_lineage_and_contract(here: Path, repo: Path, corpus: dict) -> None:
    config_path = here / "corpus-config-v1.json"
    source_path = here / "source-manifest-v1.json"
    coverage_path = here / "coverage-evidence-v1.md"
    schema_path = repo / "docs/specifications/observed-target-corpus-v1.schema.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_manifest = json.loads(source_path.read_text(encoding="utf-8"))
    manifest = json.loads((here / "manifest-v1.json").read_text(encoding="utf-8"))
    source_hash = sha256(source_path.read_bytes())
    if source_manifest["config_sha256"] != sha256(config_path.read_bytes()):
        raise ValueError("source manifest does not bind the corpus config")
    if corpus["source_manifest_sha256"] != source_hash:
        raise ValueError("target corpus does not bind the source manifest")
    if corpus["fixed_periods"] != config["periods"]:
        raise ValueError("target corpus periods differ from config")
    if corpus["conventions"]["precipitation_wet_day_threshold_mm"] != 1.0:
        raise ValueError("observed wet-day threshold is not R1mm >= 1.0 mm")

    source_stations = {row["station_id"]: row for row in source_manifest["stations"]}
    target_stations = {row["station_id"]: row for row in corpus["stations"]}
    if len(source_stations) != 17 or set(source_stations) != set(target_stations):
        raise ValueError("station identity mismatch across config/source/target")
    daymet_count = 0
    ghcn_count = 0
    for station in config["stations"]:
        station_id = station["station_id"]
        sources = source_stations[station_id]["sources"]
        target_sources = target_stations[station_id]["sources"]
        daymet = sources["daymet"]
        if (
            daymet["availability"] != "available"
            or daymet["calendar"] != "noleap_365"
            or daymet["source_sha256"] != station["daymet_source_sha256"]
            or daymet["q3_historical_source_sha256"] != station["daymet_source_sha256"]
        ):
            raise ValueError(f"{station_id}: Daymet Q3 identity check failed")
        daymet_count += 1

        ghcn = sources["ghcn"]
        if station["ghcn_station_id"] is None:
            if ghcn.get("availability") != "unavailable":
                raise ValueError(f"{station_id}: unexpected GHCN availability")
        else:
            if (
                ghcn["availability"] != "available"
                or ghcn["calendar"] != "proleptic_gregorian"
                or ghcn["dataset_version"] != "snapshot-2026-07-12"
                or ghcn["retrieval_date"] != "2026-07-12"
                or ghcn["q3_historical_source_sha256"]
                != station["q3_ghcn_source_sha256"]
                or ghcn["source_sha256"] == station["q3_ghcn_source_sha256"]
            ):
                raise ValueError(f"{station_id}: GHCN snapshot/Q3 lineage check failed")
            ghcn_count += 1

        for source_name, source in sources.items():
            target_source = target_sources[source_name]
            if source.get("availability") != "available":
                if target_source.get("availability") != "unavailable":
                    raise ValueError(
                        f"{station_id}/{source_name}: availability mismatch"
                    )
                continue
            identity = target_source["source_identity"]
            if (
                identity["source_sha256"] != source["source_sha256"]
                or identity["archive_sha256"] != source["archive_sha256"]
                or identity["fixed_window_logical_records_sha256"]
                != source["fixed_window_logical_records_sha256"]
            ):
                raise ValueError(
                    f"{station_id}/{source_name}: source identity mismatch"
                )
            for period_name, bounds in config["periods"].items():
                period = target_source["periods"][period_name]
                if period["period"] != {
                    "start_year": bounds[0],
                    "end_year": bounds[1],
                }:
                    raise ValueError(
                        f"{station_id}/{source_name}/{period_name}: period mismatch"
                    )
                coverage = period["precipitation_structure"]["coverage"]
                expected = len(expected_dates(source["calendar"], *bounds))
                if (
                    coverage["expected_days"] != expected
                    or coverage["observed_precip_days"] + coverage["missing_days"]
                    != expected
                    or not 0 <= coverage["missing_gap_runs"] <= coverage["missing_days"]
                ):
                    raise ValueError(
                        f"{station_id}/{source_name}/{period_name}: coverage mismatch"
                    )
                if source_name == "daymet" and (
                    coverage["missing_days"] != 0
                    or coverage["missing_gap_runs"] != 0
                    or period["dependence"]["raw"] == period["dependence"]["detrended"]
                ):
                    raise ValueError(
                        f"{station_id}/{period_name}: incomplete or undifferentiated Daymet"
                    )
                descriptor = period["storm_descriptors"]
                if descriptor.get(
                    "availability"
                ) != "unavailable" or not descriptor.get("reason"):
                    raise ValueError(
                        f"{station_id}/{source_name}/{period_name}: descriptor target not unavailable"
                    )
    if daymet_count != 17 or ghcn_count != 8:
        raise ValueError(f"unexpected source coverage: {daymet_count}/{ghcn_count}")

    archives = sorted((repo / "references/observed/a5a-v1").glob("*/*"))
    archive_lines = "".join(
        f"{sha256(path.read_bytes())}  {path.relative_to(repo).as_posix()}\n"
        for path in archives
    ).encode("ascii")
    expected_bindings = {
        "archive_aggregate_sha256": sha256(archive_lines),
        "archive_files": len(archives),
        "config_sha256": sha256(config_path.read_bytes()),
        "source_manifest_sha256": source_hash,
    }
    for key, expected in expected_bindings.items():
        if manifest[key] != expected:
            raise ValueError(f"final manifest binding mismatch: {key}")
    if manifest["metric_estimator"] != metric_estimator_identity(repo):
        raise ValueError(
            "portable metrics-estimator source identity differs from manifest"
        )
    for key, path in (
        ("observed_target_corpus", here / "observed-target-corpus-v1.json"),
        ("coverage_evidence", coverage_path),
        ("schema", schema_path),
    ):
        binding = manifest[key]
        if binding["path"] != path.relative_to(repo).as_posix():
            raise ValueError(f"final manifest path mismatch: {key}")
        if binding["sha256"] != sha256(path.read_bytes()):
            raise ValueError(f"final manifest content mismatch: {key}")
        if key != "schema" and binding["bytes"] != path.stat().st_size:
            raise ValueError(f"final manifest byte-length mismatch: {key}")
    archive_readme = repo / "references/observed/a5a-v1/README.md"
    if manifest["archive_documentation"] != {
        "path": archive_readme.relative_to(repo).as_posix(),
        "sha256": sha256(archive_readme.read_bytes()),
    }:
        raise ValueError("final manifest content mismatch: archive documentation")
    data_notice = repo / "references/observed/a5a-v1/THIRD_PARTY_DATA_NOTICE.md"
    if manifest["third_party_data_notice"] != {
        "path": data_notice.relative_to(repo).as_posix(),
        "sha256": sha256(data_notice.read_bytes()),
    }:
        raise ValueError("final manifest content mismatch: third-party data notice")
    for name, expected in manifest["tools"].items():
        if sha256((here / name).read_bytes()) != expected:
            raise ValueError(f"final manifest tool mismatch: {name}")
    for name, binding in manifest["build_schemas"].items():
        path = here / "schemas" / name
        if binding["path"] != path.relative_to(repo).as_posix() or binding[
            "sha256"
        ] != sha256(path.read_bytes()):
            raise ValueError(f"final manifest build-schema mismatch: {name}")
    build_readme = here / "README.md"
    if manifest["build_documentation"] != {
        "path": build_readme.relative_to(repo).as_posix(),
        "sha256": sha256(build_readme.read_bytes()),
    }:
        raise ValueError("final manifest content mismatch: build documentation")


def main() -> None:
    here = Path(__file__).resolve().parent
    repo = here.parents[4]
    subprocess.run(
        [
            "cargo",
            "build",
            "--locked",
            "--offline",
            "--bin",
            "cligen-quality-estimator",
        ],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    helper = (
        repo
        / "target/debug"
        / (
            "cligen-quality-estimator.exe"
            if sys.platform == "win32"
            else "cligen-quality-estimator"
        )
    )
    if not helper.is_file():
        raise FileNotFoundError(helper)
    sums = here / "SHA256SUMS"
    checked = 0
    for line in sums.read_text(encoding="ascii").splitlines():
        expected, relative = line.split("  ", 1)
        path = repo / relative
        actual = sha256(path.read_bytes())
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch: {relative}: {actual} != {expected}")
        checked += 1

    with tempfile.TemporaryDirectory(prefix="cligen-a5a-v1-") as temp:
        temp = Path(temp)
        rebuilt_source = temp / "source-manifest-v1.json"
        rebuilt_corpus = temp / "observed-target-corpus-v1.json"
        rebuilt_coverage = temp / "coverage-evidence-v1.md"
        rebuilt_schema = temp / "observed-target-corpus-v1.schema.json"
        subprocess.run(
            [
                sys.executable,
                str(here / "build_target_schema.py"),
                "--output",
                str(rebuilt_schema),
            ],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        public_schema = (
            repo / "docs/specifications/observed-target-corpus-v1.schema.json"
        )
        if rebuilt_schema.read_bytes() != public_schema.read_bytes():
            raise ValueError("offline target-schema rebuild is not byte-identical")
        subprocess.run(
            [
                sys.executable,
                str(here / "acquire_sources.py"),
                "--manifest",
                str(rebuilt_source),
            ],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if (
            rebuilt_source.read_bytes()
            != (here / "source-manifest-v1.json").read_bytes()
        ):
            raise ValueError("offline source-manifest rebuild is not byte-identical")
        subprocess.run(
            [
                sys.executable,
                str(here / "build_targets.py"),
                "--source-manifest",
                str(rebuilt_source),
                "--output",
                str(rebuilt_corpus),
                "--metrics-helper",
                str(helper),
            ],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if (
            rebuilt_corpus.read_bytes()
            != (here / "observed-target-corpus-v1.json").read_bytes()
        ):
            raise ValueError("offline target-corpus rebuild is not byte-identical")
        subprocess.run(
            [
                sys.executable,
                str(here / "build_coverage.py"),
                "--corpus",
                str(rebuilt_corpus),
                "--source-manifest",
                str(rebuilt_source),
                "--output",
                str(rebuilt_coverage),
            ],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if (
            rebuilt_coverage.read_bytes()
            != (here / "coverage-evidence-v1.md").read_bytes()
        ):
            raise ValueError("offline coverage-evidence rebuild is not byte-identical")

    corpus = json.loads((here / "observed-target-corpus-v1.json").read_text())
    verify_lineage_and_contract(here, repo, corpus)
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError(
            "jsonschema is required for the offline schema gate"
        ) from error
    schema_documents = [
        (
            "observed target corpus",
            corpus,
            repo / "docs/specifications/observed-target-corpus-v1.schema.json",
        ),
        (
            "corpus config",
            json.loads((here / "corpus-config-v1.json").read_text()),
            here / "schemas/corpus-config-v1.schema.json",
        ),
        (
            "source manifest",
            json.loads((here / "source-manifest-v1.json").read_text()),
            here / "schemas/source-manifest-v1.schema.json",
        ),
        (
            "final manifest",
            json.loads((here / "manifest-v1.json").read_text()),
            here / "schemas/manifest-v1.schema.json",
        ),
    ]
    validators = {}
    documents = {}
    for label, document, schema_path in schema_documents:
        schema = json.loads(schema_path.read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema)
        validators[label] = validator
        documents[label] = document
        errors = sorted(
            validator.iter_errors(document), key=lambda error: list(error.path)
        )
        if errors:
            first = errors[0]
            raise ValueError(
                f"{label} schema validation failed at {list(first.path)}: "
                f"{first.message}"
            )

    negative_checks = 0

    def reject(label, case, mutate):
        nonlocal negative_checks
        candidate = copy.deepcopy(documents[label])
        mutate(candidate)
        if validators[label].is_valid(candidate):
            raise ValueError(f"schema negative vector unexpectedly valid: {case}")
        negative_checks += 1

    reject(
        "observed target corpus",
        "target unknown field",
        lambda value: value.__setitem__("unexpected", True),
    )
    reject(
        "observed target corpus",
        "metrics version",
        lambda value: value.__setitem__("metrics_version", 2),
    )
    reject(
        "observed target corpus",
        "source hash pattern",
        lambda value: value.__setitem__("source_manifest_sha256", "not-a-hash"),
    )
    reject(
        "observed target corpus",
        "matrix width",
        lambda value: value["stations"][0]["sources"]["daymet"]["periods"]["full"][
            "dependence"
        ]["raw"]["precip_cross_month"]["pearson_correlation"][0].pop(),
    )
    reject(
        "observed target corpus",
        "correlation bound",
        lambda value: value["stations"][0]["sources"]["daymet"]["periods"]["full"][
            "dependence"
        ]["raw"]["cross_variable_by_month"]["jan"]["precip_tmax"].__setitem__(
            "pearson", 1.01
        ),
    )
    reject(
        "observed target corpus",
        "missing month",
        lambda value: value["stations"][0]["sources"]["daymet"]["periods"]["full"][
            "monthly"
        ].pop("dec"),
    )
    reject(
        "observed target corpus",
        "observed descriptor fabrication",
        lambda value: value["stations"][0]["sources"]["daymet"]["periods"]["full"][
            "storm_descriptors"
        ].__setitem__("availability", "available"),
    )
    reject(
        "observed target corpus",
        "negative coverage count",
        lambda value: value["stations"][0]["sources"]["daymet"]["periods"]["full"][
            "precipitation_structure"
        ]["coverage"].__setitem__("missing_days", -1),
    )
    reject(
        "observed target corpus",
        "duplicate station",
        lambda value: value["stations"].__setitem__(
            -1, copy.deepcopy(value["stations"][0])
        ),
    )
    reject(
        "corpus config",
        "config unknown field",
        lambda value: value.__setitem__("unexpected", True),
    )
    reject(
        "corpus config",
        "config period drift",
        lambda value: value["periods"].__setitem__("evaluation", [2011, 2025]),
    )
    reject(
        "source manifest",
        "Daymet calendar drift",
        lambda value: value["stations"][0]["sources"]["daymet"].__setitem__(
            "calendar", "proleptic_gregorian"
        ),
    )
    reject(
        "source manifest",
        "source unknown field",
        lambda value: value["stations"][0]["sources"]["daymet"].__setitem__(
            "unexpected", True
        ),
    )
    reject(
        "final manifest",
        "archive count",
        lambda value: value.__setitem__("archive_files", 24),
    )
    reject(
        "final manifest",
        "missing third-party data notice",
        lambda value: value.pop("third_party_data_notice"),
    )
    reject(
        "final manifest",
        "missing build documentation",
        lambda value: value.pop("build_documentation"),
    )
    reject(
        "final manifest",
        "manifest unknown field",
        lambda value: value.__setitem__("unexpected", True),
    )
    stations = corpus["stations"]
    available = sum(
        source.get("availability") == "available"
        for station in stations
        for source in station["sources"].values()
    )
    if len(stations) != 17 or available != 25:
        raise ValueError(f"unexpected corpus coverage: {len(stations)} / {available}")
    print(
        f"verified {checked} hashes; 17 Q3-identical Daymet + 8 new GHCN "
        f"snapshots; 102 coverage rows; {negative_checks} schema negatives; "
        "schema-valid byte-identical rebuild"
    )


if __name__ == "__main__":
    main()
