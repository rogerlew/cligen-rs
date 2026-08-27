#!/usr/bin/env python3
"""Synthetic contract tests for A11E5."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e5_execute_tested", HERE / "execute.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ContractTests(unittest.TestCase):
    def test_manifest_is_exact(self) -> None:
        value = MODULE.validate_manifest(json.loads((HERE / "execution-manifest-v1.json").read_text()))
        self.assertEqual(value["member_ids"], list(range(8)))

    def test_variance_and_low_frequency_identity_are_zero(self) -> None:
        values = np.arange(1.0, 17.0)
        self.assertEqual(MODULE.variance_log_error(values, values), 0.0)
        self.assertEqual(MODULE.low_frequency_fraction(np.ones(16)), 0.0)

    def test_cross_month_identity_is_zero(self) -> None:
        values = np.arange(192.0).reshape(16, 12)
        self.assertEqual(MODULE.cross_month_correlation_rmse(values, values), 0.0)

    def test_decision_boundaries(self) -> None:
        rows = []
        for station in range(20):
            for member in range(8):
                treatment = 0.94 if len(rows) < 54 else 1.0
                rows.append({
                    "station_id": f"s{station:02d}",
                    "member_id": member,
                    "control_family_score": 1.0,
                    "treatment_family_score": treatment,
                    "control_metrics": {metric: 1.0 for metric in MODULE.METRICS},
                    "treatment_metrics": {metric: treatment for metric in MODULE.METRICS},
                })
        decision = MODULE.evaluate_decision(rows, 0.05, 1.0 / 3.0)
        self.assertEqual(decision["pair_counts"], {"materially_improved": 54, "neutral": 106, "materially_worse": 0})
        self.assertEqual(decision["disposition"], "VIABLE_AS_UNIVERSAL_EXPLORATION")
        rows[-1]["treatment_family_score"] = 1.06
        decision = MODULE.evaluate_decision(rows, 0.05, 1.0 / 3.0)
        self.assertEqual(decision["disposition"], "MIXED_REQUIRES_ROUTING")

    def test_metric_shape_fails_closed(self) -> None:
        with self.assertRaises(MODULE.ExecutionError):
            MODULE.monthly_dispersion_error(np.ones((16, 11)), np.ones((16, 11)))


if __name__ == "__main__":
    unittest.main()
