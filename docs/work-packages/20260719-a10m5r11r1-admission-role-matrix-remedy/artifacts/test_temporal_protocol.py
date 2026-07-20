#!/usr/bin/env python3
"""Regression tests for the A10M5R11 inherited temporal protocol."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def load_selector():
    path = PACKAGE / "artifacts/jobs/temporal_select.py"
    sys.path.insert(0, str(path.parent))
    fake_numpy = types.ModuleType("numpy")
    fake_numpy.concatenate = lambda values: [item for value in values for item in value]
    sys.modules.setdefault("numpy", fake_numpy)
    spec = importlib.util.spec_from_file_location("a10m5r11_temporal_select", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load temporal selector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TemporalProtocolTest(unittest.TestCase):
    def test_retained_matrix_and_dispersion_metrics(self) -> None:
        contract = json.loads(
            (PACKAGE / "artifacts/temporal-contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [row["configuration_id"] for row in contract["roles"]],
            [
                "annual_monthly_residual_adapter-k1",
                "monthly_residual_adapter-k2",
                "annual_monthly_residual_adapter-k2",
            ],
        )
        self.assertIn("standard_deviation", contract["metrics"]["monthly_precipitation"])
        self.assertIn("precipitation_standard_deviation", contract["metrics"]["annual"])
        self.assertIn("tmax_standard_deviation", contract["metrics"]["annual"])
        self.assertEqual(contract["metrics"]["paired_daily_pattern_weight"], 0.0)

    def test_leap_safe_resampling_preserves_block_shape(self) -> None:
        module = load_selector()
        captured = {}
        module.realized_metrics = lambda dates, *_: captured.setdefault("dates", dates) or {}
        blocks = [
            {
                "dates": [dt.date(2000, 2, 28), dt.date(2000, 2, 29)],
                "precipitation": [0.0, 0.0], "tmax": [0.0, 0.0], "tmin": [0.0, 0.0],
            },
            {
                "dates": [dt.date(2001, 12, 30), dt.date(2001, 12, 31)],
                "precipitation": [0.0, 0.0], "tmax": [0.0, 0.0], "tmin": [0.0, 0.0],
            },
        ]
        module.resampled_observation(blocks, [0, 1])
        dates = captured["dates"]
        self.assertEqual(dates[:2], [dt.date(2000, 2, 28), dt.date(2000, 2, 29)])
        self.assertEqual(dates[2:], [dt.date(2017, 12, 30), dt.date(2017, 12, 31)])


if __name__ == "__main__":
    unittest.main()
