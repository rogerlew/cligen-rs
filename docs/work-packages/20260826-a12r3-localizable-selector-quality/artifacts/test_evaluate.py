#!/usr/bin/env python3
"""Synthetic unit tests for A12R3 evaluator decisions and contracts."""

import importlib.util
import json
import sys
import unittest
from unittest import mock
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a12r3_evaluate", HERE / "evaluate.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def metric_row(value):
    metrics = {name: value for name in MODULE.METRICS}
    metrics["composite"] = value
    return {"metrics": metrics}


class A12R3Tests(unittest.TestCase):
    def test_manifest_is_exact(self):
        value = json.loads(MODULE.MANIFEST_PATH.read_text())
        self.assertEqual(MODULE.validate_manifest(value)["schema_version"], 1)

    def test_manifest_rejects_extra_field(self):
        value = json.loads(MODULE.MANIFEST_PATH.read_text())
        value["extra"] = True
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.validate_manifest(value)

    def test_current_supported_disposition(self):
        manifest = json.loads(MODULE.MANIFEST_PATH.read_text())
        rows = []
        for index in range(240):
            rows.append({"policies": {
                MODULE.ARM["closest"]: metric_row(1.0),
                MODULE.ARM["current"]: metric_row(0.8),
                MODULE.ARM["reference"]: metric_row(0.9 if index < 100 else 1.1),
            }})
        _, decision = MODULE.summarize(rows, manifest)
        self.assertEqual(decision["disposition"], "CURRENT_HEURISTIC_APPROPRIATE")

    def test_closest_when_no_selector_supported(self):
        manifest = json.loads(MODULE.MANIFEST_PATH.read_text())
        rows = [{"policies": {arm: metric_row(1.0) for arm in MODULE.POLICIES}} for _ in range(240)]
        _, decision = MODULE.summarize(rows, manifest)
        self.assertEqual(decision["disposition"], "CLOSEST_PREFERRED")

    def test_reference_supported_disposition(self):
        manifest = json.loads(MODULE.MANIFEST_PATH.read_text())
        rows = [{"policies": {
            MODULE.ARM["closest"]: metric_row(1.0),
            MODULE.ARM["current"]: metric_row(1.1),
            MODULE.ARM["reference"]: metric_row(0.8),
        }} for _ in range(240)]
        _, decision = MODULE.summarize(rows, manifest)
        self.assertEqual(decision["disposition"], "ELEVATION_REFERENCE_BETTER")

    def test_both_supported_lower_arm_median_wins(self):
        manifest = json.loads(MODULE.MANIFEST_PATH.read_text())
        rows = [{"policies": {
            MODULE.ARM["closest"]: metric_row(1.0),
            MODULE.ARM["current"]: metric_row(0.9),
            MODULE.ARM["reference"]: metric_row(0.8),
        }} for _ in range(240)]
        _, decision = MODULE.summarize(rows, manifest)
        self.assertEqual(decision["disposition"], "ELEVATION_REFERENCE_BETTER")

    def test_support_rejects_family_worsening(self):
        manifest = json.loads(MODULE.MANIFEST_PATH.read_text())
        baseline = [metric_row(1.0) for _ in range(240)]
        candidate = [metric_row(0.8) for _ in range(240)]
        for row in candidate:
            row["metrics"][MODULE.METRICS[0]] = 1.06
        self.assertFalse(MODULE.paired_comparison(candidate, baseline, manifest)["supported"])

    def test_source_surface_covers_build_inputs(self):
        relative = {path.relative_to(MODULE.ROOT).as_posix() for path in MODULE.source_paths()}
        for required in ("Cargo.lock", "rust-toolchain.toml", "crates/cligen/src/prism/run.rs",
                         "crates/cligen/src/prism/localize.rs",
                         "crates/cligen/src/prism/grid.rs", "crates/cligen/src/prism/mod.rs",
                         "crates/cligen/src/prism/sync.rs", "crates/cligen/src/prism/method.json",
                         "crates/cligen/src/prism/distribution.json",
                         "crates/cligen/src/stations/manifests.json"):
            self.assertIn(required, relative)

    def test_dirty_build_is_rejected(self):
        commit = "a" * 40

        def fake_git(*arguments):
            if arguments == ("status", "--porcelain"):
                return b"?? dirty\n"
            return (commit + "\n").encode()

        with mock.patch.object(MODULE, "git", side_effect=fake_git), \
                mock.patch.object(MODULE, "source_paths", return_value=[]):
            with self.assertRaisesRegex(MODULE.EvaluationError, "not clean"):
                MODULE.verify_source(commit, require_clean=True)

    def test_execution_paths_are_disjoint(self):
        self.assertTrue(set(MODULE.paths(False).values()).isdisjoint(MODULE.paths(True).values()))

    def test_masked_errors_ignore_only_nan_month(self):
        import numpy as np
        observed = {name: np.ones(12) for name in ("sd", "skew", "pww", "pwd", "tmax_sd", "tmin_sd")}
        observed["sd"][5] = np.nan
        observed["skew"][5] = np.nan
        par = {name: np.ones(12, dtype=np.float32) for name in ("sd", "skew", "tmax_sd", "tmin_sd")}
        localized = {"pww": np.ones(12), "pwd": np.ones(12)}
        result = MODULE.errors_masked(par, observed, localized)
        self.assertTrue(all(value == 0.0 for value in result.values()))

    def test_masked_errors_reject_non_wet_family_nan(self):
        import numpy as np
        observed = {name: np.ones(12) for name in ("sd", "skew", "pww", "pwd", "tmax_sd", "tmin_sd")}
        observed["pww"][5] = np.nan
        par = {name: np.ones(12, dtype=np.float32) for name in ("sd", "skew", "tmax_sd", "tmin_sd")}
        localized = {"pww": np.ones(12), "pwd": np.ones(12)}
        with self.assertRaisesRegex(MODULE.EvaluationError, "twelve-month"):
            MODULE.errors_masked(par, observed, localized)

    def test_estimand_diagnostic_rejects_unexpected_sparse_cell(self):
        eligibility = {"sparse_wet_months": [{"month": 1, "wet_day_count": 2,
                                                "wet_predecessor_count": 1,
                                                "dry_predecessor_count": 10}]}
        site = ({"point_id": "unexpected", "regime": "hot_arid"}, None, None, None,
                None, None, None, eligibility)
        with self.assertRaisesRegex(MODULE.EvaluationError, "diagnostic reproduction"):
            MODULE.verify_estimand_diagnostic([site])

    def test_station_arm_snapshot_detaches_mutable_distance(self):
        station = {"id": "x.par", "distance_km": 1.0}
        snapshot = MODULE.snapshot_arms({"closest_localizable_v1": station})
        station["distance_km"] = 99.0
        self.assertEqual(snapshot["closest_localizable_v1"]["distance_km"], 1.0)


if __name__ == "__main__":
    unittest.main()
