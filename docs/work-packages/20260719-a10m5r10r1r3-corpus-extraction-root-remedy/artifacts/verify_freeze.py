#!/usr/bin/env python3
"""Verify the A10M5R10R1R3 corpus-root remedy and inherited freeze."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
R0 = REPO / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio"
R1R2 = REPO / (
    "docs/work-packages/20260719-a10m5r10r1r2-portable-bootstrap-control-plane-remedy"
)
JOBS = PACKAGE / "artifacts/jobs"
PACKAGE_ID = "20260719-a10m5r10r1r3-corpus-extraction-root-remedy"
RUN_ID = "a10m5r10r1r3-corpus-extraction-root-remedy-r0"
SCIENCE_MANIFEST_SHA256 = (
    "4c5669c87aa4263fd16c76e20044ae3d865df6665f86d2c2b40868d68788d887"
)
PREDECESSOR_MANIFEST_BYTES = 6138
PREDECESSOR_MANIFEST_SHA256 = (
    "7b8b3ccf81ccd09634ee457d4feec35c4a6811f5fed22c5a8f2ce6ccc74539d3"
)
CORPUS_SHA256 = "8770e127f8413eedd47d50670c359e450988444a8c4d8d43ca5645619a1b0a17"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path):
    specification = importlib.util.spec_from_file_location(path.stem, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def verify_two_file_corpus_delta() -> None:
    old_target = 'tar -xf "$run_root/corpus.tar" -C "$job_local/corpus"'
    new_target = 'tar -xf "$run_root/corpus.tar" -C "$job_local"'
    for name in ("run_control.sh", "run_candidate.sh"):
        old = (R1R2 / "artifacts/jobs" / name).read_text(encoding="utf-8")
        new = (JOBS / name).read_text(encoding="utf-8")
        expected = old.replace(old_target, new_target).replace(
            "A10M5R10R1R2", "A10M5R10R1R3"
        )
        assert old.count(old_target) == 1, name
        assert new.count(new_target) == 1, name
        assert old_target not in new, name
        assert new == expected, name
        assert '--corpus "$job_local/corpus"' in new, name
        assert 'mkdir -p -- "$output" "$job_local/corpus"' in new or (
            'mkdir -p -- "$run_root/slurm" "$output" "$job_local/corpus"' in new
        ), name


def verify_compute_sources() -> None:
    bootstrap = (JOBS / "bootstrap_environment.sh").read_text(encoding="utf-8")
    predecessor_bootstrap = (
        R1R2 / "artifacts/jobs/bootstrap_environment.sh"
    ).read_text(encoding="utf-8")
    assert bootstrap == predecessor_bootstrap.replace(
        "A10M5R10R1R2", "A10M5R10R1R3"
    )
    extraction = bootstrap.index(
        "if run_pre_python_logged runtime-extract tar -xzf"
    )
    version = bootstrap.index(
        'if run_pre_python_logged runtime-version "$host_python" --version'
    )
    diagnostics = bootstrap.index(
        '"$runtime_root/bin/python3" "$run_root/setup_diagnostics.py" record'
    )
    inline_check = bootstrap.index('"$runtime_root/bin/python3" -c')
    assert extraction < version < diagnostics < inline_check
    assert "/usr/bin/python3" not in bootstrap
    assert 'host_python=$runtime_root/bin/python3' in bootstrap
    assert '"$runtime_root/bin/python3" -m venv' in bootstrap
    assert '"Python 3.11.15"' in bootstrap
    assert "setup_log_limit=65536" in bootstrap
    assert 'tail -c "$setup_log_limit" "$bounded_log" >"$setup_log"' in bootstrap

    run_candidate = (JOBS / "run_candidate.sh").read_text(encoding="utf-8")
    assert run_candidate.index("./bootstrap_environment.sh") < run_candidate.index(
        '"$environment/bin/python" -c'
    )
    assert "/usr/bin/python3" not in run_candidate
    run_control = (JOBS / "run_control.sh").read_text(encoding="utf-8")
    assert "/usr/bin/python3" not in run_control

    for name in ("job-control-materialization.sh", "job-common-candidate.sh"):
        source = (JOBS / name).read_text(encoding="utf-8")
        assert "/usr/bin/python3.11" not in source
        assert source.count("/usr/bin/python3 -") == 2
        snippets = source.split("<<'PY'\n")[1:]
        assert len(snippets) == 2
        for snippet in snippets:
            code = snippet.split("\nPY", 1)[0]
            assert "from __future__" not in code
            ast.parse(code, filename=name, feature_version=(3, 6))

    admission = (JOBS / "admission_checker.py").read_text(encoding="utf-8")
    predecessor_admission = (
        R1R2 / "artifacts/jobs/admission_checker.py"
    ).read_text(encoding="utf-8")
    expected_admission = (
        predecessor_admission.replace("A10M5R10R1R2", "A10M5R10R1R3")
        .replace(
            "20260719-a10m5r10r1r2-portable-bootstrap-control-plane-remedy",
            PACKAGE_ID,
        )
        .replace(
            "a10m5r10r1r2-portable-bootstrap-control-plane-remedy-r0", RUN_ID
        )
        .replace(
            "a10m5r10r1r2-submission-admission",
            "a10m5r10r1r3-submission-admission",
        )
    )
    assert admission == expected_admission
    assert admission.startswith("#!/usr/bin/python3.11\n")
    assert 'host_python.get("path") == "/usr/bin/python3.11"' in admission
    assert '"record_type": "a10m5r10r1r3-submission-admission"' in admission
    setup = (JOBS / "setup_diagnostics.py").read_text(encoding="utf-8")
    predecessor_setup = (
        R1R2 / "artifacts/jobs/setup_diagnostics.py"
    ).read_text(encoding="utf-8")
    expected_setup = predecessor_setup.replace(
        "a10m5r10r1r2-submission-admission",
        "a10m5r10r1r3-submission-admission",
    ).replace(
        "a10m5r10r1r2-portable-bootstrap-control-plane-remedy-r0", RUN_ID
    )
    assert setup == expected_setup
    assert setup.startswith("#!/bin/false\n")
    assert (
        'recorded_python_path == "[JOB_LOCAL]/runtime/cpython/bin/python3"'
        in setup
    )
    assert '"portable_compute_python_authenticated"' in setup


def main() -> None:
    remedy = json.loads(
        (PACKAGE / "artifacts/job-local-capacity-contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert remedy["package_id"] == PACKAGE_ID
    assert remedy["predecessor_package_id"] == (
        "20260719-a10m5r10r1r2-portable-bootstrap-control-plane-remedy"
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

    pin_path = PACKAGE / "artifacts/corpus-layout-pin.json"
    assert pin_path.stat().st_size == 859
    assert digest(pin_path) == (
        "30058e8cbe2b420f899bcc67b5d90042e39c921ba1e75ea107d81c624437b51e"
    )
    pin = json.loads(pin_path.read_text(encoding="utf-8"))
    assert pin["package_id"] == PACKAGE_ID
    assert pin["archive"] == {"bytes": 224040960, "sha256": CORPUS_SHA256}
    assert pin["layout"]["member_count"] == 101
    assert pin["layout"]["accepted_object_count"] == 98
    assert pin["layout"]["sole_top_level_prefix"] == "corpus"
    assert remedy["corpus_layout"]["archive_sha256"] == CORPUS_SHA256
    assert remedy["corpus_layout"]["pin_bytes"] == 859
    assert remedy["corpus_layout"]["pin_sha256"] == digest(pin_path)
    assert remedy["corpus_layout"]["verified_before_authority"] is True

    predecessor_manifest = PACKAGE / "artifacts/predecessor-evidence-identities.json"
    assert predecessor_manifest.stat().st_size == PREDECESSOR_MANIFEST_BYTES
    assert digest(predecessor_manifest) == PREDECESSOR_MANIFEST_SHA256
    assert remedy["predecessor_evidence"]["identity_manifest"] == {
        "bytes": PREDECESSOR_MANIFEST_BYTES,
        "path": "artifacts/predecessor-evidence-identities.json",
        "sha256": PREDECESSOR_MANIFEST_SHA256,
    }
    builder = load_module(JOBS / "build_control_records.py")
    assert builder.PACKAGE_ID == PACKAGE_ID
    assert builder.RUN_ID == RUN_ID
    assert len(
        {
            builder.PACKAGE_ID,
            builder.RUN_ID,
            builder.AUTHORITY_ID,
            builder.BUDGET_ID,
            builder.AUTHORITY_TOKEN,
        }
    ) == 5
    predecessor = builder.predecessor_bundle()
    assert set(predecessor["predecessors"]) == {
        "a10m5r10r1r2_corpus_root_hold",
        "a10m5r10r1r1_compute_python_hold",
        "a10m5r10r1_operational_hold",
        "a10m5o1r2_toolkit_hardening",
    }
    assert predecessor["predecessors"]["a10m5r10r1r2_corpus_root_hold"][
        "terminal"
    ] == "HOLD-A10M5R10R1R2-CORPUS-ROOT-NESTING"
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
    assert failure["failure_class"] == "corpus-root-nesting"
    assert failure["portable_setup_ready"] is True
    assert failure["corpus_archive_opened"] is True
    assert failure["effective_corpus_root"] == "$job_local/corpus/corpus"
    assert failure["control_rows_published"] == 0
    assert failure["scientific_interpretation"] == "none"
    control_plane = remedy["control_plane"]
    assert control_plane["login_admission_python_path"] == "/usr/bin/python3.11"
    assert control_plane["compute_bootstrap_before_python"] is True
    assert control_plane["compute_setup_python_path"] == "$runtime_root/bin/python3"
    assert control_plane["compute_setup_python_version"] == "Python 3.11.15"
    assert control_plane["outer_failure_finalizer_compatibility"] == "python-3.6"

    portfolio = json.loads(sources["portfolio-contract.json"].read_text(encoding="utf-8"))
    portfolio_roles = [item["role_id"] for item in portfolio["roles"]]
    waves = remedy["admission"]["waves"]
    assert len(waves) == 5 and all(len(wave) == 2 for wave in waves)
    flattened = [role for wave in waves for role in wave]
    assert flattened == portfolio_roles and len(set(flattened)) == 10
    assert remedy["admission"]["maximum_live_candidate_jobs"] == 2
    assert remedy["admission"]["maximum_simultaneous_bootstraps"] == 1
    assert remedy["admission"][
        "admission_closes_after_any_observed_candidate_failure"
    ] is True
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

    for path in (*JOBS.glob("*.py"), *PACKAGE.glob("artifacts/*.py")):
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

    verify_two_file_corpus_delta()
    verify_compute_sources()
    prepare = load_module(JOBS / "prepare_assets.py")
    assert tuple(flattened) == prepare.CANDIDATE_ROLES
    print("A10M5R10R1R3-CORPUS-EXTRACTION-ROOT-FREEZE-VERIFIED")


if __name__ == "__main__":
    main()
