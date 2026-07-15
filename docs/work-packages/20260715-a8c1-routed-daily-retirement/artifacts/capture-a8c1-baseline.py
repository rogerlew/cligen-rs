#!/usr/bin/env python3
"""Capture A8c retirement and preservation identities before source edits."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).with_name("a8c1-baseline-v1.json")
IMPLEMENTATION_COMMIT = "fdd35f60241f25663614db46142bfe3683c6ce5f"
COMPARATOR_COMMIT = "046eba3c8d4508c84522c6dbd7cec4d39f094563"

REMOVAL_SURFACES = (
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
    "crates/cligen/src/routed_precip.rs",
    "crates/cligen/src/runspec.rs",
    "crates/cligen/src/station/document_v2.rs",
    "crates/cligen/src/station/mod.rs",
    "crates/cligen/src/typed_output.rs",
    "crates/cligen/tests/a8c_routed_daily.rs",
    "docs/specifications/README.md",
    "docs/specifications/SPEC-GENERATION-PROFILES.md",
    "docs/specifications/SPEC-PROVENANCE.md",
    "docs/specifications/SPEC-QUALITY-REPORT.md",
    "docs/specifications/SPEC-RUNSPEC.md",
    "docs/specifications/SPEC-STATION-DOCUMENT.md",
    "docs/specifications/provenance-v1.schema.json",
    "docs/specifications/quality-report-s2-m3.schema.json",
    "docs/specifications/runspec.schema.json",
    "docs/specifications/station-document-v2.schema.json",
)

PRESERVED_ROOTS = (
    ".gitattributes",
    "docs/reports/a7a-daily-precipitation-structure-report.md",
    "docs/reports/a7a-daily-precipitation-structure-report.manifest.json",
    "docs/work-packages/20260714-a7a-daily-precipitation-structure-baseline",
    "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility",
    "docs/work-packages/20260715-a8a-dry-regime-applicability",
    "docs/work-packages/20260715-a8b-secondary-year-fallback",
    "docs/work-packages/20260715-a8c-routed-daily-pilot",
    "docs/work-packages/20260715-a9a-successor-family-foundation",
    "references/observed/a8a-v1",
)

MUTABLE_STATUS_DOCS = (
    "docs/ROADMAP.md",
    "docs/specifications/SPEC-A8C-ROUTED-DAILY.md",
    "docs/work-packages/README.md",
    "docs/work-packages/20260715-a8c1-routed-daily-retirement/package.md",
)


def run(*args: str) -> bytes:
    return subprocess.check_output(args, cwd=ROOT)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def expand(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative in paths:
        path = ROOT / relative
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file() and "__pycache__" not in candidate.parts
            )
        else:
            raise SystemExit(f"missing baseline path: {relative}")
    return sorted(set(files))


def comparator_identity(relative: str) -> dict[str, object] | None:
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{COMPARATOR_COMMIT}:{relative}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode != 0:
        return None
    data = run("git", "show", f"{COMPARATOR_COMMIT}:{relative}")
    return {"bytes": len(data), "sha256": sha256(data)}


def main() -> None:
    source_commit = run("git", "rev-parse", "HEAD").decode().strip()
    if source_commit != "49a67775d22f0452bbf65f0a1ad35435e0d340f9":
        raise SystemExit(f"unexpected dispatch commit: {source_commit}")
    run("git", "cat-file", "-e", f"{IMPLEMENTATION_COMMIT}^{{commit}}")
    run("git", "cat-file", "-e", f"{COMPARATOR_COMMIT}^{{commit}}")

    removal = []
    for relative in REMOVAL_SURFACES:
        current = identity(ROOT / relative)
        current["comparator"] = comparator_identity(relative)
        removal.append(current)

    preserved_files = expand(PRESERVED_ROOTS)
    preserved = [identity(path) for path in preserved_files]
    mutable = [identity(ROOT / relative) for relative in MUTABLE_STATUS_DOCS]

    archive_relative = (
        "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/"
        "a8c-retained-streams-v1.tar.gz"
    )
    archive = next(item for item in preserved if item["path"] == archive_relative)
    if archive["sha256"] != "ee50d033c6022f9988fc4734cd892d518866dd7df7a35aba24448399ee47edae":
        raise SystemExit("A8c retained archive does not match the accepted identity")

    document = {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "pre_a8c_comparator_commit": COMPARATOR_COMMIT,
        "removal_surfaces": removal,
        "preserved_records": preserved,
        "mutable_status_documents": mutable,
        "counts": {
            "removal_surfaces": len(removal),
            "preserved_records": len(preserved),
            "mutable_status_documents": len(mutable),
        },
    }
    OUTPUT.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(sha256(OUTPUT.read_bytes()))


if __name__ == "__main__":
    main()
