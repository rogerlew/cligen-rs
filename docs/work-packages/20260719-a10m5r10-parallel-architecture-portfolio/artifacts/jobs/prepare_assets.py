#!/usr/bin/env python3
"""Prepare immutable assets for the A10M5R10 Lemhi portfolio run."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
R3 = REPO / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee"
M8 = REPO / "docs/work-packages/20260719-a10m5r8-climate-statistics-objective"
M9 = REPO / "docs/work-packages/20260719-a10m5r9-climate-normal-residual-architecture"
RECONSTRUCTION = (
    REPO
    / "docs/work-packages/20260718-a10m5r4r2r1-reconstruction-identity-remedy"
    / "artifacts/reconstruction-contract.json"
)

CANDIDATE_ROLES = (
    "monthly-residual-adapter-k1",
    "monthly-residual-adapter-k2",
    "annual-monthly-residual-adapter-k1",
    "annual-monthly-residual-adapter-k2",
    "hierarchical-joint-factor-adapter-k1",
    "hierarchical-joint-factor-adapter-k2",
    "climate-normal-hierarchical-state-space-k1",
    "climate-normal-hierarchical-state-space-k2",
    "physics-conditioned-hierarchical-adapter-k1",
    "physics-conditioned-hierarchical-adapter-k2",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise RuntimeError(f"required source absent: {source}")
    shutil.copyfile(source, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--canonical-cache", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    options = parser.parse_args()
    root = options.asset_root.resolve()
    cache = options.canonical_cache.resolve()
    root.mkdir(parents=True, exist_ok=True)

    canonical = ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar")
    for name in canonical:
        copy(cache / name, root / name)

    package_jobs = PACKAGE / "artifacts/jobs"
    package_assets = [
        "portfolio_core.py",
        "materialize_controls.py",
        "candidate_experiment.py",
        "select_portfolio.py",
        "run_control.sh",
        "job-control-materialization.sh",
        "run_candidate.sh",
        "job-common-candidate.sh",
        *(f"job-{role}.sh" for role in CANDIDATE_ROLES),
    ]
    for name in package_assets:
        copy(package_jobs / name, root / name)

    inherited = {
        "climate_core.py": M8 / "artifacts/jobs/climate_core.py",
        "residual_core.py": M9 / "artifacts/jobs/residual_core.py",
        "screen_core_v2.py": R3 / "artifacts/jobs/screen_core_v2.py",
        "train.py": R3 / "artifacts/jobs/train.py",
        "legacy_core.py": (
            REPO
            / "docs/work-packages/20260717-a10m5-bounded-gpu-screen"
            / "artifacts/jobs/screen.py"
        ),
        "portfolio-contract.json": PACKAGE / "artifacts/portfolio-contract.json",
        "reconstruction-contract.json": RECONSTRUCTION,
        "a10-daymet-calendar-profile-v1.json": (
            REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json"
        ),
    }
    for name, source in inherited.items():
        copy(source, root / name)

    toolkit_assets = {
        "recover-job-local-v2.sh": (
            REPO / "research/a10/lemhi_toolkit/remote/recover_job_local_v2.sh"
        ),
        "supervise-v2.sh": REPO / "research/a10/lemhi_toolkit/remote/supervise_v2.sh",
    }
    for name, source in toolkit_assets.items():
        copy(source, root / name)

    recovery = {
        "invoked": False,
        "reason": "all primary roles own supervised job-local cleanup",
    }
    (root / "recovery.json").write_text(
        json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    generated = [
        *package_assets,
        *inherited,
        *toolkit_assets,
        "recovery.json",
    ]
    for name in generated:
        if name.endswith((".sh", ".py")):
            (root / name).chmod(0o700)

    manifest = {
        "assets": {name: identity(root / name) for name in (*canonical, *generated)},
        "canonical_configuration_id": "lemhi-a10-py311-l40-v2-candidate",
        "canonical_configuration_semantic_sha256": (
            "5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d"
        ),
        "package_id": "20260719-a10m5r10-parallel-architecture-portfolio",
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": options.source_commit,
    }
    (root / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
