#!/usr/bin/env python3
"""Run the frozen single-core ADR-0006 benchmark for every R2 arm."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
SEED = 147031


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark dependency: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runspec(parameter: Path, output: Path, years: int) -> str:
    return (
        "cligen_runspec: 1\n"
        f"station:\n  par: {parameter}\n"
        "mode: continuous\n"
        f"simulation:\n  begin_year: 2001\n  years: {years}\n  interpolation: none\n"
        "rng:\n  burn: 0\n"
        "generation_profile: faithful_5_32_3\nqc_filter: faithful\n"
        f"output:\n  cli: {output}\n  quality: false\n  overwrite: true\n"
    )


def faithful_call(binary: Path, parameter: Path, work: Path, years: int) -> tuple[str, bool]:
    work.mkdir(parents=True, exist_ok=True)
    output = work / "faithful.cli"
    specification = work / "faithful.yaml"
    specification.write_text(runspec(parameter, output, years), encoding="utf-8")
    completed = subprocess.run(
        (str(binary), "run", str(specification)), capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(f"faithful benchmark failed: {completed.stderr[-400:]}")
    lines = output.read_text(encoding="utf-8").splitlines()
    expected = 16 + sum(366 if year % 4 == 0 else 365 for year in range(2001, 2001 + years))
    return digest(output), len(lines) == expected


def timed_minimum(call) -> tuple[float, int, str, bool]:
    started, repeats, identity, complete = time.perf_counter(), 0, "", True
    while time.perf_counter() - started < 1.0 or repeats == 0:
        current, valid = call()
        if identity and current != identity:
            raise RuntimeError("timed output identity changed")
        identity, complete, repeats = current, complete and valid, repeats + 1
    return time.perf_counter() - started, repeats, identity, complete


def mad_ratio(values: list[float]) -> float:
    median = statistics.median(values)
    return statistics.median(abs(item - median) for item in values) / median


def classify(ratio: float) -> str:
    return "PASS" if ratio < 5.0 else "WARN" if ratio < 30.0 else "FAIL"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if options.work_root.exists() or options.output.exists():
        raise RuntimeError("fresh runtime benchmark destinations required")
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    published = subprocess.run(
        ("git", "show", f"{head}:{relative}"), cwd=REPO, check=True, capture_output=True
    ).stdout
    manifest = json.loads((options.asset_root / "asset-manifest.json").read_text(encoding="utf-8"))
    if head != upstream or published != Path(__file__).read_bytes() or manifest.get("source_commit") != head:
        raise RuntimeError("runtime benchmark requires exact published assets")
    if hasattr(os, "sched_getaffinity"):
        allowed = sorted(os.sched_getaffinity(0))
        if not allowed:
            raise RuntimeError("no CPU affinity available")
        os.sched_setaffinity(0, {allowed[0]})
        if len(os.sched_getaffinity(0)) != 1:
            raise RuntimeError("single-core affinity failed")
    for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        if os.environ.get(variable) != "1":
            raise RuntimeError(f"single-thread environment missing: {variable}=1")
    torch.set_num_threads(1)
    sys.path.insert(0, str(options.asset_root))
    import climate_core as climate
    import continuous_core as continuous
    import portfolio_core as portfolio
    import residual_core as residuals

    experiment = load_module(
        "r15r2_runtime_experiment",
        options.asset_root / "inherited_r15_candidate_experiment.py",
    )
    selector = load_module("r15r2_runtime_selector", options.asset_root / "temporal_select.py")
    contract = json.loads((options.asset_root / "portfolio-contract.json").read_text(encoding="utf-8"))
    execution = json.loads((options.asset_root / "execution-contract.json").read_text(encoding="utf-8"))
    sites = json.loads((options.asset_root / "sites.json").read_text(encoding="utf-8"))["sites"]
    continuous.load_conditioning(options.asset_root)
    device = torch.device("cpu")
    controls: dict[str, torch.jit.ScriptModule] = {}
    for arm in execution["arms"]:
        candidate = arm["candidate"]
        role_root = options.evidence_root / "results" / arm["role"]
        if arm["uses_p2"]:
            export = role_root / "seed-work" / str(SEED) / "control-export.pt"
            controls[candidate] = torch.jit.load(str(export), map_location=device).eval()
    options.work_root.mkdir(mode=0o700)
    localized = {}
    environment = dict(os.environ)
    environment["CLIGEN_DATA_DIR"] = str(options.data_root)
    for site in sites:
        root = options.work_root / "localization" / site["point_id"]
        completed = subprocess.run(
            (
                str(options.binary), "prism", "run", "--longitude", str(site["longitude"]),
                "--latitude", str(site["latitude"]), "--years", "100", "--output-dir", str(root),
            ),
            env=environment, capture_output=True, text=True, check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"benchmark localization failed: {completed.stderr[-400:]}")
        localized[site["point_id"]] = root / "source-station.par"
    rows = []
    models = {}
    for arm in execution["arms"]:
        candidate = arm["candidate"]
        for site_index, site in enumerate(sites):
            for years in (30, 100):
                features, months, year_indices, dates = experiment.generation_tensors(
                    years, float(site["latitude"]), float(site["longitude"]),
                    float(site["elevation_m"]), device,
                )
                station = torch.tensor([1200], dtype=torch.long, device=device)
                regimes = torch.zeros(1, dtype=torch.long, device=device)
                control = controls.get(candidate)
                model_key = (candidate, len(dates))
                if model_key not in models:
                    checkpoint = (
                        options.evidence_root / "results" / arm["role"]
                        / "seed-work" / str(SEED) / "checkpoint.pt"
                    )
                    model = continuous.build_candidate(
                        contract, candidate, days=len(dates), generation=True
                    ).to(device).eval()
                    model.load_state_dict(
                        torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
                    )
                    models[model_key] = model
                model = models[model_key]
                physics = features[..., 7:13]
                if model.uses_normals:
                    continuous.set_generation_point(site["point_id"])
                    physics = continuous.condition_generation_features(physics)
                    continuous.set_generation_point(None)

                def candidate_call():
                    with torch.inference_mode():
                        base_heads = (
                            portfolio.forward_control(control, features, station, 144)
                            if model.uses_p2
                            else None
                        )
                        innovations = experiment.generation_innovations(
                            model, 1, len(dates), SEED + site_index * 100_003, device
                        )
                        heads, _ = model.member_heads(
                            base_heads, physics, regimes, months,
                            year_indices, innovations,
                        )
                        uniforms = climate.member_uniforms(
                            1, 1, len(dates), SEED + site_index * 100_003 + 900_000, device
                        )
                        weather, _ = residuals.sample_member_weather(heads, uniforms, None)
                        values = weather[:, 0].cpu().numpy().astype("<f4")
                    support = bool(
                        np.isfinite(values).all()
                        and np.all(values[..., 0] >= 0)
                        and np.all(values[..., 1] >= values[..., 2])
                    )
                    return hashlib.sha256(values.tobytes()).hexdigest(), support

                faithful = lambda: faithful_call(
                    options.binary, localized[site["point_id"]],
                    options.work_root / "faithful" / arm["arm"] / site["point_id"] / str(years), years,
                )
                for _ in range(2):
                    candidate_call()
                    faithful()
                candidate_samples, faithful_samples = [], []
                candidate_repeats, faithful_repeats = [], []
                complete, rerun_used = True, False
                for pass_index in range(2):
                    candidate_samples.clear(); faithful_samples.clear()
                    candidate_repeats.clear(); faithful_repeats.clear()
                    for sample in range(9):
                        order = (("candidate", candidate_call), ("faithful", faithful))
                        if sample % 2:
                            order = tuple(reversed(order))
                        for name, call in order:
                            elapsed, repeats, _, valid = timed_minimum(call)
                            complete = complete and valid
                            if name == "candidate":
                                candidate_samples.append(elapsed / repeats)
                                candidate_repeats.append(repeats)
                            else:
                                faithful_samples.append(elapsed / repeats)
                                faithful_repeats.append(repeats)
                    if mad_ratio(candidate_samples) <= 0.10 and mad_ratio(faithful_samples) <= 0.10:
                        break
                    rerun_used = pass_index == 0
                candidate_median = statistics.median(candidate_samples)
                faithful_median = statistics.median(faithful_samples)
                rows.append(
                    {
                        "arm": arm["arm"], "candidate": candidate, "complete": complete,
                        "candidate_mad_over_median": mad_ratio(candidate_samples),
                        "candidate_median_seconds": candidate_median,
                        "candidate_repeat_counts": candidate_repeats,
                        "candidate_samples_seconds": candidate_samples,
                        "faithful_mad_over_median": mad_ratio(faithful_samples),
                        "faithful_median_seconds": faithful_median,
                        "faithful_repeat_counts": faithful_repeats,
                        "faithful_samples_seconds": faithful_samples,
                        "horizon_years": years, "ratio": candidate_median / faithful_median,
                        "regime": site["regime"], "rerun_used": rerun_used,
                        "site": site["point_id"], "training_seed": SEED,
                    }
                )
                continuous.set_generation_point(None)
    arms = {}
    for arm in execution["arms"]:
        candidate = arm["candidate"]
        selected = [row for row in rows if row["candidate"] == candidate]
        horizon_ratios = {
            str(years): sum(row["candidate_median_seconds"] for row in selected if row["horizon_years"] == years)
            / sum(row["faithful_median_seconds"] for row in selected if row["horizon_years"] == years)
            for years in (30, 100)
        }
        regime_ratios = {
            regime: sum(row["candidate_median_seconds"] for row in selected if row["regime"] == regime)
            / sum(row["faithful_median_seconds"] for row in selected if row["regime"] == regime)
            for regime in sorted({row["regime"] for row in selected})
        }
        worst = max(*horizon_ratios.values(), *regime_ratios.values())
        arms[candidate] = {
            "classification": classify(worst), "horizon_ratios": horizon_ratios,
            "regime_ratios": regime_ratios, "worst_ratio": worst,
        }
    gates = {
        "all_rows_complete": all(row["complete"] for row in rows),
        "all_rows_finite": all(math.isfinite(row["ratio"]) for row in rows),
        "all_rows_stable": all(
            row["candidate_mad_over_median"] <= 0.10 and row["faithful_mad_over_median"] <= 0.10
            for row in rows
        ),
        "arm_roster_complete": set(arms) == {row["candidate"] for row in execution["arms"]},
        "single_core": not hasattr(os, "sched_getaffinity") or len(os.sched_getaffinity(0)) == 1,
        "timed_sample_count": all(len(row["candidate_samples_seconds"]) == 9 for row in rows),
    }
    receipt = {
        "arms": arms,
        "asset_manifest_sha256": digest(options.asset_root / "asset-manifest.json"),
        "binary": {"bytes": options.binary.stat().st_size, "sha256": digest(options.binary)},
        "gates": gates,
        "package_id": PACKAGE_ID,
        "protected_roles_opened": [],
        "rows": rows,
        "runtime_rule": {"pass_below": 5.0, "warn_below": 30.0},
        "schema_version": 1,
        "source_commit": head,
        "valid": all(gates.values()),
        "warmups": 2,
    }
    receipt["record_sha256"] = hashlib.sha256(
        json.dumps(receipt, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not receipt["valid"]:
        raise SystemExit(1)
    print("A10M5R15R2-ADR0006-BENCHMARK-PASS")


if __name__ == "__main__":
    main()
