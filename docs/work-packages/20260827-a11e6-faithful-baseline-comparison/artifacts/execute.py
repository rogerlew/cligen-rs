#!/usr/bin/env python3
"""Execute the source-bound A11E6 faithful baseline comparison."""

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
SPEC = ROOT / "docs/specifications/SPEC-A11-FAITHFUL-BASELINE-COMPARISON.md"
PACKAGE_DOC = PACKAGE.parent / "package.md"
PLAN = ROOT / "docs/exec-plans/20260827-a11e6-faithful-baseline-comparison.md"
PANEL = ROOT / "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/panel-v1.json"
A11E1 = ROOT / "docs/work-packages/20260825-a11e1-observed-strategy-comparison/artifacts/execute.py"
A11E2_DIR = ROOT / "docs/work-packages/20260825-a11e2-nearest-candidate-forcing/artifacts"
A11E2 = A11E2_DIR / "execute.py"
A11E2_MANIFEST = A11E2_DIR / "execution-manifest-v1.json"
A11E3 = ROOT / "docs/work-packages/20260825-a11e3-multi-member-forcing-stability/artifacts/development-evidence-v1.json"
A11E5_DIR = ROOT / "docs/work-packages/20260827-a11e5-interannual-family-stability/artifacts"
A11E5 = A11E5_DIR / "development-evidence-v1.json"
A11E5_EXECUTOR = A11E5_DIR / "execute.py"
A11E5D = ROOT / "docs/work-packages/20260827-a11e5d-directional-error-attribution/artifacts/directional-evidence-v1.json"
RUNTIME_ROOT = ROOT / "target/a11e6-faithful-baseline-runtime"
BURNS = (0, 101, 1009, 10007, 100003, 1000003, 10000019, 100000007)
INTERANNUAL = (
    "monthly_precipitation_dispersion_error", "monthly_temperature_dispersion_error",
    "annual_precipitation_dispersion_error", "annual_temperature_dispersion_error",
    "precipitation_cross_month_correlation_rmse", "temperature_cross_month_correlation_rmse",
    "annual_precipitation_lag1_error", "annual_temperature_lag1_error",
    "annual_precipitation_low_frequency_error", "annual_temperature_low_frequency_error",
)
LEVEL = (
    "monthly_equivalent_precipitation_mean_relative_absolute_error",
    "monthly_temperature_mean_absolute_error_c",
    "monthly_range_mean_relative_absolute_error",
    "monthly_wet_fraction_mean_absolute_error",
)
METRICS = INTERANNUAL + LEVEL


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
    if spec is None or spec.loader is None:
        raise ExecutionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def git(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if result.returncode:
        raise ExecutionError(f"git failed: {' '.join(args)}")
    return result.stdout


def validate_manifest(value: Any) -> dict[str, Any]:
    expected = json.loads(MANIFEST.read_text()) if value is not None and MANIFEST.exists() else None
    if value != expected:
        raise ExecutionError("manifest differs from frozen bytes")
    if value["member_burns"] != list(BURNS) or value["station_count"] != 20 or value["years"] != 16:
        raise ExecutionError("manifest grid differs")
    return value


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if len(source_commit) != 40 or source_commit != git("rev-parse", "origin/main").decode().strip():
        raise ExecutionError("source is not exact origin/main")
    required = (Path(__file__), MANIFEST, SCHEMA, PACKAGE / "test_execute.py", SPEC, PACKAGE_DOC, PLAN)
    hashes = {}
    for path in required:
        relative = path.relative_to(ROOT).as_posix()
        blob = git("show", f"{source_commit}:{relative}")
        if blob != path.read_bytes():
            raise ExecutionError(f"working source differs: {relative}")
        hashes[relative] = hashlib.sha256(blob).hexdigest()
    deps = manifest["dependencies"]
    checks = ((PANEL, "panel_sha256"), (A11E3, "a11e3_evidence_sha256"),
              (A11E5, "a11e5_evidence_sha256"), (A11E5D, "a11e5d_evidence_sha256"),
              (A11E1, "a11e1_executor_sha256"), (A11E2, "a11e2_executor_sha256"),
              (A11E5_EXECUTOR, "a11e5_executor_sha256"), (ROOT / "Cargo.lock", "cargo_lock_sha256"),
              (ROOT / "Cargo.toml", "cargo_toml_sha256"))
    for path, key in checks:
        if digest(path) != deps[key]:
            raise ExecutionError(f"dependency drifted: {path}")
    return {"source_commit": source_commit, "source_tree": git("rev-parse", f"{source_commit}^{{tree}}").decode().strip(),
            "published_ref": "origin/main", "source_hashes": hashes}


def parse_cli(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    precipitation = np.zeros((16, 12)); tmean = np.zeros((16, 12)); daily_range = np.zeros((16, 12)); wet = np.zeros((16, 12))
    counts = np.zeros((16, 12), dtype=int); row_count = 0
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) != 13:
            continue
        try:
            day, month, year = map(int, fields[:3]); values = list(map(float, fields[3:]))
        except ValueError:
            continue
        if not (1 <= year <= 16 and 1 <= month <= 12 and 1 <= day <= calendar.monthrange(year, month)[1]):
            raise ExecutionError("invalid generated calendar row")
        y, m = year - 1, month - 1
        precipitation[y, m] += values[0]
        tmean[y, m] += (values[4] + values[5]) / 2.0
        daily_range[y, m] += values[4] - values[5]
        wet[y, m] += float(values[0] > 0.0)
        counts[y, m] += 1; row_count += 1
    if row_count != 5844:
        raise ExecutionError(f"expected 5844 daily rows, found {row_count}")
    for year in range(1, 17):
        for month in range(1, 13):
            if counts[year - 1, month - 1] != calendar.monthrange(year, month)[1]:
                raise ExecutionError("generated month is incomplete")
    precipitation *= 30.4375 / counts
    tmean /= counts; daily_range /= counts; wet /= counts
    return precipitation, tmean, daily_range, wet


def level_metrics(gp: np.ndarray, gt: np.ndarray, gr: np.ndarray, gw: np.ndarray, observed: dict[str, Any]) -> dict[str, float]:
    op, ot = observed["precipitation"], observed["tmean"]
    observed_range = observed.get("range", observed.get("daily_range"))
    if observed_range is None:
        observed_range = observed["dtr"]
    result = {
        LEVEL[0]: float(np.mean(np.abs(np.mean(gp, axis=0) - np.mean(op, axis=0)) / np.maximum(np.mean(op, axis=0), 0.01))),
        LEVEL[1]: float(np.mean(np.abs(np.mean(gt, axis=0) - np.mean(ot, axis=0)))),
        LEVEL[2]: float(np.mean(np.abs(np.mean(gr, axis=0) - np.mean(observed_range, axis=0)) / np.maximum(np.mean(observed_range, axis=0), 0.01))),
        LEVEL[3]: float(np.mean(np.abs(np.mean(gw, axis=0) - np.mean(observed["wet_fraction"], axis=0)))),
    }
    return result


def evaluate(rows: list[dict[str, Any]], material: float, minimum: int) -> dict[str, Any]:
    if len(rows) != 160 or len({(r["station_id"], r["member_id"]) for r in rows}) != 160:
        raise ExecutionError("decision requires exact 20x8 grid")
    metrics = {}; improved_interannual = 0; worse = []
    for name in METRICS:
        faithful = float(np.median([r["faithful_metrics"][name] for r in rows]))
        circular = float(np.median([r["circular_metrics"][name] for r in rows]))
        ratio = circular / max(faithful, 1e-12)
        status = "materially_improved" if ratio <= 1.0 - material else ("noninferior" if ratio <= 1.0 + material else "materially_worse")
        improved_interannual += int(name in INTERANNUAL and status == "materially_improved")
        if status == "materially_worse": worse.append(name)
        metrics[name] = {"faithful_median": faithful, "circular_median": circular, "ratio_circular_over_faithful": ratio, "status": status,
                         "pair_counts": {key: sum((r["circular_metrics"][name] / max(r["faithful_metrics"][name], 1e-12) <= bound) for r in rows)
                                         for key, bound in (("improved_at_least_5pct", 0.95), ("noninferior_at_5pct", 1.05))}}
    enough = improved_interannual >= minimum
    disposition = "BETTER_THAN_FAITHFUL_FOR_EXPLORATION" if enough and not worse else ("MIXED_VS_FAITHFUL" if enough else "NOT_BETTER_THAN_FAITHFUL")
    return {"disposition": disposition, "interannual_materially_improved_count": improved_interannual,
            "minimum_interannual_improvements": minimum, "all_fourteen_medians_noninferior": not worse,
            "materially_worse_metrics": worse, "metrics": metrics}


def execute(source_commit: str) -> None:
    started = time.monotonic(); manifest = validate_manifest(json.loads(MANIFEST.read_text()))
    runtime = {"python": platform.python_version(), "numpy": np.__version__}
    if runtime != manifest["runtime"]: raise ExecutionError("scientific runtime differs")
    source = verify_source(source_commit, manifest)
    if RUNTIME_ROOT.exists(): raise ExecutionError(f"deterministic runtime root already exists: {RUNTIME_ROOT}")
    try:
        station_root = Path(os.environ.get("CLIGEN_DATA_DIR", str(Path.home() / ".cache/cligen"))) / "stations/us-2015/2026.07"
        database = station_root / "2015_stations.db"
        if digest(database) != manifest["dependencies"]["station_database_sha256"]: raise ExecutionError("station database identity differs")
        panel = json.loads(PANEL.read_text()); stations = panel["stations"]
        if len(stations) != 20: raise ExecutionError("panel station count differs")
        station_files = {}
        for station in stations:
            path = station_root / f"{station['station_id']}.par"
            if digest(path) != station["parameter_sha256"]: raise ExecutionError(f"parameter identity differs: {station['station_id']}")
            station_files[station["station_id"]] = path

        predecessor = load_module("a11e2_for_a11e6", A11E2)
        pred_manifest = predecessor.validate_manifest(json.loads(A11E2_MANIFEST.read_text()))
        inherited_hashes, development_rows, _ = predecessor.verify_inputs(pred_manifest)
        inherited = predecessor.ensure_base_loaded(); development, observed_preflight = inherited.load_development(development_rows)
        observed_by_id = {row["point_id"]: row for row in development}
        fit, fit_preflight = inherited.load_fit_corpus(); adapters = inherited.adapter_parameters([row for row in fit if row["role"] == "candidate_fit"])

        a11e5_module = load_module("a11e5_for_a11e6", A11E5_EXECUTOR)
        circular_interannual = {(row["station_id"], row["member_id"]): row for row in json.loads(A11E5.read_text())["rows"]}
        circular_level = {(row["station_id"], row["member_id"]): row for row in json.loads(A11E3.read_text())["rows"]}
        directional = {(row["station_id"], row["member_id"]): row for row in json.loads(A11E5D.read_text())["rows"]}
        expected_keys = {(s["station_id"], i) for s in stations for i in range(8)}
        if set(circular_interannual) != expected_keys or set(circular_level) != expected_keys or set(directional) != expected_keys:
            raise ExecutionError("closed circular grids differ")

        RUNTIME_ROOT.mkdir(parents=True); build_target = RUNTIME_ROOT / "build"
        build = subprocess.run(["cargo", "build", "--release", "--locked", "--bin", "cligen", "--target-dir", str(build_target)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode: raise ExecutionError(f"release build failed: {build.stderr[-4000:]}")
        binary = build_target / "release/cligen"; binary_sha = digest(binary)
        rows = []
        for station in stations:
            station_id = station["station_id"]; observed = observed_by_id[station_id]
            for member_id, burn in enumerate(BURNS):
                run_dir = RUNTIME_ROOT / "runs" / station_id / str(member_id); run_dir.mkdir(parents=True)
                par = run_dir / "source.par"; shutil.copyfile(station_files[station_id], par)
                cli = run_dir / "out.cli"; runspec = run_dir / "run.yaml"
                runspec.write_text("cligen_runspec: 1\nstation:\n  par: source.par\nmode: continuous\nsimulation:\n  begin_year: 1\n  years: 16\n  interpolation: none\nrng:\n  burn: %d\ngeneration_profile: faithful_5_32_3\nqc_filter: faithful\noutput:\n  cli: out.cli\n  quality: false\n  overwrite: false\n  command_echo: '-r%d -isource.par'\n" % (burn, burn))
                run = subprocess.run([str(binary), "run", "run.yaml"], cwd=run_dir, capture_output=True, text=True)
                if run.returncode: raise ExecutionError(f"cligen failed {station_id}/{burn}: {run.stderr[-2000:]}")
                provenance = run_dir / "out.cli.provenance.json"
                gp, gt, gr, gw = parse_cli(cli)
                faithful = a11e5_module.interannual_metrics(gp, gt, observed["precipitation"], observed["tmean"], adapters[observed["regime"]]["annual_weights"][12:24])
                faithful.update(level_metrics(gp, gt, gr, gw, observed))
                key = (station_id, member_id); circular = dict(circular_interannual[key]["treatment_metrics"])
                nearest = circular_level[key]["nearest_metrics"]
                circular.update({name: nearest[name] for name in LEVEL})
                if set(faithful) != set(METRICS) or set(circular) != set(METRICS) or not all(math.isfinite(v) for v in [*faithful.values(), *circular.values()]):
                    raise ExecutionError("metric set invalid")
                annual_precip = np.sum(gp, axis=1); annual_temp = gt @ adapters[observed["regime"]]["annual_weights"][12:24]
                rows.append({"station_id": station_id, "station_regime": observed["regime"], "member_id": member_id, "burn": burn,
                    "faithful_metrics": faithful, "circular_metrics": circular,
                    "differences_circular_minus_faithful": {name: circular[name] - faithful[name] for name in METRICS},
                    "directional": {"faithful_annual_precipitation_variance_ratio": float(np.var(annual_precip, ddof=1) / max(np.var(np.sum(observed["precipitation"], axis=1), ddof=1), 1e-12)),
                                    "faithful_annual_temperature_variance_ratio": float(np.var(annual_temp, ddof=1) / max(np.var(observed["tmean"] @ adapters[observed["regime"]]["annual_weights"][12:24], ddof=1), 1e-12)),
                                    "circular": directional[key]["treatment"]},
                    "provenance": {"source_par_sha256": digest(par), "runspec_sha256": digest(runspec), "cli_sha256": digest(cli),
                                   "provenance_sha256": digest(provenance), "cligen_binary_sha256": binary_sha},
                    "faithful_stream_summary_sha256": canonical_digest({"precipitation": gp.tolist(), "temperature": gt.tolist(), "range": gr.tolist(), "wet_fraction": gw.tolist()}),
                    "circular_interannual_stream_summary_sha256": circular_interannual[key]["treatment_stream_summary_sha256"],
                    "circular_level_stream_summary_sha256": circular_level[key]["nearest_stream_summary_sha256"]})
        decision_body = evaluate(rows, manifest["material_ratio"], manifest["minimum_interannual_improvements"])
        preflight = {"schema_version": "a11e6-preflight-1", "valid": True, "source_transform": "daymet_official_365_v1",
                     "normalized_statistic": "daymet_mask_normalized_month_v1", "observed": observed_preflight, "fit": fit_preflight,
                     "station_count": 20, "stream_count": 160, "expected_daily_rows_per_stream": 5844,
                     "station_database_sha256": digest(database), "confirmation_target_series_accessed": False}
        evidence = {"schema_version": "a11e6-development-evidence-1", "execution_id": manifest["execution_id"], "source_commit": source_commit,
                    "control": manifest["control_profile"], "treatment": manifest["treatment_strategy"], "paired_rows": 160, "rows": rows,
                    "decision": decision_body, "limitations": ["sixteen-year streams make higher-order temporal metrics noisy", "development observations have been reused across A11 exploratory work", "burn identifiers do not pair random draws across different generators"],
                    "confirmation_target_series_accessed": False}
        evidence["evidence_sha256"] = canonical_digest(evidence)
        decision = {"schema_version": "a11e6-development-decision-1", "terminal": "EXECUTED-COMPLETE", "science_status": "FAITHFUL_BASELINE_COMPARISON_EVALUATED", **decision_body,
                    "confirmation_authorized": False, "production_authorized": False}
        atomic_json(PACKAGE / "calendar-missingness-preflight-v1.json", preflight); atomic_json(PACKAGE / "development-evidence-v1.json", evidence); atomic_json(PACKAGE / "development-decision-v1.json", decision)
        outputs = [PACKAGE / name for name in ("calendar-missingness-preflight-v1.json", "development-evidence-v1.json", "development-decision-v1.json")]
        receipt = {"schema_version": "a11e6-execution-receipt-1", "execution_id": manifest["execution_id"], **source, "runtime": runtime,
                   "build": {"command": "cargo build --release --locked --bin cligen --target-dir <deterministic-runtime>/build", "cargo_version": subprocess.check_output(["cargo", "--version"], text=True).strip(), "rustc_version": subprocess.check_output(["rustc", "--version"], text=True).strip(), "rustflags": os.environ.get("RUSTFLAGS", ""), "cargo_lock_sha256": digest(ROOT / "Cargo.lock"), "cargo_toml_sha256": digest(ROOT / "Cargo.toml"), "cligen_binary_sha256": binary_sha},
                   "station_database_sha256": digest(database), "inherited_input_hashes": inherited_hashes,
                   "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in outputs},
                   "stream_count": 160, "elapsed_seconds": time.monotonic() - started, "confirmation_target_series_accessed": False}
        atomic_json(PACKAGE / "execution-receipt-v1.json", receipt)
    finally:
        if RUNTIME_ROOT.exists(): shutil.rmtree(RUNTIME_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--source-commit"); parser.add_argument("--validate-manifest", action="store_true"); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    manifest = validate_manifest(json.loads(MANIFEST.read_text()))
    if args.validate_manifest: print(canonical_digest(manifest)); return
    if not args.execute or not args.source_commit: parser.error("--execute requires --source-commit")
    execute(args.source_commit)


if __name__ == "__main__": main()
