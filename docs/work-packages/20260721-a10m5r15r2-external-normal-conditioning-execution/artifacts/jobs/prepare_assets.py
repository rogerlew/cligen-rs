#!/usr/bin/env python3
"""Prepare fresh A10M5R15R2 assets from authenticated R14R2R2 r3."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
R1 = PACKAGE.parent / "20260721-a10m5r15r1-prism-eligible-cohort"
CONTRACT = PACKAGE / "artifacts/execution-contract.json"
CALIBRATION = PACKAGE / "artifacts/attribution-calibration.json"
REPLAY_SOURCE = PACKAGE / "artifacts/run_temporal_replay.py"
PARENT_MANIFEST_SHA256 = "7988efbb342045f0df5ce05ddb810cc36c8be46f145f4c0bc531d02c56291c05"
PARENT_PACKAGE = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
RUN_ID = "a10m5r15r2-external-normal-conditioning-execution-r0"
PORTFOLIO_ROLE = "external-normal-conditioning-portfolio"
RECORD_TYPE = "a10m5r15r2-submission-admission"
CALIBRATION_GATES = {
    "candidate_blind": True,
    "replicate_count": True,
    "sequence_seeds_exact": True,
    "strictly_positive_margin": True,
}
BENCHMARK_TOOLCHAIN = {
    "cargo-vendor.tar.gz": {
        "bytes": 35822885,
        "sha256": "13d7f41f3e0d8b45254a1e6070db5b814d54327e9201ccbe22a57269168f0d3c",
    },
    "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz": {
        "bytes": 192171372,
        "sha256": "d2ccef59dd9f7439f2c694948069f789a044dc1addcc0803613232af8f88ee0c",
    },
}
BENCHMARK_PARAMETERS = {
    "p+4050_-11375": {"bytes": 7022, "sha256": "e6d1a9f1aa93b3c8389b83cc9e09ab02688924ac3ffaf9d5f046fb71a5be7704"},
    "p+4525_-08875": {"bytes": 7022, "sha256": "7586415909ec4eadfadfc9d9378500cec3d47a64dcbe861bb146ef8d9d48fc0f"},
    "p+3250_-10200": {"bytes": 7022, "sha256": "2ef4231cb4fe9843e70b7f7c962fab7df8f6b169e488c270ec77199faf13803f"},
    "p+3275_-08325": {"bytes": 7022, "sha256": "68350d92b5ba93524a4c735e058d6dae5a941f1f87ca1cf8c44d592c45e366a7"},
    "p+3675_-10750": {"bytes": 7022, "sha256": "2a02b7449fe92460dde0b399328b9a2b28aad9134fa416e95e840d057b4083d5"},
    "p+4025_-09900": {"bytes": 7022, "sha256": "600d160ef3b27d30bff5b50de53b28e84ccd72db313bd37c2177f67da0837b78"},
}
CALENDAR_FIELDS = ("prcp", "tmax", "tmin", "srad")
CALENDAR_FIXTURE_DATES = (
    "1984-02-28",
    "1984-02-29",
    "1984-03-01",
    "1984-12-30",
    "1984-12-31",
    "1985-01-01",
    "1987-12-31",
    "1988-01-01",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    encoded = json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return recorded == hashlib.sha256(encoded).hexdigest()


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def published(source_commit: str) -> None:
    head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    if source_commit != head or head != upstream or branch != "main":
        raise RuntimeError("A10M5R15R2 assets require exact published main")
    for path in (
        Path(__file__).resolve(),
        CONTRACT,
        PACKAGE / "artifacts/portfolio-role-map.json",
        PACKAGE / "artifacts/corpus-layout-pin.json",
        PACKAGE / "artifacts/verify_corpus_layout.py",
        PACKAGE / "artifacts/rev2_selector.py",
        PACKAGE / "artifacts/run_runtime_benchmarks.py",
        CALIBRATION,
        REPLAY_SOURCE,
        PACKAGE / "artifacts/jobs/continuous_core.py",
        PACKAGE / "artifacts/jobs/continuous_candidate_experiment.py",
        PACKAGE / "artifacts/jobs/legacy_core.py",
        PACKAGE / "artifacts/jobs/build_control_records.py",
        PACKAGE / "artifacts/jobs/materialize_admission.py",
    ):
        if path.read_bytes() != git_bytes(source_commit, path):
            raise RuntimeError(f"published execution source drift: {path.name}")


def parent_manifest(root: Path) -> dict:
    path = root / "asset-manifest.json"
    if path.is_symlink() or not path.is_file() or digest(path) != PARENT_MANIFEST_SHA256:
        raise RuntimeError("R14R2R2 r3 parent asset identity drift")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("package_id") != PARENT_PACKAGE or manifest.get("protected_roles_opened") != []:
        raise RuntimeError("R14R2R2 r3 parent authority drift")
    for name, expected in manifest["assets"].items():
        member = root / name
        if member.is_symlink() or member.stat().st_nlink != 1 or identity(member) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"R14R2R2 parent member drift: {name}")
    return manifest


def rewrite_json(path: Path, transform) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    transform(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def calendar_fixture(document: dict) -> dict:
    indices = {value: index for index, value in enumerate(document["dates"])}
    rows = []
    for date in CALENDAR_FIXTURE_DATES:
        index = indices[date]
        observed = bool(document["source_observed"][index])
        present = {
            field: document["fields"][field][index] is not None
            for field in CALENDAR_FIELDS
        }
        if any(value != observed for value in present.values()):
            raise RuntimeError("calendar fixture field mask drift")
        rows.append(
            {
                "date": date,
                "required_fields_present": present,
                "source_observed": observed,
            }
        )
    if not (
        rows[1]["source_observed"]
        and not rows[4]["source_observed"]
        and rows[-2]["source_observed"]
        and rows[-1]["source_observed"]
    ):
        raise RuntimeError("calendar fixture boundary semantics failed")
    return {
        "point_id": document["point_id"],
        "rows": rows,
        "spans_absent_leap_december_31": True,
        "spans_observed_february_29": True,
        "spans_window_end_exclusive": ["1987-12-31", "1988-01-01"],
    }


def rebuild_calendar_preflight(corpus_archive: Path, output: Path) -> None:
    profile = json.loads(
        (REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json").read_text(
            encoding="utf-8"
        )
    )
    expected = profile["fit_period_example"]
    window = profile["window_example"]
    roles = {"candidate_fit": 0, "fit_validation": 0}
    minimum_counts = {"core": 10**9, "physics": 10**9}
    fixture = None
    with tarfile.open(corpus_archive, "r:") as outer:
        for member in outer.getmembers():
            if not member.name.endswith(".tar.gz") or "/daymet-v1/" not in member.name:
                continue
            stream = outer.extractfile(member)
            if stream is None:
                raise RuntimeError("Daymet outer corpus member cannot be read")
            with tarfile.open(fileobj=io.BytesIO(stream.read()), mode="r:gz") as inner:
                for item in inner.getmembers():
                    document_stream = inner.extractfile(item)
                    if document_stream is None:
                        continue
                    document = json.load(document_stream)
                    role = document.get("role")
                    if role not in roles:
                        continue
                    dates = document["dates"]
                    observed = [bool(value) for value in document["source_observed"]]
                    if len(dates) != len(observed):
                        raise RuntimeError("Daymet date/mask length drift")
                    missing = [
                        date for date, keep in zip(dates, observed) if not keep
                    ]
                    if not (
                        len(dates) == expected["calendar_axis_rows"]
                        and dates[0] == expected["start_date_inclusive"]
                        and dates[-1] == expected["end_date_inclusive"]
                        and sum(observed) == expected["observed_rows"]
                        and missing == expected["unobserved_dates"]
                    ):
                        raise RuntimeError("Daymet calendar profile drift")
                    for field in CALENDAR_FIELDS:
                        present = [value is not None for value in document["fields"][field]]
                        if present != observed:
                            raise RuntimeError(f"Daymet {field} mask drift")
                    roles[role] += 1
                    parsed_dates = [dt.date.fromisoformat(value) for value in dates]
                    for name, fields in (
                        ("core", CALENDAR_FIELDS[:3]),
                        ("physics", CALENDAR_FIELDS),
                    ):
                        counts = {}
                        for index, date in enumerate(parsed_dates):
                            keep = observed[index] and all(
                                document["fields"][field][index] is not None
                                for field in fields
                            )
                            if keep:
                                key = (date.year, date.month)
                                counts[key] = counts.get(key, 0) + 1
                        if len(counts) != 360:
                            raise RuntimeError("calendar year-month eligibility drift")
                        minimum_counts[name] = min(
                            minimum_counts[name], min(counts.values())
                        )
                    if fixture is None and role == "candidate_fit":
                        fixture = calendar_fixture(document)
    if roles != {"candidate_fit": 1200, "fit_validation": 240}:
        raise RuntimeError(f"Daymet role roster drift: {roles}")
    if fixture is None or min(minimum_counts.values()) < 28:
        raise RuntimeError("calendar consumer preflight incomplete")
    value = {
        "corpus": identity(corpus_archive),
        "counts": {
            "calendar_axis_rows_per_point": expected["calendar_axis_rows"],
            "core_observed_rows_per_point": expected["observed_rows"],
            "physics_observed_rows_per_point": expected["observed_rows"],
            "roles": roles,
        },
        "fixture": fixture,
        "mask_composition": {
            "core": "source_observed and prcp present and tmax present and tmin present",
            "physics": "core and srad present",
        },
        "month_year_eligibility": {
            "core_minimum_observed_rows": minimum_counts["core"],
            "eligible": True,
            "physics_minimum_observed_rows": minimum_counts["physics"],
            "required_minimum_observed_rows": 28,
            "year_month_cells_per_point": 360,
        },
        "normalized_calendar_axis": profile["normalized_axis"],
        "profile_id": profile["profile_id"],
        "schema_version": 2,
        "source_bounds": {
            "end_inclusive": expected["end_date_inclusive"],
            "start_inclusive": expected["start_date_inclusive"],
        },
        "source_transform_id": profile["profile_id"],
        "unobserved_dates": expected["unobserved_dates"],
        "valid": True,
        "window": {
            "calendar_axis_rows": window["calendar_axis_rows"],
            "core_observed_rows": window["observed_rows"],
            "end_exclusive": window["end_exclusive"],
            "end_semantics": "exclusive",
            "physics_observed_rows": window["observed_rows"],
            "start_inclusive": window["start_inclusive"],
        },
    }
    (output / "calendar-preflight.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def transform_contracts(output: Path, contract: dict) -> None:
    arms = contract["arms"]
    candidates = [row["candidate"] for row in arms]
    roles = [row["role"] for row in arms]

    def portfolio(value):
        inherited_definition = value["architectures"]["centered_location_ou_smooth_climatology"]
        common = {
            "backbone_trainable": False,
            "centered_scale_ou": False,
            "decoder_head_indices": [0, 1, 3, 5],
            "decoder_head_semantics": inherited_definition["decoder_head_semantics"],
            "differentiable_selector_metric_count": 188,
            "location_ou_head_indices": [0, 1, 3, 5],
            "medium_time_scale_days": [14.0, 180.0],
            "observed_weather_inputs": [],
            "scale_ou_head_indices": [],
            "selector_aligned_annual_objective": True,
            "slow_state": True,
            "slow_time_scale_days": [180.0, 1460.0],
            "state_clock": "continuous_time_exact_ou_discretized_daily",
            "state_reset_boundaries": [],
        }
        value["architectures"] = {
            arms[0]["candidate"]: {
                **inherited_definition,
                "arm": "E0",
                "candidate_parameter_count": 1820,
                "parameter_ceiling": 340000,
                "parameter_count": 278747,
                "uses_normals": False,
                "uses_p2_backbone": True,
            },
            arms[1]["candidate"]: {
                **inherited_definition,
                "arm": "E1",
                "candidate_parameter_count": 2540,
                "deterministic_climatology_basis": "bias_free_5_by_40_outer_product_200_to_4",
                "deterministic_climatology_context": [
                    "sin_day_of_year", "cos_day_of_year", "latitude", "longitude",
                    "elevation", "36_candidate_fit_normalized_prism_monthly_normals",
                ],
                "deterministic_climatology_parameter_count": 800,
                "parameter_ceiling": 340000,
                "parameter_count": 279467,
                "uses_normals": True,
                "uses_p2_backbone": True,
            },
            arms[2]["candidate"]: {
                **common,
                "arm": "E2C",
                "base": "bias_free_descriptor_baseline_plus_centered_ou_residual",
                "baseline_mapping": "bias_free_20_to_15",
                "baseline_parameter_count": 300,
                "candidate_parameter_count": 2040,
                "context_inputs": ["sin_day_of_year", "cos_day_of_year", "latitude", "longitude", "elevation"],
                "parameter_ceiling": 330000,
                "parameter_count": 2040,
                "uses_normals": False,
                "uses_p2_backbone": False,
            },
            arms[3]["candidate"]: {
                **common,
                "arm": "E2",
                "base": "normal_anchored_mapping_plus_centered_ou_residual",
                "baseline_mapping": "bias_free_20_to_11_plus_bias_free_200_to_4",
                "baseline_parameter_count": 1020,
                "candidate_parameter_count": 2760,
                "context_inputs": [
                    "sin_day_of_year", "cos_day_of_year", "latitude", "longitude",
                    "elevation", "36_candidate_fit_normalized_prism_monthly_normals",
                ],
                "parameter_ceiling": 330000,
                "parameter_count": 2760,
                "uses_normals": True,
                "uses_p2_backbone": False,
            },
        }
        value["package_id"] = PACKAGE_ID
        value["roles"] = roles
        value["specification"] = "SPEC-A10-EXTERNAL-NORMAL-CONDITIONING-rev2"
        value["stochastic"]["evaluation_members"] = 8
        value["controls"]["capacities"]["K2"]["candidate_parameter_ceiling"] = 340000
        value["candidate_parameter_ceilings"] = {
            row["candidate"]: 340000 if row["uses_p2"] else 330000 for row in arms
        }
        value["status"] = "ratified"
        value["terminals"] = {
            "none": "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT",
            "ready": "A10M5R15-TEMPORAL-READY",
            "single": "A10M5R15-TEMPORAL-READY",
        }

    def temporal(value):
        value["contract_id"] = "a10m5r15r2-external-normal-conditioning-v1"
        value["predecessor_terminal"] = contract["corpus"]["terminal"]
        value["roles"] = [
            {
                "architecture": row["candidate"],
                "backbone_capacity": "P2" if row["uses_p2"] else "NONE",
                "capacity": row["capacity"],
                "configuration_id": row["configuration_id"],
                "role_id": row["role"],
                "seeds": [147031, 271828, 314159],
            }
            for row in arms
        ]
        value["resources"] = {
            "control_minutes": 30,
            "gpu_jobs": 2,
            "gpu_minute_ceiling": 515,
            "maximum_concurrent_candidates": 2,
            "portfolio_l40_count": 2,
            "portfolio_minutes": 240,
            "recovery_minutes": 5,
        }

    def capacity(value):
        value["package_id"] = PACKAGE_ID
        value["predecessor_package_id"] = PARENT_PACKAGE
        value["admission"]["waves"] = [[PORTFOLIO_ROLE]]
        value["storage_formula"] = {
            "components": [
                "one expanded portable runtime and environment",
                "one extracted corpus",
                "four isolated transient cache roots",
                "four candidate transient work roots",
                "one exact Rust toolchain and vendored release build root",
                "one six-station runtime-parameter root",
                "one runtime benchmark work root",
                "fixed safety margin",
            ],
            "evidence": {
                "inherited_expanded_asset_bytes": 11811160064,
                "measured_new_prebuild_tree_bytes": 3613761536,
                "measured_new_prebuild_tree_entries": 113595,
                "release_build_and_runtime_byte_allowance": 3902431232,
                "release_build_and_runtime_inode_allowance": 50000,
                "free_byte_margin": 2147483648,
                "free_inode_margin_after_inherited_and_new_allowances": 82549,
            },
            "maximum_expanded_bytes": 19327352832,
            "minimum_free_bytes_before_mutation": 21474836480,
            "minimum_free_inodes_before_mutation": 262144,
            "shared_tree_identity_before_and_after_science": True,
        }
        value["status"] = "EXECUTION-READY"

    rewrite_json(output / "portfolio-contract.json", portfolio)
    rewrite_json(output / "temporal-contract.json", temporal)
    rewrite_json(output / "job-local-capacity-contract.json", capacity)
    (output / "portfolio-role-map.json").write_bytes(
        (PACKAGE / "artifacts/portfolio-role-map.json").read_bytes()
    )
    role_map = json.loads((output / "portfolio-role-map.json").read_text())
    if [row["candidate"] for row in role_map["processes"]] != candidates:
        raise RuntimeError("role map and execution contract differ")


def transform_operational(output: Path, arms: list[dict]) -> None:
    old_roles = (
        "continuous-location-ou-k2",
        "continuous-location-ou-smooth-climatology-k2",
        "continuous-location-scale-ou-k2",
        "continuous-location-scale-ou-smooth-climatology-k2",
    )
    old_candidates = (
        "centered_location_ou",
        "centered_location_ou_smooth_climatology",
        "centered_location_and_scale_ou",
        "centered_location_and_scale_ou_smooth_climatology",
    )
    replacements = {
        PARENT_PACKAGE: PACKAGE_ID,
        "a10m5r14r2r2-two-l40-two-wave-portfolio-r3": RUN_ID,
        "a10m5r14r2r2-submission-admission": RECORD_TYPE,
        "continuous-distribution-head-factorial-portfolio": PORTFOLIO_ROLE,
        **{old: row["role"] for old, row in zip(old_roles, arms)},
        **{old: row["candidate"] for old, row in zip(old_candidates, arms)},
        "HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE": "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT",
        "A10M5R14-TEMPORAL-READY": "A10M5R15-TEMPORAL-READY",
    }
    protected = {
        "build_control_records.py",
        "continuous_candidate_experiment.py",
        "continuous_core.py",
        "inherited_r15_candidate_experiment.py",
        "inherited_r15_distribution_core.py",
        "inherited_r15_legacy_core.py",
        "legacy_core.py",
        "materialize_admission.py",
    }
    for path in output.iterdir():
        if not path.is_file() or path.name in protected or path.suffix not in (".py", ".sh"):
            continue
        text = path.read_text(encoding="utf-8")
        for old in sorted(replacements, key=len, reverse=True):
            text = text.replace(old, replacements[old])
        path.write_text(text, encoding="utf-8")


def install_runtime_execution(output: Path) -> None:
    run_path = output / "run_portfolio.sh"
    run_text = run_path.read_text(encoding="utf-8")
    if (
        run_text.count("16777216") != 1
        or run_text.count("17179869184") != 1
        or run_text.count("16000") != 2
    ):
        raise RuntimeError("parent storage preflight threshold drift")
    run_text = (
        run_text.replace("16777216", "20971520")
        .replace("17179869184", "21474836480")
        .replace("16000", "262144")
    )
    old_tail = """launcher_status=$?
set -e
restore_cleanup_permissions
trap - EXIT
"""
    new_tail = """launcher_status=$?
set -e
if [ "$launcher_status" -eq 0 ]; then
  benchmark_started=$(date +%s)
  benchmark_deadline=${SLURM_JOB_END_TIME:?SLURM end time required for runtime admission}
  benchmark_remaining=$((benchmark_deadline - benchmark_started))
  benchmark_preflight_valid=false
  [ "$benchmark_remaining" -ge 1800 ] && benchmark_preflight_valid=true
  printf '{"minimum_remaining_seconds":1800,"observed_remaining_seconds":%s,"schema_version":1,"valid":%s}\n' \\
    "$benchmark_remaining" "$benchmark_preflight_valid" \\
    >"$output/runtime-walltime-preflight.json"
  test "$benchmark_preflight_valid" = true
  benchmark_root=$job_local/runtime-benchmark
  mkdir -p -- "$benchmark_root/source" "$benchmark_root/parameters"
  tar -xzf "$run_root/source.tar.gz" -C "$benchmark_root/source"
  tar -xzf "$run_root/cargo-vendor.tar.gz" -C "$benchmark_root"
  tar -xf "$run_root/runtime-parameters.tar" -C "$benchmark_root/parameters"
  tar -xJf "$run_root/rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz" -C "$benchmark_root"
  "$benchmark_root/rust-1.92.0-x86_64-unknown-linux-gnu/install.sh" \\
    --prefix="$benchmark_root/rust-toolchain" --disable-ldconfig >/dev/null
  rm -rf -- "$benchmark_root/rust-1.92.0-x86_64-unknown-linux-gnu"
  mkdir -p -- "$benchmark_root/source/.cargo"
  printf '%s\n' '[source.crates-io]' 'replace-with = "vendored-sources"' '' \\
    '[source.vendored-sources]' 'directory = "../vendor"' \\
    >"$benchmark_root/source/.cargo/config.toml"
  PATH="$benchmark_root/rust-toolchain/bin:/usr/bin:/bin" \\
    CARGO_NET_OFFLINE=true CC=/usr/bin/gcc CXX=/usr/bin/g++ \\
    "$benchmark_root/rust-toolchain/bin/cargo" build \\
      --manifest-path "$benchmark_root/source/Cargo.toml" \\
      --release --locked --offline -p cligen --bin cligen
  cp "$benchmark_root/source/target/release/cligen" \\
    "$output/faithful-cligen-linux-x86_64"
  chmod 500 "$output/faithful-cligen-linux-x86_64"
  rm -rf -- "$benchmark_root/source/target"
  set +e
  env CUDA_VISIBLE_DEVICES= NVIDIA_VISIBLE_DEVICES=void \\
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \\
    NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \\
    PATH="$environment/bin:$benchmark_root/rust-toolchain/bin:/usr/bin:/bin" \\
    "$environment/bin/python" "$run_root/run_runtime_benchmarks.py" \\
      --asset-root "$run_root" --evidence-root "$run_root" \\
      --binary "$output/faithful-cligen-linux-x86_64" \\
      --parameter-root "$benchmark_root/parameters" \\
      --rustc "$benchmark_root/rust-toolchain/bin/rustc" \\
      --cargo "$benchmark_root/rust-toolchain/bin/cargo" \\
      --work-root "$benchmark_root/work" \\
      --output "$output/runtime-benchmark.json"
  benchmark_status=$?
  set -e
  if [ "$benchmark_status" -ne 0 ]; then launcher_status=$benchmark_status; fi
fi
restore_cleanup_permissions
trap - EXIT
"""
    if old_tail not in run_text:
        raise RuntimeError("parent portfolio runner tail drift")
    run_path.write_text(run_text.replace(old_tail, new_tail), encoding="utf-8")

    job_path = output / f"job-{PORTFOLIO_ROLE}.sh"
    job_text = job_path.read_text(encoding="utf-8")
    replacements = {
        "cleanup_permissions = load('cleanup-permissions.json')": (
            "cleanup_permissions = load('cleanup-permissions.json')\n"
            "runtime = load('runtime-benchmark.json')\n"
            "runtime_preflight = load('runtime-walltime-preflight.json')"
        ),
        "child_records_ok = True": (
            "runtime_ok = (\n"
            "    authenticated(runtime) and runtime.get('valid') is True\n"
            "    and runtime.get('package_id') == '20260721-a10m5r15r2-external-normal-conditioning-execution'\n"
            "    and runtime.get('source_commit') == manifest.get('source_commit')\n"
            "    and runtime.get('asset_manifest_sha256') == manifest_sha\n"
            "    and bool(runtime.get('gates')) and all(runtime['gates'].values())\n"
            "    and len(runtime.get('rows', [])) == 48\n"
            "    and runtime_preflight.get('valid') is True\n"
            "    and runtime_preflight.get('minimum_remaining_seconds') == 1800\n"
            "    and runtime_preflight.get('observed_remaining_seconds', 0) >= 1800\n"
            ")\n"
            "child_records_ok = True"
        ),
        "'portfolio_admission_authenticated': admission_ok,": (
            "'portfolio_admission_authenticated': admission_ok,\n"
            "    'runtime_benchmark_authenticated': runtime_ok,"
        ),
        "'submission_admission_record_sha256': admission.get('record_sha256'),": (
            "'submission_admission_record_sha256': admission.get('record_sha256'),\n"
            "    'runtime_benchmark_record_sha256': runtime.get('record_sha256'),"
        ),
    }
    for old, new in replacements.items():
        if old not in job_text:
            raise RuntimeError(f"parent portfolio finalizer drift: {old}")
        job_text = job_text.replace(old, new)
    job_path.write_text(job_text, encoding="utf-8")


def add_runtime_build_assets(
    output: Path, benchmark_assets: Path, benchmark_parameters: Path, source_commit: str
) -> None:
    for name, expected in BENCHMARK_TOOLCHAIN.items():
        source = benchmark_assets / name
        if not source.is_file() or identity(source) != expected:
            raise RuntimeError(f"benchmark toolchain asset identity drift: {name}")
        shutil.copy2(source, output / name)
    subprocess.run(
        (
            "git",
            "archive",
            "--format=tar.gz",
            f"--output={output / 'source.tar.gz'}",
            source_commit,
            "Cargo.toml",
            "Cargo.lock",
            "crates",
        ),
        cwd=REPO,
        check=True,
    )
    parameter_archive = output / "runtime-parameters.tar"
    with tarfile.open(parameter_archive, "w") as archive:
        for point_id, expected in sorted(BENCHMARK_PARAMETERS.items()):
            source = benchmark_parameters / point_id / "source-station.par"
            if not source.is_file() or identity(source) != expected:
                raise RuntimeError(f"benchmark parameter identity drift: {point_id}")
            information = tarfile.TarInfo(f"{point_id}.par")
            information.size = source.stat().st_size
            information.mode = 0o400
            information.mtime = 0
            with source.open("rb") as stream:
                archive.addfile(information, stream)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-assets", type=Path, required=True)
    parser.add_argument("--corpus-archive", type=Path, required=True)
    parser.add_argument("--benchmark-assets", type=Path, required=True)
    parser.add_argument("--benchmark-parameters", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", options.source_commit) is None:
        raise RuntimeError("full source commit required")
    published(options.source_commit)
    parent = parent_manifest(options.parent_assets)
    if options.output.exists():
        raise RuntimeError("fresh execution asset output required")
    receipt_path = PACKAGE / "artifacts/corpus-archive-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("valid") or identity(options.corpus_archive) != {key: receipt[key] for key in ("bytes", "sha256")}:
        raise RuntimeError("successor corpus archive identity drift")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    calibration_ancestor = subprocess.run(
        (
            "git",
            "merge-base",
            "--is-ancestor",
            calibration.get("source_commit", ""),
            options.source_commit,
        ),
        cwd=REPO,
        check=False,
    ).returncode == 0
    if not (
        authenticated(calibration)
        and calibration_ancestor
        and calibration.get("valid") is True
        and calibration.get("candidate_output_accessed") is False
        and calibration.get("protected_roles_opened") == []
        and calibration.get("package_id") == PACKAGE_ID
        and calibration.get("calibration_configuration")
        == "centered_location_ou_smooth_climatology-k2"
        and calibration.get("asset_manifest_sha256") == PARENT_MANIFEST_SHA256
        and calibration.get("calibration_source_commit") == contract["parent_asset_source_commit"]
        and calibration.get("calibration_stream_sha256")
        == "2bb8379f639712dc864308510bd2a8c10ac9c39ea3cae609abdc2a2bf51384ff"
        and calibration.get("sequence_seeds") == [410542, 410543]
        and calibration.get("replicates") == 1000
        and calibration.get("nearest_rank_zero_based_index") == 899
        and calibration.get("margin", 0) > 0
        and calibration.get("gates") == CALIBRATION_GATES
        and digest(CALIBRATION) == contract["replay"].get("calibration_receipt_sha256")
    ):
        raise RuntimeError("candidate-blind attribution calibration is not frozen")
    shutil.copytree(options.parent_assets, options.output, symlinks=False)
    for name in ("controller-admissions", "__pycache__"):
        path = options.output / name
        if path.exists():
            shutil.rmtree(path)
    (options.output / "controller-admissions").mkdir(mode=0o700)
    renames = {
        "continuous_candidate_experiment.py": "inherited_r15_candidate_experiment.py",
        "continuous_core.py": "inherited_r15_distribution_core.py",
        "legacy_core.py": "inherited_r15_legacy_core.py",
    }
    for old, new in renames.items():
        os.replace(options.output / old, options.output / new)
    (options.output / "run_temporal_replay.py").unlink()
    os.replace(
        options.output / "job-continuous-distribution-head-factorial-portfolio.sh",
        options.output / f"job-{PORTFOLIO_ROLE}.sh",
    )
    overlays = {
        "build_control_records.py": PACKAGE / "artifacts/jobs/build_control_records.py",
        "continuous_candidate_experiment.py": PACKAGE / "artifacts/jobs/continuous_candidate_experiment.py",
        "continuous_core.py": PACKAGE / "artifacts/jobs/continuous_core.py",
        "legacy_core.py": PACKAGE / "artifacts/jobs/legacy_core.py",
        "materialize_admission.py": PACKAGE / "artifacts/jobs/materialize_admission.py",
        "execution-contract.json": PACKAGE / "artifacts/execution-contract.json",
        "corpus-layout-pin.json": PACKAGE / "artifacts/corpus-layout-pin.json",
        "verify_corpus_layout.py": PACKAGE / "artifacts/verify_corpus_layout.py",
        "rev2_selector.py": PACKAGE / "artifacts/rev2_selector.py",
        "run_runtime_benchmarks.py": PACKAGE / "artifacts/run_runtime_benchmarks.py",
    }
    for name, source in overlays.items():
        (options.output / name).write_bytes(git_bytes(options.source_commit, source))
    replay_payload = git_bytes(options.source_commit, REPLAY_SOURCE)
    (options.output / "post-collection-replay-entry.json").write_text(
        json.dumps(
            {
                "bytes": len(replay_payload),
                "execution_location": "published repository after authenticated collection",
                "path": REPLAY_SOURCE.relative_to(REPO).as_posix(),
                "sha256": hashlib.sha256(replay_payload).hexdigest(),
                "source_commit": options.source_commit,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (options.output / "attribution-calibration.json").write_bytes(
        git_bytes(options.source_commit, CALIBRATION)
    )
    shutil.copy2(options.corpus_archive, options.output / "corpus.tar")
    rebuild_calendar_preflight(options.corpus_archive, options.output)
    for name in (
        "normal-conditioning-index.json",
        "normal-conditioning-receipt.json",
        "normal-conditioning.f32le",
        "normalizer.f64le",
    ):
        source = R1 / "artifacts/normal-conditioning" / name
        (options.output / name).write_bytes(source.read_bytes())
    transform_contracts(options.output, contract)
    transform_operational(options.output, contract["arms"])
    install_runtime_execution(options.output)
    add_runtime_build_assets(
        options.output,
        options.benchmark_assets,
        options.benchmark_parameters,
        options.source_commit,
    )
    for path in options.output.iterdir():
        if path.is_file() and path.suffix in (".py", ".sh"):
            path.chmod(0o700)
    source_paths = {
        name: path.relative_to(REPO).as_posix() for name, path in overlays.items()
    }
    assets = {}
    for path in sorted(options.output.iterdir()):
        if path.is_file() and path.name != "asset-manifest.json":
            assets[path.name] = {
                **identity(path),
                **({"source_path": source_paths[path.name]} if path.name in source_paths else {}),
            }
    manifest = {
        "assets": assets,
        "canonical_configuration_id": parent["canonical_configuration_id"],
        "canonical_configuration_semantic_sha256": parent["canonical_configuration_semantic_sha256"],
        "package_id": PACKAGE_ID,
        "parent_asset_manifest_sha256": PARENT_MANIFEST_SHA256,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": options.source_commit,
    }
    (options.output / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"A10M5R15R2-ASSETS-PREPARED {digest(options.output / 'asset-manifest.json')}")


if __name__ == "__main__":
    main()
