#!/usr/bin/env python3
"""Run the frozen single-core ADR-0006 benchmark for every R2 arm."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260722-a10m5r15r2r4-e2-initialization-remedy"
SEED = 147031
MEMBERS = 8
PARAMETER_IDENTITIES = {
    "p+4050_-11375": {"bytes": 7022, "sha256": "e6d1a9f1aa93b3c8389b83cc9e09ab02688924ac3ffaf9d5f046fb71a5be7704"},
    "p+4525_-08875": {"bytes": 7022, "sha256": "7586415909ec4eadfadfc9d9378500cec3d47a64dcbe861bb146ef8d9d48fc0f"},
    "p+3250_-10200": {"bytes": 7022, "sha256": "2ef4231cb4fe9843e70b7f7c962fab7df8f6b169e488c270ec77199faf13803f"},
    "p+3275_-08325": {"bytes": 7022, "sha256": "68350d92b5ba93524a4c735e058d6dae5a941f1f87ca1cf8c44d592c45e366a7"},
    "p+3675_-10750": {"bytes": 7022, "sha256": "2a02b7449fe92460dde0b399328b9a2b28aad9134fa416e95e840d057b4083d5"},
    "p+4025_-09900": {"bytes": 7022, "sha256": "600d160ef3b27d30bff5b50de53b28e84ccd72db313bd37c2177f67da0837b78"},
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def command_version(*command: str) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark dependency: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runspec(parameter: Path, output: Path, years: int, burn: int) -> str:
    return (
        "cligen_runspec: 1\n"
        f"station:\n  par: {parameter}\n"
        "mode: continuous\n"
        f"simulation:\n  begin_year: 2001\n  years: {years}\n  interpolation: none\n"
        f"rng:\n  burn: {burn}\n"
        "generation_profile: faithful_5_32_3\nqc_filter: faithful\n"
        f"output:\n  cli: {output}\n  quality: false\n  overwrite: true\n"
    )


def faithful_call(binary: Path, parameter: Path, work: Path, years: int) -> tuple[str, bool]:
    work.mkdir(parents=True, exist_ok=True)
    expected = 16 + sum(
        366 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 365
        for year in range(2001, 2001 + years)
    )
    identities, complete = [], True
    for member in range(MEMBERS):
        output = work / f"faithful-{member}.cli"
        specification = work / f"faithful-{member}.yaml"
        specification.write_text(runspec(parameter, output, years, member), encoding="utf-8")
        completed = subprocess.run(
            (str(binary), "run", str(specification)),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"faithful benchmark failed: {completed.stderr[-400:]}")
        lines = output.read_text(encoding="utf-8").splitlines()
        identities.append(digest(output))
        complete = complete and len(lines) == expected
    payload = "\n".join(identities).encode("ascii")
    return hashlib.sha256(payload).hexdigest(), complete


def timed_minimum(call) -> tuple[float, int, set[str], bool]:
    started, repeats, identities, complete = time.perf_counter(), 0, set(), True
    while time.perf_counter() - started < 1.0 or repeats == 0:
        current, valid = call()
        identities.add(current)
        complete, repeats = complete and valid, repeats + 1
    return time.perf_counter() - started, repeats, identities, complete


def mad_ratio(values: list[float]) -> float:
    median = statistics.median(values)
    return statistics.median(abs(item - median) for item in values) / median


def classify(ratio: float) -> str:
    return "PASS" if ratio < 5.0 else "WARN" if ratio < 30.0 else "FAIL"


def discard_contaminated_pairs(
    candidate: list[float], faithful: list[float]
) -> tuple[list[int], list[int]]:
    """Discard at most two paired trials under the frozen contamination bound."""
    kept = list(range(len(candidate)))
    discarded: list[int] = []
    while (
        mad_ratio([candidate[index] for index in kept]) > 0.10
        or mad_ratio([faithful[index] for index in kept]) > 0.10
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


def forward_control(
    control: torch.jit.ScriptModule,
    features: torch.Tensor,
    station: torch.Tensor,
    initial_hidden: torch.Tensor,
) -> torch.Tensor:
    hidden = initial_hidden
    chunks = []
    for start in range(0, features.shape[1], 365):
        heads, hidden = control(features[:, start : start + 365], station, hidden)
        chunks.append(heads)
    return torch.cat(chunks, dim=1)


def materialize_daily_fields(
    heads: torch.Tensor, uniforms: torch.Tensor, direction: torch.Tensor
) -> torch.Tensor:
    wet = (uniforms[..., 0] < torch.sigmoid(heads[..., 0])).float()
    amount_scale = torch.nn.functional.softplus(heads[..., 2]) + 1.0e-4
    amount_normal = math.sqrt(2.0) * torch.erfinv(2.0 * uniforms[..., 1] - 1.0)
    amount = torch.exp(heads[..., 1] + amount_scale * amount_normal)
    locations = heads[..., 3::2]
    scales = torch.nn.functional.softplus(heads[..., 4::2]) + 1.0e-4
    offsets = torch.arange(6, device=heads.device, dtype=torch.float32) / 7.0
    normals = torch.sqrt(-2.0 * torch.log(uniforms[..., 1:2])) * torch.cos(
        2.0 * math.pi * (uniforms[..., 2:3] + offsets)
    )
    continuous = locations + scales * normals
    tmean = continuous[..., 0]
    dtr = torch.exp(continuous[..., 1])
    return torch.stack(
        (
            wet * amount,
            tmean + dtr / 2.0,
            tmean - dtr / 2.0,
            torch.exp(continuous[..., 2]),
            torch.exp(continuous[..., 3]),
            torch.exp(continuous[..., 4]),
            86400.0 * torch.sigmoid(continuous[..., 5]),
            direction,
        ),
        dim=-1,
    )


def host_environment(cpu: int) -> dict[str, object]:
    cpu_model = "unknown"
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu_model = line.partition(":")[2].strip()
                break
    os_release = {}
    release_path = Path("/etc/os-release")
    if release_path.is_file():
        for line in release_path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key in {"ID", "VERSION_ID", "PRETTY_NAME"}:
                os_release[key] = value.strip().strip('"')
    governor_path = Path(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_governor")
    return {
        "affinity": sorted(os.sched_getaffinity(0)),
        "cpu_model": cpu_model,
        "governor": (
            governor_path.read_text(encoding="utf-8").strip()
            if governor_path.is_file()
            else "unavailable"
        ),
        "hostname": platform.node(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "os_release": os_release,
        "platform": platform.platform(),
    }


def clean_export_probe(
    candidate_export: Path,
    control_export: Path | None,
    days: int,
    width: int,
    time_output: Path,
) -> dict[str, object]:
    worker = """import time
started=time.perf_counter()
import hashlib,json,os,resource,sys
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.use_deterministic_algorithms(True)
candidate=torch.jit.load(sys.argv[1],map_location='cpu').eval()
control=torch.jit.load(sys.argv[2],map_location='cpu').eval() if sys.argv[2] else None
cold_start_seconds=time.perf_counter()-started
days=int(sys.argv[3]); width=int(sys.argv[4])
features=torch.zeros((1,days,13),dtype=torch.float32)
physics=torch.zeros((1,days,width),dtype=torch.float32)
base=torch.zeros((1,days,15),dtype=torch.float32)
if control is not None:
 hidden=torch.zeros((1,1,144),dtype=torch.float32); chunks=[]; station=torch.tensor([1200])
 for start in range(0,days,365):
  heads,hidden=control(features[:,start:start+365],station,hidden); chunks.append(heads)
 base=torch.cat(chunks,dim=1)
medium=torch.zeros((8,1,days,8),dtype=torch.float32)
slow=torch.zeros((8,1,days,4),dtype=torch.float32)
with torch.inference_mode(): output=candidate(base,physics,medium,slow).contiguous()
payload=output.numpy().tobytes()
prefix=output[:,:,:min(days,10957)].contiguous().numpy().tobytes()
value={'cold_start_seconds':cold_start_seconds,'elapsed_seconds':time.perf_counter()-started,'output_identity':hashlib.sha256(payload).hexdigest(),'output_shape':list(output.shape),'prefix_identity':hashlib.sha256(prefix).hexdigest(),'support':bool(torch.isfinite(output).all()),'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads(),'vmhwm_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
print(json.dumps(value,separators=(',',':'),sort_keys=True))
"""
    environment = dict(os.environ)
    started = time.perf_counter()
    completed = subprocess.run(
        (
            "/usr/bin/time",
            "-v",
            "-o",
            str(time_output),
            sys.executable,
            "-c",
            worker,
            str(candidate_export),
            str(control_export or ""),
            str(days),
            str(width),
        ),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    process_elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        raise RuntimeError(f"clean export probe failed: {completed.stderr[-400:]}")
    value = json.loads(completed.stdout)
    maximum_rss_kb = None
    for line in time_output.read_text(encoding="utf-8").splitlines():
        if "Maximum resident set size (kbytes):" in line:
            maximum_rss_kb = int(line.rpartition(":")[2].strip())
            break
    if maximum_rss_kb is None:
        raise RuntimeError("external peak-RSS measurement absent")
    value["external_peak_rss_bytes"] = maximum_rss_kb * 1024
    value["process_start_to_exit_seconds"] = process_elapsed
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--parameter-root", type=Path, required=True)
    parser.add_argument("--rustc", type=Path, required=True)
    parser.add_argument("--cargo", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if options.work_root.exists() or options.output.exists():
        raise RuntimeError("fresh runtime benchmark destinations required")
    manifest = json.loads((options.asset_root / "asset-manifest.json").read_text(encoding="utf-8"))
    head = manifest.get("source_commit")
    script_identity = identity(Path(__file__))
    expected_script = manifest.get("assets", {}).get("run_runtime_benchmarks.py", {})
    if (
        not isinstance(head, str)
        or len(head) != 40
        or script_identity != {key: expected_script.get(key) for key in ("bytes", "sha256")}
    ):
        raise RuntimeError("runtime benchmark requires exact published assets")
    if not hasattr(os, "sched_getaffinity"):
        raise RuntimeError("Linux CPU affinity is required")
    allowed = sorted(os.sched_getaffinity(0))
    if not allowed:
        raise RuntimeError("no CPU affinity available")
    os.sched_setaffinity(0, {allowed[0]})
    if len(os.sched_getaffinity(0)) != 1:
        raise RuntimeError("single-core affinity failed")
    for variable in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        if os.environ.get(variable) != "1":
            raise RuntimeError(f"single-thread environment missing: {variable}=1")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.cuda.is_available() or torch.cuda.device_count() != 0:
        raise RuntimeError("GPU must be hidden from the portable CPU benchmark")
    sys.path.insert(0, str(options.asset_root))
    import climate_core as climate
    import continuous_core as continuous
    import portfolio_core as portfolio
    import residual_core as residuals

    experiment = load_module(
        "r15r2_runtime_experiment",
        options.asset_root / "inherited_r15_candidate_experiment.py",
    )
    contract = json.loads((options.asset_root / "portfolio-contract.json").read_text(encoding="utf-8"))
    execution = json.loads((options.asset_root / "execution-contract.json").read_text(encoding="utf-8"))
    sites = json.loads((options.asset_root / "sites.json").read_text(encoding="utf-8"))["sites"]
    continuous.load_conditioning(options.asset_root)
    device = torch.device("cpu")
    controls: dict[str, torch.jit.ScriptModule] = {}
    exports: dict[str, dict[int, torch.jit.ScriptModule]] = {}
    artifact_identities = {}
    export_probes = {}
    options.work_root.mkdir(mode=0o700)
    probe_root = options.work_root / "clean-export-probes"
    probe_root.mkdir()
    for arm in execution["arms"]:
        candidate = arm["candidate"]
        role_root = options.evidence_root / "results" / arm["role"]
        seed_root = role_root / "seed-work" / str(SEED)
        checkpoint = seed_root / "checkpoint.pt"
        candidate_exports = {
            years: seed_root / f"candidate-export-{years}.pt" for years in (30, 100)
        }
        control_path = seed_root / "control-export.pt" if arm["uses_p2"] else None
        export_probes[candidate] = {
            str(years): clean_export_probe(
                path,
                control_path,
                len(experiment.date_axis(years)),
                42 if arm["uses_normals"] else 6,
                probe_root / f"{arm['arm']}-{years}.time-v.txt",
            )
            for years, path in candidate_exports.items()
        }
        exports[candidate] = {
            years: torch.jit.load(str(path), map_location=device).eval()
            for years, path in candidate_exports.items()
        }
        control_identity = None
        if arm["uses_p2"]:
            export = seed_root / "control-export.pt"
            controls[candidate] = torch.jit.load(str(export), map_location=device).eval()
            control_identity = identity(export)
        artifact_identities[candidate] = {
            "arm": arm["arm"],
            "candidate_exports": {
                str(years): identity(path) for years, path in candidate_exports.items()
            },
            "checkpoint": identity(checkpoint),
            "control_export": control_identity,
            "role": arm["role"],
            "training_seed": SEED,
        }
    parameters = {}
    for site in sites:
        parameter = options.parameter_root / f"{site['point_id']}.par"
        if identity(parameter) != PARAMETER_IDENTITIES.get(site["point_id"]):
            raise RuntimeError(f"benchmark parameter identity drift: {site['point_id']}")
        parameters[site["point_id"]] = parameter
    rows = []
    for arm in execution["arms"]:
        candidate = arm["candidate"]
        for site_index, site in enumerate(sites):
            for years in (30, 100):
                features, months, year_indices, dates = experiment.generation_tensors(
                    years, float(site["latitude"]), float(site["longitude"]),
                    float(site["elevation_m"]), device,
                )
                station = torch.tensor([1200], dtype=torch.long, device=device)
                control = controls.get(candidate)
                physics = features[..., 7:13]
                if arm["uses_normals"]:
                    continuous.set_generation_point(site["point_id"])
                    physics = continuous.condition_generation_features(physics)
                    continuous.set_generation_point(None)
                initial_hidden = torch.zeros((1, 1, 144), dtype=torch.float32, device=device)
                empty_base = torch.zeros((1, len(dates), 15), dtype=torch.float32, device=device)
                normal_lookups_before = continuous._NORMAL_LOOKUPS

                def candidate_call():
                    with torch.inference_mode():
                        base_heads = (
                            forward_control(control, features, station, initial_hidden)
                            if arm["uses_p2"]
                            else empty_base
                        )
                        innovations = {
                            "medium_daily": residuals.member_innovations(
                                MEMBERS, 1, len(dates), 8,
                                SEED + site_index * 100_003 + 1009, device,
                            ),
                            "slow_daily": residuals.member_innovations(
                                MEMBERS, 1, len(dates), 4,
                                SEED + site_index * 100_003 + 2018, device,
                            ),
                        }
                        heads = exports[candidate][years](
                            base_heads,
                            physics,
                            innovations["medium_daily"],
                            innovations["slow_daily"],
                        )
                        uniforms = climate.member_uniforms(
                            MEMBERS, 1, len(dates),
                            SEED + site_index * 100_003 + 900_000, device,
                        )
                        direction = climate.member_uniforms(
                            MEMBERS, 1, len(dates),
                            SEED + site_index * 100_003 + 1_800_000, device,
                        )[..., 0]
                        weather = materialize_daily_fields(heads, uniforms, direction)
                        values = weather[:, 0].cpu().numpy().astype("<f4", copy=False)
                    support = bool(
                        np.isfinite(values).all()
                        and np.all(values[..., 0] >= 0)
                        and np.all(values[..., 1] >= values[..., 2])
                        and np.all(values[..., 3:7] >= 0)
                        and np.all(values[..., 6] <= 86400)
                        and np.all((values[..., 7] > 0) & (values[..., 7] < 1))
                    )
                    if not arm["uses_normals"] and continuous._NORMAL_LOOKUPS != normal_lookups_before:
                        raise RuntimeError("descriptor-only benchmark requested normal conditioning")
                    return hashlib.sha256(values.tobytes()).hexdigest(), support

                faithful = lambda: faithful_call(
                    options.binary, parameters[site["point_id"]],
                    options.work_root / "faithful" / arm["arm"] / site["point_id"] / str(years), years,
                )
                candidate_complete = faithful_complete = True
                candidate_identities: set[str] = set()
                faithful_identities: set[str] = set()
                for _ in range(2):
                    warm_identity, warm_valid = candidate_call()
                    candidate_identities.add(warm_identity)
                    candidate_complete = candidate_complete and warm_valid
                    warm_identity, warm_valid = faithful()
                    faithful_identities.add(warm_identity)
                    faithful_complete = faithful_complete and warm_valid
                candidate_samples, faithful_samples = [], []
                candidate_repeats, faithful_repeats = [], []
                rerun_used = False
                for pass_index in range(2):
                    candidate_samples.clear(); faithful_samples.clear()
                    candidate_repeats.clear(); faithful_repeats.clear()
                    for sample in range(9):
                        order = (("candidate", candidate_call), ("faithful", faithful))
                        if sample % 2:
                            order = tuple(reversed(order))
                        for name, call in order:
                            elapsed, repeats, output_identities, valid = timed_minimum(call)
                            if name == "candidate":
                                candidate_samples.append(elapsed / repeats)
                                candidate_repeats.append(repeats)
                                candidate_identities.update(output_identities)
                                candidate_complete = candidate_complete and valid
                            else:
                                faithful_samples.append(elapsed / repeats)
                                faithful_repeats.append(repeats)
                                faithful_identities.update(output_identities)
                                faithful_complete = faithful_complete and valid
                    if mad_ratio(candidate_samples) <= 0.10 and mad_ratio(faithful_samples) <= 0.10:
                        break
                    if pass_index == 0:
                        rerun_used = True
                raw_candidate_samples = list(candidate_samples)
                raw_faithful_samples = list(faithful_samples)
                raw_candidate_repeats = list(candidate_repeats)
                raw_faithful_repeats = list(faithful_repeats)
                kept, discarded = discard_contaminated_pairs(
                    raw_candidate_samples, raw_faithful_samples
                )
                candidate_samples = [raw_candidate_samples[index] for index in kept]
                faithful_samples = [raw_faithful_samples[index] for index in kept]
                candidate_repeats = [raw_candidate_repeats[index] for index in kept]
                faithful_repeats = [raw_faithful_repeats[index] for index in kept]
                candidate_median = statistics.median(candidate_samples)
                faithful_median = statistics.median(faithful_samples)
                rows.append(
                    {
                        "arm": arm["arm"], "candidate": candidate,
                        "candidate_complete": candidate_complete,
                        "candidate_identities": sorted(candidate_identities),
                        "candidate_mad_over_median": mad_ratio(candidate_samples),
                        "candidate_median_seconds": candidate_median,
                        "candidate_repeat_counts": candidate_repeats,
                        "candidate_samples_seconds": candidate_samples,
                        "discarded_contaminated_trial_indices": discarded,
                        "faithful_identities": sorted(faithful_identities),
                        "faithful_complete": faithful_complete,
                        "faithful_mad_over_median": mad_ratio(faithful_samples),
                        "faithful_median_seconds": faithful_median,
                        "faithful_repeat_counts": faithful_repeats,
                        "faithful_samples_seconds": faithful_samples,
                        "horizon_years": years, "ratio": candidate_median / faithful_median,
                        "raw_candidate_repeat_counts": raw_candidate_repeats,
                        "raw_candidate_samples_seconds": raw_candidate_samples,
                        "raw_faithful_repeat_counts": raw_faithful_repeats,
                        "raw_faithful_samples_seconds": raw_faithful_samples,
                        "regime": site["regime"], "rerun_used": rerun_used,
                        "retained_trial_indices": kept,
                        "site": site["point_id"], "training_seed": SEED,
                    }
                )
                shutil.rmtree(
                    options.work_root
                    / "faithful"
                    / arm["arm"]
                    / site["point_id"]
                    / str(years)
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
    safeguards = {
        "cold_start_seconds_max": 15.0,
        "export_bytes_max": 262144000,
        "model_parameters_max": 50000000,
        "peak_rss_bytes_max": 2147483648,
        "warm_100_year_seconds_max": 30.0,
        "warm_30_year_seconds_max": 10.0,
    }
    for arm in execution["arms"]:
        candidate = arm["candidate"]
        selected = [row for row in rows if row["candidate"] == candidate]
        candidate_probes = export_probes[candidate]
        engineering_gates = {
            "absolute_warm_time": all(
                row["candidate_median_seconds"]
                <= (
                    safeguards["warm_30_year_seconds_max"]
                    if row["horizon_years"] == 30
                    else safeguards["warm_100_year_seconds_max"]
                )
                for row in selected
            ),
            "candidate_export_size": all(
                export["bytes"] <= safeguards["export_bytes_max"]
                for export in artifact_identities[candidate]["candidate_exports"].values()
            ),
            "candidate_model_size": arm["parameter_count"]
            <= safeguards["model_parameters_max"],
            "clean_export_cold_start": all(
                probe["cold_start_seconds"] <= safeguards["cold_start_seconds_max"]
                for probe in candidate_probes.values()
            ),
            "clean_export_peak_rss": all(
                probe["vmhwm_bytes"] <= safeguards["peak_rss_bytes_max"]
                and probe["external_peak_rss_bytes"]
                <= safeguards["peak_rss_bytes_max"]
                for probe in candidate_probes.values()
            ),
            "clean_export_prefix_exact": candidate_probes["30"]["output_identity"]
            == candidate_probes["100"]["prefix_identity"],
            "clean_export_support": all(
                probe["support"] is True
                and probe["torch_threads"] == 1
                and probe["torch_interop_threads"] == 1
                for probe in candidate_probes.values()
            ),
            "complete_output": all(row["candidate_complete"] for row in selected),
            "contamination_bound": all(
                len(row["discarded_contaminated_trial_indices"]) <= 2
                for row in selected
            ),
            "deterministic_output": all(
                len(row["candidate_identities"]) == 1 for row in selected
            ),
            "stable_samples": all(
                row["candidate_mad_over_median"] <= 0.10
                and row["faithful_mad_over_median"] <= 0.10
                for row in selected
            ),
        }
        arms[candidate]["engineering_eligible"] = all(engineering_gates.values())
        arms[candidate]["engineering_gates"] = engineering_gates
    gates = {
        "all_rows_finite": all(math.isfinite(row["ratio"]) for row in rows),
        "arm_roster_complete": set(arms) == {row["candidate"] for row in execution["arms"]},
        "cuda_hidden": not torch.cuda.is_available() and torch.cuda.device_count() == 0,
        "faithful_output_complete": all(row["faithful_complete"] for row in rows),
        "faithful_output_deterministic": all(
            len(row["faithful_identities"]) == 1 for row in rows
        ),
        "raw_timed_sample_count": all(
            len(row["raw_candidate_samples_seconds"]) == 9
            and len(row["raw_faithful_samples_seconds"]) == 9
            for row in rows
        ),
        "single_core": not hasattr(os, "sched_getaffinity") or len(os.sched_getaffinity(0)) == 1,
        "single_thread": torch.get_num_threads() == 1 and torch.get_num_interop_threads() == 1,
        "timed_sample_count": all(
            7 <= len(row["candidate_samples_seconds"]) <= 9
            and len(row["candidate_samples_seconds"]) == len(row["faithful_samples_seconds"])
            for row in rows
        ),
    }
    pinned_cpu = next(iter(os.sched_getaffinity(0)))
    dependency_assets = {
        name: {key: manifest["assets"][name][key] for key in ("bytes", "sha256")}
        for name in (
            "cargo-vendor.tar.gz",
            "corpus.tar",
            "requirements.lock",
            "runtime.tar.gz",
            "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz",
            "source.tar.gz",
            "runtime-parameters.tar",
            "wheelhouse.tar",
        )
    }
    receipt = {
        "arms": arms,
        "artifact_identities": artifact_identities,
        "asset_manifest_sha256": digest(options.asset_root / "asset-manifest.json"),
        "binary": identity(options.binary),
        "compiler": {
            "cargo": command_version(str(options.cargo), "--version"),
            "rustc_verbose": command_version(str(options.rustc), "--version", "--verbose"),
        },
        "corpus": {
            "execution_contract": execution["corpus"],
            "manifest_identity": dependency_assets["corpus.tar"],
        },
        "dependencies": {
            "assets": dependency_assets,
            "numpy": np.__version__,
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "torch": torch.__version__,
        },
        "daily_field_count": 8,
        "environment": {
            **host_environment(pinned_cpu),
            "cuda_hidden": not torch.cuda.is_available() and torch.cuda.device_count() == 0,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "nvidia_visible_devices": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
            "thread_environment": {
                name: os.environ.get(name)
                for name in (
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                )
            },
            "torch_interop_threads": torch.get_num_interop_threads(),
            "torch_threads": torch.get_num_threads(),
        },
        "export_probes": export_probes,
        "gates": gates,
        "logical_member_count": MEMBERS,
        "package_id": PACKAGE_ID,
        "parameter_identities": PARAMETER_IDENTITIES,
        "protected_roles_opened": [],
        "rows": rows,
        "runtime_rule": {"pass_below": 5.0, "warn_below": 30.0},
        "safeguards": safeguards,
        "schema_version": 1,
        "source_commit": head,
        "timed_samples": 9,
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
    print("A10M5R15R2-ADR0006-BENCHMARK-COMPLETE")


if __name__ == "__main__":
    main()
