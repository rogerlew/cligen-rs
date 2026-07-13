#!/usr/bin/env python3
"""Bind A5a source, tool, schema, and target identities."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from corpus_common import (
    build_environment,
    metric_estimator_identity,
    sha256,
    write_canonical_json,
)


def main() -> None:
    here = Path(__file__).resolve().parent
    repo = here.parents[4]
    schema = repo / "docs/specifications/observed-target-corpus-v1.schema.json"
    if not schema.is_file():
        raise FileNotFoundError(schema)
    config = here / "corpus-config-v1.json"
    source = here / "source-manifest-v1.json"
    corpus = here / "observed-target-corpus-v1.json"
    coverage = here / "coverage-evidence-v1.md"
    build_readme = here / "README.md"
    archive_readme = repo / "references/observed/a5a-v1/README.md"
    data_notice = repo / "references/observed/a5a-v1/THIRD_PARTY_DATA_NOTICE.md"
    if not data_notice.is_file():
        raise FileNotFoundError(data_notice)
    tools = [
        here / name
        for name in (
            "acquire_sources.py",
            "build_coverage.py",
            "build_target_schema.py",
            "build_targets.py",
            "corpus_common.py",
            "finalize_manifest.py",
            "verify_offline.py",
        )
    ]
    build_schemas = sorted((here / "schemas").glob("*.schema.json"))
    if {path.name for path in build_schemas} != {
        "corpus-config-v1.schema.json",
        "manifest-v1.schema.json",
        "source-manifest-v1.schema.json",
    }:
        raise ValueError("unexpected package-local build schema set")
    archives = sorted((repo / "references/observed/a5a-v1").glob("*/*"))
    if len(archives) != 25 or not all(path.is_file() for path in archives):
        raise ValueError(f"expected 25 observed source archives, found {len(archives)}")
    archive_lines = "".join(
        f"{sha256(path.read_bytes())}  {path.relative_to(repo).as_posix()}\n"
        for path in archives
    ).encode("ascii")
    estimator = metric_estimator_identity(repo)
    manifest = {
        "archive_aggregate_sha256": sha256(archive_lines),
        "archive_files": len(archives),
        "archive_documentation": {
            "path": archive_readme.relative_to(repo).as_posix(),
            "sha256": sha256(archive_readme.read_bytes()),
        },
        "third_party_data_notice": {
            "path": data_notice.relative_to(repo).as_posix(),
            "sha256": sha256(data_notice.read_bytes()),
        },
        "config_sha256": sha256(config.read_bytes()),
        "build_schemas": {
            path.name: {
                "path": path.relative_to(repo).as_posix(),
                "sha256": sha256(path.read_bytes()),
            }
            for path in build_schemas
        },
        "build_documentation": {
            "path": build_readme.relative_to(repo).as_posix(),
            "sha256": sha256(build_readme.read_bytes()),
        },
        "build_environment": build_environment(),
        "coverage_evidence": {
            "bytes": coverage.stat().st_size,
            "path": coverage.relative_to(repo).as_posix(),
            "sha256": sha256(coverage.read_bytes()),
        },
        "daymet_sources": 17,
        "ghcn_sources": 8,
        "manifest_schema_version": 1,
        "metric_estimator": estimator,
        "observed_target_corpus": {
            "bytes": corpus.stat().st_size,
            "path": corpus.relative_to(repo).as_posix(),
            "sha256": sha256(corpus.read_bytes()),
        },
        "schema": {
            "path": schema.relative_to(repo).as_posix(),
            "sha256": sha256(schema.read_bytes()),
        },
        "source_manifest_sha256": sha256(source.read_bytes()),
        "tools": {path.name: sha256(path.read_bytes()) for path in tools},
    }
    output = here / "manifest-v1.json"
    write_canonical_json(output, manifest)
    estimator_files = [repo / path for path in estimator["files"]]
    tracked = [
        config,
        source,
        corpus,
        coverage,
        output,
        schema,
        build_readme,
        archive_readme,
        data_notice,
        *build_schemas,
        *tools,
        *archives,
        *estimator_files,
    ]
    sums = "".join(
        f"{sha256(path.read_bytes())}  {path.relative_to(repo).as_posix()}\n"
        for path in sorted(
            tracked, key=lambda value: value.relative_to(repo).as_posix()
        )
    )
    (here / "SHA256SUMS").write_text(sums, encoding="ascii", newline="")
    print(output)


if __name__ == "__main__":
    main()
