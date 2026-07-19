#!/usr/bin/env python3
"""Prepare immutable assets for the staged A10M5R10R1R1 portfolio rerun."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
SCIENCE_IDENTITY_MANIFEST = PACKAGE / "artifacts/science-dependency-identities.json"
SCIENCE_IDENTITY_MANIFEST_BYTES = 3428
SCIENCE_IDENTITY_MANIFEST_SHA256 = (
    "4c5669c87aa4263fd16c76e20044ae3d865df6665f86d2c2b40868d68788d887"
)
SCIENCE_DEPENDENCY_NAMES = {
    "a10-daymet-calendar-profile-v1.json",
    "candidate_experiment.py",
    "climate_core.py",
    "legacy_core.py",
    "materialize_controls.py",
    "portfolio-contract.json",
    "portfolio_core.py",
    "reconstruction-contract.json",
    "residual_core.py",
    "screen_core_v2.py",
    "select_portfolio.py",
    "train.py",
}
PREDECESSOR_IDENTITY_MANIFEST = PACKAGE / "artifacts/predecessor-evidence-identities.json"
PREDECESSOR_IDENTITY_MANIFEST_BYTES = 2946
PREDECESSOR_IDENTITY_MANIFEST_SHA256 = (
    "f9f559d4ae5c12d66f7254b41339bb2ebaf8846620202e164e83191c3a0c26f5"
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


def load_science_identities() -> dict[str, dict[str, object]]:
    if identity(SCIENCE_IDENTITY_MANIFEST) != {
        "bytes": SCIENCE_IDENTITY_MANIFEST_BYTES,
        "sha256": SCIENCE_IDENTITY_MANIFEST_SHA256,
    }:
        raise RuntimeError("science dependency identity manifest byte drift")
    document = json.loads(SCIENCE_IDENTITY_MANIFEST.read_text(encoding="utf-8"))
    if (
        document.get("schema_version") != 1
        or document.get("package_id")
        != "20260719-a10m5r10r1-candidate-job-local-capacity-remedy"
        or document.get("predecessor_package_id")
        != "20260719-a10m5r10-parallel-architecture-portfolio"
        or document.get("predecessor_source_commit")
        != "cbf73d781df09f466d66e31d2569ca19ffaa0faf"
        or set(document.get("dependencies", {})) != SCIENCE_DEPENDENCY_NAMES
    ):
        raise RuntimeError("science dependency identity manifest mismatch")
    dependencies = document["dependencies"]
    for name, expected in dependencies.items():
        if (
            set(expected) != {"bytes", "sha256", "source_path"}
            or not isinstance(expected["bytes"], int)
            or expected["bytes"] <= 0
            or not isinstance(expected["sha256"], str)
            or len(expected["sha256"]) != 64
            or not isinstance(expected["source_path"], str)
        ):
            raise RuntimeError(f"malformed science dependency identity: {name}")
    return dependencies


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

    science_identities = load_science_identities()
    repo_root = REPO.resolve()
    for name, expected in science_identities.items():
        source = (REPO / str(expected["source_path"])).resolve()
        if not source.is_relative_to(repo_root):
            raise RuntimeError(f"science dependency escapes repository: {name}")
        actual = identity(source)
        if actual != {"bytes": expected["bytes"], "sha256": expected["sha256"]}:
            raise RuntimeError(f"frozen predecessor science drift: {name}: {actual}")
        copy(source, root / name)
        copied = identity(root / name)
        if copied != actual:
            raise RuntimeError(f"materialized predecessor science drift: {name}: {copied}")
    copy(SCIENCE_IDENTITY_MANIFEST, root / "science-dependency-identities.json")
    if identity(root / "science-dependency-identities.json") != identity(
        SCIENCE_IDENTITY_MANIFEST
    ):
        raise RuntimeError("materialized science identity manifest drift")
    if identity(PREDECESSOR_IDENTITY_MANIFEST) != {
        "bytes": PREDECESSOR_IDENTITY_MANIFEST_BYTES,
        "sha256": PREDECESSOR_IDENTITY_MANIFEST_SHA256,
    }:
        raise RuntimeError("predecessor evidence identity manifest byte drift")
    copy(
        PREDECESSOR_IDENTITY_MANIFEST,
        root / "predecessor-evidence-identities.json",
    )

    package_jobs = PACKAGE / "artifacts/jobs"
    package_assets = [
        "admission_checker.py",
        "setup_diagnostics.py",
        "bootstrap_environment.sh",
        "run_control.sh",
        "job-control-materialization.sh",
        "run_candidate.sh",
        "job-common-candidate.sh",
        *(f"job-{role}.sh" for role in CANDIDATE_ROLES),
    ]
    for name in package_assets:
        copy(package_jobs / name, root / name)

    inherited = {
        "job-local-capacity-contract.json": (
            PACKAGE / "artifacts/job-local-capacity-contract.json"
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
        *science_identities,
        "science-dependency-identities.json",
        "predecessor-evidence-identities.json",
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
        "package_id": "20260719-a10m5r10r1r1-python311-control-plane-remedy",
        "protected_roles_opened": [],
        "schema_version": 1,
        "science_dependency_identities": {
            "dependencies": science_identities,
            "manifest": identity(root / "science-dependency-identities.json"),
        },
        "source_commit": options.source_commit,
    }
    (root / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
