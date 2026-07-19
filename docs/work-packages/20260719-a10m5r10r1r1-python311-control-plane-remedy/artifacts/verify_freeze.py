#!/usr/bin/env python3
"""Verify the A10M5R10R1R1 science, predecessor, and interpreter freeze."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
R0 = REPO / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio"
JOBS = PACKAGE / "artifacts/jobs"
PACKAGE_ID = "20260719-a10m5r10r1r1-python311-control-plane-remedy"
RUN_ID = "a10m5r10r1r1-python311-control-plane-remedy-r0"
SCIENCE_MANIFEST_SHA256 = (
    "4c5669c87aa4263fd16c76e20044ae3d865df6665f86d2c2b40868d68788d887"
)
PREDECESSOR_MANIFEST_SHA256 = (
    "f9f559d4ae5c12d66f7254b41339bb2ebaf8846620202e164e83191c3a0c26f5"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path):
    specification = importlib.util.spec_from_file_location(path.stem, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def verify_control_plane_sources() -> None:
    staged = (
        "admission_checker.py",
        "setup_diagnostics.py",
        "bootstrap_environment.sh",
        "run_control.sh",
        "job-control-materialization.sh",
        "run_candidate.sh",
        "job-common-candidate.sh",
    )
    bad_absolute = re.compile(r"/usr/bin/python3(?!\.11)")
    bad_bare = re.compile(r"(?<![/A-Za-z0-9_$])python3(?=\s|$)", re.MULTILINE)
    for name in staged:
        text = (JOBS / name).read_text(encoding="utf-8")
        assert bad_absolute.search(text) is None, name
        assert bad_bare.search(text) is None, name
    assert (JOBS / "admission_checker.py").read_text(encoding="utf-8").startswith(
        "#!/usr/bin/python3.11\n"
    )
    assert (JOBS / "setup_diagnostics.py").read_text(encoding="utf-8").startswith(
        "#!/usr/bin/python3.11\n"
    )
    bootstrap = (JOBS / "bootstrap_environment.sh").read_text(encoding="utf-8")
    assert 'host_python=/usr/bin/python3.11' in bootstrap
    assert "run_logged host-python-version" in bootstrap
    assert bootstrap.index("run_logged host-python-version") < bootstrap.index(
        "runtime-extract"
    )
    assert '"$runtime_root/bin/python3" -m venv' in bootstrap
    candidate = (JOBS / "run_candidate.sh").read_text(encoding="utf-8")
    assert '"$environment/bin/python" "$run_root/candidate_experiment.py"' in candidate


def main() -> None:
    remedy = json.loads(
        (PACKAGE / "artifacts/job-local-capacity-contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert remedy["package_id"] == PACKAGE_ID
    assert remedy["predecessor_package_id"] == (
        "20260719-a10m5r10r1-candidate-job-local-capacity-remedy"
    )
    calendar = PACKAGE / "artifacts/calendar-preflight.json"
    assert calendar.stat().st_size == 578
    assert digest(calendar) == remedy["calendar_preflight"]["sha256"] == (
        "7f58a20eae635d9453ea86a473072b9e2597195ffc1d71660184d3e70b130a68"
    )
    assert calendar.read_bytes() == (R0 / "artifacts/calendar-preflight.json").read_bytes()

    science_manifest = PACKAGE / "artifacts/science-dependency-identities.json"
    assert science_manifest.stat().st_size == 3428
    assert digest(science_manifest) == SCIENCE_MANIFEST_SHA256
    assert remedy["science_dependency_manifest"]["sha256"] == SCIENCE_MANIFEST_SHA256
    science = remedy["science_contract"]["files"]
    sources = {
        "portfolio-contract.json": R0 / "artifacts/portfolio-contract.json",
        **{
            name: R0 / "artifacts/jobs" / name
            for name in science
            if name != "portfolio-contract.json"
        },
    }
    for name, expected in science.items():
        assert digest(sources[name]) == expected, name

    predecessor_manifest = PACKAGE / "artifacts/predecessor-evidence-identities.json"
    assert predecessor_manifest.stat().st_size == 2946
    assert digest(predecessor_manifest) == PREDECESSOR_MANIFEST_SHA256
    assert remedy["predecessor_evidence"]["identity_manifest"] == {
        "bytes": 2946,
        "path": "artifacts/predecessor-evidence-identities.json",
        "sha256": PREDECESSOR_MANIFEST_SHA256,
    }
    builder = load_module(JOBS / "build_control_records.py")
    predecessor = builder.predecessor_bundle()
    assert set(predecessor["predecessors"]) == {
        "a10m5r10r1_operational_hold",
        "a10m5o1r2_toolkit_hardening",
    }
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    toolkit_proof = builder.toolkit_ancestry(head)
    assert toolkit_proof["hardening_commit"] == (
        "0ddffd9ac5db2440f74f54285e0df1c2ac856c98"
    )
    assert toolkit_proof["hardening_commit_is_ancestor"] is True
    assert toolkit_proof["diff_from_hardening_commit_empty"] is True

    failure = remedy["observed_failure"]
    assert failure["failure_class"] == "host-default-python36-before-runtime-extraction"
    assert failure["runtime_archive_opened"] is False
    assert failure["wheelhouse_archive_opened"] is False
    assert failure["scientific_interpretation"] == "none"
    control_plane = remedy["control_plane"]
    assert control_plane["host_python_path"] == "/usr/bin/python3.11"
    assert control_plane["required_major_minor"] == "3.11"
    assert control_plane["verified_before_runtime_extraction"] is True

    portfolio = json.loads(sources["portfolio-contract.json"].read_text(encoding="utf-8"))
    portfolio_roles = [item["role_id"] for item in portfolio["roles"]]
    waves = remedy["admission"]["waves"]
    assert len(waves) == 5 and all(len(wave) == 2 for wave in waves)
    flattened = [role for wave in waves for role in wave]
    assert flattened == portfolio_roles and len(set(flattened)) == 10
    assert remedy["admission"]["maximum_live_candidate_jobs"] == 2
    assert remedy["admission"]["maximum_simultaneous_bootstraps"] == 1
    resources = remedy["resources"]
    assert (
        resources["control_minutes"]
        + resources["candidate_role_count"] * resources["candidate_minutes_each"]
        + resources["recovery_minutes"]
        == resources["total_gpu_minute_ceiling"]
        == 935
    )
    assert resources["attempts_per_role"] == resources["gpus_per_role"] == 1
    assert resources["scientific_retries"] is False

    for path in (*JOBS.glob("*.py"), PACKAGE / "artifacts/verify_freeze.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for role in ("control-materialization", *portfolio_roles):
        allowlist = builder.evidence_for_role(role)
        assert f"results/{role}/setup.json" in allowlist
        assert f"results/{role}/setup.log" in allowlist
        assert f"results/{role}/supervisor.json" in allowlist
        assert f"admissions/{role}.json" in allowlist

    expected_wrappers = {
        f"job-{item['role_id']}.sh": (
            item["role_id"],
            item["architecture"],
            item["capacity"],
        )
        for item in portfolio["roles"]
    }
    for name, values in expected_wrappers.items():
        text = (JOBS / name).read_text(encoding="utf-8")
        assert "exec ./job-common-candidate.sh " + " ".join(values) in text

    verify_control_plane_sources()
    checker = (JOBS / "admission_checker.py").read_text(encoding="utf-8")
    assert '"control_plane_python311"' in checker
    assert '"record_type": "a10m5r10r1r1-submission-admission"' in checker
    prepare = load_module(JOBS / "prepare_assets.py")
    assert tuple(flattened) == prepare.CANDIDATE_ROLES
    print("A10M5R10R1R1-PYTHON311-CONTROL-PLANE-FREEZE-VERIFIED")


if __name__ == "__main__":
    main()
