#!/usr/bin/env python3
"""Authenticate R2 evidence, replay twice, and apply rev-2 selection."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np

from rev2_selector import (
    EngineeringIncompleteError,
    InvalidEvidenceError,
    digest,
    dispersion_metric_keys,
    extract_observations,
    failure_terminal,
    run_selector,
)


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
RUN_ID = "a10m5r15r2-external-normal-conditioning-execution-r0"
PORTFOLIO_ROLE = "external-normal-conditioning-portfolio"
BASE_SOURCE = (
    PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial"
    / "artifacts/run_temporal_replay.py"
)
PARAMETER_COUNTS = {
    "centered_location_ou_smooth_climatology": (1820, 278747),
    "normal_conditioned_smooth_climatology": (2540, 279467),
    "descriptor_anchored_residual": (2040, 2040),
    "normal_anchored_residual": (2760, 2760),
}
PAIRINGS = {
    "normal_conditioned_smooth_climatology-k2": "centered_location_ou_smooth_climatology-k2",
    "normal_anchored_residual-v1": "descriptor_anchored_residual-v1",
}
CONFIGURATION_CANDIDATES = {
    "centered_location_ou_smooth_climatology-k2": "centered_location_ou_smooth_climatology",
    "normal_conditioned_smooth_climatology-k2": "normal_conditioned_smooth_climatology",
    "descriptor_anchored_residual-v1": "descriptor_anchored_residual",
    "normal_anchored_residual-v1": "normal_anchored_residual",
}
TERMINALS = {
    "FAIL-A10M5R15-INVALID-EVIDENCE",
    "HOLD-A10M5R15-ENGINEERING-INCOMPLETE",
    "HOLD-A10M5R15-RUNTIME-INELIGIBLE",
    "HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED",
    "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT",
    "A10M5R15-TEMPORAL-READY",
}
PARAMETER_IDENTITIES = {
    "p+4050_-11375": {"bytes": 7022, "sha256": "e6d1a9f1aa93b3c8389b83cc9e09ab02688924ac3ffaf9d5f046fb71a5be7704"},
    "p+4525_-08875": {"bytes": 7022, "sha256": "7586415909ec4eadfadfc9d9378500cec3d47a64dcbe861bb146ef8d9d48fc0f"},
    "p+3250_-10200": {"bytes": 7022, "sha256": "2ef4231cb4fe9843e70b7f7c962fab7df8f6b169e488c270ec77199faf13803f"},
    "p+3275_-08325": {"bytes": 7022, "sha256": "68350d92b5ba93524a4c735e058d6dae5a941f1f87ca1cf8c44d592c45e366a7"},
    "p+3675_-10750": {"bytes": 7022, "sha256": "2a02b7449fe92460dde0b399328b9a2b28aad9134fa416e95e840d057b4083d5"},
    "p+4025_-09900": {"bytes": 7022, "sha256": "600d160ef3b27d30bff5b50de53b28e84ccd72db313bd37c2177f67da0837b78"},
}


spec = importlib.util.spec_from_file_location("r15r2_replay_base", BASE_SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated replay base")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.PACKAGE_ID = PACKAGE_ID
base.RUN_ID = RUN_ID


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    payload = json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return isinstance(recorded, str) and recorded == hashlib.sha256(payload).hexdigest()


def require_published(path: Path, head: str) -> None:
    relative = path.relative_to(REPO).as_posix()
    payload = subprocess.run(
        ("git", "show", f"{head}:{relative}"), cwd=REPO, check=True, capture_output=True
    ).stdout
    if payload != path.read_bytes():
        raise InvalidEvidenceError(f"replay source differs from published main: {path.name}")


def verify_collection(options, head: str) -> tuple[dict, dict, dict]:
    try:
        raw = base.read_toolkit_object(options.semantic_plan)
        receipt = base.read_toolkit_object(options.plan_receipt)
        collection = base.read_toolkit_object(options.collection)
        plan = base.authenticate_plan(raw, receipt, head)
    except FileNotFoundError:
        raise
    except BaseException as error:
        raise InvalidEvidenceError("toolkit plan/collection record malformed") from error
    if not (
        base.authenticated(collection)
        and collection.get("package_id") == PACKAGE_ID
        and collection.get("run_id") == RUN_ID
        and collection.get("source_commit") == head
        and collection.get("plan_id") == receipt.get("plan_id")
        and collection.get("download_promoted") is True
        and collection.get("remote_cleanup_performed") is not True
    ):
        raise InvalidEvidenceError("collection/plan authentication failed")
    allowlist = set(plan["evidence_allowlist"])
    present = set(collection.get("present", []))
    rows = collection.get("sanitized_files", [])
    if {row["logical_name"] for row in rows} != present:
        raise InvalidEvidenceError("collection identity roster drift")
    for row in rows:
        logical = row["logical_name"]
        path = options.evidence_root / logical
        if logical not in allowlist or path.is_symlink() or not path.is_file():
            raise InvalidEvidenceError(f"collected evidence outside allowlist: {logical}")
        if {"bytes": path.stat().st_size, "sha256": digest(path)} != {
            "bytes": row["bytes"], "sha256": row["sha256"]
        }:
            raise InvalidEvidenceError(f"collected evidence identity drift: {logical}")
    return plan, receipt, collection


def verify_replay_asset_bundle(options, plan: dict, manifest: dict, head: str) -> None:
    manifest_path = options.asset_root / "asset-manifest.json"
    manifest_rows = [
        row for row in plan.get("assets", []) if row.get("logical_name") == "asset-manifest.json"
    ]
    manifest_identity = {"bytes": manifest_path.stat().st_size, "sha256": digest(manifest_path)}
    if (
        manifest_path.is_symlink()
        or not manifest_path.is_file()
        or manifest_path.stat().st_nlink != 1
        or len(manifest_rows) != 1
        or {key: manifest_rows[0].get(key) for key in ("bytes", "sha256")}
        != manifest_identity
    ):
        raise InvalidEvidenceError("staged asset manifest differs from authenticated plan")
    required = {
        "aligned_objective.py",
        "attribution-calibration.json",
        "calendar-control-expectation.json",
        "calendar-preflight.json",
        "corpus.tar",
        "execution-contract.json",
        "portfolio-contract.json",
        "portfolio-role-map.json",
        "post-collection-replay-entry.json",
        "sites.json",
        "temporal-contract.json",
        "temporal_metrics.py",
        "temporal_select.py",
    }
    if not required.issubset(manifest.get("assets", {})):
        raise InvalidEvidenceError("replay-consumed asset missing from manifest")
    for name in sorted(required):
        path = options.asset_root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            raise InvalidEvidenceError(f"unsafe replay-consumed asset: {name}")
        expected = manifest["assets"][name]
        if {"bytes": path.stat().st_size, "sha256": digest(path)} != {
            key: expected.get(key) for key in ("bytes", "sha256")
        }:
            raise InvalidEvidenceError(f"replay-consumed asset identity drift: {name}")
    entry = json.loads(
        (options.asset_root / "post-collection-replay-entry.json").read_text(encoding="utf-8")
    )
    replay_path = Path(__file__).resolve()
    if entry != {
        "bytes": replay_path.stat().st_size,
        "execution_location": "published repository after authenticated collection",
        "path": replay_path.relative_to(REPO).as_posix(),
        "sha256": digest(replay_path),
        "source_commit": head,
    }:
        raise InvalidEvidenceError("post-collection replay entry identity drift")


def verify_provenance(
    options, manifest: dict, plan: dict, runtime: dict, execution: dict
) -> tuple[dict, list[dict]]:
    role_map_path = options.asset_root / "portfolio-role-map.json"
    role_map = json.loads(role_map_path.read_text(encoding="utf-8"))
    if {"bytes": role_map_path.stat().st_size, "sha256": digest(role_map_path)} != {
        key: manifest["assets"]["portfolio-role-map.json"][key] for key in ("bytes", "sha256")
    }:
        raise InvalidEvidenceError("role-map identity drift")
    closures = []
    arm_by_candidate = {row["candidate"]: row for row in execution["arms"]}
    for process in role_map["processes"]:
        root = options.evidence_root / "results" / process["role"]
        training = json.loads((root / "training.json").read_text(encoding="utf-8"))
        streams = json.loads((root / "streams.json").read_text(encoding="utf-8"))
        expected_adapter, expected_total = PARAMETER_COUNTS[process["candidate"]]
        arm = arm_by_candidate[process["candidate"]]
        if not (
            training.get("architecture") == process["candidate"]
            and len(training.get("seeds", [])) == 3
            and streams.get("architecture") == process["candidate"]
            and streams.get("configuration_id") == arm["configuration_id"]
            and streams.get("stream_count") == 144
            and len(streams.get("streams", [])) == 144
        ):
            raise EngineeringIncompleteError(f"candidate evidence roster drift: {process['role']}")
        conditioned = process["candidate"] in {
            "normal_conditioned_smooth_climatology", "normal_anchored_residual"
        }
        final_runtime = runtime["arms"][process["candidate"]]["classification"]
        final_engineering_eligible = runtime["arms"][process["candidate"]][
            "engineering_eligible"
        ]

        def verified_provenance(provenance: dict, seed: int) -> dict:
            expected_normals = execution["conditioning"] if conditioned else None
            mapping = provenance.get("mapping_sha256")
            if not (
                provenance.get("model")
                == {"arm": arm["arm"], "candidate": arm["candidate"], "role": arm["role"]}
                and provenance.get("seed") == seed
                and provenance.get("normals_bundle") == expected_normals
                and provenance.get("normals_excluded") is (not conditioned)
                and isinstance(provenance.get("normals_window_limitation"), str)
                and bool(provenance["normals_window_limitation"])
                and provenance.get("calendar", {}).get("profile_id") == "daymet_official_365_v1"
                and isinstance(provenance.get("calendar", {}).get("preflight_sha256"), str)
                and len(provenance["calendar"]["preflight_sha256"]) == 64
                and provenance.get("corpus") == execution["corpus"]
                and provenance.get("runtime_classification")
                == "PENDING-NORMATIVE-ADR-0006-BENCHMARK"
                and ((isinstance(mapping, str) and len(mapping) == 64) if conditioned else mapping is None)
            ):
                raise InvalidEvidenceError(f"rev2 provenance drift: {process['role']}/{seed}")
            closed = dict(provenance)
            closed["provisional_runtime_classification"] = closed.pop(
                "runtime_classification"
            )
            closed["runtime_classification"] = final_runtime
            closed["runtime_engineering_eligible"] = final_engineering_eligible
            return closed

        mapping_hashes = set()
        checkpoint_rows = []
        evaluation_rows = []
        for row in training["seeds"]:
            provenance = row.get("provenance", {})
            closed = verified_provenance(provenance, row["seed"])
            mapping_hashes.add(provenance.get("mapping_sha256"))
            checkpoint_path = root / "seed-work" / str(row["seed"]) / "checkpoint.pt"
            seed_path = root / "seeds" / f"{row['seed']}.json"
            seed_record = json.loads(seed_path.read_text(encoding="utf-8"))
            candidate_exports = {
                str(years): root / "seed-work" / str(row["seed"])
                / f"candidate-export-{years}.pt"
                for years in (30, 100)
            }
            if not (
                row.get("parameter_count") == expected_adapter
                and row.get("candidate_adapter_parameter_count") == expected_adapter
                and row.get("total_parameter_count") == expected_total
                and row.get("parameter_accounting_interface")
                == "adapter-only-parameter_count-plus-explicit-total"
                and digest(checkpoint_path) == row.get("checkpoint_sha256")
                and {
                    years: digest(path) for years, path in candidate_exports.items()
                }
                == row.get("portable_candidate_exports")
                and seed_record.get("configuration_id") == arm["configuration_id"]
                and seed_record.get("provenance") == provenance
                and (
                    isinstance(row.get("portable_control_export_sha256"), str)
                    if arm["uses_p2"]
                    else row.get("portable_control_export_sha256") is None
                )
            ):
                raise InvalidEvidenceError(f"checkpoint provenance drift: {process['role']}")
            if arm["uses_p2"]:
                export = root / "seed-work" / str(row["seed"]) / "control-export.pt"
                if digest(export) != row["portable_control_export_sha256"]:
                    raise InvalidEvidenceError(f"portable control export drift: {process['role']}")
            checkpoint_rows.append(
                {
                    "checkpoint_sha256": row["checkpoint_sha256"],
                    "candidate_export_sha256": row["portable_candidate_exports"],
                    "provenance": closed,
                    "seed": row["seed"],
                }
            )
            evaluation_rows.append(
                {
                    "evaluation_record_sha256": digest(seed_path),
                    "provenance": closed,
                    "seed": row["seed"],
                }
            )
        if conditioned and (None in mapping_hashes or any(len(value) != 64 for value in mapping_hashes)):
            raise EngineeringIncompleteError(f"conditioned mapping hash absent: {process['role']}")
        stream_closure = []
        for row in streams["streams"]:
            closed = verified_provenance(row.get("provenance", {}), row["training_seed"])
            if not isinstance(row.get("stream_sha256"), str) or len(row["stream_sha256"]) != 64:
                raise InvalidEvidenceError(f"stream identity drift: {process['role']}")
            stream_closure.append(
                {
                    "member_id": row["member_id"],
                    "point_id": row["point_id"],
                    "provenance": closed,
                    "stream_sha256": row["stream_sha256"],
                    "training_seed": row["training_seed"],
                }
            )
        closures.append(
            {
                "candidate": process["candidate"],
                "checkpoints": checkpoint_rows,
                "checkpoint_mapping_sha256": sorted(value for value in mapping_hashes if value),
                "evaluations": evaluation_rows,
                "role": process["role"],
                "stream_count": streams["stream_count"],
                "streams": stream_closure,
                "streams_json_sha256": digest(root / "streams.json"),
                "training_json_sha256": digest(root / "training.json"),
            }
        )
    return role_map, closures


def terminal_for(result: dict, attribution: dict, runtime: dict) -> str:
    runtime_valid = {
        treatment: (
            runtime["arms"][CONFIGURATION_CANDIDATES[treatment]][
                "engineering_eligible"
            ]
            and runtime["arms"][CONFIGURATION_CANDIDATES[control]][
                "engineering_eligible"
            ]
            and
            runtime["arms"][CONFIGURATION_CANDIDATES[treatment]]["classification"] != "FAIL"
            and runtime["arms"][CONFIGURATION_CANDIDATES[control]]["classification"] != "FAIL"
        )
        for treatment, control in PAIRINGS.items()
    }
    temporal = {
        treatment: bool(result["candidate_decisions"][treatment]["temporally_eligible"])
        for treatment in PAIRINGS
    }
    full = {
        treatment: runtime_valid[treatment] and temporal[treatment] and attribution[treatment]["passes"]
        for treatment in PAIRINGS
    }
    if not any(runtime_valid.values()):
        return "HOLD-A10M5R15-RUNTIME-INELIGIBLE"
    if any(runtime_valid[t] and temporal[t] for t in PAIRINGS) and not any(full.values()):
        return "HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED"
    if not any(runtime_valid[t] and temporal[t] for t in PAIRINGS):
        return "HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT"
    return "A10M5R15-TEMPORAL-READY"


def runtime_aggregate(rows: list[dict]) -> dict:
    horizon_ratios = {
        str(years): sum(
            row["candidate_median_seconds"]
            for row in rows
            if row["horizon_years"] == years
        )
        / sum(
            row["faithful_median_seconds"]
            for row in rows
            if row["horizon_years"] == years
        )
        for years in (30, 100)
    }
    regime_ratios = {
        regime: sum(
            row["candidate_median_seconds"] for row in rows if row["regime"] == regime
        )
        / sum(
            row["faithful_median_seconds"] for row in rows if row["regime"] == regime
        )
        for regime in sorted({row["regime"] for row in rows})
    }
    worst = max(*horizon_ratios.values(), *regime_ratios.values())
    return {
        "classification": "PASS" if worst < 5.0 else "WARN" if worst < 30.0 else "FAIL",
        "horizon_ratios": horizon_ratios,
        "regime_ratios": regime_ratios,
        "worst_ratio": worst,
    }


def runtime_mad_ratio(values: list[float]) -> float:
    median = statistics.median(values)
    return statistics.median(abs(item - median) for item in values) / median


def runtime_discard_contaminated_pairs(
    candidate: list[float], faithful: list[float]
) -> tuple[list[int], list[int]]:
    kept = list(range(len(candidate)))
    discarded = []
    while (
        runtime_mad_ratio([candidate[index] for index in kept]) > 0.10
        or runtime_mad_ratio([faithful[index] for index in kept]) > 0.10
    ) and len(discarded) < 2:
        candidate_median = statistics.median(candidate[index] for index in kept)
        faithful_median = statistics.median(faithful[index] for index in kept)
        worst = max(
            kept,
            key=lambda index: max(
                abs(candidate[index] - candidate_median) / candidate_median,
                abs(faithful[index] - faithful_median) / faithful_median,
            ),
        )
        kept.remove(worst)
        discarded.append(worst)
    return kept, discarded


def runtime_engineering_gates(
    rows: list[dict], probes: dict, artifact: dict, arm: dict, safeguards: dict
) -> dict[str, bool]:
    return {
        "absolute_warm_time": all(
            row["candidate_median_seconds"]
            <= (
                safeguards["warm_30_year_seconds_max"]
                if row["horizon_years"] == 30
                else safeguards["warm_100_year_seconds_max"]
            )
            for row in rows
        ),
        "candidate_export_size": all(
            export["bytes"] <= safeguards["export_bytes_max"]
            for export in artifact["candidate_exports"].values()
        ),
        "candidate_model_size": arm["parameter_count"]
        <= safeguards["model_parameters_max"],
        "clean_export_cold_start": all(
            probe["cold_start_seconds"] <= safeguards["cold_start_seconds_max"]
            for probe in probes.values()
        ),
        "clean_export_peak_rss": all(
            probe["vmhwm_bytes"] <= safeguards["peak_rss_bytes_max"]
            and probe["external_peak_rss_bytes"] <= safeguards["peak_rss_bytes_max"]
            for probe in probes.values()
        ),
        "clean_export_prefix_exact": probes["30"]["output_identity"]
        == probes["100"]["prefix_identity"],
        "clean_export_support": all(
            probe["support"] is True
            and probe["torch_threads"] == 1
            and probe["torch_interop_threads"] == 1
            for probe in probes.values()
        ),
        "complete_output": all(row["candidate_complete"] is True for row in rows),
        "contamination_bound": all(
            len(row["discarded_contaminated_trial_indices"]) <= 2 for row in rows
        ),
        "deterministic_output": all(
            len(row["candidate_identities"]) == 1 for row in rows
        ),
        "stable_samples": all(
            row["candidate_mad_over_median"] <= 0.10
            and row["faithful_mad_over_median"] <= 0.10
            for row in rows
        ),
    }


def verify_runtime_semantics(options, manifest: dict, runtime: dict) -> None:
    execution = json.loads(
        (options.asset_root / "execution-contract.json").read_text(encoding="utf-8")
    )
    sites = json.loads((options.asset_root / "sites.json").read_text(encoding="utf-8"))[
        "sites"
    ]
    arm_by_candidate = {row["candidate"]: row for row in execution["arms"]}
    site_regimes = {row["point_id"]: row["regime"] for row in sites}
    rows = runtime.get("rows", [])
    expected_roster = {
        (arm["arm"], arm["candidate"], site["point_id"], site["regime"], years)
        for arm in execution["arms"]
        for site in sites
        for years in (30, 100)
    }
    observed_roster = {
        (
            row.get("arm"),
            row.get("candidate"),
            row.get("site"),
            row.get("regime"),
            row.get("horizon_years"),
        )
        for row in rows
    }
    if len(rows) != 48 or observed_roster != expected_roster:
        raise InvalidEvidenceError("runtime Cartesian roster drift")
    for row in rows:
        candidate = row["candidate"]
        retained = row.get("retained_trial_indices")
        discarded = row.get("discarded_contaminated_trial_indices")
        raw_candidate = row.get("raw_candidate_samples_seconds")
        raw_faithful = row.get("raw_faithful_samples_seconds")
        candidate_samples = row.get("candidate_samples_seconds")
        faithful_samples = row.get("faithful_samples_seconds")
        raw_candidate_repeats = row.get("raw_candidate_repeat_counts")
        raw_faithful_repeats = row.get("raw_faithful_repeat_counts")
        candidate_repeats = row.get("candidate_repeat_counts")
        faithful_repeats = row.get("faithful_repeat_counts")
        if not all(
            isinstance(value, list)
            for value in (
                retained,
                discarded,
                raw_candidate,
                raw_faithful,
                candidate_samples,
                faithful_samples,
                raw_candidate_repeats,
                raw_faithful_repeats,
                candidate_repeats,
                faithful_repeats,
            )
        ):
            raise InvalidEvidenceError("runtime sample roster malformed")
        expected_retained, expected_discarded = runtime_discard_contaminated_pairs(
            raw_candidate, raw_faithful
        )
        numeric = [
            *raw_candidate,
            *raw_faithful,
            *candidate_samples,
            *faithful_samples,
            row.get("candidate_median_seconds"),
            row.get("faithful_median_seconds"),
            row.get("ratio"),
        ]
        if not (
            row.get("arm") == arm_by_candidate[candidate]["arm"]
            and row.get("regime") == site_regimes[row["site"]]
            and row.get("training_seed") == 147031
            and isinstance(row.get("candidate_identities"), list)
            and bool(row["candidate_identities"])
            and row["candidate_identities"] == sorted(set(row["candidate_identities"]))
            and all(
                isinstance(identity, str) and len(identity) == 64
                for identity in row["candidate_identities"]
            )
            and type(row.get("candidate_complete")) is bool
            and isinstance(row.get("faithful_identities"), list)
            and bool(row["faithful_identities"])
            and row["faithful_identities"] == sorted(set(row["faithful_identities"]))
            and all(
                isinstance(identity, str) and len(identity) == 64
                for identity in row["faithful_identities"]
            )
            and type(row.get("faithful_complete")) is bool
            and isinstance(retained, list)
            and isinstance(discarded, list)
            and len(raw_candidate) == len(raw_faithful) == 9
            and retained == expected_retained
            and discarded == expected_discarded
            and 7 <= len(retained) <= 9
            and len(discarded) <= 2
            and set(retained).isdisjoint(discarded)
            and set(retained) | set(discarded) == set(range(9))
            and candidate_samples == [raw_candidate[index] for index in retained]
            and faithful_samples == [raw_faithful[index] for index in retained]
            and candidate_repeats == [raw_candidate_repeats[index] for index in retained]
            and faithful_repeats == [raw_faithful_repeats[index] for index in retained]
            and len(raw_candidate_repeats) == len(raw_faithful_repeats) == 9
            and all(type(value) is int and value > 0 for value in raw_candidate_repeats)
            and all(type(value) is int and value > 0 for value in raw_faithful_repeats)
            and all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in numeric)
            and type(row.get("rerun_used")) is bool
            and (
                row["rerun_used"]
                or (
                    runtime_mad_ratio(raw_candidate) <= 0.10
                    and runtime_mad_ratio(raw_faithful) <= 0.10
                )
            )
            and row.get("candidate_mad_over_median")
            == runtime_mad_ratio(candidate_samples)
            and row.get("faithful_mad_over_median")
            == runtime_mad_ratio(faithful_samples)
            and row["candidate_median_seconds"] == statistics.median(candidate_samples)
            and row["faithful_median_seconds"] == statistics.median(faithful_samples)
            and row["ratio"]
            == row["candidate_median_seconds"] / row["faithful_median_seconds"]
        ):
            raise InvalidEvidenceError("runtime row semantic drift")
    expected_artifacts = {}
    for candidate, arm in arm_by_candidate.items():
        root = options.evidence_root / "results" / arm["role"] / "seed-work/147031"
        expected_artifacts[candidate] = {
            "arm": arm["arm"],
            "candidate_exports": {
                str(years): {
                    "bytes": (root / f"candidate-export-{years}.pt").stat().st_size,
                    "sha256": digest(root / f"candidate-export-{years}.pt"),
                }
                for years in (30, 100)
            },
            "checkpoint": {
                "bytes": (root / "checkpoint.pt").stat().st_size,
                "sha256": digest(root / "checkpoint.pt"),
            },
            "control_export": (
                {
                    "bytes": (root / "control-export.pt").stat().st_size,
                    "sha256": digest(root / "control-export.pt"),
                }
                if arm["uses_p2"]
                else None
            ),
            "role": arm["role"],
            "training_seed": 147031,
        }
    if runtime.get("artifact_identities") != expected_artifacts:
        raise InvalidEvidenceError("timed candidate artifact identity drift")
    probes = runtime.get("export_probes", {})
    if set(probes) != set(arm_by_candidate) or any(
        set(candidate_probes) != {"30", "100"}
        for candidate_probes in probes.values()
    ):
        raise InvalidEvidenceError("clean export probe roster drift")
    for candidate_probes in probes.values():
        for horizon, probe in candidate_probes.items():
            expected_days = 10957 if horizon == "30" else 36524
            if not (
                probe.get("output_shape") == [8, 1, expected_days, 15]
                and isinstance(probe.get("output_identity"), str)
                and len(probe["output_identity"]) == 64
                and isinstance(probe.get("prefix_identity"), str)
                and len(probe["prefix_identity"]) == 64
                and type(probe.get("support")) is bool
                and probe.get("torch_threads") == 1
                and probe.get("torch_interop_threads") == 1
                and all(
                    isinstance(probe.get(key), (int, float))
                    and math.isfinite(probe[key])
                    and probe[key] > 0
                    for key in (
                        "elapsed_seconds",
                        "cold_start_seconds",
                        "external_peak_rss_bytes",
                        "process_start_to_exit_seconds",
                        "vmhwm_bytes",
                    )
                )
            ):
                raise InvalidEvidenceError("clean export probe semantic drift")
    dependency_names = {
        "cargo-vendor.tar.gz",
        "corpus.tar",
        "requirements.lock",
        "runtime.tar.gz",
        "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz",
        "source.tar.gz",
        "runtime-parameters.tar",
        "wheelhouse.tar",
    }
    expected_dependencies = {
        name: {key: manifest["assets"][name][key] for key in ("bytes", "sha256")}
        for name in dependency_names
    }
    dependencies = runtime.get("dependencies", {})
    environment = runtime.get("environment", {})
    compiler = runtime.get("compiler", {})
    if not (
        dependencies.get("assets") == expected_dependencies
        and dependencies.get("python") == "3.11.15"
        and dependencies.get("python_implementation") == "CPython"
        and dependencies.get("numpy") == "2.2.6"
        and dependencies.get("torch") == "2.7.1+cu128"
        and runtime.get("logical_member_count") == 8
        and runtime.get("daily_field_count") == 8
        and runtime.get("parameter_identities") == PARAMETER_IDENTITIES
        and runtime.get("timed_samples") == 9
        and runtime.get("warmups") == 2
        and runtime.get("safeguards")
        == {
            "cold_start_seconds_max": 15.0,
            "export_bytes_max": 262144000,
            "model_parameters_max": 50000000,
            "peak_rss_bytes_max": 2147483648,
            "warm_100_year_seconds_max": 30.0,
            "warm_30_year_seconds_max": 10.0,
        }
        and environment.get("hostname") == "node03"
        and environment.get("machine") == "x86_64"
        and environment.get("cuda_hidden") is True
        and environment.get("cuda_visible_devices") == ""
        and environment.get("nvidia_visible_devices") == "void"
        and environment.get("thread_environment")
        == {
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        }
        and environment.get("torch_threads") == 1
        and environment.get("torch_interop_threads") == 1
        and len(environment.get("affinity", [])) == 1
        and all(
            isinstance(environment.get(key), str) and environment[key]
            for key in ("cpu_model", "governor", "kernel", "platform")
        )
        and isinstance(environment.get("os_release"), dict)
        and bool(environment["os_release"])
        and isinstance(compiler.get("cargo"), str)
        and compiler["cargo"].startswith("cargo 1.92.0 ")
        and isinstance(compiler.get("rustc_verbose"), str)
        and compiler["rustc_verbose"].startswith("rustc 1.92.0 ")
        and runtime.get("corpus")
        == {
            "execution_contract": execution["corpus"],
            "manifest_identity": expected_dependencies["corpus.tar"],
        }
    ):
        raise InvalidEvidenceError("runtime environment provenance drift")
    safeguards = runtime["safeguards"]
    for candidate, arm in arm_by_candidate.items():
        selected = [row for row in rows if row["candidate"] == candidate]
        engineering_gates = runtime_engineering_gates(
            selected,
            probes[candidate],
            runtime["artifact_identities"][candidate],
            arm,
            safeguards,
        )
        expected_arm = {
            **runtime_aggregate(selected),
            "engineering_eligible": all(engineering_gates.values()),
            "engineering_gates": engineering_gates,
        }
        if runtime["arms"].get(candidate) != expected_arm:
            raise InvalidEvidenceError("runtime arm aggregate or engineering-gate drift")
    computed_gates = {
        "all_rows_finite": all(math.isfinite(row["ratio"]) for row in rows),
        "arm_roster_complete": set(runtime["arms"]) == set(arm_by_candidate),
        "cuda_hidden": environment["cuda_hidden"] is True,
        "faithful_output_complete": all(
            row["faithful_complete"] is True for row in rows
        ),
        "faithful_output_deterministic": all(
            len(row["faithful_identities"]) == 1 for row in rows
        ),
        "raw_timed_sample_count": all(
            len(row["raw_candidate_samples_seconds"]) == 9
            and len(row["raw_faithful_samples_seconds"]) == 9
            for row in rows
        ),
        "single_core": len(environment["affinity"]) == 1,
        "single_thread": environment["torch_threads"] == 1
        and environment["torch_interop_threads"] == 1,
        "timed_sample_count": all(
            7 <= len(row["candidate_samples_seconds"]) <= 9
            and len(row["candidate_samples_seconds"])
            == len(row["faithful_samples_seconds"])
            for row in rows
        ),
    }
    if runtime.get("gates") != computed_gates:
        raise InvalidEvidenceError("runtime safeguard gate recomputation drift")


def verify_analysis_receipts(options, manifest: dict, head: str) -> tuple[dict, dict]:
    calibration = json.loads(options.calibration_receipt.read_text(encoding="utf-8"))
    runtime = json.loads(options.runtime_receipt.read_text(encoding="utf-8"))
    manifest_sha256 = digest(options.asset_root / "asset-manifest.json")
    calibration_identity = {
        "bytes": options.calibration_receipt.stat().st_size,
        "sha256": digest(options.calibration_receipt),
    }
    calibration_commit = calibration.get("source_commit", "")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", calibration_commit, head),
        cwd=REPO,
        check=False,
    ).returncode == 0
    if not (
        authenticated(calibration)
        and calibration_identity
        == {key: manifest["assets"]["attribution-calibration.json"][key] for key in ("bytes", "sha256")}
        and calibration.get("package_id") == PACKAGE_ID
        and calibration.get("valid") is True
        and calibration.get("candidate_output_accessed") is False
        and calibration.get("protected_roles_opened") == []
        and calibration.get("asset_manifest_sha256")
        == "7988efbb342045f0df5ce05ddb810cc36c8be46f145f4c0bc531d02c56291c05"
        and calibration.get("calibration_source_commit")
        == "719d83451ddff698b280219708f7648ff73c8f9d"
        and calibration.get("calibration_stream_sha256")
        == "2bb8379f639712dc864308510bd2a8c10ac9c39ea3cae609abdc2a2bf51384ff"
        and calibration.get("sequence_seeds") == [410542, 410543]
        and calibration.get("replicates") == 1000
        and calibration.get("nearest_rank_zero_based_index") == 899
        and isinstance(calibration.get("gates"), dict)
        and calibration["gates"]
        and all(calibration["gates"].values())
        and math.isfinite(calibration.get("margin", math.nan))
        and calibration["margin"] > 0
        and ancestor
    ):
        raise InvalidEvidenceError("attribution calibration receipt authentication failed")
    binary_identity = {"bytes": options.binary.stat().st_size, "sha256": digest(options.binary)}
    runtime_gates = runtime.get("gates")
    if not (
        authenticated(runtime)
        and runtime.get("package_id") == PACKAGE_ID
        and runtime.get("source_commit") == head
        and runtime.get("asset_manifest_sha256") == manifest_sha256
        and runtime.get("binary") == binary_identity
        and runtime.get("runtime_rule") == {"pass_below": 5.0, "warn_below": 30.0}
        and runtime.get("protected_roles_opened") == []
        and isinstance(runtime_gates, dict)
        and set(runtime_gates)
        == {
            "all_rows_finite",
            "arm_roster_complete",
            "cuda_hidden",
            "faithful_output_complete",
            "faithful_output_deterministic",
            "raw_timed_sample_count",
            "single_core",
            "single_thread",
            "timed_sample_count",
        }
        and len(runtime.get("rows", [])) == 48
        and set(runtime.get("arms", {})) == set(PARAMETER_COUNTS)
        and all(
            row.get("classification") in {"PASS", "WARN", "FAIL"}
            and type(row.get("engineering_eligible")) is bool
            and isinstance(row.get("engineering_gates"), dict)
            and math.isfinite(row.get("worst_ratio", math.nan))
            for row in runtime["arms"].values()
        )
    ):
        raise InvalidEvidenceError("ADR-0006 runtime receipt authentication failed")
    verify_runtime_semantics(options, manifest, runtime)
    if not (
        runtime.get("valid") is True
        and all(runtime_gates.values())
    ):
        raise EngineeringIncompleteError("ADR-0006 runtime benchmark incomplete")
    return calibration, runtime


def non_gating_diagnostics(options, runtime: dict) -> dict:
    aligned = __import__("importlib.util").util.spec_from_file_location(
        "r15r2_aligned_diagnostics", options.asset_root / "aligned_objective.py"
    )
    if aligned is None or aligned.loader is None:
        raise RuntimeError("cannot load dispersion family registry")
    module = __import__("importlib.util").util.module_from_spec(aligned)
    aligned.loader.exec_module(module)
    metric_keys = tuple(module.metric_keys())
    dispersion_keys = dispersion_metric_keys(metric_keys)
    roles = {
        "E2C": "e2c-descriptor-anchored-residual-v1",
        "E2": "e2-normal-anchored-residual-v1",
    }
    dispersion = {}
    for arm, role in roles.items():
        values = []
        for seed in (147031, 271828, 314159):
            record = json.loads(
                (options.evidence_root / "results" / role / "seeds" / f"{seed}.json").read_text(
                    encoding="utf-8"
                )
            )
            scores = record["candidate"]["block_scores"]
            if set(scores) != set(metric_keys):
                raise InvalidEvidenceError("replacement selector score registry drift")
            selected = [float(scores[name]) for name in dispersion_keys]
            if not selected or not all(math.isfinite(value) for value in selected):
                raise EngineeringIncompleteError("replacement dispersion diagnostic incomplete")
            values.append(float(np.mean(selected)))
        dispersion[arm] = float(np.median(values))
    runtime_rows = runtime["rows"]
    e2_seconds = sum(
        row["candidate_median_seconds"]
        for row in runtime_rows
        if row["candidate"] == "normal_anchored_residual"
    )
    e1_seconds = sum(
        row["candidate_median_seconds"]
        for row in runtime_rows
        if row["candidate"] == "normal_conditioned_smooth_climatology"
    )
    if min(dispersion.values()) <= 0 or e1_seconds <= 0:
        raise EngineeringIncompleteError("non-gating diagnostic denominator invalid")
    return {
        "e2_over_e1_warm_runtime_ratio": e2_seconds / e1_seconds,
        "e2_over_e2c_combined_monthly_and_annual_interannual_dispersion_ratio": (
            dispersion["E2"] / dispersion["E2C"]
        ),
        "replacement_dispersion_components": dispersion,
        "selection_gating": False,
    }


def execute() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--semantic-plan", type=Path, required=True)
    parser.add_argument("--plan-receipt", type=Path, required=True)
    parser.add_argument("--calibration-receipt", type=Path, required=True)
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()
    if options.output_root.exists():
        raise EngineeringIncompleteError("fresh replay output required")
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    require_published(Path(__file__).resolve(), head)
    require_published(PACKAGE / "artifacts/rev2_selector.py", head)
    if head != upstream:
        raise InvalidEvidenceError("replay requires exact published main")
    manifest = json.loads((options.asset_root / "asset-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("source_commit") != head or manifest.get("package_id") != PACKAGE_ID:
        raise InvalidEvidenceError("asset publication identity drift")
    if {"bytes": options.corpus.stat().st_size, "sha256": digest(options.corpus)} != manifest["assets"]["corpus.tar"]:
        raise InvalidEvidenceError("corpus identity drift")
    plan, plan_receipt, collection = verify_collection(options, head)
    verify_replay_asset_bundle(options, plan, manifest, head)
    calibration, runtime = verify_analysis_receipts(options, manifest, head)
    execution = json.loads((options.asset_root / "execution-contract.json").read_text(encoding="utf-8"))
    _, provenance_closure = verify_provenance(
        options, manifest, plan, runtime, execution
    )
    options.output_root.mkdir(mode=0o700)
    observations = options.output_root / "observations"
    sites = json.loads((options.asset_root / "sites.json").read_text(encoding="utf-8"))["sites"]
    extract_observations(options.corpus, observations, sites)
    try:
        first, first_sequences = run_selector(
            asset_root=options.asset_root, binary=options.binary, data_root=options.data_root,
            evidence_root=options.evidence_root, observations=observations,
            output_root=options.output_root / "pass-a", bootstrap_seed=410542,
        )
        second, second_sequences = run_selector(
            asset_root=options.asset_root, binary=options.binary, data_root=options.data_root,
            evidence_root=options.evidence_root, observations=observations,
            output_root=options.output_root / "pass-b", bootstrap_seed=410542,
        )
        first_bytes = (options.output_root / "pass-a/temporal-result.json").read_bytes()
        second_bytes = (options.output_root / "pass-b/temporal-result.json").read_bytes()
        if first_bytes != second_bytes or first_sequences != second_sequences:
            raise EngineeringIncompleteError("selector replays differ")
        attribution = {}
        for treatment, control in PAIRINGS.items():
            treatment_u90 = float(np.quantile(first_sequences[treatment], 0.90))
            control_u90 = float(np.quantile(first_sequences[control], 0.90))
            if not all(math.isfinite(value) and value > 0 for value in (treatment_u90, control_u90)):
                raise EngineeringIncompleteError("non-finite attribution input")
            gain = 1.0 - treatment_u90 / control_u90
            attribution[treatment] = {
                "bootstrap_seed": 410542,
                "control": control,
                "control_u90": control_u90,
                "gain": gain,
                "margin": calibration["margin"],
                "passes": gain >= calibration["margin"],
                "treatment_u90": treatment_u90,
            }
        result = dict(first)
        result["attribution"] = attribution
        result["runtime"] = runtime["arms"]
        result["non_gating_diagnostics"] = non_gating_diagnostics(options, runtime)
        result["selector_replays_byte_identical"] = True
        result["terminal"] = terminal_for(result, attribution, runtime)
        if result["terminal"] not in TERMINALS:
            raise InvalidEvidenceError("terminal precedence failure")
        result_path = options.output_root / "temporal-result.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        closure = {
            "arms": [
                {**row, "runtime_classification": runtime["arms"][row["candidate"]]["classification"]}
                for row in provenance_closure
            ],
            "calendar_profile_id": "daymet_official_365_v1",
            "package_id": PACKAGE_ID,
            "protected_roles_opened": [],
            "runtime_receipt_sha256": digest(options.runtime_receipt),
            "schema_version": 1,
            "valid": True,
        }
        (options.output_root / "provenance-closure.json").write_text(
            json.dumps(closure, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        replay = {
            "asset_manifest_sha256": digest(options.asset_root / "asset-manifest.json"),
            "attribution_calibration_receipt_sha256": digest(options.calibration_receipt),
            "byte_identical_passes": True,
            "collection_record_sha256": collection["record_sha256"],
            "package_id": PACKAGE_ID,
            "plan_id": collection["plan_id"],
            "plan_receipt_record_sha256": plan_receipt["record_sha256"],
            "protected_roles_opened": [],
            "provenance_closure_sha256": digest(options.output_root / "provenance-closure.json"),
            "record_type": "a10m5r15r2-precleanup-replay",
            "run_id": RUN_ID,
            "runtime_receipt_sha256": digest(options.runtime_receipt),
            "source_commit": head,
            "temporal_result_sha256": digest(result_path),
            "terminal": result["terminal"],
        }
        replay["record_sha256"] = hashlib.sha256(
            json.dumps(replay, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        (options.output_root / "replay-identity.json").write_text(
            json.dumps(replay, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(result["terminal"])
    except BaseException:
        shutil.rmtree(options.output_root, ignore_errors=True)
        raise


def main() -> None:
    try:
        execute()
    except SystemExit:
        raise
    except BaseException as error:
        try:
            index = sys.argv.index("--output-root")
            output_root = Path(sys.argv[index + 1])
        except (ValueError, IndexError):
            raise
        output_root.mkdir(parents=True, exist_ok=True)
        terminal = failure_terminal(error)
        record = {
            "error": {"message": str(error), "type": type(error).__name__},
            "package_id": PACKAGE_ID,
            "protected_roles_opened": [],
            "record_type": "a10m5r15r2-terminal-failure",
            "run_id": RUN_ID,
            "terminal": terminal,
            "valid": False,
        }
        record["record_sha256"] = hashlib.sha256(
            json.dumps(record, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).hexdigest()
        (output_root / "terminal-failure.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(terminal)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
