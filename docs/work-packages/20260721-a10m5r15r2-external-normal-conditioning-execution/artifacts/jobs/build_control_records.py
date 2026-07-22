#!/usr/bin/env python3
"""Build fresh A10M5R15R2 toolkit authority and two-wave plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "719d83451ddff698b280219708f7648ff73c8f9d"
PARENT_PACKAGE = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
SOURCE = PACKAGE.parent / PARENT_PACKAGE / "artifacts/jobs/build_control_records.py"
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
RUN_ID = "a10m5r15r2-external-normal-conditioning-execution-r0"
RECORD_TYPE = "a10m5r15r2-submission-admission"
PORTFOLIO_ROLE = "external-normal-conditioning-portfolio"
R1 = PACKAGE.parent / "20260721-a10m5r15r1-prism-eligible-cohort"
CALIBRATION = PACKAGE / "artifacts/attribution-calibration.json"
CONTRACT = PACKAGE / "artifacts/execution-contract.json"
ROLES = (
    ("e0-centered-location-ou-smooth-climatology-k2", "centered_location_ou_smooth_climatology", "K2"),
    ("e1-normal-conditioned-smooth-climatology-k2", "normal_conditioned_smooth_climatology", "K2"),
    ("e2c-descriptor-anchored-residual-v1", "descriptor_anchored_residual", "K2"),
    ("e2-normal-anchored-residual-v1", "normal_anchored_residual", "K2"),
)
P2_ROLES = {ROLES[0][0], ROLES[1][0]}
CALIBRATION_GATES = {
    "candidate_blind": True,
    "replicate_count": True,
    "sequence_seeds_exact": True,
    "strictly_positive_margin": True,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    encoded = json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return recorded == hashlib.sha256(encoded).hexdigest()


if SOURCE.read_bytes() != git_bytes(PARENT_COMMIT, SOURCE):
    raise RuntimeError("R14R2R2 builder differs from published parent bytes")
spec = importlib.util.spec_from_file_location("inherited_r15r2_builder", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited authority builder")
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
inherited = parent.inherited
base_authority = parent.authority
base_plan = parent.plan
base_evidence = inherited.evidence


def predecessor_bundle(record_commit: str | None = None) -> dict:
    package_path = R1 / "package.md"
    disposition_path = R1 / "disposition.md"
    receipt_path = R1 / "artifacts/cohort-build-receipt.json"
    conditioning_path = R1 / "artifacts/normal-conditioning/normal-conditioning-receipt.json"
    if "Status: `A10M5R15R1-COHORT-READY`" not in package_path.read_text(encoding="utf-8"):
        raise RuntimeError("A10M5R15R1 terminal drift")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    conditioning = json.loads(conditioning_path.read_text(encoding="utf-8"))
    if receipt.get("valid") is not True or conditioning.get("valid") is not True or not all(conditioning["gates"].values()):
        raise RuntimeError("A10M5R15R1 evidence invalid")
    files = {
        path.relative_to(REPO).as_posix(): {"bytes": path.stat().st_size, "sha256": digest(path)}
        for path in (package_path, disposition_path, receipt_path, conditioning_path)
    }
    if record_commit is not None:
        for relative in files:
            if git_bytes(record_commit, REPO / relative) != (REPO / relative).read_bytes():
                raise RuntimeError("A10M5R15R1 evidence differs from published source")
    return {
        "files": files,
        "package_id": R1.name,
        "record_commit": record_commit,
        "terminal": "A10M5R15R1-COHORT-READY",
    }


def calibration_bundle(record_commit: str | None = None) -> dict:
    value = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if not (
        authenticated(value)
        and digest(CALIBRATION) == contract["replay"].get("calibration_receipt_sha256")
        and value.get("package_id") == PACKAGE_ID
        and value.get("valid") is True
        and value.get("candidate_output_accessed") is False
        and value.get("protected_roles_opened") == []
        and value.get("calibration_configuration")
        == "centered_location_ou_smooth_climatology-k2"
        and value.get("asset_manifest_sha256") == contract["parent_asset_manifest_sha256"]
        and value.get("calibration_source_commit") == contract["parent_asset_source_commit"]
        and value.get("calibration_stream_sha256") == "2bb8379f639712dc864308510bd2a8c10ac9c39ea3cae609abdc2a2bf51384ff"
        and value.get("sequence_seeds") == [410542, 410543]
        and value.get("replicates") == 1000
        and value.get("nearest_rank_zero_based_index") == 899
        and math.isfinite(value.get("margin", math.nan))
        and value["margin"] > 0
        and value.get("gates") == CALIBRATION_GATES
    ):
        raise RuntimeError("attribution calibration receipt invalid")
    if record_commit is not None:
        ancestor = subprocess.run(
            ("git", "merge-base", "--is-ancestor", value["source_commit"], record_commit),
            cwd=REPO,
            check=False,
        ).returncode == 0
        if not ancestor or git_bytes(record_commit, CALIBRATION) != CALIBRATION.read_bytes():
            raise RuntimeError("attribution calibration differs from published source")
    return {
        "artifact": {"bytes": CALIBRATION.stat().st_size, "sha256": digest(CALIBRATION)},
        "candidate_output_accessed": False,
        "record_sha256": value["record_sha256"],
        "source_commit": value["source_commit"],
        "valid": True,
    }
def authority(options) -> None:
    predecessor_bundle(options.source_commit)
    calibration_bundle(options.source_commit)
    base_authority(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    value.update(
        {
            "package_id": PACKAGE_ID,
            "attribution_calibration": calibration_bundle(options.source_commit),
            "predecessor_package_evidence": predecessor_bundle(),
            "resource_ceiling_gpu_minutes": 515,
            "resource_class": "one-control-plus-one-two-l40-two-wave-external-normal-conditioning",
        }
    )
    inherited.write(options.output, value)


def plan(options) -> None:
    predecessor_bundle(options.source_commit)
    calibration_bundle(options.source_commit)
    base_plan(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    value = json.loads(
        json.dumps(value).replace(
            "continuous-distribution-head-factorial-portfolio", PORTFOLIO_ROLE
        )
    )
    value["package_id"] = PACKAGE_ID
    value["run_id"] = RUN_ID
    value["predecessor_package_evidence"] = predecessor_bundle()
    value["attribution_calibration"] = calibration_bundle(options.source_commit)
    value["admission_materialization"]["record_type"] = RECORD_TYPE
    portfolio = next(job for job in value["jobs"] if job["role"] == PORTFOLIO_ROLE)
    portfolio.update({"gpus": 2, "gres": "gpu:l40:2", "time_limit_minutes": 240})
    extra_evidence = [
        f"results/{PORTFOLIO_ROLE}/runtime-benchmark.json",
        f"results/{PORTFOLIO_ROLE}/runtime-walltime-preflight.json",
        f"results/{PORTFOLIO_ROLE}/faithful-cligen-linux-x86_64",
        *(
            f"results/{role}/seed-work/{seed}/candidate-export-{years}.pt"
            for role, _, _ in ROLES
            for seed in (147031, 271828, 314159)
            for years in (30, 100)
        ),
        *(
            f"results/{role}/seed-work/{seed}/control-export.pt"
            for role in sorted(P2_ROLES)
            for seed in (147031, 271828, 314159)
        ),
    ]
    value["evidence_allowlist"] = list(
        dict.fromkeys([*value["evidence_allowlist"], *extra_evidence])
    )
    value["evidence_volume"]["maximum_files"] = len(value["evidence_allowlist"])
    value["job_local_capacity"].update(
        {
            "expanded_asset_bytes": 19327352832,
            "minimum_free_bytes": 21474836480,
            "required_inodes": 262144,
        }
    )
    capacity = json.loads(
        (options.asset_root / "job-local-capacity-contract.json").read_text(
            encoding="utf-8"
        )
    )
    if (
        capacity.get("package_id") != PACKAGE_ID
        or capacity.get("status") != "EXECUTION-READY"
        or capacity.get("storage_formula", {}).get(
            "minimum_free_bytes_before_mutation"
        )
        != value["job_local_capacity"]["minimum_free_bytes"]
        or capacity.get("storage_formula", {}).get(
            "minimum_free_inodes_before_mutation"
        )
        != value["job_local_capacity"]["required_inodes"]
    ):
        raise RuntimeError("runtime storage contract/semantic plan drift")
    external_assets = {
        "cargo-vendor.tar.gz",
        "corpus.tar",
        "requirements.lock",
        "runtime-parameters.tar",
        "runtime.tar.gz",
        "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz",
        "wheelhouse.tar",
    }
    for row in value["assets"]:
        if row["logical_name"] in external_assets:
            row["source_class"] = "external-redistributable"
        elif row["logical_name"] == "source.tar.gz":
            row["source_class"] = "repository-owned"
    if [(job["role"], job["gpus"], job["time_limit_minutes"]) for job in value["jobs"]] != [
        ("control-materialization", 1, 30),
        (PORTFOLIO_ROLE, 2, 240),
    ]:
        raise RuntimeError("A10M5R15R2 resource plan drift")
    inherited.write(options.output, value)


def evidence(role: str) -> list[str]:
    values = base_evidence(role)
    if role != "control-materialization":
        values.extend(
            f"results/{role}/seed-work/{seed}/candidate-export-{years}.pt"
            for seed in (147031, 271828, 314159)
            for years in (30, 100)
        )
    if role in P2_ROLES:
        values.extend(
            f"results/{role}/seed-work/{seed}/control-export.pt"
            for seed in (147031, 271828, 314159)
        )
    return values


def prospective_calendar_preflight(root: Path) -> dict:
    manifest = json.loads((root / "asset-manifest.json").read_text(encoding="utf-8"))
    path = root / "calendar-preflight.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    calendar_identity = {"bytes": path.stat().st_size, "sha256": digest(path)}
    corpus_identity = {
        key: manifest["assets"]["corpus.tar"][key] for key in ("bytes", "sha256")
    }
    if not (
        calendar_identity
        == {
            key: manifest["assets"]["calendar-preflight.json"][key]
            for key in ("bytes", "sha256")
        }
        and value.get("corpus") == corpus_identity
        and value.get("valid") is True
        and value.get("profile_id") == "daymet_official_365_v1"
        and value.get("source_transform_id") == "daymet_official_365_v1"
        and value.get("counts")
        == {
            "calendar_axis_rows_per_point": 10958,
            "core_observed_rows_per_point": 10950,
            "physics_observed_rows_per_point": 10950,
            "roles": {"candidate_fit": 1200, "fit_validation": 240},
        }
        and value.get("month_year_eligibility")
        == {
            "core_minimum_observed_rows": 28,
            "eligible": True,
            "physics_minimum_observed_rows": 28,
            "required_minimum_observed_rows": 28,
            "year_month_cells_per_point": 360,
        }
        and value.get("fixture", {}).get("spans_observed_february_29") is True
        and value.get("fixture", {}).get("spans_absent_leap_december_31") is True
        and value.get("fixture", {}).get("spans_window_end_exclusive")
        == ["1987-12-31", "1988-01-01"]
        and value.get("window")
        == {
            "calendar_axis_rows": 2922,
            "core_observed_rows": 2920,
            "end_exclusive": "1988-01-01",
            "end_semantics": "exclusive",
            "physics_observed_rows": 2920,
            "start_inclusive": "1980-01-01",
        }
    ):
        raise RuntimeError("successor calendar preflight identity or semantics drift")
    return value


parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
parent.predecessor_bundle = predecessor_bundle
inherited.PACKAGE_ID = PACKAGE_ID
inherited.PACKAGE = PACKAGE
inherited.ROLES = ROLES
inherited.RUN_ID = RUN_ID
inherited.AUTHORITY_ID = f"{RUN_ID}-authority"
inherited.BUDGET_ID = f"{RUN_ID}-budget"
inherited.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
inherited.PREDECESSOR_COMMIT = PARENT_COMMIT
inherited.predecessor_bundle = predecessor_bundle
inherited.operational_predecessor_bundle = predecessor_bundle
inherited.evidence = evidence
inherited.prospective_calendar_preflight = prospective_calendar_preflight
inherited.authority = authority
inherited.plan = plan
parent.authority = authority
parent.plan = plan


if __name__ == "__main__":
    inherited.main()
