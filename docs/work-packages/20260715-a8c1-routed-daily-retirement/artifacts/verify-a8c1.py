#!/usr/bin/env python3
"""Verify A8c runtime retirement and immutable evidence preservation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASELINE = HERE / "a8c1-baseline-v1.json"
IMPLEMENTATION_COMMIT = "fdd35f60241f25663614db46142bfe3683c6ce5f"
COMPARATOR_COMMIT = "046eba3c8d4508c84522c6dbd7cec4d39f094563"

DELETED = {
    "crates/cligen/src/routed_precip.rs",
    "crates/cligen/src/station/document_v2.rs",
    "crates/cligen/tests/a8c_routed_daily.rs",
    "docs/specifications/station-document-v2.schema.json",
}

RESTORED = {
    "crates/cligen/schemas/provenance-v1.schema.json",
    "crates/cligen/schemas/quality-report-s2-m3.schema.json",
    "crates/cligen/src/daily.rs",
    "crates/cligen/src/fast_batch.rs",
    "crates/cligen/src/lib.rs",
    "crates/cligen/src/modes.rs",
    "crates/cligen/src/parquet_output.rs",
    "crates/cligen/src/profile.rs",
    "crates/cligen/src/provenance.rs",
    "crates/cligen/src/quality/mod.rs",
    "crates/cligen/src/quality/report.rs",
    "crates/cligen/src/runspec.rs",
    "crates/cligen/src/station/mod.rs",
    "crates/cligen/src/typed_output.rs",
    "docs/specifications/SPEC-GENERATION-PROFILES.md",
    "docs/specifications/SPEC-PROVENANCE.md",
    "docs/specifications/SPEC-QUALITY-REPORT.md",
    "docs/specifications/SPEC-RUNSPEC.md",
    "docs/specifications/SPEC-STATION-DOCUMENT.md",
    "docs/specifications/provenance-v1.schema.json",
    "docs/specifications/quality-report-s2-m3.schema.json",
    "docs/specifications/runspec.schema.json",
}

RETIRED_TOKENS = (
    "a8c_routed_daily_v1",
    "a8c_integrated_daily_v1",
    "a8a_o2_logqspline_gaussian_copula_v1",
    "legacy_daily_fallback",
    "legacy_daily_only_v1",
    "cligen_randn_5_32_3_plus_splitmix64_daily_v1",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def run(*args: str) -> bytes:
    try:
        return subprocess.check_output(args, cwd=ROOT, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        fail(f"command failed ({' '.join(args)}): {error.output.decode().strip()}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_identity(record: dict[str, object]) -> None:
    path = ROOT / str(record["path"])
    if not path.is_file():
        fail(f"preserved record missing: {record['path']}")
    data = path.read_bytes()
    if len(data) != record["bytes"] or sha256(data) != record["sha256"]:
        fail(f"preserved record changed: {record['path']}")


def verify_removal_surfaces(baseline: dict[str, object]) -> None:
    records = {
        str(record["path"]): record
        for record in baseline["removal_surfaces"]  # type: ignore[index]
    }
    expected = DELETED | RESTORED | {"docs/specifications/README.md"}
    if set(records) != expected:
        fail("baseline removal-surface set differs from the reviewed inventory")

    for relative in DELETED:
        if (ROOT / relative).exists():
            fail(f"retired A8c-only surface still exists: {relative}")

    for relative in RESTORED:
        comparator = records[relative]["comparator"]
        if comparator is None:
            fail(f"restored path has no comparator identity: {relative}")
        data = (ROOT / relative).read_bytes()
        if len(data) != comparator["bytes"] or sha256(data) != comparator["sha256"]:
            fail(f"surface does not equal pre-A8c comparator: {relative}")


def verify_retired_tokens_absent() -> None:
    current_roots = (ROOT / "crates",)
    current_specs = tuple(
        path
        for path in (ROOT / "docs/specifications").iterdir()
        if path.is_file() and path.name != "SPEC-A8C-ROUTED-DAILY.md"
    )
    files = []
    for root in current_roots:
        files.extend(path for path in root.rglob("*") if path.is_file())
    files.extend(current_specs)
    for path in files:
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for token in RETIRED_TOKENS:
            if token in text:
                fail(f"retired token {token!r} remains in {path.relative_to(ROOT)}")


def verify_historical_record() -> None:
    spec = (ROOT / "docs/specifications/SPEC-A8C-ROUTED-DAILY.md").read_text()
    required = (
        "Status: retired historical specification; runtime retired by A8c1",
        IMPLEMENTATION_COMMIT,
        "no longer accepted or implemented on current `main`",
    )
    for text in required:
        if text not in spec:
            fail(f"historical A8c specification lacks retirement marker: {text}")

    registry = (ROOT / "docs/specifications/README.md").read_text()
    if "**RETIRED** (rev 1; runtime and accepted schemas removed by A8c1)" not in registry:
        fail("specification registry does not identify A8c as retired")
    if "station-document-v2.schema.json" in registry:
        fail("specification registry still advertises station document v2")


def verify_history_and_lfs(baseline: dict[str, object]) -> None:
    run("git", "cat-file", "-e", f"{IMPLEMENTATION_COMMIT}^{{commit}}")
    run("git", "merge-base", "--is-ancestor", IMPLEMENTATION_COMMIT, "HEAD")
    run("git", "cat-file", "-e", f"{COMPARATOR_COMMIT}^{{commit}}")

    archive_relative = (
        "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/"
        "a8c-retained-streams-v1.tar.gz"
    )
    archive = next(
        record
        for record in baseline["preserved_records"]  # type: ignore[index]
        if record["path"] == archive_relative
    )
    archive_data = (ROOT / archive_relative).read_bytes()
    if sha256(archive_data) != archive["sha256"] or len(archive_data) != archive["bytes"]:
        fail("A8c retained-stream archive changed")

    attr = run("git", "check-attr", "filter", "--", archive_relative).decode()
    if not attr.rstrip().endswith("filter: lfs"):
        fail("A8c retained-stream archive is not covered by Git LFS")

    pointer = run("git", "show", f"HEAD:{archive_relative}").decode()
    expected_oid = f"oid sha256:{archive['sha256']}"
    expected_size = f"size {archive['bytes']}"
    if expected_oid not in pointer or expected_size not in pointer:
        fail("HEAD does not retain the expected A8c LFS pointer")


def verify_schema_mirrors() -> None:
    pairs = (
        (
            "docs/specifications/provenance-v1.schema.json",
            "crates/cligen/schemas/provenance-v1.schema.json",
        ),
        (
            "docs/specifications/quality-report-s2-m3.schema.json",
            "crates/cligen/schemas/quality-report-s2-m3.schema.json",
        ),
    )
    for documentation, runtime in pairs:
        if (ROOT / documentation).read_bytes() != (ROOT / runtime).read_bytes():
            fail(f"schema mirror mismatch: {documentation} != {runtime}")


def verify_package_surface() -> None:
    metadata = run("cargo", "metadata", "--no-deps", "--format-version", "1")
    package_list = run("cargo", "package", "--list", "--allow-dirty", "-p", "cligen")
    for token in RETIRED_TOKENS + (
        "routed_precip.rs",
        "document_v2.rs",
        "a8c_routed_daily.rs",
        "station-document-v2.schema.json",
    ):
        if token.encode() in metadata or token.encode() in package_list:
            fail(f"retired surface appears in Cargo metadata/package contents: {token}")


def main() -> None:
    baseline = json.loads(BASELINE.read_text())
    if baseline["implementation_commit"] != IMPLEMENTATION_COMMIT:
        fail("baseline implementation commit changed")
    if baseline["pre_a8c_comparator_commit"] != COMPARATOR_COMMIT:
        fail("baseline comparator commit changed")
    if baseline["counts"] != {
        "mutable_status_documents": 4,
        "preserved_records": 148,
        "removal_surfaces": 27,
    }:
        fail("baseline counts changed")

    for record in baseline["preserved_records"]:
        require_identity(record)
    verify_removal_surfaces(baseline)
    verify_retired_tokens_absent()
    verify_historical_record()
    verify_history_and_lfs(baseline)
    verify_schema_mirrors()
    verify_package_surface()
    print(
        "PASS: 27 retirement surfaces dispositioned; 148 preserved records "
        "verified; A8c history/LFS retained; current package surface clean"
    )


if __name__ == "__main__":
    main()
