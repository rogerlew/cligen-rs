#!/usr/bin/env python3
"""Synthetic tests for A11E5D directional attribution."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a11e5d_analyze_tested", HERE / "analyze.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DirectionalTests(unittest.TestCase):
    def test_manifest_is_exact(self) -> None:
        value = MODULE.validate_manifest(json.loads((HERE / "analysis-manifest-v1.json").read_text()))
        self.assertEqual(value["station_count"], 20)

    def test_variance_record_preserves_direction(self) -> None:
        observed = np.asarray([-1.0, 0.0, 1.0])
        over = MODULE.variance_record(observed * 2.0, observed)
        under = MODULE.variance_record(observed / 2.0, observed)
        self.assertAlmostEqual(over["signed_log_variance_ratio"], np.log(4.0))
        self.assertAlmostEqual(under["signed_log_variance_ratio"], np.log(0.25))

    def test_signed_summary_separates_bias_and_scatter(self) -> None:
        entries = []
        for index, signed in enumerate((1.0, -1.0)):
            entries.append({"station_id": f"s{index}", "member_id": 0, "signed_log_variance_ratio": signed,
                            "generated_variance": np.exp(signed), "observed_variance": 1.0})
        result = MODULE.signed_summary(entries, 0.05)
        self.assertEqual(result["mean_signed_log_variance_ratio"], 0.0)
        self.assertEqual(result["mean_absolute_log_variance_ratio"], 1.0)
        self.assertEqual(result["bias_fraction_abs_mean_over_mean_absolute"], 0.0)

    def test_comparison_positive_means_treatment_more_variable(self) -> None:
        base = {"station_id": "s", "member_id": 0, "signed_log_variance_ratio": 0.0,
                "generated_variance": 1.0, "observed_variance": 1.0}
        treatment = {**base, "signed_log_variance_ratio": np.log(2.0), "generated_variance": 2.0}
        result = MODULE.comparison_summary([base], [treatment], 0.05)
        self.assertAlmostEqual(result["geometric_mean_variance_ratio"], 2.0)

    def test_empty_summary_fails_closed(self) -> None:
        with self.assertRaises(MODULE.AnalysisError):
            MODULE.signed_summary([], 0.05)


if __name__ == "__main__":
    unittest.main()
