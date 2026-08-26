#!/usr/bin/env python3
"""Synthetic tests for the prospective A12 evaluator."""

from __future__ import annotations

import importlib.util
import datetime as dt
import sys
import unittest
from pathlib import Path

import numpy as np


PATH = Path(__file__).with_name("evaluate.py")
SPEC = importlib.util.spec_from_file_location("a12_evaluate", PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class EvaluationTests(unittest.TestCase):
    def test_adjusted_skew_is_zero_for_symmetric_values(self) -> None:
        self.assertAlmostEqual(MODULE.adjusted_skew(np.array([1.0, 2.0, 3.0])), 0.0)

    def test_ranks_break_ties_by_station_id(self) -> None:
        self.assertEqual(MODULE.ranks([1.0, 1.0, 0.0], ["b", "a", "c"]), [2, 1, 0])

    def test_haversine_is_zero_at_same_coordinate(self) -> None:
        row = {"latitude": 46.0, "longitude": -117.0}
        self.assertEqual(MODULE.haversine_km(46.0, -117.0, row), 0.0)

    def test_station_precipitation_uses_occurrence_equilibrium(self) -> None:
        par = {"mean": np.ones(12), "pww": np.full(12, 0.5), "pwd": np.full(12, 0.5)}
        np.testing.assert_allclose(MODULE.station_ppt(par), MODULE.DAYS * 0.5)

    def test_errors_are_zero_for_exact_descriptor_match(self) -> None:
        values = np.ones(12, dtype=np.float32)
        par = {"mean": values, "sd": values, "skew": values, "pww": values * np.float32(0.5),
               "pwd": values * np.float32(0.25), "tmax_sd": values * np.float32(2.0),
               "tmin_sd": values * np.float32(3.0), "intensity": values}
        normals = {"monthly_ppt_in": [10.0] * 12, "monthly_tmax_f": [50.0] * 12,
                   "monthly_tmin_f": [40.0] * 12}
        localized = MODULE.localized_parameters(par, normals)
        observed = {"sd": values, "skew": values, "pww": localized["pww"],
                    "pwd": localized["pwd"],
                    "tmax_sd": values * 2.0, "tmin_sd": values * 3.0}
        result = MODULE.errors(par, observed, normals)
        self.assertTrue(all(value == 0.0 for value in result.values()))

    def test_monthly_rows_round_through_f32(self) -> None:
        lines = ["        " + "  0.10" * 12]
        value = MODULE.monthly_row(lines, 1)
        self.assertEqual(value.dtype, np.float32)
        self.assertEqual(float(value[0]), float(np.float32(0.1)))

    def test_localization_changes_occurrence_and_quantizes_to_f32(self) -> None:
        par = {"mean": np.ones(12, dtype=np.float32), "pww": np.full(12, 0.5, dtype=np.float32),
               "pwd": np.full(12, 0.25, dtype=np.float32),
               "intensity": np.ones(12, dtype=np.float32)}
        pww, pwd = MODULE.localized_occurrence(par, np.full(12, 20.0))
        self.assertFalse(np.all(pww == par["pww"]))
        self.assertTrue(all(value == float(np.float32(f"{value:.2f}")) for value in pww))
        self.assertTrue(np.all((pwd > 0.0) & (pwd < 1.0)))

    def test_unlocalizable_occurrence_fails_closed(self) -> None:
        par = {"mean": np.zeros(12, dtype=np.float32), "pww": np.full(12, 0.5, dtype=np.float32),
               "pwd": np.full(12, 0.25, dtype=np.float32),
               "intensity": np.ones(12, dtype=np.float32)}
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.localized_occurrence(par, np.full(12, 1.0))

    def test_full_localization_rejects_overflow_and_temperature_inversion(self) -> None:
        par = {"mean": np.ones(12, dtype=np.float32), "pww": np.full(12, 0.5, dtype=np.float32),
               "pwd": np.full(12, 0.25, dtype=np.float32),
               "intensity": np.full(12, 100000.0, dtype=np.float32)}
        normals = {"monthly_ppt_in": [1.0] * 12, "monthly_tmax_f": [50.0] * 12,
                   "monthly_tmin_f": [40.0] * 12}
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.localized_parameters(par, normals)
        par["intensity"] = np.ones(12, dtype=np.float32)
        normals["monthly_tmax_f"] = [30.0] * 12
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.localized_parameters(par, normals)

    def test_mask_and_date_gap_break_transition_chain(self) -> None:
        dates = [dt.date(2000, 1, 1), dt.date(2000, 1, 2), dt.date(2000, 1, 4), dt.date(2000, 1, 5)]
        precipitation = np.array([1.0, 1.0, 0.0, 1.0])
        observed = np.array([True, False, True, True])
        self.assertEqual(MODULE.wet_transition_counts(dates, observed, precipitation, (0, 2, 3)),
                         (0, 1, 0, 1))

    def test_calendar_axis_pins_leap_and_boundaries(self) -> None:
        axis = MODULE.expected_axis("1980-01-01", "2009-12-31")
        self.assertEqual(len(axis), 10958)
        self.assertEqual((axis[0], axis[-1]), ("1980-01-01", "2009-12-31"))
        self.assertIn("2000-02-29", axis)
        self.assertEqual(len(axis), len(set(axis)))

    def test_bootstrap_is_domain_separated_and_exactly_replayable(self) -> None:
        manifest = MODULE.validate_manifest(MODULE.json.loads(MODULE.MANIFEST_PATH.read_text()))
        deltas = np.linspace(-2.0, 1.0, 37) ** 3
        first = MODULE.bootstrap_interval(deltas, manifest)
        self.assertEqual(first, MODULE.bootstrap_interval(deltas, manifest))
        changed = MODULE.json.loads(MODULE.json.dumps(manifest))
        changed["bootstrap"]["domain"] = "different-domain"
        original_draws = MODULE.bootstrap_rng(manifest["bootstrap"]).integers(0, 1000, size=10).tolist()
        changed_draws = MODULE.bootstrap_rng(changed["bootstrap"]).integers(0, 1000, size=10).tolist()
        self.assertNotEqual(original_draws, changed_draws)

    def test_decision_and_paired_family_deltas(self) -> None:
        manifest = MODULE.validate_manifest(MODULE.json.loads(MODULE.MANIFEST_PATH.read_text()))
        rows = []
        for index in range(12):
            policies = {}
            for policy, metric_value in zip(MODULE.POLICIES, (1.0, 0.8, 1.1)):
                metrics = {metric: metric_value for metric in MODULE.METRICS}
                metrics["composite"] = metric_value
                policies[policy] = {"metrics": metrics}
            rows.append({"point_id": str(index), "policies": policies})
        summaries, decision = MODULE.summarize(rows, manifest)
        self.assertEqual(decision["disposition"], "CURRENT_HEURISTIC_APPROPRIATE")
        self.assertEqual(set(summaries[MODULE.POLICIES[1]]["paired_family_median_deltas"]),
                         set(MODULE.METRICS))
        for value in summaries[MODULE.POLICIES[1]]["paired_family_median_deltas"].values():
            self.assertAlmostEqual(value, -0.2)

    def test_manifest_rejects_nested_mutation(self) -> None:
        manifest = MODULE.json.loads(MODULE.MANIFEST_PATH.read_text())
        manifest["bootstrap"]["extra"] = True
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.validate_manifest(manifest)

    def test_build_receipt_rejects_tampered_source_hashes(self) -> None:
        expected = {"binary": "a" * 64}
        receipt = {"schema_version": "a12-build-receipt-1", "source_commit": "b" * 40,
                   "source_hashes": {"file": "c" * 64}, **expected}
        with self.assertRaises(MODULE.EvaluationError):
            MODULE.validate_build_receipt_fields(receipt, "b" * 40,
                                                 {"file": "d" * 64}, expected)

    def test_manifest_is_strict_and_current(self) -> None:
        manifest = MODULE.validate_manifest(MODULE.json.loads(MODULE.MANIFEST_PATH.read_text()))
        self.assertEqual(manifest["corpus"]["site_count"], 240)


if __name__ == "__main__":
    unittest.main()
