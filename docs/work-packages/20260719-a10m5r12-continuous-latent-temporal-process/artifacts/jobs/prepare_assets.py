#!/usr/bin/env python3
"""Prepare immutable A10M5R12 execution assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260719-a10m5r12-continuous-latent-temporal-process"
ROLES = (
    "continuous-medium-latent-process-k2",
    "continuous-hierarchical-latent-process-k2",
)
SCIENCE = {
    "a10-daymet-calendar-profile-v1.json": "docs/specifications/a10-daymet-calendar-profile-v1.json",
    "climate_core.py": "docs/work-packages/20260719-a10m5r8-climate-statistics-objective/artifacts/jobs/climate_core.py",
    "legacy_core.py": "docs/work-packages/20260717-a10m5-bounded-gpu-screen/artifacts/jobs/screen.py",
    "materialize_controls.py": "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/jobs/materialize_controls.py",
    "portfolio-contract.json": "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/portfolio-contract.json",
    "portfolio_core.py": "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/jobs/portfolio_core.py",
    "reconstruction-contract.json": "docs/work-packages/20260718-a10m5r4r2r1-reconstruction-identity-remedy/artifacts/reconstruction-contract.json",
    "residual_core.py": "docs/work-packages/20260719-a10m5r9-climate-normal-residual-architecture/artifacts/jobs/residual_core.py",
    "screen_core_v2.py": "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/artifacts/jobs/screen_core_v2.py",
    "train.py": "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/artifacts/jobs/train.py",
    "canonical-configuration.json": "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json",
    "canonical-designation-index.json": "research/a10/lemhi_toolkit/configurations/lemhi-canonical-designation-index-v1.json",
}
PACKAGE_ASSETS = (
    "admission_checker.py", "setup_diagnostics.py", "bootstrap_environment.sh",
    "run_control.sh", "job-control-materialization.sh",
    "run_temporal_candidate.sh", "job-common-candidate.sh",
    "continuous_candidate_experiment.py", "continuous_core.py", "temporal_metrics.py",
    *(f"job-{role}.sh" for role in ROLES),
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
    if not source.is_file() or source.is_symlink():
        raise RuntimeError(f"required regular source absent: {source}")
    shutil.copyfile(source, target)


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def verify_published_source(commit: str) -> None:
    identities = {
        subprocess.run(
            ("git", "rev-parse", name), cwd=REPO, check=True, capture_output=True, text=True
        ).stdout.strip()
        for name in ("HEAD", "origin/main")
    }
    branch = subprocess.run(
        ("git", "branch", "--show-current"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if identities != {commit} or branch != "main" or Path(__file__).read_bytes() != git_bytes(commit, relative):
        raise RuntimeError("source commit is not the exact published main scaffold")


def committed_copy(commit: str, relative: str, target: Path) -> None:
    target.write_bytes(git_bytes(commit, relative))


def verify_canonical_cache(root: Path, commit: str) -> None:
    configuration = json.loads(
        git_bytes(
            commit,
            "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json",
        )
    )
    designation = json.loads(
        git_bytes(
            commit,
            "research/a10/lemhi_toolkit/configurations/lemhi-canonical-designation-index-v1.json",
        )
    )
    current = designation["current"]
    if not (
        current["status"] == "current"
        and current["configuration_id"] == configuration["configuration_id"]
        and current["configuration_semantic_sha256"]
        == configuration["configuration_semantic_sha256"]
        == "5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d"
    ):
        raise RuntimeError("canonical designation/configuration identity drift")
    expected = {
        "runtime.tar.gz": {
            "bytes": configuration["runtime"]["artifact_bytes"],
            "sha256": configuration["runtime"]["artifact_sha256"],
        },
        "wheelhouse.tar": {
            "bytes": configuration["framework"]["wheelhouse_bytes"],
            "sha256": configuration["framework"]["wheelhouse_sha256"],
        },
        "requirements.lock": {
            "sha256": configuration["framework"]["requirements_lock_sha256"],
        },
    }
    for name, pin in expected.items():
        path = root / name
        if digest(path) != pin["sha256"] or (
            "bytes" in pin and path.stat().st_size != pin["bytes"]
        ):
            raise RuntimeError(f"canonical configuration asset drift: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--canonical-cache", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    options = parser.parse_args()
    verify_published_source(options.source_commit)
    verify_canonical_cache(options.canonical_cache.resolve(), options.source_commit)
    root = options.asset_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    source_paths: dict[str, str] = {}
    for name in ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar"):
        copy(options.canonical_cache.resolve() / name, root / name)
    for name, relative in SCIENCE.items():
        committed_copy(options.source_commit, relative, root / name)
        generated.append(name)
        source_paths[name] = relative
    for name in PACKAGE_ASSETS:
        relative = (PACKAGE / "artifacts/jobs" / name).relative_to(REPO).as_posix()
        committed_copy(options.source_commit, relative, root / name)
        generated.append(name)
        source_paths[name] = relative
    inherited = {
        "calendar-preflight.json": PACKAGE / "artifacts/calendar-preflight.json",
        "calendar-control-expectation.json": PACKAGE / "artifacts/calendar-control-expectation.json",
        "temporal-contract.json": PACKAGE / "artifacts/temporal-contract.json",
        "sites.json": PACKAGE / "artifacts/sites.json",
        "corpus-layout-pin.json": PACKAGE / "artifacts/corpus-layout-pin.json",
        "job-local-capacity-contract.json": PACKAGE / "artifacts/job-local-capacity-contract.json",
    }
    for name, source in inherited.items():
        relative = source.relative_to(REPO).as_posix()
        committed_copy(options.source_commit, relative, root / name)
        generated.append(name)
        source_paths[name] = relative
    toolkit = {
        "recover-job-local-v2.sh": REPO / "research/a10/lemhi_toolkit/remote/recover_job_local_v2.sh",
        "supervise-v2.sh": REPO / "research/a10/lemhi_toolkit/remote/supervise_v2.sh",
    }
    for name, source in toolkit.items():
        relative = source.relative_to(REPO).as_posix()
        committed_copy(options.source_commit, relative, root / name)
        generated.append(name)
        source_paths[name] = relative
    recovery = {"invoked": False, "reason": "primary roles own supervised cleanup"}
    (root / "recovery.json").write_text(
        json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    generated.append("recovery.json")
    for name in generated:
        if name.endswith((".py", ".sh")):
            (root / name).chmod(0o700)
    names = ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar", *generated)
    manifest = {
        "assets": {
            name: {
                **identity(root / name),
                **({"source_path": source_paths[name]} if name in source_paths else {}),
            }
            for name in names
        },
        "canonical_configuration_id": "lemhi-a10-py311-l40-v2-candidate",
        "canonical_configuration_semantic_sha256": "5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d",
        "package_id": PACKAGE_ID,
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
