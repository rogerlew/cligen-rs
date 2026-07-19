#!/usr/bin/env python3
"""Verify the A10M5R10R1 science identity and capacity-remedy freeze."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
R0 = REPO / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio"
JOBS = PACKAGE / "artifacts/jobs"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path):
    specification = importlib.util.spec_from_file_location(path.stem, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def main() -> None:
    remedy = json.loads(
        (PACKAGE / "artifacts/job-local-capacity-contract.json").read_text(
            encoding="utf-8"
        )
    )
    calendar = PACKAGE / "artifacts/calendar-preflight.json"
    assert calendar.stat().st_size == 578
    assert digest(calendar) == remedy["calendar_preflight"]["sha256"] == (
        "7f58a20eae635d9453ea86a473072b9e2597195ffc1d71660184d3e70b130a68"
    )
    assert calendar.read_bytes() == (
        R0 / "artifacts/calendar-preflight.json"
    ).read_bytes()
    science_manifest = PACKAGE / "artifacts/science-dependency-identities.json"
    assert digest(science_manifest) == remedy["science_dependency_manifest"][
        "sha256"
    ] == "4c5669c87aa4263fd16c76e20044ae3d865df6665f86d2c2b40868d68788d887"
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
        actual = digest(sources[name])
        assert actual == expected, (name, actual, expected)

    failure = remedy["observed_failure"]
    assert failure["wheelhouse_archive_bytes"] + failure[
        "installed_environment_payload_bytes"
    ] == failure["per_bootstrap_lower_bound_bytes"]
    assert failure["candidate_evidence_published"] is False
    assert failure["supervised_cleanup_succeeded"] is True
    assert failure["scientific_interpretation"] == "none"
    predecessor = remedy["predecessor_evidence"]
    assert predecessor["operator_supplied_path_and_sha256_required"] == [
        "operational-summary.json",
        "resource-ledger.md",
        "toolkit-recovered/terminal.json",
        "toolkit-recovered/cleanup.json",
    ]
    assert predecessor["authority_field"] == "predecessor_r0_evidence"
    assert predecessor["toolkit_genesis_predecessor_evidence"] == []
    assert predecessor["closed_run_required"] is True
    assert predecessor["verified_cleanup_required"] is True

    portfolio = json.loads(sources["portfolio-contract.json"].read_text(encoding="utf-8"))
    portfolio_roles = [item["role_id"] for item in portfolio["roles"]]
    waves = remedy["admission"]["waves"]
    assert len(waves) == 5
    assert all(len(wave) == 2 for wave in waves)
    flattened = [role for wave in waves for role in wave]
    assert flattened == portfolio_roles
    assert len(set(flattened)) == 10
    admission = remedy["admission"]
    assert admission["control_must_pass_before_candidates"] is True
    assert admission["maximum_live_candidate_jobs"] == 2
    assert admission["maximum_simultaneous_bootstraps"] == 1
    assert admission["second_role_requires_first_setup_ready"] is True
    assert admission["next_wave_requires_prior_terminal_observed_cleanup"] is True
    assert admission["checker"] == "admission_checker.py"
    assert admission["execution_location"] == "staged-remote-run"
    assert admission["receipt_template"] == "admissions/{role_id}.json"
    assert admission["atomic_receipt"] is True
    assert admission["job_wrapper_requires_authenticated_receipt"] is True

    resources = remedy["resources"]
    total = (
        resources["control_minutes"]
        + resources["candidate_role_count"] * resources["candidate_minutes_each"]
        + resources["recovery_minutes"]
    )
    assert total == resources["total_gpu_minute_ceiling"] == 935
    assert resources["attempts_per_role"] == 1
    assert resources["gpus_per_role"] == 1
    assert resources["distributed_training"] is False
    assert resources["job_arrays"] is False
    assert resources["scientific_retries"] is False

    job_local = remedy["job_local"]
    assert set(job_local["required_environment"]) == {
        "TMPDIR",
        "PIP_CACHE_DIR",
        "XDG_CACHE_HOME",
        "TORCH_HOME",
    }
    assert set(job_local["delete_after_verified_install"]) == {
        "<JOB_LOCAL>/wheels",
        "<JOB_LOCAL>/pip-cache",
    }
    assert job_local["deletion_before_science"] is True
    assert job_local["required_ready_fields"] == {
        "exit_codes.pip_install": 0,
        "exit_codes.pip_check": 0,
        "cleanup.wheelhouse_deleted_before_science": True,
        "cleanup.pip_cache_deleted_before_science": True,
        "authentication.asset_identities_authenticated": True,
        "authentication.execution_identity_authenticated": True,
        "authentication.submission_admission_authenticated": True,
        "execution_identity.run_id": "a10m5r10r1-candidate-job-local-capacity-remedy-r0",
        "ready_for_science": True,
    }
    assert {
        "authentication",
        "execution_identity",
        "record_sha256",
    } <= set(remedy["setup_diagnostics"]["required_json_fields"])

    python_sources = tuple(JOBS.glob("*.py")) + (PACKAGE / "artifacts/verify_freeze.py",)
    for path in python_sources:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    builder = load_module(JOBS / "build_control_records.py")
    for role in ("control-materialization", *portfolio_roles):
        allowlist = builder.evidence_for_role(role)
        assert f"results/{role}/setup.json" in allowlist
        assert f"results/{role}/setup.log" in allowlist
        assert f"results/{role}/supervisor.json" in allowlist
        assert f"admissions/{role}.json" in allowlist

    bootstrap = (JOBS / "bootstrap_environment.sh").read_text(encoding="utf-8")
    for assignment in (
        "TMPDIR=$job_local/tmp",
        "PIP_CACHE_DIR=$job_local/pip-cache",
        "XDG_CACHE_HOME=$job_local/cache",
        "TORCH_HOME=$job_local/torch-cache",
    ):
        assert assignment in bootstrap
    assert 'rm -rf -- "$job_local/wheels" "$job_local/pip-cache"' in bootstrap
    assert "record_setup verified-install false" in bootstrap
    assert "record_setup ready-for-science true" in bootstrap
    assert bootstrap.index("record_setup verified-install false") < bootstrap.index(
        'rm -rf -- "$job_local/wheels" "$job_local/pip-cache"'
    ) < bootstrap.index("record_setup ready-for-science true")
    assert "if ! run_logged" not in bootstrap
    for item in (
        "--asset-manifest",
        "--admission-receipt",
        "--run-id",
        "--role",
        "--job-id",
        "--node",
        "--owner-marker-sha256",
    ):
        assert item in bootstrap

    expected_wrappers = {
        f"job-{item['role_id']}.sh": (
            item["role_id"], item["architecture"], item["capacity"]
        )
        for item in portfolio["roles"]
    }
    for name, values in expected_wrappers.items():
        text = (JOBS / name).read_text(encoding="utf-8")
        invocation = "exec ./job-common-candidate.sh " + " ".join(values)
        assert invocation in text

    for name in ("job-control-materialization.sh", "job-common-candidate.sh"):
        text = (JOBS / name).read_text(encoding="utf-8")
        assert "$run_root/admissions/$role.json" in text
        assert "submission_admission_authenticated" in text
        assert "setup_execution_identity_authenticated" in text
        assert "setup_asset_identities_authenticated" in text

    checker = (JOBS / "admission_checker.py").read_text(encoding="utf-8")
    assert 'remote_root / "admissions" / f"{target}.json"' in checker
    assert 'remote_root / "admission-input" / "state.json"' in checker
    assert 'state.get("run_state") == "VERIFIED"' in checker
    assert 'state.get("run_state") == "MATRIX_ACTIVE"' in checker

    prepare = load_module(JOBS / "prepare_assets.py")
    assert tuple(flattened) == prepare.CANDIDATE_ROLES
    assert '"admission_checker.py"' in (
        JOBS / "prepare_assets.py"
    ).read_text(encoding="utf-8")

    builder_text = (JOBS / "build_control_records.py").read_text(encoding="utf-8")
    for option in (
        "--predecessor-r0-operational-summary",
        "--predecessor-r0-resource-ledger",
        "--predecessor-r0-terminal",
        "--predecessor-r0-cleanup",
    ):
        assert option in builder_text

    print("A10M5R10R1-CAPACITY-REMEDY-FREEZE-VERIFIED")


if __name__ == "__main__":
    main()
