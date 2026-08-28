#!/usr/bin/env python3
"""Execute the source-bound A11E7 faithful temperature QC attribution."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import importlib.util
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
MANIFEST = PACKAGE / "execution-manifest-v1.json"
SCHEMA = PACKAGE / "execution-manifest-v1.schema.json"
SPEC = ROOT / "docs/specifications/SPEC-A11-FAITHFUL-TEMPERATURE-QC-ATTRIBUTION.md"
PACKAGE_DOC = PACKAGE.parent / "package.md"
PLAN = ROOT / "docs/exec-plans/20260828-a11e7-faithful-temperature-qc-attribution.md"
PANEL = ROOT / "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json"
A11E1 = ROOT / "docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts/execute.py"
A11E2_DIR = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts"
A11E2 = A11E2_DIR / "execute.py"
A11E2_MANIFEST = A11E2_DIR / "execution-manifest-v1.json"
A11E5_EXECUTOR = ROOT / "docs/work-packages/20260827-a11e5-interannual-family-stability/artifacts/execute.py"
A11E6_DIR = ROOT / "docs/work-packages/20260827-a11e6-faithful-baseline-comparison/artifacts"
A11E6_EVIDENCE = A11E6_DIR / "development-evidence-v1.json"
A11E6_PROVENANCE = A11E6_DIR / "cryptographic-provenance-receipt-v1.json"
A11E6S_REVIEW = ROOT / "docs/work-packages/20260827-a11e6s-faithful-temperature-static-review/artifacts/static-review.md"
RUNTIME_ROOT = ROOT / "target/a11e7-faithful-temperature-qc-runtime"
BURNS = (0, 101, 1009, 10007, 100003, 1000003, 10000019, 100000007,
         17, 31, 53, 79, 127, 199, 317, 503, 797, 1259, 1999, 3163, 5003,
         7919, 12547, 19867, 31469, 49853, 78977, 125087, 198149, 313919,
         497503, 788129)
METRICS = ("monthly_temperature_dispersion_error", "annual_temperature_dispersion_error",
           "temperature_cross_month_correlation_rmse", "annual_temperature_lag1_error",
           "annual_temperature_low_frequency_error", "monthly_temperature_mean_absolute_error_c")


class ExecutionError(RuntimeError):
    pass


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    partial.replace(path)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise ExecutionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def git(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if result.returncode: raise ExecutionError(f"git failed: {' '.join(args)}")
    return result.stdout


def validate_manifest(value: Any) -> dict[str, Any]:
    required = {"schema_version", "execution_id", "profile", "arms", "burns", "station_count", "years",
                "material_variance_ratio", "material_error_ratio", "noninferiority_ratio", "structural_variance_ratio",
                "runtime", "resource_bound", "confirmation_target_access", "dependencies"}
    if not isinstance(value, dict) or set(value) != required: raise ExecutionError("manifest fields differ")
    if value["schema_version"] != 1 or value["execution_id"] != "a11e7-faithful-temperature-qc-attribution-v1": raise ExecutionError("manifest identity differs")
    if value["profile"] != "faithful_5_32_3" or value["arms"] != ["faithful", "off"]: raise ExecutionError("manifest arms differ")
    if value["burns"] != list(BURNS) or len(set(BURNS)) != 32: raise ExecutionError("burn grid differs")
    if value["station_count"] != 20 or value["years"] != 16 or value["resource_bound"] != {"streams_per_execution": 1280, "replays": 1}: raise ExecutionError("resource grid differs")
    if value["confirmation_target_access"] is not False: raise ExecutionError("confirmation must remain sealed")
    return value


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if len(source_commit) != 40 or source_commit != git("rev-parse", "origin/main").decode().strip(): raise ExecutionError("source is not exact origin/main")
    required = (Path(__file__), MANIFEST, SCHEMA, PACKAGE / "test_execute.py", SPEC, PACKAGE_DOC, PLAN)
    hashes = {}
    for path in required:
        relative = path.relative_to(ROOT).as_posix(); blob = git("show", f"{source_commit}:{relative}")
        if blob != path.read_bytes(): raise ExecutionError(f"working source differs: {relative}")
        hashes[relative] = hashlib.sha256(blob).hexdigest()
    deps = manifest["dependencies"]
    checks = ((PANEL, "panel_sha256"), (A11E6_EVIDENCE, "a11e6_evidence_sha256"),
              (A11E6_PROVENANCE, "a11e6_provenance_sha256"), (A11E6S_REVIEW, "a11e6s_review_sha256"),
              (A11E1, "a11e1_executor_sha256"), (A11E2, "a11e2_executor_sha256"),
              (A11E5_EXECUTOR, "a11e5_executor_sha256"), (ROOT / "Cargo.lock", "cargo_lock_sha256"),
              (ROOT / "Cargo.toml", "cargo_toml_sha256"))
    for path, key in checks:
        if digest(path) != deps[key]: raise ExecutionError(f"dependency drifted: {path}")
    return {"source_commit": source_commit, "source_tree": git("rev-parse", f"{source_commit}^{{tree}}").decode().strip(),
            "published_ref": "origin/main", "source_hashes": hashes}


def parse_cli(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    precipitation = np.zeros((16, 12)); tmean = np.zeros((16, 12)); daily_range = np.zeros((16, 12)); wet = np.zeros((16, 12)); counts = np.zeros((16, 12), dtype=int)
    rows = 0
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) != 13: continue
        try: day, month, year = map(int, fields[:3]); values = list(map(float, fields[3:]))
        except ValueError: continue
        if not (1 <= year <= 16 and 1 <= month <= 12 and 1 <= day <= calendar.monthrange(year, month)[1]): raise ExecutionError("invalid generated date")
        y, m = year - 1, month - 1; precipitation[y, m] += values[0]; tmean[y, m] += (values[4] + values[5]) / 2.0; daily_range[y, m] += values[4] - values[5]; wet[y, m] += float(values[0] > 0.0); counts[y, m] += 1; rows += 1
    if rows != 5844: raise ExecutionError(f"expected 5844 rows, found {rows}")
    for year in range(1, 17):
        for month in range(1, 13):
            if counts[year - 1, month - 1] != calendar.monthrange(year, month)[1]: raise ExecutionError("incomplete generated month")
    precipitation *= 30.4375 / counts; tmean /= counts; daily_range /= counts; wet /= counts
    return precipitation, tmean, daily_range, wet


def month_sum(value: dict[str, int]) -> int:
    if len(value) != 12 or not all(isinstance(v, int) and v >= 0 for v in value.values()): raise ExecutionError("invalid process month counts")
    return sum(value.values())


def process_summary(report: dict[str, Any], arm: str) -> dict[str, Any]:
    process = report.get("process")
    if not isinstance(process, dict) or process.get("qc_filter") != arm: raise ExecutionError("quality process identity differs")
    if arm == "faithful":
        selected = [row for row in process["retries"] if row["parameter"] in (2, 3)]
        if len(selected) != 2 or process["counterfactual"] is not None: raise ExecutionError("faithful process shape differs")
        return {"temperature_rejected_attempts": sum(month_sum(row["rejected_attempts"]) for row in selected),
                "temperature_accepted_batches": sum(month_sum(row["accepted_batches"]) for row in selected),
                "temperature_cap_give_ups": sum(event["parameter"] in (2, 3) for event in process["cap_give_ups"])}
    counter = process.get("counterfactual")
    if not isinstance(counter, dict): raise ExecutionError("off counterfactual is absent")
    selected = [row for row in counter["by_parameter"] if row["parameter"] in (2, 3)]
    if len(selected) != 2: raise ExecutionError("off temperature counterfactual differs")
    batches = sum(month_sum(row["batches"]) for row in selected); rejects = sum(month_sum(row["would_reject"]) for row in selected)
    return {"temperature_counterfactual_batches": batches, "temperature_counterfactual_would_reject": rejects,
            "temperature_counterfactual_rejection_fraction": rejects / batches}


def temperature_metrics(gp: np.ndarray, gt: np.ndarray, observed: dict[str, Any], weights: np.ndarray, a11e5: Any) -> dict[str, float]:
    all_metrics = a11e5.interannual_metrics(gp, gt, observed["precipitation"], observed["tmean"], weights)
    metrics = {name: all_metrics[name] for name in METRICS[:-1]}
    metrics[METRICS[-1]] = float(np.mean(np.abs(np.mean(gt, axis=0) - np.mean(observed["tmean"], axis=0))))
    if set(metrics) != set(METRICS) or not all(math.isfinite(value) and value >= 0.0 for value in metrics.values()): raise ExecutionError("temperature metrics invalid")
    return metrics


def build_decision(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    if len(rows) != 640 or len({(r["station_id"], r["member_id"]) for r in rows}) != 640: raise ExecutionError("decision grid differs")
    on_ratio = np.array([r["arms"]["faithful"]["annual_temperature_variance_ratio"] for r in rows]); off_ratio = np.array([r["arms"]["off"]["annual_temperature_variance_ratio"] for r in rows])
    on_error = np.abs(np.log(on_ratio)); off_error = np.abs(np.log(off_ratio)); pair_ratio = off_ratio / on_ratio
    mean_on = np.array([r["arms"]["faithful"]["metrics"][METRICS[-1]] for r in rows]); mean_off = np.array([r["arms"]["off"]["metrics"][METRICS[-1]] for r in rows])
    variance_shift = float(np.median(pair_ratio)); error_ratio = float(np.median(off_error) / max(np.median(on_error), 1e-12)); mean_ratio = float(np.median(mean_off) / max(np.median(mean_on), 1e-12))
    relief = variance_shift >= manifest["material_variance_ratio"] and error_ratio <= manifest["material_error_ratio"]
    mean_ok = mean_ratio <= manifest["noninferiority_ratio"]; structural = float(np.median(off_ratio)) < manifest["structural_variance_ratio"]
    if relief and not mean_ok: disposition = "QC_MATERIAL_WITH_CLIMATOLOGY_COST"
    elif relief and structural: disposition = "QC_MATERIAL_AND_STRUCTURAL_DEFICIT_REMAINS"
    elif relief: disposition = "QC_DOMINANT"
    elif 0.9 <= variance_shift <= 1.1 and 0.95 <= error_ratio <= 1.05: disposition = "QC_NOT_MATERIAL"
    else: disposition = "QC_MIXED"
    metric_summary = {}
    for name in METRICS:
        on = float(np.median([r["arms"]["faithful"]["metrics"][name] for r in rows])); off = float(np.median([r["arms"]["off"]["metrics"][name] for r in rows]))
        metric_summary[name] = {"faithful_median": on, "off_median": off, "ratio_off_over_faithful": off / max(on, 1e-12)}
    stations = []
    for station in sorted({r["station_id"] for r in rows}):
        selected = [r for r in rows if r["station_id"] == station]; station_on = np.array([r["arms"]["faithful"]["annual_temperature_variance_ratio"] for r in selected]); station_off = np.array([r["arms"]["off"]["annual_temperature_variance_ratio"] for r in selected])
        stations.append({"station_id": station, "faithful_median_variance_ratio": float(np.median(station_on)), "off_median_variance_ratio": float(np.median(station_off)), "median_off_over_faithful": float(np.median(station_off / station_on)), "off_closer_members": int(np.sum(np.abs(np.log(station_off)) < np.abs(np.log(station_on))))})
    return {"disposition": disposition, "annual_temperature_variance": {"faithful_median_generated_over_observed": float(np.median(on_ratio)), "off_median_generated_over_observed": float(np.median(off_ratio)), "median_pair_ratio_off_over_faithful": variance_shift, "geometric_mean_pair_ratio_off_over_faithful": float(np.exp(np.mean(np.log(pair_ratio)))), "faithful_median_absolute_log_error": float(np.median(on_error)), "off_median_absolute_log_error": float(np.median(off_error)), "ratio_of_median_errors_off_over_faithful": error_ratio, "off_closer_pair_count": int(np.sum(off_error < on_error)), "off_farther_pair_count": int(np.sum(off_error > on_error))}, "material_qc_relief": relief, "monthly_temperature_mean_noninferior": mean_ok, "structural_deficit_remains": structural, "metrics": metric_summary, "station_summaries": stations}


def execute(source_commit: str) -> None:
    started = time.monotonic(); manifest = validate_manifest(json.loads(MANIFEST.read_text())); runtime = {"python": platform.python_version(), "numpy": np.__version__}
    if runtime != manifest["runtime"]: raise ExecutionError("scientific runtime differs")
    source = verify_source(source_commit, manifest)
    if RUNTIME_ROOT.exists(): raise ExecutionError(f"runtime root exists: {RUNTIME_ROOT}")
    try:
        station_root = Path(os.environ.get("CLIGEN_DATA_DIR", str(Path.home() / ".cache/cligen"))) / "stations/us-2015/2026.07"; database = station_root / "2015_stations.db"
        if digest(database) != manifest["dependencies"]["station_database_sha256"]: raise ExecutionError("station database differs")
        panel = json.loads(PANEL.read_text()); stations = panel["stations"]
        if len(stations) != 20: raise ExecutionError("station panel differs")
        station_files = {}
        for station in stations:
            path = station_root / f"{station['station_id']}.par"
            if digest(path) != station["parameter_sha256"]: raise ExecutionError(f"parameter differs: {station['station_id']}")
            station_files[station["station_id"]] = path
        predecessor = load_module("a11e2_for_a11e7", A11E2); pred_manifest = predecessor.validate_manifest(json.loads(A11E2_MANIFEST.read_text())); inherited_hashes, development_rows, _ = predecessor.verify_inputs(pred_manifest); inherited = predecessor.ensure_base_loaded(); development, observed_preflight = inherited.load_development(development_rows); observed_by_id = {row["point_id"]: row for row in development}
        a11e5 = load_module("a11e5_for_a11e7", A11E5_EXECUTOR); anchor = {(row["station_id"], row["burn"]): row for row in json.loads(A11E6_EVIDENCE.read_text())["rows"]}
        weights = np.asarray([calendar.monthrange(2001, month)[1] for month in range(1, 13)], dtype=np.float64); weights /= np.sum(weights)
        RUNTIME_ROOT.mkdir(parents=True); build_target = RUNTIME_ROOT / "build"; build = subprocess.run(["cargo", "build", "--release", "--locked", "--bin", "cligen", "--target-dir", str(build_target)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode: raise ExecutionError(f"release build failed: {build.stderr[-4000:]}")
        binary = build_target / "release/cligen"; binary_sha = digest(binary); rows = []; anchor_count = 0
        for station in stations:
            station_id = station["station_id"]; observed = observed_by_id[station_id]
            for member_id, burn in enumerate(BURNS):
                arms = {}
                for arm in ("faithful", "off"):
                    run_dir = RUNTIME_ROOT / "runs" / station_id / str(member_id) / arm; run_dir.mkdir(parents=True); par = run_dir / "source.par"; shutil.copyfile(station_files[station_id], par); cli = run_dir / "out.cli"; runspec = run_dir / "run.yaml"
                    qc_line = f"qc_filter: {arm}\n"; runspec.write_text("cligen_runspec: 1\nstation:\n  par: source.par\nmode: continuous\nsimulation:\n  begin_year: 1\n  years: 16\n  interpolation: none\nrng:\n  burn: %d\ngeneration_profile: faithful_5_32_3\n%soutput:\n  cli: out.cli\n  quality: true\n  overwrite: false\n  command_echo: '-r%d -isource.par'\n" % (burn, qc_line, burn))
                    run = subprocess.run([str(binary), "run", "run.yaml"], cwd=run_dir, capture_output=True, text=True)
                    if run.returncode: raise ExecutionError(f"cligen failed {station_id}/{burn}/{arm}: {run.stderr[-2000:]}")
                    provenance = run_dir / "out.cli.provenance.json"; quality = run_dir / "out.cli.quality.json"; gp, gt, gr, gw = parse_cli(cli); metrics = temperature_metrics(gp, gt, observed, weights, a11e5); generated_annual = gt @ weights; observed_annual = observed["tmean"] @ weights; ratio = float(np.var(generated_annual, ddof=1) / max(np.var(observed_annual, ddof=1), 1e-12)); stream_hash = canonical_digest({"precipitation": gp.tolist(), "temperature": gt.tolist(), "range": gr.tolist(), "wet_fraction": gw.tolist()})
                    if arm == "faithful" and burn in BURNS[:8]:
                        closed = anchor[(station_id, burn)]
                        if stream_hash != closed["faithful_stream_summary_sha256"] or any(metrics[name] != closed["faithful_metrics"][name] for name in METRICS[:-1]) or metrics[METRICS[-1]] != closed["faithful_metrics"][METRICS[-1]]: raise ExecutionError(f"A11E6 faithful replay differs: {station_id}/{burn}")
                        anchor_count += 1
                    arms[arm] = {"metrics": metrics, "annual_temperature_variance_ratio": ratio, "signed_log_annual_temperature_variance_ratio": math.log(max(ratio, 1e-300)), "process": process_summary(json.loads(quality.read_text()), arm), "stream_summary_sha256": stream_hash, "provenance": {"source_par_sha256": digest(par), "runspec_sha256": digest(runspec), "cli_sha256": digest(cli), "provenance_sha256": digest(provenance), "quality_report_sha256": digest(quality), "cligen_binary_sha256": binary_sha}}
                rows.append({"station_id": station_id, "station_regime": observed["regime"], "member_id": member_id, "burn": burn, "arms": arms, "annual_variance_ratio_off_over_faithful": arms["off"]["annual_temperature_variance_ratio"] / arms["faithful"]["annual_temperature_variance_ratio"], "annual_absolute_log_error_off_minus_faithful": abs(arms["off"]["signed_log_annual_temperature_variance_ratio"]) - abs(arms["faithful"]["signed_log_annual_temperature_variance_ratio"])})
        if len(rows) * 2 != manifest["resource_bound"]["streams_per_execution"] or anchor_count != 160: raise ExecutionError("execution or anchor count differs")
        decision_body = build_decision(rows, manifest)
        preflight = {"schema_version": "a11e7-calendar-missingness-preflight-1", "valid": True, "source_transform": "daymet_official_365_v1", "normalized_statistic": "daymet_mask_normalized_month_v1", "observed": observed_preflight, "station_count": 20, "member_count": 32, "stream_count": 1280, "expected_daily_rows_per_stream": 5844, "station_database_sha256": digest(database), "a11e6_faithful_anchor_rows": anchor_count, "confirmation_target_series_accessed": False}
        evidence = {"schema_version": "a11e7-development-evidence-1", "execution_id": manifest["execution_id"], "source_commit": source_commit, "profile": manifest["profile"], "arms": manifest["arms"], "paired_rows": len(rows), "stream_count": len(rows) * 2, "rows": rows, "decision": decision_body, "limitations": ["sixteen-year observed and generated samples make variance and dependence estimates noisy", "paired burns share an origin but diverge after the first faithful rejection", "QC-off attribution does not add a missing year-scale climate state", "development observations have been reused across the A11 campaign"], "confirmation_target_series_accessed": False}; evidence["evidence_sha256"] = canonical_digest(evidence)
        decision = {"schema_version": "a11e7-development-decision-1", "terminal": "EXECUTED-COMPLETE", "science_status": "FAITHFUL_TEMPERATURE_QC_ATTRIBUTED", **decision_body, "confirmation_authorized": False, "production_authorized": False, "overlay_authorized": False}
        atomic_json(PACKAGE / "calendar-missingness-preflight-v1.json", preflight); atomic_json(PACKAGE / "development-evidence-v1.json", evidence); atomic_json(PACKAGE / "development-decision-v1.json", decision)
        outputs = [PACKAGE / name for name in ("calendar-missingness-preflight-v1.json", "development-evidence-v1.json", "development-decision-v1.json")]
        receipt = {"schema_version": "a11e7-execution-receipt-1", "execution_id": manifest["execution_id"], **source, "runtime": runtime, "build": {"command": "cargo build --release --locked --bin cligen --target-dir <deterministic-runtime>/build", "cargo_version": subprocess.check_output(["cargo", "--version"], text=True).strip(), "rustc_version": subprocess.check_output(["rustc", "--version"], text=True).strip(), "rustflags": os.environ.get("RUSTFLAGS", ""), "cargo_lock_sha256": digest(ROOT / "Cargo.lock"), "cargo_toml_sha256": digest(ROOT / "Cargo.toml"), "cligen_binary_sha256": binary_sha}, "station_database_sha256": digest(database), "source_parameter_sha256": {station["station_id"]: station["parameter_sha256"] for station in stations}, "inherited_input_hashes": inherited_hashes, "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in outputs}, "stream_count": 1280, "elapsed_seconds": time.monotonic() - started, "confirmation_target_series_accessed": False}; atomic_json(PACKAGE / "execution-receipt-v1.json", receipt)
    finally:
        if RUNTIME_ROOT.exists(): shutil.rmtree(RUNTIME_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--source-commit"); parser.add_argument("--validate-manifest", action="store_true"); parser.add_argument("--execute", action="store_true"); args = parser.parse_args(); manifest = validate_manifest(json.loads(MANIFEST.read_text()))
    if args.validate_manifest: print(canonical_digest(manifest)); return
    if not args.execute or not args.source_commit: parser.error("--execute requires --source-commit")
    execute(args.source_commit)


if __name__ == "__main__": main()
